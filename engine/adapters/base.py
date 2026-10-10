"""
Абстрактный адаптер города.

Интерфейс повторяет `public_realm_planner_multicity/engine/adapters/base.py`,
чтобы адаптеры могли переезжать между проектами. Отличие: там город отдаёт
границу и объекты для размещения, здесь — ЕДИНИЦЫ РЕШЕНИЯ, по которым считается
изменение и подбирается контроль.

Каждый город обязан отдать:
  units()      → список единиц с геометрией, населением, площадью
  boundary()   → внешняя граница города (для отсечения чужих объектов)
  footprints() → полигоны следов вмешательств, пригодные для аудита

Единица — не абстракция ради абстракции. Она несёт население и идентификатор,
без которых досье не досье: «затронуто N жителей» и ссылку на источник.
"""

from __future__ import annotations

import json
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Unit:
    """Единица решения и отчёта: статистический сектор или его аналог."""

    id: str
    name: str
    geometry: dict            # GeoJSON
    area_ha: float
    population: int
    centroid: tuple[float, float]   # lon, lat
    commune: str = ""

    @property
    def density(self) -> float:
        """Человек на гектар. Приближение депривации, не доход."""
        return self.population / self.area_ha if self.area_ha else 0.0


def centroid_of(geom: dict) -> tuple[float, float]:
    """Центроид по вершинам внешнего кольца — дёшево и достаточно для подбора."""
    c = geom["coordinates"]
    while isinstance(c[0][0], list):
        c = c[0]
    return sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)


def area_ha_of(geom: dict) -> float:
    """Площадь в гектарах, равнопромежуточное приближение."""
    rings = ([geom["coordinates"][0]] if geom["type"] == "Polygon"
             else [poly[0] for poly in geom["coordinates"]])
    total = 0.0
    for ring in rings:
        if len(ring) < 4:
            continue
        lat0 = sum(p[1] for p in ring) / len(ring)
        k = math.cos(math.radians(lat0))
        s = 0.0
        for i in range(len(ring) - 1):
            x1, y1 = ring[i][0] * k * 111320, ring[i][1] * 110540
            x2, y2 = ring[i + 1][0] * k * 111320, ring[i + 1][1] * 110540
            s += x1 * y2 - x2 * y1
        total += abs(s) / 2
    return total / 10000


def dist_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    k = math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * k * 111320, (a[1] - b[1]) * 110540)


class CityAdapter(ABC):
    """Базовый адаптер. Подклассы знают, откуда брать единицы для своего города."""

    def __init__(self, city_key: str, crs: int, bbox: tuple[float, float, float, float]):
        self.city_key = city_key
        self.crs = crs
        self.bbox = bbox

    @abstractmethod
    def units(self) -> list[Unit]:
        """Единицы решения с населением и геометрией."""

    @abstractmethod
    def footprints(self) -> list[dict]:
        """Полигоны следов вмешательств, пригодные для аудита.

        Источник следа НИКОГДА не определяется измерением — иначе граница
        подгоняется под результат. Порядок ступеней: полигон OSM ≥ 1 га →
        полигон от коммуны → обводка вручную с публикацией раньше числа →
        отказ «защитимого следа нет».
        """

    def in_city(self, point: tuple[float, float]) -> bool:
        """Лежит ли точка внутри города.

        Нужно потому, что bbox шире региона: в первом прогоне 40 из 152 парков
        оказались во Фламандском Брабанте и сравнивались с брюссельским контролем.
        """
        lon, lat = point
        return (self.bbox[0] <= lon <= self.bbox[2]
                and self.bbox[1] <= lat <= self.bbox[3])

    @staticmethod
    def _load_geojson(path: str | Path) -> list[dict]:
        return json.loads(Path(path).read_text())["features"]
