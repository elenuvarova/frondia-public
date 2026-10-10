#!/usr/bin/env python3
"""
Пакетный аудит парков любого города из config.CITIES.

Порог — из манифеста города, пул контроля — из таблицы секторов, которую пишет
calibrate_city.py. Защита от смещения подбора (разрыв > MAX_GAP → отказ) та же,
что в Брюсселе: там она отсекла 41 % парков, и без неё вердикты врали бы.

Это детектор изменений, не аудит вмешательств: значимые попадания — кандидаты,
которые проверяются по реестру документов.

Запуск:
    .venv/bin/python scripts/gee/audit_parks_city.py --project <id> --city antwerp
"""
from __future__ import annotations
import argparse, csv, json, math, statistics, sys
from collections import Counter
from pathlib import Path
import ee
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS, dist_m
from engine.config import CITIES, CONTROL, QUALITY, SUMMER_MONTHS, WINDOWS
from engine.manifest import Manifest


def s2_ndvi(geom, start, end):
    cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    def f(img):
        return (img.normalizedDifference(["B8", "B4"]).rename("ndvi")
                .updateMask(img.select("cs_cdf").gte(QUALITY["cloud_score_plus_min"])))
    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geom).filterDate(start, end)
            .filter(ee.Filter.calendarRange(SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", QUALITY["max_cloud_pct"]))
            .linkCollection(cs, ["cs_cdf"]).map(f).median())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--city", choices=list(CITIES), required=True)
    ap.add_argument("--window", default="2017_2024")
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    w = WINDOWS[args.window]; cfg = CITIES[args.city]
    thr = Manifest.read(args.city).layers["ndvi"].threshold
    parks = [f for f in ADAPTERS[args.city]().footprints() if f["in_city"]]
    pool = []
    for r in csv.DictReader(Path(f"data/{args.city}_sector_change_{args.window}.csv").open()):
        pool.append({"id": r["id"], "nb": float(r["ndvi_before"]),
                     "d": float(r["d_ndvi_raw"]), "c": (float(r["lon"]), float(r["lat"]))})
    print(f"{cfg['display_name']}: парков в городе {len(parks)}, пул контроля {len(pool)}, порог {thr}")

    x0, y0, x1, y1 = cfg["bbox"]
    box = ee.Geometry.Rectangle([x0, y0, x1, y1])
    stack = (s2_ndvi(box, *w["before"]).rename("nb").addBands(s2_ndvi(box, *w["after"]).rename("na")))
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"]), {"id": f["id"]}) for f in parks])
    print("один прогон Earth Engine по паркам…")
    rows = stack.reduceRegions(fc, ee.Reducer.mean(), 10).getInfo()["features"]

    meta = {f["id"]: f for f in parks}
    from engine.controls import match, difference_in_differences
    # одна нормировка по всему пулу — как в калибровке
    ranges = (max(o["nb"] for o in pool) - min(o["nb"] for o in pool),) * 2
    ctrl_pool = [{"id": o["id"], "nb": o["nb"], "d": o["d"], "centroid": o["c"]} for o in pool]
    out = []
    for r in rows:
        p = r["properties"]; f = meta.get(p["id"])
        if not f or p.get("nb") is None or p.get("na") is None: continue
        cs = match(p["nb"], p["nb"], f["centroid"], ctrl_pool, "nb", "nb", "d", ranges=ranges)
        if cs is None: continue
        gap = cs.gap
        eff = difference_in_differences(p["nb"], p["na"], cs)
        if abs(gap) > CONTROL["max_gap_ndvi"]: v = "контроль несопоставим"
        elif eff > thr: v = "ПОЗЕЛЕНЕЛ"
        elif eff < -thr: v = "ПОТЕРЯЛ"
        else: v = "шум"
        out.append({"osm": f["id"], "name": f["name"], "area_ha": f["area_ha"],
                    "ndvi_before": round(p["nb"], 4), "ndvi_effect": round(eff, 4),
                    "ctrl_gap": round(gap, 4), "verdict": v})
    out.sort(key=lambda r: -r["ndvi_effect"])

    # ── Второй прибор для значимых: NDVI даёт кандидата, Dynamic World говорит,
    # что именно произошло. Словарь исходов вместо одной цифры. Пороги DW есть
    # только у Брюсселя — для других городов сигнал относительный и так помечен.
    from engine.instruments import REGISTRY
    try:
        thr_dw = {k: v.threshold for k, v in Manifest.read(args.city).layers.items()}
        calibrated = all(k in thr_dw for k in ("built", "trees", "grass", "bare"))
    except Exception:
        calibrated = False
    lim = (lambda k: thr_dw[k]) if calibrated else (lambda k: 0.02)
    note = "" if calibrated else "  (DW не калиброван для города — относительный сигнал)"

    def read_change(d):
        if d["built"] > lim("built"): return "стройка / застройка"
        if d["built"] < -lim("built") and (d["grass"] > lim("grass") or d["trees"] > lim("trees")):
            return "раскрыли и озеленили"
        if d["bare"] < -lim("bare") and d["grass"] > lim("grass"): return "голая поверхность → трава"
        if d["trees"] > lim("trees") and abs(d["built"]) <= lim("built"): return "крона выросла"
        if d["trees"] < -lim("trees") and abs(d["built"]) <= lim("built"): return "крона ушла без стройки"
        if d["bare"] > lim("bare") and d["built"] < 0: return "раскрыли, но не засадили"
        return "неоднозначно"

    sig = [r for r in out if r["verdict"] in ("ПОЗЕЛЕНЕЛ", "ПОТЕРЯЛ")]
    print(f"\nвторой прибор по {len(sig)} значимым{note}…")
    for r in sig:
        g = ee.Geometry(meta[r["osm"]]["geometry"]); d = {}
        for cls in ("trees", "grass", "built", "bare"):
            i = REGISTRY[cls]
            b = i.measure(g, *w["before"]).value; a = i.measure(g, *w["after"]).value
            d[cls] = (a - b) if (a is not None and b is not None) else 0.0
        r["dw_reading"] = read_change(d)
        r["d_trees"], r["d_built"] = round(d["trees"], 3), round(d["built"], 3)
    for r in out:
        r.setdefault("dw_reading", ""); r.setdefault("d_trees", ""); r.setdefault("d_built", "")
    from collections import Counter as _C
    print("словарь исходов:", dict(_C(r["dw_reading"] for r in sig)))

    dest = Path(f"data/park_audit_{args.city}_{args.window}.csv")
    with dest.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(out[0].keys())); wr.writeheader(); wr.writerows(out)

    print(f"\nвердикты: {dict(Counter(r['verdict'] for r in out))}")
    for label, rows_ in (("ПОЗЕЛЕНЕЛИ", [r for r in out if r["verdict"] == "ПОЗЕЛЕНЕЛ"][:10]),
                         ("ПОТЕРЯЛИ", [r for r in out if r["verdict"] == "ПОТЕРЯЛ"][-8:])):
        print(f"\n──── {label} ────")
        for r in rows_:
            print(f"  {r['ndvi_effect']:+.4f}  {r['area_ha']:>6.1f} га  {r['name'][:32]:<34} {r.get('dw_reading',''):<26} разрыв {r['ctrl_gap']:+.3f}")
    print(f"\n→ {dest}\n⚠️  Детектор изменений: кандидаты, не подтверждённые вмешательства.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
