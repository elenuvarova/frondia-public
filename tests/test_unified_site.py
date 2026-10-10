"""The unified Frondia (docs/07-unified-frondia.md): the merged projects' layers reach the site whole.

Guards the merge itself: every lived-in sector of both cities carries every "what's missing" lens, City
Planner's points arrive complete and placed, and every merged layer is registered in its city's manifest
with the reason it has no threshold (a state or a recommendation, never a measured change).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.manifest import Manifest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "public" / "data"
CITIES = ["brussels", "antwerp", "ghent", "liege", "charleroi"]
MIN_RESIDENTS = 200   # the atlas does not shade near-empty sectors (lib/lenses.js)


@pytest.mark.parametrize("city", CITIES)
def test_every_lived_in_sector_carries_every_need_lens(city):
    sectors = json.loads((DATA / f"{city}.json").read_text())["sectors"]
    lived = [s for s in sectors if (s.get("pop") or 0) >= MIN_RESIDENTS]
    assert len(lived) > 0.6 * len(sectors)
    for s in lived:
        assert set(s.get("fit", {})) == {"family", "remote", "senior"}, s["id"]
        assert all(0 <= v <= 100 for v in s["fit"].values()), s["id"]
        assert set(s.get("shop", {})) == {"bakery", "cafe", "confectionery"}, s["id"]
        assert s.get("hot") is not None and s.get("r3") in (0, 1, 2), s["id"]


@pytest.mark.parametrize("city", CITIES)
def test_planner_points_arrive_complete_ranked_and_placed(city):
    p = json.loads((DATA / f"points-{city}.json").read_text())
    assert len(p["types"]) == 14
    for t in p["types"]:
        pts = [x for x in p["points"] if x["t"] == t["key"]]
        assert sorted(x["r"] for x in pts) == list(range(1, 41)), t["key"]
        assert sum(x["role"] == "named" for x in pts) == 10 and sum(x["role"] == "control" for x in pts) == 10
        assert all(x["r"] <= 10 for x in pts if x["role"] == "named")
        assert 0 <= t["before"] < t["after"] <= 1, t["key"]
    # nearly every point lands in a sector of the bundle (Antwerp's planner reaches a little further)
    assert sum(x["s"] is not None for x in p["points"]) / len(p["points"]) > 0.95


@pytest.mark.parametrize("city", CITIES)
@pytest.mark.parametrize("layer", ["fit_score", "shops_access"])
def test_merged_layers_are_registered_and_say_why_no_threshold(city, layer):
    e = Manifest.read(city).layers[layer]
    assert e.threshold is None
    assert e.threshold_source and "порога нет" in e.threshold_source
    assert e.limits and any("состояние" in x for x in e.limits)


@pytest.mark.parametrize("city", CITIES)
def test_services_fifths_are_fifths_of_the_coloured_sectors(city):
    """The legend says "best-served fifth … worst-served fifth": each band must hold about a fifth of
    the sectors the map colours. Fit Score's own percentile ranked forests and the port too, and its
    worst fifth held only 10–16 % of the coloured sectors."""
    sectors = json.loads((DATA / f"{city}.json").read_text())["sectors"]
    lived = [s for s in sectors if (s.get("pop") or 0) >= MIN_RESIDENTS]
    assert not any("fitq" in s for s in sectors if (s.get("pop") or 0) < MIN_RESIDENTS)
    for sc in ("family", "remote", "senior"):
        bands = [s["fitq"][sc] for s in lived]
        for q in range(1, 6):
            assert abs(bands.count(q) / len(bands) - 0.2) <= 0.025, (city, sc, q)
        # a better score never lands in a worse band
        order = sorted(lived, key=lambda s: -s["fit"][sc])
        assert all(a["fitq"][sc] <= b["fitq"][sc] for a, b in zip(order, order[1:]) if a["fit"][sc] > b["fit"][sc])


@pytest.mark.parametrize("city", CITIES)
def test_heat_lede_quotes_its_own_city(city):
    """The heat lens says how closely heat and canopy move together; each city prints its own r."""
    d = json.loads((DATA / f"{city}.json").read_text())
    pairs = [(s["hot"], s["cs"]) for s in d["sectors"] if s.get("hot") is not None and s.get("cs") is not None]
    import statistics
    assert d["heat_canopy_r"] == round(statistics.correlation(*zip(*pairs)), 2) < -0.5


def test_published_test_count_matches_the_suite(request):
    """The colophon says how many tests check the numbers; facts.json went stale at 74 while the suite
    had 82. Checked only when the whole suite runs."""
    if [Path(a).resolve() for a in request.config.args] != [Path(__file__).resolve().parent]:
        pytest.skip("counts only on a run of the whole suite")
    facts = json.loads((DATA / "facts.json").read_text())
    assert facts["tests"] == request.session.testscollected, "rerun scripts/site/site_data.py"


@pytest.mark.parametrize("city", CITIES)
def test_who_is_short_is_cut_in_thirds_of_residents_and_by_the_lens_value(city):
    """Phase 2 "Who is short": the income thirds each hold a third of the residents (not of the sectors:
    the poorest sectors are the most populous), every lens and choice is there, and the worst-off group
    is cut by the lens's own value, so every sector past the cut is in it and none before it."""
    d = json.loads((DATA / f"{city}.json").read_text())
    e = d["equity"]
    assert all(abs(x - 1 / 3) < 0.02 for x in e["income_share"]), e["income_share"]
    assert e["income_cuts"][0] < e["income_cuts"][1]
    expect = {"services": {"family", "remote", "senior"}, "shops": {"bakery", "cafe", "confectionery"}, "heat": {"_"}, "r3": {"_"}}
    for lens, opts in expect.items():
        assert set(e[lens]) == opts, lens
        for o, x in e[lens].items():
            assert len(x["thirds"]) == 3 and all(v is not None for v in x["thirds"]), (lens, o)
            assert all(0 < x[k] < 1 for k in ("all", "kid", "old")), (lens, o)
            if lens != "r3":
                assert 0.33 <= x["all"] <= 0.40, (lens, o, x["all"])   # a third, plus the ties at the cut
    lived = [s for s in d["sectors"] if (s.get("pop") or 0) >= MIN_RESIDENTS and s.get("hot") is not None]
    cut = e["heat"]["_"]["cut"]
    inside = sum(s["pop"] for s in lived if s["hot"] >= cut) / sum(s["pop"] for s in lived)
    assert abs(inside - e["heat"]["_"]["all"]) < 0.01


