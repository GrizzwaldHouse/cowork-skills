# owlwatcher.spec
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: PyInstaller spec file for building OwlWatcher as a standalone
#          Windows desktop application (.exe).
#
# Build command:
#     pyinstaller owlwatcher.spec
#
# Output:
#     dist/OwlWatcher/OwlWatcher.exe

import sys
from pathlib import Path

block_cipher = None

BASE = Path("C:/ClaudeSkills")
SCRIPTS = BASE / "scripts"
GUI = SCRIPTS / "gui"

a = Analysis(
    [str(GUI / "app.py")],
    pathex=[str(SCRIPTS)],
    binaries=[],
    datas=[
        # Bundle SVG assets into the 'assets' directory inside the exe
        (str(GUI / "assets" / "owl_idle.svg"), "assets"),
        (str(GUI / "assets" / "owl_alert.svg"), "assets"),
        (str(GUI / "assets" / "owl_alarm.svg"), "assets"),
        (str(GUI / "assets" / "owl_tray.svg"), "assets"),
        (str(GUI / "assets" / "owl_sleeping.svg"), "assets"),
        (str(GUI / "assets" / "owl_waking.svg"), "assets"),
        (str(GUI / "assets" / "owl_scanning.svg"), "assets"),
        (str(GUI / "assets" / "owl_curious.svg"), "assets"),
        (str(GUI / "assets" / "owl_proud.svg"), "assets"),
        # Sound effects
        (str(GUI / "assets" / "sounds" / "startup_hoot.wav"), "assets/sounds"),
        (str(GUI / "assets" / "sounds" / "alert_chirp.wav"), "assets/sounds"),
        (str(GUI / "assets" / "sounds" / "alarm_hoot.wav"), "assets/sounds"),
        (str(GUI / "assets" / "sounds" / "allclear_settle.wav"), "assets/sounds"),
    ],
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtSvg",
        "PyQt6.QtSvgWidgets",
        "PyQt6.QtMultimedia",
        "watchdog.observers",
        "watchdog.observers.polling",
        "watchdog.events",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PIL",
        "tkinter",
        "pythonnet",
        "plyer",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Check for .ico file (created by build script), fall back to None
ico_path = BASE / "scripts" / "gui" / "assets" / "owlwatcher.ico"
icon_file = str(ico_path) if ico_path.exists() else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OwlWatcher",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window -- pure GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="OwlWatcher",
)
