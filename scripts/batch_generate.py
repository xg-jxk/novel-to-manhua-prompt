#!/usr/bin/env python3
"""
批量生成漫剧镜头提示词
读取分镜表 CSV + 角色卡 JSON，输出可直接复制到即梦/LiblibAI 的提示词清单。

用法：
    python batch_generate.py storyboard.csv characters.json -o prompts.md

CSV 格式（分镜表）：
    shot_id, shot_type, camera_move, scene_desc, dialogue, duration, mood, characters
    001, 远景, 固定, 夜晚城市天际线, 旁白：... , 5, 悬疑, ""

JSON 格式（角色卡）：
    {
      "苏晚": {
        "appearance": "年轻女性，约22岁，黑色长直发，齐刘海，丹凤眼，鹅蛋脸，皮肤白皙，左眼下方有一颗小泪痣，身材纤细",
        "outfit": "米白色针织衫，浅蓝色牛仔裤，白色帆布鞋",
        "style": "韩漫美女脸，唯美厚涂风"
      }
    }
"""

import csv
import json
import argparse
from pathlib import Path


# 画风后缀映射（根据题材快速选择）
STYLE_SUFFIXES = {
    "甜宠": "唯美韩漫风格，厚涂质感，皮肤通透细腻，柔和暖光，浅景深，浪漫氛围",
    "爽文": "国漫半写实风格，硬朗线条，高对比度电影感，侧逆光勾勒轮廓，冷峻色调",
    "悬疑": "写实电影感，低调照明，大面积阴影，冷色调，低饱和度，悬疑压抑氛围，胶片颗粒感",
    "古风": "国风水墨仙侠风格，飘逸唯美，衣袂飘飘，丁达尔光效，仙气缭绕，淡彩水墨质感",
    "都市": "都市写实韩漫风格，精致干练，现代都市场景，干净构图，自然光线，高级感色调",
    "校园": "日系动漫风格，赛璐璐上色，清新明亮，青春校园感，阳光洒落，治愈氛围",
}

# 通用负面提示词基线
BASE_NEGATIVE = (
    "低质量, 模糊, 分辨率低, 噪点, 水印, 文字, 签名, logo, 边框, "
    "多余物体, 残缺, 崩坏, 解剖错误, "
    "面部崩坏, 五官变形, 眼睛不对称, 斗鸡眼, "
    "多余的手指, 手指缺失, 手指畸形, 六指, 融合的手指"
)


def load_characters(json_path: str) -> dict:
    """加载角色卡 JSON"""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_storyboard(csv_path: str) -> list[dict]:
    """加载分镜表 CSV"""
    rows = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def build_image_prompt(shot: dict, characters: dict, style: str) -> str:
    """拼接单镜头出图提示词"""
    char_names = [c.strip() for c in shot.get("characters", "").split(",") if c.strip()]

    # 拼接角色描述
    char_descs = []
    for name in char_names:
        if name in characters:
            c = characters[name]
            char_descs.append(f"{c['appearance']}，穿{c['outfit']}")
        else:
            char_descs.append(name)

    char_str = "，".join(char_descs) if char_descs else ""

    # 组装完整提示词
    parts = [
        "竖屏构图，9:16比例",
        shot.get("shot_type", "中景"),
        char_str,
        shot.get("scene_desc", ""),
        STYLE_SUFFIXES.get(style, STYLE_SUFFIXES["都市"]),
        "masterpiece, best quality, highly detailed, 8k",
    ]

    return "，".join([p for p in parts if p])


def build_video_prompt(shot: dict) -> str:
    """拼接单镜头视频提示词"""
    camera = shot.get("camera_move", "固定镜头")
    scene = shot.get("scene_desc", "")
    mood = shot.get("mood", "")

    camera_map = {
        "推": "镜头缓慢向前推进",
        "拉": "镜头向后拉远",
        "摇": "镜头缓慢摇动",
        "移": "镜头缓慢移动",
        "跟": "镜头跟随角色移动",
        "环绕": "镜头围绕角色缓慢环绕",
        "升": "镜头缓慢上升",
        "降": "镜头缓慢下降",
        "手持": "手持摄影，轻微晃动",
        "固定": "镜头固定不动",
    }

    camera_desc = camera_map.get(camera, f"镜头{camera}")

    return f"{camera_desc}，{scene}，{mood}氛围，动作自然流畅"


def generate_output(shots: list[dict], characters: dict, style: str) -> str:
    """生成完整输出 Markdown"""
    lines = ["# 漫剧镜头提示词清单\n"]
    lines.append(f"> 题材风格：{style}\n")
    lines.append("---\n")

    # 角色卡汇总
    lines.append("## 角色卡汇总\n")
    for name, info in characters.items():
        lines.append(f"### {name}")
        lines.append(f"- 外貌：{info['appearance']}")
        lines.append(f"- 服装：{info['outfit']}\n")

    lines.append("---\n")

    # 逐镜头提示词
    lines.append("## 逐镜头提示词\n")

    for shot in shots:
        sid = shot.get("shot_id", "???")
        lines.append(f"### 镜头 {sid}\n")
        lines.append(f"**景别**：{shot.get('shot_type', '')} | **运镜**：{shot.get('camera_move', '')} | **时长**：{shot.get('duration', '')}s\n")

        if shot.get("dialogue"):
            lines.append(f"**台词/旁白**：{shot['dialogue']}\n")

        # 出图提示词
        img_prompt = build_image_prompt(shot, characters, style)
        lines.append("**【出图提示词】**（复制到即梦/LiblibAI 正向提示词框）\n")
        lines.append(f"```\n{img_prompt}\n```\n")

        # 视频提示词
        vid_prompt = build_video_prompt(shot)
        lines.append("**【出视频提示词】**（图生视频模式下使用）\n")
        lines.append(f"```\n{vid_prompt}\n```\n")

        # 负面提示词
        lines.append("**【负面提示词】**（复制到负面提示词框）\n")
        lines.append(f"```\n{BASE_NEGATIVE}\n```\n")

        lines.append("---\n")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="批量生成漫剧镜头提示词")
    parser.add_argument("storyboard", help="分镜表 CSV 文件路径")
    parser.add_argument("characters", help="角色卡 JSON 文件路径")
    parser.add_argument("-o", "--output", default="prompts.md", help="输出文件路径（默认 prompts.md）")
    parser.add_argument(
        "-s", "--style",
        default="都市",
        choices=list(STYLE_SUFFIXES.keys()),
        help="题材风格（默认都市）",
    )

    args = parser.parse_args()

    shots = load_storyboard(args.storyboard)
    characters = load_characters(args.characters)

    output = generate_output(shots, characters, args.style)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"✅ 已生成 {len(shots)} 个镜头的提示词 → {args.output}")


if __name__ == "__main__":
    main()
