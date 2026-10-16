# LiblibAI 负面提示词库

> Liblib 对负面词响应强，**必加**。按景别和动作类型追加。

---

## 通用基线（所有镜头必加）

```
(face swap:1.4), (morphing:1.3), (identity drift:1.3),
(extra fingers:1.3), (bad hands:1.3), (deformed limbs:1.2),
(background change:1.2), (jump cut:1.2), (frame flickering:1.2),
(low quality:1.2), (blurry:1.1), (watermark:1.1), (text:1.1)
```

---

## 按景别追加

| 景别 | 追加负面词 |
|------|-----------|
| 特写 / 大特写 | `(asymmetric eyes:1.2), (cross-eyed:1.2), (extra eyes:1.3), (crooked mouth:1.2)` |
| 中景 / 全景 | `(extra arms:1.3), (extra legs:1.3), (wrong posture:1.1)` |
| 多人同框 | `(extra characters:1.2), (character merging:1.2)` |

---

## 按动作类型追加

| 动作类型 | 追加负面词 |
|----------|-----------|
| 打斗/飞踢 | `(foot clipping:1.3), (body morphing:1.2), (physics error:1.2), (limb distortion:1.3)` |
| 拥抱/握手 | `(hand interpenetration:1.3), (fused fingers:1.2)` |
| 奔跑 | `(foot sliding:1.2), (moonwalk:1.1)` |
| 哭戏 | `(overacting:0.9), (ugly crying:0.9)` |

---

## 按题材追加

| 题材 | 追加负面词 |
|------|-----------|
| 现代都市 | `(ancient clothing:1.2), (traditional architecture:1.1)` |
| 甜宠言情 | `(horror:1.2), (gore:1.2), (ugly expression:1.1)` |
| 悬疑惊悚 | `(bright colors:1.1), (cute style:1.2)` |
| 爽文动作 | `(cute style:1.2), (chibi:1.3), (low-poly:1.2)` |
