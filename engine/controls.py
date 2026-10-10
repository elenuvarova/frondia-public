"""
Подбор контрольной группы и разность разностей.

Зачем контроль вообще
─────────────────────
За 2017–2024 позеленел ВЕСЬ Брюссель: медиана изменения NDVI по городу +0,043
при пороге значимости 0,037. Без поправки на контроль «значимым» оказался бы
почти каждый сектор. Разность разностей вычитает общегородской сдвиг:

    эффект = (объект_после − объект_до) − (контроль_после − контроль_до)

Почему подобранные секторы, а не кольцо вокруг
──────────────────────────────────────────────
Кольцо 300–1200 м вокруг Tour et Taxis остыло СИЛЬНЕЕ объекта — весь квартал
перестраивался в тот же период, то есть кольцо было забито чужими
вмешательствами. Смена контроля на подобранные секторы перевернула знак
теплового эффекта. Соседство не гарантирует сопоставимости.

Известный дефект, ради которого существует проверка разрыва
───────────────────────────────────────────────────────────
Подбор по ближайшему соседу ломается на краях шкалы: r(исходный NDVI, разрыв
с контролем) = +0,512. Самому зелёному объекту не из чего подобрать такой же
зелёный контроль, ему достаются места бледнее, и регрессия к среднему рисует
ложный эффект. Поэтому разрыв считается всегда, и при превышении предела
вердикт НЕ выносится. На пакетном прогоне 152 парков это отсекло 46 из 112 —
41 %, ровно как предсказывала диагностика.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from .adapters.base import dist_m
from .config import CONTROL


@dataclass(frozen=True)
class ControlSet:
    """Подобранный контроль с характеристиками, которые обязаны быть в отчёте."""

    members: list[dict]           # сами единицы: id, name, базовые значения
    baseline_mean: float          # среднее исходное значение контроля
    delta_mean: float             # среднее сырое изменение контроля
    gap: float                    # разрыв: объект минус контроль по базовому

    @property
    def names(self) -> list[str]:
        """Поимённо — требование прослеживаемости: любой может пересчитать."""
        return [m.get("name") or m.get("id", "?") for m in self.members]


def match(site_baseline: float,
          site_secondary: float,
          site_centroid: tuple[float, float],
          pool: list[dict],
          baseline_key: str,
          secondary_key: str,
          delta_key: str,
          n: int | None = None,
          exclusion_m: float | None = None,
          ranges: tuple[float, float] | None = None) -> ControlSet | None:
    """Подобрать контроль по двум признакам состояния ДО вмешательства.

    Два признака, а не один: похожесть только по зелёности пустила бы в контроль
    места с другим тепловым режимом. Обе оси нормируются по размаху, иначе
    градусы задавили бы единицы индекса.

    `ranges` — размах (baseline, secondary) по ВСЕМУ городу, посчитанный один раз.
    Без него размах берётся по кандидатам после исключения соседей — у каждой
    единицы свой, и 70 из 686 секторов расходились с калибровкой в 4-м знаке.
    Один город — одна нормировка.
    """
    n = n or CONTROL["n_controls"]
    exclusion_m = exclusion_m if exclusion_m is not None else CONTROL["exclusion_m"]

    # Исключаем близкие: риск попасть в ту же стройку, что и объект.
    candidates = [c for c in pool
                  if dist_m(site_centroid, c["centroid"]) >= exclusion_m]
    if len(candidates) < n:
        return None

    if ranges:
        b_range, s_range = (ranges[0] or 1.0), (ranges[1] or 1.0)
    else:
        b_range = (max(c[baseline_key] for c in candidates)
                   - min(c[baseline_key] for c in candidates)) or 1.0
        s_range = (max(c[secondary_key] for c in candidates)
                   - min(c[secondary_key] for c in candidates)) or 1.0

    candidates.sort(key=lambda c: math.hypot(
        (c[baseline_key] - site_baseline) / b_range,
        (c[secondary_key] - site_secondary) / s_range))
    chosen = candidates[:n]

    baseline_mean = statistics.mean(c[baseline_key] for c in chosen)
    return ControlSet(
        members=chosen,
        baseline_mean=baseline_mean,
        delta_mean=statistics.mean(c[delta_key] for c in chosen),
        gap=site_baseline - baseline_mean,
    )


def difference_in_differences(site_before: float | None,
                              site_after: float | None,
                              control: ControlSet | None) -> float | None:
    """Эффект = изменение объекта минус изменение контроля."""
    if site_before is None or site_after is None or control is None:
        return None
    return (site_after - site_before) - control.delta_mean


def gap_acceptable(control: ControlSet | None,
                   max_gap: float | None = None) -> bool:
    """Сопоставим ли контроль. Отказ считать — полноценный исход, не сбой."""
    if control is None:
        return False
    limit = max_gap if max_gap is not None else CONTROL["max_gap_ndvi"]
    return abs(control.gap) <= limit


def match_all(units: list[dict],
              baseline_key: str,
              secondary_key: str,
              delta_keys: list[str],
              n: int | None = None,
              exclusion_m: float | None = None,
              max_gap: float | None = None) -> list[dict]:
    """Каждой единице — свой контроль, ОДИН на все приборы.

    Возвращает копии единиц с полями `<delta>_eff` для каждого ключа, `gap`,
    `comparable` и `control_ids`. Контроль подбирается один раз по опорному
    признаку и переиспользуется всеми приборами — иначе приборы считались бы
    по разным наборам и их нельзя было бы сравнивать между собой.

    Единственная реализация подбора для калибровки, аудита, мониторинга и
    отчётов. Раньше их было шесть, и любая правка порога расходилась по файлам.
    """
    n = n or CONTROL["n_controls"]
    exclusion_m = exclusion_m if exclusion_m is not None else CONTROL["exclusion_m"]
    max_gap = max_gap if max_gap is not None else CONTROL["max_gap_ndvi"]
    pool = [u for u in units
            if u.get(baseline_key) is not None and u.get(secondary_key) is not None]
    # Одна нормировка на весь город — как в калибровке, иначе порог и эффекты
    # считались бы в разных метриках.
    ranges = (max(u[baseline_key] for u in pool) - min(u[baseline_key] for u in pool),
              max(u[secondary_key] for u in pool) - min(u[secondary_key] for u in pool))
    out = []
    for t in pool:
        cs = match(t[baseline_key], t[secondary_key], t["centroid"],
                   [o for o in pool if o is not t],
                   baseline_key, secondary_key, delta_keys[0], n, exclusion_m, ranges)
        row = dict(t)
        if cs is None:
            row.update({"gap": None, "comparable": False, "control_ids": []})
            for k in delta_keys:
                row[k + "_eff"] = None
        else:
            row["gap"] = cs.gap
            row["comparable"] = abs(cs.gap) <= max_gap
            row["control_ids"] = [m.get("id") for m in cs.members]
            for k in delta_keys:
                vals = [m[k] for m in cs.members if m.get(k) is not None]
                row[k + "_eff"] = ((t[k] - statistics.mean(vals))
                                   if (t.get(k) is not None and vals) else None)
        out.append(row)
    return out
