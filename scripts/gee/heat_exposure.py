#!/usr/bin/env python3
"""Тепловая нагрузка секторов: состояние, а не изменение.

Важное разграничение, без которого этот слой был бы нарушением собственного
правила. Проект **отказался измерять охлаждение от вмешательств**: порог
значимости для температуры вышел 1,32 °C, больше реалистичного эффекта парка,
и утверждать «озеленение охладило квартал» на этих данных нельзя.

Здесь температура используется иначе — как **состояние**: где в городе жарче
летом. Для этого шум многолетних медиан не мешает: мы не вычитаем контроль и не
ищем эффект, а ранжируем секторы между собой в один и тот же период. Слой
отвечает на вопрос «кому тень нужнее всего», а не «помогла ли тень».

Считается: летняя медиана температуры поверхности (Landsat 8/9, тепловой канал)
за последние три года, плюс превышение над медианой города — то, что обычно
называют островом тепла.

    .venv/bin/python scripts/gee/heat_exposure.py --project <gee> --city brussels
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
from engine.config import CITIES, QUALITY, SUMMER_MONTHS  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402

YEARS = (2022, 2025)          # окно состояния: последние доступные летние сезоны
MODERN = ("LANDSAT/LC08/C02/T1_L2", "LANDSAT/LC09/C02/T1_L2")


def lst_median(geom, y0: int, y1: int):
    """Летняя медиана температуры поверхности в °C, маска облаков по QA_PIXEL."""
    def prep(img):
        qa = img.select("QA_PIXEL")
        # Ровно та же маска, что в слое ст. 8: биты 3 (облако) и 4 (тень).
        # Добавленный бит 1 (расширенное облако) вычищал все пиксели до единого.
        clear = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
        lst = img.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15)
        return lst.rename("lst").updateMask(clear)

    coll = ee.ImageCollection(MODERN[0]).merge(ee.ImageCollection(MODERN[1]))
    return (coll.filterBounds(geom)
            .filterDate(f"{y0}-01-01", f"{y1}-12-31")
            .filter(ee.Filter.calendarRange(SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
            .filter(ee.Filter.lt("CLOUD_COVER", QUALITY["max_cloud_pct"]))
            .map(prep).median())


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
    b = CITIES[city]["bbox"]
    region = ee.Geometry.Rectangle([b[0], b[1], b[2], b[3]])
    print(f"{city}: секторов {len(units)}, окно {YEARS[0]}–{YEARS[1]}, летние медианы")

    img = lst_median(region, *YEARS)
    rows = img.reduceRegions(fc, ee.Reducer.mean(), 30).getInfo()["features"]
    got = []
    for f in rows:
        p = f["properties"]
        # У изображения из ОДНОЙ полосы Earth Engine называет результат "mean",
        # а не именем полосы. В слое ст. 8 полос было несколько, поэтому там
        # имена сохранялись, и разница не всплывала.
        val = p.get("lst", p.get("mean"))
        if val is None:
            continue
        u = meta[p["id"]]
        got.append({"id": u.id, "name": u.name or u.id, "pop": u.population,
                    "area_ha": u.area_ha, "lst": float(val)})
    if not got:
        print("нет валидных измерений", file=sys.stderr)
        return 1

    city_med = statistics.median(g["lst"] for g in got)
    for g in got:
        g["excess"] = g["lst"] - city_med

    out = Path(f"cities/{city}/layers/heat_2022_2025.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "name", "population", "area_ha", "lst_summer_c", "excess_over_city_c"])
        for g in sorted(got, key=lambda x: -x["excess"]):
            w.writerow([g["id"], g["name"], g["pop"], round(g["area_ha"], 2),
                        round(g["lst"], 3), round(g["excess"], 3)])

    pop = sum(g["pop"] for g in got)
    wmean = sum(g["lst"] * g["pop"] for g in got) / pop if pop else 0
    hot = [g for g in got if g["excess"] >= 2]
    print(f"  измерено секторов: {len(got)}, медиана города {city_med:.2f} °C, "
          f"взвешено по населению {wmean:.2f} °C")
    print(f"  секторов теплее города на 2 °C и более: {len(hot)}, "
          f"жителей {sum(g['pop'] for g in hot):,}".replace(",", " "))
    print("  самые тёплые:")
    for g in sorted(got, key=lambda x: -x["excess"])[:5]:
        print(f"    {g['id']} {g['name'][:26]:<28} {g['lst']:.1f} °C  ({g['excess']:+.1f} к медиане)")

    # пересечение с кроной: кому жарко и при этом нет тени
    a8 = Path(f"cities/{city}/layers/worldcover_2021.csv")
    cross = ""
    if a8.exists():
        canopy = {r["id"]: float(r["wc_trees"]) for r in csv.DictReader(a8.open())}
        pairs = [(g["lst"], canopy[g["id"]]) for g in got if g["id"] in canopy]
        if len(pairs) > 30:
            xs, ys = zip(*pairs)
            r = statistics.correlation(xs, ys)
            both_bad = [g for g in got
                        if g["id"] in canopy and g["excess"] >= 1 and canopy[g["id"]] < 0.10]
            cross = (f"корреляция температуры с долей кроны r = {r:.3f}; "
                     f"секторов одновременно жарких (+1 °C) и без кроны (< 10 %): {len(both_bad)}")
            print(f"\n  {cross}")
            print(f"    в них живёт {sum(g['pop'] for g in both_bad):,} человек".replace(",", " "))

    m = Manifest.read(city)
    m.add(LayerEntry(
        layer="heat_2022_2025", computed=date.today().isoformat(), n_units=len(got),
        measures="летняя температура поверхности сектора и превышение над медианой города",
        unit="°C",
        method=f"медиана летних снимков {YEARS[0]}–{YEARS[1]}, тепловой канал Landsat 8/9, маска облаков QA_PIXEL",
        source="Landsat Collection 2 Level 2 (ST_B10), секторы и население Statbel",
        threshold=None,
        threshold_source=("порога нет: слой описывает состояние, а не изменение. Для изменения "
                          "температуры порог измерен и равен 1,32 °C — больше реалистичного "
                          "эффекта вмешательства, поэтому эффект охлаждения проект не измеряет"),
        limits=["температура ПОВЕРХНОСТИ, а не воздуха: это разные величины",
                "многолетняя летняя медиана смешивает съёмки при разной влажности почвы",
                "слой пригоден для ранжирования секторов между собой, но не для «стало холоднее»",
                cross or "сверка с кроной не проводилась"]))
    m.write()
    print(f"→ {out} · слоёв в манифесте {len(m.layers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
