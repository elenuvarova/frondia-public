#!/usr/bin/env python3
"""
Диагностика: почему самые зелёные коммуны уходят в минус.

Наблюдение (см. commune_crosscheck.py): обе Woluwe и Ganshoren дают отрицательное
среднее изменение растительности. Две конкурирующие причины:

  (a) НАСТОЯЩЕЕ — взрослые деревья страдали в засушливые годы, и зелёные места
      теряли крону сильнее прочих. Тогда это вторая линза продукта:
      «где город теряет крону», не связанная с вмешательствами.

  (b) АРТЕФАКТ — подбор контроля ломается на краях распределения. Самому зелёному
      сектору не из чего подобрать такой же зелёный контроль, ему достаются места
      бледнее, и регрессия к среднему рисует ложное падение.

Как различаем
─────────────
Ключ — СЫРАЯ дельта. Она не знает ничего о контроле, поэтому на неё артефакт
подбора влиять не может.

  · сырая дельта падает с ростом зелёности → причина (a), эффект настоящий;
  · сырая дельта ровная, а падает только эффект → причина (b), виноват подбор.

Дополнительно смотрим разрыв подбора: насколько контроль отличается от объекта
по зелёности ДО. Если у зелёных секторов разрыв систематически положительный
(контроль бледнее объекта), подбор смещён — и это прямое доказательство (b).

Запуск:
    .venv/bin/python scripts/gee/diagnose_green_decline.py
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

SRC = Path("data/sector_change_2017_2024.csv")
NUMERIC = ("ndvi_effect", "ndvi_before", "d_ndvi_raw",
           "ctrl_ndvi_before", "ctrl_match_gap", "ctrl_d_ndvi")


def pearson(xs: list[float], ys: list[float]) -> float:
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else 0.0


def main() -> int:
    rows = list(csv.DictReader(SRC.open()))
    for r in rows:
        for k in NUMERIC:
            r[k] = float(r[k])

    nb = [r["ndvi_before"] for r in rows]
    eff = [r["ndvi_effect"] for r in rows]
    raw = [r["d_ndvi_raw"] for r in rows]
    gap = [r["ctrl_match_gap"] for r in rows]

    print("ДИАГНОСТИКА: почему зелёные коммуны уходят в минус")
    print(f"секторов: {len(rows)}\n")

    r_eff = pearson(nb, eff)
    r_raw = pearson(nb, raw)
    r_gap = pearson(nb, gap)

    print("1. Зависимость от исходной зелёности")
    print(f"   r(NDVI до, эффект)       = {r_eff:+.3f}")
    print(f"   r(NDVI до, СЫРАЯ дельта) = {r_raw:+.3f}   ← контроля не знает")
    print()
    print("2. Качество подбора контроля")
    print(f"   r(NDVI до, разрыв с контролем) = {r_gap:+.3f}")
    print(f"   средний разрыв          = {statistics.mean(gap):+.4f}")
    print(f"   ст. отклонение разрыва  = {statistics.stdev(gap):.4f}")

    rows.sort(key=lambda r: r["ndvi_before"])
    d = len(rows) // 10
    print("\n3. По децилям исходной зелёности")
    print(f"   {'дец':<5}{'NDVI до':>9}{'разрыв':>9}{'сырая Δ':>10}{'эффект':>10}")
    print("   " + "-" * 43)
    for i in range(10):
        g = rows[i * d:(i + 1) * d] if i < 9 else rows[9 * d:]
        print(f"   {i + 1:<5}{statistics.mean(x['ndvi_before'] for x in g):>9.3f}"
              f"{statistics.mean(x['ctrl_match_gap'] for x in g):>9.4f}"
              f"{statistics.mean(x['d_ndvi_raw'] for x in g):>10.4f}"
              f"{statistics.mean(x['ndvi_effect'] for x in g):>10.4f}")

    print("\n──────── Вердикт ────────")
    strong_raw = r_raw < -0.25
    biased = abs(r_gap) > 0.25
    if strong_raw and not biased:
        print("  (a) НАСТОЯЩЕЕ. Сырая дельта падает с ростом зелёности, а подбор")
        print("      не смещён. Зелёные места действительно теряли крону.")
        print("      → это вторая линза продукта, не ошибка.")
    elif biased and not strong_raw:
        print("  (b) АРТЕФАКТ ПОДБОРА. Сырая дельта ровная, но контроль у зелёных")
        print("      секторов систематически отличается — регрессия к среднему.")
        print("      → чинить матчинг, эффект на краях распределения не заявлять.")
    elif strong_raw and biased:
        print("  СМЕШАННОЕ. Есть и настоящее падение, и смещение подбора.")
        print("      → падение реально, но его величину по этой схеме не заявлять,")
        print("        пока подбор не починен.")
    else:
        print("  НИ ТО НИ ДРУГОЕ. Связь с исходной зелёностью слабая по обоим")
        print("      каналам — наблюдение по коммунам объясняется чем-то ещё")
        print("      (например составом застройки), и требует отдельной проверки.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
