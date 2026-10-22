"""Add only SS to existing local clients. Dry-run unless --apply is explicit.

Config backups remain beside user config (potentially secret-bearing), never in this package.
Existing SS entries must match; conflicts are reported instead of overwritten.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
SERVER_ID = "software-stack"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def files_under(path: Path) -> dict[str, str]:
    return {p.relative_to(path).as_posix(): digest(p.read_bytes())
            for p in path.rglob("*") if p.is_file()}


def build_changes(home: Path, workspace_roots: list[Path]) -> tuple[list, dict]:
    python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        raise ValueError("Create the package virtual environment and install requirements first")
    if not workspace_roots or any(not p.is_absolute() or not p.is_dir() for p in workspace_roots):
        raise ValueError("Provide existing absolute workspace roots")
    command = str(python)
    args = ["-B", str(ROOT / "server.py")]
    env = {"PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1",
           "SS_WORKSPACE_ROOTS": json.dumps([str(p.resolve()) for p in workspace_roots], ensure_ascii=False)}
    expected = {"command": command, "args": args, "env": env}
    changes = []
    info = {"server": SERVER_ID, "workspace_roots": [str(p) for p in workspace_roots],
            "clients": {}, "package": str(ROOT), "git_or_remote_action": False}
    for client, path in (("codex", home / ".codex/config.toml"), ("claude", home / ".claude.json")):
        if not path.is_file():
            info["clients"][client] = "not installed; config absent, skipped"
            continue
        before = path.read_bytes()
        text = before.decode("utf-8-sig")
        data = tomllib.loads(text) if client == "codex" else json.loads(text)
        key = "mcp_servers" if client == "codex" else "mcpServers"
        servers = data.get(key, {})
        entry = expected if client == "codex" else {"type": "stdio", **expected}
        if SERVER_ID in servers:
            if servers[SERVER_ID] != entry:
                raise ValueError(f"Existing SS registration conflicts in {client}; not overwritten")
            info["clients"][client] = "already matches"
            continue
        if client == "codex":
            candidate = text.rstrip() + "\n\n[mcp_servers.software-stack]\n"
            candidate += f"command = {json.dumps(command, ensure_ascii=False)}\n"
            candidate += f"args = {json.dumps(args, ensure_ascii=False)}\n"
            candidate += "\n[mcp_servers.software-stack.env]\n"
            candidate += "".join(f"{k} = {json.dumps(v, ensure_ascii=False)}\n" for k, v in env.items())
            check = tomllib.loads(candidate)
        else:
            updated = json.loads(text)
            updated.setdefault(key, {})[SERVER_ID] = entry
            candidate = json.dumps(updated, ensure_ascii=False, indent=2) + "\n"
            check = json.loads(candidate)
        inserted = check[key].pop(SERVER_ID)
        if key not in data and not check[key]:
            del check[key]
        if check != data or inserted != entry:
            raise ValueError(f"Parity check failed before writing {client}")
        changes.append((path, before, candidate.encode("utf-8")))
        info["clients"][client] = "planned new SS entry"
    return changes, info


def install(home: Path, workspace_roots: list[Path], apply: bool = False) -> dict:
    changes, info = build_changes(home, workspace_roots)
    source = ROOT / "skills/software-stack"
    skill = home / ".agents/skills/software-stack"
    command = home / ".claude/commands/SS.md"
    command_data = (ROOT / "commands/SS.md").read_bytes()
    if skill.exists() and files_under(skill) != files_under(source):
        raise ValueError("Existing installed SS skill differs; review before updating")
    if command.exists() and command.read_bytes() != command_data:
        raise ValueError("Existing /SS command differs; not overwritten")
    # Prevent duplicate Codex skill discovery under the older user location.
    if (home / ".codex/skills/software-stack").exists():
        raise ValueError("Duplicate SS skill in .codex/skills; choose one install location")
    info.update({"applied": False, "skill_target": str(skill), "command_target": str(command),
                 "changes": len(changes), "current_session_hot_reload_verified": False})
    if not apply:
        return info
    # Preflight all snapshots before writing any client configuration.
    for path, before, _ in changes:
        if path.read_bytes() != before:
            raise ValueError("Config changed during preflight; rerun after reviewing")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backups = []
    for path, before, _ in changes:
        backup = path.with_name(path.name + ".ss-backup-" + stamp)
        with backup.open("xb") as f:
            f.write(before)
        backups.append(str(backup))
    if not skill.exists():
        skill.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, skill)
    if "claude" in info["clients"] and "skipped" not in info["clients"]["claude"]:
        command.parent.mkdir(parents=True, exist_ok=True)
        if not command.exists():
            with command.open("xb") as f:
                f.write(command_data)
    written = []
    try:
        for path, before, after in changes:
            if path.read_bytes() != before:
                raise ValueError("Client config changed during installation; stop, do not clobber")
            temp = path.with_name(path.name + ".ss-tmp-" + stamp)
            with temp.open("xb") as f:
                f.write(after)
            if path.read_bytes() != before:
                temp.unlink()
                raise ValueError("Client config changed before replacement")
            os.replace(temp, path)
            written.append((path, before, after))
            if path.read_bytes() != after:
                raise ValueError("Config readback differs after replacement")
    except Exception:
        # Only undo our exact bytes; never erase concurrent user changes.
        for path, before, after in reversed(written):
            if path.read_bytes() == after:
                path.write_bytes(before)
        raise
    info.update({"applied": True, "backups": backups,
                 "installed_skill_matches": files_under(skill) == files_under(source),
                 "original_client_config_semantics_preserved": True})
    info["clients"] = {k: ("registered" if v == "planned new SS entry" else v)
                       for k, v in info["clients"].items()}
    return info


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, action="append", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(install(Path.home(), args.workspace_root, args.apply), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as e:
        print(f"SS registration stopped: {e}", file=sys.stderr)
        sys.exit(1)
