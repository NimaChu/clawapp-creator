from __future__ import annotations

import binascii
import math
import re
import struct
import zlib
from pathlib import Path

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
    "editor-studio": {
        "primary": (255, 137, 92),
        "secondary": (255, 205, 99),
        "accent": (97, 214, 255),
        "background": (28, 21, 48),
    },
    "planner-board": {
        "primary": (76, 205, 166),
        "secondary": (96, 155, 255),
        "accent": (255, 206, 117),
        "background": (18, 33, 42),
    },
    "rhythm-stage": {
        "primary": (255, 92, 164),
        "secondary": (111, 102, 255),
        "accent": (80, 232, 215),
        "background": (25, 16, 52),
    },
    "arcade-shooter": {
        "primary": (255, 105, 89),
        "secondary": (255, 170, 91),
        "accent": (91, 219, 255),
        "background": (19, 18, 44),
    },
    "education-lab": {
        "primary": (120, 210, 118),
        "secondary": (97, 150, 255),
        "accent": (255, 203, 102),
        "background": (16, 30, 48),
    },
    "story-cosmos": {
        "primary": (163, 113, 255),
        "secondary": (255, 122, 186),
        "accent": (255, 216, 126),
        "background": (28, 17, 52),
    },
}

DEFAULT_TEMPLATE_MOTIFS = {
    "orbit-tap": "arcade-orbit",
    "memory-flip": "puzzle-cards",
    "focus-timer": "planner-board",
    "ai-rewriter": "ai-chat",
    "ocr-tool": "ocr-scan",
}

MOTIF_TO_PALETTE = {
    "arcade-orbit": "orbit-tap",
    "space-heist": "arcade-shooter",
    "arcade-shooter": "arcade-shooter",
    "survival-wave": "arcade-shooter",
    "factory-floor": "focus-timer",
    "puzzle-cards": "memory-flip",
    "block-stack": "memory-flip",
    "editor-studio": "editor-studio",
    "drawing-board": "editor-studio",
    "planner-board": "planner-board",
    "calculator-panel": "planner-board",
    "ai-chat": "ai-rewriter",
    "ocr-scan": "ocr-tool",
    "story-cosmos": "story-cosmos",
    "education-lab": "education-lab",
    "rhythm-stage": "rhythm-stage",
}

COVER_VARIANT_COUNT = 12


def slugify(value: str) -> str:
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9-]+", "-", value.strip().lower().replace("_", "-").replace(" ", "-")))


def stable_string_hash(value: str) -> int:
    total = 0
    for index, char in enumerate(value):
        total = (total * 131 + ord(char) + index) & 0xFFFFFFFF
    return total


def choose_cover_variant(template_name: str, slug: str, motif: str) -> int:
    return stable_string_hash(f"{template_name}:{slug}:{motif}") % COVER_VARIANT_COUNT


def vary_palette(
    palette: dict[str, tuple[int, int, int]],
    variant: int,
) -> dict[str, tuple[int, int, int]]:
    cycle = variant % COVER_VARIANT_COUNT
    signed = cycle - ((COVER_VARIANT_COUNT - 1) / 2)
    strength = signed * 0.035
    white = (250, 252, 255)
    black = (8, 12, 24)
    overlay = white if strength > 0 else black
    factor = abs(strength)
    adjusted = {key: _blend(color, overlay, factor) for key, color in palette.items()}
    if cycle % 3 == 1:
        adjusted["accent"] = _blend(adjusted["accent"], white, 0.12)
    elif cycle % 3 == 2:
        adjusted["secondary"] = _blend(adjusted["secondary"], adjusted["accent"], 0.16)
    return adjusted


