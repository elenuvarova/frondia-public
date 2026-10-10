#!/usr/bin/env python3
"""Official Dutch and French names of the five cities' sectors and communes, from Statbel's sector register (plan 5, L4).

Source: Statbel open data, "Statistische sectoren 2024" — the SQLite file
`sh_statbel_statistical_sectors_31370_20240101.sqlite.zip` (30 642 340 bytes, Last-Modified 16 Jul 2024), table
`sh_statbel_statistical_sectors_31370_20240101`. Licence: Statbel open data licence (CC BY 4.0), attribution "Statbel".
The zip is downloaded once into `data/raw/statbel/` (ignored by git) and checked against its SHA-256: a different file
stops the script rather than silently renaming places.

Join: `cd_sector` = the sector's `id` in the site's data; the commune is `cd_munty_refnis` = the first five characters
of the id (the commune's `code`). Only names are taken — no geometry, no numbers.

Output: `data/statbel_names_2024.csv` — `id,sector_nl,sector_fr,sub_nl,sub_fr,refnis,munty_nl,munty_fr`, one row per
sector of the five cities (the sector files of `scripts/site/site_data.py`'s `SECTORS_GEO`), sorted by id. Every text
goes through `clean()`. A sector missing from the register fails the run with the list of missing ids.

Standard library only (it must not import `site_data`, which pulls in Earth Engine). Run from the repo root:

    .venv/bin/python -m scripts.registry.statbel_names
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URL = ("https://statbel.fgov.be/sites/default/files/files/opendata/Statistische%20sectoren/"
       "sh_statbel_statistical_sectors_31370_20240101.sqlite.zip")
SHA256 = "af1564edc6ebc807e455c13dc8373d747ef1096322fc005c22547a5640c81d8f"
ZIP = ROOT / "data/raw/statbel/sh_statbel_statistical_sectors_31370_20240101.sqlite.zip"
TABLE = "sh_statbel_statistical_sectors_31370_20240101"
MEMBER = f"{TABLE}.sqlite/{TABLE}.sqlite"
OUT = ROOT / "data/statbel_names_2024.csv"
COLUMNS = ["id", "sector_nl", "sector_fr", "sub_nl", "sub_fr", "refnis", "munty_nl", "munty_fr"]
# the same files and id fields as site_data.SECTORS_GEO (kept here so this script needs no third-party import);
# tests/test_names.py fails if a sector of the site's data is missing from the output
SECTORS_GEO = {"brussels": ("data/brussels_sectors.geojson", "id"), "antwerp": ("data/antwerp_sectors.geojson", "CD_SECTOR"),
               "ghent": ("data/ghent_sectors.geojson", "CD_SECTOR"), "liege": ("data/liege_sectors.geojson", "CD_SECTOR"),
               "charleroi": ("data/charleroi_sectors.geojson", "CD_SECTOR")}


def clean(s: str | None) -> str:
    """Whitespace collapsed and trimmed, no space just inside brackets; None → ""."""
    if s is None:
        return ""
    s = re.sub(r"\s+", " ", str(s)).strip()
    return s.replace("( ", "(").replace(" )", ")")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch() -> Path:
    """The register's zip, downloaded into ZIP if it is not there yet, and checked against SHA256."""
    if not ZIP.exists():
        ZIP.parent.mkdir(parents=True, exist_ok=True)
        part = ZIP.with_suffix(".part")
        print(f"  downloading {URL}")
        with urllib.request.urlopen(URL, timeout=120) as r, part.open("wb") as f:
            while block := r.read(1 << 20):
                f.write(block)
        part.replace(ZIP)
    got = sha256(ZIP)
    if got != SHA256:
        raise SystemExit(f"Statbel's file changed: SHA-256 {got}, expected {SHA256} ({ZIP}); if the download was cut short, delete it and retry")
    return ZIP


def read_register(zip_path: Path) -> dict[str, dict]:
    """Sector code → its names in the register (raw, not yet cleaned)."""
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(zip_path) as z:
        p = Path(z.extract(MEMBER, tmp))
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
        try:
            rows = con.execute(
                "select cd_sector, tx_sector_descr_nl, tx_sector_descr_fr, tx_sub_munty_nl, tx_sub_munty_fr, "
                f"cd_munty_refnis, tx_munty_descr_nl, tx_munty_descr_fr from {TABLE}").fetchall()
        finally:
            con.close()
    return {r[0]: dict(zip(["sector_nl", "sector_fr", "sub_nl", "sub_fr", "refnis", "munty_nl", "munty_fr"], r[1:]))
            for r in rows}


def site_sector_ids() -> list[str]:
    ids = set()
    for path, key in SECTORS_GEO.values():
        for f in json.loads((ROOT / path).read_text())["features"]:
            ids.add(str(f["properties"][key]))
    return sorted(ids)


def main() -> int:
    reg = read_register(fetch())
    ids = site_sector_ids()
    missing = [i for i in ids if i not in reg]
    if missing:
        raise SystemExit(f"{len(missing)} sectors not in Statbel's register: {', '.join(missing)}")
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COLUMNS)
        for i in ids:
            r = reg[i]
            w.writerow([i, *(clean(r[k]) for k in COLUMNS[1:])])
    differ = sum(clean(reg[i]["sector_nl"]) != clean(reg[i]["sector_fr"]) for i in ids)
    print(f"  {OUT.relative_to(ROOT)}  {len(ids)} sectors, {len({reg[i]['refnis'] for i in ids})} communes, "
          f"{differ} sector names differ between Dutch and French")
    return 0


if __name__ == "__main__":
    sys.exit(main())
