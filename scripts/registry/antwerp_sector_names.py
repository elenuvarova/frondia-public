#!/usr/bin/env python3
"""Названия антверпенских секторов и районы — из реестра Statbel, по коду сектора.

Файл секторов из spot-finder несёт код, население и доход, но не название: на
страницах Антверпена сектор назывался своим кодом. Реестр Statbel 2024 (копия
лежит в соседнем репозитории neighbourhood_fit_score) даёт TX_SECTOR_DESCR_NL и
деление на районы. Берутся только атрибуты по коду, геометрия остаётся прежней.

Район. У коммуны Антверпен поле подмуниципалитета — это либо бывшая коммуна
(Deurne, Berchem…), либо номер административного квартала центра, либо порт.
Кварталы центра, Linkeroever и Шельда → район «Antwerpen»; «2 EN 3 DISTRICT
HAVENGEBIED» → «Haven»; остальное — имя бывшей коммуны. У соседних коммун
район — сама коммуна (Mortsel, Beveren…): раньше они значились «Antwerpen».

    python3 scripts/registry/antwerp_sector_names.py [--registry <sqlite>] [--relabel]

--relabel подставляет названия в уже посчитанные слои и дела, не трогая чисел:
поле name — там, где оно равно коду сектора; поле commune — там, где стоит прежнее
значение по умолчанию «Antwerpen». Формат файла (отступ JSON, окончания строк CSV)
сохраняется; изменённые строки печатаются счётом, чтобы подмену было видно.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = (ROOT.parent / "neighbourhood_fit_score/backend/pipeline/data/raw/"
            "sh_statbel_statistical_sectors_31370_20240101.sqlite/"
            "sh_statbel_statistical_sectors_31370_20240101.sqlite")
TABLE = "sh_statbel_statistical_sectors_31370_20240101"
SECTORS = ROOT / "data/antwerp_sectors.geojson"
OUT = ROOT / "data/antwerp_sector_names.csv"


def clean(name: str) -> str:
    s = re.sub(r"\s+", " ", name or "").strip()
    return s.replace("( ", "(").replace(" )", ")")


def district(sub: str, municipality: str) -> str:
    if municipality != "Antwerpen":
        return municipality
    s = (sub or "").upper()
    if "HAVENGEBIED" in s:
        return "Haven"
    if "ADMINISTR" in s or s in ("LINKEROEVER", "SCHELDE", ""):
        return "Antwerpen"
    return s.title()


RELABEL = ["cities/antwerp/layers/*.csv", "cities/antwerp/layers/*_summary.json",
           "data/monitoring_antwerp_*.csv", "data/registry/cases/droogdokkenpark.json",
           "data/registry/cases/spoor-noord.json"]


def _fix(rec: dict, names: dict) -> int:
    sid = rec.get("id")
    if not isinstance(sid, str) or sid not in names:
        return 0
    n = 0
    if "name" in rec and rec["name"] in (sid, "", None):
        rec["name"] = names[sid]["name_nl"]
        n += 1
    if "commune" in rec and rec["commune"] == "Antwerpen" and names[sid]["district"] != "Antwerpen":
        rec["commune"] = names[sid]["district"]
        n += 1
    return n


def relabel(names: dict) -> None:
    def walk(o) -> int:
        if isinstance(o, dict):
            return _fix(o, names) + sum(walk(v) for v in o.values())
        if isinstance(o, list):
            return sum(walk(v) for v in o)
        return 0

    for pattern in RELABEL:
        for p in sorted(ROOT.glob(pattern)):
            raw = p.read_text(encoding="utf-8")
            if p.suffix == ".csv":
                nl = "\r\n" if "\r\n" in raw else "\n"
                rows = list(csv.DictReader(raw.splitlines()))
                if not rows or "id" not in rows[0] or "name" not in rows[0]:
                    continue
                n = sum(_fix(r, names) for r in rows)
                if not n:
                    continue
                import io
                buf = io.StringIO()
                w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator=nl)
                w.writeheader()
                w.writerows(rows)
                new = buf.getvalue()
            else:
                obj = json.loads(raw)
                n = walk(obj)
                if not n:
                    continue
                second = raw.split("\n", 2)[1] if "\n" in raw else ""
                indent = len(second) - len(second.lstrip(" ")) or None
                new = json.dumps(obj, ensure_ascii=False, indent=indent) + ("\n" if raw.endswith("\n") else "")
            changed = sum(a != b for a, b in zip(raw.splitlines(), new.splitlines()))
            if len(raw.splitlines()) != len(new.splitlines()):
                raise SystemExit(f"{p}: при подстановке изменилось число строк — остановлено")
            p.write_text(new, encoding="utf-8")
            print(f"  {p.relative_to(ROOT)}: полей {n}, строк изменено {changed}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default=str(REGISTRY))
    ap.add_argument("--relabel", action="store_true", help="подставить названия в посчитанные слои и дела")
    args = ap.parse_args()

    ids = [f["properties"]["CD_SECTOR"] for f in json.loads(SECTORS.read_text())["features"]]
    con = sqlite3.connect(args.registry)
    q = (f'select cd_sector, tx_sector_descr_nl, tx_sub_munty_nl, tx_munty_descr_nl from "{TABLE}" '
         f'where cd_sector in ({",".join("?" * len(ids))})')
    found = {r[0]: r for r in con.execute(q, ids)}
    con.close()
    missing = [i for i in ids if i not in found]
    if missing:
        raise SystemExit(f"нет в реестре Statbel: {missing[:10]} (всего {len(missing)})")

    with OUT.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "name_nl", "district", "municipality"])
        for i in ids:
            _, name, sub, mun = found[i]
            w.writerow([i, clean(name), district(sub, mun), mun])
    by = {}
    for i in ids:
        d = district(found[i][2], found[i][3])
        by[d] = by.get(d, 0) + 1
    print(f"→ {OUT.relative_to(ROOT)} · секторов {len(ids)} · районов и коммун {len(by)}")
    print("  " + ", ".join(f"{k} {v}" for k, v in sorted(by.items(), key=lambda t: -t[1])))
    if args.relabel:
        print("подстановка названий в посчитанные файлы:")
        relabel({r["id"]: r for r in csv.DictReader(OUT.open())})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