# Who lives in the worst-off group against all residents, in points, measured on 26 Sep 2026: children in
# the hottest third, people aged 65 and over in the hottest third, 65+ in the worst-served third (family).
# "+" more often, "-" less often, "=" within the 2 points under which the atlas's reading calls it "about
# as often" (GAP_PTS in Atlas.jsx).
WHO_IS_SHORT = {
    "brussels":  ("+", "-", "+"),   # +2.8 · -9.8 · +7.4
    "antwerp":   ("+", "-", "+"),   # +3.8 · -9.0 · +5.1
    "ghent":     ("-", "-", "+"),   # -2.3 · -8.2 · +6.7
    "liege":     ("-", "-", "+"),   # -3.9 · -3.6 · +2.1
    "charleroi": ("=", "-", "="),   # +0.6 · -3.3 · +0.1
}
GAP = 0.02


@pytest.mark.parametrize("city", CITIES)
def test_who_is_short_known_answers(city):
    """Known answers, measured on 26 Sep 2026: in every city the poorest third is the hottest and misses
    both parts of 3-30-300 most often, yet it is the best served by everyday services (the dense centre),
    and people aged 65 and over live in the hottest third less often than residents overall. The rest
    differs by city (WHO_IS_SHORT): children live in the hottest third more often in Brussels and Antwerp,
    less often in Ghent and Liège, about as often in Charleroi; 65+ live in the worst-served third more
    often everywhere but Charleroi. The gaps are smaller in Wallonia. The atlas's reading sentences are
    computed from these numbers, so each city keeps its own answer."""
    e = json.loads((DATA / f"{city}.json").read_text())["equity"]
    heat, r3, fam = e["heat"]["_"], e["r3"]["_"], e["services"]["family"]
    assert heat["thirds"][0] > heat["thirds"][1] > heat["thirds"][2] and heat["thirds"][0] - heat["thirds"][2] > 2
    assert r3["thirds"][0] > 2 * r3["thirds"][2] - 0.05
    assert fam["thirds"][0] > fam["thirds"][2]
    for sign, (group, key) in zip(WHO_IS_SHORT[city], [(heat, "kid"), (heat, "old"), (fam, "old")]):
        d = group[key] - group["all"]
        assert {"+": d >= GAP, "-": d <= -GAP, "=": abs(d) < GAP}[sign], (city, key, round(d, 3))


