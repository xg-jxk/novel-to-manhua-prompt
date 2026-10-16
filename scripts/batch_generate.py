#!/usr/bin/env python3
"""
批量生成漫剧镜头提示词
读取分镜表 CSV + 角色卡 JSON，输出可直接复制到即梦/LiblibAI/可灵 的提示词清单。

用法：
    # 默认（即梦/可灵 自然语言长句格式）
    python batch_generate.py storyboard.csv characters.json -o prompts.md -s 甜宠

    # LiblibAI / SD 关键词格式
    python batch_generate.py storyboard.csv characters.json -o prompts.md -s 古风 --platform liblib

CSV 格式（分镜表，字段均可向后兼容旧版）：
    shot_id, scene_id, shot_type, camera_move, view_angle, action, scene_desc, dialogue, duration, mood, characters
    001, cafe, 远景, 固定, 平视, , 夜晚城市天际线, 旁白：..., 5, 孤独, ""
    002, cafe, 中近景, 缓慢推近, 平视, 低头吹咖啡, 苏晚坐在咖啡馆靠窗位置, 无, 4, 温柔, 苏晚

JSON 格式（角色卡，支持新格式与旧 appearance 字段自动兼容）：
    {
      "苏晚": {
        "age": "25岁左右",
        "gender": "女",
        "face_lock": "杏仁眼，鹅蛋脸，皮肤白皙，左眼下方有一颗小泪痣",
        "hair_lock": "黑色长直发，齐刘海，发尾自然微卷",
        "body_lock": "身材纤细，身高165cm左右",
        "outfit": "米白色针织衫，浅蓝色牛仔裤，白色帆布鞋",
        "style": "韩漫美女脸，唯美厚涂风"
      }
    }
"""

import csv
import json
import argparse
from pathlib import Path


# ========== 题材风格后缀（正向画风词） ==========
STYLE_SUFFIXES = {
    "甜宠": "唯美韩漫风格，厚涂质感，皮肤通透细腻，柔和暖光，浅景深，浪漫氛围",
    "爽文": "国漫半写实风格，硬朗线条，高对比度电影感，侧逆光勾勒轮廓，冷峻色调",
    "悬疑": "写实电影感，低调照明，大面积阴影，冷色调，低饱和度，悬疑压抑氛围，胶片颗粒感",
    "古风": "国风水墨仙侠风格，飘逸唯美，衣袂飘飘，丁达尔光效，仙气缭绕，淡彩水墨质感",
    "都市": "都市写实韩漫风格，精致干练，现代都市场景，干净构图，自然光线，高级感色调",
    "校园": "日系动漫风格，赛璐璐上色，清新明亮，青春校园感，阳光洒落，治愈氛围",
}

# ========== mood → 光影氛围映射 ==========
MOOD_LIGHTING = {
    "温柔": "柔和侧逆光，暖金色调，发丝边缘轮廓光，浅景深",
    "温柔思念": "柔和侧逆光，暖金色调，发丝边缘轮廓光，浅景深",
    "甜蜜": "暖光，柔和漫射，浅景深，逆光发丝金边",
    "感伤": "阴天柔光，灰蓝色调，低饱和，窗外漫射光",
    "悲伤": "阴天柔光，灰蓝色调，低饱和，雨水反光",
    "孤独": "冷色调低调照明，大面积阴影，单点路灯光源，水洼倒影",
    "意外": "硬光侧打，明暗对比，半明半暗的脸部光影",
    "怔住": "侧光勾勒轮廓，半张脸隐入阴影，高对比",
    "震惊": "硬光打在面部，瞳孔高光，明暗对比强烈，半张脸隐入阴影",
    "暧昧": "暖黄烛光，浅景深，背景光斑虚化，空气中细微光点",
    "暧昧拉扯": "暖黄室内光，浅景深，窗外冷色雨景做冷暖对比",
    "紧张": "硬光，高对比度，冷色调，手持感",
    "悬疑": "低调照明，单光源，大面积阴影，冷色调，局部打光",
    "爽感": "低角度硬光，轮廓光勾勒，高对比度，电影感",
    "霸气": "低角度仰拍硬光，侧逆光勾勒轮廓，冷峻色调",
    "治愈": "晴天自然光，树影斑驳，高明度，柔和",
    "日常": "自然室内光，柔和漫射，干净构图",
}
DEFAULT_LIGHTING = "自然光线，柔和氛围光"

