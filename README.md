# Novel to Manhua Prompt

> 输入小说原文，输出可直接投喂给**即梦 / LiblibAI / 可灵**等平台的漫剧分镜 + 标准化提示词。
> 为 AI 漫剧、竖屏短剧、动态漫工作室提供镜头级生产的「提示词基础设施」。

---

## ✨ 这是什么？

做 AI 漫剧最大的痛点不是模型不行，而是**没有标准化的生产流程**——同一个角色每镜头脸不一样，提示词全靠手感，分镜全凭感觉。

这个 Skill 把漫剧生产的「分镜拆解 → 角色卡设计 → 提示词拼接」整条链路标准化，让你：

- 📖 扔一段小说原文进去，自动拆成专业分镜表
- 🎭 自动生成角色卡，锁词保证全片角色一致
- 🎨 输出可直接复制到即梦/LiblibAI 的出图 + 出视频提示词
- ⚡ 批量生产时，用脚本一键生成整集提示词清单

---

## 🚀 快速开始

### 方式一：直接和 AI 对话使用

把 `SKILL.md` 整个文件丢给你的 AI（豆包 / GPT / Claude 都行），然后说：

> 这是我的漫剧生产 skill，现在帮我把这段小说拆成分镜并生成提示词：
>
> 【粘贴你的小说原文】

AI 就会按照 skill 里的规范，输出角色卡 + 分镜表 + 逐镜头提示词。

### 方式二：作为 Claude / Cursor Skill 加载

把整个文件夹放到你的 skills 目录下，AI 会自动在你需要时调用。

### 方式三：用脚本批量生成

如果你已经有分镜表 CSV 和角色卡 JSON：

```bash
# 默认即梦/可灵格式（自然语言长句）
python scripts/batch_generate.py storyboard.csv characters.json -o prompts.md -s 甜宠

# LiblibAI / Stable Diffusion 格式（逗号关键词 + 英文质量词）
python scripts/batch_generate.py storyboard.csv characters.json -o prompts.md -s 古风 --platform liblib
```

参数说明：
- `storyboard.csv`：分镜表文件（格式见下方）
- `characters.json`：角色卡文件（格式见下方）
- `-o prompts.md`：输出文件路径
- `-s 甜宠`：题材风格（可选：甜宠 / 爽文 / 悬疑 / 古风 / 都市 / 校园）
- `--platform`：提示词格式，`jimeng`（默认，即梦/可灵长句）或 `liblib`（SD 系关键词）

---

## 📁 项目结构

```
novel-to-manhua-prompt/
├── SKILL.md                          # 核心 Skill 定义文件
├── README.md                         # 本文件
├── LICENSE                           # MIT 开源协议
│
├── references/                       # 参考知识库（按需加载）
│   ├── prompt-structure.md           # 即梦/LiblibAI 提示词结构规范
│   ├── shot-language.md              # 镜头语言体系（景别/运镜对照表）
│   ├── character-continuity.md      # 角色一致性规范
│   ├── style-templates.md            # 6大题材风格模板
│   └── negative-prompts.md           # 负面提示词库
│
├── assets/                           # 模板资产
│   ├── storyboard-template.md       # 分镜表模板
│   └── character-sheet-template.md   # 角色卡模板
│
├── scripts/                          # 自动化脚本
│   └── batch_generate.py             # 批量提示词生成器
│
└── examples/                         # 示例
    ├── sample-novel.txt              # 示例小说输入
    └── sample-output.md               # 完整输出示例
```

---

## 🎯 适配平台

| 平台 | 适配程度 | 备注 |
|------|----------|------|
| 即梦 Dreamina | ⭐⭐⭐⭐⭐ | 原生适配，自然语言描述最佳 |
| LiblibAI 哩布哩布 | ⭐⭐⭐⭐ | 关键词式提示词，支持权重语法 |
| 可灵 Kling | ⭐⭐⭐⭐ | 视频提示词直接可用 |
| Midjourney | ⭐⭐⭐ | 需要调整为英文提示词 |
| Stable Diffusion WebUI | ⭐⭐⭐⭐ | 负面提示词直接可用 |

