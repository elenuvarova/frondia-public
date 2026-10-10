#!/usr/bin/env python3
"""
Аудит старых проектов Beliris прибором Landsat — с окнами под проект и порогом под окно.

Зачем
─────
Вывод «реставрации не видны» был снят: все восемь реставраций сдались до окна
«до» (2017), и мы сравнивали «после» с «после». Landsat даёт ряд с 1984-го,
`windows_for_completion(year, data_from=2000)` строит окно под каждый проект —
гипотезу можно наконец ПРОВЕРИТЬ, а не объявить.

Порог — под окно, не общий
──────────────────────────
Порог Landsat 0,0325 калиброван на 2017–2019 → 2021–2024. Для окна 2009–2011 →
2014–2017 шум может быть другим (Landsat 5/7 против 8). Поэтому на каждом окне
все 686 секторов по очереди играют плацебо — нулевое распределение и порог
считаются для ЭТОГО окна из того же прогона. Это бесплатно и честно.

Оговорки
────────
· 30 м: объект в 1 га — 11 пикселей; Landsat ловит ~60 % сигнала на мелких
  объектах. Парки < 3 га — предварительно.
· Сопоставление проект→парк — по координате в 500 м (кластерная проблема).
· Реставрация может ничего не менять в NDVI по построению — это и проверяем.

Запуск:  .venv/bin/python scripts/gee/audit_beliris_landsat.py --project <id>
"""
from __future__ import annotations
import argparse, csv, json, statistics, sys
from collections import defaultdict
from pathlib import Path
import ee
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS, dist_m
from engine.audit import windows_for_completion
from engine.calibrate import calibrate
from engine.config import CONTROL
from engine.instruments import REGISTRY
from engine.instruments.landsat import LEGACY, MODERN, _prep
from engine.config import QUALITY, SUMMER_MONTHS

OUT = Path("data/registry/beliris_landsat_audit.csv")