@pytest.mark.parametrize("city", CITIES)
def test_communes_are_outlined_and_carry_the_commissions_test(city):
    """Phase 2 "Communes": every commune on the map has its outline, dissolved from its sectors, and a
    tested commune's verdict is the Article 8(1) rule itself: more than 45 % green and 10 % canopy."""
    d = json.loads((DATA / f"{city}.json").read_text())
    co = d["communes"]
    assert {c["code"] for c in co["list"]} == {s["id"][:5] for s in d["sectors"]}
    assert all(c["d"].startswith("M") and c["d"].endswith("Z") for c in co["list"])
    tested = [c for c in co["list"] if "green" in c]
    assert len(tested) == co["tested"] and sum(c["exempt"] for c in tested) == co["exempt"]
    for c in tested:
        assert c["exempt"] == (c["green"] > 0.45 and c["canopy"] > 0.10), c["name"]


def test_communes_known_answers():
    """Known answers from the Article 8 page (25 Sep 2026): four of Brussels' nineteen communes are
    exempt, the region as one is not (39.3 %), and leaving the four out would take 33 % of the area and
    15 % of the residents but 59 % of the woody vegetation out of the count. Six projects registered
    before their works, one refused in advance (Neerpede); none in Antwerp, whose source has no
    "not started" status. Ghent (27 Sep 2026): two from the city's own register, Papiermolenpark with
    its control named and Rosdambeekvallei refused in advance (gap 0.048)."""
    b = json.loads((DATA / "brussels.json").read_text())
    co = b["communes"]
    assert sorted(c["name"] for c in co["list"] if c.get("exempt")) == ["Auderghem", "Uccle", "Watermael-Boitsfort", "Woluwe-Saint-Pierre"]
    assert co["region"]["exempt"] is False and abs(co["region"]["green"] - 0.393) < 0.001
    lo = co["leave_out"]
    assert (round(lo["area"], 2), round(lo["residents"], 2), round(lo["woody"], 2), lo["rest"]) == (0.33, 0.15, 0.59, 15)
    reg = b["registered"]
    assert len(reg) == 6 and [r["name"] for r in reg if not r["comparable"]] == ["Réaménagement du parc à Neerpede"]
    a = json.loads((DATA / "antwerp.json").read_text())
    assert a["registered"] == [] and a["communes"]["tested"] == 1 and a["communes"]["exempt"] == 0
    g = json.loads((DATA / "ghent.json").read_text())
    assert [(r["name"], r["type"], r["comparable"]) for r in g["registered"]] == [
        ("Papiermolenpark", "park_creation", True), ("Groenrealisatie Rosdambeekvallei", "green_realisation", False)]


# One-commune cities (26 Sep 2026): Ghent is counted, 0.6 points under the line, and would be exempt with
# farmland as green; Liège is exempt 1.0 point over it, and would not be without water as green; Charleroi
# is exempt under every reading the test runs.
ONE_COMMUNE = {"ghent": (0.4443, False, False), "liege": (0.4604, True, False), "charleroi": (0.4885, True, True)}


@pytest.mark.parametrize("city", list(ONE_COMMUNE))
def test_one_commune_cities_known_answers(city):
    green, exempt, stable = ONE_COMMUNE[city]
    co = json.loads((DATA / f"{city}.json").read_text())["communes"]
    (c,) = [c for c in co["list"] if "green" in c]
    assert (co["tested"], co["exempt"]) == (1, int(exempt)) and co["region"] is None
    assert abs(c["green"] - green) < 0.0005 and c["exempt"] is exempt and c["stable"] is stable


