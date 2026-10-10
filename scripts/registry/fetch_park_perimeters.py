#!/usr/bin/env python3
"""
Сбор пригодных для аудита периметров парков Брюсселя из OpenStreetMap.

Почему OSM, а не наша обводка
─────────────────────────────
Геометрия чужая: её рисовало сообщество, она названа, версионирована, на неё
можно сослаться. Это снимает возражение «вы сами обвели там, где позеленело» —
см. `docs/01-wireframes.md`, раздел 7½.

Отбор
─────
Именованные `leisure=park` (ways и relations), площадью **от 1 га**. Порог не
произвольный: ниже него объект занимает единицы пикселей Sentinel-2 и сигнал
тонет. Площади (`place=square`) сюда НЕ входят — замер показал, что из 130
именованных проходят девять, медиана 0,17 га.

Запуск:
    .venv/bin/python scripts/registry/fetch_park_perimeters.py
"""

from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

# Города — принято 2026-09-02: Антверпен второй. bbox в порядке Overpass (S, W, N, E).
CITIES = {
    "brussels": {"bbox": (50.76, 4.23, 50.94, 4.50),
                 "out": Path("data/perimeters/parks_brussels.geojson")},
    "antwerp":  {"bbox": (51.14, 4.22, 51.38, 4.53),
                 "out": Path("data/perimeters/parks_antwerp.geojson")},
    # третий город, 26.09.2026; в город парк засчитывает адаптер, точкой в секторах коммуны
    "ghent":    {"bbox": (50.97, 3.57, 51.20, 3.86),
                 "out": Path("data/perimeters/parks_ghent.geojson")},
    "liege":    {"bbox": (50.55, 5.51, 50.70, 5.69),
                 "out": Path("data/perimeters/parks_liege.geojson")},
    "charleroi": {"bbox": (50.34, 4.34, 50.50, 4.52),
                  "out": Path("data/perimeters/parks_charleroi.geojson")},
}
MIN_HA = 1.0
# another public instance when overpass-api.de refuses (26.09.2026: VK Maps answered, lz4 did not)
OVERPASS = __import__("os").environ.get("OVERPASS_URL", "https://overpass-api.de/api/interpreter")

def query_for(bbox):
    s, w, n, e = bbox
    return f"""[out:json][timeout:180];
(
  way["leisure"="park"]["name"]({s},{w},{n},{e});
  relation["leisure"="park"]["name"]({s},{w},{n},{e});
);
out geom;"""


def ring_area_ha(ring: list[tuple[float, float]]) -> float:
    """Площадь кольца в гектарах (равнопромежуточное приближение)."""
    if len(ring) < 4:
        return 0.0
    lat0 = sum(p[1] for p in ring) / len(ring)
    k = math.cos(math.radians(lat0))
    s = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i][0] * k * 111320, ring[i][1] * 110540
        x2, y2 = ring[i + 1][0] * k * 111320, ring[i + 1][1] * 110540
        s += x1 * y2 - x2 * y1
    return abs(s) / 2 / 10000


def closed(coords: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return coords if coords[0] == coords[-1] else coords + [coords[0]]


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Периметры парков OSM ≥ 1 га")
    ap.add_argument("--city", choices=list(CITIES), default="brussels")
    args = ap.parse_args()
    cfg = CITIES[args.city]
    OUT = cfg["out"]
    req = urllib.request.Request(
        OVERPASS,
        data=urllib.parse.urlencode({"data": query_for(cfg["bbox"])}).encode(),
        headers={"User-Agent": "map-project-research/0.1"},
    )
    print("Запрос в Overpass…")
    with urllib.request.urlopen(req, timeout=240) as r:
        data = json.loads(r.read().decode())

    els = data.get("elements", [])
    print(f"получено объектов: {len(els)}")

    feats, skipped_small, skipped_bad = [], 0, 0
    for e in els:
        name = e.get("tags", {}).get("name", "")
        if e["type"] == "way":
            g = e.get("geometry")
            if not g or len(g) < 4:
                skipped_bad += 1
                continue
            rings = [closed([(p["lon"], p["lat"]) for p in g])]
        else:
            # relation: собираем внешние кольца
            rings = []
            for m in e.get("members", []):
                if m.get("role") not in ("outer", ""):
                    continue
                g = m.get("geometry")
                if g and len(g) >= 4:
                    rings.append(closed([(p["lon"], p["lat"]) for p in g]))
            if not rings:
                skipped_bad += 1
                continue

        ha = sum(ring_area_ha(r) for r in rings)
        if ha < MIN_HA:
            skipped_small += 1
            continue

        geom = ({"type": "Polygon", "coordinates": [rings[0]]} if len(rings) == 1
                else {"type": "MultiPolygon", "coordinates": [[r] for r in rings]})
        feats.append({
            "type": "Feature",
            "properties": {
                "osm": f"{e['type']}/{e['id']}",
                "name": name,
                "area_ha": round(ha, 2),
            },
            "geometry": geom,
        })

    feats.sort(key=lambda f: -f["properties"]["area_ha"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(
        {"type": "FeatureCollection", "features": feats}, ensure_ascii=False))

    print(f"\nотброшено мельче {MIN_HA} га: {skipped_small}")
    print(f"отброшено без геометрии:  {skipped_bad}")
    print(f"ПРИГОДНЫХ ДЛЯ АУДИТА:     {len(feats)}")
    print(f"→ {OUT}\n")
    print("Крупнейшие:")
    for f in feats[:10]:
        p = f["properties"]
        print(f"  {p['area_ha']:>8.1f} га  {p['name'][:46]:<46} {p['osm']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
