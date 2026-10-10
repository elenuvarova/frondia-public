#!/usr/bin/env python3
"""
Калибровка прибора Landsat: своё нулевое распределение и свой порог.

Почему нельзя взять порог Sentinel-2
────────────────────────────────────
30 метров против 10: пиксель в девять раз крупнее, шум другой. Подставить
сентинелевский порог 0,0373 к ландсатовским числам — прямой подлог, того же
рода, что заявлять охлаждение по летним медианам.

Калибровка идёт на ТОМ ЖЕ окне (2017–2019 → 2021–2024), что и Sentinel-2.
Это намеренно: одинаковое окно позволяет сравнить приборы напрямую и понять,
сколько мы теряем на разрешении, прежде чем применять Landsat туда, куда
Sentinel-2 не дотягивается.

Запуск:
    .venv/bin/python scripts/gee/calibrate_landsat.py --project <id>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import ee

# скрипт лежит в scripts/gee/, движок — в корне репозитория
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.calibrate import calibrate
from engine.config import WINDOWS
from engine.instruments.landsat import _prep, LEGACY, MODERN
from engine.config import QUALITY, SUMMER_MONTHS

SECTORS = Path("data/brussels_sectors.geojson")
OUT = Path("data/landsat_calibration.json")


def landsat_median(geom, start: str, end: str) -> ee.Image:
    modern = ee.ImageCollection(MODERN[0]).merge(ee.ImageCollection(MODERN[1]))
    legacy = ee.ImageCollection(LEGACY[0]).merge(ee.ImageCollection(LEGACY[1]))

    def window(c):
        return (c.filterBounds(geom).filterDate(start, end)
                .filter(ee.Filter.calendarRange(
                    SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
                .filter(ee.Filter.lt("CLOUD_COVER", QUALITY["max_cloud_pct"])))

    return (window(modern).map(lambda i: _prep(i, "SR_B5", "SR_B4"))
            .merge(window(legacy).map(lambda i: _prep(i, "SR_B4", "SR_B3")))
            .median())


def main() -> int:
    ap = argparse.ArgumentParser(description="Калибровка Landsat NDVI")
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    w = WINDOWS["2017_2024"]
    bxl = ee.Geometry.Rectangle([4.23, 50.76, 4.50, 50.94])
    feats = json.loads(SECTORS.read_text())["features"]

    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f["geometry"]), {"id": f["properties"]["id"]})
        for f in feats
    ])

    print(f"считаю Landsat NDVI до/после по {len(feats)} секторам, один прогон…")
    stack = (landsat_median(bxl, *w["before"]).rename("nb")
             .addBands(landsat_median(bxl, *w["after"]).rename("na")))
    rows = stack.reduceRegions(fc, ee.Reducer.mean(), 30).getInfo()["features"]

    meta = {f["properties"]["id"]: f["properties"] for f in feats}
    units = []
    for r in rows:
        p = r["properties"]
        m = meta[p["id"]]
        if p.get("nb") is None or p.get("na") is None:
            continue
        if (m.get("area_ha") or 0) < 4.0:
            continue
        units.append({
            "id": p["id"],
            "ndvi_landsat_before": p["nb"],
            "lst_before": p["nb"],          # второй признак: тот же, отдельного нет
            "ndvi_landsat_delta": p["na"] - p["nb"],
            "centroid": (m["centroid_lon"], m["centroid_lat"]),
        })

    print(f"единиц с данными: {len(units)}\n")
    c = calibrate(units, "ndvi_landsat",
                  "ndvi_landsat_before", "lst_before")

    print(c.describe())
    print(f"несмещён: {c.unbiased}")
    print("\nпроцентили нулевого распределения:")
    for p, v in sorted(c.percentiles.items()):
        print(f"  {p:>3}: {v:+.5f}")

    s2_threshold = 0.0373
    print(f"\n──────── Сравнение приборов на одном окне ────────")
    print(f"  Sentinel-2, 10 м:  порог {s2_threshold:.4f}")
    print(f"  Landsat,    30 м:  порог {c.threshold:.4f}")
    ratio = c.threshold / s2_threshold
    print(f"  порог выше в {ratio:.2f} раза")
    print(f"\n  При этом Landsat ловит ~60 % сырого сигнала (замерено на 4 объектах).")
    print(f"  Значит эффективная чувствительность хуже примерно в {ratio / 0.6:.1f} раза:")
    print(f"  сигнал меньше, порог выше — штраф двойной.")

    OUT.write_text(json.dumps({
        "instrument": c.instrument, "n": c.n, "mean": c.mean, "sd": c.sd,
        "threshold": c.threshold, "percentiles": c.percentiles,
        "window": w["label"], "source": c.source_line,
    }, ensure_ascii=False, indent=1))
    print(f"\n→ {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