# ========== 负面提示词分层 ==========
BASE_NEGATIVE = (
    "低质量, 模糊, 分辨率低, 噪点, 水印, 文字, 签名, logo, 边框, "
    "多余物体, 残缺, 崩坏, 解剖错误"
)
FACE_NEGATIVE = "面部崩坏, 五官变形, 眼睛不对称, 斗鸡眼, 嘴歪, 脸歪, 双下巴, 表情狰狞"
HAND_NEGATIVE = "多余的手指, 手指缺失, 手指畸形, 六指, 融合的手指, 手臂过长, 多余的手臂"

# 按题材追加负面词
STYLE_NEGATIVE = {
    "甜宠": "恐怖, 血腥, 扭曲表情, 过度卡通, 幼态, Q版",
    "爽文": "幼态, Q版, 可爱风格, 低幼画风",
    "悬疑": "明亮, 鲜艳色彩, 可爱风格, 卡通, 过度饱和",
    "古风": "现代服装, 手机, 汽车, 高楼大厦, 电子产品, 现代物品",
    "都市": "古装, 古风, 古代建筑, 古代物品",
    "校园": "写实照片感, 真人质感, 3D渲染, 过度成熟",
}

# ========== 运镜映射（即梦/可灵友好的自然语言） ==========
CAMERA_MAP = {
    "推": "镜头缓慢向前推进，逐渐聚焦",
    "缓慢推近": "镜头缓慢向前推进，逐渐聚焦到角色面部",
    "拉": "镜头向后拉远，展现整个环境",
    "缓慢拉远": "镜头缓慢向后拉远，展现环境全貌",
    "摇": "镜头缓慢左右摇动",
    "横摇": "镜头从左向右缓慢摇动",
    "移": "镜头缓慢横向移动",
    "跟": "镜头跟随角色移动，保持角色在画面中心",
    "环绕": "镜头围绕角色缓慢环绕",
    "升": "镜头缓慢上升，从平视变为俯视",
    "降": "镜头缓慢下降",
    "手持": "手持摄影，轻微晃动，增加临场感",
    "固定": "镜头固定不动",
    "骤停": "镜头突然静止，时间凝固感，画面瞬间安静",
    "慢动作": "镜头慢动作，动作缓慢拉长",
}

# ========== 景别分组：决定角色描述裁剪粒度 ==========
CLOSE_UP_TYPES = {"特写", "大特写", "面部特写", "眼部特写", "眼部大特写"}  # 只留面部
MEDIUM_TYPES = {"近景", "中近景", "中景"}  # 留面部+服装上半身
WIDE_TYPES = {"全景", "中全景", "远景", "大远景", "环境镜头"}  # 全量


# ========== 加载函数 ==========
def load_characters(json_path: str) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_storyboard(csv_path: str) -> list:
    rows = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k.strip(): (v or "").strip() for k, v in row.items()})
    return rows


# ========== 角色描述裁剪（按景别） ==========
def _normalize_char(name: str, info: dict) -> dict:
    """把旧格式 appearance 拆成 face/hair/body，统一成新结构。"""
    if "face_lock" in info:  # 已经是新格式
        return info
    # 旧格式兼容：从 appearance 粗拆
    appearance = info.get("appearance", "")
    return {
        "age": info.get("age", ""),
        "gender": info.get("gender", ""),
        "face_lock": appearance,  # 旧版无法精确拆，全量留给特写
        "hair_lock": "",
        "body_lock": "",
        "outfit": info.get("outfit", ""),
        "style": info.get("style", ""),
        "name": name,
    }


