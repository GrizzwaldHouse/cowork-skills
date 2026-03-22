# OwlWatcher UI Mockup Master Plan
**Developer**: Marcus Daley
**Date**: 2026-02-24
**Purpose**: Comprehensive mockup strategy for 12+ design variations using Spline 3D + Nano Banana Pro AI

## Overview

This document outlines a complete strategy for creating 12+ high-fidelity UI mockups for OwlWatcher, combining:
- **Spline 3D**: Interactive 3D elements (owl mascot, moon toggle, file visualizations)
- **Nano Banana Pro**: Google's Gemini 3 Pro Image model for photorealistic UI assets, textures, and backgrounds
- **PyQt6 Integration**: Production-ready implementation patterns for desktop deployment

**Date Context**: As of February 24, 2026, both Nano Banana (August 2025) and Nano Banana Pro (November 2025) are available for use.

## Technology Stack

### Spline 3D (spline.design)
- Interactive 3D web scenes with JavaScript runtime
- Integrates with PyQt6 via QWebEngineView + QWebChannel
- Supports real-time animation state changes
- Export formats: `.splinecode`, embedded HTML, React components

### Nano Banana Pro
- Google AI image generation model (Released November 20, 2025)
- **Key Features**:
  - Photorealistic 4K resolution output
  - Accurate text rendering (perfect for UI labels, buttons)
  - Strong spatial understanding (layout-aware generation)
  - Available as Figma plugin + Google Antigravity integration
- **Use Cases**:
  - Background textures (cybersecurity-themed gradients, particle fields)
  - Icon generation (file type icons, status badges, alert symbols)
  - UI chrome (glass morphism panels, holographic overlays)
  - Marketing assets (hero banners, feature showcases)

### PyQt6 Desktop Integration
- QWebEngineView for Spline 3D embedding
- QWebChannel for Python ↔ JavaScript bidirectional communication
- Theme system (dark/light mode with persistent state)
- Custom widget library (OwlWidget, AmbientBackgroundWidget, DashboardWidget)

---

## The 12+ Mockup Collection

### Category 1: Core Layout Variations (4 mockups)

#### Mockup 1: **Dashboard Hero** (Current Design Enhanced)
**Theme**: Dark mode cybersecurity command center
**Spline 3D Elements**:
- Large 3D owl (center, 256px) with idle breathing animation
- Rotating moon toggle (top-right, 64px) with orbital particle ring
- 3D file cube grid (bottom panel, 6 floating cubes with glow)
**Nano Banana Prompts**:
- Background: "Dark navy gradient cybersecurity dashboard background with subtle circuit board patterns and glowing teal accents, 4K resolution"
- Panel texture: "Translucent glass morphism panel with frosted blur effect, subtle neon border glow"
**Layout**: Full dashboard with header, sidebar stats, central owl, bottom file grid

#### Mockup 2: **Minimal Sidebar**
**Theme**: Light mode clean workspace
**Spline 3D Elements**:
- Compact 3D owl (left sidebar, 96px) in sidebar header
- 2D moon toggle (header, flat icon)
- Vertical 3D file stack (sidebar, 4 stacked cubes with hover states)
**Nano Banana Prompts**:
- Background: "Soft white gradient with subtle geometric patterns, professional clean UI aesthetic"
- Sidebar: "Matte light gray panel with soft drop shadow, modern workspace design"
**Layout**: Left sidebar (200px) + main content area (file details, logs)

#### Mockup 3: **Fullscreen Immersive**
**Theme**: Dark mode no-chrome experience
**Spline 3D Elements**:
- Massive 3D owl (center, 512px) as primary focus
- Floating 3D moon orb (top-right, 128px, levitating with glow)
- Holographic 3D file ring (surrounding owl, 12 orbiting cubes)
**Nano Banana Prompts**:
- Background: "Deep space nebula with teal and purple auroras, cinematic sci-fi aesthetic, 4K"
- Hologram overlay: "Transparent HUD overlay with glowing teal scan lines and data visualization"
**Layout**: No borders, floating elements, gesture-driven controls

#### Mockup 4: **Split Panel Pro**
**Theme**: Dark mode dual-pane workflow
**Spline 3D Elements**:
- 3D owl (left panel header, 80px)
- 3D file browser (left panel, grid of cubes)
- 3D log visualizer (right panel, scrolling 3D timeline)
**Nano Banana Prompts**:
- Left panel: "Dark charcoal panel with subtle noise texture"
- Right panel: "Navy panel with animated scan lines, terminal aesthetic"
**Layout**: 50/50 vertical split, synchronized scroll

---

### Category 2: State-Driven Designs (4 mockups)

