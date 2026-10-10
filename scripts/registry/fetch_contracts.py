#!/usr/bin/env python3
"""
Сбор реестра брюссельских квартальных контрактов с quartiers.brussels.

Что это даёт
────────────
Каждая страница /1/q/NN — один контракт: название, коммуна, годы и текстовое
описание программы, где перечислены конкретные меры («déminéralisation et
verdurisation de l'espace public», «réaménagement de l'avenue…»).

Это тот самый слой документов, без которого детектор изменений по спутнику
даёт ложноположительные результаты (см. кейс Zavelenberg в CLAUDE.md).

Здесь только СБОР сырья. Структурирование мер — отдельный шаг (LLM-экстракция),
чтобы сырые страницы можно было перечитать и проверить извлечённое.

Запуск:
    .venv/bin/python scripts/registry/fetch_contracts.py --max-id 200
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://quartiers.brussels/1/q/{}"
OUT_RAW = Path("data/registry/contracts_raw.json")
UA = "map-project-research/0.1 (urban intervention registry; research)"

# «Contrat de Quartier Durable | Bruxelles (2021 - 2025)»
HEADER_RE = re.compile(
    r"(Contrat de [^|]+?)\s*\|\s*([^(]+?)\s*\((\d{4})\s*[-–—]\s*(\d{4})\)",
    re.I,
)


def strip_html(html: str) -> str:
    txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = (txt.replace("&nbsp;", " ").replace("&amp;", "&")
              .replace("&#39;", "'").replace("&quot;", '"')
              .replace("&eacute;", "é").replace("&egrave;", "è"))
    return re.sub(r"\s+", " ", txt).strip()


def fetch(url: str, timeout: int = 30) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return None
            return r.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return None


def parse(qid: int, html: str) -> dict | None:
    title = ""
    m = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
    if m:
        title = strip_html(m.group(1))

    text = strip_html(html)

    # Отрезаем общую навигацию: содержание начинается после названия квартала
    head = HEADER_RE.search(text)
    if not head:
        return None

    name = title.split("-")[-1].strip() if "-" in title else title.strip()
    contract_type, commune, y0, y1 = (g.strip() for g in head.groups())

    # Описание — всё после строки заголовка, до служебных хвостов
    body = text[head.end():]
    for stop in ("Documentation", "Partenaires", "Contact", "Newsletter"):
        i = body.find(stop)
        if 200 < i < len(body):
            body = body[:i]
    body = body.strip()

    return {
        "id": qid,
        "url": BASE.format(qid),
        "name": name,
        "contract_type": contract_type,
        "commune": commune,
        "year_start": int(y0),
        "year_end": int(y1),
        "description": body[:6000],
        "description_chars": len(body),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Сбор реестра квартальных контрактов")
    ap.add_argument("--max-id", type=int, default=200)
    ap.add_argument("--delay", type=float, default=0.4, help="пауза между запросами, с")
    args = ap.parse_args()

    OUT_RAW.parent.mkdir(parents=True, exist_ok=True)
    found, misses = [], 0

    for qid in range(1, args.max_id + 1):
        html = fetch(BASE.format(qid))
        rec = parse(qid, html) if html else None
        if rec:
            found.append(rec)
            print(f"  {qid:>3}  {rec['commune'][:18]:<18} "
                  f"{rec['year_start']}–{rec['year_end']}  {rec['name'][:34]}")
        else:
            misses += 1
        time.sleep(args.delay)

    OUT_RAW.write_text(json.dumps(found, ensure_ascii=False, indent=1))

    print(f"\nСобрано контрактов: {len(found)} (пустых id: {misses})")
    if found:
        years = [r["year_start"] for r in found]
        communes = {}
        for r in found:
            communes[r["commune"]] = communes.get(r["commune"], 0) + 1
        print(f"Годы начала: {min(years)}–{max(years)}")
        print("Коммуны:", ", ".join(f"{k} ({v})" for k, v in
                                    sorted(communes.items(), key=lambda x: -x[1])[:10]))
        print(f"→ {OUT_RAW}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
