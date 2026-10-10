#!/usr/bin/env python3
"""
Данные для отчёта по статье 8 регламента (EU) 2024/1991 — один город.

Что требует закон и что мы кладём в слой
────────────────────────────────────────
· База 2024 — уровни на летний сезон 2024 по каждой единице: зелёность (NDVI),
  крона (`trees`), трава (`grass`), застройка (`built`). Это то, ниже чего
  государству нельзя опуститься к 2030-му.
· Тренд к базе — изменение 2017–2019 → 2021–2024 против подобранного контроля,
  с порогом, посчитанным тем же прогоном (нулевое распределение тех же единиц).
  Показывает, с какой динамикой город пришёл к базе.
· Справедливость — где потери сидят по доходу и плотности. Закон об этом
  молчит, SDG 11.7 и Tree Equity Score — нет.
· Запечатывание — класс `built` против того же контроля, со своим порогом того же прогона:
  где застроили и где раскрыли покрытие сверх шума (как «artificialisé / renaturé» французского
  Mon Diagnostic Artificialisation, но с порогом). Вероятность класса, не гектары.

Что НЕ утверждается
───────────────────
Вероятности классов DW — не доли площади. NDVI — зелёность, не крона. Уровень
сектора — не уровень вмешательства. Освобождён ли город по 45 % — вопрос
делинеации, которой у Бельгии нет. Всё это печатается в отчёте рядом с числами.

Запуск:
    .venv/bin/python scripts/report/article8_data.py --project <id> --city brussels
    .venv/bin/python scripts/report/article8_data.py --city brussels --from-layer
        (без Earth Engine: порог и вердикт застройки из эффектов, уже записанных в слое)
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
from engine.adapters import ADAPTERS
from engine.config import CITIES, CONTROL, QUALITY, SUMMER_MONTHS, WINDOWS
from engine.manifest import Manifest

BASELINE = ("2024-01-01", "2024-12-31")
DW = ["trees", "grass", "built"]


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


def landsat_lst(geom, start, end):
    """Температура поверхности — ВТОРОЙ признак подбора контроля (сводится к 30 м, как весь
    стек). Порог слоя считается тем же прогоном из тех же эффектов, поэтому схема подбора
    здесь и у калибровки прибора совпадать не обязана — но печатается слоем свой порог."""
    def f(img):
        qa = img.select("QA_PIXEL")
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        return (img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15)
                .rename("lst").updateMask(clear))
    l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2"); l9 = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
    return (l8.merge(l9).filterBounds(geom).filterDate(start, end)
            .filter(ee.Filter.calendarRange(SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
            .filter(ee.Filter.lt("CLOUD_COVER", QUALITY["max_cloud_pct"])).map(f).median())


def dw_mean(geom, start, end):
    return (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(geom)
            .filterDate(start, end)
            .filter(ee.Filter.calendarRange(SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
            .select(DW).mean())


def verdict_for(eff, t):
    if t is None or eff is None: return "не калиброван"
    return "рост" if eff > t else ("потеря" if eff < -t else "шум")


def built_trend(comp: list[dict], key: str, t: float) -> dict:
    """Запечатали и раскрыли сверх шума: секторы и жители. `comp` — сопоставимые единицы."""
    up = [r for r in comp if r.get(key) is not None and r[key] > t]
    down = [r for r in comp if r.get(key) is not None and r[key] < -t]
    return {"built_up_sectors": len(up), "built_up_pop": sum(int(r["population"]) for r in up),
            "built_down_sectors": len(down), "built_down_pop": sum(int(r["population"]) for r in down)}


def from_layer(city: str) -> int:
    """Порог и вердикт застройки — ТЕМ ЖЕ прогоном, без Earth Engine.

    Слой хранит эффект застройки каждой единицы против тех же 12 мест, что у зелени; эти эффекты
    и есть нулевое распределение прибора (каждая единица сыграла «вмешательство» один раз).
    Пороги зелени и кроны пересчитываются так же и обязаны сойтись со сводкой — иначе слой
    испорчен, и ничего не пишется."""
    from engine.calibrate import from_effects
    out_dir = Path(f"cities/{city}/layers")
    path, spath = out_dir / "article8_2024.csv", out_dir / "article8_2024_summary.json"
    rows = list(csv.DictReader(path.open()))
    S = json.loads(spath.read_text())
    cal = {k: from_effects(k, [float(r[f"{k}_eff"]) for r in rows if r[f"{k}_eff"] != ""])
           for k in ("ndvi", "trees", "built")}
    for k in ("ndvi", "trees"):
        drift = abs(cal[k].threshold - S["thresholds"][k])
        print(f"{k}: из слоя {cal[k].threshold:.5f}, в сводке {S['thresholds'][k]} (расхождение {drift:.5f})")
        if drift >= 0.0005:
            raise SystemExit(f"{k}: порог из слоя не сходится со сводкой — слой не тот, что считал сводку")
    c = cal["built"]; t = round(c.threshold, 5)
    print(f"built: порог {t} (среднее {c.mean:+.5f}, n = {c.n}, {'несмещён' if c.unbiased else 'СМЕЩЁН'})")
    if not c.unbiased:
        raise SystemExit("built: прибор смещён, порог недействителен")

    fields = list(rows[0].keys())
    if "built_verdict" not in fields:
        fields.insert(fields.index("built_eff") + 1, "built_verdict")
    for r in rows:
        eff = float(r["built_eff"]) if r["built_eff"] != "" else None
        r["built_verdict"] = verdict_for(eff, t) if r["comparable"] == "True" else "контроль несопоставим"
    with path.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields); wr.writeheader(); wr.writerows(rows)

    comp = [{"eff": float(r["built_eff"]), "population": int(float(r["population"] or 0))}
            for r in rows if r["comparable"] == "True" and r["built_eff"] != ""]
    m = Manifest.read(city)
    S["thresholds"]["built"] = t
    S["thresholds_source"]["built"] = c.source_line
    S["thresholds_unbiased"]["built"] = c.unbiased
    S["thresholds_mean"]["built"] = c.mean
    S.setdefault("thresholds_instrument_manifest", {})["built"] = m.layers["built"].threshold if "built" in m.layers else None
    S["trend"].update(built_trend(comp, "eff", t))
    spath.write_text(json.dumps(S, ensure_ascii=False, indent=1))

    e = m.layers["article8_2024"]
    base = e.threshold_source.split("; застройка — ")[0]
    e.threshold_source = f"{base}; застройка — {c.source_line} (порог {t})"
    m.write()
    tr = S["trend"]
    print(f"застроили сверх шума {tr['built_up_sectors']} ({tr['built_up_pop']:,} чел) · "
          f"раскрыли {tr['built_down_sectors']} ({tr['built_down_pop']:,} чел) из {len(comp)} сопоставимых")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--city", choices=list(CITIES), required=True)
    ap.add_argument("--from-layer", action="store_true",
                    help="без Earth Engine: порог и вердикт застройки из эффектов слоя")
    args = ap.parse_args()
    if args.from_layer:
        return from_layer(args.city)
    if not args.project:
        ap.error("--project обязателен для прогона Earth Engine")
    ee.Initialize(project=args.project)

    cfg = CITIES[args.city]; w = WINDOWS["2017_2024"]
    adapter = ADAPTERS[args.city](); units = adapter.units(); income = adapter.income()
    m = Manifest.read(args.city)
    thr = {k: v.threshold for k, v in m.layers.items()}
    print(f"{cfg['display_name']}: {len(units)} единиц, порогов в манифесте {len(thr)}")

    x0, y0, x1, y1 = cfg["bbox"]; box = ee.Geometry.Rectangle([x0, y0, x1, y1])
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(u.geometry), {"id": u.id}) for u in units])

    stack = (s2_ndvi(box, *BASELINE).rename("ndvi_2024")
             .addBands(s2_ndvi(box, *w["before"]).rename("ndvi_b"))
             .addBands(s2_ndvi(box, *w["after"]).rename("ndvi_a"))
             .addBands(dw_mean(box, *BASELINE).rename([c + "_2024" for c in DW]))
             .addBands(dw_mean(box, *w["before"]).rename([c + "_b" for c in DW]))
             .addBands(dw_mean(box, *w["after"]).rename([c + "_a" for c in DW]))
             .addBands(landsat_lst(box, *w["before"]).rename("lst_b")))
    print("один прогон Earth Engine: база 2024 + окна до/после, NDVI, три класса DW, LST «до» для подбора…")
    rows = stack.reduceRegions(fc, ee.Reducer.mean(), 30).getInfo()["features"]

    by_id = {u.id: u for u in units}
    table = []
    for r in rows:
        p = r["properties"]; u = by_id.get(p["id"])
        if not u or u.area_ha < CONTROL["min_area_ha"]: continue
        if any(p.get(k) is None for k in ("ndvi_2024", "ndvi_b", "ndvi_a", "lst_b")): continue
        row = {"id": u.id, "name": u.name, "commune": u.commune, "area_ha": u.area_ha,
               "population": u.population, "density": u.density,
               "income": income.get(u.id), "c": u.centroid,
               "ndvi_2024": p["ndvi_2024"], "ndvi_b": p["ndvi_b"], "ndvi_a": p["ndvi_a"], "lst_b": p["lst_b"],
               "ndvi_d": p["ndvi_a"] - p["ndvi_b"]}
        for c in DW:
            row[c + "_2024"] = p.get(c + "_2024")
            if p.get(c + "_b") is not None and p.get(c + "_a") is not None:
                row[c + "_d"] = p[c + "_a"] - p[c + "_b"]
            else:
                row[c + "_d"] = None
        table.append(row)
    print(f"единиц с полными данными: {len(table)}")

    # один контроль на единицу, все приборы по нему — реализация в движке
    from engine.controls import match_all
    for t in table:
        t["centroid"] = t["c"]
    table = match_all(table, "ndvi_b", "lst_b", ["ndvi_d"] + [c + "_d" for c in DW])

    # Порог — ТЕМ ЖЕ ПРОГОНОМ: нулевое распределение тех же единиц, того же подбора, тех же
    # снимков. До 25.09.2026 порог брался из манифеста, а он был посчитан другой схемой:
    # Брюссель — температура «до» на 100 м вместо 30 м здесь (0,0373 против 0,0345 на той же
    # схеме), Антверпен — подбор по одной зелёности вместо двух признаков (0,0458 против
    # 0,0492). Порог не соответствовал измерению на 7–8 %, и дрейф архива Sentinel-2 между
    # прогонами добавлял своё. Так же уже устроены сезоны мониторинга и аудиты с окнами под проект.
    from engine.calibrate import calibrate
    for t in table:
        t["ndvi_delta"], t["trees_delta"], t["built_delta"] = t["ndvi_d"], t.get("trees_d"), t.get("built_d")
    cal = {k: calibrate(table, k, "ndvi_b", "lst_b") for k in ("ndvi", "trees", "built")}
    thr_manifest = {k: thr.get(k) for k in ("ndvi", "trees", "built")}
    thr = {k: round(c.threshold, 5) for k, c in cal.items()}
    for k, c in cal.items():
        print(f"порог этого прогона, {k}: {c.threshold:.5f} (среднее {c.mean:+.5f}, n = {c.n}, "
              f"{'несмещён' if c.unbiased else 'СМЕЩЁН'}); в манифесте прибора {thr_manifest[k]}")

    def verdict(eff, key):
        return verdict_for(eff, thr.get(key))

    out_dir = Path(f"cities/{args.city}/layers"); out_dir.mkdir(parents=True, exist_ok=True)
    fields = ["id", "name", "commune", "area_ha", "population", "density", "income",
              "ndvi_2024", "trees_2024", "grass_2024", "built_2024",
              "ndvi_eff", "ndvi_verdict", "trees_eff", "trees_verdict",
              "grass_eff", "built_eff", "built_verdict", "gap", "comparable",
              # входы этого прогона — снимок архива: по ним сводку и фон можно пересчитать
              # без Earth Engine, а следующий прогон покажет дрейф числом
              "ndvi_b", "ndvi_a", "ndvi_raw", "lst_b"]
    with (out_dir / "article8_2024.csv").open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields); wr.writeheader()
        for t in table:
            gap = t.get("gap")
            comp = gap is not None and abs(gap) <= CONTROL["max_gap_ndvi"]
            if t.get("ndvi_d_eff") is None:
                continue          # контроль не собрался — единицу не публикуем
            wr.writerow({
                "id": t["id"], "name": t["name"], "commune": t["commune"],
                "area_ha": round(t["area_ha"], 1), "population": t["population"],
                "density": round(t["density"], 1),
                "income": t["income"] if t["income"] is not None else "",
                "ndvi_2024": round(t["ndvi_2024"], 4),
                "trees_2024": round(t["trees_2024"], 4) if t["trees_2024"] is not None else "",
                "grass_2024": round(t["grass_2024"], 4) if t["grass_2024"] is not None else "",
                "built_2024": round(t["built_2024"], 4) if t["built_2024"] is not None else "",
                "ndvi_eff": round(t["ndvi_d_eff"], 4),
                "ndvi_verdict": verdict(t["ndvi_d_eff"], "ndvi") if comp else "контроль несопоставим",
                "trees_eff": round(t["trees_d_eff"], 4) if t.get("trees_d_eff") is not None else "",
                "trees_verdict": (verdict(t.get("trees_d_eff"), "trees") if comp else "контроль несопоставим"),
                "grass_eff": round(t["grass_d_eff"], 4) if t.get("grass_d_eff") is not None else "",
                "built_eff": round(t["built_d_eff"], 4) if t.get("built_d_eff") is not None else "",
                "built_verdict": (verdict(t.get("built_d_eff"), "built") if comp else "контроль несопоставим"),
                "gap": round(gap, 4), "comparable": comp,
                "ndvi_b": round(t["ndvi_b"], 6), "ndvi_a": round(t["ndvi_a"], 6),
                "ndvi_raw": round(t["ndvi_d"], 6), "lst_b": round(t["lst_b"], 4),
            })

    # ── сводка города ─────────────────────────────────────────────────────────
    pop = sum(t["population"] for t in table) or 1
    def wmean(key):
        vals = [(t[key], t["population"]) for t in table if t.get(key) is not None]
        return sum(v * p for v, p in vals) / (sum(p for _, p in vals) or 1)
    table = [t for t in table if t.get("ndvi_d_eff") is not None]
    comp = [t for t in table if t.get("gap") is not None and abs(t["gap"]) <= CONTROL["max_gap_ndvi"]]
    ndvi_loss = [t for t in comp if t["ndvi_d_eff"] < -thr.get("ndvi", 9)]
    ndvi_gain = [t for t in comp if t["ndvi_d_eff"] > thr.get("ndvi", 9)]
    tree_loss = [t for t in comp if t.get("trees_d_eff") is not None and "trees" in thr and t["trees_d_eff"] < -thr["trees"]]
    tree_gain = [t for t in comp if t.get("trees_d_eff") is not None and "trees" in thr and t["trees_d_eff"] > thr["trees"]]

    # справедливость: потери по терцилям дохода
    with_inc = [t for t in comp if t.get("income")]
    with_inc.sort(key=lambda t: t["income"])
    k = len(with_inc) // 3 or 1
    terciles = []
    for i, label in enumerate(("нижний", "средний", "верхний")):
        g = with_inc[i * k:(i + 1) * k] if i < 2 else with_inc[2 * k:]
        if not g: continue
        terciles.append({
            "label": label, "n": len(g),
            "income_median": statistics.median(t["income"] for t in g),
            "ndvi_2024_wmean": sum(t["ndvi_2024"] * t["population"] for t in g) / (sum(t["population"] for t in g) or 1),
            "trees_2024_wmean": sum((t["trees_2024"] or 0) * t["population"] for t in g) / (sum(t["population"] for t in g) or 1),
            "ndvi_eff_mean": statistics.mean(t["ndvi_d_eff"] for t in g),
            "loss_sectors": sum(1 for t in g if t["ndvi_d_eff"] < -thr.get("ndvi", 9)),
            "gain_sectors": sum(1 for t in g if t["ndvi_d_eff"] > thr.get("ndvi", 9)),
        })

    summary = {
        "city": args.city, "display_name": cfg["display_name"],
        "baseline_year": 2024, "window": w["label"],
        "units_total": len(units), "units_measured": len(table), "units_comparable": len(comp),
        "population": pop,
        "baseline": {"ndvi_wmean": wmean("ndvi_2024"), "trees_wmean": wmean("trees_2024"),
                     "grass_wmean": wmean("grass_2024"), "built_wmean": wmean("built_2024")},
        "trend": {
            "ndvi_eff_median": statistics.median(t["ndvi_d_eff"] for t in comp),
            "ndvi_loss_sectors": len(ndvi_loss), "ndvi_loss_pop": sum(t["population"] for t in ndvi_loss),
            "ndvi_gain_sectors": len(ndvi_gain), "ndvi_gain_pop": sum(t["population"] for t in ndvi_gain),
            "trees_loss_sectors": len(tree_loss), "trees_loss_pop": sum(t["population"] for t in tree_loss),
            "trees_gain_sectors": len(tree_gain), "trees_gain_pop": sum(t["population"] for t in tree_gain),
            **built_trend(comp, "built_d_eff", thr["built"]),
        },
        "thresholds": thr,
        "thresholds_source": {k: c.source_line for k, c in cal.items()},
        "thresholds_unbiased": {k: c.unbiased for k, c in cal.items()},
        "thresholds_mean": {k: c.mean for k, c in cal.items()},
        "thresholds_instrument_manifest": thr_manifest,
        "equity_income_terciles": terciles,
        "top_ndvi_loss": [{"id": t["id"], "name": t["name"], "commune": t["commune"],
                           "eff": round(t["ndvi_d_eff"], 4), "population": t["population"],
                           "trees_eff": round(t["trees_d_eff"], 4) if t.get("trees_d_eff") is not None else None}
                          for t in sorted(ndvi_loss, key=lambda t: t["ndvi_d_eff"])[:10]],
        "top_trees_loss": [{"id": t["id"], "name": t["name"], "commune": t["commune"],
                            "eff": round(t["trees_d_eff"], 4), "population": t["population"]}
                           for t in sorted(tree_loss, key=lambda t: t["trees_d_eff"])[:10]],
    }
    (out_dir / "article8_2024_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))

    # Манифест: у слоя свой порог и его происхождение — этот же прогон, а не прибор вообще
    from datetime import date
    from engine.manifest import LayerEntry
    prev = m.layers.get("article8_2024")
    m.add(LayerEntry(
        layer="article8_2024", computed=date.today().isoformat(), n_units=len(table),
        measures=prev.measures if prev else "уровни 2024 и тренд к базе против контроля, по единицам",
        unit=prev.unit if prev else "ед. NDVI; вероятность класса DW",
        method="разность разностей, 12 подобранных единиц по NDVI и LST «до»; порог — нулевое "
               "распределение этого же прогона",
        source=prev.source if prev else "Sentinel-2, Dynamic World, Landsat",
        threshold=thr["ndvi"],
        threshold_source=f"зелёность — {cal['ndvi'].source_line}; крона — {cal['trees'].source_line} "
                         f"(порог {thr['trees']}); застройка — {cal['built'].source_line} (порог {thr['built']})",
        limits=list(prev.limits) if prev else []))
    m.write()

    b = summary["baseline"]; tr = summary["trend"]
    print(f"\n──── База 2024, взвешено по населению ────")
    print(f"  NDVI {b['ndvi_wmean']:.3f} · trees {b['trees_wmean']:.3f} · grass {b['grass_wmean']:.3f} · built {b['built_wmean']:.3f}")
    print(f"──── Тренд к базе ({w['label']}), против контроля ────")
    print(f"  зелень: −{tr['ndvi_loss_sectors']} секторов ({tr['ndvi_loss_pop']:,} чел) · +{tr['ndvi_gain_sectors']} ({tr['ndvi_gain_pop']:,} чел)")
    print(f"  крона:  −{tr['trees_loss_sectors']} секторов ({tr['trees_loss_pop']:,} чел) · +{tr['trees_gain_sectors']} ({tr['trees_gain_pop']:,} чел)")
    print(f"──── Справедливость: терцили дохода ────")
    for t in terciles:
        print(f"  {t['label']:<8} доход {t['income_median']:>7,.0f} €  NDVI-24 {t['ndvi_2024_wmean']:.3f}  крона-24 {t['trees_2024_wmean']:.3f}  "
              f"тренд {t['ndvi_eff_mean']:+.4f}  потерь {t['loss_sectors']}  приростов {t['gain_sectors']}")
    print(f"\n→ {out_dir}/article8_2024.csv + article8_2024_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