def landsat_median(geom, start, end):
    modern = ee.ImageCollection(MODERN[0]).merge(ee.ImageCollection(MODERN[1]))
    legacy = ee.ImageCollection(LEGACY[0]).merge(ee.ImageCollection(LEGACY[1]))
    def win(c):
        return (c.filterBounds(geom).filterDate(start, end)
                .filter(ee.Filter.calendarRange(SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
                .filter(ee.Filter.lt("CLOUD_COVER", QUALITY["max_cloud_pct"])))
    return (win(modern).map(lambda i: _prep(i, "SR_B5", "SR_B4"))
            .merge(win(legacy).map(lambda i: _prep(i, "SR_B4", "SR_B3"))).median())


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--project", required=True)
    ap.add_argument("--max-year", type=int, default=2016, help="сданные не позже — те, что Sentinel не берёт")
    args = ap.parse_args(); ee.Initialize(project=args.project)

    dated = {p["title"]: p for p in json.loads(Path("data/registry/beliris_dated.json").read_text())}
    matched = {}
    for r in csv.DictReader(Path("data/registry/beliris_measured.csv").open()):
        matched.setdefault(r["project"], r)
    parks = {f["properties"]["osm"]: f for f in json.loads(Path("data/perimeters/parks_brussels.geojson").read_text())["features"]}
    ad = ADAPTERS["brussels"](); units = ad.units()
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(u.geometry), {"id": u.id}) for u in units])
    meta = {u.id: u for u in units}
    bxl = ee.Geometry.Rectangle([4.23, 50.76, 4.50, 50.94])

    todo = []
    for title, p in dated.items():
        y = p.get("end_year"); m = matched.get(title)
        if not y or y > args.max_year or not m or m.get("in_brussels") == "no": continue
        w = windows_for_completion(y, data_from=2000)
        if not w: continue
        todo.append((title, y, m["osm"], w))
    print(f"проектов Beliris ≤ {args.max_year} с датой, парком и окном: {len(todo)}")
    by_win = defaultdict(list)
    for t in todo: by_win[(t[3]["before"], t[3]["after"])].append(t)
    print(f"различных окон: {len(by_win)}\n")

    lnd = REGISTRY["ndvi_landsat"]; rows_out = []
    for (bw, aw), items in sorted(by_win.items()):
        label = f"{bw[0][:4]}–{bw[1][:4]} → {aw[0][:4]}–{aw[1][:4]}"
        stack = landsat_median(bxl, *bw).rename("nb").addBands(landsat_median(bxl, *aw).rename("na"))
        rows = stack.reduceRegions(fc, ee.Reducer.mean(), 30).getInfo()["features"]
        table = []
        for r in rows:
            q = r["properties"]; u = meta[q["id"]]
            if q.get("nb") is None or q.get("na") is None or u.area_ha < CONTROL["min_area_ha"]: continue
            table.append({"id": u.id, "name": u.name, "ndvi_landsat_before": q["nb"], "lst_before": q["nb"],
                          "ndvi_landsat_delta": q["na"] - q["nb"], "centroid": u.centroid})
        cal = calibrate(table, "ndvi_landsat", "ndvi_landsat_before", "lst_before")
        print(f"окно {label}: секторов {cal.n}, порог {cal.threshold:.4f}, среднее {cal.mean:+.5f} {'(несмещён)' if cal.unbiased else '⚠ смещён'}")
        n_rng = max(t["ndvi_landsat_before"] for t in table) - min(t["ndvi_landsat_before"] for t in table)
        for title, y, osm, w in items:
            park = parks[osm]; g = ee.Geometry(park["geometry"])
            b = lnd.measure(g, *bw); a = lnd.measure(g, *aw)
            if b.value is None or a.value is None:
                print(f"   {title[:44]:<46} нет данных"); continue
            c = park["geometry"]["coordinates"]
            while isinstance(c[0][0], list): c = c[0]
            cen = (sum(p[0] for p in c)/len(c), sum(p[1] for p in c)/len(c))
            cands = sorted((o for o in table if dist_m(cen, o["centroid"]) >= CONTROL["exclusion_m"]),
                           key=lambda o: abs(o["ndvi_landsat_before"] - b.value))[:CONTROL["n_controls"]]
            ctrl_nb = statistics.mean(o["ndvi_landsat_before"] for o in cands)
            eff = (a.value - b.value) - statistics.mean(o["ndvi_landsat_delta"] for o in cands)
            gap = b.value - ctrl_nb
            if abs(gap) > CONTROL["max_gap_ndvi"]: verdict = "контроль несопоставим"
            elif eff > cal.threshold: verdict = "ПОЗЕЛЕНЕЛ"
            elif eff < -cal.threshold: verdict = "ПОТЕРЯЛ"
            else: verdict = "шум"
            small = " (мелкий для 30 м)" if park["properties"]["area_ha"] < 3 else ""
            print(f"   {title[:44]:<46} {y}  {park['properties']['name'].split(' - ')[0][:22]:<24}{park['properties']['area_ha']:>6.1f} га  "
                  f"сцен {b.n_scenes}/{a.n_scenes}  {eff:+.4f}  {verdict}{small}")
            rows_out.append({"project": title, "end_year": y, "park": park["properties"]["name"], "osm": osm,
                             "area_ha": park["properties"]["area_ha"], "window": label, "scenes_before": b.n_scenes,
                             "scenes_after": a.n_scenes, "ndvi_before": round(b.value, 4), "ndvi_after": round(a.value, 4),
                             "effect": round(eff, 4), "threshold": round(cal.threshold, 4), "gap": round(gap, 4), "verdict": verdict})
    with OUT.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys())); wr.writeheader(); wr.writerows(rows_out)
    from collections import Counter
    print(f"\nвердикты: {dict(Counter(r['verdict'] for r in rows_out))}\n→ {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
