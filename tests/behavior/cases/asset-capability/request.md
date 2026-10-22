# 用户请求

我想让这个商品旋转半圈，露出侧面厚度，再倒下。你说做好了，但我没看到侧面的素材。我刚学前端，帮我说明现在做到了什么，下一步怎么做，别给我一整套课程。

## 已提供的资源清单

| 文件 | 已知内容 |
| --- | --- |
| `public/item-front.png` | 正面静态视图，透明背景 |
| `public/item-back.png` | 背面静态视图，透明背景 |

没有侧面视图、3D 模型或连续旋转帧。

## 当前实现

```jsx
<div className={phase === 'success' ? 'item turn' : 'item'}>
  <img src={phase === 'settled' ? '/item-back.png' : '/item-front.png'} />
</div>
```

```css
.turn { animation: turn .7s both; }
@keyframes turn {
  from { transform: translate(0, 0) rotate(0); }
  to { transform: translate(-60px, 40px) rotate(-170deg) scaleY(.2); }
}
```

已知：构建通过；还没有用户确认过的连续动画。没有授权付费图像生成、网络下载或部署。
