#!/usr/bin/env python3
"""
Бюджеты проектов Beliris и цена измеренного эффекта.

Зачем
─────
В реестре появились деньги. Это позволяет задать вопрос, которого не задаёт
никто из соседей по рынку: СКОЛЬКО СТОИЛ измеренный эффект. Распорядители
бюджетов говорят именно на этом языке, а не на языке индексов растительности.

Что делает
──────────
Для завершённых проектов домена `vert` тянет страницу проекта и вынимает
бюджет (TVAC), дату окончания и коммуны. Дальше соединяет с измеренным
эффектом по сопоставленному парку.

ОБЯЗАТЕЛЬНАЯ ОГОВОРКА, без неё числа врут
─────────────────────────────────────────
Бюджет относится ко ВСЕМУ проекту, а эффект измерен по ОДНОМУ парку внутри
него. Porte de Ninove стоил 28,5 млн, но это дороги, мост и общественные
пространства целиком, а парк — 2,25 га внутри. Говорить «28,5 млн купили
+0,25 NDVI» нельзя. Корректная формулировка: «проект стоил столько-то и включал
парк такой-то площади, который измеримо озеленился».

Поэтому считается цена за ГЕКТАР затронутого парка, а не за единицу индекса,
и рядом всегда печатается доля парка в проекте, если её можно оценить.

Запуск:
    .venv/bin/python scripts/registry/beliris_budgets.py
"""

from __future__ import annotations

import csv
import json
import re
import time
import urllib.request
from pathlib import Path

PROJECTS = Path("data/registry/beliris_projects.json")
AUDIT = Path("data/park_audit_2017_2024.csv")
OUT = Path("data/registry/beliris_budgets.json")
UA = "map-project-research/0.1"

MONEY = re.compile(r"Budget[^€]{0,40}€\s*([\d][\d.\s]{5,})", re.I)
# БЕЗ re.I: с ним отрицание [^A-Z] перестаёт пропускать буквы вообще —
# классическая ошибка, из-за которой даты не извлекались.
ENDDATE = re.compile(r"Fin du projet\s+(.{3,40}?)\s+Budget")


def strip_html(h: str) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def fetch(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def main() -> int:
    projects = json.loads(PROJECTS.read_text())
    green_done = [p for p in projects
                  if p.get("domaine") == "vert" and p.get("project_status") == "termine"]
    print(f"завершённых зелёных проектов: {len(green_done)}\n")

    out = []
    for p in green_done:
        url = p.get("url") or ""
        if url and not url.startswith("http"):
            url = "https://www.beliris.be" + ("" if url.startswith("/") else "/") + url
        html = fetch(url) if url else None
        budget = end = None
        if html:
            t = strip_html(html)
            m = MONEY.search(t)
            if m:
                budget = int(re.sub(r"[^\d]", "", m.group(1)))
            d = ENDDATE.search(t)
            if d:
                end = d.group(1).strip()
        out.append({"title": p["cleanTitle"], "url": url,
                    "budget_eur": budget, "end": end})
        mark = f"{budget:>12,} €" if budget else "        нет  "
        print(f"  {mark}  {(end or '—')[:18]:<20}{p['cleanTitle'][:44]}")
        time.sleep(0.4)

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    got = [o for o in out if o["budget_eur"]]
    print(f"\nбюджет найден у {len(got)} из {len(out)}  →  {OUT}")

    if got:
        vals = sorted(o["budget_eur"] for o in got)
        total = sum(vals)
        print(f"сумма: {total:,} €   медиана: {vals[len(vals)//2]:,} €")

    # соединяем с измеренным
    audit = {r["name"]: r for r in csv.DictReader(AUDIT.open())}
    print("\n──────── Цена и измеренный эффект ────────")
    print(f"  {'проект':<40}{'бюджет':>14}{'парк, га':>10}{'эффект':>10}  вердикт")
    print("  " + "-" * 88)
    for o in out:
        if not o["budget_eur"]:
            continue
        # грубое сопоставление по общему слову в названии
        words = [w for w in re.findall(r"[A-ZÀ-Þ][\w'’-]{3,}", o["title"])
                 if w.lower() not in ("parc", "park", "restauration", "construction",
                                      "réaménagement", "rénovation", "nouveau")]
        hit = None
        for name, r in audit.items():
            if any(w.lower() in name.lower() for w in words):
                hit = r
                break
        ha = f"{float(hit['area_ha']):.1f}" if hit else "—"
        eff = f"{float(hit['ndvi_effect']):+.4f}" if hit else "—"
        verdict = hit["verdict"] if hit else "не сопоставлен"
        print(f"  {o['title'][:38]:<40}{o['budget_eur']:>14,}{ha:>10}{eff:>10}  {verdict}")

    print("\n⚠️  Бюджет относится ко ВСЕМУ проекту, эффект измерен по ОДНОМУ парку")
    print("    внутри него. «N млн купили +0,25 NDVI» — некорректно. Корректно:")
    print("    «проект стоил N и включал парк такой-то площади, который озеленился».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
