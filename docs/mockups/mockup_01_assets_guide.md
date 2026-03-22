# Mockup 01: Dashboard Hero - Asset Generation Guide
**Developer**: Marcus Daley
**Date**: 2026-02-24
**Purpose**: Complete guide for generating AI assets and implementing Spline 3D scenes

## Overview

This guide provides exact prompts for Nano Banana Pro asset generation and Spline 3D scene specifications for Mockup 01: Dashboard Hero.

---

## Nano Banana Pro Asset Generation

### How to Generate Assets

**Option 1: Figma Plugin** (Recommended)
1. Open Figma
2. Install "Nano Banana Pro AI" plugin from Figma Community
3. Create new artboard (4096x4096 for backgrounds, 2048x2048 for textures)
4. Run plugin → Enter prompt → Generate 4 variations
5. Select best result → Export as PNG

**Option 2: Google AI Studio**
1. Visit [aistudio.google.com](https://aistudio.google.com/models/gemini-2-5-flash-image)
2. Select "Gemini 3 Pro Image" (Nano Banana Pro)
3. Paste prompt → Generate
4. Download result (4K resolution)

**Option 3: Google Antigravity** (for developers)
```python
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel('gemini-3-pro-image')

response = model.generate_images(
    prompt="Your prompt here",
    number_of_images=4,
    resolution="4096x4096"
)
```

---

## Asset #1: Background Texture

### Prompt
```
Dark navy gradient cybersecurity dashboard background with subtle
circuit board pattern overlay, glowing teal accent lines radiating
from center, professional monitoring software aesthetic, 4K resolution
seamless tileable pattern, cinematic sci-fi lighting with depth,
modern command center vibe, no text or UI elements
```

### Settings
- **Resolution**: 4096x4096 pixels
- **Format**: PNG (RGB)
- **Aspect Ratio**: 1:1 (will be scaled to 1920x1080 at runtime)
- **Style Consistency**: Enable "style reference" mode if generating multiple backgrounds

### Export Location
`C:\ClaudeSkills\scripts\gui\assets\backgrounds\dashboard_dark.png`

### PyQt6 Implementation
```python
from PyQt6.QtGui import QPixmap, QPalette, QBrush
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def _set_background(self) -> None:
        """Apply Nano Banana background to main window."""
        bg_path = ASSETS_DIR / "backgrounds" / "dashboard_dark.png"
        pixmap = QPixmap(str(bg_path))

        # Scale to window size maintaining aspect ratio
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        palette = QPalette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
```

---

## Asset #2: Glass Morphism Panel Texture

### Prompt
```
Translucent frosted glass panel texture with soft blur effect,
subtle neon teal border glow, modern UI glassmorphism style for
dark cybersecurity theme, 2048x2048 PNG with alpha transparency channel,
soft drop shadow gradient, professional desktop application aesthetic,
semi-transparent with bokeh blur
```

### Settings
- **Resolution**: 2048x2048 pixels
- **Format**: PNG with alpha channel (RGBA)
- **Transparency**: 60-70% opacity
- **Blur Radius**: Medium (simulate backdrop-filter)

### Export Location
`C:\ClaudeSkills\scripts\gui\assets\textures\glass_panel_dark.png`

### PyQt6 Implementation
```python
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QFrame

class GlassMorphPanel(QFrame):
    """Frosted glass panel using Nano Banana texture."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        # Apply Nano Banana texture as background
        self.setStyleSheet(f"""
            QFrame {{
                background-image: url({ASSETS_DIR}/textures/glass_panel_dark.png);
                background-position: center;
                background-repeat: no-repeat;
                background-size: cover;
                border: 1px solid rgba(79, 209, 197, 0.3);
                border-radius: 12px;
            }}
        """)

        # Add opacity effect
        opacity = QGraphicsOpacityEffect(self)
        opacity.setOpacity(0.7)
        self.setGraphicsEffect(opacity)
```

---

## Asset #3: File Type Icons (Set of 6)

### Prompts

**Icon 1: Document File**
```
3D isometric file document icon with folded corner, glass material
with soft teal glow, modern UI icon design, 512x512 PNG with alpha
transparency, cybersecurity aesthetic, professional software icon,
subtle drop shadow
```

**Icon 2: Python Script**
```
3D isometric Python file icon with snake logo embossed, glass material
with soft teal glow, modern UI icon design, 512x512 PNG with alpha
transparency, code file aesthetic, professional developer tool icon
```

**Icon 3: Configuration File**
```
3D isometric gear/cog icon representing settings file, glass material
with soft yellow-orange glow, modern UI icon design, 512x512 PNG with
alpha transparency, configuration aesthetic, technical icon style
```

**Icon 4: Database File**
```
3D isometric database cylinder icon, glass material with soft purple glow,
modern UI icon design, 512x512 PNG with alpha transparency, data storage
aesthetic, professional database icon
```

**Icon 5: Log File**
```
3D isometric lock/security icon representing audit log, glass material
with soft red glow, modern UI icon design, 512x512 PNG with alpha
transparency, security aesthetic, warning state indicator
```

**Icon 6: Package File**
```
3D isometric package/box icon, glass material with soft green glow,
modern UI icon design, 512x512 PNG with alpha transparency, bundle
aesthetic, deployment icon style
```

### Settings (All Icons)
- **Resolution**: 512x512 pixels
- **Format**: PNG with alpha channel
- **View**: Isometric 3D (45° angle)
- **Material**: Glass with subtle glow
- **Shadow**: Soft drop shadow 10px blur

### Export Location
`C:\ClaudeSkills\scripts\gui\assets\icons\file_[type].png`

### PyQt6 Implementation
```python
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QPushButton

class FileButton(QPushButton):
    """File button with Nano Banana generated icon."""

    def __init__(self, file_type: str, parent: QWidget | None = None):
        super().__init__(parent)

        # Load Nano Banana icon
        icon_path = ASSETS_DIR / "icons" / f"file_{file_type}.png"
        icon = QIcon(str(icon_path))
        self.setIcon(icon)
        self.setIconSize(QSize(48, 48))
```

---

## Spline 3D Scene Specifications

### Scene #1: Owl Mascot (Header Version)

**Scene Name**: `owl_idle_header.splinecode`

**Specifications**:
- **Size**: 56x56 pixels (compact for header)
- **Triangle Count**: <800 triangles
- **Animation**: Subtle breathing loop (2s duration)
  - Y position: +2 to -2 pixels
  - Scale: 1.0 to 1.02
- **Materials**:
  - Base color: `#F5DEB3` (wheat)
  - Rim light: `#4FD1C5` (teal), intensity 0.6
  - Shader: Toon style
- **Camera**: Orthographic, front-facing
- **Background**: Transparent

**Spline Editor Steps**:
1. Create sphere (head), scale to 40px diameter
2. Add two smaller spheres (eyes), scale to 8px
3. Add cone (beak), rotate -90°, scale to 6px
4. Add two cylinders (wings), rotate for folded position
5. Apply toon material with teal rim light
6. Create animation:
   - Keyframe 0s: Y=0, scale=1.0
   - Keyframe 1s: Y=-2, scale=1.02
   - Keyframe 2s: Y=0, scale=1.0 (loop)
7. Export → Scene → `.splinecode` format

**Export Location**:
`C:\ClaudeSkills\scripts\gui\assets\spline\owl_idle_header.splinecode`

---

### Scene #2: Moon Toggle Button

**Scene Name**: `moon_toggle.splinecode`

**Specifications**:
- **Size**: 64x64 pixels
- **Triangle Count**: <600 triangles
- **Animation**: Continuous rotation (20s duration)
  - Y-axis rotation: 0° to 360°
- **Particle System**: 8 orbiting star particles
  - Orbit radius: 40px
  - Particle size: 4px
  - Orbit speed: 5s per revolution
- **Materials**:
  - Crescent moon: Emissive white, intensity 0.8
  - Particles: Emissive teal, intensity 1.0
- **Interaction**: Click to toggle state (moon ↔ sun)
  - Moon state: Crescent shape
  - Sun state: Full circle with rays
- **Camera**: Orthographic, front-facing
- **Background**: Transparent

**Spline Editor Steps**:
1. Create sphere (moon body), scale to 32px
2. Use boolean subtraction to create crescent shape
3. Create particle emitter:
   - Type: Point emitter
   - Count: 8 particles
   - Lifetime: Infinite
   - Velocity: Circular orbit path
4. Create animation (moon state):
   - Continuous Y-axis rotation: 0° → 360° over 20s
5. Create animation (sun state):
   - Change material to full emissive
   - Add 8 ray spikes around perimeter
   - Same rotation animation
6. Setup event triggers:
   - `mouseDown` → trigger state transition animation
   - Duration: 0.5s flip animation (180° rotation on X-axis)
7. Export → Scene → `.splinecode` format (both states)

**Export Location**:
- `C:\ClaudeSkills\scripts\gui\assets\spline\moon_dark_mode.splinecode`
- `C:\ClaudeSkills\scripts\gui\assets\spline\moon_light_mode.splinecode`

---

### Scene #3: Large Owl Mascot (Center Stage)

**Scene Name**: `owl_idle_large.splinecode`

**Specifications**:
- **Size**: 256x256 pixels (display size, 512x512 texture)
- **Triangle Count**: <1,200 triangles
- **Animation**: Enhanced breathing + floating
  - Y position: +10 to -10 pixels (4s duration)
  - Scale: 1.0 to 1.05 (pulse effect)
  - Rotation X: -5° to +5° (gentle sway)
  - Eye blink: Every 3-5 seconds (random interval)
- **Materials**:
  - Body: Toon shader, base `#F5DEB3`, rim `#4FD1C5`
  - Eyes: Emissive white, intensity 0.9
  - Beak: Toon shader, base `#FFA500` (orange)
- **Glow Ring**:
  - Separate object, 300px diameter ring
  - Emissive teal, opacity 0.3
  - Pulsing scale animation (3s duration)
- **Camera**: Perspective, slight angle (15° tilt)
- **Background**: Transparent with radial gradient glow

**Spline Editor Steps**:
1. Import owl_idle_header.splinecode as base
2. Scale entire model 4x (to 256px display size)
3. Enhance details:
   - Add feather texture (normal map)
   - Increase eye detail (add pupils, highlights)
   - Add eyebrow geometry for expression
4. Create enhanced animations:
   - **Breathing**: Y position sine wave, 4s loop
   - **Pulse**: Scale 1.0 → 1.05 → 1.0, sync with breathing
   - **Sway**: Rotation X sine wave, 6s loop (offset from breathing)
   - **Blink**: Eyes scale Y: 1.0 → 0.1 → 1.0, 0.2s duration, trigger every 3-5s
5. Create glow ring object:
   - Torus shape, 300px diameter
   - Emissive material, teal color
   - Animation: Scale 1.0 → 1.1 → 1.0, 3s loop, opacity pulse
6. Setup camera:
   - Perspective projection
   - FOV: 50°
   - Position: (0, 30, 300) looking at owl center
   - Slight tilt: 15° on X-axis
7. Add ambient light (soft from top)
8. Export → Scene → `.splinecode` format

**Export Location**:
`C:\ClaudeSkills\scripts\gui\assets\spline\owl_idle_large.splinecode`

---

### Scene #4: File Cube Grid (6 cubes)

**Scene Name**: `file_grid.splinecode`

**Specifications**:
- **Size**: 1640x180 pixels (fits bottom panel grid)
- **Cube Count**: 6 cubes
- **Cube Size**: 80x80 pixels each
- **Spacing**: 20px gap between cubes
- **Triangle Count**: <400 per cube (2,400 total)
- **Animation**: Individual floating + hover states
  - Idle: Y position +3 to -3 pixels (3s duration, staggered)
  - Hover: Scale 1.0 → 1.1, Y offset +10px (0.3s transition)
  - Glow: Emissive rim intensity 0.3 → 1.0 on hover
- **Materials**:
  - Base: Glass shader, teal tint, opacity 0.6
  - Glow: Emissive rim light, teal color
  - Icon: Billboard sprite (2D icon inside 3D cube)
- **Status Indicators**:
  - Top-right corner orb (12px diameter)
  - Colors: Green (synced), Yellow (modified), Red (error)
  - Pulsing animation for modified/error states
- **Camera**: Isometric view (45° angle)
- **Background**: Transparent

**Spline Editor Steps**:
1. Create cube primitive (80x80x80px)
2. Apply glass material:
   - Base color: `#4FD1C5` (teal), opacity 0.6
   - Rim light: intensity 0.3 (increases to 1.0 on hover)
   - Refraction: 0.2 (subtle transparency)
3. Add billboard icon slot:
   - Plane object inside cube (60x60px)
   - Always faces camera (billboard constraint)
   - UV mapped to load external icon textures
4. Add status indicator:
   - Small sphere, top-right corner of cube
   - 12px diameter
   - Emissive material (changes color based on state)
5. Create idle animation (per cube):
   - Y position sine wave: +3 to -3 pixels
   - Duration: 3s
   - Stagger start: Cube 1 (0s), Cube 2 (0.2s), Cube 3 (0.4s), etc.
6. Create hover animation:
   - Trigger: `mouseHover` event
   - Scale: 1.0 → 1.1 (0.3s ease-out)
   - Y position: current → current + 10px
   - Rim intensity: 0.3 → 1.0
   - Glow ring: fade in outer ring (300px)
7. Duplicate cube 5 times (6 total)
8. Arrange in horizontal line (100px spacing center-to-center)
9. Setup camera:
   - Orthographic projection
   - Isometric angle: 45° on both X and Y axes
   - Centered on cube array
10. Create variants for file types:
    - Load different icon textures per cube
    - Set status indicator colors
11. Export → Scene → `.splinecode` format

**Export Location**:
`C:\ClaudeSkills\scripts\gui\assets\spline\file_grid.splinecode`

**Icon Texture References** (use Nano Banana generated icons):
- Cube 1: `file_document.png` (status: green)
- Cube 2: `file_python.png` (status: green)
- Cube 3: `file_config.png` (status: yellow)
- Cube 4: `file_database.png` (status: green)
- Cube 5: `file_log.png` (status: red)
- Cube 6: `file_package.png` (status: green)

---

## PyQt6 Integration - Complete Widget

### Spline3DWidget Implementation

```python
# spline_3d_widget.py
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QUrl, pyqtSlot, QObject
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QWidget

from gui.paths import ASSETS_DIR


class SplineBridge(QObject):
    """JavaScript ↔ Python bridge for Spline Runtime communication."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

    @pyqtSlot(str)
    def on_moon_clicked(self, state: str) -> None:
        """Called from JavaScript when moon toggle is clicked."""
        # Forward to main window theme manager
        if self.parent():
            self.parent().theme_manager.toggle_theme()

    @pyqtSlot(str)
    def on_file_clicked(self, file_id: str) -> None:
        """Called from JavaScript when file cube is clicked."""
        # Show file details panel
        print(f"File clicked: {file_id}")

    @pyqtSlot(str)
    def on_owl_state_changed(self, state: str) -> None:
        """Called from JavaScript when owl animation state changes."""
        print(f"Owl state: {state}")


class Spline3DWidget(QWebEngineView):
    """Embeds a Spline 3D scene in PyQt6 with bidirectional communication."""

    def __init__(
        self,
        scene_name: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._scene_name = scene_name

        # Setup JavaScript bridge
        self._channel = QWebChannel()
        self._bridge = SplineBridge(self)
        self._channel.registerObject("bridge", self._bridge)
        self.page().setWebChannel(self._channel)

        # Load HTML wrapper with embedded Spline scene
        html_path = ASSETS_DIR / "spline" / f"{scene_name}.html"
        if not html_path.exists():
            # Generate HTML wrapper
            self._generate_html_wrapper(scene_name)

        self.load(QUrl.fromLocalFile(str(html_path)))

    def _generate_html_wrapper(self, scene_name: str) -> None:
        """Generate HTML wrapper for Spline scene."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            margin: 0;
            overflow: hidden;
            background: transparent;
        }}
        canvas {{
            width: 100%;
            height: 100%;
            display: block;
        }}
    </style>
    <script src="https://unpkg.com/@splinetool/runtime@latest"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
</head>
<body>
    <canvas id="canvas3d"></canvas>
    <script>
        const canvas = document.getElementById('canvas3d');
        const app = new window.SPLINE.Application(canvas);

        // Load .splinecode file
        app.load('/assets/spline/{scene_name}.splinecode').then(() => {{
            console.log('Spline scene loaded: {scene_name}');
            window.splineApp = app;

            // Setup QWebChannel bridge
            new QWebChannel(qt.webChannelTransport, (channel) => {{
                const bridge = channel.objects.bridge;

                // Forward Spline events to Python
                app.addEventListener('mouseDown', (e) => {{
                    if (e.target.name === 'MoonToggle') {{
                        bridge.on_moon_clicked('toggle');
                    }}
                    if (e.target.name.startsWith('FileCube')) {{
                        bridge.on_file_clicked(e.target.id);
                    }}
                    if (e.target.name === 'OwlBody') {{
                        bridge.on_owl_state_changed('clicked');
                    }}
                }});

                // Listen for state changes from Python
                window.setOwlState = (state) => {{
                    app.emitEvent('start', `Owl_${{state}}_Anim`);
                }};
            }});
        }});
    </script>
</body>
</html>
        """

        html_path = ASSETS_DIR / "spline" / f"{scene_name}.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_content, encoding="utf-8")

    def trigger_animation(self, event_name: str, target: str) -> None:
        """Trigger Spline animation from Python."""
        js_code = f"""
        if (window.splineApp) {{
            window.splineApp.emitEvent('{event_name}', '{target}');
        }}
        """
        self.page().runJavaScript(js_code)

    def set_state(self, state: str) -> None:
        """Change owl state (triggers state machine in Spline)."""
        js_code = f"""
        if (window.setOwlState) {{
            window.setOwlState('{state}');
        }}
        """
        self.page().runJavaScript(js_code)
```

### MainWindow Integration

```python
# main_window.py (excerpt)
from gui.widgets.spline_3d_widget import Spline3DWidget

class OwlWatcherMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Apply Nano Banana background
        self._set_background()

        # Header with Spline owl + moon
        header = QWidget()
        header_layout = QHBoxLayout(header)

        self._owl_header = Spline3DWidget("owl_idle_header", parent=header)
        self._owl_header.setFixedSize(56, 56)
        header_layout.addWidget(self._owl_header)

        self._title = QLabel("OwlWatcher")
        header_layout.addWidget(self._title)

        header_layout.addStretch()

        self._moon_toggle = Spline3DWidget("moon_toggle", parent=header)
        self._moon_toggle.setFixedSize(64, 64)
        header_layout.addWidget(self._moon_toggle)

        # Central owl (large)
        self._owl_large = Spline3DWidget("owl_idle_large", parent=self)
        # ... position in center

        # File grid
        self._file_grid = Spline3DWidget("file_grid", parent=self)
        # ... position in bottom panel
```

---

## Testing Checklist

### Visual Verification
- [ ] Background gradient matches mockup (dark navy with teal accents)
- [ ] Glass panels have frosted appearance with teal glow
- [ ] File icons are consistent style (3D isometric glass)
- [ ] Owl proportions correct (56px header, 256px center)
- [ ] Moon has visible orbital particles
- [ ] File cubes show status indicators (green/yellow/red)

### Animation Verification
- [ ] Header owl breathes subtly (2s loop)
- [ ] Large owl floats + pulses (4s loop)
- [ ] Moon rotates continuously (20s)
- [ ] File cubes float with stagger (3s per cube)
- [ ] Hover effects work on all interactive elements

### Interaction Verification
- [ ] Moon toggle switches theme (dark ↔ light)
- [ ] File cubes scale up on hover
- [ ] File cubes open details panel on click
- [ ] Owl responds to click (state change or speech bubble)

### Performance Verification
- [ ] 60fps maintained on 1920x1080 display
- [ ] Memory usage under 100MB for Spline scenes
- [ ] No stuttering during animation loops
- [ ] WebGL detection fallback works (if no GPU)

---

## File Structure Summary

```
C:\ClaudeSkills\scripts\gui\
├── assets\
│   ├── backgrounds\
│   │   └── dashboard_dark.png              # Nano Banana (4096x4096)
│   ├── textures\
│   │   └── glass_panel_dark.png            # Nano Banana (2048x2048)
│   ├── icons\
│   │   ├── file_document.png               # Nano Banana (512x512)
│   │   ├── file_python.png
│   │   ├── file_config.png
│   │   ├── file_database.png
│   │   ├── file_log.png
│   │   └── file_package.png
│   └── spline\
│       ├── owl_idle_header.splinecode      # Spline 3D (56x56)
│       ├── owl_idle_header.html
│       ├── moon_toggle.splinecode          # Spline 3D (64x64)
│       ├── moon_toggle.html
│       ├── owl_idle_large.splinecode       # Spline 3D (256x256)
│       ├── owl_idle_large.html
│       ├── file_grid.splinecode            # Spline 3D (1640x180)
│       └── file_grid.html
└── widgets\
    └── spline_3d_widget.py                 # PyQt6 integration widget
```

---

## Next Steps

1. **Generate Nano Banana Assets** (Est. 2 hours)
   - Use Figma plugin or Google AI Studio
   - Export all assets to correct directories
   - Verify resolution and format

2. **Create Spline 3D Scenes** (Est. 6 hours)
   - Model owl mascot in Spline Editor
   - Create moon toggle with particles
   - Build file cube grid with interactions
   - Export all `.splinecode` files

3. **Integrate into PyQt6** (Est. 4 hours)
   - Implement `Spline3DWidget` class
   - Update `MainWindow` layout
   - Setup QWebChannel bridge
   - Test all interactions

4. **Polish & Test** (Est. 2 hours)
   - Verify animations at 60fps
   - Test theme toggle functionality
   - Ensure WebGL fallback works
   - Document any issues

**Total Estimated Time**: 14 hours
