"""
Адаптер Брюсселя.

Единицы — статистические секторы Statbel (724 штуки), общий ключ соединения
всех проектов: `EPSG:31370`, REFNIS. Следы вмешательств — именованные парки OSM
от 1 га.

Почему точка-в-полигоне, а не bbox
──────────────────────────────────
Первый пакетный прогон взял парки по bbox и получил 40 объектов из Фламандского
Брабанта (Dilbeek, Sint-Pieters-Leeuw, Vilvoorde), которые сравнивались с
брюссельским контролем. Здесь принадлежность городу проверяется попаданием
в любой сектор, а не в прямоугольник.
"""

from __future__ import annotations

from pathlib import Path

from .base import CityAdapter, Unit, area_ha_of, centroid_of

SECTORS = Path("data/brussels_sectors.geojson")
PARKS = Path("data/perimeters/parks_brussels.geojson")
INCOME = Path("data/brussels_income.csv")   # Statbel, медианный облагаемый доход, 2023

# REFNIS Брюссельского столичного региона. Сверено по пяти известным секторам:
# Peterbos → 21001, Parvis Saint-Roch → 21004, Karreveld → 21012,
# Coghen → 21016, Gare du Nord → 21015.
REFNIS = {
    "21001": "Anderlecht", "21002": "Auderghem", "21003": "Berchem-Sainte-Agathe",
    "21004": "Bruxelles", "21005": "Etterbeek", "21006": "Evere",
    "21007": "Forest", "21008": "Ganshoren", "21009": "Ixelles",
    "21010": "Jette", "21011": "Koekelberg", "21012": "Molenbeek",
    "21013": "Saint-Gilles", "21014": "Saint-Josse", "21015": "Schaerbeek",
    "21016": "Uccle", "21017": "Watermael-Boitsfort",
    "21018": "Woluwe-Saint-Lambert", "21019": "Woluwe-Saint-Pierre",
}

MIN_FOOTPRINT_HA = 1.0     # ниже — единицы пикселей Sentinel-2, не измеряется


def _point_in_ring(pt: tuple[float, float], ring: list) -> bool:
    x, y = pt
    inside = False
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside


class BrusselsAdapter(CityAdapter):
    def __init__(self):
        super().__init__("brussels", 31370, (4.23, 50.76, 4.50, 50.94))
        self._units: list[Unit] | None = None
        self._rings: list[tuple] | None = None

    def units(self) -> list[Unit]:
        if self._units is not None:
            return self._units
        out = []
        for f in self._load_geojson(SECTORS):
            p = f["properties"]
            geom = f["geometry"]
            out.append(Unit(
                id=p["id"],
                name=p.get("name_fr") or p.get("name_nl") or "",
                geometry=geom,
                area_ha=p.get("area_ha") or area_ha_of(geom),
                population=p.get("population") or 0,
                centroid=(p.get("centroid_lon"), p.get("centroid_lat"))
                if p.get("centroid_lon") else centroid_of(geom),
                commune=REFNIS.get(p.get("cd_munty_refnis"), "?"),
            ))
        self._units = out
        return out

    def income(self) -> dict[str, float]:
        """Медианный облагаемый доход по сектору, Statbel 2023.

        Заменяет плотность как прокси депривации в формуле справедливости:
        «поставили там, где нужнее?» теперь считается по доходу, а не по
        приближению. Файл извлечён из кэша spot-finder (TF_PSNL_INC_TAX_SECTOR).
        """
        import csv
        if not INCOME.exists():
            return {}
        out = {}
        for r in csv.DictReader(INCOME.open()):
            try:
                out[r["id"]] = float(r["median_income"])
            except (TypeError, ValueError):
                continue
        return out

    def footprints(self) -> list[dict]:
        """Именованные парки OSM от 1 га — ступень 1 источника следа.

        Геометрия ЧУЖАЯ: её рисовало сообщество OSM, она названа и версионирована.
        Это снимает возражение «вы сами обвели там, где позеленело».
        """
        out = []
        for f in self._load_geojson(PARKS):
            p = f["properties"]
            ha = p.get("area_ha") or area_ha_of(f["geometry"])
            if ha < MIN_FOOTPRINT_HA:
                continue
            c = centroid_of(f["geometry"])
            out.append({
                "id": p["osm"],
                "name": p.get("name", ""),
                "geometry": f["geometry"],
                "area_ha": ha,
                "centroid": c,
                "source": "OSM leisure=park, именованный",
                "in_city": self.in_city_precise(c),
            })
        return out

    def in_city_precise(self, point: tuple[float, float]) -> bool:
        """Попадание в любой сектор — надёжнее прямоугольника."""
        if self._rings is None:
            rings = []
            for u in self.units():
                g = u.geometry
                for r in ([g["coordinates"][0]] if g["type"] == "Polygon"
                          else [poly[0] for poly in g["coordinates"]]):
                    xs = [q[0] for q in r]
                    ys = [q[1] for q in r]
                    rings.append((min(xs), min(ys), max(xs), max(ys), r))
            self._rings = rings
        lon, lat = point
        for x0, y0, x1, y1, r in self._rings:
            if x0 <= lon <= x1 and y0 <= lat <= y1 and _point_in_ring(point, r):
                return True
        return False
