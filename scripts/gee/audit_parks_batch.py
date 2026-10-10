#!/usr/bin/env python3
"""
Пакетный аудит всех пригодных парков Брюсселя.

Что считает
───────────
Для каждого парка из `data/perimeters/parks_brussels.geojson` — изменение
растительности 2017–2019 → 2021–2024 относительно 12 подобранных контрольных
секторов (разность разностей), с вердиктом по калиброванному порогу 0,0373.

Защита от смещения подбора — обязательна здесь
──────────────────────────────────────────────
Диагностика (`diagnose_green_decline.py`) показала: подбор по ближайшему соседу
ломается на краях шкалы зелёности, r(NDVI до, разрыв с контролем) = +0,512.
Парки как класс зелёные, то есть сидят в верхних децилях — ровно там, где
контроля подходящего нет и объект тянет к центру.

Поэтому для каждого парка считается РАЗРЫВ между его исходным NDVI и средним
исходным NDVI его контроля. Если разрыв больше MAX_GAP, вердикт не выносится:
печатается «контроль несопоставим». Это ступень 4 из решения о следе
вмешательства — отказ считать является результатом, а не сбоем.

ВАЖНО о смысле результата
─────────────────────────
Это НЕ аудит вмешательств: большинство парков ни во что не вмешивались. Это
детектор изменений по пригодным объектам. Значимые попадания — КАНДИДАТЫ,
которые дальше проверяются по реестру документов. Без документа причина
изменения неизвестна (урок Zavelenberg).

Запуск:
    .venv/bin/python scripts/gee/audit_parks_batch.py --project <id>
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from pathlib import Path

import ee

PARKS = Path("data/perimeters/parks_brussels.geojson")
SECTORS_TABLE = Path("data/sector_change_2017_2024.csv")
OUT = Path("data/park_audit_2017_2024.csv")

BEFORE = {"start": "2017-01-01", "end": "2019-12-31"}
AFTER = {"start": "2021-01-01", "end": "2024-12-31"}
SUMMER = (6, 8)
MAX_CLOUD = 30

NDVI_THRESHOLD = 0.0373     # калиброванный порог значимости
N_CONTROLS = 12
EXCLUSION_M = 1500          # ближе — риск попасть в ту же стройку
MAX_GAP = 0.04              # предел несопоставимости контроля по NDVI «до»


def s2_ndvi(geom, rng):
    cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")

    def f(img):
        return (img.normalizedDifference(["B8", "B4"]).rename("ndvi")
                .updateMask(img.select("cs_cdf").gte(0.6)))

    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geom).filterDate(rng["start"], rng["end"])
            .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], "month"))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD))
            .linkCollection(cs, ["cs_cdf"]).map(f).median())


def landsat_lst(geom, rng):
    def f(img):
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        return (img.select("ST_B10").multiply(0.00341802).add(149.0)
                .subtract(273.15).rename("lst").updateMask(clear))

    l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
    return (l8.merge(l9).filterBounds(geom)
            .filterDate(rng["start"], rng["end"])
            .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], "month"))
            .filter(ee.Filter.lt("CLOUD_COVER", MAX_CLOUD))
            .map(f).median())


def centroid(geom: dict) -> tuple[float, float]:
    c = geom["coordinates"]
    while isinstance(c[0][0], list):
        c = c[0]
    return sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)


def dist_m(a, b):
    k = math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * k * 111320, (a[1] - b[1]) * 110540)


def main() -> int:
    ap = argparse.ArgumentParser(description="Пакетный аудит парков")
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    parks = json.loads(PARKS.read_text())["features"]
    print(f"парков к расчёту: {len(parks)}")

    sectors = list(csv.DictReader(SECTORS_TABLE.open()))
    for s in sectors:
        for k in ("ndvi_before", "lst_before", "d_ndvi_raw", "d_lst_raw"):
            s[k] = float(s[k])
        s["c"] = (float(s["lon"]), float(s["lat"]))
    print(f"контрольный пул: {len(sectors)} секторов")

    bxl = ee.Geometry.Rectangle([4.23, 50.76, 4.50, 50.94])
    stack = (s2_ndvi(bxl, BEFORE).rename("nb")
             .addBands(s2_ndvi(bxl, AFTER).rename("na"))
             .addBands(landsat_lst(bxl, BEFORE).rename("lb"))
             .addBands(landsat_lst(bxl, AFTER).rename("la")))

    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f["geometry"]), {"osm": f["properties"]["osm"]})
        for f in parks
    ])

    print("один прогон Earth Engine по всем парсам…")
    rows = stack.reduceRegions(fc, ee.Reducer.mean(), 10).getInfo()["features"]
    meta = {f["properties"]["osm"]: f for f in parks}

    n_rng = max(s["ndvi_before"] for s in sectors) - min(s["ndvi_before"] for s in sectors)
    l_rng = max(s["lst_before"] for s in sectors) - min(s["lst_before"] for s in sectors)

    results = []
    for r in rows:
        p = r["properties"]
        f = meta.get(p["osm"])
        if not f or None in (p.get("nb"), p.get("na"), p.get("lb"), p.get("la")):
            continue

        c = centroid(f["geometry"])
        pool = [s for s in sectors if dist_m(c, s["c"]) >= EXCLUSION_M]
        if len(pool) < N_CONTROLS:
            continue
        pool.sort(key=lambda s: math.hypot((s["ndvi_before"] - p["nb"]) / n_rng,
                                           (s["lst_before"] - p["lb"]) / l_rng))
        ctrl = pool[:N_CONTROLS]

        ctrl_nb = statistics.mean(s["ndvi_before"] for s in ctrl)
        gap = p["nb"] - ctrl_nb
        eff_ndvi = (p["na"] - p["nb"]) - statistics.mean(s["d_ndvi_raw"] for s in ctrl)
        eff_lst = (p["la"] - p["lb"]) - statistics.mean(s["d_lst_raw"] for s in ctrl)

        if abs(gap) > MAX_GAP:
            verdict = "контроль несопоставим"
        elif eff_ndvi > NDVI_THRESHOLD:
            verdict = "ПОЗЕЛЕНЕЛ"
        elif eff_ndvi < -NDVI_THRESHOLD:
            verdict = "ПОТЕРЯЛ"
        else:
            verdict = "шум"

        results.append({
            "osm": p["osm"],
            "name": f["properties"]["name"],
            "area_ha": f["properties"]["area_ha"],
            "ndvi_before": round(p["nb"], 4),
            "ndvi_effect": round(eff_ndvi, 4),
            "lst_effect": round(eff_lst, 3),
            "ctrl_gap": round(gap, 4),
            "verdict": verdict,
        })

    results.sort(key=lambda r: -r["ndvi_effect"])
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    counts: dict[str, int] = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    print(f"\nпосчитано парков: {len(results)}  →  {OUT}")
    print("вердикты:", ", ".join(f"{k}: {v}" for k, v in
                                 sorted(counts.items(), key=lambda x: -x[1])))

    usable = [r for r in results if r["verdict"] != "контроль несопоставим"]
    print(f"\n──────── Значимо позеленели ────────")
    for r in [x for x in usable if x["verdict"] == "ПОЗЕЛЕНЕЛ"][:15]:
        print(f"  {r['ndvi_effect']:+.4f}  {r['area_ha']:>6.1f} га  "
              f"{r['name'][:44]:<44} разрыв {r['ctrl_gap']:+.3f}")

    print(f"\n──────── Значимо потеряли ────────")
    for r in [x for x in usable if x["verdict"] == "ПОТЕРЯЛ"][-10:]:
        print(f"  {r['ndvi_effect']:+.4f}  {r['area_ha']:>6.1f} га  "
              f"{r['name'][:44]:<44} разрыв {r['ctrl_gap']:+.3f}")

    print("\n⚠️  Это детектор изменений, а не аудит вмешательств: большинство парков")
    print("    ни во что не вмешивались. Значимые попадания — КАНДИДАТЫ, которые")
    print("    дальше проверяются по реестру документов (урок Zavelenberg).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
