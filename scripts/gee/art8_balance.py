#!/usr/bin/env python3
"""
Баланс после базы 2024 — в гектарах (фаза 2c, пункт 2).

Зачем
─────
Статья 8 считает чистую потерю ПЛОЩАДИ зелени и кроны против базы 2024 года, а атлас до сих пор
считал секторы. Французский Mon Diagnostic Artificialisation показывает каждой коммуне три столбика:
застроено, возвращено природе, чистый итог — в гектарах. Здесь то же для зелени, кроны и застройки,
но с порогом шума: гектары, изменившиеся сверх того, что делали 12 подобранных мест.

Как
───
· Гектары требуют жёсткого класса: вероятность класса Dynamic World — не доля площади (крона по
  WorldCover втрое больше). Поэтому на каждое лето — среднее вероятностей за июнь–август и класс-победитель
  в каждом пикселе 10 м; доля пикселей класса в секторе × площадь сектора = гектары.
· Зелень — прочтение ст. 3(20), как в официальном слое (CLCplus 2,3,4,5,6,8,10): деревья, трава,
  кустарник, затопляемая растительность и вода; пашня (crops) — нет. Крона — деревья. Застройка — built.
· База — лето 2024 (база закона), сезоны — 2025 и 2026. Один прогон Earth Engine на город: все три лета,
  NDVI и температура поверхности 2024 для подбора.
· Эффект сектора — изменение его доли минус среднее изменение 12 мест, самых похожих в 2024 году по
  зелёности и температуре (та же схема, что в слое ст. 8), не ближе 1,5 км. Порог — нулевое распределение
  ЭТОГО ЖЕ прогона, свой на каждый класс и сезон. Гектары сверх шума = эффект × площадь сектора.
· Чистый баланс = гектары прироста сверх шума − гектары потерь сверх шума, по сопоставимым секторам.
  Рядом печатается сырой итог по городу (без вычитания мест) — с оговоркой, что в нём и смена класса
  от лета к лету, и общегородской сдвиг.

Чего это НЕ говорит
───────────────────
Не официальная площадь по CLCplus/WVL (их на 2025–2026 нет) и не кадастр: это гектары так, как их
классифицирует Dynamic World. Один сезон шумнее четырёхлетнего окна. Причину изменения даёт документ.

Запуск:
    .venv/bin/python scripts/gee/art8_balance.py --project <id> --city brussels
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from datetime import date
from pathlib import Path

import ee

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.calibrate import from_effects  # noqa: E402
from engine.config import CITIES, CONTROL, QUALITY, SUMMER_MONTHS  # noqa: E402
from engine.controls import match_all  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402

BASE = 2024
SEASONS = (2025, 2026)
DW_BANDS = ["water", "trees", "grass", "flooded_vegetation", "crops", "shrub_and_scrub", "built", "bare", "snow_and_ice"]
GREEN_IDX = [0, 1, 2, 3, 5]          # вода, деревья, трава, затопляемая, кустарник — ст. 3(20); пашня (4) — нет
CLASSES = {"green": "зелень (ст. 3(20))", "trees": "крона", "built": "застройка"}


def summer(y: int) -> tuple[str, str]:
    return f"{y}-{SUMMER_MONTHS[0]:02d}-01", f"{y}-{SUMMER_MONTHS[1] + 1:02d}-01"


def dw_hard(geom, y: int):
    """Класс-победитель среднего лета; три бинарные полосы и число снимков."""
    col = (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(geom).filterDate(*summer(y)))
    label = col.select(DW_BANDS).mean().toArray().arrayArgmax().arrayGet([0])
    green = label.remap(GREEN_IDX, [1] * len(GREEN_IDX), 0)
    return (green.rename(f"green_{y}").addBands(label.eq(1).rename(f"trees_{y}"))
            .addBands(label.eq(6).rename(f"built_{y}"))), col.size()


def s2_ndvi(geom, y: int):
    cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")

    def f(img):
        return (img.normalizedDifference(["B8", "B4"]).rename("ndvi")
                .updateMask(img.select("cs_cdf").gte(QUALITY["cloud_score_plus_min"])))
    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(geom).filterDate(*summer(y))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", QUALITY["max_cloud_pct"]))
            .linkCollection(cs, ["cs_cdf"]).map(f).median())


def landsat_lst(geom, y: int):
    def f(img):
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        return img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("lst").updateMask(clear)
    l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2"); l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
    return (l8.merge(l9).filterBounds(geom).filterDate(*summer(y))
            .filter(ee.Filter.lt("CLOUD_COVER", QUALITY["max_cloud_pct"])).map(f).median())


def verdict(eff, t, comparable):
    if not comparable:
        return "контроль несопоставим"
    if eff is None:
        return "не измерено"
    return "рост" if eff > t else ("потеря" if eff < -t else "шум")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--city", choices=list(CITIES), required=True)
    args = ap.parse_args()
    ee.Initialize(project=args.project)
    cfg = CITIES[args.city]
    x0, y0, x1, y1 = cfg["bbox"]
    box = ee.Geometry.Rectangle([x0, y0, x1, y1])
    units = ADAPTERS[args.city]().units()
    by_id = {u.id: u for u in units}
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(u.geometry), {"id": u.id}) for u in units])

    stack, sizes = None, {}
    for y in (BASE, *SEASONS):
        img, n = dw_hard(box, y)
        stack = img if stack is None else stack.addBands(img)
        sizes[y] = n
    stack = stack.addBands(s2_ndvi(box, BASE).rename("ndvi_24")).addBands(landsat_lst(box, BASE).rename("lst_24"))
    scenes = {y: n.getInfo() for y, n in sizes.items()}
    print(f"{cfg['display_name']}: {len(units)} единиц; снимков Dynamic World по летам {scenes}")
    rows = stack.reduceRegions(fc, ee.Reducer.mean(), 10).getInfo()["features"]

    table = []
    for r in rows:
        p = r["properties"]; u = by_id[p["id"]]
        if u.area_ha < CONTROL["min_area_ha"]:
            continue
        need = ["ndvi_24", "lst_24"] + [f"{k}_{y}" for k in CLASSES for y in (BASE, *SEASONS)]
        if any(p.get(k) is None for k in need):
            continue
        t = {"id": u.id, "name": u.name or "", "commune": u.commune or "", "area_ha": u.area_ha,
             "population": u.population, "centroid": u.centroid, "ndvi_24": p["ndvi_24"], "lst_24": p["lst_24"]}
        for k in CLASSES:
            for y in (BASE, *SEASONS):
                t[f"{k}_{y}"] = p[f"{k}_{y}"]
            for s in SEASONS:
                t[f"{k}_d{s}"] = p[f"{k}_{s}"] - p[f"{k}_{BASE}"]
        table.append(t)
    print(f"единиц с полными данными: {len(table)}")

    keys = [f"{k}_d{s}" for s in SEASONS for k in CLASSES]
    scored = match_all(table, "ndvi_24", "lst_24", keys)
    cal = {}
    for s in SEASONS:
        for k in CLASSES:
            effs = [r[f"{k}_d{s}_eff"] for r in scored if r[f"{k}_d{s}_eff"] is not None]
            c = from_effects(f"{k}_{s}", effs)
            cal[(k, s)] = c
            print(f"  {s} {k:<6} порог {c.threshold:.5f} (среднее {c.mean:+.5f}, n = {c.n}, "
                  f"{'несмещён' if c.unbiased else 'СМЕЩЁН'})")

    layers = ROOT / f"cities/{args.city}/layers"
    summary = {"city": args.city, "computed": date.today().isoformat(), "base": BASE, "seasons": {},
               "scenes": scenes, "min_scenes": QUALITY["min_scenes"],
               # меньше снимков за лето — композит шумный, итог сезона предварительный (как qualify() в аудите)
               "preliminary": {str(y): n < QUALITY["min_scenes"] for y, n in scenes.items()}, "green_classes": "water, trees, grass, flooded_vegetation, shrub_and_scrub (not crops)",
               "units_measured": len(scored)}
    m = Manifest.read(args.city)
    for s in SEASONS:
        thr = {k: round(cal[(k, s)].threshold, 5) for k in CLASSES}
        out = []
        for r in scored:
            comp = r.get("gap") is not None and r["comparable"]
            row = {"id": r["id"], "name": r["name"], "commune": r["commune"], "area_ha": round(r["area_ha"], 2),
                   "population": r["population"]}
            for k in CLASSES:
                eff = r[f"{k}_d{s}_eff"]
                v = verdict(eff, thr[k], comp)
                row.update({
                    f"{k}_{BASE}_ha": round(r[f"{k}_{BASE}"] * r["area_ha"], 2),
                    f"{k}_{s}_ha": round(r[f"{k}_{s}"] * r["area_ha"], 2),
                    f"{k}_raw_ha": round(r[f"{k}_d{s}"] * r["area_ha"], 2),
                    f"{k}_eff": round(eff, 7) if eff is not None else "",
                    f"{k}_eff_ha": round(eff * r["area_ha"], 2) if eff is not None else "",
                    f"{k}_verdict": v,
                })
            row["gap"] = round(r["gap"], 4) if r.get("gap") is not None else ""
            row["comparable"] = comp
            out.append(row)
        with (layers / f"art8_balance_{s}.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(out[0]), lineterminator="\n")
            w.writeheader(); w.writerows(out)

        block = {"thresholds": thr,
                 "thresholds_source": {k: cal[(k, s)].source_line for k in CLASSES},
                 "thresholds_unbiased": {k: cal[(k, s)].unbiased for k in CLASSES},
                 "units_comparable": sum(1 for r in out if r["comparable"])}
        for k in CLASSES:
            lost = [r for r in out if r[f"{k}_verdict"] == "потеря"]
            gain = [r for r in out if r[f"{k}_verdict"] == "рост"]
            block[k] = {
                "lost_sectors": len(lost), "gained_sectors": len(gain),
                "lost_ha": round(sum(r[f"{k}_eff_ha"] for r in lost), 1),
                "gained_ha": round(sum(r[f"{k}_eff_ha"] for r in gain), 1),
                "raw_base_ha": round(sum(r[f"{k}_{BASE}_ha"] for r in out), 1),
                "raw_season_ha": round(sum(r[f"{k}_{s}_ha"] for r in out), 1),
            }
            block[k]["net_ha"] = round(block[k]["gained_ha"] + block[k]["lost_ha"], 1)
            block[k]["raw_net_ha"] = round(block[k]["raw_season_ha"] - block[k]["raw_base_ha"], 1)
        summary["seasons"][str(s)] = block
        print(f"\n── {BASE} → {s} ──")
        for k in CLASSES:
            b = block[k]
            print(f"  {CLASSES[k]:<20} потеряно сверх шума {b['lost_ha']:>8} га ({b['lost_sectors']}) · прирост "
                  f"{b['gained_ha']:>7} га ({b['gained_sectors']}) · чисто {b['net_ha']:>7} га · сырой итог {b['raw_net_ha']} га")

        m.add(LayerEntry(
            layer=f"art8_balance_{s}", computed=date.today().isoformat(), n_units=len(out),
            measures=f"баланс после базы {BASE}: зелень (ст. 3(20)), крона и застройка в гектарах, лето {BASE} против "
                     f"лета {s}, против 12 подобранных мест; чистый итог сверх шума",
            unit="га; доля площади (жёсткий класс Dynamic World)",
            method="класс-победитель средних вероятностей Dynamic World за лето, 10 м; доля класса × площадь сектора; "
                   "разность разностей против 12 мест, похожих в 2024 по NDVI и LST; порог — нулевое распределение "
                   "этого же прогона, свой на класс",
            source="Dynamic World V1; Sentinel-2 NDVI и Landsat LST 2024 для подбора; секторы и население Statbel",
            threshold=thr["green"],
            threshold_source="; ".join(f"{CLASSES[k]} — {cal[(k, s)].source_line} (порог {thr[k]})" for k in CLASSES),
            limits=["гектары так, как их классифицирует Dynamic World, — не CLCplus/WVL и не кадастр",
                    "один сезон против одного — шумнее четырёхлетнего окна",
                    "сырой итог по городу включает смену класса от лета к лету и общегородской сдвиг",
                    "причина изменения — из документов, не из снимка"]))
    (layers / "art8_balance_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    m.write()
    print(f"\n→ {layers}/art8_balance_{{{','.join(map(str, SEASONS))}}}.csv + art8_balance_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
