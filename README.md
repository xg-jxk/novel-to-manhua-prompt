# Novel to Manhua Prompt

输入小说/网文原文，6 维配置卡强制选择后，输出适配的视频生成提示词清单。

## 快速开始

1. 把小说原文扔给 AI
2. AI 会按 6 维配置卡问你（不选就用默认）
3. 直接输出视频提示词清单，复制到 LiblibAI / 即梦 就能用

## 6 维配置

| 维度 | 默认 | 选项 |
|------|------|------|
| 平台 | LiblibAI | 即梦 / LiblibAI |
| 题材 | 自动识别 | 穿书反派恋爱养成 / 其他 |
| 画风 | 3D次时代建模 | 日系二次元 / 韩漫厚涂 / 写实电影感 |
| 画幅 | 16:9 | 9:16 / 1:1 |
| 甜虐配比 | 甜虐交织 | 纯甜宠 / 虐心为主 |
| 旁白模式 | 内心OS | 纯对话 / 系统音+OS |

## 目录结构

```
references/
├── jimeng/        即梦平台规范
├── liblib/        LiblibAI 平台规范
├── genres/        题材模板（可扩展）
└── styles/        画风模板（可扩展）
```

## 扩展方式

- 加新平台：`references/` 下建新目录，放 video-prompts.md / negative-prompts.md / examples.md
- 加新题材：`references/genres/` 丢新 md
- 加新画风：`references/styles/` 丢新 md

详见 `references/genres/README.md` 和 `references/styles/README.md`。
