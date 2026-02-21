# sound_manager.py
# Developer: Marcus Daley
# Date: 2026-02-20
# Purpose: Audio feedback for state transitions with graceful degradation when QtMultimedia unavailable

"""
Sound effect manager for OwlWatcher.

Wraps Qt multimedia to play short owl-themed sounds on state transitions.
Degrades gracefully if QtMultimedia is unavailable.

Usage::

    sounds = SoundManager()
    sounds.enabled = True
    sounds.play("startup")
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QSettings, QUrl

from gui.constants import QSETTINGS_APP, QSETTINGS_ORG
from gui.paths import ASSETS_DIR

logger = logging.getLogger("sound_manager")

SOUNDS_DIR = ASSETS_DIR / "sounds"

# Sound name -> WAV filename
_SOUND_FILES: dict[str, str] = {
    "startup": "startup_hoot.wav",
    "alert": "alert_chirp.wav",
    "alarm": "alarm_hoot.wav",
    "allclear": "allclear_settle.wav",
}

# Try importing QtMultimedia (may not be installed)
_HAS_MULTIMEDIA = False
_QSoundEffect = None

try:
    from PyQt6.QtMultimedia import QSoundEffect
    _HAS_MULTIMEDIA = True
    _QSoundEffect = QSoundEffect
except ImportError:
    logger.info("QtMultimedia not available -- sounds disabled.")


class SoundManager:
    """Manages owl sound effects with enable/disable persistence.

    Parameters
    ----------
    settings_key:
        QSettings key to persist the enabled state.
    """

    def __init__(self, settings_key: str = "soundEnabled") -> None:
        self._settings_key = settings_key
        self._settings = QSettings(QSETTINGS_ORG, QSETTINGS_APP)
        self._enabled = self._settings.value(settings_key, False, type=bool)
        self._effects: dict[str, object] = {}

        if _HAS_MULTIMEDIA:
            self._load_effects()

    def _load_effects(self) -> None:
        """Pre-load all sound effects."""
        for name, filename in _SOUND_FILES.items():
            path = SOUNDS_DIR / filename
            if path.exists() and _QSoundEffect is not None:
                effect = _QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(0.5)
                self._effects[name] = effect
            else:
                logger.warning("Sound file not found: %s", path)

    @property
    def available(self) -> bool:
        """Whether the sound system is functional."""
        return _HAS_MULTIMEDIA and len(self._effects) > 0

    @property
    def enabled(self) -> bool:
        """Whether sounds are currently enabled."""
        return self._enabled and self.available

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        self._settings.setValue(self._settings_key, value)

    def play(self, name: str) -> None:
        """Play a named sound effect if enabled.

        Parameters
        ----------
        name:
            One of ``"startup"``, ``"alert"``, ``"alarm"``, ``"allclear"``.
        """
        if not self.enabled:
            return
        effect = self._effects.get(name)
        if effect is not None:
            effect.play()
        else:
            logger.debug("Unknown sound: %r", name)
