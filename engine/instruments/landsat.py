"""
Прибор на Landsat: зелёность с 1984 года ценой разрешения.

Зачем нужен
───────────
Sentinel-2 надёжен с 2017 года, и из-за этого 80 из 153 завершённых проектов
Beliris невозможно проверить: их работы закончились раньше, чем появились
снимки на окно «до». Landsat закрывает период с 1984 года.

Чем платим
──────────
30 метров вместо 10. Пиксель Landsat — это 900 м² против 100 м² у Sentinel-2,
то есть объект в 1 га это 11 пикселей вместо 100. Значит:

  · порог значимости будет ВЫШЕ — шум на грубой сетке больше;
  · нижняя граница по площади поднимется, вероятно до 3–5 га;
  · края объекта сильнее смешиваются с окружением.

Поэтому это ОТДЕЛЬНЫЙ прибор со своей калибровкой, а не «тот же NDVI, но
из другого источника». Порог Sentinel-2 (0,0373) к нему неприменим, и
подставить его было бы прямым подлогом.

Два поколения спутников
───────────────────────
L8/L9 несут NIR в `SR_B5`, красный в `SR_B4`; L4/L5/L7 — в `SR_B4` и `SR_B3`.
Коэффициенты Collection 2 Level-2 одинаковы: значение × 0,0000275 − 0,2.
"""

from __future__ import annotations

import ee

from .base import Instrument, Reading, register
from ..config import QUALITY, SUMMER_MONTHS

# Collection 2 Level-2, официальные коэффициенты отражения
SCALE, OFFSET = 0.0000275, -0.2

MODERN = ("LANDSAT/LC08/C02/T1_L2", "LANDSAT/LC09/C02/T1_L2")   # NIR=B5, Red=B4
LEGACY = ("LANDSAT/LT05/C02/T1_L2", "LANDSAT/LE07/C02/T1_L2")   # NIR=B4, Red=B3


def _prep(img: ee.Image, nir: str, red: str) -> ee.Image:
    """Маска облаков по QA_PIXEL и NDVI из масштабированных каналов."""
    qa = img.select("QA_PIXEL")
    clear = (qa.bitwiseAnd(1 << 3).eq(0)      # облако
             .And(qa.bitwiseAnd(1 << 4).eq(0))  # тень облака
             .And(qa.bitwiseAnd(1 << 1).eq(0)))  # расширенное облако
    n = img.select(nir).multiply(SCALE).add(OFFSET)
    r = img.select(red).multiply(SCALE).add(OFFSET)
    return (n.subtract(r).divide(n.add(r)).rename("ndvi")
            .updateMask(clear)
            .copyProperties(img, ["system:time_start"]))


class LandsatNDVI(Instrument):
    name = "ndvi_landsat"
    measures = "зелёность растительности (грубая сетка, длинный ряд)"
    unit = "ед. NDVI"
    source = ("Landsat 5/7/8/9 Collection 2 Level-2, летние медианы, "
              "маска облаков по QA_PIXEL, 30 м")
    limits = (
        "30 м на пиксель: объект в 1 га — это 11 пикселей, нижняя граница "
        "площади выше, чем у Sentinel-2",
        "порог значимости СВОЙ и выше сентинелевского: подставлять 0,0373 нельзя",
        "меряет зелёность, а не крону — как и NDVI на Sentinel-2",
    )

    def _collection(self, geom, start: str, end: str) -> ee.ImageCollection:
        modern = ee.ImageCollection(MODERN[0]).merge(ee.ImageCollection(MODERN[1]))
        legacy = ee.ImageCollection(LEGACY[0]).merge(ee.ImageCollection(LEGACY[1]))

        def window(c):
            return (c.filterBounds(geom).filterDate(start, end)
                    .filter(ee.Filter.calendarRange(
                        SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
                    .filter(ee.Filter.lt("CLOUD_COVER", QUALITY["max_cloud_pct"])))

        return (window(modern).map(lambda i: _prep(i, "SR_B5", "SR_B4"))
                .merge(window(legacy).map(lambda i: _prep(i, "SR_B4", "SR_B3"))))

    def measure(self, geom, start: str, end: str) -> Reading:
        coll = self._collection(geom, start, end)
        val = coll.median().reduceRegion(
            ee.Reducer.mean(), geom, scale=30,
            maxPixels=int(1e9), bestEffort=True).get("ndvi")
        value, n = ee.List([val, coll.size()]).getInfo()
        note = None
        if n is not None and n < QUALITY["min_scenes"]:
            note = f"сцен {n} — меньше {QUALITY['min_scenes']}, медиана шумная"
        return Reading(value, n, note)


register(LandsatNDVI())
