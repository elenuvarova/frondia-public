#!/usr/bin/env python3
"""
Калибровка прибора для любого города из config.CITIES.

Порог — свойство пары (город, прибор). Брюссельский 0,0373 к Антверпену
неприменим по построению: другой состав застройки, другая динамика, другой шум.
Каждая единица города по очереди — плацебо, распределение эффектов — нулевое,
порог — его 95-й процентиль. Результат идёт в манифест города.

Запуск:
    .venv/bin/python scripts/gee/calibrate_city.py --project <id> --city antwerp
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import ee
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS
from engine.calibrate import calibrate
from engine.config import CITIES, QUALITY, SUMMER_MONTHS, WINDOWS
from engine.instruments import REGISTRY
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
    ap.add_argument("--instrument", choices=["ndvi", "dw"], default="ndvi",
                    help="ndvi — зелёность; dw — пять классов Dynamic World разом")
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    w = WINDOWS[args.window]
    cfg = CITIES[args.city]
    adapter = ADAPTERS[args.city]()
    units = adapter.units()
    print(f"{cfg['display_name']}: {len(units)} единиц · окно {w['label']}")

    x0, y0, x1, y1 = cfg["bbox"]
    box = ee.Geometry.Rectangle([x0, y0, x1, y1])
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(u.geometry), {"id": u.id}) for u in units])
    by_id = {u.id: u for u in units}
    if args.instrument == "dw":
        # Пять классов разом; контроль подбирается по ОДНОМУ признаку — NDVI «до».
        # ⚠️ Не как в Брюсселе: там калибровка шла по двум (NDVI + LST «до», 100 м).
        # Поле lst_before здесь — копия NDVI, то есть второй оси у подбора нет.
        # Порог прибора годится только потребителям с той же схемой (аудиты парков,
        # дела аудита); слой ст. 8 считает свой порог тем же прогоном (25.09.2026).
        CLS = ["trees", "grass", "shrub_and_scrub", "built", "bare"]
        def dw_mean(start, end):
            return (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(box)
                    .filterDate(start, end)
                    .filter(ee.Filter.calendarRange(SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
                    .select(CLS).mean())
        stack = (s2_ndvi(box, *w["before"]).rename("nb")
                 .addBands(dw_mean(*w["before"]).rename([c + "_b" for c in CLS]))
                 .addBands(dw_mean(*w["after"]).rename([c + "_a" for c in CLS])))
        print("один прогон Earth Engine: NDVI «до» + пять классов DW до/после…")
        rows = stack.reduceRegions(fc, ee.Reducer.mean(), 30).getInfo()["features"]
        table = []
        for r in rows:
            p = r["properties"]; u = by_id.get(p["id"])
            if not u or p.get("nb") is None or u.area_ha < 4.0: continue
            if any(p.get(c + "_b") is None or p.get(c + "_a") is None for c in CLS): continue
            row = {"id": u.id, "ndvi_before": p["nb"], "lst_before": p["nb"], "centroid": u.centroid}
            for c in CLS: row[c + "_delta"] = p[c + "_a"] - p[c + "_b"]
            table.append(row)
        print(f"единиц с данными и площадью ≥ 4 га: {len(table)}\n")
        m = Manifest.read(args.city)
        results = {}
        for c in CLS:
            key = "shrub" if c == "shrub_and_scrub" else c
            cal = calibrate(table, c, "ndvi_before", "lst_before")
            results[key] = cal
            print(cal.describe())
            m.from_instrument(REGISTRY[key],
                method="разность разностей, те же 12 контролей по NDVI «до», что у ndvi",
                threshold=round(cal.threshold, 5), threshold_source=cal.source_line,
                n_units=cal.n, computed="2026-09-02")
        path = m.write()
        Path(f"data/{args.city}_dw_calibration.json").write_text(json.dumps(
            {k: {"n": v.n, "mean": v.mean, "sd": v.sd, "threshold": v.threshold}
             for k, v in results.items()}, ensure_ascii=False, indent=1))
        print(f"\n→ {path}  (слоёв в манифесте: {len(m.layers)})")
        print("Брюссель для сравнения: grass 0,009 · shrub 0,005 · bare 0,006 · trees 0,014 · built 0,025")
        return 0

    stack = (s2_ndvi(box, *w["before"]).rename("nb")
             .addBands(s2_ndvi(box, *w["after"]).rename("na")))
    print("один прогон Earth Engine по всем единицам…")
    rows = stack.reduceRegions(fc, ee.Reducer.mean(), 30).getInfo()["features"]

    table = []
    for r in rows:
        p = r["properties"]; u = by_id.get(p["id"])
        if not u or p.get("nb") is None or p.get("na") is None: continue
        if u.area_ha < 4.0: continue
        # ⚠️ второй признак — копия NDVI: подбор по одной зелёности, в отличие от Брюсселя
        table.append({"id": u.id, "ndvi_before": p["nb"], "lst_before": p["nb"],
                      "ndvi_delta": p["na"] - p["nb"], "centroid": u.centroid})
    print(f"единиц с данными и площадью ≥ 4 га: {len(table)}\n")

    # пул контроля для аудита следов — те же колонки, что у брюссельского файла
    import csv
    tbl = Path(f"data/{args.city}_sector_change_{args.window}.csv")
    with tbl.open("w", newline="") as fh:
        wr = csv.writer(fh); wr.writerow(["id", "ndvi_before", "lst_before", "d_ndvi_raw", "lon", "lat"])
        for t in table:
            # 6 знаков, не 4: при 4 пересчёт движком расходился с оригиналом
            # на 8 % секторов из-за смены 12-го соседа при равных расстояниях
            wr.writerow([t["id"], round(t["ndvi_before"], 6), round(t["lst_before"], 6),
                         round(t["ndvi_delta"], 6), round(t["centroid"][0], 6), round(t["centroid"][1], 6)])
    print(f"пул контроля → {tbl}")

    c = calibrate(table, "ndvi", "ndvi_before", "lst_before")
    print(c.describe()); print(f"несмещён: {c.unbiased}")
    for p_, v in sorted(c.percentiles.items()): print(f"  {p_:>3}-й процентиль: {v:+.5f}")

    m = Manifest(args.city)
    m.from_instrument(REGISTRY["ndvi"],
        method="разность разностей, 12 подобранных единиц",
        threshold=round(c.threshold, 5), threshold_source=c.source_line,
        n_units=c.n, computed="2026-09-02")
    path = m.write()
    Path(f"data/{args.city}_calibration.json").write_text(json.dumps(
        {"instrument": "ndvi", "n": c.n, "mean": c.mean, "sd": c.sd,
         "threshold": c.threshold, "percentiles": c.percentiles,
         "window": w["label"], "source": c.source_line}, ensure_ascii=False, indent=1))
    print(f"\n→ {path}")
    print(f"Брюссель, тот же прибор и окно: порог 0,0373 · ст.откл. 0,0179")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
