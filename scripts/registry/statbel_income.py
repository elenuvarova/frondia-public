#!/usr/bin/env python3
"""Облагаемый доход по секторам из таблицы Statbel — медиана и среднее последнего года, для любого города.

Зачем. Доход в пакетах был разный: у Брюсселя медиана Statbel 2023, у Антверпена
среднее той же таблицы (так его принёс spot-finder, `MEAN_INCOME`). Терцили и
отношения «беднейшая треть к богатейшей» по разным величинам между городами не
сравниваются. Этот выгрузчик берёт одну и ту же таблицу и одну и ту же величину.

Источник: `TF_PSNL_INC_TAX_SECTOR.xlsx` (Statbel, ряд с 2005 года), лежит в кеше
`spot-finder-geo`. Лист читается потоково: 160 МБ XML в память не грузятся.
Правило отбора — как у брюссельского файла, сделанного раньше: все строки
последнего года по коммунам города, включая «вне сектора» (ZZZZ) и пустые
медианы, где Statbel скрыл значение для малых секторов.

Проверка: `--city brussels --check` сравнивает результат с `data/brussels_income.csv`
байт в байт — выгрузчик обязан повторить уже используемый файл.

    python3 scripts/registry/statbel_income.py --city antwerp
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.adapters import ADAPTERS  # noqa: E402

SOURCE = ROOT.parent / "spot-finder-geo/pipeline/data/statbel_cache/TF_PSNL_INC_TAX_SECTOR.xlsx"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
FIELDS = ["id", "year", "median_income", "mean_income", "n_taxpayers", "name_fr"]


def rows(path: Path):
    """Строки листа как словари по заголовку; значения — текст ячеек как в источнике."""
    with zipfile.ZipFile(path) as z:
        shared = []
        for _, el in ET.iterparse(z.open("xl/sharedStrings.xml")):
            if el.tag == NS + "si":
                shared.append("".join(t.text or "" for t in el.iter(NS + "t")))
                el.clear()
        head = None
        for _, el in ET.iterparse(z.open("xl/worksheets/sheet1.xml")):
            if el.tag != NS + "row":
                continue
            vals = {}
            for c in el.findall(NS + "c"):
                col = "".join(ch for ch in c.get("r", "") if ch.isalpha())
                v = c.find(NS + "v")
                vals[col] = "" if v is None else shared[int(v.text)] if c.get("t") == "s" else v.text
            el.clear()
            if head is None:
                head = vals
                continue
            yield {head[k]: vals.get(k, "") for k in head}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True, choices=list(ADAPTERS))
    ap.add_argument("--source", default=str(SOURCE))
    ap.add_argument("--check", action="store_true", help="сравнить с уже лежащим файлом, не перезаписывая")
    args = ap.parse_args()

    refnis = sorted({u.id[:5] for u in ADAPTERS[args.city]().units()})
    picked = [r for r in rows(Path(args.source)) if r["CD_MUNTY_REFNIS"] in refnis]
    year = max(r["CD_YEAR"] for r in picked)
    picked = [r for r in picked if r["CD_YEAR"] == year]

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(FIELDS)
    for r in picked:
        w.writerow([r["CD_SECTOR"], r["CD_YEAR"], r["MS_MEDIAN_NET_TAXABLE_INC"],
                    r["MS_AVG_TOT_NET_TAXABLE_INC"], r["MS_NBR_NON_ZERO_INC"], r["TX_SECTOR_DESCR_FR"]])
    out = ROOT / f"data/{args.city}_income.csv"
    n_med = sum(1 for r in picked if r["MS_MEDIAN_NET_TAXABLE_INC"])
    print(f"{args.city}: коммун {len(refnis)}, год {year}, строк {len(picked)}, с медианой {n_med}")
    data = buf.getvalue().encode("utf-8")       # окончания строк \r\n, как пишет модуль csv
    if args.check:
        same = out.exists() and out.read_bytes() == data
        print(f"  сверка с {out.relative_to(ROOT)}: {'совпадает байт в байт' if same else 'РАСХОДИТСЯ'}")
        return 0 if same else 1
    out.write_bytes(data)
    print(f"→ {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
