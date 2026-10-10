#!/usr/bin/env python3
"""Правило 3-30-300 по секторам: признанная норма, посчитанная на наших данных.

Правило предложено Сесилом Конейнендейком в 2021 году и стало общей рамкой в
городском лесоводстве: из каждого жилища должно быть видно **3 дерева**, в
районе должно быть **30 % кроны**, до ближайшего парка — не более **300 метров**.
Исследование 862 европейских городов (Nature Communications) показало, что
полностью норме соответствует менее 15 % населения.

Что считаем и чего не считаем:

  **30 % кроны — считаем.** Доля площади сектора под деревьями по ESA WorldCover
  (жёсткая классификация 10 м). Именно доля площади, а не вероятность класса:
  наш инструмент Dynamic World для процентов не годится и systematically
  занижает в лесистых секторах — это показала сверка (r = 0,76 по рангу,
  но 0,10 против 0,31 по величине).

  **300 м до парка — считаем.** Доля площади сектора в пределах 300 м от
  именованного парка OSM площадью ≥ 1 га. Считается растром расстояний в Earth
  Engine, не по центроиду: сектор может наполовину лежать у парка, наполовину нет.

  **3 дерева из окна — НЕ считаем и не притворяемся.** Для этого нужен обзор от
  каждого здания, а не сводка по сектору. Пункт печатается как неизмеренный.

    .venv/bin/python scripts/gee/rule_3_30_300.py --project <gee> --city brussels
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

import ee

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.config import CITIES  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402

CANOPY_TARGET = 0.30      # 30 % кроны в районе
PARK_DIST_M = 300         # 300 м до парка
PARK_MIN_HA = 1.0         # парк считается парком от гектара — наш же порог следа


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--city", default="brussels", choices=list(CITIES))
    args = ap.parse_args()
    ee.Initialize(project=args.project)
    city = args.city

    ad = ADAPTERS[city]()
    units = ad.units()
    meta = {u.id: u for u in units}
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(u.geometry), {"id": u.id}) for u in units])

    parks_path = Path(f"data/perimeters/parks_{city}.geojson")
    feats = [f for f in json.loads(parks_path.read_text())["features"]
             if f["properties"].get("area_ha", 0) >= PARK_MIN_HA
             and f["properties"].get("in_brussels", True) is not False]
    print(f"{city}: секторов {len(units)}, парков ≥ {PARK_MIN_HA:.0f} га — {len(feats)}")
    parks = ee.FeatureCollection([ee.Feature(ee.Geometry(f["geometry"])) for f in feats])

    # Растр расстояния до ближайшего парка: 1 внутри 300 м, 0 дальше.
    near = (parks.distance(searchRadius=3000, maxError=10)
            .lte(PARK_DIST_M).unmask(0).rename("near_park"))
    trees = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map").eq(10).rename("canopy")
    rows = trees.addBands(near).reduceRegions(fc, ee.Reducer.mean(), 10).getInfo()["features"]

    out = Path(f"cities/{city}/layers/rule_3_30_300.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    got = []
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "name", "population", "canopy_share", "near_park_share",
                    "passes_30", "passes_300", "passes_both"])
        for f in rows:
            p = f["properties"]
            u = meta[p["id"]]
            if p.get("canopy") is None:
                continue
            can, near_s = float(p["canopy"]), float(p.get("near_park") or 0)
            p30, p300 = can >= CANOPY_TARGET, near_s >= 0.5
            # Шесть знаков, а не четыре: при округлении до 0,3000 признак
            # выполнения расходился со значением на границе — та же ловушка,
            # что была с сектором ровно на пороге в атласе.
            w.writerow([u.id, u.name or "", u.population, round(can, 6), round(near_s, 6),
                        int(p30), int(p300), int(p30 and p300)])
            got.append({"id": u.id, "name": u.name or u.id, "pop": u.population,
                        "can": can, "near": near_s, "p30": p30, "p300": p300})

    pop = sum(g["pop"] for g in got)
    def share(pred):
        return sum(g["pop"] for g in got if pred(g)) / pop if pop else 0
    s30, s300, both, neither = (share(lambda g: g["p30"]), share(lambda g: g["p300"]),
                                share(lambda g: g["p30"] and g["p300"]),
                                share(lambda g: not g["p30"] and not g["p300"]))
    print(f"  секторов измерено: {len(got)}, население {pop:,}".replace(",", " "))
    print(f"  живёт при кроне ≥ 30 %:            {s30:.1%}")
    print(f"  живёт в 300 м от парка ≥ 1 га:     {s300:.1%}")
    print(f"  выполняются оба измеримых пункта:  {both:.1%}")
    print(f"  не выполняется ни один:            {neither:.1%}")
    print("  третий пункт (3 дерева из окна) не измерен: нужен обзор от здания")

    m = Manifest.read(city)
    m.add(LayerEntry(
        layer="rule_3_30_300", computed=date.today().isoformat(), n_units=len(got),
        measures=("выполнение измеримой части правила 3-30-300: доля кроны в секторе "
                  "и доля площади в 300 м от парка ≥ 1 га"),
        unit="доля площади и признак выполнения",
        method=(f"крона — доля площади класса «деревья» ESA WorldCover 10 м, порог {CANOPY_TARGET:.0%}; "
                f"близость — растр расстояния до парков, порог {PARK_DIST_M} м, сектор засчитывается "
                "при половине площади в радиусе"),
        source="ESA WorldCover v200 (2021), парки OpenStreetMap ≥ 1 га, секторы и население Statbel",
        threshold=None,
        threshold_source="порога значимости нет: это норма из литературы, а не измеренное изменение",
        limits=["пункт «3 дерева из окна» не измерен: нужен обзор от каждого здания",
                "парк определяется как именованный полигон OSM ≥ 1 га — частные и закрытые сады не отделены",
                "крона по эпохе 2021 года, а не на текущий сезон",
                "сектор засчитывается целиком при половине площади в радиусе: граница условна"]))
    m.write()
    print(f"→ {out} · слоёв в манифесте {len(m.layers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
