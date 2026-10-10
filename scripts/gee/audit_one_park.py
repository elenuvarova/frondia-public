#!/usr/bin/env python3
"""
Аудит одного парка с настраиваемыми окнами — проверка чувствительности к срокам.

Зачем
─────
Пакетный прогон использует фиксированное окно «до» 2017–2019. Если работы шли
именно в эти годы, окно захватывает СТРОЙКУ, а не исходное состояние. Голый грунт
стройплощадки даёт очень низкий NDVI, и эффект получается завышенным: сравнение
идёт не «пустырь → парк», а «стройка → парк».

Проверяется сдвигом окна «до» на годы перед началом работ. Если эффект резко
падает — число было раздуто стройкой. Если держится — эффект настоящий.

Пример (Parc de la Porte de Ninove, работы завершены в 2019):
    .venv/bin/python scripts/gee/audit_one_park.py --project <id> \\
        --name Ninove --before 2016-01-01 2016-12-31
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path

import ee

PARKS = Path("data/perimeters/parks_brussels.geojson")
SECTORS_TABLE = Path("data/sector_change_2017_2024.csv")

SUMMER = (6, 8)
MAX_CLOUD = 30
N_CONTROLS = 12
EXCLUSION_M = 1500
NDVI_THRESHOLD = 0.0373
MAX_GAP = 0.04


def s2_ndvi(geom, start, end):
    cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    coll = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geom).filterDate(start, end)
            .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], "month"))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD))
            .linkCollection(cs, ["cs_cdf"])
            .map(lambda i: i.normalizedDifference(["B8", "B4"]).rename("ndvi")
                 .updateMask(i.select("cs_cdf").gte(0.6))))
    return coll.median(), coll.size()


def centroid(geom):
    c = geom["coordinates"]
    while isinstance(c[0][0], list):
        c = c[0]
    return sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)


def dist_m(a, b):
    k = math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * k * 111320, (a[1] - b[1]) * 110540)


def main() -> int:
    ap = argparse.ArgumentParser(description="Аудит одного парка с окнами")
    ap.add_argument("--project", required=True)
    ap.add_argument("--name", required=True, help="часть названия парка")
    ap.add_argument("--before", nargs=2, metavar=("START", "END"),
                    default=["2017-01-01", "2019-12-31"])
    ap.add_argument("--after", nargs=2, metavar=("START", "END"),
                    default=["2021-01-01", "2024-12-31"])
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    parks = json.loads(PARKS.read_text())["features"]
    hits = [f for f in parks
            if args.name.lower() in f["properties"]["name"].lower()]
    if not hits:
        print(f"парк «{args.name}» не найден")
        return 1
    park = max(hits, key=lambda f: f["properties"]["area_ha"])
    props = park["properties"]
    geom = ee.Geometry(park["geometry"])

    print(f"{props['name']}  ·  {props['area_ha']} га  ·  {props['osm']}")
    print(f"окно ДО:    {args.before[0]} … {args.before[1]}")
    print(f"окно ПОСЛЕ: {args.after[0]} … {args.after[1]}\n")

    nb_img, nb_n = s2_ndvi(geom, *args.before)
    na_img, na_n = s2_ndvi(geom, *args.after)

    def mean(img):
        return img.reduceRegion(ee.Reducer.mean(), geom, scale=10,
                                maxPixels=int(1e9), bestEffort=True).get("ndvi")

    nb, na, n_before, n_after = ee.List(
        [mean(nb_img), mean(na_img), nb_n, na_n]).getInfo()

    print(f"сцен: до {n_before} · после {n_after}")
    if n_before is None or nb is None:
        print("нет данных в окне «до» — сдвинь границы")
        return 1
    if min(n_before, n_after) < 8:
        print(f"⚠️  меньше 8 сцен — медиана шумная, результат предварительный")

    # контроль: сектора, подобранные по исходной зелёности
    sectors = list(csv.DictReader(SECTORS_TABLE.open()))
    for s in sectors:
        s["ndvi_before"] = float(s["ndvi_before"])
        s["d_ndvi_raw"] = float(s["d_ndvi_raw"])
        s["c"] = (float(s["lon"]), float(s["lat"]))

    c = centroid(park["geometry"])
    pool = [s for s in sectors if dist_m(c, s["c"]) >= EXCLUSION_M]
    pool.sort(key=lambda s: abs(s["ndvi_before"] - nb))
    ctrl = pool[:N_CONTROLS]

    ctrl_nb = statistics.mean(s["ndvi_before"] for s in ctrl)
    ctrl_d = statistics.mean(s["d_ndvi_raw"] for s in ctrl)
    gap = nb - ctrl_nb
    effect = (na - nb) - ctrl_d

    print(f"\nNDVI объекта:   {nb:+.4f} → {na:+.4f}   сырая дельта {na - nb:+.4f}")
    print(f"контроль:       {ctrl_nb:+.4f}          сырая дельта {ctrl_d:+.4f}")
    print(f"разрыв подбора: {gap:+.4f}  (предел {MAX_GAP})")
    print(f"\nЭФФЕКТ: {effect:+.4f}   порог {NDVI_THRESHOLD}")

    if abs(gap) > MAX_GAP:
        print("ВЕРДИКТ: контроль несопоставим, эффект не заявляем")
    elif effect > NDVI_THRESHOLD:
        print("ВЕРДИКТ: ПОЗЕЛЕНЕЛ, значимо")
    elif effect < -NDVI_THRESHOLD:
        print("ВЕРДИКТ: ПОТЕРЯЛ, значимо")
    else:
        print("ВЕРДИКТ: в пределах шума")

    # контроль важен для прослеживаемости — печатаем поимённо
    print("\nконтрольные секторы:")
    for s in ctrl:
        print(f"  {s['id']:<12} {s['name'][:26]:<26} NDVI до {s['ndvi_before']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
