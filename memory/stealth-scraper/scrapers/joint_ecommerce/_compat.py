"""
Compatibility loader for legacy `joint-ecommerce` modules.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

LEGACY_PACKAGE_NAME = "_joint_ecommerce_legacy"


def _legacy_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "joint-ecommerce"


def _ensure_legacy_package() -> None:
    """Register a virtual package that points at the legacy directory."""
    if LEGACY_PACKAGE_NAME in sys.modules:
        return

    legacy_path = _legacy_dir()
    if not legacy_path.exists():
        raise ModuleNotFoundError(
            f"Legacy module directory not found: {legacy_path}"
        )

    package = ModuleType(LEGACY_PACKAGE_NAME)
    package.__path__ = [str(legacy_path)]
    package.__file__ = str(legacy_path / "__init__.py")
    package.__package__ = LEGACY_PACKAGE_NAME
    sys.modules[LEGACY_PACKAGE_NAME] = package


def load_legacy_submodule(name: str):
    """Load a module from `joint-ecommerce` via a valid import namespace."""
    _ensure_legacy_package()
    return importlib.import_module(f"{LEGACY_PACKAGE_NAME}.{name}")
