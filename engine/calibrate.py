"""
Калибровка прибора: нулевое распределение и порог значимости.

Идея
────
Каждая единица города по очереди играет роль «вмешательства»: ей подбирается
контроль по обычным правилам и считается разность разностей. Подавляющее
большинство единиц ничем не «вмешивались», поэтому распределение полученных
эффектов — это НУЛЕВОЕ распределение метода для данного прибора в данном городе.

Порог берётся из хвостов: эффект настоящего вмешательства должен выйти за
95-й процентиль шума, иначе заявлять нечего.

Что проверяет средним
─────────────────────
Среднее нулевого распределения обязано быть около нуля. Отличие означает, что
схема подбора систематически смещена, и тогда порог считать бессмысленно —
сначала чинить подбор. На Брюсселе оба прибора прошли: NDVI −0,0000,
классы Dynamic World от +0,00001 до −0,00019.

Почему это не разовая проверка, а часть продукта
───────────────────────────────────────────────
Порог — свойство пары (город, прибор). Новый город обязан пройти калибровку
заново: у него другой состав застройки, другая динамика и другой шум.
Прибор без калибровки считать умеет, называть результат значимым — нет.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from .config import CONTROL


@dataclass(frozen=True)
class Calibration:
    """Результат калибровки одного прибора в одном городе."""

    instrument: str
    n: int
    mean: float
    sd: float
    threshold: float
    percentiles: dict[int, float]

    @property
    def unbiased(self) -> bool:
        """Не смещён ли прибор. Порог при смещении считать нельзя."""
        return abs(self.mean) < 0.1 * self.sd

    @property
    def source_line(self) -> str:
        """Строка происхождения порога для манифеста — обязательное поле."""
        return (f"нулевое распределение по {self.n} единицам, 95-й процентиль, "
                f"среднее {self.mean:+.5f}, ст. отклонение {self.sd:.5f}")

    def describe(self) -> str:
        flag = "" if self.unbiased else "  ⚠ СМЕЩЁН, порог недействителен"
        return (f"{self.instrument:<18}среднее {self.mean:+.5f}   "
                f"ст.откл. {self.sd:.5f}   порог {self.threshold:.5f}{flag}")


def percentile(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    i = (len(xs) - 1) * p / 100
    lo, hi = math.floor(i), math.ceil(i)
    return xs[lo] if lo == hi else xs[lo] * (hi - i) + xs[hi] * (i - lo)


def calibrate(units: list[dict],
              instrument: str,
              baseline_key: str,
              secondary_key: str,
              n_controls: int | None = None,
              exclusion_m: float | None = None) -> Calibration:
    """Посчитать нулевое распределение прибора по единицам города.

    `units` — единицы с полями `<baseline_key>`, `<secondary_key>`,
    `<instrument>_delta` и `centroid`. Контроль подбирается ТЕМИ ЖЕ правилами,
    что в аудите, иначе порог не соответствовал бы измерению.
    """
    from .controls import match_all
    delta_key = f"{instrument}_delta"
    scored = match_all(units, baseline_key, secondary_key, [delta_key],
                       n=n_controls, exclusion_m=exclusion_m)
    return from_effects(instrument,
                        [r[delta_key + "_eff"] for r in scored if r[delta_key + "_eff"] is not None])


def from_effects(instrument: str, effects: list[float]) -> Calibration:
    """Порог из уже посчитанных эффектов: каждая единица сыграла «вмешательство» против своего
    контроля, и эти эффекты И ЕСТЬ нулевое распределение. Так слой, хранящий эффекты прибора
    против того же контроля, калибрует его без повторного подбора — тем же прогоном."""
    if len(effects) < 30:
        raise ValueError(f"единиц для калибровки слишком мало: {len(effects)}")

    return Calibration(
        instrument=instrument,
        n=len(effects),
        mean=statistics.mean(effects),
        sd=statistics.stdev(effects),
        threshold=max(abs(percentile(effects, 2.5)), abs(percentile(effects, 97.5))),
        percentiles={p: percentile(effects, p) for p in (5, 25, 50, 75, 95)},
    )
