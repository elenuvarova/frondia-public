"""
Приборы на снимках Sentinel-2: зелёность (NDVI) и классы покрытия (Dynamic World).

Оба откалиброваны на Брюсселе по нулевому распределению 686 секторов, оба
оказались несмещёнными. Пороги лежат в пакете города, а не здесь.

Почему два прибора, а не один
─────────────────────────────
NDVI меряет ЗЕЛЁНОСТЬ и не отличает молодое дерево от травы, а запечатанность
не видит вовсе. Dynamic World даёт по тем же снимкам классы покрытия. Два
независимых прибора, сказавших одно, — довод сильно тяжелее одного числа:
Porte de Ninove подтверждён обоими (NDVI +0,25 и built −0,127).

И они ловят разное. Quai des Matériaux по NDVI выглядел как «молодые посадки
вместо травы», а Dynamic World показал `trees` без движения при `bare` вверх:
покрытие раскрыли, но не засадили. Один прибор такое различить не может.
"""

from __future__ import annotations

import ee

from .base import Instrument, Reading, register
from ..config import QUALITY, SUMMER_MONTHS


def _summer(coll: ee.ImageCollection, start: str, end: str) -> ee.ImageCollection:
    return (coll.filterDate(start, end)
            .filter(ee.Filter.calendarRange(SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month")))


class NDVI(Instrument):
    name = "ndvi"
    measures = "зелёность растительности"
    unit = "ед. NDVI"
    source = ("Sentinel-2 SR Harmonized, летние медианы, маска облаков "
              "Cloud Score+ (cs_cdf ≥ 0,6)")
    limits = (
        "меряет зелёность, а не древесную крону: молодая посадка на лугу читается "
        "как ПОТЕРЯ",
        "реставрация парка не меняет зелёность и остаётся невидимой",
    )

    def _collection(self, geom, start: str, end: str) -> ee.ImageCollection:
        cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")

        def to_ndvi(img):
            clear = img.select("cs_cdf").gte(QUALITY["cloud_score_plus_min"])
            return (img.normalizedDifference(["B8", "B4"]).rename("ndvi")
                    .updateMask(clear))

        base = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(geom)
        return (_summer(base, start, end)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", QUALITY["max_cloud_pct"]))
                .linkCollection(cs, ["cs_cdf"]).map(to_ndvi))

    def measure(self, geom, start: str, end: str) -> Reading:
        coll = self._collection(geom, start, end)
        val = coll.median().reduceRegion(
            ee.Reducer.mean(), geom, scale=10,
            maxPixels=int(1e9), bestEffort=True).get("ndvi")
        value, n = ee.List([val, coll.size()]).getInfo()
        note = None
        if n is not None and n < QUALITY["min_scenes"]:
            note = f"сцен {n} — меньше {QUALITY['min_scenes']}, медиана шумная"
        return Reading(value, n, note)


class LandCoverClass(Instrument):
    """Один класс покрытия Dynamic World.

    ⚠️ Значение — СРЕДНЯЯ ВЕРОЯТНОСТЬ класса, а не доля площади. `built` 0,55
    в парке не означает «55 % запечатано»: на 10 м в смешанной застройке
    классификатор не уверен. Годится как относительный сигнал, абсолютные
    значения интерпретировать нельзя.
    """

    unit = "вероятность класса"
    source = "Dynamic World V1 по Sentinel-2, летние средние, 10 м"
    limits = (
        "средняя вероятность класса, НЕ доля площади: абсолютные значения "
        "не интерпретировать",
    )

    def __init__(self, band: str, name: str, measures: str):
        self.band = band
        self.name = name
        self.measures = measures

    def measure(self, geom, start: str, end: str) -> Reading:
        base = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(geom)
        coll = _summer(base, start, end).select(self.band)
        val = coll.mean().reduceRegion(
            ee.Reducer.mean(), geom, scale=10,
            maxPixels=int(1e9), bestEffort=True).get(self.band)
        value, n = ee.List([val, coll.size()]).getInfo()
        return Reading(value, n)


# ── реестр ────────────────────────────────────────────────────────────────────

register(NDVI())
register(LandCoverClass("built", "built", "запечатанность и застройка"))
register(LandCoverClass("trees", "trees", "древесная крона"))
register(LandCoverClass("grass", "grass", "травяной покров"))
register(LandCoverClass("bare", "bare", "голая поверхность"))
register(LandCoverClass("shrub_and_scrub", "shrub", "кустарник"))
