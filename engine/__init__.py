"""
Движок измерения городских изменений.

Принцип, зашитый в устройство: порог значимости — свойство пары
(город, прибор), измеренное на данных, а не константа в коде. Прибор без
калибровки может считать числа, но не имеет права называть их значимыми.
"""

from .config import CITIES, CONTROL, LIMITS, QUALITY, WINDOWS  # noqa: F401
from .manifest import Manifest, LayerEntry  # noqa: F401
from .audit import AuditResult, InstrumentResult, audit_footprint  # noqa: F401

__all__ = ["CITIES", "CONTROL", "LIMITS", "QUALITY", "WINDOWS",
           "Manifest", "LayerEntry",
           "AuditResult", "InstrumentResult", "audit_footprint"]