#### Mockup 5: **Scanning Active State**
**Theme**: Dark mode with animated scan overlay
**Spline 3D Elements**:
- 3D owl in "scanning" pose (eyes wide, head rotating)
- Pulsing radar wave (emanating from owl center)
- 3D file cubes with scan beam highlight
**Nano Banana Prompts**:
- Scan overlay: "Transparent teal radar sweep with radial gradient, cybersecurity scanning effect"
- Active files: "Glowing teal file icons with pulse animation, high-tech UI elements"
**Layout**: Dashboard with animated scan overlay

#### Mockup 6: **Alert Critical State**
**Theme**: Dark mode with red warning indicators
**Spline 3D Elements**:
- 3D owl in "alarm" pose (feathers ruffled, eyes glowing red)
- Spinning red orb (above owl, 64px danger beacon)
- 3D file cubes with red danger highlights
**Nano Banana Prompts**:
- Alert background: "Dark red gradient with warning stripes, urgent UI state"
- Threat indicator: "Glowing red shield icon with cracks, danger visualization"
**Layout**: Dashboard with modal alert overlay

#### Mockup 7: **Idle Sleeping State**
**Theme**: Light mode low-power display
**Spline 3D Elements**:
- 3D owl in "sleeping" pose (eyes closed, Z's floating)
- Dim moon (low opacity, muted)
- Static 2D file grid (no animation)
**Nano Banana Prompts**:
- Background: "Soft cream gradient with cloud textures, peaceful aesthetic"
- Sleep overlay: "Transparent white vignette with soft blur"
**Layout**: Minimalist dashboard, reduced chrome

#### Mockup 8: **Proud Success State**
**Theme**: Dark mode with celebration effects
**Spline 3D Elements**:
- 3D owl in "proud" pose (chest puffed, wings spread)
- Gold confetti particles (3D particle system)
- 3D file cubes with green checkmarks
**Nano Banana Prompts**:
- Success background: "Dark navy with gold sparkle particles, celebration UI"
- Badge: "Shiny gold achievement badge with 3D depth, reward icon"
**Layout**: Dashboard with success banner

---

### Category 3: Advanced Integrations (4 mockups)

#### Mockup 9: **AR Overlay Concept**
**Theme**: Transparent overlay for desktop integration
**Spline 3D Elements**:
- Floating 3D owl (no background, pure transparency)
- Holographic moon toggle (glass effect)
- AR-style file markers (minimal 3D indicators)
**Nano Banana Prompts**:
- Holographic elements: "Transparent glass UI elements with edge glow, AR interface aesthetic"
- Markers: "Minimal floating location pins with holographic material"
**Layout**: Frameless transparent window, always-on-top mode

#### Mockup 10: **Multi-Monitor Command Center**
**Theme**: Dark mode ultra-wide layout
**Spline 3D Elements**:
- Triple 3D owl views (left: sleeping, center: scanning, right: alert)
- Synchronized 3D moon phases (3 moons showing different states)
- Massive 3D file globe (center, 512px, files on sphere surface)
**Nano Banana Prompts**:
- Ultra-wide BG: "Seamless dark gradient spanning 5760px width, cinematic command center"
- Globe texture: "Sci-fi holographic sphere with glowing node connections"
**Layout**: 3-panel ultra-wide (1920x1080 per panel)

#### Mockup 11: **Mobile Companion Concept**
**Theme**: Light mode touch-optimized
**Spline 3D Elements**:
- Small 3D owl (top, 64px, touch-friendly size)
- Large tap target moon (96px button)
- Swipeable 3D file cards (horizontal carousel)
**Nano Banana Prompts**:
- Mobile BG: "Light gradient with bottom-to-top fade, mobile UI aesthetic"
- Cards: "Frosted glass cards with drop shadows, iOS design language"
**Layout**: Mobile portrait (375x812), bottom navigation

#### Mockup 12: **Web Dashboard Port**
**Theme**: Dark mode responsive web app
**Spline 3D Elements**:
- Embedded Spline scene (React component, full viewport)
- Interactive 3D owl (click to trigger animations)
- Live 3D stats orbs (updating metrics visualization)
**Nano Banana Prompts**:
- Web chrome: "Dark modern web app header with glassmorphism navbar"
- Stats panels: "Dark cards with gradient borders, data dashboard UI"
**Layout**: Responsive flexbox grid, adapts 320px - 2560px

---

### Bonus Mockups (Optional Explorations)

#### Mockup 13: **Retro Terminal Theme**
**Spline 3D**: Pixelated 3D owl (voxel art style)
**Nano Banana**: "Retro CRT monitor scanlines, green phosphor glow, vintage terminal aesthetic"

#### Mockup 14: **Neon Cyberpunk**
**Spline 3D**: Chrome 3D owl with reflections
**Nano Banana**: "Neon pink and cyan cityscape, Blade Runner aesthetic, rain effects"

#### Mockup 15: **Nature Organic Theme**
**Spline 3D**: Wooden carved owl (textured)
**Nano Banana**: "Forest scene with soft bokeh, natural wood textures, earthy UI palette"

---

## Implementation Workflow

### Phase 1: Asset Generation (Week 1)

#### Step 1.1: Nano Banana Pro Asset Creation
Use Figma plugin or Google Antigravity to generate:

1. **Backgrounds** (12 variations, 4K resolution):
   ```
   Prompt Template:
   "[Theme description] background for desktop UI application,
   4K resolution, seamless tileable pattern, [mood keywords],
   professional software interface aesthetic"
   ```

2. **Textures** (6 variations):
   - Glass morphism panels (dark + light)
   - Holographic overlays
   - Alert/warning gradients
   - Success celebration effects
   - Particle systems (nebula, confetti, scan lines)

3. **Icons & Badges** (20+ variations):
   - File type indicators (documents, images, code, data)
   - Status badges (synced, modified, error, new)
   - Action buttons (play, pause, refresh, settings)

**Nano Banana Settings**:
- Resolution: 4096x4096 (backgrounds), 512x512 (icons)
- Style consistency: Use same prompt structure + style reference
- Text rendering: Enable "perfect text" mode for button labels

#### Step 1.2: Spline 3D Scene Creation
Create in Spline Editor (spline.design):

1. **Owl Mascot States** (8 scenes):
   - Sleeping (eyes closed, Z's particle emitter)
   - Waking (eyes half-open, stretch animation)
   - Idle (breathing loop, occasional blink)
   - Scanning (head rotation 360°, eyes glow)
   - Curious (head tilt, pupils dilate)
   - Alert (wide eyes, feather ruffle)
   - Alarm (red glow, shake animation)
   - Proud (wings spread, chest puff)

   **3D Modeling Notes**:
   - Base mesh: 1,200 triangles (optimized for real-time)
   - Materials: Cartoon shader with rim lighting
   - Animation: State machine with crossfade transitions
   - Export: `.splinecode` files for web embedding

2. **Moon Toggle** (2 states):
   - Crescent moon (dark mode indicator)
   - Sun (light mode indicator)
   - Rotation animation (180° flip on toggle)
   - Particle ring (orbiting stars)

3. **File Visualizations** (3 layouts):
   - Grid of cubes (6x6, hover grow effect)
   - Vertical stack (4 cards, drag-to-reorder)
   - Globe sphere (files on surface, rotate to browse)

   **Interaction Events**:
   - `onMouseDown`: Select file, show details panel
   - `onMouseHover`: Highlight file, show tooltip
   - `onDrag`: Reorder files in stack/grid

4. **Stats Orbs** (3 types):
   - Health orb (green, pulsing)
   - Threat orb (red, rotating with spikes)
   - Activity chart (3D bar graph, real-time updates)

**Spline Export Settings**:
- Format: `.splinecode` (compressed binary)
- Texture resolution: 1024px (balance quality vs size)
- Enable physics: No (static scenes only)
- Optimize for web: Yes (reduce draw calls)

### Phase 2: Figma Mockup Assembly (Week 2)

#### Step 2.1: Create Figma File Structure
```
OwlWatcher Mockups/
├── 📁 00_Assets/
│   ├── Backgrounds (12 PNG from Nano Banana)
│   ├── Textures (6 PNG overlays)
│   ├── Icons (20+ SVG/PNG)
│   └── Spline Previews (screenshots of 3D scenes)
├── 📁 01_Core_Layouts/ (Mockups 1-4)
├── 📁 02_State_Driven/ (Mockups 5-8)
├── 📁 03_Advanced/ (Mockups 9-12)
└── 📁 04_Bonus/ (Mockups 13-15)
```

#### Step 2.2: Assembly Process per Mockup
For each of the 12+ mockups:

1. **Create artboard** (1920x1080 for desktop, adjust for mobile/web)
2. **Apply Nano Banana background** (drag PNG from Assets)
3. **Add Spline 3D placeholders**:
   - Export screenshot from Spline Editor (1920x1080, transparent PNG)
   - Place in Figma with note: "SPLINE 3D SCENE - owl_[state].splinecode"
   - Add interactive overlay (click zones with hotspot markers)
4. **Add UI chrome** (headers, panels, buttons using Nano Banana textures)
5. **Typography** (use system fonts for mockup, note PyQt6 font equivalents):
   - Headers: Segoe UI Semibold 24pt
   - Body: Segoe UI Regular 14pt
   - Labels: Segoe UI Regular 10pt
6. **Annotations**:
   - Label Spline 3D zones with orange boxes
   - Label Nano Banana assets with purple boxes
   - Add implementation notes as comment threads

#### Step 2.3: Interactive Prototype
In Figma Prototype mode:
- Link moon toggle between dark/light variants
- Create hotspots on owl → opens state selector menu
- Simulate file hover (show detail panel transition)
- Add state transitions (idle → scanning → alert flow)

**Export for development**:
- All artboards as PNG (2x resolution: 3840x2160)
- CSS specs via Figma Inspect panel (copy as PyQt6 StyleSheet)
- Interactive prototype shareable link

### Phase 3: PyQt6 Implementation (Weeks 3-4)

#### Step 3.1: Integrate Nano Banana Assets

**Store assets**:
```python
# Directory structure
gui/
├── assets/
│   ├── backgrounds/
│   │   ├── dashboard_dark.png        # Nano Banana generated
│   │   ├── dashboard_light.png
│   │   └── ...
│   ├── textures/
│   │   ├── glass_panel_dark.png
│   │   ├── hologram_overlay.png
│   │   └── ...
│   └── icons/
│       ├── file_document.png
│       └── ...
```

**Load in PyQt6**:
```python
from PyQt6.QtGui import QPixmap, QPalette, QBrush
from gui.paths import ASSETS_DIR

class ThemedBackgroundWidget(QWidget):
    """Widget with Nano Banana generated background."""

    def __init__(self, theme: str = "dark", parent: QWidget | None = None):
        super().__init__(parent)
        self._theme = theme
        self._load_background()

    def _load_background(self) -> None:
        bg_path = ASSETS_DIR / "backgrounds" / f"dashboard_{self._theme}.png"
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

**Glass morphism panel** (using Nano Banana texture):
```python
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QGraphicsBlurEffect

class GlassMorphPanel(QFrame):
    """Frosted glass panel using Nano Banana texture."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }
        """)

        # Load Nano Banana frosted texture as overlay
        texture = QLabel(self)
        texture_pixmap = QPixmap(str(ASSETS_DIR / "textures" / "glass_panel_dark.png"))
        texture.setPixmap(texture_pixmap)
        texture.setScaledContents(True)
        texture.setGeometry(self.rect())

        # Apply blur effect for glassmorphism
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(20)
        texture.setGraphicsEffect(blur)

        # Semi-transparent overlay
        opacity = QGraphicsOpacityEffect()
        opacity.setOpacity(0.3)
        texture.setGraphicsEffect(opacity)
```

#### Step 3.2: Integrate Spline 3D Scenes

**QWebEngineView integration**:
```python
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import pyqtSlot, QObject

class SplineBridge(QObject):
    """JavaScript ↔ Python bridge for Spline Runtime."""

    @pyqtSlot(str)
    def on_owl_state_changed(self, state: str) -> None:
        """Called from JavaScript when owl animation state changes."""
        logging.info(f"Owl state changed to: {state}")
        # Update Python-side state machine
        self.parent().set_owl_state(state)

    @pyqtSlot(str)
    def on_file_clicked(self, file_id: str) -> None:
        """Called from JavaScript when 3D file cube is clicked."""
        logging.info(f"File clicked: {file_id}")
        # Show file details panel

class Spline3DWidget(QWebEngineView):
    """Embeds Spline 3D scene in PyQt6."""

    def __init__(self, scene_name: str, parent: QWidget | None = None):
        super().__init__(parent)

        # Setup JavaScript bridge
        self._channel = QWebChannel()
        self._bridge = SplineBridge(self)
        self._channel.registerObject("bridge", self._bridge)
        self.page().setWebChannel(self._channel)

        # Load local HTML with embedded Spline scene
        html_path = ASSETS_DIR / "spline" / f"{scene_name}.html"
        self.load(QUrl.fromLocalFile(str(html_path)))

    def trigger_animation(self, event_name: str, target: str) -> None:
        """Trigger Spline animation from Python."""
        js_code = f"""
        if (window.splineApp) {{
            window.splineApp.emitEvent('{event_name}', '{target}');
        }}
        """
        self.page().runJavaScript(js_code)
```

**HTML template** (place in `gui/assets/spline/owl_idle.html`):
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { margin: 0; overflow: hidden; background: transparent; }
        canvas { width: 100%; height: 100%; }
    </style>
    <script src="https://unpkg.com/@splinetool/runtime@latest"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
</head>
<body>
    <canvas id="canvas3d"></canvas>
    <script>
        const canvas = document.getElementById('canvas3d');
        const app = new window.SPLINE.Application(canvas);

        // Load .splinecode file (generated from Spline Editor)
        app.load('/assets/spline/owl_idle.splinecode').then(() => {
            console.log('Spline scene loaded');
            window.splineApp = app;

            // Setup QWebChannel bridge
            new QWebChannel(qt.webChannelTransport, (channel) => {
                const bridge = channel.objects.bridge;

                // Forward Spline events to Python
                app.addEventListener('mouseDown', (e) => {
                    if (e.target.name === 'Owl') {
                        // Owl was clicked, notify Python
                        bridge.on_owl_state_changed('curious');
                    }
                    if (e.target.name.startsWith('FileCube')) {
                        bridge.on_file_clicked(e.target.id);
                    }
                });
            });
        });
    </script>
</body>
</html>
```

#### Step 3.3: State Machine Integration

Connect Spline 3D animations to OwlStateMachine:
```python
from gui.owl_state_machine import OwlStateMachine, OwlState
from gui.widgets.spline_3d_widget import Spline3DWidget

class OwlWatcherMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize state machine
        self._state_machine = OwlStateMachine()
        self._state_machine.state_changed.connect(self._on_owl_state_changed)

        # Initialize Spline 3D owl widget
        self._owl_3d = Spline3DWidget("owl_idle", parent=self)
        self.setCentralWidget(self._owl_3d)

        # Start in idle state
        self._state_machine.transition_to(OwlState.IDLE)

    def _on_owl_state_changed(self, new_state: OwlState) -> None:
        """Update Spline 3D scene when state machine transitions."""
        state_name = new_state.name.lower()

        # Load corresponding Spline scene
        self._owl_3d.load_scene(f"owl_{state_name}")

        # Or trigger animation in current scene
        self._owl_3d.trigger_animation('start', f'Owl_{state_name}_Anim')
```

---

## Guides for Advanced Design Implementation

### Guide 1: Nano Banana Pro Prompt Engineering for UI Assets

#### Best Practices for Consistent Output

**1. Use Style Reference Images**:
When generating a set of related assets, first generate a "style anchor" and reference it:
```
First prompt: "Dark navy cybersecurity dashboard background, teal accents"
→ Generate → Save as style_reference.png

Subsequent prompts: "Glass morphism panel texture [reference: style_reference.png]"
```

**2. Structured Prompt Template**:
```
[Subject] for [Context], [Style], [Technical Specs], [Mood]

Example:
"Holographic HUD overlay for desktop monitoring app, transparent glass material,
4K resolution seamless tileable, futuristic cybersecurity aesthetic"
```

**3. Iterate with Variations**:
Generate 4 variations per prompt, then:
- Select best candidate
- Use "Edit" mode to refine specific areas
- Apply "Upscale to 4K" for final export

**4. Text Rendering**:
For UI elements with text:
```
"Dark button with label 'Scan Now', glass morphism style, teal glow on hover,
accurate text rendering, professional UI design"
```
Enable "Perfect Text" mode in Figma plugin settings.

#### Asset Organization Workflow

**Figma Asset Library Setup**:
1. Create "OwlWatcher Assets" Figma file
2. Organize into components:
   - `/Backgrounds` → Variants for each theme
   - `/Textures` → Glass, metal, holographic
   - `/Icons` → File types, status badges
   - `/Effects` → Particles, glows, overlays
3. Publish as Team Library for reuse across mockups

**Export Settings**:
- Backgrounds: PNG, 4096x4096, 100% quality
- Textures: PNG with alpha, 2048x2048
- Icons: SVG (vector) + PNG fallback (512x512)

### Guide 2: Spline 3D Scene Optimization

#### Performance Budget

Target metrics for real-time 60fps on desktop:
- **Triangle count**: <5,000 per scene
- **Texture memory**: <50MB total
- **Draw calls**: <20 per frame
- **Animation curves**: <100 keyframes per state

#### Asset Creation in Spline Editor

**1. Owl Mascot Modeling**:
- Use Spline's primitive shapes (sphere, cylinder, cone) for base forms
- Apply "Subdivide" sparingly (prefer low-poly aesthetic)
- Materials: Use "Toon" shader with rim lighting
  - Base color: `#F5DEB3` (wheat)
  - Rim color: `#4FD1C5` (teal)
  - Rim intensity: 0.8

**2. Animation State Setup**:
```
Idle State:
- Y position: +5 to -5 (breathing loop, 2s duration)
- Rotation X: -2° to 2° (subtle sway)
- Eyes: Blink every 3-5 seconds (scale Y: 1.0 → 0.1 → 1.0, 0.2s)

Scanning State:
- Rotation Y: 0° → 360° (continuous rotation, 4s duration)
- Eyes: Glow emission (intensity: 0.0 → 1.0, pulse 1s)
- Head: Tilt forward 15° (detect gesture)

Alert State:
- Scale: 1.0 → 1.1 → 1.0 (pump animation, 0.5s loop)
- Feathers: Particle emitter (50 particles, upward velocity)
- Color: Shift to red tint (lerp base color to #FF4444)
```

**3. Export for PyQt6 Integration**:
- File → Export → Scene
- Format: `.splinecode` (optimized binary)
- Settings:
  - Compression: High
  - Include physics: No (unless interactive dragging needed)
  - Texture resolution: 1024px
- Output: Save to `gui/assets/spline/owl_[state].splinecode`

#### Fallback Strategy

If user's hardware doesn't support WebGL:
```python
def _check_webgl_support(self) -> bool:
    """Test if QWebEngineView can render WebGL."""
    test_html = """
    <canvas id="test"></canvas>
    <script>
        const canvas = document.getElementById('test');
        const gl = canvas.getContext('webgl');
        window.hasWebGL = (gl !== null);
    </script>
    """
    # ... test loading ...
    return result

# In MainWindow __init__:
if self._check_webgl_support():
    self._owl = Spline3DWidget("owl_idle")
else:
    # Fallback to pre-rendered sprite widget
    from gui.widgets.owl_3d_widget import Owl3DWidget
    self._owl = Owl3DWidget(owl_size=128)
    logging.warning("WebGL not supported, using 2D sprite fallback")
```

### Guide 3: Responsive Layout Patterns

#### Adaptive UI for Multiple Screen Sizes

**Breakpoints** (match common display resolutions):
```python
class ScreenSize(Enum):
    SMALL = 1366, 768    # Laptop
    MEDIUM = 1920, 1080  # Desktop
    LARGE = 2560, 1440   # 2K monitor
    XLARGE = 3840, 2160  # 4K monitor

class ResponsiveMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._current_layout = None
        self.resizeEvent = self._on_resize

    def _on_resize(self, event: QResizeEvent) -> None:
        width = event.size().width()

        if width < 1600:
            self._apply_layout(ScreenSize.SMALL)
        elif width < 2200:
            self._apply_layout(ScreenSize.MEDIUM)
        elif width < 3000:
            self._apply_layout(ScreenSize.LARGE)
        else:
            self._apply_layout(ScreenSize.XLARGE)

    def _apply_layout(self, size: ScreenSize) -> None:
        if self._current_layout == size:
            return  # Already applied

        match size:
            case ScreenSize.SMALL:
                # Compact: Hide sidebar, small owl
                self._owl.setFixedSize(64, 64)
                self._sidebar.hide()
            case ScreenSize.MEDIUM:
                # Standard: Show sidebar, medium owl
                self._owl.setFixedSize(128, 128)
                self._sidebar.show()
            case ScreenSize.LARGE | ScreenSize.XLARGE:
                # Expanded: Large owl, stats dashboard
                self._owl.setFixedSize(256, 256)
                self._stats_panel.show()

        self._current_layout = size
```

#### Dynamic Scaling for Spline 3D

Match Spline canvas resolution to window size:
```python
class Spline3DWidget(QWebEngineView):
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

        # Update canvas dimensions via JavaScript
        width = event.size().width()
        height = event.size().height()

        js_code = f"""
        if (window.splineApp) {{
            const canvas = document.getElementById('canvas3d');
            canvas.width = {width};
            canvas.height = {height};
            window.splineApp.resize();
        }}
        """
        self.page().runJavaScript(js_code)
```

---

## Best Practices for UI/GUI Design Tool

### Problem Statement
You want to create a **visual layout editor** for OwlWatcher (and future projects) that allows designing PyQt6 interfaces without hand-coding XML/Python.

### Recommended Architecture

#### Option 1: Extend Qt Designer (Recommended)
**Why**: Qt Designer is the official visual editor for PyQt6/PySide6, production-ready, and extensible via plugins.

**Workflow**:
1. Design layout in Qt Designer (drag-and-drop widgets)
2. Export to `.ui` file (XML format)
3. Convert to Python at build time: `pyuic6 layout.ui -o layout_ui.py`
4. Import in main app: `from gui.generated import Ui_MainWindow`

**Custom Widget Integration**:
Register OwlWidget, Spline3DWidget as custom widgets in Qt Designer:
```python
# designer_plugin.py (install in Qt Designer plugins folder)
from PyQt6.QtDesigner import QPyDesignerCustomWidgetPlugin
from gui.widgets.owl_widget import OwlWidget

class OwlWidgetPlugin(QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._initialized = False

    def initialize(self, core):
        if self._initialized:
            return
        self._initialized = True

    def isInitialized(self):
        return self._initialized

    def createWidget(self, parent):
        return OwlWidget(owl_size=128, parent=parent)

    def name(self):
        return "OwlWidget"

    def group(self):
        return "OwlWatcher Widgets"

    def icon(self):
        # Return QPixmap for toolbar icon
        return QPixmap(":/icons/owl.png")

    def toolTip(self):
        return "Animated owl mascot widget"
```

**Advantages**:
- ✅ Zero development cost (already exists)
- ✅ Official Qt tooling (well-documented)
- ✅ Live preview of layouts
- ✅ Property editor for widget configuration

**Limitations**:
- ❌ Cannot visually edit Spline 3D scenes (use Spline Editor for that)
- ❌ Limited styling (CSS must be applied via code)

#### Option 2: Build Custom Figma-to-PyQt6 Converter (Advanced)
**Why**: If you want pixel-perfect design handoff from Figma → PyQt6 code generation.

**Architecture**:
```
Figma Design
    ↓ (via Figma REST API)
JSON Scene Graph (nodes, properties, styles)
    ↓ (via Python converter script)
PyQt6 Python Code (widget tree, stylesheets)
```

**Implementation Steps**:

**Step 1: Figma API Integration**
```python
import requests
from typing import Any

FIGMA_API_KEY = "your_token"
FIGMA_FILE_KEY = "abc123"

def fetch_figma_file(file_key: str) -> dict[str, Any]:
    """Fetch Figma file JSON via REST API."""
    url = f"https://api.figma.com/v1/files/{file_key}"
    headers = {"X-Figma-Token": FIGMA_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json()

figma_data = fetch_figma_file(FIGMA_FILE_KEY)
```

**Step 2: Parse Scene Graph**
```python
def parse_figma_node(node: dict[str, Any]) -> str:
    """Convert Figma node to PyQt6 widget code."""
    node_type = node.get("type")

    match node_type:
        case "FRAME":
            # Frame → QFrame
            return f"frame = QFrame()\nframe.setFixedSize({node['absoluteBoundingBox']['width']}, {node['absoluteBoundingBox']['height']})"
        case "TEXT":
            # Text → QLabel
            text_content = node['characters']
            return f"label = QLabel('{text_content}')"
        case "RECTANGLE":
            # Rectangle → QFrame with background color
            color = node['fills'][0]['color']
            rgb = f"rgb({int(color['r']*255)}, {int(color['g']*255)}, {int(color['b']*255)})"
            return f"rect = QFrame()\nrect.setStyleSheet('background-color: {rgb};')"
        case _:
            return f"# Unsupported node type: {node_type}"
```

**Step 3: Generate PyQt6 Code**
```python
def generate_pyqt6_code(figma_data: dict[str, Any]) -> str:
    """Generate complete PyQt6 Python file from Figma data."""
    lines = [
        "from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame",
        "from PyQt6.QtCore import Qt",
        "",
        "class GeneratedWidget(QWidget):",
        "    def __init__(self, parent=None):",
        "        super().__init__(parent)",
        "        layout = QVBoxLayout(self)",
        "",
    ]

    # Traverse Figma scene graph
    for page in figma_data['document']['children']:
        for child in page['children']:
            widget_code = parse_figma_node(child)
            lines.append(f"        {widget_code}")
            lines.append(f"        layout.addWidget({child['name'].lower()})")

    return "\n".join(lines)

# Usage:
code = generate_pyqt6_code(figma_data)
with open("gui/generated/figma_import.py", "w") as f:
    f.write(code)
```

**Step 4: Handle Spline 3D Placeholders**
In Figma, mark Spline zones with naming convention:
- Frame named `SPLINE_owl_idle` → generates `Spline3DWidget("owl_idle")`

```python
def parse_figma_node(node: dict[str, Any]) -> str:
    node_name = node.get("name", "")

    if node_name.startswith("SPLINE_"):
        scene_name = node_name.replace("SPLINE_", "")
        return f"spline_widget = Spline3DWidget('{scene_name}')"
    # ... rest of parsing logic
```

**Advantages**:
- ✅ Pixel-perfect design handoff
- ✅ Designers work in Figma (familiar tool)
- ✅ Auto-generates PyQt6 code on save

**Limitations**:
- ❌ Significant development effort (2-3 weeks to build)
- ❌ Limited to static layouts (no complex interactions)
- ❌ Requires Figma API access + token management

#### Option 3: Web-Based Live Editor (Most Ambitious)
Build a React app that:
1. Renders live PyQt6 widget preview (via QWebEngineView)
2. Provides drag-and-drop component palette
3. Outputs Python code on "Export"

**Tech Stack**:
- Frontend: React + TailwindCSS + Monaco Editor (code preview)
- Backend: Python Flask API (converts editor state → PyQt6 code)
- Preview: Embedded PyQt6 subprocess (render changes in real-time)

**Complexity**: 6-8 weeks development time. Only recommended if building a reusable tool for multiple projects.

---

### Recommended Path Forward

**For OwlWatcher specifically**:
1. **Use Qt Designer** for static layouts (header, panels, grids)
2. **Use Figma** for design mockups (visual exploration, client presentations)
3. **Hand-code dynamic widgets** (OwlWidget, Spline3DWidget) as they require custom logic
4. **Document patterns** in `skills/desktop-ui-designer/` for reuse

**For a reusable design tool**:
Start with **Option 2 (Figma-to-PyQt6 converter)**:
- Lower development cost than full web editor
- Leverages existing Figma expertise
- Provides tangible time savings for future projects
- Can be open-sourced as a standalone tool

---

## Timeline & Deliverables

### Week 1: Asset Generation
- [ ] Generate 12 backgrounds with Nano Banana Pro (Figma plugin)
- [ ] Generate 6 texture overlays (glass, holographic, alert gradients)
- [ ] Generate 20+ icons and badges
- [ ] Create 8 Spline 3D owl states in Spline Editor
- [ ] Export all `.splinecode` files

### Week 2: Mockup Assembly
- [ ] Create Figma file with 12+ artboards
- [ ] Assemble mockups 1-12 (compose Nano Banana + Spline screenshots)
- [ ] Add annotations and implementation notes
- [ ] Create interactive prototype (link artboards)
- [ ] Export PNG previews + CSS specs

### Week 3: PyQt6 Integration
- [ ] Implement `ThemedBackgroundWidget` with Nano Banana assets
- [ ] Implement `GlassMorphPanel` with texture overlays
- [ ] Integrate `Spline3DWidget` with QWebEngineView
- [ ] Connect state machine to Spline animations
- [ ] Test on target hardware (verify 60fps)

### Week 4: Polish & Documentation
- [ ] Create video walkthrough of each mockup (screen recording)
- [ ] Write implementation guide (this document)
- [ ] Create Figma-to-PyQt6 converter script (if pursuing Option 2)
- [ ] Update CLAUDE.md with new patterns

---

## References

- **Nano Banana Pro Documentation**: [UX Planet Article](https://uxplanet.org/ui-design-with-nano-banana-pro-51aa803457d5)
- **Nano Banana Figma Plugin**: [Figma Community](https://www.figma.com/community/plugin/1549333261761511637/nano-banana-pro-ai-figma-plugin-for-ai-image-generation-ad-creatives-ui-ux-mockups)
- **Spline 3D Editor**: [spline.design](https://spline.design)
- **Spline React Integration**: `@splinetool/react-spline` npm package
- **PyQt6 QWebEngineView Docs**: [Qt WebEngine Widgets](https://doc.qt.io/qt-6/qtwebenginewidgets-index.html)
- **Marcus's Coding Standards**: `C:\ClaudeSkills\skills\universal-coding-standards\SKILL.md`
- **Desktop UI Patterns**: `C:\ClaudeSkills\skills\desktop-ui-designer\SKILL.md`

---

## Appendix: Prompt Library for Nano Banana Pro

### Background Prompts

**Dark Cybersecurity Theme**:
```
Dark navy gradient background for desktop monitoring application,
subtle circuit board pattern overlay, glowing teal accent lines,
professional cybersecurity aesthetic, 4K resolution seamless tileable,
cinematic sci-fi lighting
```

**Light Clean Workspace**:
```
Soft white gradient background with geometric shapes,
minimal professional design, subtle drop shadows,
modern workspace aesthetic, 4K resolution seamless tileable,
natural daylight ambient
```

**Neon Cyberpunk**:
```
Dark cityscape with neon pink and cyan lights,
rain-soaked reflections, Blade Runner aesthetic,
holographic billboards in background, 4K resolution,
cyberpunk futuristic vibe
```

### Texture Prompts

**Glass Morphism Panel**:
```
Translucent frosted glass panel texture,
subtle blur effect with neon teal border glow,
modern UI glassmorphism style, 2048x2048 PNG with alpha channel,
soft drop shadow, professional desktop app aesthetic
```

**Holographic Overlay**:
```
Transparent holographic HUD overlay with scan lines,
teal and purple gradient accents, futuristic AR interface,
grid pattern background, 2048x2048 PNG with alpha channel,
sci-fi data visualization aesthetic
```

### Icon Prompts

**File Document Icon**:
```
3D file document icon with folded corner,
glass material with soft glow, teal accent color,
isometric view, 512x512 PNG with transparency,
modern UI icon design, perfect text rendering for 'DOC' label
```

**Status Badge (Synced)**:
```
Circular badge icon with green checkmark,
glowing ring animation effect, glass morphism style,
512x512 PNG with transparency, professional UI element,
success state indicator
```
