"""
build_owlwatcher.py
Developer: Marcus Daley
Date: 2026-02-20
Purpose: Build script for packaging OwlWatcher into a standalone Windows
         executable using PyInstaller. Handles icon generation from SVG
         and invokes PyInstaller with the owlwatcher.spec file.

Usage:
    python build_owlwatcher.py            # Full build
    python build_owlwatcher.py --clean     # Clean build artifacts first
    python build_owlwatcher.py --icon-only # Only generate the .ico file
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path("C:/ClaudeSkills")
SPEC_FILE = BASE_DIR / "owlwatcher.spec"
ASSETS_DIR = BASE_DIR / "scripts" / "gui" / "assets"
ICO_OUTPUT = ASSETS_DIR / "owlwatcher.ico"
SVG_SOURCE = ASSETS_DIR / "owl_tray.svg"
DIST_DIR = BASE_DIR / "dist"
BUILD_DIR = BASE_DIR / "build"


def generate_ico() -> bool:
    """Generate a .ico file from the owl_tray.svg using PyQt6.

    Returns True on success, False on failure.
    """
    if ICO_OUTPUT.exists():
        print(f"  Icon already exists: {ICO_OUTPUT}")
        return True

    if not SVG_SOURCE.exists():
        print(f"  WARNING: SVG source not found: {SVG_SOURCE}")
        return False

    try:
        from PyQt6.QtCore import QSize, Qt
        from PyQt6.QtGui import QGuiApplication, QImage, QPainter
        from PyQt6.QtSvg import QSvgRenderer

        # QGuiApplication needed for rendering (headless is fine)
        app = QGuiApplication.instance() or QGuiApplication(sys.argv)

        renderer = QSvgRenderer(str(SVG_SOURCE))
        if not renderer.isValid():
            print(f"  WARNING: Invalid SVG: {SVG_SOURCE}")
            return False

        # Generate multiple sizes for a proper .ico
        sizes = [16, 32, 48, 64, 128, 256]
        images: list[QImage] = []

        for size in sizes:
            image = QImage(QSize(size, size), QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            renderer.render(painter)
            painter.end()
            images.append(image)

        # Save the largest as the .ico (Qt doesn't support multi-res .ico natively)
        # Use the 256px image for best quality
        largest = images[-1]
        largest.save(str(ICO_OUTPUT), "ICO")

        if ICO_OUTPUT.exists():
            print(f"  Icon generated: {ICO_OUTPUT}")
            return True

        # Fallback: save as PNG then note it for manual conversion
        png_path = ASSETS_DIR / "owlwatcher.png"
        largest.save(str(png_path), "PNG")
        print(f"  PNG saved (ICO save not supported by this Qt build): {png_path}")
        print("  You can convert it to .ico with an online tool or Pillow.")
        return False

    except ImportError:
        print("  WARNING: PyQt6 not available for icon generation.")
        print("  The .exe will be built without a custom icon.")
        return False
    except Exception as exc:
        print(f"  WARNING: Icon generation failed: {exc}")
        return False


def clean_build_artifacts() -> None:
    """Remove previous build and dist directories."""
    for directory in [BUILD_DIR, DIST_DIR]:
        if directory.exists():
            print(f"  Removing {directory}...")
            shutil.rmtree(directory)
    print("  Clean complete.")


def run_pyinstaller() -> int:
    """Run PyInstaller with the spec file.

    Returns the process exit code.
    """
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        str(SPEC_FILE),
    ]

    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    return result.returncode


def create_desktop_shortcut() -> None:
    """Create a Windows desktop shortcut for OwlWatcher.exe."""
    exe_path = DIST_DIR / "OwlWatcher" / "OwlWatcher.exe"
    if not exe_path.exists():
        print("  Skipping shortcut: .exe not found.")
        return

    try:
        import winreg
        # Get the Desktop path from the registry
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        )
        desktop_path = Path(winreg.QueryValueEx(key, "Desktop")[0])
        winreg.CloseKey(key)
    except Exception:
        desktop_path = Path.home() / "Desktop"

    shortcut_path = desktop_path / "OwlWatcher.lnk"

    try:
        # Use PowerShell to create the shortcut
        ps_script = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$sc = $ws.CreateShortcut("{shortcut_path}"); '
            f'$sc.TargetPath = "{exe_path}"; '
            f'$sc.Arguments = "--visible"; '
            f'$sc.WorkingDirectory = "{exe_path.parent}"; '
            f'$sc.Description = "OwlWatcher - File Security Monitor"; '
            f'$sc.Save()'
        )
        subprocess.run(
            ["powershell", "-Command", ps_script],
            check=True,
            capture_output=True,
        )
        print(f"  Desktop shortcut created: {shortcut_path}")
    except Exception as exc:
        print(f"  WARNING: Could not create shortcut: {exc}")
        print(f"  You can manually create a shortcut to: {exe_path}")


def main() -> None:
    """Orchestrate the full build process."""
    parser = argparse.ArgumentParser(
        description="Build OwlWatcher standalone executable",
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="Remove build artifacts before building",
    )
    parser.add_argument(
        "--icon-only", action="store_true",
        help="Only generate the .ico file, skip PyInstaller build",
    )
    parser.add_argument(
        "--no-shortcut", action="store_true",
        help="Skip creating the desktop shortcut",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  OwlWatcher Build Script")
    print("=" * 60)

    # Step 1: Clean (optional)
    if args.clean:
        print("\n[1/4] Cleaning build artifacts...")
        clean_build_artifacts()
    else:
        print("\n[1/4] Skipping clean (use --clean to remove old builds)")

    # Step 2: Generate icon
    print("\n[2/4] Generating application icon...")
    generate_ico()

    if args.icon_only:
        print("\n  --icon-only specified. Stopping here.")
        return

    # Step 3: Run PyInstaller
    print("\n[3/4] Building executable with PyInstaller...")
    exit_code = run_pyinstaller()

    if exit_code != 0:
        print(f"\n  BUILD FAILED (exit code {exit_code})")
        sys.exit(exit_code)

    exe_path = DIST_DIR / "OwlWatcher" / "OwlWatcher.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n  BUILD SUCCESSFUL")
        print(f"  Executable: {exe_path}")
        print(f"  Size: {size_mb:.1f} MB")
    else:
        print("\n  WARNING: Build completed but .exe not found at expected path.")

    # Step 4: Desktop shortcut
    if not args.no_shortcut:
        print("\n[4/4] Creating desktop shortcut...")
        create_desktop_shortcut()
    else:
        print("\n[4/4] Skipping desktop shortcut (--no-shortcut)")

    print("\n" + "=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
