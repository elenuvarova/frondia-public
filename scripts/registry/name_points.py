#!/usr/bin/env python3
"""Назвать точки линии выполнения: где урны нужнее всего — и случайный контроль.

Правило выбора, целиком проверяемое по файлам:
  1. сектор Брюсселя из НИЖНЕГО терциля по медианному облагаемому доходу (Statbel);
  2. в радиусе 150 м от центроида сектора сегодня нет ни одной урны в OSM;
  3. сектор не меньше 4 га — иначе центроид не представляет территорию.

Отобранные секторы **случайно делятся пополам** с фиксированным зерном: половина
становится названными точками (то, что мы объявляем приоритетом), половина —
контролем (те же условия, но мы про них молчим). Через несколько лет разность
долей появления скажет, изменилось ли что-нибудь там, где мы назвали, — сверх
дрейфа карты OSM, который сам по себе даёт трёхкратный рост.

Почему так, а не «проверим, где урны появились за прошлые годы»: обратная
проверка запрещена той же дисциплиной, что и след вмешательства. Точки
называются ДО проверки, иначе граница подгоняется под результат.

    .venv/bin/python scripts/registry/name_points.py --city brussels --kind waste_basket
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.config import CITIES, CONTROL  # noqa: E402
from engine.registries.points import KINDS, register, save  # noqa: E402
from scripts.registry.osm_appearance import overpass  # noqa: E402

SEED = "facta-2026-09-04"      # зерно разделения: фиксировано и напечатано
NEAR_M = 150                   # «урна рядом есть» — в этом радиусе от центроида
RADIUS_M = 50                  # радиус самой проверки появления


def dist_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[1], a[0], b[1], b[0]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def coin(unit_id: str) -> bool:
    """Половина от зерна: воспроизводимо кем угодно, не подбирается под результат."""
    return int(hashlib.sha256((SEED + unit_id).encode()).hexdigest(), 16) % 2 == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="brussels", choices=list(CITIES))
    ap.add_argument("--kind", default="waste_basket", choices=list(KINDS))
    ap.add_argument("--out", default="data/registry/named_points.json")
    args = ap.parse_args()

    ad = ADAPTERS[args.city]()
    units = [u for u in ad.units() if u.area_ha >= CONTROL["min_area_ha"]]
    income = ad.income() if hasattr(ad, "income") else {}
    have_income = [u for u in units if income.get(u.id)]
    if not have_income:
        print("нет данных о доходе — правило выбора не определено", file=sys.stderr)
        return 1
    vals = sorted(income[u.id] for u in have_income)
    cut = vals[len(vals) // 3]
    poor = [u for u in have_income if income[u.id] <= cut]
    print(f"{args.city}: единиц {len(units)}, с доходом {len(have_income)}, "
          f"нижний терциль (≤ {cut:,.0f} €) — {len(poor)}".replace(",", " "))

    b = CITIES[args.city]["bbox"]
    print(f"беру все объекты «{args.kind}» города одним запросом…")
    j = overpass(f'nwr["{KINDS[args.kind]}"]({b[1]},{b[0]},{b[3]},{b[2]});out center;')
    pts = []
    for e in j.get("elements", []):
        lon = e.get("lon") or (e.get("center") or {}).get("lon")
        lat = e.get("lat") or (e.get("center") or {}).get("lat")
        if lon and lat:
            pts.append((lon, lat))
    print(f"  на карте сейчас: {len(pts)}")

    empty = []
    for u in poor:
        c = u.centroid
        if not any(dist_m(c, p) <= NEAR_M for p in pts):
            empty.append(u)
    print(f"  из них без объекта в {NEAR_M} м от центроида: {len(empty)}")

    rule = (f"нижний терциль по медианному доходу Statbel (≤ {cut:,.0f} €), "
            f"нет объекта «{args.kind}» в {NEAR_M} м от центроида сектора на "
            f"дату регистрации, площадь ≥ {CONTROL['min_area_ha']:.0f} га").replace(",", " ")
    exp_named = (f"если город ставит объекты там, где их нет и где живут беднее, "
                 f"объект появится в {RADIUS_M} м от точки к следующей проверке")
    exp_ctrl = ("контроль: те же условия, точка не объявлена приоритетом; "
                "её появления — дрейф карты и обычная работа города")

    records = []
    for u in empty:
        named = coin(u.id)
        records.append(register(
            id=f"{args.city[:3]}-{args.kind[:2]}-{u.id}", city=args.city, unit_id=u.id,
            kind=args.kind, lon=u.centroid[0], lat=u.centroid[1], radius_m=RADIUS_M,
            role="named" if named else "control", rule=rule,
            expectation=exp_named if named else exp_ctrl,
            source=f"Statbel доход + OSM на дату регистрации; зерно разделения {SEED}",
            note=u.name or ""))
    save(records, Path(args.out))
    n_named = sum(1 for r in records if r.role == "named")
    print(f"\nзарегистрировано {len(records)} точек: названных {n_named}, "
          f"контрольных {len(records) - n_named}")
    print(f"зерно разделения {SEED} — половина определяется хешем от него и id сектора")
    print(f"→ {args.out}")

    csv_out = Path(args.out).with_suffix(".csv")
    with csv_out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "unit_id", "name", "role", "kind", "lon", "lat", "radius_m", "registered_at", "point_hash"])
        for r in records:
            w.writerow([r.id, r.unit_id, r.note, r.role, r.kind, round(r.lon, 6), round(r.lat, 6),
                        r.radius_m, r.registered_at, r.point_hash])
    print(f"→ {csv_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
