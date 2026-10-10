#!/usr/bin/env python3
"""
Ретро-аудит городского вмешательства по спутниковым снимкам.

Питон-версия скрипта retro_audit.js — та же методика, но числа печатаются
в терминал, чтобы их можно было сразу разбирать и итерировать.

ГЛАВНОЕ: меряем не «стало на X холоднее», а разность разностей —

    эффект = (объект_после − объект_до) − (контроль_после − контроль_до)

Абсолютная температура скачет год от года из-за погоды. Без контрольного
кольца мы бы измерили лето, а не вмешательство.

Запуск:
    .venv/bin/python scripts/gee/retro_audit.py --project <cloud-project-id>
"""

from __future__ import annotations

import argparse
import json
import math
import sys

import ee

# ─────────────────────────────────────────────────────────────────────────────
# Параметры
# ─────────────────────────────────────────────────────────────────────────────

# ⚠️ ПРИБЛИЗИТЕЛЬНЫЙ периметр: Parc de la Senne, фаза 2, квартал Masui–Reine.
# Заменить настоящим из contrat de quartier durable.
PERIMETER_COORDS = [[
    [4.3505, 50.8695],
    [4.3585, 50.8695],
    [4.3585, 50.8745],
    [4.3505, 50.8745],
]]

BEFORE = {"start": "2017-01-01", "end": "2019-12-31", "label": "до 2017–2019"}
AFTER = {"start": "2021-01-01", "end": "2024-12-31", "label": "после 2021–2024"}

SUMMER = (6, 8)          # июнь–август: зимние снимки не говорят ни о кроне, ни о перегреве
CONTROL_INNER_M = 300    # отступ, чтобы не захватить край стройки
CONTROL_OUTER_M = 1200
MAX_CLOUD = 30           # % облачности для отбора сцен
MIN_SCENES = 8           # ниже этого медиана шумная и результату верить нельзя


# ─────────────────────────────────────────────────────────────────────────────
# Коллекции
# ─────────────────────────────────────────────────────────────────────────────

def s2_summer(geom: ee.Geometry, rng: dict) -> ee.ImageCollection:
    """Летний NDVI по Sentinel-2 с маской облаков Cloud Score+."""
    cs_plus = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")

    def to_ndvi(img: ee.Image) -> ee.Image:
        clear = img.select("cs_cdf").gte(0.6)
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("ndvi")
        return ndvi.updateMask(clear).copyProperties(img, ["system:time_start"])

    return (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geom)
        .filterDate(rng["start"], rng["end"])
        .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], "month"))
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD))
        .linkCollection(cs_plus, ["cs_cdf"])
        .map(to_ndvi)
    )


def lst_summer(geom: ee.Geometry, rng: dict) -> ee.ImageCollection:
    """Летняя температура поверхности по Landsat 8/9 Collection 2 Level-2.

    ST_B10 — готовый продукт, выводить ничего не надо: применяем официальные
    коэффициенты и переводим в Цельсий.
    """
    def to_lst(img: ee.Image) -> ee.Image:
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        lst = (
            img.select("ST_B10")
            .multiply(0.00341802).add(149.0).subtract(273.15)
            .rename("lst")
        )
        return lst.updateMask(clear).copyProperties(img, ["system:time_start"])

    l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
    return (
        l8.merge(l9)
        .filterBounds(geom)
        .filterDate(rng["start"], rng["end"])
        .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], "month"))
        .filter(ee.Filter.lt("CLOUD_COVER", MAX_CLOUD))
        .map(to_lst)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Статистика
# ─────────────────────────────────────────────────────────────────────────────

def zonal_mean(img: ee.Image, band: str, geom: ee.Geometry, scale: int):
    """Среднее по зоне. Возвращает None, если в зоне не осталось валидных пикселей."""
    return img.select(band).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=scale,
        maxPixels=int(1e9),
        bestEffort=True,
    ).get(band)


def diff_in_diff(delta_img, band, site, control, scale, unit, title):
    on_site = zonal_mean(delta_img, band, site, scale).getInfo()
    on_ctrl = zonal_mean(delta_img, band, control, scale).getInfo()

    print(f"\n──────── {title} ────────")
    if on_site is None or on_ctrl is None:
        print("  нет валидных пикселей — проверь периметр и облачность")
        return None

    effect = on_site - on_ctrl
    print(f"  внутри периметра:          {on_site:+.3f} {unit}")
    print(f"  контрольное кольцо:        {on_ctrl:+.3f} {unit}")
    print(f"  ЭФФЕКТ (разн. разностей):  {effect:+.3f} {unit}")
    return effect


# ─────────────────────────────────────────────────────────────────────────────
# Главное
# ─────────────────────────────────────────────────────────────────────────────