def infer_art_direction(template_name: str, slug: str, hint_text: str = "") -> str:
    text = " ".join(filter(None, [template_name, slug, hint_text])).lower()
    keyword_map = [
        ("ocr", "ocr-scan"),
        ("scan", "ocr-scan"),
        ("vision", "ocr-scan"),
        ("receipt", "ocr-scan"),
        ("chart", "ocr-scan"),
        ("rewrite", "ai-chat"),
        ("ai", "ai-chat"),
        ("llm", "ai-chat"),
        ("chat", "ai-chat"),
        ("planner", "planner-board"),
        ("calendar", "planner-board"),
        ("schedule", "planner-board"),
        ("todo", "planner-board"),
        ("timer", "planner-board"),
        ("focus", "planner-board"),
        ("calc", "calculator-panel"),
        ("calculator", "calculator-panel"),
        ("budget", "calculator-panel"),
        ("finance", "calculator-panel"),
        ("editor", "editor-studio"),
        ("pixel", "editor-studio"),
        ("paint", "drawing-board"),
        ("draw", "drawing-board"),
        ("doodle", "drawing-board"),
        ("rhythm", "rhythm-stage"),
        ("music", "rhythm-stage"),
        ("beat", "rhythm-stage"),
        ("orbit", "arcade-orbit"),
        ("arcade", "arcade-orbit"),
        ("gravity", "arcade-orbit"),
        ("tetris", "block-stack"),
        ("block", "block-stack"),
        ("puzzle", "puzzle-cards"),
        ("memory", "puzzle-cards"),
        ("card", "puzzle-cards"),
        ("factory", "factory-floor"),
        ("automation", "factory-floor"),
        ("heist", "space-heist"),
        ("ship", "space-heist"),
        ("starship", "space-heist"),
        ("shooter", "arcade-shooter"),
        ("bullet", "arcade-shooter"),
        ("hell", "arcade-shooter"),
        ("monster", "survival-wave"),
        ("survival", "survival-wave"),
        ("void", "survival-wave"),
        ("story", "story-cosmos"),
        ("verse", "story-cosmos"),
        ("dream", "story-cosmos"),
        ("mystery", "story-cosmos"),
        ("calligraphy", "education-lab"),
        ("character", "education-lab"),
        ("hanzi", "education-lab"),
        ("learn", "education-lab"),
        ("education", "education-lab"),
    ]
    for keyword, motif in keyword_map:
        if keyword in text:
            return motif
    return DEFAULT_TEMPLATE_MOTIFS.get(template_name, "arcade-orbit")


def pick_palette_for_manifest(manifest: dict, motif: str) -> dict[str, tuple[int, int, int]]:
    text = " ".join(
        [
            str(manifest.get("category", "")).lower(),
            str(manifest.get("modelCategory", "")).lower(),
            str(manifest.get("name", "")).lower(),
            str(manifest.get("description", "")).lower(),
            " ".join(str(item).lower() for item in manifest.get("tags", [])),
        ]
    )
    resolved_motif = infer_art_direction("generic", str(manifest.get("slug") or manifest.get("id") or ""), text) if motif == "arcade-orbit" else motif
    palette_key = MOTIF_TO_PALETTE.get(resolved_motif)
    if palette_key:
        return TEMPLATE_PALETTES[palette_key]
    if "utility" in text or "tool" in text:
        return TEMPLATE_PALETTES["planner-board"]
    return TEMPLATE_PALETTES["orbit-tap"]


def create_default_assets(assets_dir: Path, template_name: str, slug: str = "") -> tuple[str, str]:
    thumbnail_path = assets_dir / "thumbnail.png"
    icon_path = assets_dir / "icon.png"
    motif = infer_art_direction(template_name, slug)
    variant = choose_cover_variant(template_name, slug, motif)
    base_palette = TEMPLATE_PALETTES.get(template_name) or TEMPLATE_PALETTES[MOTIF_TO_PALETTE.get(motif, "orbit-tap")]
    palette = vary_palette(base_palette, variant)
    create_thumbnail_png(thumbnail_path, palette, motif, variant)
    create_icon_png(icon_path, palette, motif, variant)
    return "assets/thumbnail.png", "assets/icon.png"


