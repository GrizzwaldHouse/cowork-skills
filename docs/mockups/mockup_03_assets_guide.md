# Mockup 03: Fullscreen Immersive - Asset Generation Guide

**Developer**: Marcus Daley
**Date**: 2026-02-25
**Mockup**: Fullscreen Immersive Experience with Owl Catching Animation

---

## Table of Contents

1. [Nano Banana Pro Prompts](#nano-banana-pro-prompts)
2. [Spline 3D Scene Specifications](#spline-3d-scene-specifications)
3. [Animation Timing Reference](#animation-timing-reference)
4. [Sound Effect Integration Points](#sound-effect-integration-points)
5. [PyQt6 Integration Guide](#pyqt6-integration-guide)
6. [Testing Checklist](#testing-checklist)

---

## 1. Nano Banana Pro Prompts

### Asset #1: Deep Space Nebula Background (4K)

**Model**: Gemini 3 Pro Image (Nano Banana Pro)
**Resolution**: 3840x2160 (4K) or 1920x1080 (Full HD)
**Format**: PNG (lossless) or WebP (optimized)

**Primary Prompt**:
```
Deep space nebula environment, volumetric teal and purple auroras weaving through cosmic dust,
distant galaxies and star clusters twinkling with varied brightness, cinematic sci-fi aesthetic,
dark void between nebula arms, gravitational lens distortion near center creating subtle light
bending, layered cosmic dust clouds with depth separation, no text no UI elements no watermarks,
ultra high resolution 4K, photorealistic volumetric lighting, deep black background with rich
color gradients, anamorphic lens flare subtly placed
```

**Variation Prompts for Different States**:

**Idle State Background**:
```
Serene deep space nebula, soft teal and lavender auroras gently drifting, minimal star activity,
calm cosmic dust settled into wispy layers, low contrast peaceful atmosphere, dark void dominant,
subtle breathing glow from center, cinematic matte painting style, 4K resolution, no text
```

**Alert State Background**:
```
Intense deep space nebula, crimson and orange energy surges through teal aurora layers, rapid
star pulsing, cosmic dust agitated and swirling violently, high contrast dramatic atmosphere,
electrical discharges between nebula arms, volcanic red undertones, urgent cinematic lighting,
4K resolution, no text
```

**Scanning State Background**:
```
Active deep space nebula, sweeping teal beam cutting across purple aurora layers, radar-like
concentric rings visible in cosmic dust, stars aligned in grid pattern suggesting digital
overlay, focused spotlight effect from center, tactical sci-fi atmosphere, 4K resolution, no text
```

**Success State Background**:
```
Celebratory deep space nebula, golden light bursting through teal and purple auroras, stars
twinkling at maximum brightness like confetti, warm amber cosmic dust particles floating upward,
triumphant cinematic lighting with god rays, rich vibrant colors, 4K resolution, no text
```

### Asset #2: HUD Overlay Elements (Transparent PNG)

**Prompt for Scan Grid**:
```
Transparent futuristic holographic HUD overlay, glowing teal scan grid with fine lines every
100 pixels, corner targeting brackets with technical readouts, data stream indicators flowing
downward, subtle hexagonal pattern underlying the grid, military-grade tactical display aesthetic,
PNG with alpha transparency, no background color, thin precise lines
```

**Prompt for Targeting Reticle**:
```
Holographic targeting reticle, circular design with crosshairs, teal glow with subtle purple
accent, rotating tick marks around outer ring, inner focus circle with breath animation markers,
technical measurement lines, transparent background PNG, sci-fi military aesthetic
```

**Prompt for Corner Brackets**:
```
Four corner bracket overlays for screen edges, thin teal glowing lines forming L-shaped brackets,
small technical text readouts near each corner, subtle animated scan line passing through,
transparent PNG, futuristic tactical interface design
```

### Asset #3: Owl Character Sprites (Multiple States)

**Base Owl Prompt**:
```
Stylized cybersecurity guardian owl character, large expressive eyes with teal bioluminescent
glow, sleek feather design with circuit board patterns subtly integrated, proud standing pose
facing forward, dark feathers with teal and purple accent highlights, digital energy aura
surrounding the owl, transparent background, high detail game character art style, 512x512
```

**Owl Catching/Pecking Sprite Sheet**:
```
Sprite sheet of cybersecurity owl character pecking downward animation, 6 frames horizontal
layout, frame 1: head raised alert, frame 2: head tilting down, frame 3: beak reaching forward
and down, frame 4: beak at lowest point catching, frame 5: head pulling back up with prize,
frame 6: return to standing, teal bioluminescent eyes, dark feathers with circuit patterns,
transparent background, 3072x512 (6 frames at 512x512 each)
```

**Owl Scanning Sprite Sheet**:
```
Sprite sheet of cybersecurity owl character scanning animation, 8 frames horizontal layout,
owl head rotating from left to right with teal scanning beam emanating from eyes, radar sweep
effect, alert posture with raised ear tufts, dark feathers with circuit patterns, transparent
background, 4096x512 (8 frames at 512x512 each)
```

**Owl Sleeping Sprite**:
```
Cybersecurity owl character in sleeping pose, eyes gently closed with subtle teal glow through
eyelids, feathers slightly ruffled and relaxed, peaceful expression, floating Z particles near
head, soft ambient glow reduced, dark feathers with dimmed circuit patterns, transparent
background, 512x512
```

**Owl Alert Sprite**:
```
Cybersecurity owl character in high alert pose, eyes wide open with intense red and orange glow,
ear tufts fully raised, feathers bristled and electrified, aggressive stance, red energy aura
crackling around body, dark feathers with overcharged red circuit patterns, transparent
background, 512x512
```

**Owl Success/Proud Sprite**:
```
Cybersecurity owl character celebrating success, eyes bright with golden glow, chest puffed out
proudly, wings slightly spread showing achievement, gold confetti particles around, trophy glow
effect, warm amber energy aura, dark feathers with golden circuit patterns, transparent
background, 512x512
```

### Asset #4: File Type Icons (Holographic Style)

**Prompt Template** (replace [TYPE] and [SYMBOL]):
```
Holographic floating [TYPE] file icon, translucent teal glass material with internal [SYMBOL]
symbol glowing, subtle refraction and light scattering, thin border outline with energy pulse,
cubic shape with rounded edges, sci-fi data crystal aesthetic, transparent background, 128x128
```

**Specific File Type Prompts**:

| File Type | Replace [TYPE] | Replace [SYMBOL] |
|-----------|---------------|-------------------|
| Document | document | paper scroll |
| Python | code | python snake |
| Config | settings | gear mechanism |
| Data | analytics | bar chart |
| Security | security | shield lock |
| Package | package | cube box |
| Design | design | paintbrush palette |
| Database | database | cylinder stack |
| Test | testing | flask beaker |
| Log | log file | text lines scrolling |
| Tools | utility | wrench hammer |
| Docs | documentation | book pages |

### Asset #5: Energy Burst Effects

**Catch Burst Prompt**:
```
Circular energy burst explosion effect, teal and cyan plasma expanding outward from center
point, radial light rays with particle debris, shockwave ring visible, bright white core fading
to teal edges, transparent background PNG sequence, sci-fi energy release, 256x256
```

**Peck Impact Prompt**:
```
Small impact spark effect, 3-4 bright teal sparks radiating from impact point, tiny particle
debris, electrical discharge lines, comic-style impact star shape, transparent background,
128x128
```

---

## 2. Spline 3D Scene Specifications

### Scene #1: Massive Owl Centerpiece

**File**: `owl_massive_immersive.splinecode`
**Dimensions**: 512x512px viewport
**Polygon Budget**: 15,000-25,000 tris

**Model Specifications**:
- Base mesh: Stylized owl with large head, prominent eyes, compact body
- Eye geometry: Separate mesh with emissive teal material (HDR intensity 2.0)
- Feather detail: Normal map based, not geometry (performance)
- Circuit pattern: Emissive texture overlay on feather normal map

**Materials**:
| Part | Base Color | Metallic | Roughness | Emissive |
|------|-----------|----------|-----------|----------|
| Body feathers | #1a2332 | 0.3 | 0.7 | None |
| Eye iris | #4fd1c5 | 0.0 | 0.2 | #4fd1c5 @ 2.0 |
| Eye pupil | #000000 | 0.0 | 0.1 | None |
| Beak | #2d3748 | 0.6 | 0.4 | None |
| Circuit lines | #4fd1c5 | 0.8 | 0.2 | #4fd1c5 @ 1.5 |
| Talons | #374151 | 0.7 | 0.3 | None |

**Animations** (Spline State Machine):

| State | Animation | Duration | Loop | Easing |
|-------|-----------|----------|------|--------|
| idle | Gentle breathing (scale Y: 1.0→1.03→1.0) | 5s | Yes | ease-in-out |
| scanning | Head rotation (Y: -30°→30°→-30°) | 6s | Yes | linear |
| catching | Swoop forward + peck (3 rapid pecks) | 1.5s | No | cubic-bezier |
| alert | Rapid shake + eye glow intensify | 0.5s | Yes | ease-in-out |
| success | Wing spread + chest puff | 2s | No | ease-out |
| sleeping | Slow drift + eye close | 8s | Yes | ease-in-out |

**Catching Animation Keyframes (Detailed)**:
```
Frame 0 (0.0s): Rest position, facing forward
Frame 15 (0.3s): Rotate toward target, lean forward 20°, scale 1.2x
Frame 20 (0.4s): First peck - head drops 30px, beak opens
Frame 22 (0.44s): First peck return - head rises
Frame 25 (0.5s): Second peck - head drops 30px, beak snaps
Frame 27 (0.54s): Second peck return - head rises
Frame 30 (0.6s): Third peck - head drops 30px, beak catches (cube disappears)
Frame 35 (0.7s): Head rises with "prize", satisfied expression
Frame 50 (1.0s): Begin return to center
Frame 75 (1.5s): Back to rest position, idle animation resumes
```

**Lighting**:
- Key light: Point light above-right, teal (#4fd1c5), intensity 1.5
- Fill light: Ambient, purple (#9333ea), intensity 0.3
- Rim light: Back light, white, intensity 0.8
- Eye glow: Emissive material, no external light needed

**Interaction Events** (Spline → JavaScript):
```javascript
// Spline event listeners
spline.addEventListener('mouseDown', (e) => {
    if (e.target.name === 'owl_body') {
        // Trigger state cycle
    }
});
```

### Scene #2: Moon Orb

**File**: `moon_orb_levitate.splinecode`
**Dimensions**: 128x128px viewport
**Polygon Budget**: 3,000-5,000 tris

**Model Specifications**:
- Sphere with cratered surface (displacement map)
- Crescent shadow using secondary sphere as shadow caster
- Anti-gravity particle emitter (20 particles, upward drift)

**Materials**:
| Part | Base Color | Metallic | Roughness | Emissive |
|------|-----------|----------|-----------|----------|
| Moon surface | #fbbf24 | 0.2 | 0.8 | #fbbf24 @ 0.5 |
| Craters | #92400e | 0.1 | 0.9 | None |
| Glow rim | #fb923c | 0.0 | 0.1 | #fb923c @ 2.0 |

**Animations**:
- Levitation: translateY oscillation (±20px), 6s loop
- Rotation: Y-axis full rotation, 15s loop
- Particle emission: 20 particles/sec, upward, fade over 3s

### Scene #3: Holographic File Cubes (12 units)

**File**: `file_ring_orbit.splinecode`
**Dimensions**: 900x900px viewport (orbital area)
**Polygon Budget**: 500 tris per cube (6,000 total)

**Model Specifications (per cube)**:
- Rounded cube (corner radius 0.15)
- Icon plane (front face, accepts texture swap)
- Label plane (bottom face, text mesh)
- Trail particle emitter (behind cube in orbit direction)

**Materials**:
| Part | Base Color | Metallic | Roughness | Emissive |
|------|-----------|----------|-----------|----------|
| Cube body | #1a2332 (90% opacity) | 0.4 | 0.3 | None |
| Cube border | #4fd1c5 | 0.8 | 0.1 | #4fd1c5 @ 1.0 |
| Icon face | Texture swap | 0.0 | 0.5 | Varies |
| Trail | #4fd1c5 | 0.0 | 0.0 | #4fd1c5 @ 1.5 |

**Orbital Parameters** (Kepler-inspired):

| Cube # | Orbit Radius | Period | Phase Offset | Eccentricity |
|--------|-------------|--------|--------------|--------------|
| 1 | 380px | 20s | 0° | 0.05 |
| 2 | 400px | 22s | 30° | 0.03 |
| 3 | 360px | 18s | 60° | 0.07 |
| 4 | 420px | 24s | 90° | 0.02 |
| 5 | 370px | 19s | 120° | 0.06 |
| 6 | 410px | 23s | 150° | 0.04 |
| 7 | 390px | 21s | 180° | 0.05 |
| 8 | 430px | 25s | 210° | 0.03 |
| 9 | 365px | 18.5s | 240° | 0.06 |
| 10 | 405px | 22.5s | 270° | 0.04 |
| 11 | 385px | 20.5s | 300° | 0.05 |
| 12 | 415px | 23.5s | 330° | 0.03 |

**Catching Interaction (Cube Behavior)**:
```
When cube is clicked:
1. Cube orbit animation pauses
2. Cube border turns bright white
3. Cube emits "selected" particles (8 radial sparks)
4. Owl catching animation triggers (see Scene #1)
5. At peck frame 30: cube scales to 0 over 0.4s
6. Energy burst spawns at cube position
7. After 1.5s: cube respawns at original orbit position with fade-in
```

---

## 3. Animation Timing Reference

### Owl Catching Sequence (Master Timeline)

```
TIME    EVENT                           CSS CLASS / JS TRIGGER
─────────────────────────────────────────────────────────────
0.00s   User clicks file cube           click event fires
0.00s   Owl orbit pause                 .catching added to container
0.00s   Owl swoop begins                animation: owl-swoop 1.5s
0.30s   Owl reaches cube vicinity       30% keyframe
0.40s   First peck down                 40% keyframe
0.45s   First peck return + pecking     .pecking added to .owl-massive
0.50s   Second peck down                50% keyframe
0.55s   Second peck return              55% keyframe
0.60s   Cube caught                     .being-caught added to cube
0.60s   Energy burst spawns             .catch-burst element created
0.70s   Cube fully absorbed             cube-caught 100% keyframe
1.00s   Owl begins return               70% → 100% keyframe transition
1.20s   Energy burst removed            burst element removed from DOM
1.50s   Owl back at center              animation complete
1.50s   Alert/window opens              alert() or window.open()
2.00s   Cube respawns                   .being-caught removed, opacity reset
```

### State Transition Timing

```
STATE        ENTER DURATION    EXIT DURATION    LOOP DURATION
──────────────────────────────────────────────────────────────
idle         0.5s fade-in      0.3s fade-out    5s breathe
scanning     0.4s ramp-up      0.3s ramp-down   6s sweep
alert        0.1s instant      0.5s fade-out    0.5s shake
catching     0.0s immediate    0.5s return       1.5s total
success      0.3s build-up     1.0s fade-out    2s celebration
sleeping     2.0s drift-down   1.0s wake-up     8s breathe
```

---

## 4. Sound Effect Integration Points

### Sound Trigger Map

Each sound trigger is marked in the JavaScript with a comment pattern:
`// SOUND: [event_name]`

| Event | Trigger Point | Suggested Sound | Duration |
|-------|--------------|-----------------|----------|
| `cube_hover` | Mouse enters file cube | Soft tonal chime, ascending | 0.2s |
| `cube_click` | File cube clicked | Digital select confirmation | 0.3s |
| `owl_swoop` | Owl starts moving toward cube | Whoosh with teal frequency filter | 0.5s |
| `owl_peck_1` | First peck impact | Sharp tap/click | 0.1s |
| `owl_peck_2` | Second peck impact | Sharp tap/click (slightly higher) | 0.1s |
| `owl_peck_3` | Third peck / catch | Satisfying crunch/snap | 0.15s |
| `energy_burst` | Burst effect spawns | Electrical discharge pulse | 0.4s |
| `cube_absorbed` | Cube finishes shrinking | Soft digital dissolve | 0.3s |
| `owl_return` | Owl returns to center | Reverse whoosh, settling | 0.5s |
| `window_open` | Application window appears | Achievement chime, warm | 0.5s |
| `cube_respawn` | Cube reappears in orbit | Digital materialization | 0.4s |
| `state_idle` | Enter idle state | Ambient low hum (loop) | Loop |
| `state_scanning` | Enter scanning state | Radar sweep ping (loop) | Loop |
| `state_alert` | Enter alert state | Alarm klaxon (loop) | Loop |
| `state_success` | Enter success state | Triumphant fanfare | 2.0s |
| `state_sleeping` | Enter sleeping state | Soft breathing (loop) | Loop |

### Audio Implementation Pattern (Web Audio API)

```javascript
// Audio context setup for Spline/PyQt6 integration
class OwlAudioEngine {
    constructor() {
        this.ctx = new AudioContext();
        this.sounds = {};
    }

    async loadSound(name, url) {
        const response = await fetch(url);
        const buffer = await response.arrayBuffer();
        this.sounds[name] = await this.ctx.decodeAudioData(buffer);
    }

    play(name, volume = 1.0) {
        if (!this.sounds[name]) return;
        const source = this.ctx.createBufferSource();
        const gain = this.ctx.createGain();
        source.buffer = this.sounds[name];
        gain.gain.value = volume;
        source.connect(gain);
        gain.connect(this.ctx.destination);
        source.start(0);
    }
}
```

---

## 5. PyQt6 Integration Guide

### Architecture Overview

```
┌─────────────────────────────────────────┐
│           PyQt6 Main Window             │
│  ┌───────────────────────────────────┐  │
│  │        QWebEngineView             │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │   Mockup 03 HTML/CSS/JS    │  │  │
│  │  │  ┌───────────────────────┐  │  │  │
│  │  │  │   Spline 3D Viewer   │  │  │  │
│  │  │  │   (iframe embed)     │  │  │  │
│  │  │  └───────────────────────┘  │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
│           QWebChannel Bridge            │
│         (Python ↔ JavaScript)           │
└─────────────────────────────────────────┘
```

### QWebChannel Bridge Code

```python
# owl_bridge.py
# Developer: Marcus Daley
# Date: 2026-02-25
# Purpose: Python ↔ JavaScript bridge for OwlWatcher Mockup 03

from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt6.QtWebChannel import QWebChannel


class OwlBridge(QObject):
    """Bidirectional communication bridge between PyQt6 and Mockup 03 HTML."""

    # Signals: Python → JavaScript
    state_changed = pyqtSignal(str)       # Notify JS of owl state change
    file_update = pyqtSignal(str, str)    # Notify JS of file change (path, action)
    theme_changed = pyqtSignal(str)       # Notify JS of theme change

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_state = "idle"

    @pyqtSlot(str)
    def on_cube_clicked(self, file_type):
        """Called from JavaScript when user clicks a file cube."""
        # SOUND: cube_click
        print(f"Cube clicked: {file_type}")
        # Launch the corresponding application/window
        self._launch_file_viewer(file_type)

    @pyqtSlot(str)
    def on_owl_catch_complete(self, file_type):
        """Called from JavaScript after owl catching animation finishes."""
        # SOUND: window_open
        print(f"Owl caught: {file_type}, opening window...")
        self._open_application_window(file_type)

    @pyqtSlot(str)
    def on_state_request(self, new_state):
        """Called from JavaScript to request owl state change."""
        valid_states = ["idle", "scanning", "alert", "catching", "success", "sleeping"]
        if new_state in valid_states:
            self._current_state = new_state
            self.state_changed.emit(new_state)

    @pyqtSlot(result=str)
    def get_current_state(self):
        """Returns current owl state to JavaScript."""
        return self._current_state

    def _launch_file_viewer(self, file_type):
        """Maps file types to application launches."""
        file_type_map = {
            "Doc": "documents_viewer",
            "Python": "code_editor",
            "Config": "config_editor",
            "Data": "analytics_dashboard",
            "Security": "security_panel",
            "Package": "package_manager",
            "Design": "design_studio",
            "Database": "database_browser",
            "Test": "test_runner",
            "Log": "log_viewer",
            "Tools": "tool_manager",
            "Docs": "documentation_browser",
        }
        app_name = file_type_map.get(file_type, "generic_viewer")
        print(f"Launching {app_name} for {file_type}")

    def _open_application_window(self, file_type):
        """Opens the actual application window after catching animation."""
        # Implementation connects to OwlWatcher's existing window management
        pass
```

### JavaScript Bridge Consumer

```javascript
// Inside Mockup 03 HTML <script> tag
// Connects to PyQt6 QWebChannel bridge

new QWebChannel(qt.webChannelTransport, function(channel) {
    const bridge = channel.objects.owlBridge;

    // Receive state changes from Python
    bridge.state_changed.connect(function(newState) {
        setOwlState(newState);
    });

    // Receive file updates from Python
    bridge.file_update.connect(function(path, action) {
        updateFileCube(path, action);
    });

    // Send cube click to Python (replaces alert())
    window.notifyCubeClick = function(fileType) {
        bridge.on_cube_clicked(fileType);
    };

    // Send catch complete to Python
    window.notifyCatchComplete = function(fileType) {
        bridge.on_owl_catch_complete(fileType);
    };
});
```

### Spline 3D Embed in QWebEngineView

```html
<!-- Replace emoji owl placeholder with actual Spline embed -->
<script type="module" src="https://unpkg.com/@splinetool/viewer@1.9.82/build/spline-viewer.js"></script>

<spline-viewer
    url="https://prod.spline.design/YOUR_SCENE_ID/scene.splinecode"
    style="width: 512px; height: 512px;"
    events-target="global"
></spline-viewer>
```

### PyQt6 Window Setup

```python
# main_window_immersive.py
# Developer: Marcus Daley
# Date: 2026-02-25
# Purpose: PyQt6 window hosting Mockup 03 immersive experience

import sys
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QMainWindow

from owl_bridge import OwlBridge


class ImmersiveWindow(QMainWindow):
    """Frameless fullscreen window hosting Mockup 03."""

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_bridge()
        self._load_mockup()

    def _setup_window(self):
        """Configure frameless fullscreen window."""
        self.setWindowTitle("OwlWatcher - Immersive")
        self.showFullScreen()
        # Transparent background for AR overlay potential
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def _setup_bridge(self):
        """Initialize QWebChannel bridge."""
        self._bridge = OwlBridge(self)
        self._channel = QWebChannel(self)
        self._channel.registerObject("owlBridge", self._bridge)

    def _load_mockup(self):
        """Load Mockup 03 HTML into QWebEngineView."""
        self._view = QWebEngineView(self)
        self._view.page().setWebChannel(self._channel)
        mockup_path = Path("C:/ClaudeSkills/docs/mockups/mockup_03_fullscreen_immersive.html")
        self._view.setUrl(QUrl.fromLocalFile(str(mockup_path)))
        self.setCentralWidget(self._view)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImmersiveWindow()
    sys.exit(app.exec())
```

---

## 6. Testing Checklist

### Visual Tests

- [ ] Deep space nebula renders at full 1920x1080 without tiling artifacts
- [ ] All 12 file cubes orbit smoothly at 60fps
- [ ] Owl breathing animation is visible and smooth
- [ ] Moon orb levitation and rotation are synchronized
- [ ] Aurora effects drift without stuttering
- [ ] Starfield twinkling is subtle and not distracting
- [ ] HUD overlay scan grid is visible but not overpowering
- [ ] Corner brackets render at correct screen positions
- [ ] Data streams flow smoothly in all 4 positions

### Interaction Tests

- [ ] Clicking any file cube triggers owl catching animation
- [ ] Owl swoops toward correct cube position (all 12 cubes)
- [ ] Pecking animation plays 3 times during swoop
- [ ] Cube shrinks and flies toward owl during catch
- [ ] Energy burst effect appears at cube position
- [ ] Owl returns to center after catching
- [ ] Window/app opens after animation completes
- [ ] Cube respawns after being caught
- [ ] Cannot trigger multiple catches simultaneously
- [ ] Mouse gravity field follows cursor smoothly
- [ ] Scroll zoom works (0.7x to 1.5x range)
- [ ] Spacebar resets zoom and position
- [ ] Moon orb click triggers theme toggle
- [ ] Owl click triggers state cycle

### Performance Tests

- [ ] Maintains 60fps with all animations running
- [ ] No memory leaks from particle trail generation
- [ ] Energy burst elements properly cleaned up after animation
- [ ] Smooth performance with multiple rapid cube clicks
- [ ] GPU usage stays below 60% during normal operation

### PyQt6 Integration Tests

- [ ] QWebEngineView loads mockup HTML correctly
- [ ] QWebChannel bridge establishes connection
- [ ] Python receives cube click events from JavaScript
- [ ] JavaScript receives state change signals from Python
- [ ] Fullscreen mode renders without letterboxing
- [ ] Spline 3D viewer loads within QWebEngineView
- [ ] File monitoring events propagate to visual updates
