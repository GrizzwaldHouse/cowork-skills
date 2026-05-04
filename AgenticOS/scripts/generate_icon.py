# generate_icon.py
# Developer: Marcus Daley
# Date: 2026-05-01
# Purpose: Generate the branded AgenticOS tray icon — gold anchor with
#          neural-network dots on deep-navy — as a multi-resolution ICO.
#          Run once: python AgenticOS/scripts/generate_icon.py

from __future__ import annotations
import math
from pathlib import Path
from PIL import Image, ImageDraw

NAVY  = (27, 40, 56, 255)
GOLD  = (201, 169, 78, 255)
DGOLD = (139, 116, 53, 255)

OUT_PATH = Path(__file__).parent.parent / "dashboard" / "assets" / "tray-icon.ico"


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), NAVY)
    d   = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    r  = int(size * 0.38)
    lw = max(2, size // 20)

    # Outer ring
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GOLD, width=lw)

    # Anchor shaft
    sh = int(size * 0.28)
    sw = max(2, size // 18)
    d.rectangle([cx - sw // 2, cy - sh // 2, cx + sw // 2, cy + sh // 2], fill=GOLD)

    # Anchor crossbar
    cb  = int(size * 0.20)
    ch  = max(2, size // 18)
    bar_y = cy - sh // 2 + size // 10
    d.rectangle([cx - cb, bar_y - ch // 2, cx + cb, bar_y + ch // 2], fill=GOLD)

    # Anchor top ring
    tr = max(2, size // 12)
    d.ellipse([cx - tr, bar_y - tr * 2, cx + tr, bar_y], outline=GOLD, width=lw)

    # Curved flukes at bottom
    fk  = int(size * 0.14)
    bot = cy + sh // 2
    d.arc([cx - fk * 2, bot - fk, cx,        bot + fk], 0, 180, fill=GOLD, width=lw)
    d.arc([cx,          bot - fk, cx + fk * 2, bot + fk], 0, 180, fill=GOLD, width=lw)

    # Neural nodes — 6 dots evenly spaced on the outer ring
    nd = max(2, size // 20)
    for i in range(6):
        angle = math.radians(i * 60 - 30)
        nx = int(cx + r * math.cos(angle))
        ny = int(cy + r * math.sin(angle))
        d.ellipse([nx - nd, ny - nd, nx + nd, ny + nd], fill=DGOLD)

    return img


def main() -> None:
    sizes  = [16, 32, 48, 64, 128, 256]
    frames = [draw_icon(s) for s in sizes]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT_PATH,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"Icon written to {OUT_PATH}")


if __name__ == "__main__":
    main()