def _blend(a: tuple[int, int, int], b: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    clamped = max(0.0, min(1.0, factor))
    return tuple(int(a[index] + (b[index] - a[index]) * clamped) for index in range(3))


def _mix(base: tuple[int, int, int], overlay: tuple[int, int, int], strength: float) -> tuple[int, int, int]:
    return _blend(base, overlay, max(0.0, min(1.0, strength)))


def _clamp(value: int) -> int:
    return max(0, min(255, value))


def _rgba(color: tuple[int, int, int], alpha: int = 255) -> bytes:
    return bytes((_clamp(color[0]), _clamp(color[1]), _clamp(color[2]), _clamp(alpha)))


def _rect(x: int, y: int, left: float, top: float, right: float, bottom: float) -> bool:
    return left <= x <= right and top <= y <= bottom


def _circle(x: int, y: int, cx: float, cy: float, radius: float) -> bool:
    dx = x - cx
    dy = y - cy
    return dx * dx + dy * dy <= radius * radius


def _ellipse(x: int, y: int, cx: float, cy: float, rx: float, ry: float) -> bool:
    if rx == 0 or ry == 0:
        return False
    dx = (x - cx) / rx
    dy = (y - cy) / ry
    return dx * dx + dy * dy <= 1.0


def _ring(x: int, y: int, cx: float, cy: float, radius: float, thickness: float) -> bool:
    distance = math.hypot(x - cx, y - cy)
    return radius - thickness <= distance <= radius + thickness


def _distance_to_segment(x: int, y: int, ax: float, ay: float, bx: float, by: float) -> float:
    abx = bx - ax
    aby = by - ay
    apx = x - ax
    apy = y - ay
    ab2 = abx * abx + aby * aby
    if ab2 == 0:
        return math.hypot(x - ax, y - ay)
    t = max(0.0, min(1.0, (apx * abx + apy * aby) / ab2))
    closest_x = ax + abx * t
    closest_y = ay + aby * t
    return math.hypot(x - closest_x, y - closest_y)


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


def _draw_lobster_badge(base: tuple[int, int, int], x: int, y: int, width: int, height: int, variant: int) -> tuple[int, int, int]:
    shell = (255, 112, 82)
    cream = (255, 239, 229)
    gold = (255, 196, 94)
    cx = width * 0.14 + (variant - (COVER_VARIANT_COUNT / 2)) * 1.2
    cy = height * 0.18
    if _ellipse(x, y, cx, cy + height * 0.03, width * 0.045, height * 0.055):
        return _mix(base, shell, 0.96)
    if _ellipse(x, y, cx, cy - height * 0.035, width * 0.03, height * 0.035):
        return _mix(base, shell, 0.98)
    if _circle(x, y, cx - width * 0.022, cy - height * 0.08, 7) or _circle(x, y, cx + width * 0.022, cy - height * 0.08, 7):
        return _mix(base, cream, 0.92)
    if _distance_to_segment(x, y, cx + width * 0.045, cy + height * 0.01, cx + width * 0.09, cy - height * 0.025) < 5:
        return _mix(base, gold, 0.9)
    return base


def create_thumbnail_png(path: Path, palette: dict[str, tuple[int, int, int]], motif: str, variant: int = 0) -> None:
    width, height = 1024, 576
    background = palette["background"]
    primary = palette["primary"]
    secondary = palette["secondary"]
    accent = palette["accent"]
    white = (248, 251, 255)
    variant_shift = (variant - ((COVER_VARIANT_COUNT - 1) / 2)) / COVER_VARIANT_COUNT

    def pixel_at(x: int, y: int) -> bytes:
        horizontal = x / max(1, width - 1)
        vertical = y / max(1, height - 1)
        base = _blend(background, primary, vertical * 0.36)
        base = _blend(base, secondary, horizontal * 0.22)

        glow_points = [
            (width * (0.22 + variant_shift * 0.08), height * 0.26, accent, width * 0.24),
            (width * (0.76 - variant_shift * 0.06), height * 0.76, white, width * 0.18),
        ]
        for gx, gy, color, radius in glow_points:
            distance = math.hypot(x - gx, y - gy)
            glow = max(0.0, 1.0 - distance / radius)
            if glow > 0:
                base = _blend(base, color, glow * 0.34)

        if motif == "arcade-orbit":
            if _ring(x, y, width * 0.61, height * 0.56, width * 0.2 + variant_shift * 32, 4.5):
                base = _mix(base, white, 0.7)
            if _circle(x, y, width * 0.34, height * 0.36, width * 0.085):
                base = _mix(base, accent, 0.9)
            if _circle(x, y, width * 0.72, height * 0.5, width * 0.09):
                base = _mix(base, secondary, 0.9)
        elif motif == "space-heist":
            if _ellipse(x, y, width * 0.54, height * 0.6, width * 0.17, height * 0.09):
                base = _mix(base, secondary, 0.92)
            if _distance_to_segment(x, y, width * 0.36, height * 0.44, width * 0.72, height * 0.34) < 7:
                base = _mix(base, white, 0.78)
            if _triangle_lock(x, y, width * 0.72, height * 0.54, 72):
                base = _mix(base, accent, 0.88)
        elif motif == "arcade-shooter":
            if _ring(x, y, width * 0.58, height * 0.48, width * 0.12, 3.5) or _ring(x, y, width * 0.58, height * 0.48, width * 0.06, 2.5):
                base = _mix(base, white, 0.78)
            if _distance_to_segment(x, y, width * 0.42, height * 0.48, width * 0.74, height * 0.48) < 4 or _distance_to_segment(x, y, width * 0.58, height * 0.32, width * 0.58, height * 0.64) < 4:
                base = _mix(base, accent, 0.82)
            if _distance_to_segment(x, y, width * 0.28, height * 0.7, width * 0.48, height * 0.54) < 9:
                base = _mix(base, primary, 0.9)
        elif motif == "survival-wave":
            for cx in [0.34, 0.5, 0.66]:
                if _circle(x, y, width * cx, height * 0.58, 42):
                    base = _mix(base, primary if cx < 0.5 else secondary, 0.88)
            if _distance_to_segment(x, y, width * 0.28, height * 0.34, width * 0.76, height * 0.74) < 6:
                base = _mix(base, accent, 0.8)
        elif motif == "puzzle-cards":
            for left, top, right, bottom, color in [
                (width * 0.22, height * 0.23, width * 0.42, height * 0.59, primary),
                (width * 0.41, height * 0.18, width * 0.61, height * 0.54, secondary),
                (width * 0.6, height * 0.26, width * 0.8, height * 0.62, accent),
            ]:
                if _rect(x, y, left, top, right, bottom):
                    base = _mix(base, color, 0.92)
        elif motif == "block-stack":
            for left, top, right, bottom, color in [
                (width * 0.28, height * 0.54, width * 0.52, height * 0.66, primary),
                (width * 0.4, height * 0.42, width * 0.64, height * 0.54, secondary),
                (width * 0.52, height * 0.3, width * 0.76, height * 0.42, accent),
            ]:
                if _rect(x, y, left, top, right, bottom):
                    base = _mix(base, color, 0.94)
        elif motif == "editor-studio" or motif == "drawing-board":
            if _rect(x, y, width * 0.2, height * 0.2, width * 0.72, height * 0.72):
                base = _mix(base, white, 0.24)
            if _distance_to_segment(x, y, width * 0.62, height * 0.28, width * 0.82, height * 0.72) < 12:
                base = _mix(base, accent, 0.9)
            if motif == "drawing-board" and _ring(x, y, width * 0.44, height * 0.44, width * 0.09, 6):
                base = _mix(base, secondary, 0.76)
        elif motif == "planner-board":
            if _rect(x, y, width * 0.22, height * 0.2, width * 0.78, height * 0.74):
                base = _mix(base, white, 0.18)
            for yy in [0.3, 0.42, 0.54, 0.66]:
                if _distance_to_segment(x, y, width * 0.28, height * yy, width * 0.72, height * yy) < 3:
                    base = _mix(base, primary, 0.72)
            if _rect(x, y, width * 0.28, height * 0.3, width * 0.38, height * 0.42):
                base = _mix(base, accent, 0.88)
        elif motif == "calculator-panel":
            if _rect(x, y, width * 0.28, height * 0.16, width * 0.74, height * 0.76):
                base = _mix(base, white, 0.14)
            if _rect(x, y, width * 0.34, height * 0.24, width * 0.68, height * 0.34):
                base = _mix(base, secondary, 0.76)
            for row in range(3):
                for col in range(3):
                    left = width * (0.34 + col * 0.12)
                    top = height * (0.42 + row * 0.1)
                    if _rect(x, y, left, top, left + width * 0.08, top + height * 0.07):
                        base = _mix(base, primary if (row + col) % 2 == 0 else accent, 0.86)
        elif motif == "ai-chat":
            if _ellipse(x, y, width * 0.42, height * 0.44, width * 0.19, height * 0.13):
                base = _mix(base, primary, 0.92)
            if _ellipse(x, y, width * 0.62, height * 0.58, width * 0.18, height * 0.12):
                base = _mix(base, secondary, 0.92)
            if _distance_to_segment(x, y, width * 0.42, height * 0.58, width * 0.53, height * 0.72) < 9:
                base = _mix(base, accent, 0.84)
        elif motif == "ocr-scan":
            if _rect(x, y, width * 0.28, height * 0.14, width * 0.72, height * 0.8):
                base = _mix(base, white, 0.22)
            if _rect(x, y, width * 0.34, height * 0.3, width * 0.66, height * 0.66):
                border = abs(x - width * 0.34) < 5 or abs(x - width * 0.66) < 5 or abs(y - height * 0.3) < 5 or abs(y - height * 0.66) < 5
                if border:
                    base = _mix(base, accent, 0.9)
            if _distance_to_segment(x, y, width * 0.34, height * 0.22, width * 0.62, height * 0.22) < 4:
                base = _mix(base, primary, 0.75)
        elif motif == "story-cosmos":
            if _rect(x, y, width * 0.3, height * 0.22, width * 0.72, height * 0.72):
                base = _mix(base, white, 0.18)
            if _distance_to_segment(x, y, width * 0.51, height * 0.22, width * 0.51, height * 0.72) < 4:
                base = _mix(base, secondary, 0.72)
            if _circle(x, y, width * 0.76, height * 0.26, 18) or _circle(x, y, width * 0.82, height * 0.34, 12):
                base = _mix(base, accent, 0.92)
        elif motif == "education-lab":
            if _rect(x, y, width * 0.2, height * 0.22, width * 0.78, height * 0.74):
                base = _mix(base, white, 0.16)
            if _distance_to_segment(x, y, width * 0.32, height * 0.34, width * 0.68, height * 0.62) < 8:
                base = _mix(base, primary, 0.84)
            if _distance_to_segment(x, y, width * 0.48, height * 0.3, width * 0.48, height * 0.68) < 5:
                base = _mix(base, accent, 0.78)
        elif motif == "rhythm-stage":
            bars = [0.3, 0.4, 0.5, 0.6, 0.7]
            heights = [0.16, 0.28, 0.38, 0.26, 0.18]
            for idx, center in enumerate(bars):
                left = width * center - width * 0.04
                top = height * (0.66 - heights[idx] - variant_shift * 0.04)
                right = width * center + width * 0.04
                bottom = height * 0.66
                if _rect(x, y, left, top, right, bottom):
                    base = _mix(base, primary if idx % 2 == 0 else accent, 0.9)
            if _distance_to_segment(x, y, width * 0.24, height * 0.34, width * 0.78, height * 0.3) < 4:
                base = _mix(base, secondary, 0.82)

        base = _draw_lobster_badge(base, x, y, width, height, variant)
        return _rgba(base)

    write_png(path, width, height, pixel_at)


def create_icon_png(path: Path, palette: dict[str, tuple[int, int, int]], motif: str, variant: int = 0) -> None:
    size = 384
    background = palette["background"]
    primary = palette["primary"]
    secondary = palette["secondary"]
    accent = palette["accent"]
    white = (249, 251, 255)

    def pixel_at(x: int, y: int) -> bytes:
        horizontal = x / max(1, size - 1)
        vertical = y / max(1, size - 1)
        base = _blend(background, primary, vertical * 0.32)
        base = _blend(base, secondary, horizontal * 0.16)

        if _ring(x, y, size * 0.5, size * 0.5, size * 0.32, 8):
            base = _mix(base, white, 0.5)

        if motif in ("arcade-orbit", "space-heist", "arcade-shooter", "survival-wave"):
            if _circle(x, y, size * 0.56, size * 0.5, size * 0.1):
                base = _mix(base, accent, 0.9)
        elif motif in ("puzzle-cards", "block-stack"):
            if _rect(x, y, size * 0.3, size * 0.34, size * 0.52, size * 0.56) or _rect(x, y, size * 0.48, size * 0.46, size * 0.7, size * 0.68):
                base = _mix(base, primary, 0.9)
        elif motif in ("editor-studio", "drawing-board"):
            if _rect(x, y, size * 0.26, size * 0.28, size * 0.72, size * 0.72):
                base = _mix(base, white, 0.2)
            if _distance_to_segment(x, y, size * 0.54, size * 0.3, size * 0.76, size * 0.72) < 10:
                base = _mix(base, accent, 0.86)
        elif motif in ("planner-board", "calculator-panel", "ocr-scan", "education-lab", "story-cosmos", "ai-chat", "rhythm-stage"):
            if _rect(x, y, size * 0.24, size * 0.24, size * 0.76, size * 0.76):
                base = _mix(base, white, 0.18)
            if motif == "rhythm-stage":
                if _rect(x, y, size * 0.32, size * 0.46, size * 0.4, size * 0.7) or _rect(x, y, size * 0.48, size * 0.34, size * 0.56, size * 0.7) or _rect(x, y, size * 0.64, size * 0.52, size * 0.72, size * 0.7):
                    base = _mix(base, primary, 0.88)
            elif motif == "ai-chat":
                if _ellipse(x, y, size * 0.44, size * 0.44, size * 0.15, size * 0.11) or _ellipse(x, y, size * 0.6, size * 0.58, size * 0.14, size * 0.1):
                    base = _mix(base, secondary, 0.9)
            elif motif == "ocr-scan":
                if _rect(x, y, size * 0.34, size * 0.34, size * 0.66, size * 0.66):
                    border = abs(x - size * 0.34) < 4 or abs(x - size * 0.66) < 4 or abs(y - size * 0.34) < 4 or abs(y - size * 0.66) < 4
                    if border:
                        base = _mix(base, accent, 0.92)
            elif motif == "calculator-panel":
                if _rect(x, y, size * 0.34, size * 0.3, size * 0.66, size * 0.4):
                    base = _mix(base, secondary, 0.74)
            else:
                if _distance_to_segment(x, y, size * 0.34, size * 0.4, size * 0.66, size * 0.6) < 10:
                    base = _mix(base, primary, 0.84)

        base = _draw_lobster_badge(base, x, y, size, size, variant)
        return _rgba(base)

    write_png(path, size, size, pixel_at)


def _triangle_lock(x: int, y: int, cx: float, cy: float, size: float) -> bool:
    left = (cx - size * 0.5, cy + size * 0.4)
    right = (cx + size * 0.5, cy + size * 0.4)
    top = (cx, cy - size * 0.45)
    denominator = ((right[1] - top[1]) * (left[0] - top[0]) + (top[0] - right[0]) * (left[1] - top[1]))
    if denominator == 0:
        return False
    a = ((right[1] - top[1]) * (x - top[0]) + (top[0] - right[0]) * (y - top[1])) / denominator
    b = ((top[1] - left[1]) * (x - top[0]) + (left[0] - top[0]) * (y - top[1])) / denominator
    c = 1 - a - b
    return 0 <= a <= 1 and 0 <= b <= 1 and 0 <= c <= 1