---

## 📋 输入输出示例

**输入**（小说原文）：
> 傍晚的咖啡馆里，苏晚坐在靠窗的位置，双手捧着热拿铁……门口的风铃叮当作响，陆深站在门口……

**输出**（完整交付物）：
1. ✅ 角色卡汇总（苏晚 / 陆深 的外貌锁词 + 服装锁词）
2. ✅ 7 个镜头的分镜表（景别 / 运镜 / 台词 / 时长）
3. ✅ 每个镜头的「出图提示词 + 出视频提示词 + 负面提示词」

完整示例见 [examples/sample-output.md](examples/sample-output.md)。

---

## 🔧 CSV / JSON 格式说明

### 分镜表 CSV 格式

```csv
shot_id,scene_id,shot_type,camera_move,view_angle,action,scene_desc,dialogue,duration,mood,characters
001,cafe,远景,固定,平视,,傍晚街景细雨,旁白：...,4,孤独,
002,cafe,中近景,缓慢推近,平视,低头吹咖啡睫毛低垂,苏晚坐在靠窗位置,无,4,温柔思念,苏晚
003,cafe,大特写,固定,平视,眼睛缓缓睁大瞳孔微震,,无,2,震惊,苏晚
```

字段说明：
- `shot_id`：镜号（三位数）
- `scene_id`：场景组标识，同一场景填同一个值，脚本自动让后续镜头继承首镜头环境描述
- `shot_type`：景别（远景/中景/特写/大特写等）
- `camera_move`：运镜（固定/推/缓慢推近/拉/摇/环绕/手持/骤停等）
- `view_angle`：视角（平视/俯视/仰视/过肩/第一人称），可留空默认平视
- `action`：角色动作表情（具体可视觉化，如「低头吹咖啡，睫毛低垂」）
- `scene_desc`：环境描述，同场景首镜头写全，后续可留空自动继承
- `dialogue`：台词或旁白
- `duration`：时长（秒）
- `mood`：情绪词，自动匹配光影（温柔/震惊/孤独/暧昧/爽感/悬疑等）
- `characters`：出场角色（多个用英文逗号分隔，顺序决定左右站位）

### 角色卡 JSON 格式（推荐新格式）

```json
{
  "苏晚": {
    "age": "25岁左右",
    "gender": "女",
    "face_lock": "杏仁眼，鹅蛋脸，皮肤白皙，鼻梁小巧，左眼下方一颗小泪痣",
    "hair_lock": "黑色长直发，齐刘海，发尾自然微卷",
    "body_lock": "身材纤细，身高165cm左右",
    "outfit": "燕麦色宽松毛衣，深色牛仔裤，白色帆布鞋",
    "style": "韩漫美女脸，唯美厚涂风"
  }
}
```

脚本会**按景别自动裁剪锁词**：特写只用 face_lock + hair_lock，全景才用全量。旧版 `appearance` 字段也能兼容读取。

---

## 💡 最佳实践

### 角色一致性是第一优先级
1. 先给每个主要角色生成一张**定妆照**（正面、半身、光线均匀）
2. 后续每个镜头都用平台的「角色参考 / 图生图」功能锁定这张脸
3. 参考图权重建议 0.5-0.7

### 提示词生成原则
- 角色描述**一字不改**地从角色卡复制，不要自由发挥
- 每个镜头只用**一种运镜**，不要又推又摇又环绕
- 竖屏短剧平均镜头时长 3-6 秒，前 3 秒必须有钩子

### 批量生产流程
1. 小说 → AI 拆成分镜表（Markdown）
2. 分镜表 → 整理成 CSV
3. 角色卡 → 写成 JSON
4. 跑脚本 → 一键生成整集提示词清单
5. 人工微调 → 批量投喂平台

---

## 🤝 贡献

欢迎提 Issue 和 PR！你可以：

- 补充更多题材的风格模板
- 增加更多平台的适配说明
- 优化脚本功能
- 提交优秀的示例片段

---

## 📄 License

[MIT](LICENSE)

自由使用，商用免费，只需保留版权声明。
