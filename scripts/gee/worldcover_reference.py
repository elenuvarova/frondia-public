#!/usr/bin/env python3
"""Официальная крона: ESA WorldCover 10 м как независимая сверка нашего измерения.

Зачем. Регламент (EU) 2024/1991 предписывает считать по данным Copernicus, а
VVSG официально спросила, как извлечь из них проценты и площади. Мы меряем крону
классификатором Dynamic World — это средняя вероятность класса, а не доля
площади, и величину нельзя читать как проценты территории. ESA WorldCover даёт
именно **долю площади**: жёсткая классификация 10 м, класс 10 — древесный покров.

Слой отвечает сразу на два вопроса:
  · сколько процентов сектора занято деревьями по официальному продукту;
  · насколько наш прибор согласуется с ним — корреляция и расхождения поимённо.

⚠️ Это НЕ замена нашему измерению и не «правильный ответ». WorldCover существует
на 2020 и 2021 годы, то есть не годится ни для базы 2024-го, ни для изменений;
у него один снимок вместо ряда и жёсткие классы вместо вероятностей. Он полезен
ровно тем, что независим: если два разных продукта согласны, доверия больше.

    .venv/bin/python scripts/gee/worldcover_reference.py --project <gee> --city brussels
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from datetime import date
from pathlib import Path

import ee

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.config import CITIES  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402

# ESA WorldCover v200 = эпоха 2021. Классы: 10 деревья, 20 кустарник, 30 трава,
# 40 пашня, 50 застройка, 60 голая земля, 80 вода.
COLLECTION = "ESA/WorldCover/v200"
CLASSES = {"wc_trees": 10, "wc_shrub": 20, "wc_grass": 30, "wc_built": 50, "wc_bare": 60}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--city", default="brussels", choices=list(CITIES))
    args = ap.parse_args()
    ee.Initialize(project=args.project)
    city = args.city

    ad = ADAPTERS[city]()
    units = ad.units()
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(u.geometry), {"id": u.id}) for u in units])
    meta = {u.id: u for u in units}
    print(f"{city}: секторов {len(units)}, продукт {COLLECTION} (эпоха 2021)")

    wc = ee.ImageCollection(COLLECTION).first().select("Map")
    # Доля площади каждого класса = среднее по маске класса.
    bands = [wc.eq(code).rename(name) for name, code in CLASSES.items()]
    stack = bands[0]
    for b in bands[1:]:
        stack = stack.addBands(b)
    rows = stack.reduceRegions(fc, ee.Reducer.mean(), 10).getInfo()["features"]

    out = Path(f"cities/{city}/layers/worldcover_2021.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    got = []
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "name", "area_ha", "population", *CLASSES])
        for f in rows:
            p = f["properties"]
            u = meta[p["id"]]
            if p.get("wc_trees") is None:
                continue
            vals = [round(float(p.get(k) or 0), 4) for k in CLASSES]
            w.writerow([u.id, u.name or "", round(u.area_ha, 2), u.population, *vals])
            got.append({"id": u.id, "name": u.name or u.id, "pop": u.population,
                        **{k: float(p.get(k) or 0) for k in CLASSES}})
    print(f"  измерено секторов: {len(got)}")

    pop = sum(g["pop"] for g in got)
    wmean = {k: sum(g[k] * g["pop"] for g in got) / pop for k in CLASSES} if pop else {}
    print("  доли площади, взвешено по населению:")
    for k, v in wmean.items():
        print(f"    {k:<10} {v:.3f}")

    # сверка с нашим измерением кроны
    a8p = Path(f"cities/{city}/layers/article8_2024.csv")
    corr_txt = "слоя ст. 8 нет — сверка не проводилась"
    if a8p.exists():
        ours = {r["id"]: float(r["trees_2024"]) for r in csv.DictReader(a8p.open())
                if r.get("trees_2024") not in ("", None)}
        pairs = [(ours[g["id"]], g["wc_trees"]) for g in got if g["id"] in ours]
        if len(pairs) > 30:
            xs, ys = zip(*pairs)
            r = statistics.correlation(xs, ys)
            corr_txt = f"корреляция с нашим trees: r = {r:.3f} на {len(pairs)} секторах"
            print(f"\n  {corr_txt}")
            print(f"    наш trees (средняя вероятность): {statistics.mean(xs):.3f}")
            print(f"    WorldCover (доля площади):       {statistics.mean(ys):.3f}")
            diffs = sorted(((g["wc_trees"] - ours[g["id"]], g) for g in got if g["id"] in ours),
                           key=lambda t: -abs(t[0]))
            print("    сильнейшие расхождения:")
            for d, g in diffs[:5]:
                print(f"      {g['id']} {g['name'][:24]:<26} наш {ours[g['id']]:.3f} · "
                      f"WorldCover {g['wc_trees']:.3f} · разница {d:+.3f}")

    m = Manifest.read(city)
    m.add(LayerEntry(
        layer="worldcover_2021", computed=date.today().isoformat(), n_units=len(got),
        measures="доля площади сектора по классам ESA WorldCover: деревья, кустарник, трава, застройка, голая земля",
        unit="доля площади 0–1",
        method="жёсткая классификация 10 м, доля класса = среднее по маске класса внутри сектора",
        source=f"{COLLECTION} (ESA WorldCover, эпоха 2021)",
        threshold=None,
        threshold_source="порога нет: это независимая сверка состояния, а не изменение против контроля",
        limits=["эпоха 2021: ни для базы 2024 года, ни для измерения изменений не годится",
                "жёсткие классы вместо вероятностей — сравнивать с нашим trees можно по рангу, не по величине",
                "один снимок вместо ряда: сезонная и годовая изменчивость не усредняется",
                corr_txt]))
    m.write()
    print(f"→ {out} · слоёв в манифесте {len(m.layers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