def describe_character(name: str, info: dict, shot_type: str, position: str = "") -> str:
    """
    按景别裁剪角色描述。
    position: "画面左侧" / "画面右侧" / "画面前景" 等空间锚定，可选。
    """
    info = _normalize_char(name, info)
    parts = []

    # 年龄感
    age = info.get("age", "")
    gender = info.get("gender", "")
    head = ""
    if gender and age:
        head = f"{gender}性，{age}"
    elif age:
        head = age
    elif gender:
        head = f"{gender}性"

    if shot_type in CLOSE_UP_TYPES:
        # 特写：只留发型 + 面部
        desc_bits = [b for b in [head, info.get("hair_lock", ""), info.get("face_lock", "")] if b]
    elif shot_type in MEDIUM_TYPES:
        # 中近景：面部 + 上半身服装
        desc_bits = [b for b in [head, info.get("face_lock", ""), f"穿{info['outfit']}" if info.get("outfit") else ""] if b]
    else:
        # 全景/远景：全量外貌 + 体型 + 服装
        desc_bits = [b for b in [
            head, info.get("hair_lock", ""), info.get("face_lock", ""),
            info.get("body_lock", ""), f"穿{info['outfit']}" if info.get("outfit") else ""
        ] if b]

    desc = "，".join(desc_bits)
    if position:
        desc = f"{position}，{desc}"
    return desc


def describe_unknown_character(name: str, position: str = "") -> str:
    """角色卡里没有的路人，给一个中性描述，不瞎编外貌。"""
    desc = f"背景人物「{name}」，轮廓柔和，非焦点"
    if position:
        desc = f"{position}，{desc}"
    return desc


def assemble_characters(shot: dict, characters: dict) -> str:
    """多角色拼接，加空间锚定。"""
    raw = shot.get("characters", "")
    names = [n.strip() for n in raw.split(",") if n.strip()]
    if not names:
        return ""

    shot_type = shot.get("shot_type", "中景")
    descs = []

    if len(names) == 1:
        name = names[0]
        if name in characters:
            descs.append(describe_character(name, characters[name], shot_type))
        else:
            descs.append(describe_unknown_character(name))
    else:
        # 多角色：左右站位锚定
        positions = ["画面左侧", "画面右侧", "画面中间", "画面左后", "画面右后"]
        for i, name in enumerate(names):
            pos = positions[i] if i < len(positions) else ""
            if name in characters:
                descs.append(describe_character(name, characters[name], shot_type, position=pos))
            else:
                descs.append(describe_unknown_character(name, position=pos))

    return "；".join(descs)


# ========== 场景背景复用（同 scene_id 分组） ==========
def group_scenes(shots: list) -> dict:
    """按 scene_id 分组，记录每个 scene_id 第一次出现的 scene_desc。"""
    seen = {}
    for shot in shots:
        sid = shot.get("scene_id", "").strip()
        if not sid:
            continue
        if sid not in seen:
            seen[sid] = shot.get("scene_desc", "")
    return seen


def get_scene_desc(shot: dict, scene_first_desc: dict) -> str:
    """同 scene_id 第二次起，自动复用首镜头的环境描述。特写/大特写不继承（背景虚化）。"""
    sid = shot.get("scene_id", "").strip()
    this_desc = shot.get("scene_desc", "").strip()
    shot_type = shot.get("shot_type", "")

    # 用户明确写了环境描述就用用户的
    if this_desc:
        return this_desc
    # 特写/大特写：背景完全虚化，不堆环境描述
    if shot_type in CLOSE_UP_TYPES:
        return ""
    if not sid or sid not in scene_first_desc:
        return ""
    if shot.get("shot_id") == _first_shot_id_of_scene(sid, scene_first_desc):
        return scene_first_desc[sid]
    return f"环境同前（{scene_first_desc[sid]}）"


