#!/usr/bin/env python3
"""
Ретро-аудит с ПОДОБРАННЫМ контролем вместо кольца.

Зачем это вместо retro_audit.py
───────────────────────────────
Первый прогон на Tour et Taxis показал: контрольное кольцо 300–1200 м вокруг
объекта остыло СИЛЬНЕЕ самого объекта. Причина не в шуме — весь квартал
перестраивался в тот же период, то есть кольцо забито чужими вмешательствами.

Здесь контроль строится иначе: из 724 статистических секторов Брюсселя
выбираются те, что до вмешательства были максимально похожи на объект по
растительности и температуре, и при этом лежат достаточно далеко, чтобы не
попасть в ту же стройку.

    эффект = (объект_после − объект_до) − (контроль_после − контроль_до)

Запуск:
    .venv/bin/python scripts/gee/retro_audit_matched.py \
        --project <cloud-project-id> \
        --geojson data/perimeters/tour_et_taxis.geojson
"""

from __future__ import annotations

import argparse
import json
import math
import sys

import ee

SECTORS_PATH = "data/brussels_sectors.geojson"

BEFORE = {"start": "2017-01-01", "end": "2019-12-31", "label": "до 2017–2019"}
AFTER = {"start": "2021-01-01", "end": "2024-12-31", "label": "после 2021–2024"}

SUMMER = (6, 8)
MAX_CLOUD = 30
N_CONTROLS = 12              # сколько секторов взять в контроль
EXCLUSION_M = 1500           # ближе этого к объекту сектора не берём — риск той же стройки
MATCH_SCALE_NDVI = 30        # для подбора хватает грубее, чем для измерения
MATCH_SCALE_LST = 100


# ── коллекции ────────────────────────────────────────────────────────────────

def s2_ndvi(geom, rng):
    cs_plus = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")

    def to_ndvi(img):
        clear = img.select("cs_cdf").gte(0.6)
        return (img.normalizedDifference(["B8", "B4"]).rename("ndvi")
                .updateMask(clear).copyProperties(img, ["system:time_start"]))

    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geom).filterDate(rng["start"], rng["end"])
            .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], "month"))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD))
            .linkCollection(cs_plus, ["cs_cdf"]).map(to_ndvi).median())


def landsat_lst(geom, rng):
    def to_lst(img):
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        lst = (img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15)
               .rename("lst"))
        return lst.updateMask(clear).copyProperties(img, ["system:time_start"])

    l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
    return (l8.merge(l9).filterBounds(geom)
            .filterDate(rng["start"], rng["end"])
            .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], "month"))
            .filter(ee.Filter.lt("CLOUD_COVER", MAX_CLOUD))
            .map(to_lst).median())


# ── вспомогательное ──────────────────────────────────────────────────────────

def load_site(path):
    gj = json.load(open(path))
    feat = gj["features"][0] if gj.get("type") == "FeatureCollection" else gj
    geom = feat["geometry"]
    name = feat.get("properties", {}).get("name", path)

    rings = ([geom["coordinates"][0]] if geom["type"] == "Polygon"
             else [p[0] for p in geom["coordinates"]])

    def area(ring):
        lat0 = sum(p[1] for p in ring) / len(ring)
        k = math.cos(math.radians(lat0))
        s = sum(ring[i][0] * k * 111320 * (ring[i + 1][1] * 110540)
                - ring[i + 1][0] * k * 111320 * (ring[i][1] * 110540)
                for i in range(len(ring) - 1))
        return abs(s) / 2

    return ee.Geometry(geom), name, sum(area(r) for r in rings) / 10000


def mean_of(img, band, geom, scale):
    v = img.select(band).reduceRegion(
        ee.Reducer.mean(), geom, scale=scale, maxPixels=int(1e9), bestEffort=True
    ).get(band)
    return v