def load_perimeter(path: str) -> tuple[ee.Geometry, str, float]:
    """Читает GeoJSON-периметр и возвращает геометрию, имя и площадь в гектарах."""
    with open(path) as fh:
        gj = json.load(fh)

    feat = gj["features"][0] if gj.get("type") == "FeatureCollection" else gj
    geom = feat["geometry"]
    name = feat.get("properties", {}).get("name", path)

    rings = ([geom["coordinates"][0]] if geom["type"] == "Polygon"
             else [poly[0] for poly in geom["coordinates"]])

    def ring_area_m2(ring):
        lat0 = sum(p[1] for p in ring) / len(ring)
        k = math.cos(math.radians(lat0))
        s = 0.0
        for i in range(len(ring) - 1):
            x1, y1 = ring[i][0] * k * 111320, ring[i][1] * 110540
            x2, y2 = ring[i + 1][0] * k * 111320, ring[i + 1][1] * 110540
            s += x1 * y2 - x2 * y1
        return abs(s) / 2

    ha = sum(ring_area_m2(r) for r in rings) / 10000
    return ee.Geometry(geom), name, ha


def main() -> int:
    ap = argparse.ArgumentParser(description="Ретро-аудит вмешательства по снимкам")
    ap.add_argument("--project", required=True, help="ID проекта Google Cloud")
    ap.add_argument("--geojson", help="Путь к GeoJSON с настоящим периметром")
    args = ap.parse_args()

    try:
        ee.Initialize(project=args.project)
    except Exception as exc:
        print(f"Не удалось подключиться к Earth Engine: {exc}", file=sys.stderr)
        print("Сначала выполни: .venv/bin/earthengine authenticate", file=sys.stderr)
        return 1

    if args.geojson:
        site, site_name, site_ha = load_perimeter(args.geojson)
    else:
        site = ee.Geometry.Polygon(PERIMETER_COORDS)
        site_name, site_ha = "приблизительный прямоугольник", None

    control = site.buffer(CONTROL_OUTER_M).difference(site.buffer(CONTROL_INNER_M), 1)

    print(f"РЕТРО-АУДИТ · {BEFORE['label']}  →  {AFTER['label']}")
    print(f"Объект: {site_name}")
    if site_ha is not None:
        px = site_ha  # 1 тепловой пиксель Landsat ≈ 100×100 м = 1 га
        print(f"Площадь: {site_ha:.1f} га  ≈  {px:.0f} тепловых пикселей Landsat")
        if site_ha < 5:
            print("⚠️  Меньше ~5 га: для теплового канала это единицы пикселей.")
            print("    LST-результату верить нельзя, NDVI (10 м) остаётся валидным.")
    print("Полож. LST = стало теплее. Полож. NDVI = стало зеленее.")

    # Сначала обеспеченность снимками: без неё числа ниже ничего не значат
    n_s2_before = s2_summer(site, BEFORE).size().getInfo()
    n_s2_after = s2_summer(site, AFTER).size().getInfo()
    n_ls_before = lst_summer(site, BEFORE).size().getInfo()
    n_ls_after = lst_summer(site, AFTER).size().getInfo()

    print("\n──────── Обеспеченность снимками ────────")
    print(f"  Sentinel-2, до / после:  {n_s2_before} / {n_s2_after}")
    print(f"  Landsat,    до / после:  {n_ls_before} / {n_ls_after}")

    thin = [n for n in (n_s2_before, n_s2_after, n_ls_before, n_ls_after) if n < MIN_SCENES]
    if thin:
        print(f"  ⚠️  меньше {MIN_SCENES} сцен в каком-то окне — медиана шумная, "
              "результат ниже считать предварительным")

    ndvi_delta = (
        s2_summer(site, AFTER).median()
        .subtract(s2_summer(site, BEFORE).median())
        .rename("ndvi_delta")
    )
    lst_delta = (
        lst_summer(site, AFTER).median()
        .subtract(lst_summer(site, BEFORE).median())
        .rename("lst_delta")
    )

    lst_effect = diff_in_diff(
        lst_delta, "lst_delta", site, control, 100, "°C", "Температура поверхности")
    ndvi_effect = diff_in_diff(
        ndvi_delta, "ndvi_delta", site, control, 10, "ед. NDVI", "Растительность (NDVI)")

    # ── Вердикт ──────────────────────────────────────────────────────────────
    print("\n──────── Как это читать ────────")
    if lst_effect is None or ndvi_effect is None:
        print("  Расчёт не дал значений. Проверить периметр и окна.")
    elif lst_effect <= -1.0 and ndvi_effect >= 0.05:
        print("  Сигнал есть по обоим показателям — гипотеза verification-first подтверждена.")
    elif abs(lst_effect) < 0.5:
        print("  Тепловой эффект в пределах шума.")
        if ndvi_effect >= 0.03:
            print("  При этом NDVI даёт уверенный сигнал — озеленение измеряется,")
            print("  температура нет. Две вероятные причины, их надо разделить:")
            print("    1) мало тепловых пикселей (нужен объект от ~25 га);")
            print("    2) контрольное кольцо загрязнено — вокруг тоже что-то строили.")
            print("  Следующий шаг: контроль не кольцом, а подобранными секторами.")
    else:
        print("  Промежуточный результат — смотреть вместе с обеспеченностью снимками.")

    if site_ha is None:
        print("\n⚠️  Периметр приблизительный. Настоящий — из OSM или contrat de quartier.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
