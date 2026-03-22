#!/usr/bin/env python3
from __future__ import annotations

import argparse
import binascii
import json
import re
import shutil
import struct
import zlib
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

TEMPLATE_PALETTES = {
    "orbit-tap": {
        "primary": (108, 140, 255),
        "secondary": (67, 214, 255),
        "accent": (255, 196, 87),
        "background": (12, 18, 44),
    },
    "memory-flip": {
        "primary": (255, 110, 163),
        "secondary": (131, 112, 255),
        "accent": (255, 221, 118),
        "background": (33, 24, 69),
    },
    "focus-timer": {
        "primary": (87, 206, 166),
        "secondary": (86, 169, 255),
        "accent": (255, 209, 102),
        "background": (16, 38, 48),
    },
    "ai-rewriter": {
        "primary": (88, 122, 255),
        "secondary": (130, 83, 255),
        "accent": (118, 255, 214),
        "background": (17, 16, 52),
    },
    "ocr-tool": {
        "primary": (83, 156, 255),
        "secondary": (76, 225, 189),
        "accent": (255, 210, 92),
        "background": (15, 22, 45),
    },
}


def slugify(value: str) -> str:
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9-]+", "-", value.strip().lower().replace("_", "-").replace(" ", "-")))


def replace_in_file(path: Path, replacements: dict[str, str]) -> None:
    content = path.read_text(encoding="utf-8")
    for source, target in replacements.items():
        content = content.replace(source, target)
    path.write_text(content, encoding="utf-8")


def _blend(a: tuple[int, int, int], b: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    clamped = max(0.0, min(1.0, factor))
    return tuple(int(a[index] + (b[index] - a[index]) * clamped) for index in range(3))


def _clamp(value: int) -> int:
    return max(0, min(255, value))


def _rgba(color: tuple[int, int, int], alpha: int = 255) -> bytes:
    return bytes((_clamp(color[0]), _clamp(color[1]), _clamp(color[2]), _clamp(alpha)))


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def write_png(path: Path, width: int, height: int, pixel_at) -> None:
    rows = []
    for y in range(height):
        row = bytearray(b"\x00")
        for x in range(width):
            row.extend(pixel_at(x, y))
        rows.append(bytes(row))

    compressed = zlib.compress(b"".join(rows), level=9)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", ihdr),
            _png_chunk(b"IDAT", compressed),
            _png_chunk(b"IEND", b""),
        ]
    )
    path.write_bytes(png)


def create_thumbnail_png(path: Path, palette: dict[str, tuple[int, int, int]]) -> None:
    width, height = 1280, 720
    background = palette["background"]
    primary = palette["primary"]
    secondary = palette["secondary"]
    accent = palette["accent"]
    white = (250, 252, 255)

    def pixel_at(x: int, y: int) -> bytes:
        vertical = y / max(1, height - 1)
        horizontal = x / max(1, width - 1)
        base = _blend(background, primary, vertical * 0.42)
        base = _blend(base, secondary, horizontal * 0.24)

        dx1 = x - width * 0.28
        dy1 = y - height * 0.34
        d1 = (dx1 * dx1 + dy1 * dy1) ** 0.5
        glow1 = max(0.0, 1.0 - d1 / (width * 0.22))
        if glow1 > 0:
            base = _blend(base, accent, glow1 * 0.72)

        dx2 = x - width * 0.78
        dy2 = y - height * 0.72
        d2 = (dx2 * dx2 + dy2 * dy2) ** 0.5
        glow2 = max(0.0, 1.0 - d2 / (width * 0.18))
        if glow2 > 0:
            base = _blend(base, white, glow2 * 0.38)

        orbit_y = height * 0.58
        orbit_curve = ((x - width * 0.52) / (width * 0.4)) ** 2
        orbit_distance = abs(y - (orbit_y + orbit_curve * 26))
        if orbit_distance < 2.4:
            base = _blend(base, white, 0.58)
        elif orbit_distance < 5.5:
            base = _blend(base, secondary, 0.28)

        planet_dx = x - width * 0.68
        planet_dy = y - height * 0.49
        planet_distance = (planet_dx * planet_dx + planet_dy * planet_dy) ** 0.5
        planet_radius = width * 0.09
        if planet_distance < planet_radius:
            shade = 1.0 - planet_distance / planet_radius
            planet = _blend(primary, secondary, 0.35 + 0.25 * horizontal)
            planet = _blend(planet, white, shade * 0.24)
            base = planet
        elif planet_distance < planet_radius + 6:
            ring = max(0.0, 1.0 - (planet_distance - planet_radius) / 6)
            base = _blend(base, accent, ring * 0.6)

        star_dx = x - width * 0.22
        star_dy = y - height * 0.38
        star_distance = (star_dx * star_dx + star_dy * star_dy) ** 0.5
        star_radius = width * 0.075
        if star_distance < star_radius:
            star = _blend(accent, white, 0.45)
            star = _blend(star, white, max(0.0, 1.0 - star_distance / star_radius) * 0.4)
            base = star

        return _rgba(base)

    write_png(path, width, height, pixel_at)


def create_icon_png(path: Path, palette: dict[str, tuple[int, int, int]]) -> None:
    size = 512
    background = palette["background"]
    primary = palette["primary"]
    secondary = palette["secondary"]
    accent = palette["accent"]
    white = (250, 252, 255)

    def pixel_at(x: int, y: int) -> bytes:
        horizontal = x / max(1, size - 1)
        vertical = y / max(1, size - 1)
        base = _blend(background, primary, vertical * 0.44)
        base = _blend(base, secondary, horizontal * 0.22)

        center_x = size * 0.5
        center_y = size * 0.5
        dx = x - center_x
        dy = y - center_y
        distance = (dx * dx + dy * dy) ** 0.5

        core_radius = size * 0.22
        if distance < core_radius:
            base = _blend(accent, white, max(0.0, 1.0 - distance / core_radius) * 0.35)

        ring_distance = abs(distance - size * 0.32)
        if ring_distance < 6:
            base = _blend(base, white, 0.62)
        elif ring_distance < 12:
            base = _blend(base, secondary, 0.35)

        badge_left = size * 0.18
        badge_top = size * 0.7
        if badge_left < x < size * 0.82 and badge_top < y < size * 0.83:
            stripe = ((x - badge_left) / (size * 0.64))
            badge = _blend(primary, secondary, stripe)
            badge = _blend(badge, white, 0.16)
            base = badge

        return _rgba(base)

    write_png(path, size, size, pixel_at)


def create_default_assets(assets_dir: Path, template_name: str) -> tuple[str, str]:
    thumbnail_path = assets_dir / "thumbnail.png"
    icon_path = assets_dir / "icon.png"
    palette = TEMPLATE_PALETTES[template_name]
    create_thumbnail_png(thumbnail_path, palette)
    create_icon_png(icon_path, palette)
    return "assets/thumbnail.png", "assets/icon.png"


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
    thumbnail_asset, icon_asset = create_default_assets(assets_dir, args.template)

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
        "thumbnail": thumbnail_asset,
        "icon": icon_asset,
        "screenshots": [thumbnail_asset],
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
    print("Generated default cover assets: assets/thumbnail.png and assets/icon.png")
    print("You can replace them with custom PNG/JPG/WebP artwork later for a stronger store listing.")
    print("Next step: build or customize the app under app/, then package it with build_nima_package.py")


if __name__ == "__main__":
    main()
