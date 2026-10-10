#!/usr/bin/env python3
"""
Data download with its manifest (phase 2b, docs/07-unified-frondia.md).

Every layer behind the atlas as a CSV in English, and next to it a manifest that says, layer by
layer, what it measures, how, from what source, with what threshold and where that threshold comes
from, what it cannot do, what every column means and under what terms it may be reused — so any
number on the site can be recomputed from the files alone.

The city packages (cities/<city>/) stay the source: their layers and their Russian manifests are
not touched. This script reads them and writes

    site/public/downloads/<city>/<layer>.csv     one per layer, cell labels in English
    site/public/downloads/<city>/manifest.json   the English manifest
    site/public/data/downloads.json              the index the /data page reads
    site/public/data/downloads.<loc>.json        the same index with its words in Dutch or French, for every
                                                 language with data texts (scripts/site/texts.py, L5); the files
                                                 themselves and their manifest stay English (L6)

Run with site_data.py (it calls `write_all`), or on its own:
    .venv/bin/python scripts/site/downloads.py
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.config import CONTROL  # noqa: E402
from engine.manifest import Manifest  # noqa: E402
from scripts.site.texts import Catalog, Join, Num, Place, T, Text, available, render, LOCS  # noqa: E402

SITE = ROOT / "site" / "public"
CITY_NAME = {"brussels": "Brussels", "antwerp": "Antwerp", "ghent": "Ghent", "liege": "Liège", "charleroi": "Charleroi"}

# the cells of the Russian layers that are words, not numbers
VERDICT = {"рост": "up", "потеря": "down", "шум": "noise", "контроль несопоставим": "refused", "не измерено": "not measured"}
DW_LABEL = {"СТРОЙКА": "construction", "ПОТЕРЯ КРОНЫ": "canopy loss", "не подтверждено": "not confirmed", "": ""}
BULLETIN = {"construction": "construction", "confirmed": "canopy loss", "unconfirmed": "not confirmed", "gained": "gained"}

# reuse terms of the sources. A layer that uses OpenStreetMap is a derived database under the ODbL
# and must stay under it; everything else is offered under CC BY 4.0 with its sources credited
ODBL = "ODbL 1.0 (derived from OpenStreetMap)"
CCBY = "CC BY 4.0"
CREDIT = {
    "s2": "Contains modified Copernicus Sentinel data (2016–2026)",
    "dw": "Dynamic World V1 (Google, World Resources Institute), CC BY 4.0",
    "landsat": "Landsat Collection 2 courtesy of the U.S. Geological Survey",
    "clms": "© European Union, Copernicus Land Monitoring Service, European Environment Agency (CLCplus Backbone 2021, HRL Woody Vegetation Layer 2021, HRL Tree Cover Density 2018)",
    "cgls": "Copernicus Global Land Service, Land Cover 100 m (Proba-V, VITO), epoch 2019",
    "worldcover": "© ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium, CC BY 4.0",
    "statbel": "Source: Statbel (Directorate-General Statistics – Statistics Belgium), CC BY 4.0; aggregated and joined by Frondia",
    "gisco": "Eurostat GISCO: LAU 2024, degree of urbanisation 2024, urban centres and clusters 2021; © EuroGeographics for the administrative boundaries",
    "osm": "© OpenStreetMap contributors, ODbL 1.0",
    "gtfs": "Public transport stops and timetables: {transit} open data",
    "bimd": "Deprivation weights: Belgian Index of Multiple Deprivation 2011",
    "groenkaart": "Groenkaart Vlaanderen 2018, 2021, 2024 © Digitaal Vlaanderen / Agentschap voor Natuur en Bos, Modellicentie Gratis Hergebruik",
    "trees_ghent": "Tree register: Stad Gent, locaties-bomen-gent, Modellicentie Gratis Hergebruik",
    "trees_brussels": "Tree register: Ville de Bruxelles, Bruxelles Environnement, Bruxelles Mobilité (arbres-bomen-vbx-be-bm), CC BY 4.0",
    "trees_antwerp": "Tree register: Stad Antwerpen, layer boom (geodata.antwerpen.be); the source states no licence, so only counts per sector are published",
}

SECTOR_COLS = {
    "id": "Statbel statistical sector code (the join key of every layer)",
    "name": "sector name, as Statbel writes it",
}


def _row_sectors(city: str) -> list[dict]:
    return [{"id": u.id, "name": u.name, "commune": u.commune, "population": u.population,
             "area_ha": round(u.area_ha, 2), "lon": round(u.centroid[0], 6), "lat": round(u.centroid[1], 6)}
            for u in ADAPTERS[city]().units()]


def _csv(path: Path) -> list[dict]:
    return list(csv.DictReader(path.open(encoding="utf-8")))


def _monitoring(city: str, season: int) -> list[dict]:
    """The season's layer as measured, plus the bulletin's reading after the documents (a sector the
    instruments call a canopy loss can be a building site by the documents: Peterbos, 2026)."""
    from scripts.report.monitoring_html import apply_documents, funnel, load_layer
    man = Manifest.read(city)
    rows = _csv(ROOT / f"cities/{city}/layers/monitoring_{season}.csv")
    F = funnel(apply_documents(load_layer(city, season), city, season), man.layers[f"monitoring_{season}"].threshold)
    reading = {r["id"]: BULLETIN[k] for k in BULLETIN for r in F[k]}
    for r in rows:
        r["dw_label"] = DW_LABEL.get(r["dw_label"], r["dw_label"])
        r["bulletin"] = reading.get(r["id"], "")
    return rows


def _lau(city: str) -> list[dict]:
    rows = _csv(ROOT / f"cities/{city}/layers/art8_official_lau_2021.csv")
    for r in rows:
        g, c = float(r["green_ucuc"]), float(r["canopy_wvl_ucuc"])
        why = []
        if g <= 0.45:
            why.append(f"green {100 * g:.1f}% ≤ 45%")
        if c <= 0.10:
            why.append(f"canopy {100 * c:.1f}% ≤ 10%")
        r["reason"] = "; ".join(why) if why else "green and canopy above both thresholds"
    return rows


def _article8(city: str) -> list[dict]:
    rows = _csv(ROOT / f"cities/{city}/layers/article8_2024.csv")
    for r in rows:
        r["ndvi_verdict"] = VERDICT.get(r["ndvi_verdict"], r["ndvi_verdict"])
        r["trees_verdict"] = VERDICT.get(r["trees_verdict"], r["trees_verdict"])
        r["built_verdict"] = VERDICT.get(r["built_verdict"], r["built_verdict"])
    return rows


def _balance(city: str, season: int) -> list[dict]:
    p = ROOT / f"cities/{city}/layers/art8_balance_{season}.csv"
    if not p.exists():
        return []
    rows = _csv(p)
    for r in rows:
        for k in ("green", "trees", "built"):
            r[f"{k}_verdict"] = VERDICT.get(r[f"{k}_verdict"], r[f"{k}_verdict"])
    return rows


def _if_exists(name):
    def build(city):
        p = ROOT / f"cities/{city}/layers/{name}.csv"
        return _csv(p) if p.exists() else []
    return build


def _points(city: str) -> list[dict]:
    """City Planner's forty ranked candidates per kind of object, with the sector each falls in
    (as the site places it) and the role the rank gives it."""
    src = SITE / "data" / f"points-{city}.json"
    if not src.exists():          # site_data writes it only for a city City Planner has run for
        return []
    site = json.loads(src.read_text())
    sector = {(p["t"], p["r"]): p.get("s") or "" for p in site["points"]}
    # the city's register at the named and comparison points (object_registers.py), keyed like the planner's ranks
    official = {}
    reg, flags = ROOT / f"data/registry/named_points_{city}.json", ROOT / f"data/registry/named_points_{city}_official.csv"
    if reg.exists() and flags.exists():
        sys.path.insert(0, str(ROOT / "scripts/registry"))
        from osm_appearance import taken_out
        fl = {r["point"]: r for r in _csv(flags)}
        for x in json.loads(reg.read_text()):
            t, _, rank = x["unit_id"].partition("#")
            if x["id"] in fl:
                official[(t, int(rank))] = fl[x["id"]] | {"out": taken_out(fl[x["id"]])}
    out = []
    for f in sorted((ROOT / f"cities/{city}/points").glob("*.geojson")):
        g = json.loads(f.read_text())
        kind = g.get("properties", {}).get("asset")
        if not kind:          # the Fit Score improvements are not planner points
            continue
        for ft in sorted(g["features"], key=lambda x: x["properties"]["rank"]):
            p, (lon, lat) = ft["properties"], ft["geometry"]["coordinates"][:2]
            rank = int(p["rank"])
            out.append({"kind": kind, "rank": rank,
                        "role": "named" if rank <= 10 else "comparison" if rank <= 20 else "further",
                        "lon": round(lon, 6), "lat": round(lat, 6), "sector": sector.get((kind, rank), ""),
                        "score": p.get("Score"), "gap_score": p.get("GapScore"), "equity_index": p.get("EquityIndex"),
                        "named_at": p.get("named_at", ""),
                        **({"official_at_point": o["official_at_point"], "official_within_500m": o["official_within_500m"],
                            "map_gap_500m": o["not_in_planner_osm_within_500m"], "out_of_check": o["out"]}
                           if (o := official.get((kind, rank))) else
                           {"official_at_point": "", "official_within_500m": "", "map_gap_500m": "", "out_of_check": ""})})
    return out


def _coverage(city: str) -> list[dict]:
    out = []
    for f in sorted((ROOT / f"cities/{city}/points").glob("*.geojson")):
        pr = json.loads(f.read_text()).get("properties", {})
        if pr.get("asset") and pr.get("coverage_steps"):
            out += [{"kind": pr["asset"], "n": n, "coverage": v, "service_radius_m": pr.get("service_radius_m")}
                    for n, v in enumerate(pr["coverage_steps"])]
    return out


def _passthrough(name):
    return lambda city: _csv(ROOT / f"cities/{city}/layers/{name}.csv")


def _thr(city: str, key: str) -> tuple[float | None, Text | None]:
    """A measured layer's threshold and, in words, where it comes from: a template whose numbers are put in by
    texts.render (thresholds with four decimals; counts as plain integers, as the f-strings wrote them)."""
    man = Manifest.read(city)
    controls = str(CONTROL["n_controls"])
    if key == "article8_2024":
        s8 = json.loads((ROOT / f"cities/{city}/layers/article8_2024_summary.json").read_text())
        t = s8["thresholds"]
        return t["ndvi"], T("threshold.article8",
                            "Greenness {ndvi}, canopy {trees}, built-up {built}: the 95th percentile of this run's own null "
                            "distribution — every one of the {n} comparable sectors plays “intervention” once "
                            "against its own {controls} matched places, and the effects it shows are pure noise.",
                            ndvi=Num(t["ndvi"], 4), trees=Num(t.get("trees", 0), 4), built=Num(t.get("built", 0), 4),
                            n=str(s8["units_comparable"]), controls=controls)
    if key.startswith("monitoring_"):
        season = int(key.split("_")[1])
        cal = ROOT / f"data/monitoring_{city}_{season}_calibration.json"
        c = json.loads(cal.read_text()) if cal.exists() else {}
        thr = man.layers[key].threshold
        # only the base years: the calibration file writes its window in Russian ("2023–2025 → сезон 2026")
        m = re.search(r"(\d{4})\s*[–-]\s*(\d{4})", c.get("window") or "")
        base = f"{m.group(1)}–{m.group(2)}" if m else f"{season - 3}–{season - 1}"
        return thr, T("threshold.monitoring",
                      "{thr}: the 95th percentile of the season's own null distribution (base {base} against summer {season}, "
                      "every sector playing “intervention” once). A loss is published only when the second instrument "
                      "(Dynamic World) agrees.",
                      thr=Num(thr, 4), base=base, season=str(season))
    if key.startswith("art8_balance_"):
        S = json.loads((ROOT / f"cities/{city}/layers/art8_balance_summary.json").read_text())
        b = S["seasons"][key.rsplit("_", 1)[1]]
        t = b["thresholds"]
        return t["green"], T("threshold.balance",
                             "Green {green}, canopy {trees}, built-up {built} (share of the sector's area): "
                             "the 95th percentile of this run's own null distribution, each class and season on its own — every "
                             "sector plays “intervention” once against its {controls} matched places.",
                             green=Num(t["green"], 4), trees=Num(t["trees"], 4), built=Num(t["built"], 4), controls=controls)
    if key == "groenkaart_2018_2024":
        c = json.loads((ROOT / f"cities/{city}/layers/groenkaart_check_summary.json").read_text())
        t, cp, gp = c["gk_thresholds"], c["pairs"]["canopy"], c["pairs"]["green"]
        kn = lambda x: (str(x["k"]), str(x["n"]))
        (cs_k, cs_n), (cc_k, cc_n) = kn(cp["specificity"]), kn(cp["agreement_when_ours_changed"])
        (gs_k, gs_n), (gc_k, gc_n) = kn(gp["specificity"]), kn(gp["agreement_when_ours_changed"])
        return t["hg_d"], T("threshold.groenkaart",
                            "High green {high}, all green {green} (share of the sector): the aerial map passed "
                            "through the same method, 2018 against the mean of 2021 and 2024, the same {controls} matched "
                            "places, its own null distribution. Against the detector: canopy — noise agreed in {cs_k} of "
                            "{cs_n}, “changed” in {cc_k} of {cc_n}; "
                            "greenness — {gs_k} of {gs_n} and {gc_k} of {gc_n}.",
                            high=Num(t["hg_d"], 4), green=Num(t["gr_d"], 4), controls=controls,
                            cs_k=cs_k, cs_n=cs_n, cc_k=cc_k, cc_n=cc_n, gs_k=gs_k, gs_n=gs_n, gc_k=gc_k, gc_n=gc_n)
    if key == "trees_register":
        return None, T("threshold.trees", "No significance threshold: an execution line, what was planted and kept, not a measured effect.")
    if key.startswith(("art8_baseline", "art8_sensitivity", "t8_UEAPolygons")):
        return None, T("threshold.level", "No significance threshold: a level for one year, not a change. The Commission’s own format carries "
                                          "no threshold either; whether anything changed beyond noise is the layer under “What changed”.")
    return None, None


# ── the layers, in the order of the atlas's questions ───────────────────────────────────────────────
LAYERS: list[dict] = [
    {"key": "sectors", "group": "Sectors", "build": _row_sectors, "licence": CCBY, "credit": ["statbel"],
     "title": "Statistical sectors",
     "measures": "The unit every layer is joined on: each statistical sector with its commune, residents, area and centroid.",
     "unit": "people, hectares, degrees (WGS 84)", "method": "Read from the city package: Statbel sectors with their 2024 population; the centroid is the polygon's.",
     "source": "Statbel statistical sectors and population", "limits": ["Sector boundaries are not included: download them from Statbel (statistical sectors, open data) and join on id."],
     "columns": {**SECTOR_COLS, "commune": "commune (municipality) the sector lies in", "population": "residents (Statbel)",
                 "area_ha": "area of the sector, hectares", "lon": "centroid longitude, WGS 84", "lat": "centroid latitude, WGS 84"}},

    {"key": "article8_2024", "group": "What changed", "build": _article8, "licence": CCBY, "credit": ["s2", "dw", "landsat", "statbel"],
     "title": "Green, canopy and built-up in 2024, and the trend against matched places",
     "measures": "Summer 2024 levels of greenness (NDVI) and of tree, grass and built-up cover, and the change from summers 2017–19 to 2021–24 against twelve matched sectors.",
     "unit": "NDVI units; Dynamic World class probability", "method": "Difference in differences: the sector's change minus the mean change of the 12 sectors most alike before (greenness and summer surface temperature), none closer than 1.5 km. A sector whose closest match differs by more than 0.04 NDVI before is refused, not compared.",
     "source": "Copernicus Sentinel-2 (summer medians, Cloud Score+ mask), Dynamic World V1, Landsat surface temperature for the matching; income: Statbel 2023",
     "limits": ["Class values are probabilities, not shares of ground: compare them between sectors, do not read them as percentages of area.",
                "Greenness is not tree canopy: a young planting on a meadow reads as a loss, and restoring an existing park does not show."],
     "columns": {**SECTOR_COLS, "commune": "commune", "area_ha": "area, hectares", "population": "residents",
                 "density": "residents per hectare", "income": "median taxable income, €, Statbel 2023",
                 "ndvi_2024": "summer 2024 greenness (NDVI), sector mean", "trees_2024": "summer 2024 tree cover, Dynamic World class probability",
                 "grass_2024": "summer 2024 grass cover, class probability", "built_2024": "summer 2024 built-up cover, class probability",
                 "ndvi_eff": "effect on greenness: the sector's change minus its 12 matched places' mean change",
                 "ndvi_verdict": "up (greener beyond noise), down (lost beyond noise), noise, or refused (no comparable places)",
                 "trees_eff": "effect on tree cover, same matched places", "trees_verdict": "the same verdict for tree cover",
                 "grass_eff": "effect on grass cover", "built_eff": "effect on built-up (sealed) cover, same matched places",
                 "built_verdict": "up (more built-up beyond noise: sealed), down (less beyond noise: unsealed), noise, or refused",
                 "gap": "greenness before: the sector minus its matched places (above 0.04 in absolute value: refused)",
                 "comparable": "True when the matched places are comparable", "ndvi_b": "greenness before, summers 2017–19",
                 "ndvi_a": "greenness after, summers 2021–24", "ndvi_raw": "change without subtracting matched places (after − before)",
                 "lst_b": "summer land surface temperature before, °C (Landsat), used for matching"}},

    *[{"key": f"monitoring_{s}", "group": "What changed", "build": (lambda c, s=s: _monitoring(c, s)), "licence": CCBY, "credit": ["s2", "dw"],
       "title": f"Monitoring, summer {s}",
       "measures": f"Greenness in summer {s} against a rolling base of the three summers before, sector by sector, with the second instrument's reading of every loss.",
       "unit": "NDVI units; class probability", "method": "Difference in differences against the same kind of matched places, with the season's own threshold. A loss beyond the threshold is read by Dynamic World (tree cover down: canopy loss; built-up up: construction; neither: not confirmed), then by documents.",
       "source": "Copernicus Sentinel-2, Dynamic World V1 (trees, built) for corroboration",
       "limits": ["One season is noisier than a four-year window: a loss is named only when two instruments agree.",
                  "The cause is not in the numbers: it comes from documents, and without one it stays unknown."],
       "columns": {**SECTOR_COLS, "area_ha": "area, hectares", "population": "residents",
                   "ndvi_before": "greenness, mean of the base summers", "ndvi_delta": f"summer {s} minus the base",
                   "effect": "the change minus the matched places' mean change", "gap": "greenness before, the sector minus its matched places",
                   "comparable": "True when the matched places are comparable",
                   "dw_label": "the second instrument's reading of a loss beyond the threshold: construction, canopy loss or not confirmed",
                   "dw_trees": "tree cover change, class probability (seasons from 2025)", "dw_built": "built-up change, class probability (seasons from 2025)",
                   "bulletin": "the season bulletin's reading after documents: construction, canopy loss, not confirmed or gained"}}
      for s in (2024, 2025, 2026)],

    {"key": "art8_official_lau_2021", "group": "The law", "build": _lau, "licence": CCBY, "credit": ["clms", "gisco"],
     "title": "Article 8(1) by commune, with the Commission’s method",
     "measures": "The share of urban green and tree canopy in each commune (LAU) and in its urban centres and clusters, and whether the commune passes the exemption of Article 8(1): more than 45% green and more than 10% canopy.",
     "unit": "share of area, 0–1", "method": "The EEA and JRC script NRR_Art8 repeated on open data: LAU 2024 × the 1 km² grid of urban centres and clusters 2021; the share of a class's pixels inside the polygon, by pixel centre.",
     "source": "Copernicus CLCplus Backbone 2021 (10 m), HRL Woody Vegetation Layer 2021 (5 m), HRL Tree Cover Density 2018 (10 m); Eurostat LAU 2024, degree of urbanisation 2024, clusters 2021",
     "limits": ["Green from CLCplus 2021, where the Regulation names 2023; canopy from WVL 2021, allowed for draft plans only.",
                "Matching CLCplus classes to Article 3(20) is our reading; the verdict was re-checked with arable land as green and without water."],
     "columns": {"lau_id": "LAU code (BE_ + NIS code)", "name": "commune", "degurba": "degree of urbanisation (1 = city)",
                 "population": "residents (LAU 2024)", "area_km2_official": "official area, km²", "area_km2_all": "measured area, km²",
                 "green_all": "green share, whole LAU", "green_with7_all": "green share counting arable land", "green_no_water_all": "green share without water",
                 "sealed_all": "sealed share, whole LAU", "canopy_wvl_all": "woody vegetation share, whole LAU", "tcd_all": "mean tree cover density, whole LAU",
                 "tcd_any_all": "share of pixels with any tree cover", "area_km2_ucuc": "area inside urban centres and clusters, km²",
                 "green_ucuc": "green share inside urban centres and clusters (the test's green)", "green_with7_ucuc": "the same, counting arable land",
                 "green_no_water_ucuc": "the same, without water", "sealed_ucuc": "sealed share inside centres and clusters",
                 "canopy_wvl_ucuc": "woody vegetation share inside centres and clusters (the test's canopy)", "tcd_ucuc": "mean tree cover density inside",
                 "tcd_any_ucuc": "share of pixels with any tree cover inside", "exempt": "True when the commune passes the exemption",
                 "reason": "why it does not pass, in numbers", "exempt_with7": "the verdict counting arable land", "exempt_no_water": "the verdict without water",
                 "green_ucuc_statbel": "green share with the commune built from Statbel sectors", "canopy_wvl_ucuc_statbel": "canopy share, the same way",
                 "exempt_statbel": "the verdict, the same way", "stable": "True when the verdict holds under every reading above"}},

    {"key": "art8_baseline_2021", "group": "The law", "build": _passthrough("art8_baseline_2021"), "licence": CCBY, "credit": ["clms", "gisco"],
     "title": "The zero measurement by commune, in hectares",
     "measures": "For each commune, the area of its urban ecosystem and the green and tree canopy inside it, in hectares and per cent, for both boundaries the Commission leaves to the country: the urban centres and clusters inside the commune, and the whole commune. The form of the Dutch national zero measurement (PBL, 25 August 2026).",
     "unit": "hectares; per cent", "method": "The shares of the layer above multiplied by the area they were measured on: nothing is recomputed. A city of several communes adds a row for all of them together.",
     "source": "Frondia’s repeat of the EEA and JRC script NRR_Art8 (the layer above); Copernicus CLCplus Backbone 2021, HRL Woody Vegetation Layer 2021; Eurostat LAU 2024, urban centres and clusters 2021",
     "limits": ["2021 data: the Commission allows the Woody Vegetation Layer 2021 for draft plans only.",
                "Hectares are the pixels' area inside the 1:1M boundary, not the land register.",
                "Matching CLCplus classes to Article 3(20) is our reading: see the sensitivity table."],
     "columns": {"lau_id": "LAU code as the Commission writes it (lau2024.BE.<NIS code>); empty on the row for all communes together",
                 "name": "commune", "population": "residents (LAU 2024)",
                 "uea_ucuc_ha": "urban ecosystem as urban centres and clusters inside the commune, hectares",
                 "green_ucuc_ha": "green inside it, hectares", "green_ucuc_pct": "green inside it, per cent (the exemption's green)",
                 "canopy_ucuc_ha": "tree canopy inside it, hectares", "canopy_ucuc_pct": "tree canopy inside it, per cent (the exemption's canopy)",
                 "uea_lau_ha": "urban ecosystem as the whole commune, hectares", "green_lau_ha": "green in the whole commune, hectares",
                 "green_lau_pct": "green in the whole commune, per cent", "canopy_lau_ha": "tree canopy in the whole commune, hectares",
                 "canopy_lau_pct": "tree canopy in the whole commune, per cent",
                 "exempt": "True when more than 45% green and more than 10% canopy in urban centres and clusters",
                 "stable": "True when the verdict holds under every reading of the sensitivity table"}},

    {"key": "art8_sensitivity_2021", "group": "The law", "build": _passthrough("art8_sensitivity_2021"), "licence": CCBY, "credit": ["clms", "gisco"],
     "title": "How the exemption verdict depends on the reading",
     "measures": "The Article 8(1) verdict of each commune under every reading the test runs: the official one, arable land counted as green, water not counted as green, and the commune built from Statbel sectors instead of the 1:1M boundary.",
     "unit": "per cent; True or False", "method": "The thresholds of Article 8(1), more than 45% green and more than 10% canopy, applied to the shares of each reading.",
     "source": "Frondia’s repeat of NRR_Art8 (the layer “Article 8(1) by commune”)",
     "limits": ["Only the readings the test runs: other boundaries a country may choose were not tried."],
     "columns": {"lau_id": "LAU code (lau2024.BE.<NIS code>)", "name": "commune",
                 "reading": "official, with_arable, without_water or statbel_sectors",
                 "green_pct": "green in urban centres and clusters under this reading, per cent",
                 "canopy_pct": "tree canopy there, per cent", "exempt": "the verdict under this reading (empty where the reading was not computed)"}},

    *[{"key": f"t8_UEAPolygons_{v}", "group": "The law", "copy": f"t8_UEAPolygons_{v}.gpkg", "format": "GeoPackage",
       "licence": CCBY, "credit": ["clms", "gisco"],
       "title": f"The Reportnet file, {short}",
       "measures": f"t8_UEAPolygons: one polygon per commune with the area of tree canopy (area_tcc) and of urban green (area_ugs) in km², the urban ecosystem taken as {label}. The schema of the Commission’s own example, field by field.",
       "unit": "km²", "method": "The commune’s LAU 2024 polygon (Eurostat GISCO, EPSG:3035) with the areas of the layers above; area_tcc as text with five decimals, as the Commission’s script rounds it.",
       "source": "Schema: EEA and JRC, github.com/eea/NRR_Art8 (commit of 22 September 2026). Numbers: Frondia’s repeat of that script on open data.",
       "limits": ["A draft on 2021 data: the Woody Vegetation Layer 2021 is allowed for draft plans only.",
                  "area_ugs is empty in the Commission’s example; here it is our reading of Article 3(20) in CLCplus classes.",
                  "uea_id is empty, as in the example: the country assigns it.",
                  "No R-tree spatial index (optional in GeoPackage); GIS software builds one on opening if it needs it."],
       "columns": {"fid": "feature id, inherited from GISCO’s LAU layer as in the example", "geom": "the commune’s polygon, MULTIPOLYGON, EPSG:3035",
                   "uea_id": "urban ecosystem id, empty", "lau_id": "LAU code (lau2024.BE.<NIS code>)",
                   "area_tcc": "tree canopy (Woody Vegetation Layer) in the urban ecosystem, km², text",
                   "area_ugs": "urban green (CLCplus, our reading of Article 3(20)) in the urban ecosystem, km²"}}
      for v, label, short in (("ucuc", "the urban centres and clusters inside the commune", "centres and clusters"),
                              ("lau", "the whole commune", "whole commune"))],

    *[{"key": f"art8_balance_{s}", "group": "The law", "build": (lambda c, s=s: _balance(c, s)), "licence": CCBY,
       "credit": ["dw", "s2", "landsat", "statbel"],
       "title": f"Since the 2024 base, in hectares: summer {s}",
       "measures": f"For each sector, urban green (the Regulation’s reading: trees, grass, shrub and water, not farmland), tree canopy and built-up ground in hectares in summer 2024 and summer {s}, and the change beyond noise against twelve matched places.",
       "unit": "hectares; share of the sector’s area", "method": "Each summer, the class with the highest mean Dynamic World probability wins each 10 m pixel; a class’s share of the sector times its area gives hectares. The effect is the sector’s change in share minus its matched places’ mean change (the most alike in 2024 by greenness and surface temperature, none closer than 1.5 km); times the area, hectares beyond what comparable places did.",
       "source": "Dynamic World V1; Copernicus Sentinel-2 greenness and Landsat surface temperature of summer 2024 for the matching; Statbel sectors and population",
       "limits": ["Hectares as Dynamic World classifies the ground: not the official CLCplus and Woody Vegetation layers, and not the land register.",
                 "One summer against another is noisier than a four-year window.",
                 "The raw hectares include the classes’ shift from one summer to the next; only the effect subtracts it.",
                 "A park that loses trees can read as more built-up when a mixed pixel changes class."],
       "columns": {**SECTOR_COLS, "commune": "commune", "area_ha": "area, hectares", "population": "residents",
                   **{f"{k}_{y}_ha": f"{w}, summer {y}, hectares" for k, w in (("green", "urban green"), ("trees", "tree canopy"), ("built", "built-up"))
                      for y in (2024, s)},
                   **{f"{k}_raw_ha": f"{w}: summer {s} minus summer 2024, hectares, without matched places" for k, w in (("green", "urban green"), ("trees", "tree canopy"), ("built", "built-up"))},
                   **{f"{k}_eff": f"{w}: the change in share minus the matched places’ mean change" for k, w in (("green", "urban green"), ("trees", "tree canopy"), ("built", "built-up"))},
                   **{f"{k}_eff_ha": f"{w}: that effect in hectares" for k, w in (("green", "urban green"), ("trees", "tree canopy"), ("built", "built-up"))},
                   **{f"{k}_verdict": f"{w}: up, down, noise or refused" for k, w in (("green", "urban green"), ("trees", "tree canopy"), ("built", "built-up"))},
                   "gap": "greenness in 2024, the sector minus its matched places (above 0.04 in absolute value: refused)",
                   "comparable": "True when the matched places are comparable"}}
      for s in (2025, 2026)],

    {"key": "fit_score", "group": "What’s missing", "build": _passthrough("fit_score"), "licence": ODBL, "credit": ["osm", "gtfs", "statbel"],
     "title": "Everyday services within walking distance",
     "measures": "How well a sector serves three ways of living — a family with children, remote work, seniors — by walking access to fourteen everyday services.",
     "unit": "score 0–100 and percentile; per-service scores 0–1", "method": "Walking time from the sector's centroid on the OpenStreetMap walking graph; each service scored with a plateau-and-decay curve; public transport weighted by departures in the morning peak; a weighted sum per scenario; the percentile is Hazen's, over the city's sectors.",
     "source": "Neighbourhood Fit Score pipeline: OpenStreetMap points of interest and walking graph, Statbel sectors, {transit} timetables",
     "limits": ["A state, not a measured change: never mix it with the effects above.",
                "OpenStreetMap is not equally complete everywhere: a score reflects the map as well as the city.",
                "The scenario weights are an editorial choice, not a measurement."],
     "columns": {"id": SECTOR_COLS["id"], "scenario": "family, remote or senior", "score": "the scenario's score, 0–100",
                 "percentile": "rank among the city's sectors, 0–100",
                 **{k: f"{k.replace('gp', 'GP').replace('_', ' ')} sub-score, 0–1" for k in
                    ("cafe", "childcare", "convenience", "gp", "hospital", "library", "park", "pharmacy", "playground", "restaurant", "school", "sport", "supermarket")},
                 "transit": "public transport sub-score, 0–1, weighted by departures"}},

    {"key": "shops_access", "group": "What’s missing", "build": _passthrough("shops_access"), "licence": ODBL, "credit": ["osm", "statbel"],
     "title": "Bakeries, cafés and confectioners within reach",
     "measures": "The distance from a sector to the nearest bakery, café and confectioner, and how many of each lie inside it.",
     "unit": "metres; count", "method": "From the sector's representative point to the nearest venue of each kind, anywhere in the city, in a straight line (SpotFinder).",
     "source": "SpotFinder pipeline: OpenStreetMap venues, Statbel sectors",
     "limits": ["A state, not a measured change.", "Straight-line distance, not along streets.", "OpenStreetMap is not equally complete everywhere."],
     "columns": {"id": SECTOR_COLS["id"], "bakery_m": "metres to the nearest bakery", "cafe_m": "metres to the nearest café",
                 "confectionery_m": "metres to the nearest confectioner", "bakery_in_sector": "bakeries inside the sector",
                 "cafe_in_sector": "cafés inside the sector", "confectionery_in_sector": "confectioners inside the sector"}},

    {"key": "heat_2022_2025", "group": "What’s missing", "build": _passthrough("heat_2022_2025"), "licence": CCBY, "credit": ["landsat", "statbel"],
     "title": "Summer heat",
     "measures": "The summer land surface temperature of each sector and how far it lies above or below the city's median sector.",
     "unit": "°C", "method": "The median of summer scenes 2022–2025, Landsat 8/9 thermal band, cloud-masked with QA_PIXEL.",
     "source": "Landsat Collection 2 Level 2 (ST_B10), Statbel sectors and population",
     "limits": ["Surface temperature, not air temperature.",
                "Good for ranking sectors against each other; not for “it got cooler”: the threshold for a change in temperature came out at 1.32 °C, more than a realistic park effect, so cooling is not measured."],
     "columns": {**SECTOR_COLS, "population": "residents", "area_ha": "area, hectares",
                 "lst_summer_c": "median summer surface temperature 2022–2025, °C", "excess_over_city_c": "that minus the city's median sector, °C"}},

    {"key": "rule_3_30_300", "group": "What’s missing", "build": _passthrough("rule_3_30_300"), "licence": ODBL, "credit": ["worldcover", "osm", "statbel"],
     "title": "The 3-30-300 rule",
     "measures": "The two measurable parts of the rule: 30% tree canopy in the sector, and a park of at least one hectare within 300 m.",
     "unit": "share of area; pass flags", "method": "Canopy: the share of ESA WorldCover's tree class (10 m), pass at 30%. Parks: named OpenStreetMap polygons of 1 ha or more; a sector passes when half of its area lies within 300 m of one.",
     "source": "ESA WorldCover v200 (2021), OpenStreetMap parks, Statbel sectors and population",
     "limits": ["The first part, three trees in view from every window, is not measured.", "Private and closed gardens are not told apart from parks."],
     "columns": {**SECTOR_COLS, "population": "residents", "canopy_share": "tree canopy share of the sector (WorldCover)",
                 "near_park_share": "share of the sector within 300 m of a park of 1 ha or more", "passes_30": "1 when canopy ≥ 30%",
                 "passes_300": "1 when at least half the sector is within 300 m of a park", "passes_both": "1 when both parts pass"}},

    {"key": "population_age", "group": "What’s missing", "build": _passthrough("population_age"), "licence": CCBY, "credit": ["statbel"],
     "title": "Residents by age",
     "measures": "Children under 15, adults, people aged 65 and over, and 80 and over separately.",
     "unit": "people; share", "method": "The 2021 census by sector, sex and age, summed into four bands; 80+ is part of 65+.",
     "source": "Statbel, Census 2021, table TF_CENSUS_2021_S01",
     "limits": ["The census date, not 2024.", "Small sectors may be rounded by Statbel for privacy."],
     "columns": {**SECTOR_COLS, "population_census": "residents at the 2021 census", "children_0_14": "children under 15",
                 "adults_15_64": "aged 15 to 64", "seniors_65_plus": "aged 65 and over", "seniors_80_plus": "aged 80 and over (included in 65+)",
                 "share_children": "children under 15, share of residents", "share_seniors": "aged 65 and over, share of residents"}},

    {"key": "planner_points", "group": "What to place", "build": _points, "licence": ODBL, "credit": ["osm", "statbel", "bimd"],
     "title": "Where City Planner would place the next objects",
     "measures": "For fourteen kinds of public object, the forty best places ranked by City Planner; the first ten of each kind were named on 5 September 2026, the next ten are their comparison.",
     "unit": "rank; coordinates; planner's scores", "method": "A greedy maximum-coverage solver over a demand grid weighted by deprivation, with a 500 m service radius: each next place is the one that covers the most unmet demand.",
     "source": "City Planner pipeline: OpenStreetMap objects and points of demand, Statbel sectors, deprivation by sector",
     "limits": ["A recommendation, not a measurement.", "Ranks 11–20 are slightly worse than 1–10 by construction: as a comparison group they are conservative."],
     "columns": {"kind": "kind of object", "rank": "planner's rank, 1–40", "role": "named (1–10), comparison (11–20) or further (21–40)",
                 "lon": "longitude, WGS 84", "lat": "latitude, WGS 84", "sector": "Statbel sector the place falls in (empty outside the package)",
                 "score": "planner's composite score", "gap_score": "unmet demand the place covers, 0–1", "equity_index": "deprivation weight, 0–1",
                 "named_at": "the date the points were fixed",
                 "official_at_point": "objects of the same kind in the city's own register within the point's 50 m check radius (empty: no register of this kind)",
                 "official_within_500m": "the same within 500 m, the planner's service radius",
                 "map_gap_500m": "of those within 500 m, how many the planner's OpenStreetMap did not have within 50 m: a gap of the map, not of the street (empty where that OSM was not kept)",
                 "out_of_check": "True when an object already stood within the check radius by the register, so the point leaves the named-against-comparison check"}},

    {"key": "planner_coverage", "group": "What to place", "build": _coverage, "licence": ODBL, "credit": ["osm", "statbel", "bimd"],
     "title": "Coverage after each of the next forty objects",
     "measures": "The share of demand within 500 m of an object, today (n = 0) and after each rank is placed: the curve under “What if N more?”.",
     "unit": "share of demand, 0–1", "method": "From the same City Planner run as the ranked places.",
     "source": "City Planner pipeline", "limits": ["Coverage of demand points, not of residents."],
     "columns": {"kind": "kind of object", "n": "objects added, 0–40", "coverage": "share of demand covered", "service_radius_m": "service radius, metres"}},

    {"key": "groenkaart_2018_2024", "group": "Cross-checks", "build": _if_exists("groenkaart_2018_2024"), "licence": CCBY, "credit": ["groenkaart", "statbel"],
     "title": "Groenkaart Vlaanderen by sector, the detector’s outside check",
     "measures": "The share of each sector under high green (over 3 m), low green, farmland and no green in the Flemish aerial green map of 2018, 2021 and 2024. Passed through the same method as the satellite, it tells how often the detector’s verdicts are confirmed.",
     "unit": "share of the classified area, 0–1", "method": "The 1 m map sampled at 4 m (nearest neighbour) from the ANB web coverage service; a pixel counts when its centre falls in the Statbel sector (Lambert 72).",
     "source": "Groenkaart Vlaanderen (ANB, Digitaal Vlaanderen): segmentation of summer aerial photographs, high green by height",
     "limits": ["Flanders only: Antwerp and Ghent. Brussels and Wallonia have no two comparable editions.",
                "Summer 2018 was a drought: low green in that edition reads low.",
                "Two instruments agreeing or not, not an error against the truth: the aerial map has errors of its own."],
     "columns": {"id": SECTOR_COLS["id"], "px": "sampled 4 m pixels in the sector",
                 **{f"{k}_{y}": f"{w}, {y}" for y in (2018, 2021, 2024) for k, w in (("valid", "classified share of the sector's pixels"),
                   ("high", "high green (over 3 m), share of the classified area"), ("low", "low green (under 3 m), share"),
                   ("agri", "farmland, share"), ("none", "no green, share"))}}},

    {"key": "trees_register", "group": "What to place", "build": _if_exists("trees_register"), "licence": CCBY, "credit": ["trees_ghent"],
     "title": "Trees in the city’s register, by sector",
     "measures": "How many of the trees the city manages stand in each sector, and in Ghent how many were planted in each year from 2020 to 2025. A snapshot of the register is kept, so trees that leave it can be counted from the next one.",
     "unit": "trees", "method": "Each tree's point placed in its Statbel sector; the register's own planting year (Ghent).",
     "source": "The city's open tree register", "limits": ["Only trees the city manages: gardens and private land are not in it.",
                "A tree leaving the register may have been felled, have died or been re-surveyed: the register does not say which.",
                "A planting year exists in Ghent's register only, and not for every tree."],
     "columns": {"id": SECTOR_COLS["id"], "trees": "trees in the register", **{f"planted_{y}": f"planted in {y}" for y in range(2020, 2026)},
                 "gone": "trees that left the register since the previous snapshot", "came": "trees that entered it"}},

    {"key": "worldcover_2021", "group": "Cross-checks", "build": _passthrough("worldcover_2021"), "licence": CCBY, "credit": ["worldcover", "statbel"],
     "title": "ESA WorldCover shares, a check on our tree class",
     "measures": "The share of each sector under trees, shrub, grass, built-up and bare ground, by a hard 10 m classification.",
     "unit": "share of area, 0–1", "method": "The mean of each class's mask inside the sector.",
     "source": "ESA WorldCover v200, epoch 2021",
     "limits": ["One epoch, 2021: not a baseline and not a change.", "Hard classes against Dynamic World's probabilities: compare the rank, not the value."],
     "columns": {**SECTOR_COLS, "area_ha": "area, hectares", "population": "residents", "wc_trees": "tree share", "wc_shrub": "shrub share",
                 "wc_grass": "grass share", "wc_built": "built-up share", "wc_bare": "bare ground share"}},

    {"key": "canopy_probav_2019", "group": "Cross-checks", "build": _passthrough("canopy_probav_2019"), "licence": CCBY, "credit": ["cgls"],
     "title": "Proba-V tree cover, a third instrument",
     "measures": "The tree cover fraction of each sector from a different producer and sensor.",
     "unit": "share of area, 0–1", "method": "The tree-coverfraction band, mean over the sector, 100 m grid.",
     "source": "Copernicus Global Land Service, Land Cover 100 m (Proba-V, VITO), epoch 2019",
     "limits": ["Epoch 2019, and the series has ended.", "On a 100 m grid small crowns in dense streets read as zero."],
     "columns": {**SECTOR_COLS, "canopy_share": "tree cover fraction"}},
]


def _csv_bytes(rows: list[dict]) -> tuple[int, bytes, list[str]]:
    cols = list(rows[0].keys()) if rows else []
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return len(rows), buf.getvalue().encode("utf-8"), cols


def _gpkg(src: Path) -> tuple[int, bytes, list[str]]:
    """A GeoPackage goes out as the package holds it, byte for byte; rows and columns read from it."""
    import sqlite3
    data = src.read_bytes()
    con = sqlite3.connect(src)
    tbl = con.execute("select table_name from gpkg_contents where data_type='features'").fetchone()[0]
    n = con.execute(f'select count(*) from "{tbl}"').fetchone()[0]
    cols = [r[1] for r in con.execute(f'pragma table_info("{tbl}")')]
    con.close()
    return n, data, cols


# the operator whose timetables each city's Fit Score reads
TRANSIT = {"brussels": "STIB-MIVB", "antwerp": "De Lijn", "ghent": "De Lijn", "liege": "TEC", "charleroi": "TEC"}


def _osm(source_ru: str) -> Text | None:
    """Where a layer's OpenStreetMap came from, read off the package manifest's Russian source line, which
    the importer writes from what the pipeline recorded (a Geofabrik extract with its data timestamp, or
    live Overpass)."""
    stamps = sorted(set(re.findall(r"выгрузки Geofabrik \S+, данные на ([0-9TZ:-]+)", source_ru)))
    if stamps:
        return T("osm.geofabrik", "OpenStreetMap from a Geofabrik extract of Belgium, data as of {stamps}.", stamps=", ".join(stamps))
    m = re.search(r"живого Overpass(?: \([^)]*\))?, (?:запрос|не позже) ([0-9-]+)", source_ru)
    if m:
        return T("osm.overpass", "OpenStreetMap from live Overpass queries, on or before {date}.", date=m.group(1))
    if "OSM" in source_ru and "не записан" in source_ru:
        return T("osm.unrecorded", "Which OpenStreetMap snapshot was read was not recorded at the time.")
    return None


def _column(key: str, col: str, description: str) -> Text:
    """A column shared by the sector layers (SECTOR_COLS, same words everywhere) is one unit; any other is the layer's."""
    return T(f"column.{col}" if SECTOR_COLS.get(col) == description else f"layer.{key}.column.{col}", description)


