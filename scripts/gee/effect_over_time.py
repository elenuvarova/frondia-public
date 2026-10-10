#!/usr/bin/env python3
"""
Устойчивость эффекта во времени: посезонная разность разностей.

Вопрос
──────
Аудит говорит «+0,25 за 2021–2024». Он не говорит, КОГДА эффект появился и
ДЕРЖИТСЯ ли он. Парк, позеленевший в 2021-м и побуревший к 2024-му, — другая
история, чем парк, который держит уровень. Для планирования важно и то, через
сколько лет после сдачи эффект виден: это «время до эффекта», которого нет ни
у кого из соседей по рынку.

Что считает
───────────
База — окно до работ (для Ninove 2017–2018). Дальше каждое лето 2020…2025
отдельно: NDVI объекта и средний NDVI тех же 12 контрольных секторов, что на
странице аудита. Эффект сезона = (объект_сезон − объект_база) − (контроль_сезон
− контроль_база).

Оговорка про порог: аудитный порог 0,0373 калиброван на окне «после» в четыре
лета. Один сезон шумнее — мониторинг на окне 3→1 дал 0,0312 при базе из трёх
лет, здесь база из двух. Печатаем оба порога и не выдаём посезонный вердикт
за аудитный.

Запуск:
    .venv/bin/python scripts/gee/effect_over_time.py --project <id> --case ninove
"""
from __future__ import annotations
import argparse, csv, json, statistics, sys
from pathlib import Path
import ee
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.instruments import REGISTRY
from engine.adapters import ADAPTERS
from engine.manifest import Manifest


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--project", required=True)
    ap.add_argument("--case", default="ninove")
    ap.add_argument("--seasons", default=None, help="годы ряда «2020-2026»; по умолчанию — до последнего полного лета")
    ap.add_argument("--city", default="brussels"); ap.add_argument("--base", default="2016-2018", help="окно базы, годы")
    args = ap.parse_args(); ee.Initialize(project=args.project)

    C = json.loads(Path(f"data/registry/cases/{args.case}.json").read_text())
    parks = json.loads(Path(f"data/perimeters/parks_{args.city}.geojson").read_text())["features"]
    site = next(f for f in parks if f["properties"]["osm"] == C["osm"])
    units = {u.id: u for u in ADAPTERS[args.city]().units()}
    ctrl_ids = [c["id"] for c in C["controls"]]
    base = C["timing_check"]["rows"][-1]["window"]          # «2016, до работ» / «2017–2019, стандарт»
    # база до работ: для Ninove работы шли 2017–2019 → берём 2016–2018 как компромисс
    # между «до работ» (2016, 2 сцены) и «достаточно сцен»
    by0, by1 = args.base.split("-")
    b0, b1 = f"{by0}-01-01", f"{by1}-12-31"
    # порог аудита — самого дела (его схема подбора, тот же прогон; audit_case.py), прибора — только если дела ещё нет
    own = next((i["threshold"] for i in C.get("instruments", []) if i["key"] == "ndvi"), None)
    thr_audit = own if own is not None else Manifest.read(args.city).layers["ndvi"].threshold
    ndvi = REGISTRY["ndvi"]
    g_site = ee.Geometry(site["geometry"])
    fc_ctrl = ee.FeatureCollection([ee.Feature(ee.Geometry(units[i].geometry), {"id": i}) for i in ctrl_ids])

    def ctrl_mean(start, end):
        img = ndvi._collection(g_site.buffer(20000), start, end).median()
        rows = img.reduceRegions(fc_ctrl, ee.Reducer.mean(), 10).getInfo()["features"]
        vals = [r["properties"].get("mean") for r in rows if r["properties"].get("mean") is not None]
        return statistics.mean(vals) if vals else None

    sb = ndvi.measure(g_site, b0, b1); cb = ctrl_mean(b0, b1)
    print(f"{C['name']} · база {b0[:4]}–{b1[:4]}: объект {sb.value:.3f} ({sb.n_scenes} сцен), контроль {cb:.3f}")
    season_thr = {"brussels": 0.0312, "antwerp": 0.0477}.get(args.city, 0.031)
    print(f"порог аудита (4 лета) {thr_audit:.4f} · сезонный порог мониторинга {season_thr:.4f}\n")
    from datetime import date
    last_summer = date.today().year if date.today().month >= 9 else date.today().year - 1
    if args.seasons:
        y0, y1 = map(int, args.seasons.split("-"))
    else:
        prev = C.get("over_time", {}).get("seasons") or [{"season": int(by1) + 2}]
        y0, y1 = prev[0]["season"], last_summer
    print(f"{'сезон':<7}{'сцен':>5}{'объект':>9}{'контроль':>10}{'эффект':>9}  чтение")
    out = []
    for y in range(y0, y1 + 1):
        s = ndvi.measure(g_site, f"{y}-01-01", f"{y}-12-31"); c = ctrl_mean(f"{y}-01-01", f"{y}-12-31")
        if s.value is None or c is None:
            print(f"{y:<7}{'—':>5}"); continue
        eff = (s.value - sb.value) - (c - cb)
        note = ("сверх аудитного порога" if eff > thr_audit else
                "сверх сезонного, ниже аудитного" if eff > season_thr else "в шуме")
        print(f"{y:<7}{s.n_scenes:>5}{s.value:>9.3f}{c:>10.3f}{eff:>+9.4f}  {note}")
        out.append({"season": y, "scenes": s.n_scenes, "site": round(s.value, 4),
                    "control": round(c, 4), "effect": round(eff, 4)})
    series = {"base": [b0, b1], "site_base": sb.value, "ctrl_base": cb, "threshold_audit": thr_audit, "seasons": out}
    p = Path(f"data/registry/cases/{args.case}_over_time.json")
    p.write_text(json.dumps(series, ensure_ascii=False, indent=1))
    # ряд — сразу в дело: раньше его переносили руками. Заметку человека не трогаем.
    case_path = Path(f"data/registry/cases/{args.case}.json")
    C = json.loads(case_path.read_text())
    note = (C.get("over_time") or {}).get("note")
    C["over_time"] = {**series, **({"note": note} if note else {})}
    case_path.write_text(json.dumps(C, ensure_ascii=False, indent=1))
    first = next((o["season"] for o in out if o["effect"] > thr_audit), None)
    held = all(o["effect"] > thr_audit for o in out if o["season"] >= (first or 9999))
    print(f"\nпервый сезон сверх аудитного порога: {first}  ·  держится до конца ряда: {held}")
    print(f"→ {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
