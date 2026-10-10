#!/usr/bin/env python3
"""
Сбор реестра проектов Beliris и сверка с измеренными изменениями по паркам.

Зачем это появилось
───────────────────
Сильнейший измеренный эффект во всём Брюсселе (Parc de la Porte de Ninove,
+0,25) оказался ВНЕ нашего реестра: это проект Beliris, а не contrat de quartier.
Значит 98 квартальных контрактов покрывают лишь часть вмешательств, и реестр
надо расширять по источникам финансирования.

Beliris — федерально-региональный орган, финансирующий инфраструктуру Брюсселя.
Его список проектов отдаётся AJAX-эндпоинтом с доменом, статусом и координатами:
это лучше квартальных контрактов, где координат нет вовсе.

Что берём
─────────
Домен `vert` (зелёные пространства) со статусом `termine` — только завершённые,
потому что незавершённые нечего аудировать. Дальше каждый проект сопоставляется
с ближайшим парком из `data/perimeters/parks_brussels.geojson` и печатается
измеренный по нему эффект.

Сопоставление по расстоянию — ГРУБОЕ. Совпадение названий проверяется глазами;
скрипт печатает и то и другое, решение за человеком.

Запуск:
    .venv/bin/python scripts/registry/fetch_beliris.py
"""

from __future__ import annotations

import csv
import json
import math
import urllib.request
from pathlib import Path

AJAX = ("https://www.beliris.be/beliris/ajax/projects.php?language=FR"
        "&filterStatus%5B%5D=en_projet&filterStatus%5B%5D=en_execution"
        "&filterStatus%5B%5D=termine&filterCommune=&page_alias=")
OUT = Path("data/registry/beliris_projects.json")
PARKS = Path("data/perimeters/parks_brussels.geojson")
AUDIT = Path("data/park_audit_2017_2024.csv")
MATCH_RADIUS_M = 600


def dist_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    k = math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * k * 111320, (a[1] - b[1]) * 110540)


def centroid(geom: dict) -> tuple[float, float]:
    c = geom["coordinates"]
    while isinstance(c[0][0], list):
        c = c[0]
    return sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)


def first_float(v) -> float | None:
    """Координаты иногда приходят как '50.82|50.83' — берём первое число."""
    if v is None:
        return None
    try:
        return float(str(v).split("|")[0])
    except ValueError:
        return None


def main() -> int:
    req = urllib.request.Request(AJAX, headers={"User-Agent": "map-project-research/0.1"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.loads(r.read().decode())
    projects = data["projects"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(projects, ensure_ascii=False, indent=1))

    by_domain: dict[str, int] = {}
    for p in projects:
        by_domain[p.get("domaine", "?")] = by_domain.get(p.get("domaine", "?"), 0) + 1
    print(f"проектов Beliris: {len(projects)}  →  {OUT}")
    print("по доменам:", ", ".join(f"{k}: {v}" for k, v in
                                   sorted(by_domain.items(), key=lambda x: -x[1])))

    green_done = [p for p in projects
                  if p.get("domaine") == "vert" and p.get("project_status") == "termine"]
    print(f"\nзелёные и ЗАВЕРШЁННЫЕ: {len(green_done)}")

    parks = json.loads(PARKS.read_text())["features"]
    park_pts = [(centroid(f["geometry"]), f["properties"]) for f in parks]
    audit = {r["osm"]: r for r in csv.DictReader(AUDIT.open())}

    print(f"\n{'проект Beliris':<46}{'ближайший парк OSM':<34}{'м':>6}{'эффект':>10}  вердикт")
    print("-" * 112)

    matched = []
    for p in sorted(green_done, key=lambda x: x["cleanTitle"]):
        lat, lon = first_float(p.get("lat")), first_float(p.get("long"))
        if lat is None or lon is None:
            print(f"{p['cleanTitle'][:44]:<46}{'нет координат':<34}")
            continue
        pt = (lon, lat)
        near = sorted(((dist_m(pt, c), c, pr) for c, pr in park_pts),
                      key=lambda x: x[0])[0]
        d, _, pr = near
        if d > MATCH_RADIUS_M:
            print(f"{p['cleanTitle'][:44]:<46}{'— нет парка рядом —':<34}{d:>6.0f}")
            continue
        a = audit.get(pr["osm"])
        eff = f"{float(a['ndvi_effect']):+.4f}" if a else "—"
        verdict = a["verdict"] if a else "не считался"
        print(f"{p['cleanTitle'][:44]:<46}{pr['name'][:32]:<34}{d:>6.0f}{eff:>10}  {verdict}")
        matched.append({"beliris": p["cleanTitle"], "park": pr["name"],
                        "osm": pr["osm"], "dist_m": round(d),
                        "ndvi_effect": a["ndvi_effect"] if a else None,
                        "verdict": verdict})

    print(f"\nсопоставлено проектов с парками: {len(matched)} из {len(green_done)}")
    print("\n⚠️  Сопоставление по расстоянию — грубое. Совпадение названий проверять")
    print("    глазами: рядом может стоять другой парк, а координата Beliris —")
    print("    это точка, а не контур работ.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
