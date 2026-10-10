#!/usr/bin/env python3
"""Возрастная структура секторов: Census 2021, Statbel.

Зачем. До сих пор справедливость меряли одним признаком — доходом. Но к жаре и
к нехватке зелени уязвимы не «бедные вообще», а вполне определённые группы:
**дети до 15 и люди старше 65**. Регламент (EU) 2024/1991 о них молчит, как и о
доходе; медицинская литература — нет. Слой добавляет второе измерение к тому же
сектору Statbel, на котором уже стоит всё остальное.

Источник: `TF_CENSUS_2021_S01` — население по сектору, полу и возрастной группе,
всё население Бельгии, 662 964 строки. Открытые данные Statbel.

Итог: `cities/<city>/layers/population_age.csv` — по сектору доли и абсолютные
числа четырёх групп, плюс запись в манифест с границами применимости.

    .venv/bin/python scripts/registry/fetch_statbel_age.py --city brussels
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.config import CITIES  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402

URL = ("https://statbel.fgov.be/sites/default/files/files/opendata/"
       "TF_CENSUS_2021/TF_CENSUS_2021_S01.zip")
CACHE = Path("data/registry/statbel_census_2021_s01.zip")

# Группы: до 15 — дети, 15–64 — трудоспособные, 65+ — пожилые, 80+ отдельно как
# самая уязвимая к жаре подгруппа (входит в 65+, не суммируется с ней).
BANDS = {"children_0_14": range(0, 15), "adults_15_64": range(15, 65),
         "seniors_65_plus": range(65, 121), "seniors_80_plus": range(80, 121)}


def band_of(code: str) -> list[str]:
    """Возрастная группа Census вида '0-4', '85+' → наши полосы."""
    code = code.strip()
    if code.endswith("+"):
        lo = int(code[:-1]); hi = lo
    elif "-" in code:
        lo, hi = (int(x) for x in code.split("-", 1))
    else:
        try:
            lo = hi = int(code)
        except ValueError:
            return []
    mid = (lo + hi) // 2
    return [name for name, rng in BANDS.items() if mid in rng]


def download() -> bytes:
    if CACHE.exists():
        return CACHE.read_bytes()
    print(f"скачиваю Census 2021 (около 5 МБ)…")
    req = urllib.request.Request(URL, headers={"User-Agent": "frondia-research/0.1"})
    with urllib.request.urlopen(req, timeout=300) as f:
        data = f.read()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_bytes(data)
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="brussels", choices=list(CITIES))
    args = ap.parse_args()
    city = args.city

    ad = ADAPTERS[city]()
    units = {u.id: u for u in ad.units()}
    print(f"{city}: секторов в адаптере {len(units)}")

    raw = download()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        txt = z.read(z.namelist()[0]).decode("utf-8-sig", errors="replace")

    agg: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    rows = csv.DictReader(io.StringIO(txt), delimiter="|")
    seen = 0
    for r in rows:
        sid = (r.get("CD_SECTOR") or "").strip()
        if sid not in units:
            continue
        seen += 1
        pop = int(float(r.get("MS_POP") or 0))
        agg[sid]["total"] += pop
        for b in band_of(r.get("CD_AGE") or ""):
            agg[sid][b] += pop
    print(f"строк по этому городу: {seen}, секторов с данными: {len(agg)}")

    out = Path(f"cities/{city}/layers/population_age.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["id", "name", "population_census", "children_0_14", "adults_15_64",
              "seniors_65_plus", "seniors_80_plus", "share_children", "share_seniors"]
    n_written = 0
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for sid, u in units.items():
            a = agg.get(sid)
            if not a or not a["total"]:
                continue
            t = a["total"]
            w.writerow({"id": sid, "name": u.name or "", "population_census": t,
                        "children_0_14": a["children_0_14"], "adults_15_64": a["adults_15_64"],
                        "seniors_65_plus": a["seniors_65_plus"], "seniors_80_plus": a["seniors_80_plus"],
                        "share_children": round(a["children_0_14"] / t, 4),
                        "share_seniors": round(a["seniors_65_plus"] / t, 4)})
            n_written += 1

    total = sum(a["total"] for a in agg.values())
    kids = sum(a["children_0_14"] for a in agg.values())
    old = sum(a["seniors_65_plus"] for a in agg.values())
    oldest = sum(a["seniors_80_plus"] for a in agg.values())
    print(f"население по переписи {total:,}: детей до 15 — {kids:,} ({kids / total:.1%}), "
          f"65+ — {old:,} ({old / total:.1%}), из них 80+ — {oldest:,}".replace(",", " "))

    m = Manifest.read(city)
    m.add(LayerEntry(
        layer="population_age", computed=date.today().isoformat(), n_units=n_written,
        measures="возрастная структура сектора: дети до 15, трудоспособные, 65+ и 80+ отдельно",
        unit="человек и доля",
        method="суммирование по полу и возрастным группам переписи до четырёх полос; "
               "80+ входит в 65+ и с ней не складывается",
        source="Statbel, Census 2021, таблица TF_CENSUS_2021_S01 (население по сектору, полу, возрасту)",
        threshold=None,
        threshold_source="порога нет: это состояние населения, а не изменение против контроля",
        limits=["перепись 2021 года — состояние на её дату, а не на 2024-й",
                "возрастная полоса приписывается по середине интервала переписи",
                "малые секторы Statbel могут быть округлены для защиты приватности"]))
    m.write()
    print(f"→ {out} · слоёв в манифесте {len(m.layers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