_first_scene_seen = {}
def _first_shot_id_of_scene(sid: str, scene_first_desc: dict) -> str:
    # scene_first_desc 是按出现顺序构造的，这里简单返回一个标记
    # 真正判断由 group 顺序决定，这里用一个外部字典缓存
    return _first_scene_seen.get(sid, "")


# ========== 出图提示词组装 ==========
def build_image_prompt(shot: dict, characters: dict, style: str,
                       scene_first_desc: dict, platform: str = "jimeng") -> str:
    shot_type = shot.get("shot_type", "中景")
    view_angle = shot.get("view_angle", "").strip()
    action = shot.get("action", "").strip()

    # 1. 画幅
    parts = ["竖屏构图，9:16比例"]

    # 2. 景别 + 视角
    shot_bits = [shot_type]
    if view_angle:
        shot_bits.append(f"{view_angle}角度")
    parts.append("，".join(shot_bits))

    # 3. 角色锁词（按景别裁剪）
    char_str = assemble_characters(shot, characters)
    if char_str:
        parts.append(char_str)

    # 4. 动作表情（独立层）
    if action:
        parts.append(action)

    # 5. 场景环境
    scene_desc = get_scene_desc(shot, scene_first_desc)
    if scene_desc:
        parts.append(scene_desc)

    # 6. 光影氛围（按 mood 动态）
    mood = shot.get("mood", "").strip()
    lighting = MOOD_LIGHTING.get(mood, DEFAULT_LIGHTING)
    parts.append(lighting)

    # 7. 画风质感（题材后缀）
    parts.append(STYLE_SUFFIXES.get(style, STYLE_SUFFIXES["都市"]))

    # 8. 质量词（按平台）
    if platform == "liblib":
        parts.append("masterpiece, best quality, highly detailed, 8k, ultra-detailed")
    else:
        parts.append("高清细节，电影质感，精致渲染")

    # 拼接：jimeng 用中文逗号长句，liblib 用英文逗号关键词
    if platform == "liblib":
        return ", ".join([p for p in parts if p])
    return "，".join([p for p in parts if p])


# ========== 出视频提示词组装 ==========
def build_video_prompt(shot: dict, platform: str = "jimeng") -> str:
    camera = shot.get("camera_move", "固定镜头")
    scene = shot.get("scene_desc", "").strip()
    action = shot.get("action", "").strip()
    mood = shot.get("mood", "").strip()

    camera_desc = CAMERA_MAP.get(camera, f"镜头{camera}")
    mood_word = MOOD_LIGHTING.get(mood, mood or "")

    parts = [camera_desc]
    if action:
        parts.append(f"角色{action}")
    if scene:
        parts.append(scene)
    if mood_word:
        parts.append(f"{mood}氛围")
    # 防崩约束：图生视频最关键的稳定性提示
    parts.append("人物面部保持稳定，肢体动作幅度小，背景不发生突变，无跳帧")

    if platform == "liblib":
        return ", ".join([p for p in parts if p])
    return "，".join([p for p in parts if p])


# ========== 动态负面提示词 ==========
def build_negative(shot_type: str, style: str) -> str:
    parts = [BASE_NEGATIVE]
    if shot_type in CLOSE_UP_TYPES:
        parts.append(FACE_NEGATIVE)
    if shot_type in MEDIUM_TYPES or shot_type in WIDE_TYPES:
        parts.append(HAND_NEGATIVE)
    if style in STYLE_NEGATIVE:
        parts.append(STYLE_NEGATIVE[style])
    return ", ".join(parts)


