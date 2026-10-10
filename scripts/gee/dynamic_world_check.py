#!/usr/bin/env python3
"""
Проверка Dynamic World как второго прибора рядом с NDVI.

Что проверяем
─────────────
NDVI меряет ЗЕЛЁНОСТЬ и не отличает молодое дерево от травы. Из-за этого
Geboortebos (новая посадка на лугу) и Quai des Matériaux (парк на заросшем
пустыре) показали ПОТЕРЮ растительности, хотя оба — озеленение.

Dynamic World даёт по тем же снимкам Sentinel-2 (10 м, ряд с 2015) вероятности
классов: trees, grass, built, bare, shrub_and_scrub. Если он различает эти
случаи — у нас появляется второй независимый прибор, и два разных прибора,
говорящие одно, сильнее одного.

Гипотезы, которые проверяются
─────────────────────────────
1. Porte de Ninove (пустырь → парк): built/bare вниз, trees/grass вверх
2. Parc de Haren (новый парк): то же
3. Quai des Matériaux (заросший пустырь → парк): NDVI упал, но trees должны
   вырасти или built вырасти — тогда падение NDVI объяснено, а не загадочно
4. Реставрации (Josaphat, Karreveld): классы не меняются — что и ожидается

Запуск:
    .venv/bin/python scripts/gee/dynamic_world_check.py --project <id>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import ee

PARKS = Path("data/perimeters/parks_brussels.geojson")
BEFORE = ("2017-01-01", "2019-12-31")
AFTER = ("2021-01-01", "2024-12-31")
SUMMER = (6, 8)

CLASSES = ["trees", "grass", "shrub_and_scrub", "built", "bare"]

# что смотрим и зачем
CASES = [
    ("Ninove", "пустырь → парк, NDVI +0,25"),
    ("Haren", "новый парк, NDVI +0,07"),
    ("Matériaux", "заросший пустырь → парк, NDVI −0,07 ← загадка"),
    ("Josaphat", "реставрация, NDVI ~0"),
    ("Karreveld", "реставрация, NDVI ~0"),
    ("Tour et Taxis", "новый парк, NDVI +0,05"),
]


def dw_mean(geom: ee.Geometry, start: str, end: str) -> ee.Dictionary:
    coll = (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
            .filterBounds(geom).filterDate(start, end)
            .filter(ee.Filter.calendarRange(SUMMER[0], SUMMER[1], "month")))
    return (coll.select(CLASSES).mean()
            .reduceRegion(ee.Reducer.mean(), geom, scale=10,
                          maxPixels=int(1e9), bestEffort=True))


def main() -> int:
    ap = argparse.ArgumentParser(description="Dynamic World как второй прибор")
    ap.add_argument("--project", required=True)
    args = ap.parse_args()
    ee.Initialize(project=args.project)

    parks = json.loads(PARKS.read_text())["features"]

    for needle, note in CASES:
        hits = [f for f in parks if needle.lower() in f["properties"]["name"].lower()]
        if not hits:
            print(f"\n{needle}: не найден в периметрах")
            continue
        f = max(hits, key=lambda x: x["properties"]["area_ha"])
        geom = ee.Geometry(f["geometry"])

        b = dw_mean(geom, *BEFORE).getInfo()
        a = dw_mean(geom, *AFTER).getInfo()
        if not b or b.get("trees") is None:
            print(f"\n{f['properties']['name'][:44]}: нет данных Dynamic World")
            continue

        print(f"\n─── {f['properties']['name'][:46]}  ({f['properties']['area_ha']} га)")
        print(f"    {note}")
        print(f"    {'класс':<18}{'до':>8}{'после':>8}{'Δ':>9}")
        for c in CLASSES:
            if b.get(c) is None or a.get(c) is None:
                continue
            print(f"    {c:<18}{b[c]:>8.3f}{a[c]:>8.3f}{a[c] - b[c]:>+9.3f}")

    print("\n──────── Как читать ────────")
    print("  Рост trees при падении NDVI = молодые посадки заменили траву:")
    print("  озеленение состоялось, а яркость упала. Это и есть объяснение,")
    print("  которого NDVI дать не может.")
    print("  Рост built = стройка или мощение, тогда падение NDVI честное.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
