#!/usr/bin/env python3
"""
Бюджеты квартальных контрактов и их привязка к измеренным паркам.

Зачем
─────
Бенчмарк «евро на гектар измеренного результата» после проверки дат остался
с одной чистой точкой (Haren). Ему нужен реестр: у какого вмешательства какой
бюджет, какой объект и когда сдан. Beliris дал 14 бюджетов; здесь — 98
квартальных контрактов, у которых бюджет лежит прямо в описании.

Привязка к объекту — по имени, названному в документе
─────────────────────────────────────────────────────
Периметров у контрактов нет. Но описание называет парки словами: «parc de
Résédas», «parc Maximilien». Если именованный парк OSM ≥ 1 га упомянут в
описании контракта — связь документальная, а не геометрическая. Это ступень 2
из решения о следе: документ говорит, что мерить.

Оговорки, обязательные к произнесению
─────────────────────────────────────
· Упоминание ≠ вмешательство: Parc Maximilien в Héliport-Anvers упомянут как
  ОРИЕНТИР («bordées par le parc Maximilien»), а не как мера. Экстракция мер
  (`extract_greening.py`) отличает состояние от действия; здесь — только связь.
· Сроки: контракт 4 года + до 2 лет на работы. Год сдачи объекта неизвестен;
  берём `year_end + 1` как прокси и печатаем статус по окнам, не вердикт.
· Бюджет — на весь контракт (жильё, соцпрограмма, пространство); парк — часть.
  «N млн купили +X» некорректно; корректно — «контракт на N включал парк,
  который изменился на X».

Запуск:
    .venv/bin/python scripts/registry/contract_budgets_links.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.audit import windows_for_completion

CONTRACTS = Path("data/registry/contracts_raw.json")
PARKS = Path("data/perimeters/parks_brussels.geojson")
AUDIT = Path("data/park_audit_2017_2024.csv")
OUT_BUDGETS = Path("data/registry/contracts_budgets.json")
OUT_LINKS = Path("data/registry/contract_park_links.csv")

# «Budgets Région 14 125 000,00 &euro; Anderlecht 743 424,83 &euro; Total 14 868 424,83 &euro;»
MONEY = re.compile(r"(Total|Région|Region|Commune|[A-ZÉ][\w\-']{3,})\s+([\d][\d   ]{3,}(?:,\d{1,2})?)\s*(?:&euro;|€)")
GENERIC = {"parc", "park", "de", "du", "des", "la", "le", "les", "van", "het", "de", "d'", "l'"}


def to_eur(s: str) -> float:
    s = s.replace(" ", "").replace(" ", "").replace(" ", "").replace(",", ".")
    return float(s)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s)


def park_keys(name: str) -> list[str]:
    """Специфические слова названия парка: «Parc de la Porte de Ninove - Ninoofsepoortpark»
    → ['porte', 'ninove', 'ninoofsepoortpark']. Общие слова отброшены."""
    keys = []
    for part in name.split(" - "):
        for w in norm(part).split():
            if len(w) >= 4 and w not in GENERIC:
                keys.append(w)
    return keys


def main() -> int:
    contracts = json.loads(CONTRACTS.read_text())
    parks = json.loads(PARKS.read_text())["features"]
    audit = {r["osm"]: r for r in csv.DictReader(AUDIT.open())}

    # ── бюджеты ──────────────────────────────────────────────────────────────
    budgets = {}
    for c in contracts:
        found = {}
        for label, num in MONEY.findall(c["description"]):
            try:
                found[label] = to_eur(num)
            except ValueError:
                continue
        total = found.get("Total") or found.get("Région") or found.get("Region")
        if total:
            budgets[c["id"]] = {"total_eur": total, "parts": found}
    print(f"контрактов: {len(contracts)}, бюджет извлечён у {len(budgets)}")
    vals = sorted(b["total_eur"] for b in budgets.values())
    if vals:
        print(f"  сумма {sum(vals):,.0f} € · медиана {vals[len(vals)//2]:,.0f} € · макс {vals[-1]:,.0f} €")
    OUT_BUDGETS.write_text(json.dumps(
        {str(k): v for k, v in budgets.items()}, ensure_ascii=False, indent=1))

    # ── связи контракт → парк: описание обязано НАЗВАТЬ парк рядом со словом
    # «parc/park». Одно общее слово («ouest», «ligne», «jardin») цепляло полгорода.
    # Плюс фильтр по частоте: слово, встречающееся больше чем в 6 описаниях
    # из 98, — не имя, а язык.
    texts = {c["id"]: norm(c["description"] + " " + c["name"]) for c in contracts}
    def df(word): return sum(1 for t in texts.values() if re.search(rf"\b{re.escape(word)}\b", t))
    in_city = [f for f in parks if f["properties"].get("in_brussels", True)]
    links = []
    for f in in_city:
        fr = f["properties"]["name"].split(" - ")[0]
        core = [w for w in norm(fr).split() if w not in GENERIC and len(w) >= 3]
        core = [w for w in core if df(w) <= 6]           # частотные слова вон
        if not core:
            continue
        pat = r"\b(?:parc|park|square|jardin)\w*\s+(?:(?:de|du|des|la|le|l|d|van|het)\s+){0,3}" + r"\s+(?:(?:de|du|des|la|le|l|d)\s+){0,2}".join(re.escape(w) for w in core)
        for c in contracts:
            if re.search(pat, texts[c["id"]]):
                links.append((c, f))

    by_park = defaultdict(list)
    for c, f in links:
        by_park[f["properties"]["osm"]].append(c["id"])

    rows = []
    for c, f in links:
        p = f["properties"]; a = audit.get(p["osm"], {})
        completion = c["year_end"] + 1
        w = windows_for_completion(completion)
        if c["year_end"] <= 2019 and completion <= 2019:
            timing = "сдан до окна «до» — обе базы после проекта"
        elif completion >= 2021:
            timing = "сдан в окне «после» — стандартное окно ловит стройку"
        else:
            timing = "укладывается в стандартное окно"
        rows.append({
            "contract_id": c["id"], "contract": c["name"], "commune": c["commune"],
            "years": f"{c['year_start']}–{c['year_end']}", "completion_proxy": completion,
            "budget_total_eur": budgets.get(c["id"], {}).get("total_eur", ""),
            "park": p["name"].split(" - ")[0], "osm": p["osm"], "area_ha": p["area_ha"],
            "ndvi_effect": a.get("ndvi_effect", ""), "verdict": a.get("verdict", "не измерен"),
            "timing_standard_window": timing,
            "own_window": w["label"] if w else "нет данных Sentinel-2 на окно «до»",
            "contracts_on_same_park": len(by_park[p["osm"]]),
        })
    rows.sort(key=lambda r: (r["contract_id"], r["park"]))
    with OUT_LINKS.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["none"])
        wr.writeheader(); wr.writerows(rows)

    print(f"\nсвязей контракт→парк по имени в описании: {len(rows)} "
          f"({len({r['contract_id'] for r in rows})} контрактов, {len(by_park)} парков)")
    print(f"\n{'контракт':<22}{'годы':<11}{'бюджет':>14}  {'парк':<26}{'га':>5}{'эффект':>9}  {'вердикт':<22}сроки")
    print("-" * 130)
    for r in rows:
        b = f"{r['budget_total_eur']:,.0f}" if r["budget_total_eur"] else "—"
        e = f"{float(r['ndvi_effect']):+.3f}" if r["ndvi_effect"] else "—"
        print(f"{r['contract'][:20]:<22}{r['years']:<11}{b:>14}  {r['park'][:24]:<26}{r['area_ha']:>5.1f}{e:>9}  "
              f"{r['verdict'][:20]:<22}{r['timing_standard_window'][:34]}")

    ok = [r for r in rows if r["timing_standard_window"].startswith("укладывается") and r["budget_total_eur"]
          and r["verdict"] in ("ПОЗЕЛЕНЕЛ", "ПОТЕРЯЛ", "шум")]
    print(f"\nстрок, пригодных для бенчмарка по стандартному окну (бюджет + вердикт + сроки): {len(ok)}")
    print(f"→ {OUT_BUDGETS}\n→ {OUT_LINKS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