# ========== 输出 Markdown ==========
def generate_output(shots: list, characters: dict, style: str, platform: str) -> str:
    global _first_scene_seen
    _first_scene_seen = {}
    scene_first_desc = {}
    for shot in shots:
        sid = shot.get("scene_id", "").strip()
        if sid and sid not in scene_first_desc:
            scene_first_desc[sid] = shot.get("scene_desc", "")
            _first_scene_seen[sid] = shot.get("shot_id", "")

    lines = ["# 漫剧镜头提示词清单\n"]
    lines.append(f"> 题材风格：{style} | 平台格式：{platform} | 镜头数：{len(shots)}\n")
    lines.append("---\n")

    # 角色卡汇总
    lines.append("## 角色卡汇总\n")
    for name, info in characters.items():
        info = _normalize_char(name, info)
        lines.append(f"### {name}")
        if info.get("age") or info.get("gender"):
            lines.append(f"- 基础设定：{info.get('gender','')} {info.get('age','')}".strip())
        if info.get("face_lock"):
            lines.append(f"- 面部锁词：{info['face_lock']}")
        if info.get("hair_lock"):
            lines.append(f"- 发型锁词：{info['hair_lock']}")
        if info.get("body_lock"):
            lines.append(f"- 体型锁词：{info['body_lock']}")
        if info.get("outfit"):
            lines.append(f"- 服装：{info['outfit']}")
        if info.get("style"):
            lines.append(f"- 风格：{info['style']}\n")

    lines.append("---\n")
    lines.append("## 逐镜头提示词\n")

    warnings = []
    for shot in shots:
        sid = shot.get("shot_id", "???")
        lines.append(f"### 镜头 {sid}\n")
        lines.append(
            f"**景别**：{shot.get('shot_type','')} | "
            f"**运镜**：{shot.get('camera_move','')} | "
            f"**视角**：{shot.get('view_angle','平视')} | "
            f"**时长**：{shot.get('duration','')}s | "
            f"**情绪**：{shot.get('mood','')}\n"
        )
        if shot.get("dialogue"):
            lines.append(f"**台词/旁白**：{shot['dialogue']}\n")

        # 出图
        img = build_image_prompt(shot, characters, style, scene_first_desc, platform)
        lines.append("**【出图提示词】**（复制到正向提示词框）\n")
        lines.append(f"```\n{img}\n```\n")
        if len(img) > 250:
            warnings.append(f"镜头{sid} 出图提示词 {len(img)} 字，超过 250 字预算，建议精简环境描述")

        # 出视频
        vid = build_video_prompt(shot, platform)
        lines.append("**【出视频提示词】**（图生视频模式）\n")
        lines.append(f"```\n{vid}\n```\n")
        if len(vid) > 150:
            warnings.append(f"镜头{sid} 视频提示词 {len(vid)} 字，超过 150 字预算")

        # 负面
        neg = build_negative(shot.get("shot_type", ""), style)
        lines.append("**【负面提示词】**\n")
        lines.append(f"```\n{neg}\n```\n")
        lines.append("---\n")

    if warnings:
        lines.append("\n## ⚠️ 长度预算警告\n")
        for w in warnings:
            lines.append(f"- {w}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="批量生成漫剧镜头提示词")
    parser.add_argument("storyboard", help="分镜表 CSV 文件路径")
    parser.add_argument("characters", help="角色卡 JSON 文件路径")
    parser.add_argument("-o", "--output", default="prompts.md", help="输出文件路径（默认 prompts.md）")
    parser.add_argument("-s", "--style", default="都市",
                        choices=list(STYLE_SUFFIXES.keys()), help="题材风格（默认都市）")
    parser.add_argument("--platform", default="jimeng", choices=["jimeng", "liblib"],
                        help="提示词格式：jimeng=自然语言长句（即梦/可灵），liblib=逗号关键词（SD/Liblib）")

    args = parser.parse_args()
    shots = load_storyboard(args.storyboard)
    characters = load_characters(args.characters)
    output = generate_output(shots, characters, args.style, args.platform)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"✅ 已生成 {len(shots)} 个镜头的提示词（{args.platform} 格式，{args.style} 风格）→ {args.output}")


if __name__ == "__main__":
    main()
