#!/usr/bin/env python3
"""
Кому досталось озеленение: анализ справедливости изменений 2017–2024.

Вопрос, которого не задаёт никто
────────────────────────────────
Tree Equity Score (США), Mobiscore (BE) и UpGreen (ЕС) оценивают ТЕКУЩЕЕ
состояние. Ни один не спрашивает, куда пошло изменение. А это отдельный вопрос
с политическим весом:

    озеленение произошло там, где оно нужнее, — или там, где и так было зелено?

Что считается
─────────────
1. Связь измеренного изменения растительности с плотностью населения.
2. Связь с исходной зелёностью: прирастало к бедному или к богатому.

Оговорки, обязательные к произнесению
─────────────────────────────────────
· Плотность — ПРИБЛИЖЕНИЕ депривации, не доход. Дохода в наших данных нет.
  В Брюсселе плотность и депривация связаны (плотный «бедный полумесяц» вдоль
  канала), но это корреляция, а не тождество.
· Считается ВСЁ изменение, а не только вмешательства. Часть его — естественная
  динамика, стройки и смена землепользования.
· Это корреляция по 686 секторам, а не причинно-следственная связь.

Запуск:
    .venv/bin/python scripts/gee/equity_of_greening.py
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

CHANGE = Path("data/sector_change_2017_2024.csv")
SECTORS = Path("data/brussels_sectors.geojson")
NDVI_THRESHOLD = 0.0373


def pearson(xs: list[float], ys: list[float]) -> float:
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else 0.0


def main() -> int:
    meta = {f["properties"]["id"]: f["properties"]
            for f in json.loads(SECTORS.read_text())["features"]}

    rows = []
    for r in csv.DictReader(CHANGE.open()):
        m = meta.get(r["id"])
        if not m:
            continue
        pop, area = m.get("population") or 0, m.get("area_ha") or 0
        if pop <= 0 or area <= 0:
            continue
        rows.append({
            "id": r["id"],
            "name": r["name"],
            "effect": float(r["ndvi_effect"]),
            "ndvi_before": float(r["ndvi_before"]),
            "density": pop / area,          # человек на гектар
            "pop": pop,
        })

    print(f"секторов с населением: {len(rows)}")
    print(f"жителей охвачено: {sum(r['pop'] for r in rows):,}\n")

    dens = [r["density"] for r in rows]
    eff = [r["effect"] for r in rows]
    nb = [r["ndvi_before"] for r in rows]

    print("──────── Связи ────────")
    print(f"  r(плотность, изменение)       = {pearson(dens, eff):+.3f}")
    print(f"  r(исходная зелёность, измен.) = {pearson(nb, eff):+.3f}")
    print(f"  r(плотность, исх. зелёность)  = {pearson(dens, nb):+.3f}  ← контекст\n")

    # по квинтилям плотности
    rows.sort(key=lambda r: r["density"])
    q = len(rows) // 5
    print("──────── По квинтилям плотности населения ────────")
    print(f"  {'квинтиль':<12}{'чел/га':>9}{'NDVI до':>10}{'ср. измен.':>12}"
          f"{'знач.+':>8}{'знач.−':>8}{'жителей':>10}")
    print("  " + "-" * 69)
    for i in range(5):
        g = rows[i * q:(i + 1) * q] if i < 4 else rows[4 * q:]
        up = sum(1 for x in g if x["effect"] > NDVI_THRESHOLD)
        dn = sum(1 for x in g if x["effect"] < -NDVI_THRESHOLD)
        label = ["1 (редкие)", "2", "3", "4", "5 (плотные)"][i]
        print(f"  {label:<12}{statistics.mean(x['density'] for x in g):>9.1f}"
              f"{statistics.mean(x['ndvi_before'] for x in g):>10.3f}"
              f"{statistics.mean(x['effect'] for x in g):>+12.4f}"
              f"{up:>8}{dn:>8}{sum(x['pop'] for x in g):>10,}")

    # сколько людей живёт там, где значимо потеряли
    lost = [r for r in rows if r["effect"] < -NDVI_THRESHOLD]
    gained = [r for r in rows if r["effect"] > NDVI_THRESHOLD]
    print(f"\n──────── Сколько людей это касается ────────")
    print(f"  живут в секторах со значимым ПРИРОСТОМ:  {sum(r['pop'] for r in gained):>9,}"
          f"  ({len(gained)} секторов)")
    print(f"  живут в секторах со значимой ПОТЕРЕЙ:    {sum(r['pop'] for r in lost):>9,}"
          f"  ({len(lost)} секторов)")

    if lost:
        print("\n  Секторы со значимой потерей, по числу жителей:")
        for r in sorted(lost, key=lambda x: -x["pop"])[:8]:
            print(f"    {r['pop']:>6,} чел  {r['effect']:+.4f}  "
                  f"{r['density']:>5.1f} чел/га  {r['name'][:30]}")

    print("\n⚠️  Плотность — приближение депривации, не доход. Считается ВСЁ изменение,")
    print("    а не только вмешательства. Корреляция, не причинность.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