def manifest_bytes(manifest: dict) -> bytes:
    """The city's manifest.json as written: English, indented."""
    return json.dumps(render(manifest, "en"), ensure_ascii=False, indent=1).encode("utf-8")


def build_city(city: str) -> tuple[dict, dict[Path, bytes]]:
    """The city's manifest with its words as texts.Text (rendered per language by texts.render), and the files to write —
    the layers' CSVs and GeoPackages and the English manifest.json — as bytes. Writes nothing."""
    out = SITE / "downloads" / city
    files: dict[Path, bytes] = {}
    layers = []
    for spec in LAYERS:
        key = spec["key"]
        if spec.get("copy"):
            src = ROOT / f"cities/{city}/layers/{spec['copy']}"
            if not src.exists():
                continue
            n, data, cols = _gpkg(src)
            files[out / spec["copy"]] = data
        else:
            rows = spec["build"](city)
            if not rows:
                continue
            n, data, cols = _csv_bytes(rows)
            files[out / f"{key}.csv"] = data
        missing = [c for c in cols if c not in spec["columns"]]
        if missing:
            raise SystemExit(f"{city}/{key}: columns without a description: {missing}")
        thr, thr_from = _thr(city, key)
        # when the layer was computed, from the package manifest (the planner's places carry their own date)
        man = Manifest.read(city).layers
        ref = (man.get(key) or (man.get("points_toilets") if key.startswith("planner") else None)
               or (man.get("t8_UEAPolygons") if key.startswith("t8_UEAPolygons") else None))
        L = f"layer.{key}"
        # the operator goes in as a value ({transit}), so one translation serves every city
        source = T(f"{L}.source", spec["source"].removesuffix(".") + ".",
                   **({"transit": TRANSIT[city]} if "{transit}" in spec["source"] else {}))
        layers.append({
            "key": key, "group": spec["group"], "title": T(f"{L}.title", spec["title"]), "file": spec.get("copy") or f"{key}.csv",
            "format": spec.get("format", "CSV"),
            "rows": n, "bytes": len(data), "computed": getattr(ref, "computed", None) if ref else None,
            "measures": T(f"{L}.measures", spec["measures"]), "unit": T(f"{L}.unit", spec["unit"]),
            "method": T(f"{L}.method", spec["method"]),
            "source": Join((source, _osm(getattr(ref, "source", "") or "")), sep=" ", fix=("..", ".")),
            "threshold": thr,
            "threshold_from": thr_from or T("threshold.none", "No significance threshold: this layer is a state or a recommendation, not a measured change."),
            "limits": [T(f"{L}.limits.{i}", x) for i, x in enumerate(spec["limits"])], "licence": spec["licence"],
            "credit": [(CREDIT[f"trees_{city}"] if c == "trees_ghent" else CREDIT[c]).replace("{transit}", TRANSIT[city])
                       for c in spec["credit"]],
            "columns": [{"name": c, "description": _column(key, c, spec["columns"][c])} for c in cols],
        })
    manifest = {"city": city, "name": Place(city), "join_key": "id (Statbel statistical sector); lau_id for the Article 8 files",
                "encoding": "CSV: UTF-8, comma-separated, a header row. GeoPackage: OGC GeoPackage 1.2, EPSG:3035",
                "layers": layers}
    files[out / "manifest.json"] = manifest_bytes(manifest)
    return manifest, files


