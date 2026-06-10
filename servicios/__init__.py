"""Servicios package — backward-compatible re-exports with deprecation warnings.

Each platform service is now a sub-package (e.g. servicios.sala).
Old import paths still work but emit DeprecationWarning.
"""
from __future__ import annotations

import warnings
from typing import Any


def __getattr__(name: str) -> Any:
    """Lazy import with deprecation warning for old-style imports."""
    _aliases: dict[str, tuple[str, str]] = {
        # "OldClassName": ("module.path", "ClassName")
        "ServicioSala": ("servicios.sala", "ServicioSala"),
        "ServicioTiktok": ("servicios.tiktok", "ServicioTiktok"),
        "ServicioKick": ("servicios.kick", "ServicioKick"),
        "ServicioYouTube": ("servicios.youtube", "ServicioYouTube"),
        "ServicioTwich": ("servicios.twich", "ServicioTwich"),
        "YouTubeRealTimeService": ("servicios.youtuberealtime", "YouTubeRealTimeService"),
    }

    if name in _aliases:
        module_path, class_name = _aliases[name]
        warnings.warn(
            f"Importing {name} from 'servicios' is deprecated. "
            f"Use 'from {module_path} import {class_name}' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    raise AttributeError(f"module 'servicios' has no attribute {name!r}")
