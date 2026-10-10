#!/usr/bin/env python3
"""
Поле для сайта: летняя зелёность города, снятая тем же прибором, что меряет.

У референсов в герое нарисованный градиент. У нас на его месте настоящее поле:
летняя медиана NDVI Sentinel-2 — прибор `ndvi` движка, та же маска облаков
Cloud Score+ и те же летние месяцы. Цвет означает измерение: тёплое бледное —
запечатанное, зелёное — растительность, тёмно-зелёный — лес, голубое — вода.

Лесной конец палитры — зелёный, а не бирюзовый (25.09.2026): бирюза — цвет вердикта
«позеленел» (`--gain-*`), и при протанопии бирюзовый лес под сектором «в пределах
шума» было не отличить от значимого прироста (ΔE00 0,8 при непрозрачности 0,6).
Под картами с данными поле кладётся с непрозрачностью 0,30: тогда минимум ΔE00 против
обеих шкал вердиктов — 10,8 при всех типах цветового зрения, и самое тёмное место поля
(L* 79,7) светлее самой светлой заливки (L* 65,4). В полную силу поле идёт только туда,
где данных нет: герой и линза «Поле».

Две рамки:
  atlas — ровно охват секторов; совпадает с SVG атласа (проекция atlas_data.py:
          долгота × cos(широты), ширина 1000), поэтому полигоны ложатся точно;
  wide  — тот же центр, 16:10 с запасом, для полноэкранного героя (размыт) и для
          подложки атласа вокруг города (`context`, резкий), чтобы карта не обрывалась
          краем прямоугольника секторов.

Две палитры: light (бумага) и dark (ночь, приглушённая — под полигоны атласа);
сайт пока берёт только light, ночная выгружается флагом `--dark`. Третья, cadro, — только
для героя концепции «Satoyama + сирень»: её кадр получают перекраской готового light
(`field_recolor.py`), без Earth Engine.
Кадры героя размыты гауссовым ядром в метрах на стороне Earth Engine — мягкое
поле без жёстких краёв, и JPEG весит десятки килобайт, а не мегабайты.

Рядом пишется `field-<city>.json`: охват каждой рамки в градусах и в координатах
SVG атласа — сайт кладёт картинку под полигоны без подгонки.

Запуск:
    .venv/bin/python scripts/site/field.py --project <id> --city brussels
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import ee

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.config import CITIES  # noqa: E402
from engine.instruments.vegetation import NDVI  # noqa: E402

OUT = Path("site/public/field")
NDVI_MIN, NDVI_MAX = -0.1, 0.9          # 9 ступеней через 0,125
PALETTES = {
    # вода · дымка · плотная застройка · масло · жёлто-зелёный · светло-зелёный ·
    # листовой · травяной · тёмно-зелёный (лес); светлота растительной ветки монотонна
    "light": ["a9cadb", "d9e3e4", "f2e4d6", "f4e2b8", "e6e39a",
              "cadb8e", "a1c873", "72a652", "4a7e3a"],
    "dark": ["16324a", "0f1416", "121614", "151b17", "1a241c",
             "1f3122", "264029", "2f5534", "4d7a50"],
    # концепция «Satoyama + сирень» (26.09.2026): зелёные — кластеры CADRO (143:189 на
    # refs, OKLab) от лайма к лесной бирюзе, вода — его перивинкль, застройка — как в light.
    # Только для героя концепции: под картами с данными эту ветку не проверяли.
    "cadro": ["84a7d5", "d9e3e4", "f2e4d6", "f4e2b8", "c9ed73",
              "9cd25b", "64ac46", "308838", "186e50"],
}
WIDE_ASPECT, WIDE_MARGIN = 1.6, 0.08    # 16:10, запас 8 % высоты сверху и снизу


def rings(g):
    return [g["coordinates"][0]] if g["type"] == "Polygon" else [pp[0] for pp in g["coordinates"]]


def frames(city: str) -> dict:
    """Охваты рамок — той же арифметикой, что atlas_data.py."""
    units = ADAPTERS[city]().units()
    lat0 = sum(u.centroid[1] for u in units) / len(units)
    kx, ky = 111320 * math.cos(math.radians(lat0)), 110540
    pts = [p for u in units for r in rings(u.geometry) for p in r]
    x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
    y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
    W = 1000.0
    scale = W / ((x1 - x0) * kx)
    H = (y1 - y0) * ky * scale
    atlas = {"lon": [x0, x1], "lat": [y0, y1], "svg": [0.0, 0.0, W, round(H, 2)]}
    h = H * (1 + 2 * WIDE_MARGIN)
    w = max(W, h * WIDE_ASPECT)
    dx, dy = (w - W) / 2, (h - H) / 2
    wide = {"lon": [x0 - dx / (kx * scale), x1 + dx / (kx * scale)],
            "lat": [y0 - dy / (ky * scale), y1 + dy / (ky * scale)],
            "svg": [round(-dx, 2), round(-dy, 2), round(w, 2), round(h, 2)]}
    return {"atlas": atlas, "wide": wide}


def summer_ndvi(region, year: int) -> ee.Image:
    return NDVI()._collection(region, f"{year}-01-01", f"{year}-12-31").median()


def shrink(path: Path, quality: int, width: int | None = None) -> None:
    """Пережать JPEG для сайта. Earth Engine отдаёт JPEG без выбора качества, и
    резкая карта весит под 3 МБ. `sips` есть на любом Mac; без него файл остаётся как есть."""
    if not shutil.which("sips"):
        return
    cmd = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality)]
    if width:
        cmd += ["--resampleWidth", str(width)]
    subprocess.run(cmd + [str(path), "--out", str(path)], check=True, capture_output=True)


def save(img: ee.Image, box: dict, width: int, path: Path,
         quality: int | None = None, web_width: int | None = None) -> None:
    (lx0, lx1), (ly0, ly1) = box["lon"], box["lat"]
    region = ee.Geometry.Rectangle([lx0, ly0, lx1, ly1], "EPSG:4326", False)
    height = round(width * box["svg"][3] / box["svg"][2])
    url = img.getThumbURL({"region": region, "dimensions": f"{width}x{height}",
                           "crs": "EPSG:4326", "format": "jpg"})
    path.write_bytes(urllib.request.urlopen(url, timeout=300).read())
    if quality:
        shrink(path, quality, web_width)
    print(f"  {path.name}  {web_width or width}px  {path.stat().st_size // 1024} КБ", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--city", choices=list(CITIES), required=True)
    ap.add_argument("--base-year", type=int, default=2024, help="год подложки атласа (база ст. 8)")
    ap.add_argument("--years", default="2017-2026", help="кадры героя, лета")
    ap.add_argument("--blur-m", type=float, default=90, help="сигма размытия кадров героя, м")
    ap.add_argument("--only", choices=["atlas", "wide", "context"], default=None,
                    help="atlas — рамка ровно по секторам (сайтом не используется, для проверки совмещения)")
    ap.add_argument("--dark", action="store_true", help="выгрузить и ночную палитру")
    ap.add_argument("--true-color", action="store_true",
                    help="резкий снимок в естественных цветах (B4/B3/B2) в рамке wide — для героя-аэрофото")
    ap.add_argument("--photos", default=None, metavar="YEARS",
                    help="снимки в естественных цветах для шторки атласа «весь город до и после», "
                         "например 2017,2024 → <city>-photo-<год>.jpg")
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    OUT.mkdir(parents=True, exist_ok=True)
    fr = frames(args.city)
    lo, hi = fr["wide"]["lon"], fr["wide"]["lat"]
    region = ee.Geometry.Rectangle([lo[0], hi[0], lo[1], hi[1]], "EPSG:4326", False)
    vis = lambda img, pal: img.visualize(min=NDVI_MIN, max=NDVI_MAX, palette=PALETTES[pal])

    pals = list(PALETTES) if args.dark else ["light"]
    if args.only == "atlas":
        base = summer_ndvi(region, args.base_year)
        for pal in pals:
            save(vis(base, pal), fr["atlas"], 2000,
                 OUT / f"{args.city}-atlas-{args.base_year}-{pal}.jpg", quality=62)

    if args.photos:
        # «Весь город до и после»: фотография, а не измерение. Уровень L1C (до атмосферной коррекции),
        # потому что L2A в каталоге Earth Engine за лето 2017 покрывает Брюссель не целиком (чёрный клин
        # на западе рамки); L1C взят для обоих лет, чтобы цвет совпадал. Маска облаков — Cloud Score+,
        # как у прибора, но строже (0,7 вместо 0,6); где за лето не осталось ни одного чистого пикселя, дыру
        # закрывает медиана без маски. Композит — 30-й процентиль, а не медиана: дымка только осветляет, и
        # у медианы лета 2017 (20 сцен, у пикселя 3–5 чистых) северо-восток Антверпена выходил синеватым.
        from engine.instruments.vegetation import _summer
        cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
        for year in (int(y) for y in args.photos.split(",")):
            raw = (_summer(ee.ImageCollection("COPERNICUS/S2_HARMONIZED").filterBounds(region),
                           f"{year}-01-01", f"{year}-12-31")
                   .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40)))
            RGB = ["B4", "B3", "B2"]
            clear = raw.linkCollection(cs, ["cs_cdf"]).map(
                lambda i: i.updateMask(i.select("cs_cdf").gte(0.7)).select(RGB))
            low = clear.reduce(ee.Reducer.percentile([30])).rename(RGB)
            rgb = low.unmask(raw.select(RGB).median()).divide(10000)
            # L1C carries the atmosphere's blue haze: each band is stretched between its own 1st and 99th
            # percentile inside the city's frame, per year, so a hazier summer does not read as a change
            (ax0, ax1), (ay0, ay1) = fr["atlas"]["lon"], fr["atlas"]["lat"]
            st = rgb.reduceRegion(ee.Reducer.percentile([1, 99]), ee.Geometry.Rectangle([ax0, ay0, ax1, ay1]),
                                  scale=60, bestEffort=True).getInfo()
            img = rgb.visualize(bands=RGB, min=[st[f"{b}_p1"] for b in RGB], max=[st[f"{b}_p99"] for b in RGB], gamma=1.35)
            save(img, fr["wide"], 2400, OUT / f"{args.city}-photo-{year}.jpg", quality=64)
        return 0

    if args.true_color:
        # естественные цвета: та же летняя медиана Sentinel-2 и та же маска облаков, что у прибора,
        # только каналы красный-зелёный-синий вместо индекса; это фотография, не измерение
        from engine.instruments.vegetation import _summer
        cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
        coll = (_summer(ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region),
                        f"{args.base_year}-01-01", f"{args.base_year}-12-31")
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
                .linkCollection(cs, ["cs_cdf"])
                .map(lambda i: i.updateMask(i.select("cs_cdf").gte(0.6))))
        rgb = coll.median().select(["B4", "B3", "B2"]).divide(10000)
        img = rgb.visualize(min=0.0, max=0.22, gamma=1.25)
        save(img, fr["wide"], 2400, OUT / f"{args.city}-truecolor-{args.base_year}.jpg", quality=64)
        return 0

    if args.only in (None, "context"):
        base = summer_ndvi(region, args.base_year)
        save(vis(base, "light"), fr["wide"], 2400, OUT / f"{args.city}-context-{args.base_year}-light.jpg",
             quality=60)

    y0, y1 = (int(y) for y in args.years.split("-"))
    years = list(range(y0, y1 + 1))
    if args.only in (None, "wide"):
        kernel = ee.Kernel.gaussian(radius=args.blur_m * 3, sigma=args.blur_m, units="meters")
        for y in years:
            soft = summer_ndvi(region, y).convolve(kernel)
            for pal in pals:
                save(vis(soft, pal), fr["wide"], 1600, OUT / f"{args.city}-wide-{y}-{pal}.jpg",
                     quality=62, web_width=1200)

    meta = {"city": args.city, "instrument": "ndvi", "source": NDVI.source,
            "ndvi_range": [NDVI_MIN, NDVI_MAX], "palettes": PALETTES,
            "base_year": args.base_year, "years": years, "blur_sigma_m": args.blur_m,
            "frames": fr}
    (OUT / f"field-{args.city}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"→ {OUT}/field-{args.city}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
