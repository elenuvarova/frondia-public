#!/usr/bin/env python3
"""Сборка дела аудита для проекта с известной датой сдачи — окно под проект, Landsat.

Отличие от `audit_case.py`. Тот собирает дело в стандартном окне 2017–2024 по
Sentinel-2 и берёт контроль из предпосчитанной таблицы секторов. Здесь окно
строится от года сдачи, а для проектов до эры Sentinel-2 прибор — Landsat, и
предпосчитанной таблицы для такого окна нет: она считается этим же прогоном,
на ней же калибруется порог окна.

Что делает движок, а не текст: измерение следа и контроля, подбор контроля,
разность разностей, порог окна, ряд по сезонам. Человеческое — документы,
границы, формулировки — из существующего файла дела не трогается.

⚠️ Второго прибора у таких дел нет: Dynamic World начинается с середины 2015 года,
и для окна «до» 2006–2008 его не существует. Это печатается на странице как
отсутствие подтверждения, а не замалчивается.

    .venv/bin/python scripts/report/audit_case_dated.py --project <gee> --city antwerp \\
        --park "Park Spoor Noord" --slug spoor-noord
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

import ee

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS, dist_m  # noqa: E402
from engine.calibrate import calibrate  # noqa: E402
from engine.config import CITIES, CONTROL, QUALITY, SUMMER_MONTHS  # noqa: E402
from engine.instruments import REGISTRY  # noqa: E402
from engine.instruments.landsat import LEGACY, MODERN, _prep  # noqa: E402

HUMAN = ["title", "name", "one_line", "documents", "cluster", "limits", "verdict_line", "cta"]


def last_full_summer() -> int:
    """Последнее завершённое лето: сезон кончается в августе, в сентябре он уже полный."""
    from datetime import date
    d = date.today()
    return d.year if d.month >= 9 else d.year - 1


def landsat_ndvi(geom, start, end):
    modern = ee.ImageCollection(MODERN[0]).merge(ee.ImageCollection(MODERN[1]))
    legacy = ee.ImageCollection(LEGACY[0]).merge(ee.ImageCollection(LEGACY[1]))

    def win(c):
        return (c.filterBounds(geom).filterDate(start, end)
                .filter(ee.Filter.calendarRange(SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
                .filter(ee.Filter.lt("CLOUD_COVER", QUALITY["max_cloud_pct"])))
    return (win(modern).map(lambda i: _prep(i, "SR_B5", "SR_B4"))
            .merge(win(legacy).map(lambda i: _prep(i, "SR_B4", "SR_B3"))).median())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--city", required=True, choices=list(CITIES))
    ap.add_argument("--park", required=True, help="имя парка в слое park_audit_dated")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--seasons", default="", help="годы ряда через запятую; по умолчанию от конца работ до последнего полного лета")
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    layer = Path(f"cities/{args.city}/layers/park_audit_dated.csv")
    row = next(r for r in csv.DictReader(layer.open()) if r["park"].startswith(args.park))
    bw = tuple(x.strip() for x in row["window"].split("→")[0].split("–"))
    aw = tuple(x.strip() for x in row["window"].split("→")[1].split("–"))
    before = (f"{bw[0]}-01-01", f"{bw[1]}-12-31")
    after = (f"{aw[0]}-01-01", f"{aw[1]}-12-31")
    instr = row["instrument"]
    print(f"{row['project']} · сдан {row['completed_year']} · окно {row['window']} · прибор {instr}")

    parks = json.loads(Path(f"data/perimeters/parks_{args.city}.geojson").read_text())["features"]
    park = next(f for f in parks if f["properties"]["osm"] == row["osm"])
    g = ee.Geometry(park["geometry"])
    c = park["geometry"]["coordinates"]
    while isinstance(c[0][0], list):
        c = c[0]
    cen = (sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c))

    ad = ADAPTERS[args.city]()
    units = ad.units()
    meta = {u.id: u for u in units}
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(u.geometry), {"id": u.id}) for u in units])
    b = CITIES[args.city]["bbox"]
    region = ee.Geometry.Rectangle([b[0], b[1], b[2], b[3]])

    med = landsat_ndvi if instr == "ndvi_landsat" else None
    if med is None:
        print("это дело для Sentinel-2 — используйте audit_case.py", file=sys.stderr)
        return 1
    scale = 30

    print("считаю таблицу секторов и порог этого окна…")
    stack = med(region, *before).rename("nb").addBands(med(region, *after).rename("na"))
    rows = stack.reduceRegions(fc, ee.Reducer.mean(), scale).getInfo()["features"]
    pool = []
    for q in (x["properties"] for x in rows):
        u = meta[q["id"]]
        if q.get("nb") is None or q.get("na") is None or u.area_ha < CONTROL["min_area_ha"]:
            continue
        pool.append({"id": u.id, "name": u.name or u.id, "ndvi_landsat_before": q["nb"], "lst_before": q["nb"],
                     "ndvi_landsat_delta": q["na"] - q["nb"], "centroid": u.centroid,
                     "nb": q["nb"], "d": q["na"] - q["nb"], "c": u.centroid})
    cal = calibrate(pool, "ndvi_landsat", "ndvi_landsat_before", "lst_before")
    print(f"  секторов {cal.n}, порог {cal.threshold:.4f}, среднее {cal.mean:+.5f}, "
          f"{'несмещён' if cal.unbiased else 'СМЕЩЁН'}")

    inst_obj = REGISTRY[instr]
    sb = inst_obj.measure(g, *before)
    sa = inst_obj.measure(g, *after)
    cands = sorted((o for o in pool if dist_m(cen, o["c"]) >= CONTROL["exclusion_m"]),
                   key=lambda o: abs(o["nb"] - sb.value))[:CONTROL["n_controls"]]
    ctrl_nb = statistics.mean(o["nb"] for o in cands)
    ctrl_d = statistics.mean(o["d"] for o in cands)
    eff = (sa.value - sb.value) - ctrl_d
    gap = sb.value - ctrl_nb
    print(f"  след: {sb.value:.3f} → {sa.value:.3f}, сцен {sb.n_scenes}/{sa.n_scenes}; "
          f"эффект {eff:+.4f}, разрыв {gap:+.4f}")

    ctrl_geom = ee.FeatureCollection([ee.Feature(ee.Geometry(meta[o["id"]].geometry)) for o in cands]).geometry()
    seasons = ([int(x) for x in args.seasons.split(",") if x.strip()]
               or list(range(int(row["completed_year"]) + 2, last_full_summer() + 1)))
    series = []
    print("ряд по сезонам (эффект против тех же контролей, база — окно «до»):")
    ctrl_b = inst_obj.measure(ctrl_geom, *before).value
    for y in seasons:
        s = inst_obj.measure(g, f"{y}-01-01", f"{y}-12-31")
        cs = inst_obj.measure(ctrl_geom, f"{y}-01-01", f"{y}-12-31")
        if s.value is None or cs.value is None or ctrl_b is None:
            continue
        e = (s.value - sb.value) - (cs.value - ctrl_b)
        series.append({"season": y, "scenes": s.n_scenes, "site": round(s.value, 3),
                       "control": round(cs.value, 3), "effect": round(e, 3)})
        print(f"   {y}: сцен {s.n_scenes:>2}  след {s.value:.3f}  контроль {cs.value:.3f}  эффект {e:+.3f}")

    key = row["osm"].replace("/", "_")
    computed = {
        "slug": args.slug, "osm": row["osm"], "area_ha": float(row["area_ha"]),
        "window_before": f"{bw[0]}–{bw[1]}", "window_after": f"{aw[0]}–{aw[1]}",
        "instrument_note": ("Прибор — Landsat, 30 м: проект сдан до начала ряда Sentinel-2, "
                            "и другого снимка на окно «до» не существует."),
        "image_note": f"Сцен: {sb.n_scenes} в окне «до», {sa.n_scenes} в окне «после».",
        "calibration_n": str(cal.n),
        "instruments": [{"key": instr, "label": "Зелёность растительности (NDVI, Landsat 30 м)",
                         "before": round(sb.value, 3), "after": round(sa.value, 3), "effect": round(eff, 4),
                         "threshold": round(cal.threshold, 4), "significant": abs(eff) > cal.threshold,
                         "reading": ""}],
        "second_instrument": ("Второго прибора у этого дела нет: Dynamic World начинается с середины 2015 года, "
                              f"а окно «до» здесь {bw[0]}–{bw[1]}. Подтверждения сменой классов покрытия "
                              "предъявить нечем, и это сказано прямо."),
        "controls": [{"id": o["id"], "name": o["name"], "ndvi_before": round(o["nb"], 3),
                      "d_ndvi_raw": round(o["d"], 4), "dist_km": round(dist_m(cen, o["c"]) / 1000, 1)}
                     for o in cands],
        "control_gap": round(gap, 4),
        "timing_rows": [{"window": f"{bw[0]}–{bw[1]}, окно под проект", "scenes": sb.n_scenes,
                         "ndvi_before": round(sb.value, 3), "effect": round(eff, 4), "gap": round(gap, 4)}],
        "images": {"before": f"data/exports/{key}_before.png", "after": f"data/exports/{key}_after.png",
                   "delta": f"data/exports/{key}_delta_relative.png"},
        "over_time": {"threshold_audit": round(cal.threshold, 4), "threshold_season": round(cal.threshold, 4),
                      "base": f"{bw[0]}–{bw[1]}", "seasons": series},
        "_ctrl_d": round(ctrl_d, 4),
    }

    path = Path(f"data/registry/cases/{args.slug}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    case = json.loads(path.read_text()) if path.exists() else {}
    note = (case.get("over_time") or {}).get("note")          # заметку человека к ряду не теряем
    if note:
        computed["over_time"]["note"] = note
    for k, v in computed.items():
        if k == "timing_rows":
            tc = case.setdefault("timing_check", {"why": "", "rows": [], "conclusion": ""})
            tc["rows"] = v
        elif k == "instruments" and case.get("instruments"):
            old = {i["key"]: i.get("reading", "") for i in case["instruments"]}
            for i in v:
                i["reading"] = old.get(i["key"], "")
            case[k] = v
        else:
            case[k] = v
    for k in HUMAN:
        case.setdefault(k, [] if k in ("documents", "cluster", "limits") else "")
    path.write_text(json.dumps(case, ensure_ascii=False, indent=1))
    print(f"→ {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