def build_index() -> tuple[dict, dict[Path, bytes]]:
    """The index the /data page reads (texts.Text inside) and every file of every city. Writes nothing: the size of a
    manifest is measured on its bytes in memory."""
    index: dict = {}
    files: dict[Path, bytes] = {}
    for city in CITY_NAME:
        m, f = build_city(city)
        files |= f
        index[city] = {"name": m["name"], "manifest_bytes": len(f[SITE / "downloads" / city / "manifest.json"]), "layers": m["layers"]}
    return index, files


def _index_json(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":"))


def write_all() -> dict:
    """Writes the files, downloads.json (English) and downloads.<loc>.json for every language with data texts; a
    language without them has no file (the site reads the English one while that language is in preview)."""
    doc, files = build_index()
    en = render(doc, "en")
    # every language rendered before anything is written: a missing translation stops the run with the files as they were
    langs = {loc: render(doc, loc, Catalog.load(loc)) for loc in available()}
    for p, data in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    (SITE / "data").mkdir(parents=True, exist_ok=True)
    (SITE / "data" / "downloads.json").write_text(_index_json(en), encoding="utf-8")
    for loc in LOCS:
        p = SITE / "data" / f"downloads.{loc}.json"
        if loc in langs:
            p.write_text(_index_json(langs[loc]), encoding="utf-8")
        else:
            p.unlink(missing_ok=True)
    return en


if __name__ == "__main__":
    idx = write_all()
    for c, v in idx.items():
        print(f"  downloads/{c}: {len(v['layers'])} layers, {sum(l['bytes'] for l in v['layers']) // 1024} KB")
