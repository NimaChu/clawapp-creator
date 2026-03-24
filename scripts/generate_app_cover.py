#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scaffold_mini_game import (
    TEMPLATE_PALETTES,
    choose_cover_variant,
    create_icon_png,
    create_thumbnail_png,
    infer_art_direction,
    slugify,
    stable_string_hash,
    vary_palette,
)


def pick_palette(manifest: dict, motif: str) -> dict[str, tuple[int, int, int]]:
    tags = " ".join(str(item).lower() for item in manifest.get("tags", []))
    category = str(manifest.get("category", "")).lower()
    model_category = str(manifest.get("modelCategory", "")).lower()
    name = str(manifest.get("name", "")).lower()
    description = str(manifest.get("description", "")).lower()
    text = " ".join([tags, category, model_category, name, description])

    if any(keyword in text for keyword in ("ocr", "vision", "scan", "image")):
        return TEMPLATE_PALETTES["ocr-tool"]
    if any(keyword in text for keyword in ("ai", "rewrite", "llm", "chat", "text")):
        return TEMPLATE_PALETTES["ai-rewriter"]
    if any(keyword in text for keyword in ("timer", "focus", "productivity", "utility", "tool")):
        return TEMPLATE_PALETTES["focus-timer"]
    if any(keyword in text for keyword in ("memory", "flip", "card", "puzzle")):
        return TEMPLATE_PALETTES["memory-flip"]
    if any(keyword in text for keyword in ("game", "arcade", "adventure", "action", "rpg", "orbit", "heist")):
        return TEMPLATE_PALETTES["orbit-tap"]

    palette_keys = list(TEMPLATE_PALETTES)
    return TEMPLATE_PALETTES[palette_keys[stable_string_hash(motif) % len(palette_keys)]]


def load_manifest(project_dir: Path, manifest_path: Path | None) -> tuple[Path, dict]:
    resolved = manifest_path or (project_dir / "manifest.json")
    if not resolved.exists():
        raise SystemExit(f"manifest not found: {resolved}")
    try:
        return resolved, json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"manifest is not valid JSON: {resolved} ({exc})") from exc


def resolve_assets_dir(project_dir: Path, explicit_assets: Path | None) -> Path:
    assets_dir = explicit_assets or (project_dir / "assets")
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate CLAWSPACE cover assets (thumbnail.png + icon.png) for an existing app project.",
    )
    parser.add_argument("project", help="Path to the app project root")
    parser.add_argument("--manifest", help="Optional explicit path to manifest.json")
    parser.add_argument("--assets-dir", help="Optional explicit assets directory")
    parser.add_argument(
        "--motif",
        help="Optional art direction override such as ocr, ai, timer, cards, factory, mystery, pixel-rpg, space-heist, tetris",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing thumbnail.png and icon.png if they already exist",
    )
    args = parser.parse_args()

    project_dir = Path(args.project).expanduser().resolve()
    if not project_dir.exists():
        raise SystemExit(f"project directory not found: {project_dir}")

    manifest_path, manifest = load_manifest(project_dir, Path(args.manifest).expanduser().resolve() if args.manifest else None)
    assets_dir = resolve_assets_dir(project_dir, Path(args.assets_dir).expanduser().resolve() if args.assets_dir else None)

    slug = slugify(str(manifest.get("slug") or manifest.get("id") or project_dir.name))
    motif = args.motif or infer_art_direction("generic", slug)
    variant = choose_cover_variant("generic", slug, motif)
    palette = vary_palette(pick_palette(manifest, motif), variant)

    thumbnail_path = assets_dir / "thumbnail.png"
    icon_path = assets_dir / "icon.png"

    if not args.force:
        existing = [str(path) for path in (thumbnail_path, icon_path) if path.exists()]
        if existing:
            raise SystemExit(
                "refusing to overwrite existing assets without --force: " + ", ".join(existing)
            )

    create_thumbnail_png(thumbnail_path, palette, motif, variant)
    create_icon_png(icon_path, palette, motif, variant)

    manifest_updated = False
    if manifest.get("thumbnail") != "assets/thumbnail.png":
        manifest["thumbnail"] = "assets/thumbnail.png"
        manifest_updated = True
    if manifest.get("icon") != "assets/icon.png":
        manifest["icon"] = "assets/icon.png"
        manifest_updated = True

    if manifest_updated and manifest_path.parent == project_dir:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Project: {project_dir}")
    print(f"Manifest: {manifest_path}")
    print(f"Motif: {motif}")
    print(f"Variant: {variant + 1}")
    print(f"Generated: {thumbnail_path}")
    print(f"Generated: {icon_path}")
    if manifest_updated and manifest_path.parent == project_dir:
        print("Updated manifest fields: thumbnail, icon")
    print("Tip: for a higher-end hero cover, run a separate design pass with the $svg-cover-generator skill and then replace assets/thumbnail.png.")


if __name__ == "__main__":
    main()
