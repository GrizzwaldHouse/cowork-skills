# Mockup 02: Advanced Sidebar Command Center - Asset Generation Guide
**Developer**: Marcus Daley
**Date**: 2026-02-24
**Purpose**: Asset generation for multi-layer holographic sidebar with neural network visualization

## Overview

Mockup 02 pushes technical boundaries with a sophisticated sidebar-based interface featuring:
- **Multi-layer depth rendering** with parallax scrolling
- **Holographic visual effects** (scan lines, edge glow, blur)
- **Neural network activity visualization** with real-time data flow
- **Advanced 3D file stack** with perspective transforms
- **Real-time log timeline** with 3D event markers

---

## Nano Banana Pro Asset Generation

### Asset #1: Neural Network Background

#### Prompt
```
Deep space neural network visualization with glowing interconnected nodes
and data connection lines, dark blue purple gradient backdrop, futuristic
AI aesthetic with depth, 4K resolution, subtle particle field in background,
holographic grid overlay with perspective, cyberpunk command center vibe,
nodes pulsing with energy, no text or UI elements, seamless tileable pattern
```

#### Settings
- **Resolution**: 4096x4096 pixels
- **Format**: PNG (RGB)
- **Style**: Cyberpunk neural network
- **Color Palette**: Deep blues (#0a0e27), purples (#9333ea), teals (#4fd1c5)
- **Special**: Enable "depth" mode for layered nodes

#### Export Location
`C:\ClaudeSkills\scripts\gui\assets\backgrounds\neural_network_dark.png`

#### PyQt6 Implementation
```python
def _set_neural_background(self) -> None:
    """Apply neural network background with animated grid overlay."""
    bg_path = ASSETS_DIR / "backgrounds" / "neural_network_dark.png"
    pixmap = QPixmap(str(bg_path))

    # Create animated widget for grid scrolling
    bg_widget = QWidget(self)
    bg_widget.setGeometry(self.rect())

    # Apply pixmap
    palette = QPalette()
    palette.setBrush(QPalette.ColorRole.Window, QBrush(pixmap))
    bg_widget.setPalette(palette)
    bg_widget.setAutoFillBackground(True)

    # Animated grid overlay
    grid_overlay = QWidget(bg_widget)
    grid_overlay.setGeometry(bg_widget.rect())
    grid_overlay.setStyleSheet("""
        background-image:
            repeating-linear-gradient(90deg, rgba(79, 209, 197, 0.02) 0px,
                                      transparent 1px, transparent 80px),
            repeating-linear-gradient(0deg, rgba(147, 51, 234, 0.02) 0px,
                                      transparent 1px, transparent 80px);
    """)

    # Animate grid scrolling
    animation = QPropertyAnimation(grid_overlay, b"pos")
    animation.setDuration(20000)
    animation.setStartValue(QPoint(0, 0))
    animation.setEndValue(QPoint(80, 80))
    animation.setLoopCount(-1)
    animation.start()
```

---

### Asset #2: Holographic Sidebar Panel Texture

#### Prompt
```
Translucent holographic sidebar panel with frosted glass effect and
scan lines, neon teal edge glow, multi-layer depth with blur gradients,
2048x2048 PNG with alpha transparency, futuristic command center aesthetic,
subtle circuit pattern embedded in glass, cyberpunk interface material,
vertical orientation optimized
```

#### Settings
- **Resolution**: 2048x2048 pixels
- **Format**: PNG with alpha (RGBA)
- **Transparency**: 70% base opacity with gradient
- **Special Features**:
  - Scan line pattern (horizontal, 4px spacing)
  - Edge glow (teal, 8px blur)
  - Circuit board emboss (subtle)

#### Export Location
`C:\ClaudeSkills\scripts\gui\assets\textures\holo_sidebar_panel.png`

#### PyQt6 Implementation
```python
class HolographicSidebar(QFrame):
    """Advanced sidebar with holographic effects."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedWidth(400)

        # Apply Nano Banana holographic texture
        texture_path = ASSETS_DIR / "textures" / "holo_sidebar_panel.png"
        self.setStyleSheet(f"""
            QFrame {{
                background-image: url({texture_path});
                background-position: center;
                background-repeat: no-repeat;
                background-size: cover;
                border-right: 2px solid rgba(79, 209, 197, 0.4);
            }}
        """)

        # Animated scan lines overlay
        self._scan_lines = self._create_scan_lines()

        # Edge glow effect
        self._edge_glow = self._create_edge_glow()

    def _create_scan_lines(self) -> QWidget:
        """Create animated scan line overlay."""
        scan_widget = QWidget(self)
        scan_widget.setGeometry(self.rect())
        scan_widget.setStyleSheet("""
            background: repeating-linear-gradient(
                0deg,
                rgba(79, 209, 197, 0.03) 0px,
                transparent 1px,
                transparent 4px
            );
        """)
        scan_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Animate scan lines scrolling
        animation = QPropertyAnimation(scan_widget, b"pos")
        animation.setDuration(8000)
        animation.setStartValue(QPoint(0, 0))
        animation.setEndValue(QPoint(0, 4))
        animation.setLoopCount(-1)
        animation.start()

        return scan_widget

    def _create_edge_glow(self) -> QWidget:
        """Create pulsing edge glow effect."""
        glow_widget = QWidget(self)
        glow_widget.setGeometry(self.width() - 4, 0, 4, self.height())
        glow_widget.setStyleSheet("""
            background: linear-gradient(
                to bottom,
                rgba(79, 209, 197, 0.8) 0%,
                rgba(147, 51, 234, 0.8) 50%,
                rgba(251, 146, 60, 0.8) 100%
            );
        """)

        # Apply blur effect
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(8)
        glow_widget.setGraphicsEffect(blur)

        # Pulse animation
        opacity_anim = QPropertyAnimation(glow_widget, b"windowOpacity")
        opacity_anim.setDuration(3000)
        opacity_anim.setStartValue(0.6)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setLoopCount(-1)
        opacity_anim.start()

        return glow_widget
```

---

### Asset #3: 3D File Type Icons (Enhanced Set)

#### Prompts

Same 6 icons from Mockup 01, but with enhanced holographic styling:

**Icon 1: Document File (Holographic Version)**
```
3D isometric file document icon with folded corner, holographic glass
material with neon teal glow and rainbow refraction, futuristic UI icon
design, 512x512 PNG with alpha transparency, cyberpunk aesthetic with
scan lines visible in material, professional software icon, dramatic
lighting with depth
```

**Icon 2-6**: Apply same "holographic glass material with rainbow refraction" treatment to Python, Config, Database, Log, and Package icons.

#### Settings
- **Resolution**: 512x512 pixels each
- **Format**: PNG with alpha
- **Material**: Holographic glass with refraction
- **Lighting**: Dramatic rim light from top-left

#### Export Location
`C:\ClaudeSkills\scripts\gui\assets\icons\holo_file_[type].png`

---

### Asset #4: Neural Activity Bar Chart Elements

#### Prompt
```
Vertical holographic bar chart element with gradient glow effect,
neon teal to purple gradient fill, futuristic data visualization aesthetic,
512x128 PNG with alpha transparency, glass material with internal glow,
top rounded cap with pulsing node, cyberpunk UI component, animated
energy flow appearance, no background
```

#### Settings
- **Resolution**: 512x128 pixels (vertical bar)
- **Format**: PNG with alpha
- **Gradient**: Teal (#4fd1c5) to purple (#9333ea)
- **Special**: Pulsing glow node at top

#### Export Location
`C:\ClaudeSkills\scripts\gui\assets\neural\bar_element.png`

---

## Spline 3D Scene Specifications

### Scene #1: Owl Mascot (Sidebar Version - 96px)

**Scene Name**: `owl_sidebar.splinecode`

**Specifications**:
- **Size**: 96x96 pixels
- **Triangle Count**: <1,000 triangles
- **Animation**: Enhanced floating with subtle Y-axis rotation
  - Y position: +8 to -8 pixels (3s duration)
  - Y-axis rotation: 0° to 10° (subtle perspective)
  - Scale pulse: 1.0 to 1.03
- **Materials**:
  - Body: Holographic shader with rainbow refraction
  - Eyes: Emissive white with teal rim glow
  - Rim light: Teal (#4fd1c5), intensity 0.8
- **Special Effect**: Holographic ring orbiting around owl
  - Ring: Dashed border, 120px diameter
  - Rotation: 360° over 10s
  - Material: Emissive teal with opacity 0.3
- **Camera**: Perspective with 15° tilt
- **Background**: Transparent

**Spline Editor Steps**:
1. Import `owl_idle_header.splinecode` from Mockup 01
2. Scale to 96px display size
3. Replace toon shader with holographic material:
   - Base: Glass with refraction index 1.5
   - Fresnel: Rainbow color ramp (0° = teal, 180° = purple)
   - Emissive: 0.3 intensity base glow
4. Create enhanced animations:
   - **Float**: Y sine wave +8 to -8 over 3s
   - **Rotate**: Y-axis 0° to 10° over 3s (sync with float)
   - **Pulse**: Scale 1.0 → 1.03 → 1.0, 3s loop
5. Add holographic ring:
   - Torus primitive, 120px diameter, 2px thickness
   - Dashed line material (12 segments, 6 gaps)
   - Rotation animation: 360° Y-axis over 10s
   - Position: Orbits around owl at 60px radius
6. Lighting setup:
   - Point light: Teal color, position (30, 50, 100)
   - Rim light: White, intensity 0.8, angle 45°
7. Camera: Perspective FOV 50°, slight tilt for depth
8. Export → Scene → `.splinecode`

**Export Location**:
`C:\ClaudeSkills\scripts\gui\assets\spline\owl_sidebar.splinecode`

---

### Scene #2: 3D File Stack with Parallax Depth

**Scene Name**: `file_stack_3d.splinecode`

**Specifications**:
- **Size**: 360x140 pixels per layer (6 layers total)
- **Triangle Count**: <800 per layer (4,800 total)
- **Depth Layers**: Each layer has Z-depth offset
  - Layer 1: Z = 0 (front)
  - Layer 2: Z = -20px
  - Layer 3: Z = -40px
  - Layer 4: Z = -60px
  - Layer 5: Z = -80px
  - Layer 6: Z = -100px
- **Animation**: Independent floating per layer (staggered)
  - Layer 1: Y +3 to -3, 4s duration, 0s delay
  - Layer 2: Y +3 to -3, 4s duration, 0.3s delay
  - Layer 3: Y +3 to -3, 4s duration, 0.6s delay
  - (etc.)
- **Hover State**: Scale 1.0 → 1.1, TranslateZ +30px, RotateY 5°
- **Materials**:
  - Base: Glass panel with frosted blur
  - Border: Emissive teal, 1px width
  - Icon: Billboard sprite (always faces camera)
- **Interaction**: `mouseHover` triggers scale + glow effect
- **Camera**: Perspective with parallax support
- **Background**: Transparent

**Spline Editor Steps**:
1. Create base layer card:
   - Rounded rectangle primitive: 360x140px, 12px radius
   - Glass material: Base color rgba(26, 35, 50, 0.8), refraction 0.2
   - Border: 1px emissive teal outline
2. Add icon slot (billboard):
   - Plane object: 56x56px
   - Billboard constraint (always faces camera)
   - UV mapped for external texture loading
3. Add status orb indicator:
   - Small sphere: 12px diameter
   - Position: Top-right corner (+165px X, +60px Y)
   - Emissive material (color changes per state)
4. Create depth layers:
   - Duplicate layer 6 times
   - Set Z-depth: 0, -20, -40, -60, -80, -100
   - Each layer independent material (slight opacity variation)
5. Create idle animations (per layer):
   - Y position sine wave: +3 to -3 over 4s
   - Stagger start times: 0s, 0.3s, 0.6s, 0.9s, 1.2s, 1.5s
6. Create hover animation:
   - Trigger: `mouseHover` event
   - Scale: 1.0 → 1.1 (0.4s cubic-bezier ease-out)
   - TranslateZ: current → current + 30px
   - RotateY: 0° → 5°
   - Glow: Rim intensity 0.3 → 1.0
   - Outer ring: Fade in 300px glow ring
7. Setup camera:
   - Perspective projection, FOV 50°
   - Position: (0, 0, 400) looking at layer stack center
   - Parallax enabled: Layers respond to mouse movement
8. Setup icon texture loading:
   - Each layer's billboard loads from external PNG
   - Mapping: Layer 1 = document, Layer 2 = python, etc.
9. Export → Scene → `.splinecode`

**Export Location**:
`C:\ClaudeSkills\scripts\gui\assets\spline\file_stack_3d.splinecode`

**Icon Texture References**:
- Layer 1: `holo_file_document.png`
- Layer 2: `holo_file_python.png`
- Layer 3: `holo_file_config.png`
- Layer 4: `holo_file_database.png`
- Layer 5: `holo_file_log.png`
- Layer 6: `holo_file_package.png`

---

### Scene #3: Real-Time Log Visualizer (3D Timeline)

**Scene Name**: `log_visualizer_3d.splinecode`

**Specifications**:
- **Size**: 1480x300 pixels (fits main content area)
- **Timeline Track**: Horizontal line, 1200px length, 2px height
- **Event Markers**: 6 spheres along timeline, 40px diameter
- **Triangle Count**: <300 per marker (1,800 total)
- **Animation**: Continuous pulse + particle trails
  - Marker pulse: Scale 1.0 → 1.2 → 1.0, 3s loop (staggered)
  - Particle trails: Energy flow from left to right
- **Materials**:
  - Timeline track: Emissive gradient (teal → purple → orange)
  - Event markers: Glass sphere with internal glow
  - Particles: Emissive dots, 4px size
- **Interaction**: `mouseHover` on marker → scale 1.5x, show info tooltip
- **Camera**: Orthographic, front view
- **Background**: Transparent

**Spline Editor Steps**:
1. Create timeline track:
   - Thin rectangle: 1200x2px
   - Emissive material with gradient:
     - Left (0%): Teal rgba(79, 209, 197, 0.3)
     - Center (50%): Purple rgba(147, 51, 234, 0.5)
     - Right (100%): Orange rgba(251, 146, 60, 0.3)
   - Position: Horizontal center, Y=150px (vertical center)
2. Create event marker (sphere):
   - UV Sphere primitive: 40px diameter
   - Glass material:
     - Base: Transparent glass, refraction 1.3
     - Inner glow: Emissive core, teal color, intensity 0.8
   - Border ring: 2px emissive outline, teal glow
   - Icon: Billboard emoji (📝, 🔄, ✅, 📁, 🔔, ⚡)
3. Create marker pulse animation:
   - Scale: 1.0 → 1.2 → 1.0, 3s duration
   - Glow intensity: 0.8 → 1.5 → 0.8, sync with scale
   - Shadow blur: 20px → 40px → 20px
4. Duplicate marker 6 times:
   - Position along timeline: 10%, 25%, 40%, 55%, 70%, 85%
   - Stagger pulse animation: 0s, 0.5s, 1s, 1.5s, 2s, 2.5s
   - Assign different icons per marker
5. Create particle trail system:
   - Point emitter at left edge (0%, Y=150px)
   - Particle count: 50 active particles
   - Velocity: +10px/s horizontal (left to right)
   - Lifetime: 10s
   - Size: 4px diameter
   - Material: Emissive teal, opacity fade 1.0 → 0.0
   - Trail: Connect previous position with line renderer
6. Create hover animation:
   - Trigger: `mouseHover` event per marker
   - Scale: 1.2 → 1.5 (0.3s ease-out)
   - Z-index: Bring to front
   - Info tooltip: Show event details (separate UI layer)
7. Setup camera:
   - Orthographic projection (no perspective distortion)
   - Centered on timeline
   - Fixed view (no rotation)
8. Export → Scene → `.splinecode`

**Export Location**:
`C:\ClaudeSkills\scripts\gui\assets\spline\log_visualizer_3d.splinecode`

---

## PyQt6 Integration - Advanced Sidebar Widget

### HolographicSidebar Implementation

```python
# holographic_sidebar.py
from __future__ import annotations

from PyQt6.QtCore import QPropertyAnimation, QPoint, Qt
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QScrollArea, QWidget
from PyQt6.QtGui import QPixmap, QPainter

from gui.widgets.spline_3d_widget import Spline3DWidget
from gui.paths import ASSETS_DIR


class HolographicSidebar(QFrame):
    """Advanced sidebar with multi-layer holographic effects."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedWidth(400)

        # Apply Nano Banana holographic texture
        self._setup_holographic_background()

        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with 3D owl
        header = self._create_header()
        layout.addWidget(header)

        # 3D file stack with parallax
        file_stack = self._create_file_stack()
        layout.addWidget(file_stack)

        # Neural visualization
        neural_viz = self._create_neural_viz()
        layout.addWidget(neural_viz)

        # Animated overlays
        self._create_scan_lines()
        self._create_edge_glow()

    def _setup_holographic_background(self) -> None:
        """Apply holographic panel texture."""
        texture_path = ASSETS_DIR / "textures" / "holo_sidebar_panel.png"

        self.setStyleSheet(f"""
            HolographicSidebar {{
                background-image: url({texture_path});
                background-position: center;
                background-size: cover;
                border-right: 2px solid rgba(79, 209, 197, 0.4);
            }}
        """)

    def _create_header(self) -> QWidget:
        """Create header with Spline 3D owl."""
        header = QWidget()
        header.setFixedHeight(180)

        layout = QVBoxLayout(header)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Spline 3D owl (96px)
        owl = Spline3DWidget("owl_sidebar", parent=header)
        owl.setFixedSize(96, 96)
        layout.addWidget(owl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title label
        title = QLabel("OwlWatcher")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: white;
            background: linear-gradient(135deg, #4fd1c5 0%, #9333ea 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        """)
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        return header

    def _create_file_stack(self) -> QWidget:
        """Create 3D file stack with parallax scrolling."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                width: 8px;
                background: rgba(79, 209, 197, 0.05);
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4fd1c5, stop:1 #9333ea);
                border-radius: 4px;
            }
        """)

        # Spline 3D file stack
        file_stack = Spline3DWidget("file_stack_3d", parent=scroll_area)
        file_stack.setMinimumHeight(6 * 140 + 5 * 15)  # 6 layers + gaps

        scroll_area.setWidget(file_stack)

        # Connect scroll event for parallax effect
        scroll_area.verticalScrollBar().valueChanged.connect(
            lambda value: self._update_parallax(file_stack, value)
        )

        return scroll_area

    def _update_parallax(self, file_stack: Spline3DWidget, scroll_value: int) -> None:
        """Update 3D parallax based on scroll position."""
        js_code = f"""
        if (window.splineApp) {{
            const layers = window.splineApp.findObjectsByName('FileLayer');
            layers.forEach((layer, index) => {{
                const depth = (index + 1) * 0.1;
                layer.position.y = {scroll_value} * depth * 0.1;
            }});
        }}
        """
        file_stack.page().runJavaScript(js_code)

    def _create_neural_viz(self) -> QWidget:
        """Create neural network activity visualization."""
        neural_widget = QWidget()
        neural_widget.setFixedHeight(200)
        neural_widget.setStyleSheet("""
            background: linear-gradient(0deg,
                rgba(10, 14, 39, 0.95) 0%, transparent 100%);
            border-top: 1px solid rgba(79, 209, 197, 0.2);
        """)

        # Use QCustomPlot or QPainter for real-time bars
        # For now, placeholder implementation
        # TODO: Implement real-time neural activity bars

        return neural_widget

    def _create_scan_lines(self) -> None:
        """Create animated scan line overlay."""
        scan_widget = QWidget(self)
        scan_widget.setGeometry(self.rect())
        scan_widget.setStyleSheet("""
            background: repeating-linear-gradient(0deg,
                rgba(79, 209, 197, 0.03) 0px,
                transparent 1px,
                transparent 4px);
        """)
        scan_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        scan_widget.lower()  # Behind other widgets

        # Animate scrolling
        animation = QPropertyAnimation(scan_widget, b"pos")
        animation.setDuration(8000)
        animation.setStartValue(QPoint(0, 0))
        animation.setEndValue(QPoint(0, 4))
        animation.setLoopCount(-1)
        animation.start()

        self._scan_animation = animation  # Keep reference

    def _create_edge_glow(self) -> None:
        """Create pulsing edge glow effect."""
        glow_widget = QWidget(self)
        glow_widget.setGeometry(self.width() - 4, 0, 4, self.height())
        glow_widget.setStyleSheet("""
            background: linear-gradient(to bottom,
                rgba(79, 209, 197, 0.8) 0%,
                rgba(147, 51, 234, 0.8) 50%,
                rgba(251, 146, 60, 0.8) 100%);
        """)
        glow_widget.raise_()  # In front

        # Apply blur
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(8)
        glow_widget.setGraphicsEffect(blur)

        # Pulse animation
        opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        opacity_anim.setDuration(3000)
        opacity_anim.setStartValue(0.6)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setLoopCount(-1)
        opacity_anim.start()

        self._glow_animation = opacity_anim  # Keep reference
```

---

## Advanced Features Implementation

### Feature 1: Parallax Scrolling

**JavaScript Bridge** (in Spline HTML wrapper):
```javascript
// Listen for scroll events from PyQt6
window.updateParallax = (scrollValue) => {
    const layers = splineApp.findObjectsByName('FileLayer');
    layers.forEach((layer, index) => {
        const depth = (index + 1) * 0.1;
        layer.position.y = scrollValue * depth * 0.1;
    });
};

// Also respond to mouse movement for subtle parallax
document.addEventListener('mousemove', (e) => {
    const mouseX = (e.clientX / window.innerWidth) - 0.5;
    const mouseY = (e.clientY / window.innerHeight) - 0.5;

    layers.forEach((layer, index) => {
        const depth = (index + 1) * 0.05;
        layer.position.x += mouseX * depth * 10;
        layer.position.z += mouseY * depth * 10;
    });
});
```

### Feature 2: Real-Time Neural Activity

**Python Backend** (collect system metrics):
```python
import psutil

class NeuralActivityMonitor:
    """Monitors system metrics for neural visualization."""

    def __init__(self):
        self._metrics = {
            'cpu': 0.0,
            'memory': 0.0,
            'disk': 0.0,
            'network': 0.0,
            'sync': 0.0,
        }

    def update_metrics(self) -> dict[str, float]:
        """Update all metrics and return normalized values (0.0 - 1.0)."""
        self._metrics['cpu'] = psutil.cpu_percent() / 100.0
        self._metrics['memory'] = psutil.virtual_memory().percent / 100.0
        self._metrics['disk'] = psutil.disk_usage('/').percent / 100.0

        # Network (bytes sent in last second / theoretical max)
        net_io = psutil.net_io_counters()
        self._metrics['network'] = min(net_io.bytes_sent / 1_000_000, 1.0)

        # Sync activity (files synced in last minute)
        self._metrics['sync'] = self._get_sync_activity()

        return self._metrics
```

**Update Neural Bars** (from PyQt6 to Spline):
```python
def _update_neural_bars(self, metrics: dict[str, float]) -> None:
    """Update Spline 3D neural bars based on real-time metrics."""
    js_code = f"""
    if (window.splineApp) {{
        const bars = window.splineApp.findObjectsByName('NeuralBar');
        bars[0].scale.y = {metrics['cpu']};      // CPU bar
        bars[1].scale.y = {metrics['memory']};   // Memory bar
        bars[2].scale.y = {metrics['disk']};     // Disk bar
        bars[3].scale.y = {metrics['network']};  // Network bar
        bars[4].scale.y = {metrics['sync']};     // Sync bar
    }}
    """
    self._neural_viz_widget.page().runJavaScript(js_code)
```

---

## Testing Checklist

### Visual Verification
- [ ] Neural network background has depth and glowing nodes
- [ ] Holographic sidebar has scan lines and edge glow
- [ ] 3D owl has holographic ring orbiting
- [ ] File stack layers have visible depth (Z-spacing)
- [ ] Neural bars pulse and update dynamically
- [ ] Timeline events have particle trails

### Animation Verification
- [ ] Sidebar scan lines scroll continuously (8s loop)
- [ ] Edge glow pulses smoothly (3s loop)
- [ ] Owl floats + rotates (3s loop)
- [ ] File layers float with stagger (4s per layer)
- [ ] File layers respond to parallax scrolling
- [ ] Neural bars update in real-time (2s intervals)
- [ ] Timeline particles flow left-to-right

### Interaction Verification
- [ ] Hovering file layer scales + rotates + glows
- [ ] Clicking file layer loads details in main panel
- [ ] Hovering timeline event scales 1.5x
- [ ] Clicking timeline event shows log details
- [ ] Scrolling file stack triggers parallax effect
- [ ] Neural bars respond to system activity

### Performance Verification
- [ ] 60fps maintained with all animations active
- [ ] Parallax scrolling is smooth (no jank)
- [ ] Memory usage under 150MB for all Spline scenes
- [ ] WebGL detection fallback works
- [ ] Real-time neural updates don't block UI

---

## Advanced Concepts Used

1. **Multi-Layer Depth Rendering**: Z-axis positioning creates true 3D depth
2. **Parallax Scrolling**: Layers move at different speeds based on depth
3. **Holographic Visual Effects**: Scan lines, edge glow, frosted blur, rainbow refraction
4. **Real-Time Data Visualization**: System metrics drive 3D bar heights
5. **Billboard Sprites**: Icons always face camera for readability
6. **Particle Systems**: Energy flow and trails for dynamic effects
7. **State-Driven Animations**: Hover/click triggers complex animation sequences
8. **Bidirectional Communication**: PyQt6 ↔ Spline via QWebChannel
9. **GPU-Accelerated Rendering**: All effects use WebGL shaders
10. **Adaptive Detail**: LOD (Level of Detail) reduces triangles when not focused

---

## File Structure Summary

```
C:\ClaudeSkills\scripts\gui\
├── assets\
│   ├── backgrounds\
│   │   └── neural_network_dark.png         # Nano Banana (4096x4096)
│   ├── textures\
│   │   └── holo_sidebar_panel.png          # Nano Banana (2048x2048)
│   ├── icons\
│   │   ├── holo_file_document.png          # Nano Banana (512x512)
│   │   ├── holo_file_python.png
│   │   ├── holo_file_config.png
│   │   ├── holo_file_database.png
│   │   ├── holo_file_log.png
│   │   └── holo_file_package.png
│   ├── neural\
│   │   └── bar_element.png                 # Nano Banana (512x128)
│   └── spline\
│       ├── owl_sidebar.splinecode          # Spline 3D (96x96)
│       ├── owl_sidebar.html
│       ├── file_stack_3d.splinecode        # Spline 3D (360x840)
│       ├── file_stack_3d.html
│       ├── log_visualizer_3d.splinecode    # Spline 3D (1480x300)
│       └── log_visualizer_3d.html
└── widgets\
    ├── holographic_sidebar.py              # Main sidebar widget
    └── neural_activity_monitor.py          # System metrics collector
```

---

## Next Steps

1. **Generate Nano Banana Assets** (Est. 3 hours)
   - Neural network background (most complex)
   - Holographic panel texture with scan lines
   - 6 holographic file icons
   - Neural bar chart element

2. **Create Spline 3D Scenes** (Est. 8 hours)
   - Owl with holographic shader + orbiting ring
   - 6-layer file stack with depth + parallax
   - Timeline visualizer with particle system
   - Test all interactions

3. **Integrate into PyQt6** (Est. 6 hours)
   - Implement `HolographicSidebar` widget
   - Setup parallax scrolling system
   - Connect real-time neural metrics
   - Test bidirectional communication

4. **Polish & Optimize** (Est. 3 hours)
   - Verify 60fps performance
   - Tune parallax sensitivity
   - Optimize Spline triangle counts
   - Test on lower-end hardware

**Total Estimated Time**: 20 hours

---

## Comparison: Mockup 01 vs Mockup 02

| Feature | Mockup 01 (Dashboard Hero) | Mockup 02 (Advanced Sidebar) |
|---------|---------------------------|------------------------------|
| Layout | Full dashboard, centered owl | Sidebar + main content split |
| Background | Cybersecurity gradient | Neural network visualization |
| 3D Complexity | 3 scenes (owl, moon, grid) | 3 scenes (owl, stack, timeline) |
| Interactivity | Click + hover | Click + hover + parallax scroll |
| Visual Effects | Glow, pulse, float | Holographic, scan lines, depth |
| Data Visualization | Static file grid | Real-time neural activity |
| Advanced Features | None | Parallax, particle systems, LOD |
| Triangle Count | ~4,000 | ~6,800 |
| Performance Target | 60fps | 60fps (more demanding) |
| Sophistication Level | High | **Maximum** |

Mockup 02 pushes every boundary beyond Mockup 01! 🚀
