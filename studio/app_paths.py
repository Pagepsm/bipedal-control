"""Separate immutable packaged resources from user-controlled persistent data.

Packaged Windows application: sys._MEIPASS is PyInstaller's read-only resource root.
Source checkout: the directory containing this module.
"""
from __future__ import annotations
import os
from pathlib import Path
import sys

APP_SLUG = 'BipedalTerrainStudio'


def resource_root() -> Path:
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)).resolve()


def data_root() -> Path:
    # Override is intended only for isolated CI/developer tests, not for public web use.
    override = os.environ.get('BIPEDAL_DATA_ROOT')
    if override:
        return Path(override).expanduser().resolve()
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA')
        if not base:
            base = str(Path.home() / 'AppData' / 'Local')
        return Path(base) / APP_SLUG
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local' / 'share'))) / APP_SLUG


def ensure_data_dirs() -> Path:
    root = data_root()
    for sub in ('terrains', 'settings', 'logs'):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
