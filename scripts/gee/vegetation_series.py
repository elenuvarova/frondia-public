#!/usr/bin/env python3
"""Ряд растительного покрова без смены метода: каждое лето одна и та же схема, 2016–2025.

Зачем. Bruxelles Environnement объявил падение растительного покрова региона с ~55 % (2016) до 48,7 %
(2023) и сам признал, что отчасти это «l'amélioration des techniques de cartographie» (bx1, 24.06.2026).
Вопрос: что показывает ряд, в котором метод НЕ менялся? Если он почти ровный, бóльшая часть
объявленного падения — смена картирования; если падает — где и насколько.

Что считаем, на всю территорию города (объединение секторов Statbel), каждое лето июнь–август:
  · доля пикселей 10 м, где класс-победитель среднего лета Dynamic World — растительность
    (деревья, трава, затопляемая, пашня, кустарник) — та же жёсткая классификация, что в art8_balance;
  · то же для деревьев;
  · медиана NDVI Sentinel-2 (Cloud Score+), и доля пикселей с NDVI > 0,3 — грубая «растительная» маска.
Межгодовой разброс ряда — это шум погоды и снимков; изменение меньше него за 7 лет не измерено.

Чего здесь нет. Контроля: регион целиком не с чем сравнить внутри города. Поэтому это не вердикт
«изменилось сверх шума», а проверка направления и порядка объявленной цифры. NDVI — зелёность, не
площадь; Dynamic World — другой классификатор, чем у Bruxelles Environnement; сравнивать один в один
6,3 пункта нельзя. Лето 2016 снимал только Sentinel-2A — снимков меньше, число печатается.

    .venv/bin/python scripts/gee/vegetation_series.py --project my-project-maps-507221 --city brussels

Пишет data/derived/vegetation_series_<city>.csv.
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path

import ee

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.config import CITIES, QUALITY  # noqa: E402

YEARS = range(2016, 2026)
DW_BANDS = ["water", "trees", "grass", "flooded_vegetation", "crops", "shrub_and_scrub", "built", "bare", "snow_and_ice"]
VEG_IDX = [1, 2, 3, 4, 5]          # деревья, трава, затопляемая, пашня, кустарник


def summer(y: int) -> tuple[str, str]:
    return f"{y}-06-01", f"{y}-09-01"


def layers(geom, y: int):
    dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(geom).filterDate(*summer(y))
    label = dw.select(DW_BANDS).mean().toArray().arrayArgmax().arrayGet([0])
    cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")

    def nd(img):
        return (img.normalizedDifference(["B8", "B4"]).rename("ndvi")
                .updateMask(img.select("cs_cdf").gte(QUALITY["cloud_score_plus_min"])))
    s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(geom).filterDate(*summer(y))
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", QUALITY["max_cloud_pct"])))
    ndvi = s2.linkCollection(cs, ["cs_cdf"]).map(nd).median()
    img = (label.remap(VEG_IDX, [1] * len(VEG_IDX), 0).rename("veg")
           .addBands(label.eq(1).rename("trees"))
           .addBands(ndvi.rename("ndvi"))
           .addBands(ndvi.gt(0.3).rename("ndvi_gt03")))
    return img, dw.size(), s2.size()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--city", choices=list(CITIES), default="brussels")
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    units = ADAPTERS[args.city]().units()
    region = ee.FeatureCollection([ee.Feature(ee.Geometry(u.geometry)) for u in units]).geometry().dissolve(10)
    rows = []
    for y in YEARS:
        img, n_dw, n_s2 = layers(region, y)
        mean = img.select(["veg", "trees", "ndvi_gt03"]).reduceRegion(
            ee.Reducer.mean(), region, 10, maxPixels=1e10)
        med = img.select("ndvi").reduceRegion(ee.Reducer.median(), region, 10, maxPixels=1e10)
        m, d = mean.getInfo(), med.getInfo()
        n2 = n_s2.getInfo()
        row = {"year": y, "dw_scenes": n_dw.getInfo(), "s2_scenes": n2,
               # too few clear scenes for a summer is an outcome of its own (QUALITY["min_scenes"]): «preliminary»
               "preliminary": n2 < QUALITY["min_scenes"],
               "veg_dw": m.get("veg"), "trees_dw": m.get("trees"),
               "ndvi_gt03": m.get("ndvi_gt03"), "ndvi_median": d.get("ndvi")}
        rows.append(row)
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}, flush=True)

    out = ROOT / f"data/derived/vegetation_series_{args.city}.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
    by_year = {r["year"]: r for r in rows}
    for k in ("veg_dw", "trees_dw", "ndvi_gt03", "ndvi_median"):
        vals = [r[k] for r in rows if r[k] is not None]
        a, b = by_year[2016][k], by_year[2023][k]
        print(f"{k}: 2016 {a:.4f} → 2023 {b:.4f} (Δ {b - a:+.4f}); "
              f"межгодовой разброс ст.откл. {statistics.stdev(vals):.4f}, размах {max(vals) - min(vals):.4f}")
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
