# generate_placeholder_sprites.py
# Developer: Marcus Daley
# Date: 2026-02-21
# Purpose: Generate placeholder 3D owl sprites for testing the Owl3DWidget before final renders are ready

"""
Generate placeholder 3D owl sprite images for testing.

Creates simple colored circles with state labels as temporary sprites
while you work on generating the final 3D renders. This lets you test
the crossfade animations and integration immediately.

Usage::

    python scripts/gui/generate_placeholder_sprites.py

This will create 8 PNG files in scripts/gui/assets/owl_3d/:
- owl_3d_sleeping.png (purple)
- owl_3d_waking.png (blue)
- owl_3d_idle.png (green)
- owl_3d_scanning.png (cyan)
- owl_3d_curious.png (yellow)
- owl_3d_alert.png (orange)
- owl_3d_alarm.png (red)
- owl_3d_proud.png (gold)
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Sprite directory
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
SPRITE_DIR = ASSETS_DIR / "owl_3d"

# State colors (for placeholder identification)
STATE_COLORS = {
    "sleeping": (147, 112, 219, 255),  # Purple
    "waking": (100, 149, 237, 255),    # Cornflower blue
    "idle": (60, 179, 113, 255),       # Medium sea green
    "scanning": (64, 224, 208, 255),   # Turquoise
    "curious": (255, 215, 0, 255),     # Gold
    "alert": (255, 165, 0, 255),       # Orange
    "alarm": (220, 20, 60, 255),       # Crimson
    "proud": (218, 165, 32, 255),      # Goldenrod
}

SIZE = 512


def create_placeholder_sprite(state: str, color: tuple[int, int, int, int]) -> None:
    """Create a placeholder sprite for the given state.

    Parameters
    ----------
    state:
        Owl state name (e.g., "sleeping", "idle").
    color:
        RGBA color tuple for the placeholder circle.
    """
    # Create image with transparency
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw colored circle
    margin = 50
    draw.ellipse(
        [(margin, margin), (SIZE - margin, SIZE - margin)],
        fill=color,
        outline=(255, 255, 255, 255),
        width=4,
    )

    # Draw smaller white circle for face
    face_margin = 150
    draw.ellipse(
        [(face_margin, face_margin), (SIZE - face_margin, SIZE - face_margin)],
        fill=(255, 255, 255, 200),
    )

    # Draw eyes (two circles)
    eye_y = 200
    eye_radius = 20
    # Left eye
    draw.ellipse(
        [(180, eye_y), (180 + eye_radius * 2, eye_y + eye_radius * 2)],
        fill=(30, 30, 30, 255),
    )
    # Right eye
    draw.ellipse(
        [(280, eye_y), (280 + eye_radius * 2, eye_y + eye_radius * 2)],
        fill=(30, 30, 30, 255),
    )

    # Draw beak (triangle)
    beak_points = [(SIZE // 2, 280), (SIZE // 2 - 15, 250), (SIZE // 2 + 15, 250)]
    draw.polygon(beak_points, fill=(255, 140, 0, 255))

    # Draw state label
    try:
        # Try to use a nice font
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        # Fallback to default font
        font = ImageFont.load_default()

    text = state.upper()
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (SIZE - text_width) // 2
    text_y = SIZE - 80

    # Draw text with outline for visibility
    for offset_x, offset_y in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        draw.text(
            (text_x + offset_x, text_y + offset_y),
            text,
            font=font,
            fill=(0, 0, 0, 255),
        )
    draw.text((text_x, text_y), text, font=font, fill=(255, 255, 255, 255))

    # Save sprite
    output_path = SPRITE_DIR / f"owl_3d_{state}.png"
    img.save(output_path, "PNG")
    print(f"✅ Created: {output_path}")


def main() -> None:
    """Generate all placeholder sprites."""
    print("Generating placeholder 3D owl sprites...")
    print(f"Output directory: {SPRITE_DIR}\n")

    # Create sprite directory if it doesn't exist
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate each state
    for state, color in STATE_COLORS.items():
        create_placeholder_sprite(state, color)

    print("\n✨ Done! Placeholder sprites generated.")
    print("\nYou can now run the app and see the Owl3DWidget in action.")
    print("Replace these placeholders with real 3D renders when ready.")
    print(f"\nSprites location: {SPRITE_DIR}")


if __name__ == "__main__":
    main()
