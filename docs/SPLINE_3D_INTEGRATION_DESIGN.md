# Spline 3D Integration Design Document

**Project**: OwlWatcher Desktop Application
**Developer**: Marcus Daley
**Date**: 2026-02-24
**Purpose**: Comprehensive design for integrating interactive Spline 3D elements into PyQt6 desktop application

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [3D Elements Specification](#3d-elements-specification)
4. [Technical Integration Strategy](#technical-integration-strategy)
5. [Implementation Details](#implementation-details)
6. [Performance Considerations](#performance-considerations)
7. [Fallback Strategy](#fallback-strategy)
8. [File Structure](#file-structure)
9. [Implementation Checklist](#implementation-checklist)
10. [Code Examples](#code-examples)

---

## Executive Summary

This document outlines the integration of interactive Spline 3D elements into the OwlWatcher PyQt6 desktop application. The design uses `QWebEngineView` to embed Spline's web runtime, enabling real-time 3D animations and interactivity while maintaining the existing PyQt6 architecture.

**Key Integration Points:**
- 3D Animated Owl Mascot (replaces 2D sprite system)
- 3D Moon Toggle Button (theme switcher)
- 3D File Visualization Dashboard
- 3D Statistics Visualization
- 3D Interactive Controls

**Recommended Approach:** QWebEngineView with JavaScript bridge for bidirectional communication between PyQt6 and Spline runtime.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    OwlWatcher Application (PyQt6)               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐         ┌───────────────────────────────┐  │
│  │               │         │                               │  │
│  │  MainWindow   │◄────────┤   OwlStateMachine             │  │
│  │               │         │   (state transitions)         │  │
│  └───────┬───────┘         └───────────────────────────────┘  │
│          │                                                      │
│          │ creates/manages                                     │
│          │                                                      │
│  ┌───────▼────────────────────────────────────────────────┐   │
│  │         Spline3DWidget (QWidget)                       │   │
│  │                                                         │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  QWebEngineView                                  │  │   │
│  │  │  ┌────────────────────────────────────────────┐  │  │   │
│  │  │  │  HTML + Spline Runtime (@splinetool/runtime)│  │  │   │
│  │  │  │                                             │  │  │   │
│  │  │  │  ┌────────────────────────────────────┐    │  │  │   │
│  │  │  │  │  Spline 3D Scene (*.splinecode)    │    │  │  │   │
│  │  │  │  │  - Owl Mascot                      │    │  │  │   │
│  │  │  │  │  - Moon Toggle                     │    │  │  │   │
│  │  │  │  │  - File Visualization              │    │  │  │   │
│  │  │  │  │  - Stats Widgets                   │    │  │  │   │
│  │  │  │  └────────────────────────────────────┘    │  │  │   │
│  │  │  └────────────────────────────────────────────┘  │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │                                                         │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  QWebChannel (JavaScript ↔ PyQt6 Bridge)         │  │   │
│  │  │  - emit_state_change(state: str)                 │  │   │
│  │  │  - emit_theme_change(theme: str)                 │  │   │
│  │  │  - emit_file_event(file_data: dict)              │  │   │
│  │  │  - emit_stats_update(stats: dict)                │  │   │
│  │  │  - receive_3d_click(object_id: str)              │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Data Flow:
PyQt6 State Change ─────► QWebChannel ─────► JavaScript ─────► Spline Scene Update
Spline User Interaction ◄──── QWebChannel ◄──── JavaScript Event ◄──── 3D Click
```

---

## 3D Elements Specification

### 1. 3D Animated Owl Mascot

**Purpose**: Replace the current 2D sprite-based owl with fully interactive 3D model.

**States to Animate** (matching current state machine):
- `sleeping`: Gentle breathing, eyes closed, head tucked
- `waking`: Stretching wings, one eye opening, yawning motion
- `idle`: Alert posture, slow head turn (15° rotation), occasional blink
- `scanning`: 360° head rotation (smooth loop), focused eyes
- `curious`: Head tilt, eyes wide, ear tufts raised
- `alert`: Feathers ruffle, eyes wide, body upright
- `alarm`: Red glow effect, rapid feather puff, pulsing animation
- `proud`: Chest out, wings slightly spread, confident stance

**Spline Animation Specifications**:
- **Idle State Loop**: 3-second breathing cycle (chest expand/contract)
- **Head Turn**: 2-second smooth rotation interpolation
- **Alert Pulse**: 1.5-second loop with scale 1.0 → 1.05 → 1.0
- **Alarm Glow**: Emissive material on eyes, intensity 0 → 100 over 0.5s
- **Feather Ruffle**: Physics-based simulation with spring damping

**Interactive Features**:
- Hover: Owl eyes follow cursor within 30° cone
- Click: Play "hoot" sound effect, brief head bob animation
- Speech Bubble Integration: Position bubble 60px above owl's head in 3D space

**Materials**:
- Body: PBR material with subsurface scattering (feather depth)
- Eyes: Glossy BSDF with reflection map
- Beak: Metallic gold accent (#C9A94E)
- Emissive glow (alarm state): #FF6B6B

**Spline Scene File**: `owl_mascot.splinecode`

---

### 2. 3D Moon Toggle Button

**Purpose**: Replace flat moon SVG button with interactive 3D rotating moon for theme switching.

**Visual States**:
- **Dark Theme**: Full moon with crater details, cool blue-white glow
- **Light Theme**: Sun with warm yellow-orange glow, radial rays

**Animations**:
- **Rotation**: Continuous slow spin (360° over 60 seconds)
- **Transition**: Day → Night crossfade with 1-second rotation flip
- **Hover Effect**: Scale 1.0 → 1.1, glow intensity +20%
- **Click Ripple**: Radial shockwave emanating from click point (0.5s duration)
- **Orbiting Particles**:
  - Night mode: 8 white stars orbiting at varying speeds
  - Day mode: Yellow light rays pulsing outward

**Materials**:
- Moon surface: Bump-mapped texture with normal map for craters
- Sun surface: Emissive shader with noise displacement
- Glow: Bloom post-processing effect

**Interactive Features**:
- Click: Toggle theme + emit `themeChanged` signal to PyQt6
- Hover: Tooltip appears showing "Switch to Light/Dark Theme"

**Spline Scene File**: `moon_toggle.splinecode`

---

### 3. 3D File Visualization Dashboard

**Purpose**: Display watched files as floating 3D objects in orbital layout around owl.

**File Representations**:
- **Python files**: Blue glowing cubes (#3B82F6)
- **JSON files**: Green spinning spheres (#10B981)
- **Markdown files**: Gold floating documents (#C9A94E)
- **Executable files**: Red pulsing dodecahedrons (#EF4444, warning state)

**Animations**:
- **Orbital Motion**: Files orbit owl in elliptical paths (varying speeds)
- **Create Event**: File fades in with scale 0 → 1 over 0.8s
- **Modify Event**: Pulse animation (scale 1.0 → 1.2 → 1.0 over 0.5s) + bright flash
- **Delete Event**: Fade out + particle explosion (0.6s duration)
- **Hover**: File enlarges to 1.3x scale, displays filename tooltip

**Layout Algorithm**:
```
- Max visible files: 20 (oldest files fade out as new ones arrive)
- Orbital radius: 150-250px from owl center (randomized per file)
- Vertical spread: -50px to +50px (creates depth)
- Rotation speed: 10-30 seconds per orbit (file-type dependent)
```

**Interactive Features**:
- Click file: Emit `fileClicked` signal with file path to PyQt6
- Right-click: Context menu (open location, view details)

**Spline Scene File**: `file_dashboard.splinecode`

---

### 4. 3D Stats Visualization

**Purpose**: Replace 2D charts with interactive 3D data visualizations.

#### 4.1 Events Per Minute (3D Bar Chart)
- **Visual**: Rising/falling 3D bars with gradient fill
- **Animation**: Bars grow from 0 to target height over 0.5s
- **Color Gradient**: Green (low activity) → Yellow (moderate) → Red (burst detected)
- **Max Bars**: 10 bars representing last 10 minutes
- **Interaction**: Hover shows exact event count tooltip

#### 4.2 Threat Level (Rotating Energy Orb)
- **Visual**: Pulsing sphere with particle effects
- **Colors**:
  - Low threat: Green (#10B981)
  - Moderate threat: Yellow (#FBBF24)
  - High threat: Red (#EF4444) with flame particles
- **Animation**: Rotation speed increases with threat level
- **Size**: Scales from 40px (low) to 80px (high)

#### 4.3 Uptime Ring (3D Progress Indicator)
- **Visual**: Circular ring that fills clockwise as uptime increases
- **Color**: Gold (#C9A94E) with metallic shader
- **Animation**: Smooth fill progress with trailing glow effect
- **Center Text**: Displays uptime in HH:MM:SS (3D extruded text)

#### 4.4 File Type Distribution (3D Pie Chart)
- **Visual**: Exploded pie chart with floating slices
- **Animation**: Slices rotate slowly and gently bob up/down
- **Colors**: Match file type colors from dashboard
- **Interaction**: Click slice to filter event log by file type

**Spline Scene File**: `stats_visualization.splinecode`

---

### 5. Interactive 3D Controls

**Purpose**: Replace flat QPushButton widgets with 3D glass-morphism styled controls.

#### 5.1 Start/Stop Button
- **Visual**: 3D glass sphere with frosted transparency
- **Idle State**: Green glow (#10B981), "START" text floating inside
- **Active State**: Red glow (#EF4444), "STOP" text, pulsing animation
- **Click Animation**: Shockwave ripple + scale bounce (1.0 → 0.9 → 1.0)

#### 5.2 Export Button
- **Visual**: 3D download arrow icon inside glass container
- **Hover**: Arrow bounces downward repeatedly (0.8s loop)
- **Click**: Arrow shoots downward out of view, particles trail behind
- **File Export Progress**: Progress bar fills glass container from bottom to top

#### 5.3 Settings Gear
- **Visual**: 3D mechanical gear with metallic material
- **Hover**: Gear rotates 90° clockwise
- **Click**: Full 360° spin with bounce easing
- **Active State**: Continuous slow rotation while settings dialog is open

**Materials**: Glass BSDF with roughness 0.2, IOR 1.45, transmission 0.8

**Spline Scene Files**: `controls_start_stop.splinecode`, `controls_export.splinecode`, `controls_settings.splinecode`

---

## Technical Integration Strategy

### Option A: QWebEngineView (Recommended)

**Advantages**:
- Full access to Spline's interactive runtime
- Real-time bidirectional communication via QWebChannel
- Hardware-accelerated WebGL rendering
- Supports mouse/keyboard events
- Can embed multiple Spline scenes in one view

**Disadvantages**:
- Requires PyQtWebEngine dependency
- Larger memory footprint than native Qt widgets
- Requires WebGL support (fallback needed)

**Dependencies**:
```bash
pip install PyQt6-WebEngine
```

---

### Option B: Video/GIF Export (NOT Recommended)

**Why Not**:
- No interactivity (static playback only)
- Large file sizes for smooth animations
- Cannot respond to state changes in real-time
- No mouse hover/click detection

---

### Option C: Electron Companion App (Overkill)

**Why Not**:
- Separate process complexity
- IPC overhead for communication
- Duplicates existing PyQt6 UI
- Harder to maintain consistency

---

## Implementation Details

### QWebEngineView Integration

#### Core Spline3DWidget

```python
# spline_3d_widget.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Base widget for embedding Spline 3D scenes in PyQt6 via QWebEngineView

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import QObject, QUrl, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QVBoxLayout, QWidget

logger = logging.getLogger("spline_3d_widget")


class SplineBridge(QObject):
    """JavaScript ↔ PyQt6 communication bridge.

    Exposes Python methods to JavaScript via QWebChannel and provides
    callback registration for events from Spline runtime.
    """

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._event_callbacks: dict[str, Callable[[Any], None]] = {}

    def register_callback(self, event_name: str, callback: Callable[[Any], None]) -> None:
        """Register a Python callback for a JavaScript event.

        Parameters
        ----------
        event_name:
            Name of the event (e.g., "clicked", "hoverEnter")
        callback:
            Python function to call when event fires from JavaScript
        """
        self._event_callbacks[event_name] = callback
        logger.debug("Registered callback for event: %s", event_name)

    @pyqtSlot(str, str)
    def emit_event(self, event_name: str, data_json: str) -> None:
        """Called from JavaScript when a Spline event occurs.

        Parameters
        ----------
        event_name:
            Event identifier
        data_json:
            JSON-encoded event data
        """
        try:
            data = json.loads(data_json) if data_json else {}
            callback = self._event_callbacks.get(event_name)
            if callback:
                callback(data)
            else:
                logger.warning("No callback registered for event: %s", event_name)
        except json.JSONDecodeError as exc:
            logger.error("Failed to decode event data JSON: %s", exc)

    @pyqtSlot(str)
    def log_from_js(self, message: str) -> None:
        """Logging proxy for JavaScript console messages."""
        logger.debug("[Spline JS] %s", message)


class Spline3DWidget(QWidget):
    """Base widget for embedding Spline 3D scenes in PyQt6.

    Parameters
    ----------
    scene_url:
        URL or local file path to Spline scene HTML file
    width:
        Widget width in pixels
    height:
        Widget height in pixels
    parent:
        Optional parent widget

    Usage::

        widget = Spline3DWidget("file:///assets/owl_mascot.html", 300, 300)
        widget.register_callback("clicked", lambda data: print("Owl clicked!"))
        widget.call_js_function("setState", "alert")
    """

    def __init__(
        self,
        scene_url: str,
        width: int = 400,
        height: int = 400,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setFixedSize(width, height)

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Web view
        self._web_view = QWebEngineView(self)
        self._web_view.setFixedSize(width, height)

        # JavaScript bridge
        self._bridge = SplineBridge(self)
        self._channel = QWebChannel(self)
        self._channel.registerObject("pyqt_bridge", self._bridge)

        # Inject QWebChannel into web page
        self._web_view.page().setWebChannel(self._channel)

        # Load scene
        if scene_url.startswith("http://") or scene_url.startswith("https://"):
            self._web_view.setUrl(QUrl(scene_url))
        else:
            # Local file path
            file_url = QUrl.fromLocalFile(str(Path(scene_url).resolve()))
            self._web_view.setUrl(file_url)

        layout.addWidget(self._web_view)

        logger.info("Spline3DWidget initialized with scene: %s", scene_url)

    def register_callback(self, event_name: str, callback: Callable[[Any], None]) -> None:
        """Register a callback for Spline runtime events.

        Parameters
        ----------
        event_name:
            Event identifier (e.g., "owlClicked", "moonToggled")
        callback:
            Python function to execute when event fires
        """
        self._bridge.register_callback(event_name, callback)

    def call_js_function(self, function_name: str, *args: Any) -> None:
        """Call a JavaScript function exposed by the Spline scene.

        Parameters
        ----------
        function_name:
            Name of the global JavaScript function
        *args:
            Arguments to pass (must be JSON-serializable)
        """
        args_json = json.dumps(args)
        js_code = f"{function_name}(...{args_json});"
        self._web_view.page().runJavaScript(js_code)
        logger.debug("Called JS function: %s with args: %s", function_name, args_json)

    def reload_scene(self) -> None:
        """Reload the Spline scene (useful for development/debugging)."""
        self._web_view.reload()
```

---

#### Spline HTML Template

**File**: `C:\ClaudeSkills\scripts\gui\assets\spline_scenes\owl_mascot.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Owl Mascot 3D</title>
    <style>
        body, html {
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: transparent;
        }
        canvas {
            width: 100%;
            height: 100%;
            display: block;
        }
    </style>
</head>
<body>
    <canvas id="canvas3d"></canvas>

    <!-- Spline Runtime -->
    <script type="module">
        import { Application } from 'https://unpkg.com/@splinetool/runtime@latest/build/runtime.js';

        const canvas = document.getElementById('canvas3d');
        const app = new Application(canvas);

        // Load Spline scene (replace with your exported .splinecode URL)
        app.load('https://prod.spline.design/YOUR_SCENE_ID/scene.splinecode');

        // QWebChannel setup for PyQt6 communication
        let pyqtBridge = null;

        new QWebChannel(qt.webChannelTransport, function(channel) {
            pyqtBridge = channel.objects.pyqt_bridge;
            console.log('QWebChannel bridge connected');
            pyqtBridge.log_from_js('Spline scene loaded successfully');
        });

        // Helper: Send event to Python
        function emitToPython(eventName, data) {
            if (pyqtBridge) {
                const jsonData = JSON.stringify(data);
                pyqtBridge.emit_event(eventName, jsonData);
            }
        }

        // Global functions callable from Python
        window.setState = function(stateName) {
            console.log('Setting owl state:', stateName);

            // Map state names to Spline animation triggers
            const animations = {
                'sleeping': 'Sleeping Loop',
                'waking': 'Waking Transition',
                'idle': 'Idle Loop',
                'scanning': 'Scanning 360',
                'curious': 'Curious Tilt',
                'alert': 'Alert Feathers',
                'alarm': 'Alarm Pulse',
                'proud': 'Proud Stance'
            };

            const animName = animations[stateName];
            if (animName) {
                // Trigger Spline animation by name
                const owl = app.findObjectByName('Owl');
                if (owl) {
                    owl.emitEvent('mouseDown'); // Example: trigger animation
                }
            }
        };

        window.setTheme = function(themeName) {
            console.log('Setting theme:', themeName);

            // Adjust scene lighting/materials based on theme
            if (themeName === 'light') {
                // Increase ambient light intensity
                const ambientLight = app.findObjectByName('Ambient Light');
                if (ambientLight) {
                    ambientLight.intensity = 1.5;
                }
            } else {
                const ambientLight = app.findObjectByName('Ambient Light');
                if (ambientLight) {
                    ambientLight.intensity = 0.8;
                }
            }
        };

        // Forward Spline events to Python
        app.addEventListener('mouseDown', (event) => {
            if (event.target && event.target.name === 'Owl') {
                emitToPython('owlClicked', { timestamp: Date.now() });
            }
        });

        app.addEventListener('mouseHover', (event) => {
            if (event.target && event.target.name === 'Owl') {
                emitToPython('owlHover', { x: event.position.x, y: event.position.y });
            }
        });
    </script>

    <!-- QWebChannel JavaScript library (injected by PyQt6) -->
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
</body>
</html>
```

---

#### Owl3D Widget (Spline-Powered)

```python
# owl_3d_spline_widget.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Spline-based 3D owl mascot widget integrating with OwlStateMachine

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtWidgets import QWidget

from gui.constants import OWL_HEADER_SIZE
from gui.paths import ASSETS_DIR
from gui.widgets.spline_3d_widget import Spline3DWidget

logger = logging.getLogger("owl_3d_spline_widget")

# Path to Spline scene HTML
_OWL_SCENE_PATH = ASSETS_DIR / "spline_scenes" / "owl_mascot.html"


class Owl3DSplineWidget(QWidget):
    """Spline-powered 3D owl mascot widget.

    Drop-in replacement for Owl3DWidget that uses Spline runtime for
    fully interactive 3D animations.

    Parameters
    ----------
    owl_size:
        Width and height of the owl display area in pixels.
    parent:
        Optional parent widget.
    """

    def __init__(
        self,
        owl_size: int = OWL_HEADER_SIZE,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._current_state = "idle"

        # Create Spline 3D widget
        self._spline_widget = Spline3DWidget(
            scene_url=str(_OWL_SCENE_PATH),
            width=owl_size,
            height=owl_size,
            parent=self,
        )

        # Register event callbacks
        self._spline_widget.register_callback("owlClicked", self._on_owl_clicked)
        self._spline_widget.register_callback("owlHover", self._on_owl_hover)

        # Set initial state
        self.set_state("idle")

    def set_state(self, state: str) -> None:
        """Switch the owl to a visual state.

        Parameters
        ----------
        state:
            One of the 8 owl states (sleeping, waking, idle, scanning,
            curious, alert, alarm, proud).
        """
        valid_states = {
            "sleeping", "waking", "idle", "scanning",
            "curious", "alert", "alarm", "proud"
        }

        if state not in valid_states:
            logger.warning("Unknown owl state: %r (using idle)", state)
            state = "idle"

        self._current_state = state
        self._spline_widget.call_js_function("setState", state)
        logger.info("Owl state changed to: %s", state)

    @property
    def current_state(self) -> str:
        """Return the current owl state name."""
        return self._current_state

    def say(self, message: str, duration_ms: int = 5000) -> None:
        """Show a speech bubble with the given message.

        Parameters
        ----------
        message:
            Text to display in the speech bubble.
        duration_ms:
            How long to show the bubble before it fades out.
        """
        # Send message to Spline runtime to render 3D speech bubble
        self._spline_widget.call_js_function(
            "showSpeechBubble",
            message,
            duration_ms,
        )

    def dismiss(self) -> None:
        """Immediately hide the speech bubble."""
        self._spline_widget.call_js_function("hideSpeechBubble")

    # -- Private event handlers -----------------------------------------------

    def _on_owl_clicked(self, data: dict) -> None:
        """Handle owl click event from Spline runtime."""
        logger.info("Owl clicked at timestamp: %s", data.get("timestamp"))
        # Could emit Qt signal here for MainWindow to handle

    def _on_owl_hover(self, data: dict) -> None:
        """Handle owl hover event from Spline runtime."""
        # Could implement eye-tracking cursor follow here
        pass
```

---

#### Moon Toggle Button (Spline)

```python
# moon_toggle_3d_widget.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Spline-based 3D moon toggle button for theme switching

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget

from gui.paths import ASSETS_DIR
from gui.theme import Theme
from gui.widgets.spline_3d_widget import Spline3DWidget

logger = logging.getLogger("moon_toggle_3d_widget")

_MOON_SCENE_PATH = ASSETS_DIR / "spline_scenes" / "moon_toggle.html"


class MoonToggle3DWidget(QWidget):
    """Interactive 3D moon toggle button for theme switching.

    Emits `themeToggled` signal when clicked, with the new theme.
    """

    themeToggled = pyqtSignal(Theme)

    def __init__(self, width: int = 80, height: int = 80, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_theme = Theme.DARK

        self._spline_widget = Spline3DWidget(
            scene_url=str(_MOON_SCENE_PATH),
            width=width,
            height=height,
            parent=self,
        )

        # Register click event
        self._spline_widget.register_callback("moonClicked", self._on_moon_clicked)

    def set_theme(self, theme: Theme) -> None:
        """Update the moon visual state to match the current theme.

        Parameters
        ----------
        theme:
            The theme to display (DARK shows moon, LIGHT shows sun)
        """
        self._current_theme = theme
        theme_name = "dark" if theme == Theme.DARK else "light"
        self._spline_widget.call_js_function("setTheme", theme_name)

    def _on_moon_clicked(self, data: dict) -> None:
        """Handle moon button click event."""
        new_theme = Theme.LIGHT if self._current_theme == Theme.DARK else Theme.DARK
        self._current_theme = new_theme

        # Update Spline visual with transition animation
        theme_name = "dark" if new_theme == Theme.DARK else "light"
        self._spline_widget.call_js_function("setTheme", theme_name)

        # Emit signal for ThemeManager
        self.themeToggled.emit(new_theme)
        logger.info("Theme toggled to: %s", new_theme.value)
```

---

## Performance Considerations

### Memory Footprint
- **QWebEngineView overhead**: ~50-80 MB per instance (Chromium engine)
- **Spline scene size**: 2-5 MB per `.splinecode` file
- **Recommendation**: Limit to 3-4 concurrent Spline widgets maximum

### GPU Acceleration
- **WebGL requirement**: Fallback needed for systems without GPU support
- **Detection**:
```python
def check_webgl_support() -> bool:
    """Check if system supports WebGL rendering."""
    from PyQt6.QtWebEngineCore import QWebEngineProfile

    profile = QWebEngineProfile.defaultProfile()
    settings = profile.settings()

    # Check if WebGL is available
    return settings.testAttribute(
        settings.WebAttribute.WebGLEnabled
    )
```

### Frame Rate Optimization
- Target 60 FPS for smooth animations
- Use Spline's LOD (Level of Detail) system for complex scenes
- Limit particle counts:
  - Idle state: 0 particles
  - Alert state: Max 50 particles
  - Alarm state: Max 100 particles

### Asset Loading
- **Lazy loading**: Load Spline scenes only when widget is visible
- **Preloading**: Critical scenes (owl mascot) load on app startup
- **Caching**: Spline runtime caches loaded scenes automatically

---

## Fallback Strategy

### Graceful Degradation Path

```python
# spline_fallback.py
# Developer: Marcus Daley
# Date: 2026-02-24
# Purpose: Automatic fallback from Spline 3D to 2D sprites when WebGL unavailable

from __future__ import annotations

import logging
from typing import Type

from PyQt6.QtWidgets import QWidget

logger = logging.getLogger("spline_fallback")


def get_owl_widget_class() -> Type[QWidget]:
    """Return the appropriate owl widget class based on system capabilities.

    Returns Owl3DSplineWidget if WebGL is supported, otherwise falls back
    to Owl3DWidget (sprite-based).
    """
    try:
        # Attempt to import QWebEngineView
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        from gui.widgets.owl_3d_spline_widget import Owl3DSplineWidget

        # Check WebGL support
        if check_webgl_support():
            logger.info("WebGL supported - using Spline 3D owl widget")
            return Owl3DSplineWidget
        else:
            logger.warning("WebGL not supported - falling back to sprite-based owl")
            from gui.widgets.owl_3d_widget import Owl3DWidget
            return Owl3DWidget

    except ImportError:
        logger.warning("PyQt6-WebEngine not installed - using sprite-based owl")
        from gui.widgets.owl_3d_widget import Owl3DWidget
        return Owl3DWidget


def check_webgl_support() -> bool:
    """Check if the system supports WebGL rendering."""
    try:
        from PyQt6.QtWebEngineCore import QWebEngineProfile

        profile = QWebEngineProfile.defaultProfile()
        settings = profile.settings()

        return settings.testAttribute(
            settings.WebAttribute.WebGLEnabled
        )
    except Exception as exc:
        logger.error("Failed to check WebGL support: %s", exc)
        return False
```

**Usage in MainWindow**:
```python
from gui.widgets.spline_fallback import get_owl_widget_class

# In MainWindow.__init__:
OwlWidgetClass = get_owl_widget_class()
self._owl = OwlWidgetClass(owl_size=OWL_HEADER_SIZE)
```

---

## File Structure

```
C:\ClaudeSkills\
├── scripts\
│   └── gui\
│       ├── assets\
│       │   ├── spline_scenes\           # Spline HTML integration files
│       │   │   ├── owl_mascot.html
│       │   │   ├── moon_toggle.html
│       │   │   ├── file_dashboard.html
│       │   │   ├── stats_visualization.html
│       │   │   └── controls.html
│       │   │
│       │   ├── spline_code\              # Exported .splinecode files
│       │   │   ├── owl_mascot.splinecode
│       │   │   ├── moon_toggle.splinecode
│       │   │   ├── file_dashboard.splinecode
│       │   │   ├── stats_visualization.splinecode
│       │   │   └── controls_*.splinecode
│       │   │
│       │   └── owl_3d\                   # Fallback 2D sprites (existing)
│       │       ├── owl_3d_sleeping.png
│       │       └── ...
│       │
│       └── widgets\
│           ├── spline_3d_widget.py       # Base Spline integration widget
│           ├── spline_fallback.py        # Fallback strategy logic
│           ├── owl_3d_spline_widget.py   # Spline-powered owl mascot
│           ├── moon_toggle_3d_widget.py  # Spline-powered moon button
│           ├── file_dashboard_3d.py      # 3D file visualization
│           ├── stats_3d_widgets.py       # 3D chart widgets
│           └── controls_3d_widgets.py    # 3D button widgets
│
└── docs\
    └── SPLINE_3D_INTEGRATION_DESIGN.md  # This document
```

---

## Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Install PyQt6-WebEngine dependency
- [ ] Create `Spline3DWidget` base class with QWebChannel bridge
- [ ] Test basic HTML embedding with simple Spline scene
- [ ] Verify bidirectional communication (Python → JS → Python)
- [ ] Implement WebGL fallback detection

### Phase 2: Owl Mascot (Week 2)
- [ ] Design 3D owl model in Spline (or commission artist)
- [ ] Create all 8 state animations in Spline
- [ ] Export `owl_mascot.splinecode`
- [ ] Build `owl_mascot.html` integration file
- [ ] Implement `Owl3DSplineWidget` with state machine integration
- [ ] Add speech bubble 3D rendering in Spline scene
- [ ] Test state transitions and event callbacks

### Phase 3: Moon Toggle (Week 3)
- [ ] Design 3D moon/sun models in Spline
- [ ] Implement rotation and transition animations
- [ ] Add particle effects (stars/rays)
- [ ] Build `MoonToggle3DWidget` with theme integration
- [ ] Connect to `ThemeManager.toggle_theme()`
- [ ] Test theme switching in both directions

### Phase 4: File Visualization (Week 4)
- [ ] Design 3D file object models (cubes, spheres, documents)
- [ ] Implement orbital layout algorithm in JavaScript
- [ ] Add create/modify/delete animations
- [ ] Build file event data pipeline (Python → Spline)
- [ ] Test with real file watcher events
- [ ] Optimize performance for 20+ concurrent file objects

### Phase 5: Stats Visualization (Week 5)
- [ ] Design 3D bar chart, energy orb, ring, and pie chart
- [ ] Implement data-driven animations
- [ ] Build data update pipeline from SecurityEngine
- [ ] Add interactive tooltips
- [ ] Test with live stats updates

### Phase 6: Controls (Week 6)
- [ ] Design glass-morphism 3D button models
- [ ] Implement hover/click animations
- [ ] Connect to existing QPushButton functionality
- [ ] Add accessibility keyboard shortcuts
- [ ] Test all control interactions

### Phase 7: Polish & Optimization (Week 7)
- [ ] Performance profiling (FPS, memory usage)
- [ ] Optimize Spline scene LOD settings
- [ ] Add loading spinners for scene initialization
- [ ] Implement graceful error handling
- [ ] Write unit tests for QWebChannel bridge
- [ ] Document all public APIs

### Phase 8: Deployment (Week 8)
- [ ] Create installation guide for PyQt6-WebEngine
- [ ] Package Spline scenes with application
- [ ] Test on multiple systems (GPU vs. CPU rendering)
- [ ] Verify fallback strategy on low-end hardware
- [ ] Update `CLAUDE.md` with Spline integration notes

---

## Code Examples

### Example 1: Updating Owl State from Python

```python
# In main_window.py or wherever OwlStateMachine is used:

from gui.widgets.spline_fallback import get_owl_widget_class

# Initialize owl widget
OwlWidgetClass = get_owl_widget_class()
self._owl = OwlWidgetClass(owl_size=OWL_HEADER_SIZE)

# Connect to state machine
self._owl_state_machine.state_changed.connect(self._on_owl_state_changed)

def _on_owl_state_changed(self, new_state: OwlState) -> None:
    """Handle owl state transitions."""
    state_name = new_state.name.lower()  # e.g., "ALERT" -> "alert"
    self._owl.set_state(state_name)
```

### Example 2: Moon Toggle Theme Switching

```python
# In main_window.py header:

from gui.widgets.moon_toggle_3d_widget import MoonToggle3DWidget
from gui.theme import ThemeManager, Theme

# Initialize widgets
self._theme_manager = ThemeManager()
self._moon_toggle = MoonToggle3DWidget(width=60, height=60)

# Connect signals
self._moon_toggle.themeToggled.connect(self._on_theme_toggled)

def _on_theme_toggled(self, new_theme: Theme) -> None:
    """Handle theme change from moon button click."""
    self._theme_manager.apply_theme(new_theme)

    # Update all other widgets to match theme
    self._update_all_widget_themes(new_theme)
```

### Example 3: File Event to 3D Visualization

```python
# In file_dashboard_3d.py:

from gui.widgets.spline_3d_widget import Spline3DWidget

class FileDashboard3DWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._spline = Spline3DWidget(
            scene_url="assets/spline_scenes/file_dashboard.html",
            width=400,
            height=400,
        )

        # Register click callback
        self._spline.register_callback("fileClicked", self._on_file_clicked)

    def add_file_event(self, event_type: str, file_path: str, file_ext: str) -> None:
        """Forward file event to Spline scene for visualization.

        Parameters
        ----------
        event_type:
            "created", "modified", or "deleted"
        file_path:
            Full path to the file
        file_ext:
            File extension (e.g., ".py")
        """
        event_data = {
            "type": event_type,
            "path": file_path,
            "extension": file_ext,
            "timestamp": datetime.now().isoformat(),
        }

        self._spline.call_js_function("addFileEvent", event_data)

    def _on_file_clicked(self, data: dict) -> None:
        """Handle file object click in 3D scene."""
        file_path = data.get("path", "")
        logger.info("File clicked in 3D view: %s", file_path)

        # Open file location in file explorer
        import subprocess
        subprocess.Popen(f'explorer /select,"{file_path}"')
```

### Example 4: Stats Update Pipeline

```python
# In stats_3d_widgets.py:

from gui.widgets.spline_3d_widget import Spline3DWidget

class Stats3DWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._spline = Spline3DWidget(
            scene_url="assets/spline_scenes/stats_visualization.html",
            width=600,
            height=400,
        )

    def update_events_per_minute(self, counts: list[int]) -> None:
        """Update the 3D bar chart with new event counts.

        Parameters
        ----------
        counts:
            List of event counts for last 10 minutes (newest first)
        """
        self._spline.call_js_function("updateBarChart", counts)

    def update_threat_level(self, level: float) -> None:
        """Update the threat orb visualization.

        Parameters
        ----------
        level:
            Threat level from 0.0 (safe) to 1.0 (critical)
        """
        self._spline.call_js_function("updateThreatOrb", level)

    def update_uptime(self, seconds: int) -> None:
        """Update the uptime ring progress.

        Parameters
        ----------
        seconds:
            Total uptime in seconds
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        uptime_data = {
            "total_seconds": seconds,
            "display": f"{hours:02d}:{minutes:02d}:{secs:02d}"
        }

        self._spline.call_js_function("updateUptimeRing", uptime_data)
```

---

## Next Steps

### Immediate Actions
1. Install PyQt6-WebEngine and test basic QWebEngineView functionality
2. Create a simple Spline scene (e.g., rotating cube) as proof-of-concept
3. Implement `Spline3DWidget` base class and verify QWebChannel communication

### Designer Actions
1. Design 3D owl model in Spline with all 8 state animations
2. Export owl scene as `.splinecode` and embed in HTML template
3. Create moon/sun toggle button with transition animation

### Integration Planning
1. Review current `OwlStateMachine` signal flow
2. Plan widget replacement strategy (phased vs. all-at-once)
3. Determine performance benchmarks for acceptable frame rates

---

## References

- **Spline Documentation**: https://docs.spline.design
- **Spline Runtime API**: https://www.npmjs.com/package/@splinetool/runtime
- **PyQt6 QWebEngineView**: https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineWidgets/QWebEngineView.html
- **QWebChannel Guide**: https://doc.qt.io/qt-6/qtwebchannel-javascript.html

---

**Document Version**: 1.0
**Last Updated**: 2026-02-24
**Status**: Design Complete - Ready for Implementation
