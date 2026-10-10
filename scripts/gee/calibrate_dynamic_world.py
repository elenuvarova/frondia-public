#!/usr/bin/env python3
"""
Калибровка Dynamic World: нулевые распределения и пороги значимости.

Зачем
─────
Второй прибор без калибровки — это красивые числа без права называть их
значимыми. NDVI прошёл эту процедуру (`placebo_band.py`) и получил порог 0,0373.
Здесь то же самое для классов Dynamic World.

Метод тот же: каждый из 686 секторов по очереди играет роль «вмешательства»,
ему подбираются 12 контрольных секторов, считается разность разностей.
Распределение этих эффектов = нулевое распределение метода для данного класса.

ВАЖНО про подбор контроля
─────────────────────────
Контроль подбирается по ТЕМ ЖЕ признакам, что и для NDVI (исходные NDVI и LST
из `sector_change_2017_2024.csv`). Это сделано намеренно: контрольные наборы
получаются идентичными для обоих приборов, поэтому их результаты сравнимы между
собой. Разные приборы, одни и те же контроли, одна и та же арифметика.

Запуск:
    .venv/bin/python scripts/gee/calibrate_dynamic_world.py --project <id>
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path

import ee

SECTORS_GEO = Path("data/brussels_sectors.geojson")
SECTORS_TABLE = Path("data/sector_change_2017_2024.csv")
OUT = Path("data/dw_calibration.json")

BEFORE = ("2017-01-01", "2019-12-31")
AFTER = ("2021-01-01", "2024-12-31")
SUMMER = (6, 8)
CLASSES = ["trees", "grass", "shrub_and_scrub", "built", "bare"]

N_CONTROLS = 12
EXCLUSION_M = 1500


def dw_composite(geom: ee.Geometry, start: str, end: str) -> ee.Image:
    return (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
            .filterBounds(geom).filterDate(start, end)
            .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], "month"))
            .select(CLASSES).mean())


def dist_m(a, b):
    k = math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * k * 111320, (a[1] - b[1]) * 110540)


def percentile(xs, p):
    xs = sorted(xs)
    i = (len(xs) - 1) * p / 100
    lo, hi = math.floor(i), math.ceil(i)
    return xs[lo] if lo == hi else xs[lo] * (hi - i) + xs[hi] * (i - lo)


def main() -> int:
    ap = argparse.ArgumentParser(description="Калибровка Dynamic World")
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    # признаки для подбора — те же, что у NDVI, чтобы контроли совпадали
    table = {r["id"]: r for r in csv.DictReader(SECTORS_TABLE.open())}
    for r in table.values():
        r["ndvi_before"] = float(r["ndvi_before"])
        r["lst_before"] = float(r["lst_before"])
        r["c"] = (float(r["lon"]), float(r["lat"]))

    feats = [f for f in json.loads(SECTORS_GEO.read_text())["features"]
             if f["properties"]["id"] in table]
    print(f"секторов в расчёте: {len(feats)}")

    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f["geometry"]), {"id": f["properties"]["id"]})
        for f in feats
    ])

    bxl = ee.Geometry.Rectangle([4.23, 50.76, 4.50, 50.94])
    before = dw_composite(bxl, *BEFORE).regexpRename("^", "b_")
    after = dw_composite(bxl, *AFTER).regexpRename("^", "a_")

    print("один прогон Earth Engine по всем секторам…")
    rows = (before.addBands(after)
            .reduceRegions(fc, ee.Reducer.mean(), 10).getInfo()["features"])

    data = []
    for r in rows:
        p = r["properties"]
        t = table.get(p["id"])
        if not t:
            continue
        if any(p.get(f"b_{c}") is None or p.get(f"a_{c}") is None for c in CLASSES):
            continue
        rec = {"id": p["id"], "c": t["c"],
               "ndvi_before": t["ndvi_before"], "lst_before": t["lst_before"]}
        for c in CLASSES:
            rec[f"d_{c}"] = p[f"a_{c}"] - p[f"b_{c}"]
        data.append(rec)

    print(f"секторов с полными данными: {len(data)}\n")

    n_rng = max(d["ndvi_before"] for d in data) - min(d["ndvi_before"] for d in data)
    l_rng = max(d["lst_before"] for d in data) - min(d["lst_before"] for d in data)

    effects: dict[str, list[float]] = {c: [] for c in CLASSES}
    for t in data:
        pool = [o for o in data
                if o["id"] != t["id"] and dist_m(t["c"], o["c"]) >= EXCLUSION_M]
        if len(pool) < N_CONTROLS:
            continue
        pool.sort(key=lambda o: math.hypot(
            (o["ndvi_before"] - t["ndvi_before"]) / n_rng,
            (o["lst_before"] - t["lst_before"]) / l_rng))
        ctrl = pool[:N_CONTROLS]
        for c in CLASSES:
            effects[c].append(t[f"d_{c}"] - statistics.mean(o[f"d_{c}"] for o in ctrl))

    print(f"{'класс':<18}{'среднее':>10}{'ст.откл.':>10}{'порог 95%':>12}")
    print("-" * 50)
    result = {}
    for c in CLASSES:
        xs = effects[c]
        thr = max(abs(percentile(xs, 2.5)), abs(percentile(xs, 97.5)))
        mean = statistics.mean(xs)
        result[c] = {"n": len(xs), "mean": round(mean, 5),
                     "sd": round(statistics.stdev(xs), 5), "threshold": round(thr, 5)}
        flag = "" if abs(mean) < 0.002 else "  ⚠ смещён"
        print(f"{c:<18}{mean:>+10.5f}{statistics.stdev(xs):>10.5f}{thr:>12.5f}{flag}")

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    print(f"\n→ {OUT}")

    print("\n──────── Приложение к измеренному ────────")
    for name, vals in (
        ("Porte de Ninove", {"built": -0.127, "grass": +0.099, "trees": +0.007}),
        ("Quai des Matériaux", {"built": -0.042, "bare": +0.022, "trees": -0.001}),
        ("Parc de Haren", {"built": -0.042, "trees": +0.030, "grass": +0.011}),
    ):
        print(f"\n  {name}")
        for c, v in vals.items():
            thr = result[c]["threshold"]
            verdict = "ЗНАЧИМО" if abs(v) > thr else "в пределах шума"
            print(f"    {c:<10}{v:>+8.3f}   порог {thr:.3f}   {verdict}")

    print("\n  Среднее нулевого распределения около нуля = прибор не смещён.")
    print("  Отличие от нуля означает системную ошибку подбора для этого класса.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
