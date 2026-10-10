#!/usr/bin/env python3
"""
Все завершённые проекты Beliris против измеренных изменений — без фильтра по домену.

Почему без фильтра
──────────────────
Первый прогон брал только `domaine == "vert"` (19 проектов). Оказалось, что
**Porte de Ninove — сильнейший измеренный эффект во всём Брюсселе (+0,25 NDVI,
built −0,127) — числится как `public`, а не `vert`.**

Ярлык домена отражает, как администрация подшила проект, а не что физически
произошло на земле. Переустройство общественного пространства, которое раскрывает
асфальт и засаживает, — это озеленение независимо от того, в какую папку оно
попало.

Это тот же урок, что и в остальном проекте: не отбирать по названию, а мерить
всё и смотреть, что скажут данные. Так же детектор изменений находит кандидатов
без списка вмешательств, и так же экстракция мер отличает состояние от действия.

Запуск:
    .venv/bin/python scripts/registry/beliris_all_measured.py
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

PROJECTS = Path("data/registry/beliris_projects.json")
PARKS = Path("data/perimeters/parks_brussels.geojson")
AUDIT = Path("data/park_audit_2017_2024.csv")
OUT = Path("data/registry/beliris_measured.csv")

MATCH_RADIUS_M = 500


def dist_m(a, b):
    k = math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * k * 111320, (a[1] - b[1]) * 110540)


def centroid(geom):
    c = geom["coordinates"]
    while isinstance(c[0][0], list):
        c = c[0]
    return sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)


def first_float(v):
    if v is None:
        return None
    try:
        return float(str(v).split("|")[0])
    except ValueError:
        return None


def main() -> int:
    projects = [p for p in json.loads(PROJECTS.read_text())
                if p.get("project_status") == "termine"]
    print(f"завершённых проектов Beliris (все домены): {len(projects)}")
    print("по доменам:", dict(Counter(p["domaine"] for p in projects)), "\n")

    parks = json.loads(PARKS.read_text())["features"]
    park_pts = [(centroid(f["geometry"]), f["properties"]) for f in parks]
    audit = {r["osm"]: r for r in csv.DictReader(AUDIT.open())}

    rows = []
    for p in projects:
        lat, lon = first_float(p.get("lat")), first_float(p.get("long"))
        if lat is None or lon is None:
            continue
        pt = (lon, lat)
        near = min(((dist_m(pt, c), pr) for c, pr in park_pts), key=lambda x: x[0])
        d, pr = near
        if d > MATCH_RADIUS_M:
            continue
        a = audit.get(pr["osm"])
        if not a:
            continue
        rows.append({
            "project": p["cleanTitle"],
            "domaine": p["domaine"],
            "url": p.get("url", ""),
            "park": pr["name"],
            "osm": pr["osm"],
            "area_ha": pr["area_ha"],
            "dist_m": round(d),
            "ndvi_effect": float(a["ndvi_effect"]),
            "verdict": a["verdict"],
            "in_brussels": a.get("in_brussels", "?"),
        })

    rows.sort(key=lambda r: -r["ndvi_effect"])
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"сопоставлено с измеренным парком: {len(rows)}  →  {OUT}")
    print("вердикты:", dict(Counter(r["verdict"] for r in rows)))

    sig = [r for r in rows if r["verdict"] in ("ПОЗЕЛЕНЕЛ", "ПОТЕРЯЛ")]
    print(f"\n──────── Значимые ({len(sig)}) ────────")
    print(f"  {'эффект':>9}  {'домен':<10}{'проект':<44}{'парк':<26}{'м':>5}")
    print("  " + "-" * 98)
    for r in sig:
        print(f"  {r['ndvi_effect']:>+9.4f}  {r['domaine']:<10}"
              f"{r['project'][:42]:<44}{r['park'][:24]:<26}{r['dist_m']:>5}")

    by_dom = Counter(r["domaine"] for r in sig)
    print(f"\nзначимые по доменам: {dict(by_dom)}")
    if by_dom and by_dom.most_common(1)[0][0] != "vert":
        print("⚠️  Значимые эффекты приходят НЕ только из домена «vert» —")
        print("    фильтровать проекты по ярлыку категории нельзя.")

    # ── КЛАСТЕРЫ: один узел — несколько проектов ─────────────────────────────
    # Сопоставление по близости раздаёт ОДИН эффект многим проектам. Считать
    # так цену эффекта нельзя: пять проектов «купили» бы один и тот же +0,25.
    # Но за этим стоит настоящий факт: вмешательства приходят КЛАСТЕРАМИ, и
    # приписать эффект одной бюджетной строке часто невозможно по существу.
    # Правильная единица — узел и сумма бюджетов всех проектов вокруг него.
    clusters: dict[str, list[dict]] = {}
    for r in rows:
        clusters.setdefault(r["osm"], []).append(r)
    multi = {k: v for k, v in clusters.items() if len(v) > 1}

    print(f"\n──────── Кластеры: узлов с несколькими проектами {len(multi)} ────────")
    for osm, group in sorted(multi.items(), key=lambda x: -abs(x[1][0]["ndvi_effect"]))[:8]:
        g0 = group[0]
        print(f"\n  {g0['park'][:40]}  {g0['ndvi_effect']:+.4f}  ({g0['verdict']})")
        for r in sorted(group, key=lambda x: x["dist_m"]):
            print(f"      {r['dist_m']:>4} м  {r['domaine']:<10}{r['project'][:52]}")

    print("\n⚠️  Эффект узла — СОВОКУПНЫЙ результат всех проектов кластера.")
    print("    Приписывать его одному проекту нельзя. Для цены эффекта считать")
    print("    сумму бюджетов кластера против изменения узла.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
