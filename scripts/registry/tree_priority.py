#!/usr/bin/env python3
"""Где сажать деревья — приоритет секторов, названный заранее (линия выполнения для крон).

Зачем. Линзы атласа уже говорят, где не хватает кроны (3-30-300) и где жарко. Этот слой делает из них
то же, что City Planner делает для скамеек: называет ДО работ, куда сажать в первую очередь, и
оставляет ранги ниже отсечки контролем. Через годы проверяется, выросла ли крона в названных секторах
сильнее, чем в контрольных, — тем же методом, с порогом.

Правило — записано ДО результата (09.10.2026)
─────────────────────────────────────────────
· Единица — сектор Statbel с жителями. Входы — уже опубликованные слои пакета:
  доля кроны по ESA WorldCover (`rule_3_30_300.canopy_share`, жёсткая классификация 10 м),
  перегрев поверхности лета 2022–2025 над медианой города (`heat_2022_2025.excess_over_city_c`),
  жители (`population`).
· Нужда = (0,30 − доля кроны) × перегрев °C × жители, только где крона < 30 % и перегрев > 0.
  Смысл: жители, которым не хватает кроны до нормы 30 %, взвешенные тем, насколько у них жарче.
  Прохладный сектор без кроны в приоритет не попадает — это решение правила, а не пробел.
· Ранги по убыванию нужды, ничья — по id. Ранги 1–10 — рекомендация, 11–20 — контроль.
· Хеш геометрии сектора и дата записи фиксируются в момент записи; правка — новая запись.

Чего правило не знает и не притворяется: где физически есть место под дерево (подземные сети,
ширина тротуара, собственность). Сектор с высокой нуждой может оказаться без места — тогда это
отказ на проверке, а не ошибка ранга. Жара здесь — состояние, не эффект (порог эффекта охлаждения
1,32 °C больше, чем даёт парк).

Как это проверят. Молодые деревья со спутника не видны годами, поэтому две ступени:
  1) реестр посадок города (`trees_register.csv`, где есть) — посажено ли в названных секторах чаще,
     чем в контрольных; 2) через 5+ лет — эффект кроны против 12 подобранных мест с порогом.
Контроль консервативен: ранги 11–20 по построению чуть менее нуждающиеся.

    .venv/bin/python scripts/registry/tree_priority.py --city ghent
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402
from engine.registries.preregistration import geometry_hash  # noqa: E402

TARGET = 0.30
NAMED_TO, CONTROL_TO = 10, 20


def read(city: str, layer: str) -> dict[str, dict]:
    return {r["id"]: r for r in csv.DictReader((ROOT / f"cities/{city}/layers/{layer}.csv").open())}


def income_thirds(rows: list[dict]) -> dict[str, int]:
    """Треть дохода по медианному облагаемому доходу Statbel 2023 (как в линзе «кто в нехватке»)."""
    withinc = sorted((r for r in rows if r["income"] is not None), key=lambda r: r["income"])
    n = len(withinc)
    return {r["id"]: 1 + min(2, i * 3 // n) for i, r in enumerate(withinc)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="ghent")
    ap.add_argument("--force", action="store_true",
                    help="a NEW version of the list: the old file is kept beside it with its date; without it a changed list is refused")
    args = ap.parse_args()
    city = args.city

    rule = read(city, "rule_3_30_300")
    heat = read(city, "heat_2022_2025")
    a8 = read(city, "article8_2024")
    plant = read(city, "trees_register") if (ROOT / f"cities/{city}/layers/trees_register.csv").exists() else {}
    units = {u.id: u for u in ADAPTERS[city]().units()}

    rows = []
    for sid, r in rule.items():
        if sid not in heat or sid not in units:
            continue
        pop = int(float(r["population"] or 0))
        canopy = float(r["canopy_share"])
        excess = float(heat[sid]["excess_over_city_c"])
        need = (TARGET - canopy) * excess * pop if (canopy < TARGET and excess > 0 and pop > 0) else 0.0
        inc = a8.get(sid, {}).get("income")
        rows.append({"id": sid, "name": r["name"], "population": pop, "canopy_share": round(canopy, 4),
                     "heat_excess_c": round(excess, 3), "need": round(need, 2),
                     "income": float(inc) if inc not in (None, "") else None,
                     "trees_registered": int(plant[sid]["trees"]) if sid in plant else None})
    rows.sort(key=lambda r: (-r["need"], r["id"]))
    thirds = income_thirds(rows)
    for i, r in enumerate(rows, 1):
        r["rank"] = i if r["need"] > 0 else None
        r["role"] = ("named" if r["rank"] and r["rank"] <= NAMED_TO else
                     "control" if r["rank"] and r["rank"] <= CONTROL_TO else "")
        r["income_third"] = thirds.get(r["id"])

    today = run_day = date.today().isoformat()
    has_register = bool(plant)
    records = [{"id": f"{city[:3]}-tree-{r['rank']:02d}", "city": city, "unit_id": r["id"], "name": r["name"],
                "role": r["role"], "rank": r["rank"], "need": r["need"],
                "geometry_hash": geometry_hash(units[r["id"]].geometry), "registered_at": today,
                "rule": "нужда = (0,30 − крона WorldCover) × перегрев лета 2022–2025 над медианой города × жители; "
                        "1–10 названы, 11–20 контроль",
                "expectation": (("крона в названных секторах вырастет сильнее, чем в контрольных; первая ступень — "
                                 "посадки по реестру города после последней копии реестра не позже даты записи "
                                 "(data/registry/snapshots), вторая — эффект кроны против 12 мест через 5+ лет")
                                if has_register else
                                ("крона в названных секторах вырастет сильнее, чем в контрольных; реестра посадок город "
                                 "не публикует — проверка только эффектом кроны против 12 мест через 5+ лет"))}
               for r in rows if r["role"]]

    # A registration is never rewritten (engine/registries/preregistration.py: an edit is a new record). The same list
    # keeps its first date; a different one is refused unless --force, which keeps the old file beside the new.
    reg = ROOT / f"data/registry/tree_priority_{city}.json"
    if not reg.exists() and list(reg.parent.glob(f"{reg.stem}_v*.json")):
        raise SystemExit(f"{reg.name} is missing but archived versions exist: refused (an earlier --force did not finish?)")
    old_records, arch = None, None
    if reg.exists():
        old = old_records = json.loads(reg.read_text())
        key = lambda rs: [(r["unit_id"], r["rank"], r["role"], r["geometry_hash"]) for r in rs]
        if key(old) == key(records):
            records = old_records = old
            today = min(r["registered_at"] for r in old)
        elif not args.force:
            raise SystemExit(f"{reg.name}: the list changed since {min(r['registered_at'] for r in old)} — "
                             "refused; a new version needs --force (the old file is kept)")
        else:
            # the old version is archived under its own version number, never over another archive; the new one's ids
            # carry the next number, so two versions never share an id (an edit is a new record)
            prev = max((int(r.get("version", 1)) for r in old), default=1)
            arch = reg.with_name(f"{reg.stem}_v{prev}.json")
            if arch.exists():
                raise SystemExit(f"{arch.name} exists: refused, nothing archived over it")
            for r in records:
                r["version"] = prev + 1
                r["id"] = r["id"].replace("-tree-", f"-tree-v{prev + 1}-")

    layer = ROOT / f"cities/{city}/layers/tree_priority.csv"
    fields = ["id", "name", "population", "canopy_share", "heat_excess_c", "need", "rank", "role",
              "income_third", "trees_registered"]
    with layer.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    # write the new version beside the old first, then swap: a run that fails halfway leaves the old list in place
    tmp = reg.with_name(reg.name + ".tmp")
    tmp.write_text(json.dumps(records, ensure_ascii=False, indent=1))
    if reg.exists() and args.force and records is not old_records:
        reg.rename(arch)
    tmp.replace(reg)

    eligible = [r for r in rows if r["need"] > 0]
    named = [r for r in rows if r["role"] == "named"]
    m = Manifest.read(city)
    m.add(LayerEntry(
        layer="tree_priority", computed=run_day, n_units=len(rows),
        measures="приоритет посадки деревьев по сектору: жители без нормы кроны 30 %, взвешенные перегревом",
        unit="жители × недостающая доля кроны × °C (ранг важнее величины)",
        method="нужда = (0,30 − доля кроны) × перегрев лета над медианой города × жители, где крона < 30 % и "
               "перегрев > 0; ранги 1–10 названы до работ, 11–20 — контроль; хеш геометрии и дата записи",
        source="ESA WorldCover 2021 (крона, слой rule_3_30_300), Landsat 8/9 лета 2022–2025 (heat_2022_2025), Statbel",
        threshold=None,
        threshold_source="порога нет: это рекомендация, а не измерение; проверка — позже, против контроля, с порогом",
        limits=["место под дерево не известно: подземные сети, ширина тротуара и собственность не учтены",
                "жара — состояние, не эффект: охлаждение от посадок не обещается (порог 1,32 °C)",
                "молодые деревья со спутника не видны годами; первая проверка — по реестру посадок города",
                f"список назван {today} (data/registry/tree_priority_{city}.json); `computed` — дата этого прогона",
                f"в приоритет попадают {len(eligible)} из {len(rows)} секторов (крона < 30 % и жарче медианы города)"]))
    m.write()

    print(f"{city}: секторов {len(rows)}, с нуждой {len(eligible)}")
    for r in (x for x in rows[:CONTROL_TO] if x["rank"]):
        print(f"  {r['rank']:>2} {r['role']:<7} {r['name'][:28]:<28} жителей {r['population']:>5} "
              f"крона {r['canopy_share']:.2f} +{r['heat_excess_c']:.1f} °C  треть дохода {r['income_third']}"
              + ("" if r["trees_registered"] is None else f"  в реестре деревьев {r['trees_registered']}"))
    if named:
        print(f"  треть дохода у названных: {[r['income_third'] for r in named]}")
    print(f"→ {layer.relative_to(ROOT)}, {reg.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
