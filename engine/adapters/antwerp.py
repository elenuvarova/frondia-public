"""
Адаптер Антверпена — второй город, принят 2026-09-02.

Почему именно он
────────────────
Обязанность по ст. 8 регламента 2024/1991 кусает во Фландрии: Антверпен слаб по
норме 3-30-300, исключение «> 45 % зелени» ему не светит, ответственное
ведомство — Agentschap Natuur en Bos. Брюссель — витрина, Антверпен — покупатель
с юридическим рычагом.

Откуда данные
─────────────
Секторы Statbel уже собраны в `spot-finder-geo/pipeline/data/antwerpen_statbel_sectors.geojson`
(458 секторов, WGS84) и — в отличие от брюссельского файла — несут `MEAN_INCOME`.
Копия лежит в `data/antwerp_sectors.geojson`. Названий секторов там нет; они и
районы — в `data/antwerp_sector_names.csv` из реестра Statbel
(`scripts/registry/antwerp_sector_names.py`). Без этого файла `Unit.name` = код.

Что обязательно заново
──────────────────────
Калибровка всех семи приборов. Порог — свойство пары (город, прибор); брюссельские
0,0373 и 0,0325 к Антверпену неприменимы по построению. Следы работ — парки OSM
≥ 1 га по антверпенскому bbox, отдельный прогон `fetch_park_perimeters.py`.
"""

from __future__ import annotations

from pathlib import Path

from .base import CityAdapter, Unit, area_ha_of, centroid_of

SECTORS = Path("data/antwerp_sectors.geojson")
NAMES = Path("data/antwerp_sector_names.csv")
INCOME = Path("data/antwerp_income.csv")   # Statbel, медианный облагаемый доход, 2023
PARKS = Path("data/perimeters/parks_antwerp.geojson")
MIN_FOOTPRINT_HA = 1.0


def _names(path: Path = NAMES) -> dict[str, dict]:
    if not path.exists():
        return {}
    import csv
    with path.open() as fh:
        return {r["id"]: r for r in csv.DictReader(fh)}


def _strip_z(geom: dict) -> dict:
    """Statbel-экспорт несёт третью координату 0.0 — GEE и хеши её не любят."""
    def rings(coords):
        return [[[p[0], p[1]] for p in ring] for ring in coords]
    if geom["type"] == "Polygon":
        return {"type": "Polygon", "coordinates": rings(geom["coordinates"])}
    if geom["type"] == "MultiPolygon":
        return {"type": "MultiPolygon",
                "coordinates": [rings(poly) for poly in geom["coordinates"]]}
    return geom


def _point_in_ring(pt, ring) -> bool:
    x, y = pt
    inside = False
    for i in range(len(ring) - 1):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[i + 1][0], ring[i + 1][1]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside


class AntwerpAdapter(CityAdapter):
    # the files and the default district as attributes, so a Flemish city built the same way (Ghent)
    # only names its own
    SLUG, BBOX = "antwerp", (4.22, 51.14, 4.53, 51.38)
    SECTORS, NAMES, INCOME, PARKS = SECTORS, NAMES, INCOME, PARKS
    DEFAULT_DISTRICT = "Antwerpen"

    def __init__(self):
        super().__init__(self.SLUG, 31370, self.BBOX)
        self._units: list[Unit] | None = None
        self._rings: list[tuple] | None = None

    def units(self) -> list[Unit]:
        if self._units is not None:
            return self._units
        out = []
        names = _names(self.NAMES)
        for f in self._load_geojson(self.SECTORS):
            p = f["properties"]
            geom = _strip_z(f["geometry"])
            sid = p.get("CD_SECTOR") or p.get("cd_sector") or ""
            n = names.get(sid, {})
            out.append(Unit(
                id=sid,
                name=n.get("name_nl") or p.get("TX_SECTOR_DESCR_NL") or sid,
                geometry=geom,
                area_ha=area_ha_of(geom),
                population=int(p.get("POPULATION") or 0),
                centroid=centroid_of(geom),
                commune=n.get("district") or self.DEFAULT_DISTRICT,
            ))
        self._units = out
        return out

    def income(self) -> dict[str, float]:
        """Медианный облагаемый доход по сектору, Statbel 2023 — та же величина, что в Брюсселе.

        До 25.09.2026 здесь был СРЕДНИЙ доход (`MEAN_INCOME` из файла spot-finder), и терцили
        двух городов считались по разным величинам. Медиана — из `data/antwerp_income.csv`
        (`scripts/registry/statbel_income.py`); среднее той же таблицы совпадает с
        `MEAN_INCOME` во всех 380 секторах, то есть источник и год те же. Без файла —
        прежнее среднее, чтобы старые прогоны оставались воспроизводимыми.
        """
        if self.INCOME.exists():
            import csv
            with self.INCOME.open() as fh:
                return {r["id"]: float(r["median_income"]) for r in csv.DictReader(fh) if r["median_income"]}
        return {u.id: float(p.get("MEAN_INCOME") or 0)
                for u, p in zip(self.units(),
                                (f["properties"] for f in self._load_geojson(self.SECTORS)))
                if p.get("MEAN_INCOME") is not None}

    def footprints(self) -> list[dict]:
        if not self.PARKS.exists():
            return []
        out = []
        for f in self._load_geojson(self.PARKS):
            p = f["properties"]
            ha = p.get("area_ha") or area_ha_of(f["geometry"])
            if ha < MIN_FOOTPRINT_HA:
                continue
            c = centroid_of(f["geometry"])
            out.append({
                "id": p["osm"], "name": p.get("name", ""),
                "geometry": f["geometry"], "area_ha": ha, "centroid": c,
                "source": "OSM leisure=park, именованный",
                "in_city": self.in_city_precise(c),
            })
        return out

    def in_city_precise(self, point) -> bool:
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
        return any(x0 <= lon <= x1 and y0 <= lat <= y1 and _point_in_ring(point, r)
                   for x0, y0, x1, y1, r in self._rings)
