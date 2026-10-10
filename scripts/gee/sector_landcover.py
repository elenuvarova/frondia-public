#!/usr/bin/env python3
"""
Классы Dynamic World по всем секторам города и по следам дел — одной таблицей.

Зачем
─────
Дело аудита сравнивает классы покрытия на следе работ с теми же 12 секторами,
что и NDVI. Для этого нужны изменения классов по всем секторам тех же окон:
из них вычитается контроль, и из них же строится нулевое распределение той
схемы подбора, что в деле, то есть порог — тем же прогоном.

Раньше калибровка Dynamic World (`calibrate_dynamic_world.py`) хранила только
пороги, и дело сравнивало СЫРОЕ изменение на следе с порогом, откалиброванным
на эффектах против контроля. Теперь хранится сама таблица: порог и эффект
пересчитываются без Earth Engine, а следующий прогон покажет дрейф числом.

Следы дел считаются в том же прогоне, что и секторы: след — это просто ещё
одна строка таблицы. Композит — как у прибора (`engine/instruments/vegetation.py`):
летние месяцы, среднее вероятностей класса, 10 м. Для каждого пикселя набор
снимков тот же, фильтр по рамке города или по следу его не меняет.

Запуск:
    .venv/bin/python scripts/gee/sector_landcover.py --project <id> --city brussels
    → data/<city>_sector_landcover_<окно>.csv (+ _meta.json: число сцен, дата прогона)
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

import ee

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.config import SUMMER_MONTHS, WINDOWS

# полоса Dynamic World → имя прибора (как в engine/instruments/vegetation.py)
CLASSES = {"built": "built", "trees": "trees", "grass": "grass", "bare": "bare", "shrub_and_scrub": "shrub"}
SECTORS = {"brussels": ("data/brussels_sectors.geojson", "id"),
           "antwerp": ("data/antwerp_sectors.geojson", "CD_SECTOR"),
           "ghent": ("data/ghent_sectors.geojson", "CD_SECTOR"),
           "liege": ("data/liege_sectors.geojson", "CD_SECTOR"),
           "charleroi": ("data/charleroi_sectors.geojson", "CD_SECTOR")}


def flat(geom: dict) -> dict:
    """Только долгота и широта: у секторов Антверпена в файле есть третья координата, а EE её не принимает."""
    def walk(c):
        return c[:2] if isinstance(c[0], (int, float)) else [walk(k) for k in c]
    return {"type": geom["type"], "coordinates": walk(geom["coordinates"])}


def composite(region: ee.Geometry, start: str, end: str) -> tuple[ee.Image, ee.Number]:
    coll = (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(region).filterDate(start, end)
            .filter(ee.Filter.calendarRange(SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
            .select(list(CLASSES)))
    return coll.mean(), coll.size()


def bbox(features: list[dict]) -> list[float]:
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0]); ys.append(c[1]); return
        for k in c: walk(k)
    for f in features: walk(f["geometry"]["coordinates"])
    return [min(xs) - 0.01, min(ys) - 0.01, max(xs) + 0.01, max(ys) + 0.01]


def case_footprints(city: str) -> list[dict]:
    """Следы дел этого города: полигон OSM из того же файла, что берёт audit_case.py.
    Нет файла парков — нет и дел: дело всегда указывает на полигон из него."""
    src = Path(f"data/perimeters/parks_{city}.geojson")
    if not src.exists():
        return []
    parks = {f["properties"]["osm"]: f for f in json.loads(src.read_text())["features"]}
    out = []
    for p in sorted(Path("data/registry/cases").glob("*.json")):
        osm = json.loads(p.read_text()).get("osm")
        if osm in parks:
            out.append({"type": "Feature", "geometry": parks[osm]["geometry"],
                        "properties": {"uid": f"osm:{osm}", "kind": "footprint"}})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Классы Dynamic World по секторам и следам дел")
    ap.add_argument("--project", required=True)
    ap.add_argument("--city", required=True, choices=sorted(SECTORS))
    ap.add_argument("--window", default="2017_2024")
    ap.add_argument("--chunk", type=int, default=100)
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    path, key = SECTORS[args.city]
    sectors = [{"type": "Feature", "geometry": f["geometry"],
                "properties": {"uid": str(f["properties"][key]), "kind": "sector"}}
               for f in json.loads(Path(path).read_text())["features"]]
    feats = sectors + case_footprints(args.city)
    region = ee.Geometry.Rectangle(bbox(sectors))
    w = WINDOWS[args.window]
    before, n_before = composite(region, *w["before"])
    after, n_after = composite(region, *w["after"])
    img = before.regexpRename("^", "b_").addBands(after.regexpRename("^", "a_"))
    print(f"{args.city}: {len(sectors)} секторов + {len(feats) - len(sectors)} следов, окно {w['label']}")

    rows = []
    for i in range(0, len(feats), args.chunk):
        part = feats[i:i + args.chunk]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry(flat(f["geometry"])), f["properties"]) for f in part])
        got = img.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=10, tileScale=4).getInfo()["features"]
        rows += [r["properties"] for r in got]
        print(f"  {min(i + args.chunk, len(feats))}/{len(feats)}")

    out = Path(f"data/{args.city}_sector_landcover_{args.window}.csv")
    cols = ["id", "kind"] + [f"{p}_{CLASSES[c]}" for c in CLASSES for p in ("b", "a")]
    with out.open("w", newline="") as fh:
        wr = csv.writer(fh); wr.writerow(cols)
        for r in rows:
            vals = []
            for c in CLASSES:
                for p in ("b", "a"):
                    v = r.get(f"{p}_{c}")
                    vals.append("" if v is None else f"{v:.6f}")
            wr.writerow([r["uid"], r["kind"]] + vals)
    meta = {"city": args.city, "window": w["label"], "run": dt.date.today().isoformat(),
            "scenes_before": n_before.getInfo(), "scenes_after": n_after.getInfo(),
            "composite": f"Dynamic World V1, months {SUMMER_MONTHS[0]}–{SUMMER_MONTHS[1]}, mean, 10 m",
            "rows": len(rows), "footprints": [r["uid"] for r in rows if r["kind"] == "footprint"]}
    out.with_name(out.stem + "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    empty = sum(1 for r in rows if r.get("b_built") is None or r.get("a_built") is None)
    print(f"→ {out}  ({len(rows)} строк, без значений {empty}; сцен {meta['scenes_before']} / {meta['scenes_after']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
