#!/usr/bin/env python3
"""
Мониторинг вперёд: что изменилось в городе за один сезон.

Вопрос
──────
Не «сработало ли вмешательство», а «где в этом сезоне зелень ушла сверх шума».
Закон требует замер раз в шесть лет, PlanIT Geo продаёт раз в два, спутник
даёт ряд бесплатно — мы меряем ежегодно. О потере надо знать ДО 2030-го.

Почему это тот же движок
────────────────────────
Скользящая база (три предыдущих лета) против одного сезона, разность
разностей против подобранного контроля. Каждый сектор по очереди — плацебо,
значит нулевое распределение считается в том же прогоне. Порог из аудита
(0,0373) сюда переносить НЕЛЬЗЯ: окно «после» — один сезон вместо четырёх,
шум выше. Порог берётся из этого же распределения.

Запуск:
    .venv/bin/python scripts/gee/monitor_season.py --project <id> --season 2024
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from pathlib import Path

import ee

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from engine.audit import annual_windows
from engine.calibrate import calibrate, percentile
from engine.config import CITIES, CONTROL, QUALITY, SUMMER_MONTHS  # noqa: F401
from engine.adapters import ADAPTERS

SECTORS = Path("data/brussels_sectors.geojson")


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
    ap = argparse.ArgumentParser(description="Мониторинг одного сезона")
    ap.add_argument("--project", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--city", choices=list(CITIES), default="brussels")
    args = ap.parse_args()

    w = annual_windows(args.season)
    if not w:
        print("базе не хватает лет Sentinel-2 для этого сезона")
        return 1
    print(f"МОНИТОРИНГ · {args.city} · {w['label']}\n")

    ee.Initialize(project=args.project)
    cfg = CITIES[args.city]; x0, y0, x1, y1 = cfg["bbox"]
    bxl = ee.Geometry.Rectangle([x0, y0, x1, y1])
    # единицы из адаптера города — геометрия, население, имена; один источник
    units_city = ADAPTERS[args.city]().units()
    feats = [{"geometry": u.geometry, "properties": {"id": u.id, "name_fr": u.name, "area_ha": u.area_ha,
              "population": u.population, "centroid_lon": u.centroid[0], "centroid_lat": u.centroid[1]}}
             for u in units_city]
    fc = ee.FeatureCollection([
        ee.Feature(ee.Geometry(f["geometry"]), {"id": f["properties"]["id"]})
        for f in feats])

    stack = (s2_ndvi(bxl, *w["before"]).rename("nb")
             .addBands(s2_ndvi(bxl, *w["after"]).rename("na")))
    print(f"считаю NDVI по {len(feats)} секторам, один прогон…")
    rows = stack.reduceRegions(fc, ee.Reducer.mean(), 30).getInfo()["features"]

    meta = {f["properties"]["id"]: f["properties"] for f in feats}
    units = []
    for r in rows:
        p, m = r["properties"], meta[r["properties"]["id"]]
        if p.get("nb") is None or p.get("na") is None:
            continue
        if (m.get("area_ha") or 0) < CONTROL["min_area_ha"]:
            continue
        units.append({
            "id": p["id"], "name": m.get("name_fr") or m.get("name_nl") or "",
            "area_ha": m["area_ha"], "population": m.get("population") or 0,
            "ndvi_before": p["nb"], "lst_before": p["nb"],
            "ndvi_delta": p["na"] - p["nb"],
            "centroid": (m["centroid_lon"], m["centroid_lat"]),
        })

    # калибровка на этом же окне — порог аудита сюда не переносится
    cal = calibrate(units, "ndvi", "ndvi_before", "lst_before")
    print(cal.describe())
    print(f"несмещён: {cal.unbiased}\n")
    # калибровка сезона — рядом со слоем, чтобы пакет брал порог из прогона, а не из рук
    Path(f"data/monitoring_{args.city}_{args.season}_calibration.json").write_text(json.dumps({
        "city": args.city, "season": args.season, "window": w["label"], "n": cal.n,
        "mean": cal.mean, "sd": cal.sd, "threshold": cal.threshold, "unbiased": cal.unbiased,
        "source": f"нулевое распределение мониторинга, окно {w['label']}, {args.city}",
    }, ensure_ascii=False, indent=1))

    # эффект каждого сектора против подобранного контроля — ОДНА реализация в движке
    from engine.controls import match_all
    scored = []
    for r in match_all(units, "ndvi_before", "lst_before", ["ndvi_delta"]):
        if r["ndvi_delta_eff"] is None:
            continue
        scored.append({**r, "effect": r["ndvi_delta_eff"]})

    thr = cal.threshold
    ok = [s for s in scored if s["comparable"]]
    lost = sorted([s for s in ok if s["effect"] < -thr], key=lambda s: s["effect"])
    gained = sorted([s for s in ok if s["effect"] > thr], key=lambda s: -s["effect"])
    refused = len(scored) - len(ok)

    print(f"──────── Сезон {args.season}: порог {thr:.4f} ────────")
    print(f"  секторов: {len(scored)}, контроль несопоставим: {refused}")
    print(f"  ПОТЕРЯЛИ сверх порога: {len(lost)}   жителей: {sum(s['population'] for s in lost):,}")
    print(f"  прибавили сверх порога: {len(gained)}   жителей: {sum(s['population'] for s in gained):,}\n")

    # ── Подтверждение вторым прибором ────────────────────────────────────────
    # Урок первого прогона (сезон 2024): из трёх сильнейших NDVI-потерь одна была
    # стройкой (built +0,075), одна — противоречила Dynamic World (trees и grass
    # выросли), одна — не подтвердилась ничем. Потеря за ОДИН сезон публикуется
    # только при согласии двух приборов. Пороги DW — из манифеста, не с потолка.
    from engine.manifest import Manifest
    from engine.instruments import REGISTRY
    thr_dw = {k: v.threshold for k, v in Manifest.read(args.city).layers.items()}
    geom_by_id = {f["properties"]["id"]: f["geometry"] for f in feats}

    def corroborate(sid):
        g = ee.Geometry(geom_by_id[sid])
        d = {}
        for cls in ("trees", "built"):
            inst = REGISTRY[cls]
            b = inst.measure(g, *w["before"]).value
            a = inst.measure(g, *w["after"]).value
            d[cls] = (a - b) if (a is not None and b is not None) else None
        if d["built"] is not None and d["built"] > thr_dw["built"]:
            return "СТРОЙКА", d
        if d["trees"] is not None and d["trees"] < -thr_dw["trees"]:
            return "ПОТЕРЯ КРОНЫ", d
        return "не подтверждено", d

    print("  Потери — то, о чём региону надо знать до 2030-го (с проверкой вторым прибором):")
    print(f"    {'эффект':>8}  {'жителей':>8}  {'га':>5}  {'сектор':<12}{'название':<24}{'вердикт':<16}Δtrees  Δbuilt")
    for s in lost:   # ВСЕ потери сверх порога, не только сильнейшие: иначе «не проверено» — вина скрипта
        label, d = corroborate(s["id"])
        s["dw_label"] = label; s["dw_trees"] = d["trees"]; s["dw_built"] = d["built"]
        t = f"{d['trees']:+.3f}" if d["trees"] is not None else "  —  "
        b = f"{d['built']:+.3f}" if d["built"] is not None else "  —  "
        print(f"    {s['effect']:+.4f}  {s['population']:>8,}  {s['area_ha']:>5.0f}  "
              f"{s['id']:<12}{s['name'][:22]:<24}{label:<16}{t}  {b}")
    confirmed = [s for s in lost if s.get("dw_label") == "ПОТЕРЯ КРОНЫ"]
    print(f"\n  Подтверждённых потерь кроны: {len(confirmed)} из {len(lost)} проверенных.")
    print("  Только они идут в отчёт. Стройка — отдельная строка, «не подтверждено» — не публикуется.")

    out = Path(f"data/monitoring_{args.city}_{args.season}.csv")
    with out.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["id", "name", "area_ha", "population",
                                            "ndvi_before", "ndvi_delta", "effect",
                                            "gap", "comparable", "dw_label",
                                            "dw_trees", "dw_built"])
        wr.writeheader()
        for s in sorted(scored, key=lambda x: x["effect"]):
            wr.writerow({k: (round(s[k], 4) if isinstance(s.get(k), float) else s.get(k, ""))
                         for k in wr.fieldnames})
    audit_thr = thr_dw.get("ndvi")
    print(f"\n→ {out}   (порог сезона {thr:.4f}, аудитный {audit_thr:.4f} — не сравнивать)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
