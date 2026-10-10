#!/usr/bin/env python3
"""Прибор линии выполнения: был ли объект в названной точке на заданную дату.

Работает на исторических запросах Overpass (`[date:...]`): сервер отдаёт снимок
карты на прошедшую дату, а не сегодняшнюю. Это позволяет спросить «стояла ли
урна в этой точке в 2020 году» и сравнить с сегодняшним днём.

⚠️ Главное ограничение, ради которого существует контроль. OSM — не перепись
города. В центральном квадрате Брюсселя урн в OSM было 53 в 2016-м, 114 в 2020-м
и 205 сейчас: рост втрое — это работа картографов. Поэтому прибор всегда
меряет ДВА набора точек, названных в один день: проверяемые и контрольные.
Разность долей появления — то, что осталось после вычитания дрейфа карты.

Режимы:
  --drift        измерить дрейф карты по городу: сколько объектов было и стало
  --check        проверить зарегистрированные точки из data/registry/named_points.json

    .venv/bin/python scripts/registry/osm_appearance.py --drift --city brussels --kind waste_basket
    .venv/bin/python scripts/registry/osm_appearance.py --check --kind waste_basket --before 2020-01-01
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.config import CITIES  # noqa: E402
from engine.registries.points import KINDS, AppearanceResult, load  # noqa: E402

ENDPOINT = "https://overpass-api.de/api/interpreter"
UA = {"User-Agent": "frondia-research/0.1 (municipal change measurement; noncommercial)"}
PAUSE_S = 6.0   # публичный сервер общий: исторические запросы тяжелее обычных


def overpass(body: str, at: str | None = None, timeout: int = 180, tries: int = 5) -> dict:
    """Запрос к Overpass с отступлением при 429/504.

    Публичный сервер общий и исторические запросы для него тяжёлые, поэтому
    вежливость здесь часть инструмента: пауза между запросами и растущая
    задержка после отказа. Иначе прибор портит ресурс, которым пользуется.
    """
    head = "[out:json][timeout:120]" + (f'[date:"{at}T00:00:00Z"]' if at else "") + ";"
    data = urllib.parse.urlencode({"data": head + body}).encode()
    delay = 8.0
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(ENDPOINT, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as f:
                return json.loads(f.read().decode())
        except urllib.error.HTTPError as e:
            if e.code not in (429, 504) or attempt == tries:
                raise
            print(f"    сервер занят ({e.code}), жду {delay:.0f} с…", flush=True)
            time.sleep(delay); delay *= 2
        except (TimeoutError, urllib.error.URLError):
            if attempt == tries:
                raise
            print(f"    нет ответа, жду {delay:.0f} с…", flush=True)
            time.sleep(delay); delay *= 2
    raise RuntimeError("Overpass не ответил")


def count_in_bbox(kind: str, bbox: tuple[float, float, float, float], at: str | None) -> int:
    """Сколько объектов этого типа лежит в рамке на дату. bbox: (lon_min, lat_min, lon_max, lat_max)."""
    b = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"
    j = overpass(f'nwr["{KINDS[kind]}"]({b});out ids;', at)
    return len(j.get("elements", []))


def present_at(kind: str, lon: float, lat: float, radius_m: int, at: str | None) -> bool:
    """Стоял ли объект этого типа в радиусе от точки на дату."""
    j = overpass(f'nwr["{KINDS[kind]}"](around:{radius_m},{lat},{lon});out ids;', at)
    return len(j.get("elements", [])) > 0


def drift(city: str, kind: str, dates: list[str]) -> list[dict]:
    """Дрейф карты: сколько объектов видит OSM по всему городу на каждую дату.
    Это не измерение города — это измерение полноты карты, и печатается как таковое."""
    bbox = CITIES[city]["bbox"]
    out = []
    for d in dates:
        n = count_in_bbox(kind, bbox, d if d != "now" else None)
        out.append({"date": d, "count": n})
        print(f"  {d:<12} {n:>6}")
        time.sleep(PAUSE_S)
    return out


def official_flags(path: Path) -> dict[str, dict]:
    """Пометки реестра города у точек (object_registers.py), если они есть рядом с реестром точек."""
    p = path.with_name(path.stem + "_official.csv")
    if not p.exists():
        return {}
    import csv
    return {r["point"]: r for r in csv.DictReader(p.open())}


def taken_out(flag: dict | None) -> bool:
    """Правило 27.09.2026 (до первой проверки): точка выходит из сравнения, если объект того же вида по реестру
    города стоял в её радиусе до регистрации или стоит там без даты в первом снимке реестра — появление в OSM
    там было бы картографией. Объект с датой позже регистрации — это как раз появление, и точка остаётся."""
    if not flag or not int(flag["official_at_point"]):
        return False
    return int(flag["official_at_point"]) > int(flag["official_at_point_after_registration"])


def check(kind: str, before: str, after: str | None, path: Path) -> AppearanceResult:
    pts = [p for p in load(path) if p.kind == kind]
    res = AppearanceResult(kind=kind, date_before=before, date_after=after or "сейчас")
    flags = official_flags(path)
    if flags:
        gaps = [flags[p.id]["not_in_planner_osm_within_500m"] for p in pts if p.id in flags]
        if gaps and all(g != "" for g in gaps):
            res.gap_named = sum(1 for p in pts if p.role == "named" and p.id in flags and int(flags[p.id]["not_in_planner_osm_within_500m"]))
            res.gap_control = sum(1 for p in pts if p.role != "named" and p.id in flags and int(flags[p.id]["not_in_planner_osm_within_500m"]))
    for p in pts:
        bad = p.validate()
        if bad:
            print(f"  ⚠ {p.id}: {'; '.join(bad)} — пропущена")
            continue
        if taken_out(flags.get(p.id)):
            res.excluded.append(p.id)
            print(f"  {p.role:<8} {p.id:<28} — по реестру города объект уже стоит в радиусе: из сравнения исключена")
            continue
        was = present_at(kind, p.lon, p.lat, p.radius_m, before)
        time.sleep(PAUSE_S)
        now = present_at(kind, p.lon, p.lat, p.radius_m, after)
        time.sleep(PAUSE_S)
        appeared = (not was) and now
        if p.role == "named":
            res.named_total += 1
            res.named_appeared += appeared
        else:
            res.control_total += 1
            res.control_appeared += appeared
        res.detail.append({"id": p.id, "role": p.role, "unit_id": p.unit_id,
                           "was": was, "now": now, "appeared": appeared})
        print(f"  {p.role:<8} {p.id:<28} было {'да' if was else 'нет':<3} стало {'да' if now else 'нет':<3}"
              f"{'  ← появилось' if appeared else ''}")
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drift", action="store_true", help="измерить дрейф карты по городу")
    ap.add_argument("--check", action="store_true", help="проверить зарегистрированные точки")
    ap.add_argument("--city", default="brussels", choices=list(CITIES))
    ap.add_argument("--kind", default="waste_basket", choices=list(KINDS))
    ap.add_argument("--dates", default="2016-01-01,2018-01-01,2020-01-01,2022-01-01,2024-01-01,now")
    ap.add_argument("--before", default="2020-01-01")
    ap.add_argument("--after", default=None)
    ap.add_argument("--registry", default="data/registry/named_points.json")
    args = ap.parse_args()

    if args.drift:
        print(f"Дрейф карты OSM · {args.city} · {args.kind}\n"
              f"  это полнота карты, а не число объектов в городе:")
        rows = drift(args.city, args.kind, [d.strip() for d in args.dates.split(",")])
        first, last = rows[0]["count"], rows[-1]["count"]
        if first:
            print(f"\n  за период карта пополнилась в {last / first:.1f} раза — "
                  f"без контрольных точек любой рост «появлений» объясняется этим")
        out = Path(f"data/registry/osm_drift_{args.city}_{args.kind}.json")
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
        print(f"→ {out}")
        return 0

    if args.check:
        path = Path(args.registry)
        if not load(path):
            print("зарегистрированных точек нет: сначала назовите точки", file=sys.stderr)
            return 1
        print(f"Проверка появления · {args.kind} · {args.before} → {args.after or 'сейчас'}")
        res = check(args.kind, args.before, args.after, path)
        nr, cr = res.named_rate, res.control_rate
        print(f"\n  названные:   {res.named_appeared}/{res.named_total}"
              f"{f' = {nr:.0%}' if nr is not None else ''}")
        print(f"  контрольные: {res.control_appeared}/{res.control_total}"
              f"{f' = {cr:.0%}' if cr is not None else ''}")
        if res.excluded:
            print(f"  исключено по реестру города: {len(res.excluded)} ({', '.join(res.excluded)})")
        print(f"  вердикт: {res.verdict()}")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
