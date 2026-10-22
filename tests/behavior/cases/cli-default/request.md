# 用户请求

这个命令默认导出的每条 JSON 都应该包含 `duration_ms`。加 `--metrics` 才有不是我想要的结果，不要增加操作步骤。请给最小修复及验证方式，不要部署或升级依赖。

## 当前代码

```python
def export_row(task, duration_ms, metrics=False):
    row = {"task": task}
    if metrics:
        row["duration_ms"] = duration_ms
    return row
```

```python
parser.add_argument("--metrics", action="store_true")
args = parser.parse_args()
print(json.dumps(export_row("compile", 42, args.metrics)))
```

现有测试均通过：

```python
assert export_row("compile", 42) == {"task": "compile"}
assert export_row("compile", 42, True) == {"task": "compile", "duration_ms": 42}
```

没有其他调用方材料；本次保持 task 字段与既有 `--metrics` 命令兼容，不需要新增浏览器页面。
