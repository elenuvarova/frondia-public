"""
Аудит одного следа вмешательства: связывает адаптер, приборы, контроль и манифест.

Что такое аудит здесь
─────────────────────
Не «посчитать число», а собрать всё, без чего число нельзя публиковать:
измерения двумя приборами, поимённый контроль, разрыв подбора, число сцен,
вердикт по измеренному порогу и границы применимости.

Порядок жёсткий и намеренный
────────────────────────────
1. След берётся ИЗВНЕ (полигон OSM, полигон коммуны или заранее
   зафиксированная обводка) — никогда не выводится из измерения, иначе граница
   подгоняется под результат.
2. Контроль подбирается по состоянию ДО вмешательства.
3. Проверяется разрыв: если сопоставимого контроля нет — отказ, а не число.
4. Только после этого считается эффект и сравнивается с порогом из манифеста.

Отказ на шаге 3 — полноценный исход, наравне с «значимо» и «шум».
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import CONTROL, MONITORING, QUALITY, WINDOWS
from .controls import ControlSet, difference_in_differences, gap_acceptable
from .instruments.base import Instrument, Reading, Verdict


@dataclass
class InstrumentResult:
    """Результат одного прибора по одному следу."""

    instrument: str
    measures: str
    unit: str
    before: Reading
    after: Reading
    effect: float | None
    verdict: Verdict

    @property
    def line(self) -> str:
        """Строка для отчёта: число всегда рядом с порогом."""
        if self.effect is None:
            return f"{self.instrument}: нет данных"
        thr = self.verdict.threshold
        thr_s = f"порог {thr:.4f}" if thr is not None else "порог не измерен"
        return (f"{self.instrument}: {self.effect:+.4f} {self.unit}, "
                f"{thr_s} → {self.verdict.outcome}")


@dataclass
class AuditResult:
    """Полный результат аудита. Всё, что нужно отчёту, и ничего лишнего."""

    footprint_id: str
    footprint_name: str
    area_ha: float
    window: str
    control: ControlSet | None
    results: dict[str, InstrumentResult] = field(default_factory=dict)
    refusal: str | None = None

    @property
    def claimable(self) -> bool:
        """Можно ли вообще что-то утверждать по этому аудиту."""
        return self.refusal is None and any(
            r.verdict.claimable for r in self.results.values())

    @property
    def significant(self) -> dict[str, InstrumentResult]:
        return {k: v for k, v in self.results.items()
                if v.verdict.outcome in ("significant_up", "significant_down")}

    def summary(self) -> str:
        """Человеческая сводка — то, что идёт в шапку отчёта."""
        if self.refusal:
            return f"{self.footprint_name}: отказ — {self.refusal}"
        sig = self.significant
        if not sig:
            return (f"{self.footprint_name}: изменений сверх порога нет "
                    f"(проверено приборов: {len(self.results)})")
        parts = [f"{k} {v.effect:+.3f}" for k, v in sig.items()]
        return f"{self.footprint_name}: {', '.join(parts)}"


def audit_footprint(footprint: dict,
                    pool: list[dict],
                    instruments: dict[str, Instrument],
                    thresholds: dict[str, float],
                    window: str | dict = "2017_2024",
                    baseline_instrument: str = "ndvi") -> AuditResult:
    """Провести аудит одного следа всеми переданными приборами.

    `pool` — единицы-кандидаты в контроль, каждая со своими базовыми значениями
    и сырыми дельтами по каждому прибору (ключи `<pribor>_before`, `<pribor>_delta`).

    `window` — либо ключ из `WINDOWS`, либо свой словарь `{before, after, label}`.
    Окна ПОД ПРОЕКТ важнее, чем кажется: при одном общем окне из 153 проектов
    Beliris по срокам проходили 5, при подобранных — 13, и среди них Porte de
    Ninove, сильнейший кейс города. Общее окно было ограничением инструмента,
    а не свойством данных.
    """
    w = WINDOWS[window] if isinstance(window, str) else window
    res = AuditResult(
        footprint_id=footprint["id"],
        footprint_name=footprint.get("name") or footprint["id"],
        area_ha=footprint.get("area_ha", 0.0),
        window=w["label"],
        control=None,
    )

    if footprint.get("area_ha", 0) < 1.0:
        res.refusal = ("след меньше 1 га: единицы пикселей Sentinel-2, "
                       "этим инструментом не измеряется")
        return res
    if footprint.get("in_city") is False:
        res.refusal = "след вне города: контроль подбирается из чужих единиц"
        return res

    # Сроки работ обязаны укладываться МЕЖДУ окнами. Иначе измеряется либо
    # стройка, либо период, когда не происходило ничего. Ошибка, стоившая двух
    # неверных выводов: восемь проектов Beliris закончились в 2011–2016, то есть
    # до начала окна «до», а Quai des Matériaux — летом 2024, внутри окна «после».
    completed = footprint.get("completed_year")
    if completed is not None:
        before_end = int(w["before"][1][:4])
        after_start = int(w["after"][0][:4])
        if completed <= before_end:
            res.refusal = (f"работы завершены в {completed}, до конца окна «до» "
                           f"({before_end}): оба окна после проекта, мерить нечего")
            return res
        if completed >= after_start:
            res.refusal = (f"работы завершены в {completed}, внутри окна «после» "
                           f"(с {after_start}): измерялась бы стройка")
            return res

    if baseline_instrument not in instruments:
        res.refusal = (f"опорный прибор {baseline_instrument!r} не передан: "
                       "без него не подобрать контроль")
        return res

    geom = footprint["geometry"]
    base = instruments[baseline_instrument]

    # 1. Состояние объекта ДО и ПОСЛЕ по опорному прибору
    site_before = base.measure(geom, *w["before"])
    site_after = base.measure(geom, *w["after"])
    if not site_before.usable or not site_after.usable:
        res.refusal = "нет валидных измерений в одном из окон"
        return res
    if (site_before.n_scenes or 0) < QUALITY["min_scenes"]:
        res.refusal = (f"сцен в окне «до» {site_before.n_scenes}, нужно "
                       f"{QUALITY['min_scenes']}: медиана шумная")
        return res

    # 2. Контроль по состоянию ДО
    from .controls import match
    ctrl = match(
        site_baseline=site_before.value,
        site_secondary=footprint.get("secondary_before", site_before.value),
        site_centroid=footprint["centroid"],
        pool=pool,
        baseline_key=f"{baseline_instrument}_before",
        secondary_key=footprint.get("secondary_key", f"{baseline_instrument}_before"),
        delta_key=f"{baseline_instrument}_delta",
    )
    res.control = ctrl

    # 3. Разрыв подбора — до всякого счёта эффекта
    if not gap_acceptable(ctrl, CONTROL["max_gap_ndvi"]):
        gap = f"{ctrl.gap:+.4f}" if ctrl else "контроль не собран"
        res.refusal = (f"сопоставимого контроля нет (разрыв {gap}, предел "
                       f"{CONTROL['max_gap_ndvi']}): объект на краю шкалы")
        return res

    # 4. Эффект по каждому прибору
    for name, inst in instruments.items():
        b = site_before if name == baseline_instrument else inst.measure(geom, *w["before"])
        a = site_after if name == baseline_instrument else inst.measure(geom, *w["after"])
        c = ctrl if name == baseline_instrument else _control_for(ctrl, name)
        eff = difference_in_differences(b.value, a.value, c)
        res.results[name] = InstrumentResult(
            instrument=name, measures=inst.measures, unit=inst.unit,
            before=b, after=a, effect=eff,
            verdict=inst.judge(eff, thresholds.get(name), ctrl.gap,
                               CONTROL["max_gap_ndvi"]),
        )
    return res


def _control_for(ctrl: ControlSet | None, instrument: str) -> ControlSet | None:
    """Тот же контроль, но со средней дельтой нужного прибора.

    Контроль подбирается ОДИН РАЗ по опорному прибору и переиспользуется всеми
    остальными — иначе приборы считались бы по разным наборам и их результаты
    нельзя было бы сравнивать между собой.
    """
    if ctrl is None:
        return None
    key = f"{instrument}_delta"
    members = [m for m in ctrl.members if key in m]
    if not members:
        return None
    import statistics
    return ControlSet(
        members=ctrl.members,
        baseline_mean=ctrl.baseline_mean,
        delta_mean=statistics.mean(m[key] for m in members),
        gap=ctrl.gap,
    )


def windows_for_completion(completed_year: int,
                           before_years: int = 3,
                           min_before_years: int = 2,
                           settle_years: int = 2,
                           after_years: int = 4,
                           data_from: int = 2017,
                           data_to: int = 2025) -> dict | None:
    """Построить окна под конкретный проект по году сдачи.

    Окно «до» кончается за год до сдачи, окно «после» начинается через
    `settle_years` — молодым посадкам нужно прижиться, а стройплощадке уйти
    из кадра.

    Окно «до» СЖИМАЕТСЯ, если упирается в начало данных, но не короче
    `min_before_years`. Это не мелочь: при жёстких трёх годах Porte de Ninove
    (сдан 2019) выпадал, хотя два года 2017–2018 у него есть и результат на них
    устойчив. Число лет печатается в label, чтобы читатель видел, на чём
    посчитано.

    Возвращает None, когда данных не хватает даже на сжатое окно.
    """
    b_end = completed_year - 1
    a_start = completed_year + settle_years
    a_end = min(a_start + after_years - 1, data_to)
    if a_end - a_start < 1:
        return None

    for years in range(before_years, min_before_years - 1, -1):
        b_start = b_end - years + 1
        if b_start >= data_from:
            note = "" if years == before_years else f", окно «до» сжато до {years} лет"
            return {
                "before": (f"{b_start}-01-01", f"{b_end}-12-31"),
                "after": (f"{a_start}-01-01", f"{a_end}-12-31"),
                "label": f"{b_start}–{b_end} → {a_start}–{a_end}{note}",
                "before_years": years,
            }
    return None


# Порог различимости прибора по размеру следа. На 30 м объект в 3 га — 11–30
# пикселей, и вердикт Landsat там не измерение, а видимость: так вышло с
# Droogdokkenpark (1,58 га, «мелкий для 30 м»), так же ошибались 4 из 4 значимых
# в аудите Beliris ≤ 2016.
MIN_HA_LANDSAT = 3.0


def instrument_for(completed_year: int, area_ha: float,
                   min_before_years: int = 2) -> tuple[str, dict, str] | None:
    """Выбрать прибор и окна под объект: не только по году, но и по размеру.

    Правило года само по себе неверно. Sentinel-2 идёт с 2017-го, поэтому проект,
    сданный в 2018-м, не оставляет двух лет на окно «до» — и правило «нет ряда →
    Landsat» переключает прибор на 30 м. Для парка в 1,6 га это подмена измерения
    видимостью: у Droogdokkenpark так получился вердикт «мелкий для 30 м» при
    том, что Sentinel-2 с базой одного 2016 года даёт защитимые +0,147.

    Поэтому для следа мельче `MIN_HA_LANDSAT` Sentinel-2 имеет приоритет: окно
    «до» сжимается до одного года, а короткая база объявляется оговоркой —
    вызывающий обязан напечатать её рядом с числом.

    Возвращает (прибор, окна, оговорка) либо None, если окна нет ни у кого.
    """
    w = windows_for_completion(completed_year, min_before_years=min_before_years)
    if w:
        return "ndvi", w, ""
    if area_ha < MIN_HA_LANDSAT:
        w1 = windows_for_completion(completed_year, min_before_years=1)
        if w1:
            return ("ndvi", w1,
                    f"след {area_ha:.1f} га мельче {MIN_HA_LANDSAT:.0f} га — Landsat 30 м даёт "
                    f"единицы пикселей; взят Sentinel-2 с окном «до» в "
                    f"{w1['before_years']} год, число сцен печатать рядом с эффектом")
    wl = windows_for_completion(completed_year, min_before_years=min_before_years, data_from=2000)
    if wl:
        caveat = ("" if area_ha >= MIN_HA_LANDSAT else
                  f"след {area_ha:.1f} га на 30 м — вердикт предварительный")
        return "ndvi_landsat", wl, caveat
    return None


def annual_windows(season_year: int,
                   baseline_years: int | None = None,
                   data_from: int = 2017) -> dict | None:
    """Окна для мониторинга вперёд: скользящая база против одного сезона.

    Отличие от аудита вмешательства: здесь нет проекта и нет даты сдачи —
    вопрос «что изменилось в этом сезоне против последних лет». База — три
    предыдущих лета, «после» — текущее. Порог тот же, из манифеста: нулевое
    распределение метода не зависит от того, ищем мы эффект или потерю.

    Возвращает None, если базе не хватает лет Sentinel-2.
    """
    by = baseline_years or MONITORING["baseline_years"]
    b_end = season_year - 1 - MONITORING["gap_years"]
    b_start = b_end - by + 1
    if b_start < data_from:
        return None
    return {
        "before": (f"{b_start}-01-01", f"{b_end}-12-31"),
        "after": (f"{season_year}-01-01", f"{season_year}-12-31"),
        "label": f"{b_start}–{b_end} → сезон {season_year}",
        "mode": "monitoring",
    }


def audit_preregistered(dossier,
                        after_site: dict[str, Reading],
                        control_before: dict[str, float],
                        control_after: dict[str, float],
                        instruments: dict[str, Instrument],
                        thresholds: dict[str, float],
                        after_window: dict,
                        works_end_year: int | None) -> AuditResult:
    """Аудит записи, зафиксированной ДО работ.

    Отличие от `audit_footprint`: ничего из «до» здесь не измеряется и не
    подбирается. База «до» — из `preregistered_baseline.csv`, контроль — из
    `preregistered_controls.json`, оба привязаны к хешу геометрии. Аудитор
    приносит только измерения «после»: по следу (`after_site`) и по названным
    контрольным секторам за оба окна (`control_before`, `control_after` — средние
    по прибору; окно «до» у контроля то же фиксированное, что у базы).

    Отказы — те же, что в ретро-аудите, плюс два собственных:
    контроль признан несопоставимым до работ; база «до» захватывает работы.
    """
    rec = dossier.record
    res = AuditResult(footprint_id=rec.id, footprint_name=rec.name, area_ha=0.0,
                      window=after_window.get("label", ""), control=None)

    problems = dossier.validate()
    if problems:
        res.refusal = "досье не защитимо: " + "; ".join(problems)
        return res
    if not dossier.baseline:
        res.refusal = "база «до» не снята до работ: аудит без предрегистрации"
        return res
    if dossier.control is None or not dossier.control.get("comparable"):
        gap = dossier.control.get("gap") if dossier.control else None
        gap_s = f"{gap:+.4f}" if gap is not None else "не подобран"
        res.refusal = (f"контроль признан несопоставимым до работ (разрыв {gap_s}, "
                       f"зафиксировано {rec.registered_at}): аудит без вердикта")
        return res

    base_window = next(iter(dossier.baseline.values()))["window"]
    base_end = int(base_window[5:9]) if "–" in base_window else int(base_window[:4])
    if rec.works_start and int(rec.works_start[:4]) <= base_end:
        res.refusal = (f"база «до» ({base_window}) захватывает начало работ "
                       f"{rec.works_start}: снимать базу надо было раньше")
        return res
    if works_end_year is None:
        res.refusal = "срок сдачи неизвестен: окно «после» нельзя назначить"
        return res
    after_start = int(after_window["after"][0][:4])
    if works_end_year >= after_start:
        res.refusal = (f"работы завершены в {works_end_year}, не раньше окна «после» "
                       f"({after_start}): измерялась бы стройка")
        return res

    gap = dossier.control["gap"]
    for name, inst in instruments.items():
        b = dossier.baseline.get(name)
        a = after_site.get(name)
        if b is None or b["value"] is None or a is None or not a.usable \
                or name not in control_before or name not in control_after:
            res.results[name] = InstrumentResult(
                instrument=name, measures=inst.measures, unit=inst.unit,
                before=Reading(None), after=a or Reading(None), effect=None,
                verdict=inst.judge(None, thresholds.get(name)))
            continue
        eff = (a.value - b["value"]) - (control_after[name] - control_before[name])
        res.results[name] = InstrumentResult(
            instrument=name, measures=inst.measures, unit=inst.unit,
            before=Reading(b["value"], b.get("scenes")), after=a, effect=eff,
            verdict=inst.judge(eff, thresholds.get(name), gap, CONTROL["max_gap_ndvi"]))
    return res
