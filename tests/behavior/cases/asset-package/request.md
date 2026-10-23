# 用户请求

关掉新特效开关后，浏览器网络里没有下载它的图。是不是就能说这次上线包体没有增加？有人建议把原件、制作笔记和运行图都放进公开素材目录省事。请审查这种交付方式。

## 已有证据

```text
设置: FEATURE_NEW_EFFECT=false
同一构建的匿名页面观察: 新 PNG 请求数=0
构建步骤: 把 public 内容复制进 dist，不检查特效开关
```

构建输出清单节选（不是整包清单）：

```text
dist/effects/v2/pose-a.png        1,400,000 bytes
dist/effects/v2/pose-b.png        1,200,000 bytes
dist/effects/v2/master.psd      28,000,000 bytes
dist/effects/v2/prompts.md           4,000 bytes
dist/LICENSES/asset-license.txt      1,800 bytes
dist/source/offer.zip          依法需提供的对应源码归档
```

没有旧版完整产物清单、压缩传输测量或浏览器解码内存报告。原件和笔记尚未确定是否需要公开；许可说明与对应源码按本项目的交付要求必须保留。资源源文件目前仍在工作目录，不应直接删除。

本轮只允许审查和给出最小验证/整理方案；没有授权移动删除文件、重建、提交或发布。请给出准确的包体结论和下一步，不替换工具链。
