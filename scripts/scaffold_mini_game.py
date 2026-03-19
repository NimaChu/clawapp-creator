#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

TEMPLATES = {
    "orbit-tap": {
        "dir": "starter-mini-game",
        "default_category": "小游戏",
        "default_description": "点击移动中的星球，45 秒内拿到最高分。",
        "default_features": ["轻量、即开即玩的点击得分小游戏"],
        "default_tags": ["Game", "HTML5", "Starter"],
        "default_stack": ["HTML", "CSS", "JavaScript"],
        "default_steps": ["打开应用", "点击开始", "完成一局游戏"],
        "default_model_category": "none",
    },
    "memory-flip": {
        "dir": "starter-memory-flip",
        "default_category": "小游戏",
        "default_description": "翻开卡片配对，在最短时间内完成整局记忆挑战。",
        "default_features": ["经典翻牌配对玩法", "适合二次改造成主题小游戏"],
        "default_tags": ["Game", "Puzzle", "Memory"],
        "default_stack": ["HTML", "CSS", "JavaScript"],
        "default_steps": ["打开应用", "开始翻牌", "完成全部配对"],
        "default_model_category": "none",
    },
    "focus-timer": {
        "dir": "starter-focus-timer",
        "default_category": "工具",
        "default_description": "一个轻量专注计时器，带任务标题、番茄钟和完成记录。",
        "default_features": ["适合上传的静态效率工具", "可快速改造成主题型实用应用"],
        "default_tags": ["Utility", "Timer", "Productivity"],
        "default_stack": ["HTML", "CSS", "JavaScript"],
        "default_steps": ["输入任务标题", "开始专注", "记录完成结果"],
        "default_model_category": "none",
    },
    "ai-rewriter": {
        "dir": "starter-ai-rewriter",
        "default_category": "AI工具",
        "default_description": "输入一句草稿，调用平台模型生成更自然的表达版本。",
        "default_features": ["已接入平台统一模型接口", "适合改造成文案、灵感或对话类应用"],
        "default_tags": ["AI", "Text", "Writing"],
        "default_stack": ["HTML", "CSS", "JavaScript", "Platform LLM API"],
        "default_steps": ["输入原始文本", "点击生成", "查看润色结果"],
        "default_model_category": "text",
    },
    "ocr-tool": {
        "dir": "starter-ocr",
        "default_category": "AI工具",
        "default_description": "上传图片并调用平台多模态模型，识别文字与图像内容。",
        "default_features": ["支持 OCR 与图片内容分析", "已接入平台多模态模型接口"],
        "default_tags": ["AI", "OCR", "Vision"],
        "default_stack": ["HTML", "CSS", "JavaScript", "Platform Multimodal API"],
        "default_steps": ["上传图片", "点击开始分析", "查看识别结果"],
        "default_model_category": "multimodal",
    },
}


def slugify(value: str) -> str:
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9-]+", "-", value.strip().lower().replace("_", "-").replace(" ", "-")))


def replace_in_file(path: Path, replacements: dict[str, str]) -> None:
    content = path.read_text(encoding="utf-8")
    for source, target in replacements.items():
        content = content.replace(source, target)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a starter static mini-game for Nima Tech Space.")
    parser.add_argument("--out", required=True, help="Output project directory")
    parser.add_argument("--name", required=True, help="App name")
    parser.add_argument("--slug", help="App slug, defaults to slugified name")
    parser.add_argument("--description", required=True, help="One-line app description")
    parser.add_argument("--author", default="Your Name", help="Author name")
    parser.add_argument("--category", help="Category label")
    parser.add_argument("--template", choices=sorted(TEMPLATES.keys()), default="orbit-tap", help="Starter template")
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    template = TEMPLATES[args.template]
    template_dir = skill_dir / "assets" / template["dir"]
    manifest_template_path = skill_dir / "assets" / "manifest.example.json"
    readme_template_path = skill_dir / "assets" / "README.template.md"

    out_dir = Path(args.out).expanduser().resolve()
    app_dir = out_dir / "app"
    assets_dir = out_dir / "assets"
    slug = slugify(args.slug or args.name)

    out_dir.mkdir(parents=True, exist_ok=True)
    if any(out_dir.iterdir()):
      raise SystemExit(f"output directory is not empty: {out_dir}")

    shutil.copytree(template_dir, app_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)
    if args.template == "ocr-tool":
        shutil.copy(template_dir / "ocr-icon.svg", assets_dir / "ocr-icon.svg")
        shutil.copy(template_dir / "ocr-thumb.svg", assets_dir / "ocr-thumb.svg")

    replacements = {
        "__APP_NAME__": args.name,
        "__APP_DESCRIPTION__": args.description,
        "__APP_SLUG__": slug,
    }

    for path in app_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".html", ".css", ".js", ".json", ".md"}:
            replace_in_file(path, replacements)

    manifest = json.loads(manifest_template_path.read_text(encoding="utf-8"))
    manifest.update({
        "id": slug,
        "slug": slug,
        "name": args.name,
        "description": args.description,
        "category": args.category or template["default_category"],
        "author": {
            "name": args.author,
            "url": "",
        },
        "links": {
            "github": "",
            "homepage": "",
        },
        "thumbnail": "assets/ocr-thumb.svg" if args.template == "ocr-tool" else "",
        "icon": "assets/ocr-icon.svg" if args.template == "ocr-tool" else "",
        "screenshots": ["assets/ocr-thumb.svg"] if args.template == "ocr-tool" else [],
        "features": template["default_features"],
        "tags": template["default_tags"],
        "techStack": template["default_stack"],
        "usageSteps": template["default_steps"],
        "modelCategory": template["default_model_category"],
    })

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    readme = readme_template_path.read_text(encoding="utf-8")
    readme = readme.replace("{{APP_NAME}}", args.name)
    readme = readme.replace("{{ONE_LINE_DESCRIPTION}}", args.description)
    readme = readme.replace("{{TEMPLATE_NAME}}", args.template)
    (out_dir / "README.md").write_text(readme, encoding="utf-8")

    print(f"Scaffolded project: {out_dir}")
    print(f"Package slug: {slug}")
    print(f"Starter template: {args.template}")
    print("Recommended next step: add assets/thumbnail.png, assets/icon.png, and one screenshot for a better store listing.")
    print("If you skip them, CLAWSPACE will still show a default generated cover.")
    print("Next step: build or customize the app under app/, then package it with build_nima_package.py")


if __name__ == "__main__":
    main()
