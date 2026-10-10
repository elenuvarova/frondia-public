#!/usr/bin/env python3
"""
Даты окончания и бюджеты ВСЕХ завершённых проектов Beliris — и что из них пригодно.

Зачем
─────
Два вывода были опрокинуты датами: восемь проектов закончились до начала нашего
окна «до», а Quai des Matériaux — внутри окна «после». Значит перед любым
измерением надо знать срок, а не после.

Что считает пригодным
─────────────────────
Объект годится к аудиту, если работы закончились МЕЖДУ окнами:
после конца «до» и до начала «после». Плюс запас: Sentinel-2 надёжно доступен
с 2017 года (S2B запущен в марте 2017), раньше — только Landsat 30 м,
для которого нужна отдельная калибровка.

Домены НЕ фильтруются: сильнейший эффект в городе (Porte de Ninove) числится
как `public`, а мост рядом как `mobilite`. Ярлык говорит, куда подшили бумагу.

Запуск:
    .venv/bin/python scripts/registry/beliris_dates.py
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from collections import Counter
from pathlib import Path

PROJECTS = Path("data/registry/beliris_projects.json")
OUT = Path("data/registry/beliris_dated.json")
UA = "map-project-research/0.1"

MONEY = re.compile(r"Budget[^€]{0,40}€\s*([\d][\d.\s]{5,})", re.I)
# БЕЗ re.I: с ним отрицание перестаёт пропускать буквы.
ENDDATE = re.compile(r"Fin du projet\s+(.{3,40}?)\s+Budget")
YEAR = re.compile(r"(19|20)\d{2}")

# Окна аудита и предел доступности Sentinel-2
BEFORE_END = 2019
AFTER_START = 2021
S2_FROM = 2017


def strip_html(h: str) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def fetch(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return None


def classify(year: int | None) -> str:
    if year is None:
        return "срок неизвестен"
    if year <= BEFORE_END:
        if year < S2_FROM:
            return "закончен до эры Sentinel-2"
        return "закончен до окна «до»"
    if year >= AFTER_START:
        return "закончен внутри окна «после»"
    return "ПРИГОДЕН"


def main() -> int:
    projects = [p for p in json.loads(PROJECTS.read_text())
                if p.get("project_status") == "termine"]
    print(f"завершённых проектов (все домены): {len(projects)}")
    print("тяну страницы, это займёт пару минут…\n")

    out = []
    for i, p in enumerate(projects, 1):
        url = p.get("url") or ""
        if url and not url.startswith("http"):
            url = "https://www.beliris.be/" + url.lstrip("/")
        html = fetch(url) if url else None
        budget = end = year = None
        if html:
            t = strip_html(html)
            m = MONEY.search(t)
            if m:
                budget = int(re.sub(r"[^\d]", "", m.group(1)))
            d = ENDDATE.search(t)
            if d:
                end = d.group(1).strip()
                y = YEAR.search(end)
                if y:
                    year = int(y.group(0))
        out.append({"title": p["cleanTitle"], "domaine": p["domaine"],
                    "url": url, "budget_eur": budget, "end": end,
                    "end_year": year, "status": classify(year),
                    "lat": p.get("lat"), "long": p.get("long")})
        if i % 25 == 0:
            print(f"  …{i} из {len(projects)}")
        time.sleep(0.35)

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"\n→ {OUT}")

    st = Counter(o["status"] for o in out)
    print("\n──────── Пригодность к аудиту ────────")
    for k, v in st.most_common():
        print(f"  {k:<34}{v:>4}")

    fit = [o for o in out if o["status"] == "ПРИГОДЕН"]
    print(f"\n──────── Пригодные ({len(fit)}) ────────")
    for o in sorted(fit, key=lambda x: -(x["budget_eur"] or 0)):
        b = f"{o['budget_eur']:,} €" if o["budget_eur"] else "бюджет неизвестен"
        print(f"  {o['end_year']}  {o['domaine']:<10}{b:>18}  {o['title'][:48]}")

    years = Counter(o["end_year"] for o in out if o["end_year"])
    print("\n──────── Годы окончания ────────")
    for y in sorted(years):
        bar = "█" * years[y]
        mark = " ← окно" if BEFORE_END < y < AFTER_START else ""
        print(f"  {y}  {bar} {years[y]}{mark}")

    print("\n⚠️  Окна — параметр, а не закон. Для проектов вне окна нужны СВОИ окна;")
    print("    но до 2017 Sentinel-2 недоступен, а Landsat 30 м требует")
    print("    отдельной калибровки: другой прибор — другой порог.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
