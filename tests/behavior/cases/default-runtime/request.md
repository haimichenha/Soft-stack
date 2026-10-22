# 用户请求

保存成功后应该自动播放那个短确认动画。我这里还是只有静态图；不要让我多点一个按钮，也不要重做已经满意的配色。请先判断下一步怎么修。

## 当前运行证据

```json
{"deployed":"build-r7","browser":"build-r7","mode":"auto","prefersReducedMotion":true,"assetsReady":true}
```

相关代码：

```js
const gentle = prefersReducedMotion && mode !== 'force';
const backgroundFps = gentle ? 12 : 30;
const confirmation = gentle ? 'static' : 'short-confirmation';
```

已有测试：

```text
default auto + prefersReducedMotion=true => confirmation is static: PASS
force + prefersReducedMotion=true => short-confirmation plays: PASS
background stops after unmount: PASS
```

已授权本地修复，但未授权生产发布或更改操作系统设置。现在只有以上证据，没有新的实测或截图。
