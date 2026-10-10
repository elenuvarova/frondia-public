#!/usr/bin/env python3
"""
Полоса шума метода: плацебо на случайных секторах.

Идея
────
Каждый из 724 статистических секторов Брюсселя по очереди притворяется
«вмешательством»: ему подбираются 12 похожих контрольных секторов и считается
разность разностей. Подавляющее большинство секторов ничем не «вмешивались»,
поэтому распределение полученных эффектов — это НУЛЕВОЕ распределение метода.

Из него берётся порог: эффект настоящего вмешательства должен выходить за
95-й процентиль шума, иначе заявлять нечего.

Оптимизация: характеристики всех секторов «до» и «после» считаются одним
запросом к Earth Engine, дальше вся статистика — локально и мгновенно.

Запуск:
    .venv/bin/python scripts/gee/placebo_band.py --project <id>
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys

import ee

SECTORS_PATH = "data/brussels_sectors.geojson"

BEFORE = {"start": "2017-01-01", "end": "2019-12-31"}
AFTER = {"start": "2021-01-01", "end": "2024-12-31"}
SUMMER = (6, 8)
MAX_CLOUD = 30

N_CONTROLS = 12
EXCLUSION_M = 1500
MIN_AREA_HA = 4.0        # мелкие секторы шумные — как и в аудите
NDVI_SCALE = 30
LST_SCALE = 100


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


def centroid(geom):
    coords = geom["coordinates"]
    while isinstance(coords[0][0], list):
        coords = coords[0]
    return (sum(c[0] for c in coords) / len(coords),
            sum(c[1] for c in coords) / len(coords))


def dist_m(a, b):
    k = math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * k * 111320, (a[1] - b[1]) * 110540)


def percentile(xs, p):
    xs = sorted(xs)
    i = (len(xs) - 1) * p / 100
    lo, hi = math.floor(i), math.ceil(i)
    return xs[lo] if lo == hi else xs[lo] * (hi - i) + xs[hi] * (i - lo)


def main() -> int:
    ap = argparse.ArgumentParser(description="Нулевое распределение метода")
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    ee.Initialize(project=args.project)

    bxl = ee.Geometry.Rectangle([4.23, 50.76, 4.50, 50.94])
    gj = json.load(open(SECTORS_PATH))
    feats = gj["features"]

    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f["geometry"]), {"id": f["properties"]["id"]})
        for f in feats
    ])

    print(f"Считаю NDVI и LST до/после по {len(feats)} секторам — один прогон…")

    ndvi = (s2_ndvi(bxl, BEFORE).rename("nb")
            .addBands(s2_ndvi(bxl, AFTER).rename("na")))
    lst = (landsat_lst(bxl, BEFORE).rename("lb")
           .addBands(landsat_lst(bxl, AFTER).rename("la")))

    ndvi_rows = ndvi.reduceRegions(fc, ee.Reducer.mean(), NDVI_SCALE).getInfo()["features"]
    lst_rows = lst.reduceRegions(fc, ee.Reducer.mean(), LST_SCALE).getInfo()["features"]

    lst_by_id = {r["properties"]["id"]: r["properties"] for r in lst_rows}
    meta = {f["properties"]["id"]: f["properties"] for f in feats}
    geom_by_id = {f["properties"]["id"]: f["geometry"] for f in feats}

    # Собираем таблицу
    table = []
    for r in ndvi_rows:
        p = r["properties"]
        sid = p["id"]
        l = lst_by_id.get(sid, {})
        m = meta[sid]
        if None in (p.get("nb"), p.get("na"), l.get("lb"), l.get("la")):
            continue
        if m.get("area_ha", 0) < MIN_AREA_HA:
            continue
        table.append({
            "id": sid,
            "name": m.get("name_fr") or m.get("name_nl") or "",
            "area_ha": m["area_ha"],
            "nb": p["nb"], "na": p["na"],
            "lb": l["lb"], "la": l["la"],
            "d_ndvi": p["na"] - p["nb"],
            "d_lst": l["la"] - l["lb"],
            "c": centroid(geom_by_id[sid]),
        })

    print(f"Секторов с полными данными и площадью ≥ {MIN_AREA_HA} га: {len(table)}\n")

    # Нормировки для подбора
    nbs = [t["nb"] for t in table]
    lbs = [t["lb"] for t in table]
    n_rng = (max(nbs) - min(nbs)) or 1
    l_rng = (max(lbs) - min(lbs)) or 1

    ndvi_effects, lst_effects, scored = [], [], []
    for t in table:
        pool = [
            o for o in table
            if o["id"] != t["id"] and dist_m(t["c"], o["c"]) >= EXCLUSION_M
        ]
        if len(pool) < N_CONTROLS:
            continue
        pool.sort(key=lambda o: math.hypot((o["nb"] - t["nb"]) / n_rng,
                                           (o["lb"] - t["lb"]) / l_rng))
        ctrl = pool[:N_CONTROLS]
        ne = t["d_ndvi"] - statistics.mean(o["d_ndvi"] for o in ctrl)
        le = t["d_lst"] - statistics.mean(o["d_lst"] for o in ctrl)
        ndvi_effects.append(ne)
        lst_effects.append(le)
        scored.append({
            "id": t["id"], "name": t["name"], "area_ha": round(t["area_ha"], 1),
            "ndvi_effect": round(ne, 4), "lst_effect": round(le, 3),
            # базовые значения и сырые дельты — без них нельзя отличить
            # настоящий эффект от артефакта подбора контроля
            "ndvi_before": round(t["nb"], 4), "ndvi_after": round(t["na"], 4),
            "lst_before": round(t["lb"], 2), "lst_after": round(t["la"], 2),
            "d_ndvi_raw": round(t["d_ndvi"], 4), "d_lst_raw": round(t["d_lst"], 3),
            # каким оказался контроль: если он систематически зеленее или бледнее
            # объекта, сравнение смещено
            "ctrl_ndvi_before": round(statistics.mean(o["nb"] for o in ctrl), 4),
            "ctrl_lst_before": round(statistics.mean(o["lb"] for o in ctrl), 2),
            "ctrl_d_ndvi": round(statistics.mean(o["d_ndvi"] for o in ctrl), 4),
            "ctrl_match_gap": round(t["nb"] - statistics.mean(o["nb"] for o in ctrl), 4),
            "lon": round(t["c"][0], 5), "lat": round(t["c"][1], 5)})

    def report(name, xs, unit):
        print(f"──────── Нулевое распределение · {name} ────────")
        print(f"  секторов в выборке: {len(xs)}")
        print(f"  среднее:            {statistics.mean(xs):+.4f} {unit}")
        print(f"  ст. отклонение:     {statistics.stdev(xs):.4f} {unit}")
        for p in (5, 25, 50, 75, 95, 99):
            print(f"  {p:>3}-й процентиль:   {percentile(xs, p):+.4f} {unit}")
        thr = max(abs(percentile(xs, 2.5)), abs(percentile(xs, 97.5)))
        print(f"  ⇒ порог значимости (95 %): |эффект| > {thr:.4f} {unit}\n")
        return thr

    n_thr = report("NDVI", ndvi_effects, "ед.")
    l_thr = report("Температура", lst_effects, "°C")

    # Хвосты: где на самом деле что-то произошло
    ranked = sorted(scored, key=lambda r: r["ndvi_effect"], reverse=True)
    above = [r for r in ranked if r["ndvi_effect"] > n_thr]
    below = [r for r in ranked if r["ndvi_effect"] < -n_thr]

    print(f"──────── Секторы выше порога: ПОЗЕЛЕНЕЛИ ({len(above)}) ────────")
    for r in above[:15]:
        print(f"  {r['id']:<12} {r['name'][:26]:<26} "
              f"{r['ndvi_effect']:+.4f}   {r['area_ha']:.0f} га")

    print(f"\n──────── Секторы ниже порога: ОБЛЫСЕЛИ ({len(below)}) ────────")
    for r in below[:10]:
        print(f"  {r['id']:<12} {r['name'][:26]:<26} "
              f"{r['ndvi_effect']:+.4f}   {r['area_ha']:.0f} га")

    import csv
    with open("data/sector_change_2017_2024.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "id", "name", "area_ha", "ndvi_effect", "lst_effect",
            "ndvi_before", "ndvi_after", "lst_before", "lst_after",
            "d_ndvi_raw", "d_lst_raw",
            "ctrl_ndvi_before", "ctrl_lst_before", "ctrl_d_ndvi", "ctrl_match_gap",
            "lon", "lat"])
        w.writeheader()
        for r in ranked:
            w.writerow({k: r[k] for k in w.fieldnames})
    print(f"\nВсе {len(ranked)} секторов → data/sector_change_2017_2024.csv")

    print("──────── Приложение к измеренному ────────")
    print(f"  Tour et Taxis, NDVI +0.044  →  "
          f"{'ЗНАЧИМО' if 0.044 > n_thr else 'в пределах шума'} (порог {n_thr:.3f})")
    print(f"  Tour et Taxis, LST  −0.235  →  "
          f"{'ЗНАЧИМО' if 0.235 > l_thr else 'в пределах шума'} (порог {l_thr:.3f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