@pytest.mark.parametrize("city", CITIES)
def test_what_if_n_more_reads_the_planners_own_curve(city):
    """Phase 2 "What if N more?": each object type carries the planner's coverage after each rank, from
    the same run as its ranked points: 41 values, today first and all forty last, never falling (a greedy
    solver only adds coverage)."""
    p = json.loads((DATA / f"points-{city}.json").read_text())
    for t in p["types"]:
        st = t["steps"]
        assert len(st) == t["n"] + 1 == 41, t["key"]
        assert abs(st[0] - t["before"]) < 0.001 and abs(st[-1] - t["after"]) < 0.001, t["key"]
        assert all(b >= a - 1e-9 for a, b in zip(st, st[1:])), t["key"]


def _jpeg_size(path: Path) -> tuple[int, int]:
    """Width and height from a JPEG's frame header (no imaging library in the project)."""
    b, i = path.read_bytes(), 2
    while i < len(b) - 9:
        if b[i] != 0xFF:
            i += 1
            continue
        m = b[i + 1]
        if m == 0xD8 or m == 0x01 or 0xD0 <= m <= 0xD7 or m == 0xFF:
            i += 1 if m == 0xFF else 2
            continue
        if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            return int.from_bytes(b[i + 7:i + 9], "big"), int.from_bytes(b[i + 5:i + 7], "big")
        i += 2 + int.from_bytes(b[i + 2:i + 4], "big")
    raise ValueError(f"no frame header in {path}")


@pytest.mark.parametrize("city", CITIES)
def test_whole_city_photos_share_the_fields_frame(city):
    """Phase 2 "The whole city before and after": two true-colour summers, one from each end of the
    measurement windows, in the field's own frame, so the swipe lies exactly under the sectors."""
    d = json.loads((DATA / f"{city}.json").read_text())
    ph = d["photos"]
    assert ph["years"] == [2017, 2024]
    before, after = d["window"].split(" → ")   # "2017–2019 → 2021–2024"
    assert before.startswith(str(ph["years"][0])) and after.endswith(str(ph["years"][1]))
    assert ph["box"] == d["field"]["box"]
    sizes = [_jpeg_size(ROOT / "site" / "public" / s) for s in ph["src"]]
    assert sizes[0] == sizes[1]
    w, h = sizes[0]
    assert abs(w / h - ph["box"][2] / ph["box"][3]) < 0.01


