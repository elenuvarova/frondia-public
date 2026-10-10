#!/usr/bin/env python3
"""
Экспорт картинок «до / после» для сектора — визуальная проверка измеренного.

Числа без картинки проверить нельзя: +0,039 NDVI может быть и реальным
озеленением, и артефактом обработки. Здесь снимки выгружаются как PNG,
чтобы посмотреть глазами.

Выгружается четыре файла:
  <id>_before.png          — летний медианный композит RGB за окно «до»
  <id>_after.png           — то же за окно «после»
  <id>_delta_relative.png  — изменение ОТНОСИТЕЛЬНО базовой линии ← это на экран аудита
  <id>_delta_raw.png       — сырое изменение, для сравнения

Почему две карты изменения. За 2017–2024 позеленел весь Брюссель, поэтому карта
сырой дельты выходит равномерно бирюзовой по всему кадру и не означает ничего.
Ноль шкалы обязан стоять там же, где ноль в отчётном числе, иначе картинка
противоречит подписи под ней. Проверено на Parvis Saint-Roch.

Честная оговорка: Sentinel-2 даёт 10 м на пиксель. Сектор в 5 га — это примерно
23×23 пикселя. Поэтому кадрируем шире сектора и обводим его границу, иначе
смотреть не на что.

Запуск:
    .venv/bin/python scripts/gee/export_before_after.py \
        --project <id> --sector 21004D600
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

import ee

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

SECTORS_PATH = "data/brussels_sectors.geojson"
OUT_DIR = Path("data/exports")

BEFORE = {"start": "2017-01-01", "end": "2019-12-31"}
AFTER = {"start": "2021-01-01", "end": "2024-12-31"}
SUMMER = (6, 8)
MAX_CLOUD = 20          # для картинки берём чище, чем для статистики
CONTEXT_M = 420         # сколько метров контекста вокруг сектора


def s2_collection(geom, rng, max_cloud=MAX_CLOUD):
    cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geom).filterDate(rng["start"], rng["end"])
            .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], "month"))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud))
            .linkCollection(cs, ["cs_cdf"])
            .map(lambda i: i.updateMask(i.select("cs_cdf").gte(0.6))))


def download(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "map-project/0.1"})
    with urllib.request.urlopen(req, timeout=180) as r, open(path, "wb") as fh:
        fh.write(r.read())
    print(f"  → {path}  ({path.stat().st_size // 1024} КБ)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Экспорт до/после по сектору")
    ap.add_argument("--project", required=True)
    ap.add_argument("--sector", help="id сектора, напр. 21004D600")
    ap.add_argument("--footprint", help="часть названия парка из parks_<city>.geojson")
    ap.add_argument("--city", default="brussels", help="brussels | antwerp")
    ap.add_argument("--px", type=int, default=900, help="размер картинки в пикселях")
    ap.add_argument("--baseline", type=float, default=None,
                    help="среднее изменение контроля; без него берётся медиана по городу")
    args = ap.parse_args()

    ee.Initialize(project=args.project)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.footprint:
        feats = json.load(open(f"data/perimeters/parks_{args.city}.geojson"))["features"]
        match = [f for f in feats if args.footprint.lower() in f["properties"]["name"].lower()]
        if not match:
            print(f"парк «{args.footprint}» не найден", file=sys.stderr); return 1
        match.sort(key=lambda f: -f["properties"]["area_ha"])
        props = match[0]["properties"]
        name = props["name"]
        key = props["osm"].replace("/", "_")
    else:
        feats = json.load(open(SECTORS_PATH))["features"]
        match = [f for f in feats if f["properties"]["id"] == args.sector]
        if not match:
            print(f"сектор {args.sector} не найден", file=sys.stderr); return 1
        props = match[0]["properties"]
        name = props.get("name_fr") or props.get("name_nl") or args.sector
        key = args.sector
    sector = ee.Geometry(match[0]["geometry"])
    region = sector.buffer(CONTEXT_M).bounds()
    print(f"{key} · {name} · {props['area_ha']:.1f} га")
    print(f"Кадр: сектор + {CONTEXT_M} м контекста\n")

    before = s2_collection(region, BEFORE)
    after = s2_collection(region, AFTER)
    print(f"сцен: до {before.size().getInfo()} · после {after.size().getInfo()}")

    rgb_vis = {"bands": ["B4", "B3", "B2"], "min": 200, "max": 2200, "gamma": 1.15}

    # Контур сектора поверх снимка — иначе непонятно, куда смотреть
    outline = ee.Image().byte().paint(
        featureCollection=ee.FeatureCollection([ee.Feature(sector)]),
        color=1, width=2)

    for label, coll in (("before", before), ("after", after)):
        img = coll.median().visualize(**rgb_vis)
        img = img.blend(outline.visualize(palette=["FFFF00"]))
        url = img.getThumbURL({"region": region, "dimensions": args.px, "format": "png"})
        download(url, OUT_DIR / f"{key}_{label}.png")

    # ── Карта изменения ──────────────────────────────────────────────────────
    # ВАЖНО: показываем изменение ОТНОСИТЕЛЬНО базовой линии, а не сырое.
    # За 2017–2024 позеленел весь Брюссель, поэтому карта сырой дельты выходит
    # равномерно бирюзовой и не значит ничего. Ноль шкалы должен стоять там же,
    # где ноль в отчётном числе, — иначе карта противоречит подписи под ней.
    ndvi_b = before.median().normalizedDifference(["B8", "B4"])
    ndvi_a = after.median().normalizedDifference(["B8", "B4"])
    delta = ndvi_a.subtract(ndvi_b)

    if args.baseline is not None:
        baseline = args.baseline
        src = "среднее изменение контрольной группы (передано аргументом)"
    else:
        from engine.config import CITIES
        x0, y0, x1, y1 = CITIES[args.city]["bbox"]
        bxl = ee.Geometry.Rectangle([x0, y0, x1, y1])
        baseline = delta.reduceRegion(
            reducer=ee.Reducer.median(), geometry=bxl, scale=100,
            maxPixels=int(1e9), bestEffort=True).values().get(0).getInfo()
        src = "медиана изменения по всему Брюсселю"

    print(f"\nБазовая линия карты: {baseline:+.4f} — {src}")
    relative = delta.subtract(ee.Image.constant(baseline))

    ramp = {"min": -0.15, "max": 0.15,
            "palette": ["c9302f", "e05f5f", "f09a9a", "E8E8E4",
                        "5cc4b6", "22998d", "0f6b63"]}
    rel_vis = relative.visualize(**ramp).blend(outline.visualize(palette=["000000"]))
    url = rel_vis.getThumbURL({"region": region, "dimensions": args.px, "format": "png"})
    download(url, OUT_DIR / f"{key}_delta_relative.png")

    # Сырую дельту тоже сохраняем — она показывает, ПОЧЕМУ нужна поправка
    raw_vis = delta.visualize(**{**ramp, "min": -0.25, "max": 0.25}) \
        .blend(outline.visualize(palette=["000000"]))
    url = raw_vis.getThumbURL({"region": region, "dimensions": args.px, "format": "png"})
    download(url, OUT_DIR / f"{key}_delta_raw.png")

    print("\nНа _delta_relative: бирюзовое — изменилось сильнее базовой линии,")
    print("красное — слабее. Это то, что показывает экран аудита.")
    print("_delta_raw оставлен для сравнения: там бирюзово всё, и в этом смысла нет.")
    print("Жёлтый контур на снимках и чёрный на картах — граница сектора.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
