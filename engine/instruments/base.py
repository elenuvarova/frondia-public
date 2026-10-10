"""
Реестр приборов измерения.

Устройство повторяет `spot-finder-geo/pipeline/formulas.py`: именованный реестр,
где каждая запись — самостоятельная сущность со своим смыслом, и их НЕЛЬЗЯ
схлопывать в одну общую формулу. Там это были разные типы заведений, здесь —
разные физические величины.

Что такое прибор
────────────────
Прибор умеет измерить одну величину по геометрии за окно времени и знает про
себя три вещи, без которых число нельзя публиковать:

  · что он меряет      — человеческими словами, для манифеста и отчёта
  · чем он меряет      — источник данных и метод
  · порог значимости   — измеренный на нулевом распределении ЭТОГО города

Последнее принципиально: порог не константа в коде, а результат калибровки.
Прибор без калибровки может считать числа, но не имеет права называть их
значимыми. Ровно эта дисциплина отделяет измерение от впечатления.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Reading:
    """Одно измерение по геометрии за окно."""

    value: float | None
    n_scenes: int | None = None
    note: str | None = None

    @property
    def usable(self) -> bool:
        return self.value is not None


@dataclass(frozen=True)
class Verdict:
    """Результат сравнения эффекта с порогом. Отказ — полноценный исход."""

    effect: float | None
    threshold: float | None
    outcome: str          # "significant_up" | "significant_down" | "noise"
                          # | "control_incomparable" | "insufficient_data"
    detail: str = ""

    @property
    def claimable(self) -> bool:
        """Можно ли вообще что-то утверждать по этому результату."""
        return self.outcome in ("significant_up", "significant_down", "noise")


class Instrument(ABC):
    """Базовый прибор. Подклассы описывают одну физическую величину."""

    #: короткое имя, ключ в манифесте и в таблицах
    name: str = ""
    #: что меряет — человеческими словами
    measures: str = ""
    #: единица измерения для печати
    unit: str = ""
    #: источник данных и метод
    source: str = ""
    #: чего этот прибор НЕ умеет; попадает в отчёт рядом с числом
    limits: tuple[str, ...] = ()

    @abstractmethod
    def measure(self, geom, start: str, end: str) -> Reading:
        """Измерить величину по геометрии за окно [start, end]."""

    def judge(self, effect: float | None, threshold: float | None,
              control_gap: float | None = None,
              max_gap: float | None = None) -> Verdict:
        """Превратить эффект в вердикт. Общая логика для всех приборов."""
        if effect is None:
            return Verdict(None, threshold, "insufficient_data",
                           "нет валидных пикселей или сцен в окне")
        if max_gap is not None and control_gap is not None and abs(control_gap) > max_gap:
            return Verdict(effect, threshold, "control_incomparable",
                           f"разрыв с контролем {control_gap:+.4f} превышает предел "
                           f"{max_gap}: сопоставимого контроля в городе нет")
        if threshold is None:
            return Verdict(effect, None, "insufficient_data",
                           "прибор не откалиброван для этого города")
        if effect > threshold:
            return Verdict(effect, threshold, "significant_up")
        if effect < -threshold:
            return Verdict(effect, threshold, "significant_down")
        return Verdict(effect, threshold, "noise",
                       "изменение в пределах погрешности метода")

    def manifest(self, threshold: float | None = None,
                 threshold_source: str | None = None) -> dict:
        """Описание прибора для манифеста городского пакета.

        Слой без манифеста в отчёт не попадает — это техническое воплощение
        правила «у любого числа виден источник».
        """
        return {
            "instrument": self.name,
            "measures": self.measures,
            "unit": self.unit,
            "source": self.source,
            "threshold": threshold,
            "threshold_source": threshold_source,
            "limits": list(self.limits),
        }


#: Реестр приборов. Заполняется при импорте модулей приборов.
REGISTRY: dict[str, Instrument] = {}


def register(instrument: Instrument) -> Instrument:
    """Зарегистрировать прибор под его именем."""
    if not instrument.name:
        raise ValueError("у прибора должно быть имя")
    if instrument.name in REGISTRY:
        raise ValueError(f"прибор {instrument.name!r} уже зарегистрирован")
    REGISTRY[instrument.name] = instrument
    return instrument