@pytest.mark.parametrize("city", CITIES)
def test_dossier_counts_what_the_russian_dossier_counts(city):
    """Phase 2b, the sector dossier: the site's page puts into English what scripts/report/dossier_html.py
    computes, so the numbers are recomputed here that script's way, from the Article 8 layer and the
    census layer: the city's medians, the third of sectors with the least canopy and the share of all
    children who live in it."""
    import csv
    import statistics
    d = json.loads((DATA / f"{city}.json").read_text())
    dz = d["dossier"]
    rows = list(csv.DictReader((ROOT / f"cities/{city}/layers/article8_2024.csv").open()))
    for key, col in (("t24", "trees_2024"), ("n24", "ndvi_2024"), ("b24", "built_2024")):
        vals = [float(r[col]) for r in rows if r[col] not in ("", None)]
        assert abs(dz["medians"][key] - statistics.median(vals)) < 6e-4, key
    by = sorted((r for r in rows if r["trees_2024"] not in ("", None)), key=lambda r: float(r["trees_2024"]))
    third = {r["id"] for r in by[:len(by) // 3]}
    assert {s["id"] for s in d["sectors"] if s.get("lt3")} == third
    age = {r["id"]: r for r in csv.DictReader((ROOT / f"cities/{city}/layers/population_age.csv").open())}
    kids = sum(int(age[i]["children_0_14"]) for i in third if i in age) / sum(int(v["children_0_14"]) for v in age.values())
    assert abs(dz["kids_third"] - kids) < 6e-4
    # after the baseline: only the bulletin's four kinds, only seasons after 2024
    for s in d["sectors"]:
        for yr, kind, _ in s.get("after", []):
            assert yr in dz["seasons"] and yr > 2024 and kind in ("construction", "confirmed", "unconfirmed", "gained")


def test_dossier_rule_picks_known_sectors():
    """The open rule (lowest income third, lowest canopy third, at least 1 °C hotter, a commune the law
    counts, 500 residents; the most children first) picks what the Russian dossier picked: Ten Eekhove
    first of 77 in Antwerp, and in Brussels the hand-picked Etangs Noirs comes third of 110."""
    ant = json.loads((DATA / "antwerp.json").read_text())["dossier"]["pick"]
    bxl = json.loads((DATA / "brussels.json").read_text())["dossier"]["pick"]
    assert ant["n"] == 77 and ant["ids"][0] == "11002R13-"
    assert bxl["n"] == 110 and bxl["ids"].index("21012A152") == 2


@pytest.mark.parametrize("city", ["liege", "charleroi"])
def test_dossier_rule_picks_none_in_an_exempt_city(city):
    """The rule asks for a commune the law counts. Liège and Charleroi are exempt under Article 8(1), so
    it picks no sector there, and the dossier page says why instead of choosing one some other way."""
    d = json.loads((DATA / f"{city}.json").read_text())
    assert d["dossier"]["pick"]["n"] == 0 and d["dossier"]["pick"]["ids"] == []
    assert all(c["exempt"] for c in d["communes"]["list"] if "green" in c)


@pytest.mark.parametrize("city", CITIES)
def test_downloads_are_english_complete_and_licensed(city):
    """Phase 2b, the data download: every file the /data page offers exists, holds as many rows as the
    package layer it comes from, carries no Russian left over from the package, documents every column,
    and a layer built on OpenStreetMap stays under the ODbL."""
    import csv
    import re
    index = json.loads((DATA / "downloads.json").read_text())[city]
    folder = ROOT / "site" / "public" / "downloads" / city
    manifest = json.loads((folder / "manifest.json").read_text())
    assert [l["key"] for l in manifest["layers"]] == [l["key"] for l in index["layers"]]
    assert not re.search("[А-Яа-яЁё]", (folder / "manifest.json").read_text())
    for layer in index["layers"]:
        if layer.get("format") == "GeoPackage":
            import sqlite3
            src = ROOT / f"cities/{city}/layers/{layer['file']}"
            assert (folder / layer["file"]).read_bytes() == src.read_bytes(), layer["key"]
            con = sqlite3.connect(folder / layer["file"])
            assert con.execute("select srs_id, geometry_type_name from gpkg_geometry_columns").fetchone() == (3035, "MULTIPOLYGON")
            assert con.execute('select count(*) from "t8_UEAPolygons"').fetchone()[0] == layer["rows"]
            assert [c["name"] for c in layer["columns"]] == [r[1] for r in con.execute('pragma table_info("t8_UEAPolygons")')]
            con.close()
            continue
        text = (folder / layer["file"]).read_text(encoding="utf-8")
        assert not re.search("[А-Яа-яЁё]", text), layer["key"]
        rows = list(csv.DictReader(text.splitlines()))
        assert len(rows) == layer["rows"] and [c["name"] for c in layer["columns"]] == list(rows[0].keys())
        src = ROOT / f"cities/{city}/layers/{layer['key']}.csv"
        if src.exists():
            assert len(rows) == sum(1 for _ in csv.DictReader(src.open(encoding="utf-8"))), layer["key"]
        if any("OpenStreetMap" in c for c in layer["credit"]):
            assert layer["licence"].startswith("ODbL"), layer["key"]
        if layer["key"].startswith(("article8", "monitoring")):
            assert layer["threshold"] and "95th percentile" in layer["threshold_from"]


def test_downloads_read_the_bulletin_after_documents():
    """The season file keeps what the instruments said and adds the bulletin's reading after the
    documents: in Brussels 2026 Peterbos reads as a canopy loss by both instruments and as construction
    by the documents (works from April 2026), Wolvendael and Parc Forestier stay canopy losses."""
    import csv
    rows = {r["name"]: r for r in csv.DictReader((ROOT / "site/public/downloads/brussels/monitoring_2026.csv").open())}
    assert rows["PETERBOS"]["dw_label"] == "canopy loss" and rows["PETERBOS"]["bulletin"] == "construction"
    assert rows["WOLVENDAEL"]["bulletin"] == rows["PARC FORESTIER"]["bulletin"] == "canopy loss"


@pytest.mark.parametrize("city", CITIES)
def test_sealed_ground_on_the_atlas_is_the_layers_verdict(city):
    """Phase 2c, item 1: the atlas's built-up measure shows the layer's own verdicts and threshold, and
    its legend is the distribution of the same effects the map colours (comparable sectors only)."""
    import csv
    d = json.loads((DATA / f"{city}.json").read_text())
    b = d["built"]
    S = json.loads((ROOT / f"cities/{city}/layers/article8_2024_summary.json").read_text())
    rows = {r["id"]: r for r in csv.DictReader((ROOT / f"cities/{city}/layers/article8_2024.csv").open())}
    word = {"рост": "up", "потеря": "down", "шум": "noise", "контроль несопоставим": "refused"}
    assert b["threshold"] == S["thresholds"]["built"]
    for s in d["sectors"]:
        r = rows.get(s["id"])
        assert s.get("bv") == (word[r["built_verdict"]] if r else None), s["id"]
    assert (b["counts"]["up"], b["counts"]["down"]) == (S["trend"]["built_up_sectors"], S["trend"]["built_down_sectors"])
    shown = [s for s in d["sectors"] if s["cmp"] and s.get("be") is not None]
    assert sum(b["hist"]["effect"]) == len(shown)
    assert b["hist"]["lo"] <= min(s["be"] for s in shown) and b["hist"]["hi"] >= max(s["be"] for s in shown)


def test_commune_pages_read_the_packages():
    """Phase 2c, item 3: every commune the Commission's test ran on has a page, and its numbers are the
    packages': the test from the summary (six decimals — rounding to four first printed Uccle 60.9 % and
    Molenbeek 27.1 % against 60.8 and 27.0), the readings, the zero measurement, the balance summed from the
    sectors beyond noise, and the 2017–2024 verdicts counted from the city's own sectors."""
    import csv
    pages = json.loads((DATA / "communes.json").read_text())
    by = {p["code"]: p for p in pages}
    for city in CITIES:
        S = json.loads((ROOT / f"cities/{city}/layers/art8_official_2021_summary.json").read_text())
        d = json.loads((DATA / f"{city}.json").read_text())
        atlas = {c["code"]: c for c in d["communes"]["list"]}
        for r in S["laus"]:
            code = r["lau_id"][3:]
            p = by[code]
            assert p["city"] == city and p["lau_id"] == f"lau2024.BE.{code}"
            assert p["art8"]["green"] == r["green_ucuc"] == atlas[code]["green"]
            assert p["art8"]["exempt"] == r["exempt"]
            sens = {x["reading"]: x for x in p["art8"]["readings"]}
            assert sens["official"]["exempt"] == r["exempt"] and sens["with_arable"]["exempt"] == r["exempt_with7"]
            secs = [s for s in d["sectors"] if s["id"][:5] == code]
            assert p["change"]["counts"]["up"] == sum(s.get("nv") == "up" for s in secs)
            assert p["change"]["built"]["up"] == sum(s.get("bv") == "up" for s in secs)
            for season in ("2025", "2026"):
                rows = [x for x in csv.DictReader((ROOT / f"cities/{city}/layers/art8_balance_{season}.csv").open()) if x["id"][:5] == code]
                lost = sum(float(x["trees_eff_ha"]) for x in rows if x["trees_verdict"] == "потеря")
                assert abs(p["balance"]["seasons"][season]["trees"]["lost"] - lost) < 0.06
    assert len(pages) == 23
    u = by["21016"]
    assert u["name"] == "Uccle" and u["art8"]["exempt"] and round(100 * u["art8"]["green"], 1) == 60.8
    assert {(e["name"], e["season"], e["kind"]) for e in u["events"]} >= {("WOLVENDAEL", 2025, "canopy loss"), ("WOLVENDAEL", 2026, "canopy loss")}
    a = by["21001"]
    assert "ninove" in a["cases"] and any("Neerpede" in x["name"] and not x["comparable"] for x in a["registered"])
    ant = by["11002"]
    assert set(ant["cases"]) == {"droogdokkenpark", "spoor-noord"} and ant["dossier"]["n"].upper().startswith("TEN EEKHOVE")
    assert round(100 * by["21012"]["art8"]["green"], 1) == 27.0


def test_official_canopy_editions_known_answers():
    """Two editions of the official canopy layer (WVL 2018 carries the 2018 forest mask, 2021 does not):
    the city-wide canopy rises in every city, the independent aerial map in Flanders rises far less,
    and Antwerp's widest gap is the old park whose aerial canopy barely moved. Measured answers, per city."""
    facts = json.loads((DATA / "facts.json").read_text())
    ed = facts["editions"]
    assert set(ed) == {"brussels", "antwerp", "ghent", "liege", "charleroi"}
    for c, e in ed.items():
        assert e["canopy_2021"] - e["canopy_2018"] > 0.03, c
        assert e["threshold_canopy"] > 0.05, c   # a sector's canopy change under 5 points is noise in every city
    for c in ("antwerp", "ghent"):
        a = ed[c]["aerial"]
        official = a["official_canopy_2021"] - a["official_canopy_2018"]
        aerial = a["aerial_high_2021"] - a["aerial_high_2018"]
        assert official > 2 * aerial, c
    ex = ed["antwerp"]["aerial"]["example"]
    assert ex["name"] == "PARK" and ex["official_2018"] < 0.1 and ex["official_2021"] > 0.6
    assert abs(ex["aerial_2021"] - ex["aerial_2018"]) < 0.1


def test_brussels_own_vegetation_map_known_answers():
    """Bruxelles Environnement's map, 2021 and 2023, through the atlas's threshold: the 2023 share is the figure
    the region announced (48.7 %), and only a few sectors move beyond noise against their twelve places."""
    bv = json.loads((DATA / "facts.json").read_text())["be_vegetation"]
    assert abs(bv["share_2023"] - 0.487) < 0.001   # the region's announced 48.7 %: the map is read in the right frame
    assert bv["share_2021"] > bv["share_2023"]
    v = bv["verdicts"]
    assert (v["потеря"], v["прирост"]) == (10, 18)
    # losses and gains beyond noise apart: the raw 274 ha drop is mostly a city-wide shift, not where sectors moved
    assert bv["loss_ha"] < 0 < bv["gain_ha"] and abs(bv["loss_ha"]) < abs(bv["raw_change_ha"]) / 10


@pytest.mark.parametrize("city", CITIES)
def test_tree_priority_rides_on_the_atlas_sectors(city):
    """Ranks 1–10 named for planting before any planting, 11–20 their comparison: twenty sectors per city carry
    the rank and role the layer wrote, and the city carries the day they were named."""
    d = json.loads((DATA / f"{city}.json").read_text())
    tagged = sorted((s["tr"], s["trl"]) for s in d["sectors"] if "tr" in s)
    assert [r for r, _ in tagged] == list(range(1, 21))
    assert all((role == "named") == (rank <= 10) for rank, role in tagged)
    # a tripwire for the preregistration, not a known answer: the list was named on this day and must keep it
    assert d["tree_named_at"] == "2026-10-09"
    # the planting check starts from the city's own register where there is one (Antwerp, Brussels, Ghent)
    assert (d["tree_register_copy"] is None) == (city in ("liege", "charleroi"))
    # the base never comes after the record
    assert d["tree_register_copy"] is None or d["tree_register_copy"] <= d["tree_named_at"]


def test_groenkaart_check_counts_direction_beside_verdicts():
    """When our canopy says "changed", Groenkaart agrees on the verdict in 7 of 22 sectors and on the direction in
    15 of 22 (its own threshold is higher): both rates are in the data (facts.json), from the same run; the pages print
    only the verdict rate — the direction rate is too close to a coin to quote. Measured 09.10.2026."""
    c = json.loads((DATA / "facts.json").read_text())["check"]["pooled"]["canopy"]
    assert c["agreement_when_ours_changed"] == {"k": 7, "n": 22}
    assert c["direction_when_ours_changed"] == {"k": 15, "n": 22}



def test_proof_photos_show_the_sectors_the_numbers_are_about():
    """The landing's photo pairs and the numbers under them come from two scripts: the photos must be of the very
    sectors the data chose (proof_photos.py reads the examples; a rerun of the checks must be followed by it)."""
    proof = json.loads((DATA.parent / "proof/proof.json").read_text())
    facts = json.loads((DATA / "facts.json").read_text())
    assert proof["editions"]["sector"] == facts["editions"]["antwerp"]["aerial"]["example"]["id"]
    assert proof["region"]["sector"] == facts["be_vegetation"]["example"]["id"]
    for pair in proof.values():
        assert set(pair["files"]) == set(pair["sources"]) and pair["credit"] and pair["licence"]
