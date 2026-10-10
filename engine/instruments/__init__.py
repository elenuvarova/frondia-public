"""Приборы измерения. Импорт модуля наполняет REGISTRY."""

from .base import Instrument, Reading, Verdict, REGISTRY, register  # noqa: F401
from . import vegetation  # noqa: F401  — регистрирует ndvi, built, trees, grass, bare, shrub
from . import landsat     # noqa: F401  — регистрирует ndvi_landsat (30 м, ряд с 1984)

__all__ = ["Instrument", "Reading", "Verdict", "REGISTRY", "register"]
