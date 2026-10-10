#!/usr/bin/env python3
"""
Statistical sectors of a Belgian city taken as its municipality (phase 2b, docs/07-unified-frondia.md):
Ghent (REFNIS 44021), Liège (62063), Charleroi (52011).

The city is the municipality itself, the sectors carrying its REFNIS, not a box around it. That is the
unit Article 8 counts (one LAU), and it keeps neighbouring municipalities out of the city's scales
(Antwerp's file, clipped by a box in spot-finder, carries some; Brussels is the region). Names are
Statbel's in the city's language: Dutch in Ghent, French in Liège and Charleroi.

Inputs, all Statbel open data already on disk:
  * the sector register 2024 (geometry in Lambert 72 with names and former municipalities), the copy in
    the sibling repository `neighbourhood_fit_score`;
  * population by sector on 1 January 2024 (`OPENDATA_SECTOREN_2024.xlsx`), the copy in `spot-finder-geo`.

Writes `data/<city>_sectors.geojson` (WGS84: CD_SECTOR, TX_SECTOR_DESCR_NL — the sector's name in the
city's language, the field name kept for the adapters — district, POPULATION) and
`data/<city>_sector_names.csv` (id, name_nl, district), the shape the Antwerp adapter reads. The district
is the former municipality: Ledeberg, Gentbrugge… in Ghent; Grivegnée, Jupille… in Liège.

Needs geopandas and openpyxl, which Frondia's own environment does not carry; run it with a geodata
environment, e.g. the SpotFinder pipeline's:

    ../spot-finder-geo/.venv/bin/python scripts/registry/city_sectors.py --city ghent
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = (ROOT.parent / "neighbourhood_fit_score/backend/pipeline/data/raw/"
            "sh_statbel_statistical_sectors_31370_20240101.sqlite/"
            "sh_statbel_statistical_sectors_31370_20240101.sqlite")
LAYER = "sh_statbel_statistical_sectors_31370_20240101"
POPULATION = ROOT.parent / "spot-finder-geo/pipeline/data/statbel_cache/OPENDATA_SECTOREN_2024.xlsx"
CITIES = {"ghent": ("44021", "nl"), "liege": ("62063", "fr"), "charleroi": ("52011", "fr")}


def population(REFNIS: str) -> dict[str, int]:
    df = pd.read_excel(POPULATION)
    code = next(c for c in df.columns if str(c).upper() in ("CD_SECTOR", "SECTOR_CD", "CD_SECTOR_NL"))
    val = next(c for c in df.columns if str(c).upper() in ("POPULATION", "TOTAL", "MS_POPULATION", "MS_POP"))
    df = df[df[code].astype(str).str.startswith(REFNIS)]
    return {str(k).strip(): int(v) for k, v in df.groupby(code)[val].sum().items()}


# Walloon sub-municipalities as Statbel writes them: upper case, no accents, with the slivers of other
# municipalities booked to them. The district is the former municipality as it is spelt.
DISTRICT_FR = {
    "LIEGE(MEUSE NORD) + PARTIE DE HERSTAL,SAINT-NICOLAS,VOTTEM": "Liège (north)",
    "LIEGE(MEUSE SUD)": "Liège (south)",
    "GRIVEGNEE": "Grivegnée", "CHENEE": "Chênée",
    "ANGLEUR + PARTIE DE OUGREE + PARTIE DE TILFF ET DE EMBOURG": "Angleur",
    "PARTIE DE OUGREE": "Ougrée", "GLAIN & PARTIE ANS": "Glain", "PARTIE ANS": "Ans",
    "ROCOURT + PARTIE DE VOROUX-LEZ-LIERS": "Rocourt",
    "GOSSELIES + PARTIE DE WAYAUX": "Gosselies",
    "MODIFICATION DE LIMITE COMMUNALE": "Charleroi",   # sectors added by a boundary change
}


def district(sub: str, lang: str = "nl") -> str:
    """Statbel's sub-municipality in plain type: "SINT-DENIJS-WESTREM - AFSNEE" → "Sint-Denijs-Westrem, Afsnee",
    "ZWIJNAARDE*+DEEL VAN MERELBEKE" → "Zwijnaarde" (a sliver of Merelbeke is booked with it)."""
    raw = (sub or "").split("*")[0].strip()
    if lang == "fr" and raw in DISTRICT_FR:
        return DISTRICT_FR[raw]
    s = raw.replace(" - ", ", ")
    small = {"de", "du", "des", "la", "le", "les", "sur", "lez", "au", "aux", "en"} if lang == "fr" else set()
    def word(w, first):
        return w if (w in small and not first) else w.capitalize()
    return "-".join(" ".join(word(w, i == 0 and j == 0) for i, w in enumerate(part.split(" ")))
                    for j, part in enumerate(s.lower().split("-")))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True, choices=list(CITIES))
    city = ap.parse_args().city
    REFNIS, lang = CITIES[city]
    OUT, NAMES = ROOT / f"data/{city}_sectors.geojson", ROOT / f"data/{city}_sector_names.csv"
    g = gpd.read_file(REGISTRY, layer=LAYER)
    g = g[g["cd_munty_refnis"].astype(str) == REFNIS].copy()
    pop = population(REFNIS)
    g = g.to_crs(4326)
    feats, names = [], []
    for _, r in g.sort_values("cd_sector").iterrows():
        sid = str(r["cd_sector"]).strip()
        d = district(r[f"tx_sub_munty_{lang}"] or r[f"tx_munty_descr_{lang}"], lang)
        name = " ".join(str(r[f"tx_sector_descr_{lang}"]).split())
        feats.append({"type": "Feature",
                      "properties": {"CD_SECTOR": sid, "TX_SECTOR_DESCR_NL": name, "district": d,
                                     "POPULATION": pop.get(sid, 0)},
                      "geometry": json.loads(gpd.GeoSeries([r.geometry], crs=4326).to_json())["features"][0]["geometry"]})
        names.append({"id": sid, "name_nl": name, "district": d})
    OUT.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, ensure_ascii=False))
    with NAMES.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "name_nl", "district"])
        w.writeheader()
        w.writerows(names)
    total = sum(f["properties"]["POPULATION"] for f in feats)
    missing = [f["properties"]["CD_SECTOR"] for f in feats if f["properties"]["CD_SECTOR"] not in pop]
    print(f"→ {OUT.relative_to(ROOT)}: {len(feats)} sectors, population {total:,}, without a population row: {len(missing)}")
    print("  districts:", sorted({n['district'] for n in names}))


if __name__ == "__main__":
    main()
