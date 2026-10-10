#!/usr/bin/env python3
"""
Сверка реестра контрактов с измеренным изменением — на уровне коммуны.

Зачем именно коммуна
────────────────────
Периметров работ в открытом доступе нет, поэтому связать «где потратили» с «где
изменилось» точечно нельзя. Но у обеих сторон есть один общий ключ, который
никуда не делся: коммуна. У контрактов она указана словом, у секторов — кодом
REFNIS. Это позволяет задать вопрос грубо, но честно:

    там, где квартальных контрактов было больше, измеримого озеленения больше?

Что это НЕ доказывает
─────────────────────
Девятнадцать точек, сильное смешение причин: контракты идут в неблагополучные
плотные кварталы, которые отличаются от остальных по десятку признаков сразу.
Положительная связь здесь не доказывает, что её создали контракты. Отсутствие
связи тоже ничего не опровергает — оно согласуется с уже установленным фактом,
что рассеянные уличные посадки на уровне сектора не различимы.

Это разведка, а не вывод. Печатаем таблицу и коэффициент, выводы делает человек.

Запуск:
    .venv/bin/python scripts/registry/commune_crosscheck.py
"""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

SECTORS = Path("data/brussels_sectors.geojson")
CHANGE = Path("data/sector_change_2017_2024.csv")
CONTRACTS = Path("data/registry/contracts_raw.json")

NDVI_THRESHOLD = 0.0373          # порог значимости из placebo_band.py
WINDOW = (2017, 2024)            # окно измерения

# REFNIS Брюссельского столичного региона. Сверено по пяти известным секторам:
# Peterbos → 21001, Parvis Saint-Roch → 21004, Karreveld → 21012,
# Coghen → 21016, Gare du Nord → 21015.
REFNIS = {
    "21001": "Anderlecht",
    "21002": "Auderghem",
    "21003": "Berchem-Sainte-Agathe",
    "21004": "Bruxelles",
    "21005": "Etterbeek",
    "21006": "Evere",
    "21007": "Forest",
    "21008": "Ganshoren",
    "21009": "Ixelles",
    "21010": "Jette",
    "21011": "Koekelberg",
    "21012": "Molenbeek",
    "21013": "Saint-Gilles",
    "21014": "Saint-Josse",
    "21015": "Schaerbeek",
    "21016": "Uccle",
    "21017": "Watermael-Boitsfort",
    "21018": "Woluwe-Saint-Lambert",
    "21019": "Woluwe-Saint-Pierre",
}


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else 0.0


def main() -> int:
    # сектор → коммуна
    sec_commune = {}
    for f in json.loads(SECTORS.read_text())["features"]:
        p = f["properties"]
        sec_commune[p["id"]] = REFNIS.get(p.get("cd_munty_refnis"), "?")

    # измеренное изменение по секторам
    by_commune: dict[str, list[float]] = {c: [] for c in REFNIS.values()}
    for row in csv.DictReader(CHANGE.open()):
        c = sec_commune.get(row["id"])
        if c and c in by_commune:
            by_commune[c].append(float(row["ndvi_effect"]))

    # контракты по коммунам
    contracts = json.loads(CONTRACTS.read_text())
    total: dict[str, int] = {c: 0 for c in REFNIS.values()}
    in_window: dict[str, int] = {c: 0 for c in REFNIS.values()}
    unmatched = []
    for k in contracts:
        name = (k.get("commune") or "").strip()
        if name not in total:
            unmatched.append(name or "(пусто)")
            continue
        total[name] += 1
        # контракт мог отразиться в окне, если его работы шли до 2024 и он
        # закончился не раньше 2018 — иначе эффект был бы уже в окне «до»
        if k["year_end"] >= 2018 and k["year_start"] <= WINDOW[1]:
            in_window[name] += 1

    print(f"Контрактов всего: {len(contracts)}, не сопоставлено с коммуной: "
          f"{len(unmatched)} {sorted(set(unmatched))}\n")

    rows = []
    for commune, effects in by_commune.items():
        if not effects:
            continue
        above = sum(1 for e in effects if e > NDVI_THRESHOLD)
        rows.append({
            "commune": commune,
            "sectors": len(effects),
            "contracts": total[commune],
            "in_window": in_window[commune],
            "mean": statistics.mean(effects),
            "median": statistics.median(effects),
            "above": above,
            "share_above": above / len(effects),
        })

    rows.sort(key=lambda r: -r["in_window"])

    print(f"{'коммуна':<22}{'сект.':>6}{'контр.':>8}{'в окне':>8}"
          f"{'сред. Δ':>10}{'медиана':>10}{'знач.':>7}{'доля':>8}")
    print("-" * 79)
    for r in rows:
        print(f"{r['commune']:<22}{r['sectors']:>6}{r['contracts']:>8}{r['in_window']:>8}"
              f"{r['mean']:>+10.4f}{r['median']:>+10.4f}{r['above']:>7}"
              f"{r['share_above']:>7.1%}")

    # корреляции
    cw = [r["in_window"] for r in rows]
    print("\n──────── Связь «контракты в окне» × «измеренное изменение» ────────")
    for label, key in (("среднее изменение", "mean"),
                       ("медиана изменения", "median"),
                       ("доля значимых секторов", "share_above")):
        r = pearson(cw, [x[key] for x in rows])
        print(f"  {label:<26} r = {r:+.3f}")

    print(f"\n  Точек: {len(rows)} коммун. Это разведка, а не вывод:")
    print("  контракты идут в неблагополучные плотные кварталы, которые отличаются")
    print("  от остальных по десятку признаков сразу. Связь здесь не означает причину,")
    print("  а её отсутствие согласуется с уже доказанным — уличные посадки")
    print("  на уровне сектора не различимы.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
