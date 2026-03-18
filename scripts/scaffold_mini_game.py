#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


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
    parser.add_argument("--category", default="小游戏", help="Category label")
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    template_dir = skill_dir / "assets" / "starter-mini-game"
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

    replacements = {
        "Orbit Tap": args.name,
        "点击移动中的星球，45 秒内拿到最高分。": args.description,
    }

    replace_in_file(app_dir / "index.html", replacements)

    manifest = json.loads(manifest_template_path.read_text(encoding="utf-8"))
    manifest.update({
        "id": slug,
        "slug": slug,
        "name": args.name,
        "description": args.description,
        "category": args.category,
        "author": {
            "name": args.author,
            "url": "",
        },
        "links": {
            "github": "",
            "homepage": "",
        },
        "thumbnail": "",
        "icon": "",
        "screenshots": [],
        "features": ["轻量、即开即玩的静态小游戏"],
        "tags": ["Game", "HTML5", "Starter"],
        "techStack": ["HTML", "CSS", "JavaScript"],
        "usageSteps": ["打开应用", "点击开始", "完成一局游戏"],
        "modelCategory": "none",
    })

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    readme = readme_template_path.read_text(encoding="utf-8")
    readme = readme.replace("{{APP_NAME}}", args.name)
    readme = readme.replace("{{ONE_LINE_DESCRIPTION}}", args.description)
    (out_dir / "README.md").write_text(readme, encoding="utf-8")

    print(f"Scaffolded project: {out_dir}")
    print(f"Package slug: {slug}")
    print("Next step: build or customize the app under app/, then package it with build_nima_package.py")


if __name__ == "__main__":
    main()
