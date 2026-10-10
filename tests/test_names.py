"""Place names in the page's language (plan 5, L4): the official Dutch and French names of Statbel's sector register
2024 joined on the sector code, written next to the English site's own name only where they differ."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "public" / "data"
CITIES = ["brussels", "antwerp", "ghent", "liege", "charleroi"]
NAMES = {r["id"]: r for r in csv.DictReader((ROOT / "data/statbel_names_2024.csv").open(encoding="utf-8"))}


def city(c):
    return json.loads((DATA / f"{c}.json").read_text())


@pytest.mark.parametrize("c", CITIES)
def test_every_sector_is_in_statbels_register_with_its_commune(c):
    for s in city(c)["sectors"]:
        assert s["id"] in NAMES, s["id"]
        assert NAMES[s["id"]]["refnis"] == s["id"][:5]


@pytest.mark.parametrize("c", CITIES)
def test_the_english_name_is_unchanged_and_a_variant_only_where_it_differs(c):
    for s in city(c)["sectors"]:
        r = NAMES[s["id"]]
        if r["sector_nl"] or r["sector_fr"]:
            assert " ".join(s["n"].split()) in (r["sector_nl"], r["sector_fr"]), s["id"]   # the register drops double spaces
        for k in ("n_nl", "n_fr", "c_nl", "c_fr"):
            if k in s:
                assert s[k] and s[k] != s[k[0]], (s["id"], k)


def test_brussels_known_answers():
    b = {s["id"]: s for s in city("brussels")["sectors"]}
    assert (b["21001A00-"]["n"], b["21001A00-"]["n_nl"], "n_fr" in b["21001A00-"]) == ("RESISTANCE", "VERZET", False)
    assert b["21004E72-"]["n_nl"] == "ROODHUISPLEIN-ZUID" and b["21004E72-"]["c_nl"] == "Brussel"
    assert "c_fr" not in b["21004E72-"]                       # "Bruxelles" is the English site's own name
    communes = {x["code"]: x for x in city("brussels")["communes"]["list"]}
    assert (communes["21002"]["name"], communes["21002"]["name_nl"]) == ("Auderghem", "Oudergem")


def test_flemish_and_walloon_known_answers():
    a = {s["id"]: s for s in city("antwerp")["sectors"]}
    assert a["11002A00-"]["c_fr"] == "Anvers" and "c_nl" not in a["11002A00-"]
    assert not any(k in a["11001A01-"] for k in ("n_nl", "n_fr", "c_nl", "c_fr"))
    g = city("ghent")["communes"]["list"][0]
    assert (g["name"], g["name_nl"], g["name_fr"]) == ("Ghent", "Gent", "Gand")
    l = {s["id"]: s for s in city("liege")["sectors"]}
    assert (l["62063A00-"]["c"], l["62063A00-"]["c_nl"], l["62063A00-"]["c_fr"]) == ("Liège (north)", "Luik (noord)", "Liège (nord)")


def test_commune_pages_and_audits_carry_the_names_and_the_region():
    pages = {p["code"]: p for p in json.loads((DATA / "communes.json").read_text())}
    assert pages["21002"]["name_nl"] == "Oudergem" and pages["44021"]["name_fr"] == "Gand"
    assert {p["region_key"] for p in pages.values()} == {"brussels", "flanders", "wallonia"}
    for case in json.loads((DATA / "cases.json").read_text()):
        for x in case["controls"]:
            r = NAMES[x["id"]]
            if r["sector_nl"] and r["sector_nl"] != x["name"]:
                assert x["name_nl"] == r["sector_nl"], (case["slug"], x["id"])


# Both ways: every variant the data carries is the register's, and every name the register gives that differs from the
# English one is there. Recomputed here from the CSV alone, not by site_data's own functions.
def ws(a):
    return " ".join((a or "").split())


def expect(key, en, nl, fr):
    return {f"{key}_{lang}": v for lang, v in (("nl", nl), ("fr", fr)) if v and ws(v) != ws(en)}


def pick(d, key):
    return {k: d[k] for k in (f"{key}_nl", f"{key}_fr") if k in d}


MUNTY = {r["refnis"]: (r["munty_nl"], r["munty_fr"]) for r in NAMES.values()}
# the English site's own district labels (site_data.DISTRICT_I18N), written out here as the second copy
DISTRICTS = {"Liège (north)": ("Luik (noord)", "Liège (nord)"), "Liège (south)": ("Luik (zuid)", "Liège (sud)"),
             "Haven": ("Haven", "Port")}


def sector_expect(s):
    r = NAMES[s["id"]]
    return expect("n", s["n"], r["sector_nl"], r["sector_fr"])


@pytest.mark.parametrize("c", CITIES)
def test_every_sector_carries_exactly_the_registers_names_that_differ(c):
    for s in city(c)["sectors"]:
        r = NAMES[s["id"]]
        assert pick(s, "n") == sector_expect(s), s["id"]
        if s["c"] in DISTRICTS:
            want = expect("c", s["c"], *DISTRICTS[s["c"]])
        elif c == "brussels" or s["c"] in (r["munty_nl"], r["munty_fr"]):
            want = expect("c", s["c"], r["munty_nl"], r["munty_fr"])
        else:
            want = {}
        assert pick(s, "c") == want, s["id"]


@pytest.mark.parametrize("c", CITIES)
def test_every_commune_of_the_atlas_carries_the_registers_names_that_differ(c):
    for x in city(c)["communes"]["list"]:
        assert pick(x, "name") == expect("name", x["name"], *MUNTY[x["code"]]), x["code"]


def test_commune_pages_events_tops_and_dossier_match_the_register_by_id():
    region = {"brussels": "brussels", "antwerp": "flanders", "ghent": "flanders", "liege": "wallonia", "charleroi": "wallonia"}
    for p in json.loads((DATA / "communes.json").read_text()):
        assert pick(p, "name") == expect("name", p["name"], *MUNTY[p["code"]]), p["code"]
        assert p["region_key"] == region[p["city"]]
        for e in p["events"]:
            assert pick(e, "name") == expect("name", e["name"], NAMES[e["id"]]["sector_nl"], NAMES[e["id"]]["sector_fr"]), e["id"]
        for x in p["change"]["top"] + p["change"]["top_built"] + ([p["dossier"]] if p["dossier"] else []):
            assert pick(x, "n") == sector_expect(x), (p["code"], x["id"])
    for case in json.loads((DATA / "cases.json").read_text()):
        for x in case["controls"]:
            r = NAMES[x["id"]]
            assert pick(x, "name") == expect("name", x["name"], r["sector_nl"], r["sector_fr"]), (case["slug"], x["id"])


def test_the_names_script_reads_the_same_sector_files_as_the_site():
    from scripts.registry import statbel_names
    from scripts.site import site_data
    assert statbel_names.SECTORS_GEO == site_data.SECTORS_GEO
    assert {k: (v["nl"], v["fr"]) for k, v in site_data.DISTRICT_I18N.items()} == DISTRICTS