# ── главное ──────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Ретро-аудит с подобранным контролем")
    ap.add_argument("--project", required=True)
    ap.add_argument("--geojson", required=True, help="Периметр вмешательства")
    ap.add_argument("--controls", type=int, default=N_CONTROLS)
    args = ap.parse_args()

    try:
        ee.Initialize(project=args.project)
    except Exception as exc:
        print(f"Earth Engine недоступен: {exc}", file=sys.stderr)
        return 1

    site, site_name, site_ha = load_site(args.geojson)
    print(f"РЕТРО-АУДИТ С ПОДОБРАННЫМ КОНТРОЛЕМ · {BEFORE['label']} → {AFTER['label']}")
    print(f"Объект: {site_name}")
    print(f"Площадь: {site_ha:.1f} га ≈ {site_ha:.0f} тепловых пикселей Landsat\n")

    # 1. Характеристики объекта ДО вмешательства
    brussels = ee.Geometry.Rectangle([4.23, 50.76, 4.50, 50.94])
    ndvi_before_img = s2_ndvi(brussels, BEFORE)
    lst_before_img = landsat_lst(brussels, BEFORE)

    site_ndvi_before = ee.Number(mean_of(ndvi_before_img, "ndvi", site, MATCH_SCALE_NDVI))
    site_lst_before = ee.Number(mean_of(lst_before_img, "lst", site, MATCH_SCALE_LST))
    s_nb, s_lb = site_ndvi_before.getInfo(), site_lst_before.getInfo()
    print(f"Объект ДО: NDVI {s_nb:.3f} · LST {s_lb:.2f} °C")

    # 2. Те же характеристики для всех 724 секторов
    sectors_gj = json.load(open(SECTORS_PATH))
    sectors = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f["geometry"]), {
            "id": f["properties"]["id"],
            "name": f["properties"].get("name_fr") or f["properties"].get("name_nl") or "",
            "area_ha": f["properties"].get("area_ha", 0),
        })
        for f in sectors_gj["features"]
    ])

    print(f"Считаю характеристики ДО по {sectors.size().getInfo()} секторам…")
    stacked = ndvi_before_img.select("ndvi").addBands(lst_before_img.select("lst"))
    stats = stacked.reduceRegions(
        collection=sectors, reducer=ee.Reducer.mean(), scale=MATCH_SCALE_LST
    )
    rows = stats.getInfo()["features"]

    # 3. Отбраковка: слишком близкие, слишком мелкие, без данных
    site_centroid = site.centroid(1).coordinates().getInfo()

    def dist_m(lon, lat):
        k = math.cos(math.radians(lat))
        return math.hypot((lon - site_centroid[0]) * k * 111320,
                          (lat - site_centroid[1]) * 110540)

    candidates = []
    for r in rows:
        p = r["properties"]
        if p.get("ndvi") is None or p.get("lst") is None:
            continue
        if p.get("area_ha", 0) < site_ha * 0.5:      # слишком мелкий сектор — шумный
            continue


        candidates.append(p | {"geometry": r["geometry"]})

    # локальные центроиды — дешевле, чем гонять в GEE
    def local_centroid(geom):
        coords = geom["coordinates"]
        while isinstance(coords[0][0], list):
            coords = coords[0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return sum(lons) / len(lons), sum(lats) / len(lats)

    kept = []
    for c in candidates:
        lon, lat = local_centroid(c["geometry"])
        d = dist_m(lon, lat)
        if d < EXCLUSION_M:
            continue
        kept.append(c | {"dist_m": d})

    print(f"Кандидатов после отбраковки: {len(kept)} "
          f"(исключены ближе {EXCLUSION_M} м и мельче {site_ha * 0.5:.1f} га)")

    # 4. Подбор по похожести ДО: нормируем обе оси и берём ближайших
    ndvis = [c["ndvi"] for c in kept]
    lsts = [c["lst"] for c in kept]
    ndvi_sd = (max(ndvis) - min(ndvis)) or 1
    lst_sd = (max(lsts) - min(lsts)) or 1

    for c in kept:
        c["match_dist"] = math.hypot((c["ndvi"] - s_nb) / ndvi_sd,
                                     (c["lst"] - s_lb) / lst_sd)
    kept.sort(key=lambda c: c["match_dist"])
    matched = kept[:args.controls]

    print(f"\n──────── Контрольные секторы ({len(matched)}) ────────")
    for c in matched:
        print(f"  {c['id']:<12} {c['name'][:24]:<24} "
              f"NDVI {c['ndvi']:.3f}  LST {c['lst']:.2f}  "
              f"{c['dist_m'] / 1000:.1f} км")

    control = ee.FeatureCollection([
        ee.Feature(ee.Geometry(c["geometry"])) for c in matched
    ]).geometry()

    # 5. Измерение ПОСЛЕ и разность разностей
    ndvi_after_img = s2_ndvi(brussels, AFTER)
    lst_after_img = landsat_lst(brussels, AFTER)

    def did(before_img, after_img, band, scale, unit, title):
        sb = ee.Number(mean_of(before_img, band, site, scale))
        sa = ee.Number(mean_of(after_img, band, site, scale))
        cb = ee.Number(mean_of(before_img, band, control, scale))
        ca = ee.Number(mean_of(after_img, band, control, scale))
        vals = ee.List([sb, sa, cb, ca]).getInfo()
        if any(v is None for v in vals):
            print(f"\n──────── {title} ────────\n  нет данных")
            return None
        sb, sa, cb, ca = vals
        d_site, d_ctrl = sa - sb, ca - cb
        effect = d_site - d_ctrl
        print(f"\n──────── {title} ────────")
        print(f"  объект:   {sb:+.3f} → {sa:+.3f}   изменение {d_site:+.3f} {unit}")
        print(f"  контроль: {cb:+.3f} → {ca:+.3f}   изменение {d_ctrl:+.3f} {unit}")
        print(f"  ЭФФЕКТ:   {effect:+.3f} {unit}")
        return effect

    lst_eff = did(lst_before_img, lst_after_img, "lst", 100, "°C", "Температура поверхности")
    ndvi_eff = did(ndvi_before_img, ndvi_after_img, "ndvi", 10, "ед. NDVI", "Растительность")

    print("\n──────── Итог ────────")
    if site_ha < 25:
        print(f"  Объект {site_ha:.0f} га — для теплового канала это мало "
              "(нужно от ~25 га).")
        print("  NDVI при этом валиден: Sentinel-2 даёт 10 м.")
    if ndvi_eff is not None and ndvi_eff >= 0.03:
        print(f"  Озеленение подтверждено: {ndvi_eff:+.3f} NDVI против контроля.")
    if lst_eff is not None:
        print(f"  Температура: {lst_eff:+.3f} °C "
              f"({'охлаждение' if lst_eff < -0.5 else 'в пределах шума'}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
