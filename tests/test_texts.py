"""The data's own words in Dutch and French (plan 5, L5): the English is a template, the numbers are put in by code in
the reader's notation, a translation is bound to the English it was made from by a hash, and the English output is the
one the site has always had."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.site import texts
from scripts.site.texts import Join, Missing, Munty, Num, Place, Text, h, nums, render

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "public" / "data"


def tx(key, en, **values):
    """A Text built without T(), so these test keys never enter texts.UNITS (the set every language must translate)."""
    return Text(key, en, tuple(sorted(values.items())))


def test_numbers_and_places_in_each_notation():
    t = tx("test.thr", "Greenness {ndvi} in {city}.", ndvi=Num(0.0373, 4), city=Place("liege"))
    assert render(t, "en") == "Greenness 0.0373 in Liège."
    cat = {"test.thr": {"en": h("Greenness {ndvi} in {city}."), "text": "Groenheid {ndvi} in {city}."}}
    assert render(t, "nl", cat) == "Groenheid 0,0373 in Luik."
    assert render(tx("test.neg", "{v}", v=Num(-0.04, 2)), "fr", {"test.neg": {"en": h("{v}"), "text": "{v}"}}) == "−0,04"


def test_a_stale_or_missing_translation_stops_the_build():
    t = tx("test.stale", "Old English.")
    with pytest.raises(Missing):
        render(t, "nl", {"test.stale": {"en": h("Older English."), "text": "Oud."}})
    with pytest.raises(Missing):
        render(t, "nl", {})
    with pytest.raises(Missing):            # a placeholder lost in translation
        render(tx("test.ph", "A {x}.", x="b"), "nl", {"test.ph": {"en": h("A {x}."), "text": "Een."}})


def test_a_text_without_values_keeps_its_braces_and_joins_mend_double_stops():
    assert render(tx("test.brace", "The {model} said so."), "en") == "The {model} said so."
    assert render(Join((tx("test.a", "Statbel."), "."), sep="", fix=("..", ".")), "en") == "Statbel."


def test_a_join_drops_an_empty_part_so_no_stray_space_is_left():
    """Ruling T7: a layer without an OpenStreetMap line had no trailing space before templates, and has none now."""
    src = tx("test.src", "Statbel.")
    assert render(Join((src, ""), sep=" ", fix=("..", ".")), "en") == "Statbel."
    assert render(Join((src, None), sep=" "), "en") == "Statbel."
    assert render(Join((src, tx("test.osm", "OSM.")), sep=" "), "en") == "Statbel. OSM."


def test_one_key_cannot_carry_two_english_templates():
    try:
        texts.T("test.twice", "One.")
        assert texts.T("test.twice", "One.").en == "One."
        with pytest.raises(SystemExit):
            texts.T("test.twice", "Two.")
    finally:
        texts.UNITS.pop("test.twice", None)
        texts.FIELDS.pop("test.twice", None)


def test_communes_are_named_by_statbel_whatever_form_the_register_uses():
    assert render(Munty("Bruxelles"), "en") == "Bruxelles"
    assert render(Munty("Bruxelles"), "nl") == "Brussel"
    assert render(Munty("Berchem-Sainte-Agathe"), "nl") == "Sint-Agatha-Berchem"
    assert render(Munty("Molenbeek"), "nl") == "Sint-Jans-Molenbeek"        # the English site's short form
    assert render(Munty("Saint-Josse"), "fr") == "Saint-Josse-ten-Noode"
    with pytest.raises(SystemExit, match="Atlantis"):
        render(Munty("Atlantis"), "nl")


def test_literal_numbers_read_alike_in_each_notation_and_quotes_keep_the_original():
    """Ruling P29: the same rule as site/web/scripts/numbers.mjs — French groups with U+202F (or U+00A0), never ".";
    a quoted span keeps the source's notation and is not compared."""
    assert nums("1,246,136 people, 0.0373", "en") == nums("1.246.136 inwoners, 0,0373", "nl") \
        == nums("1 246 136 habitants, 0,0373", "fr") == ["0.0373", "1246136"]
    assert nums("2017–2024", "nl") == ["2017", "2024"]
    assert nums("1.5 km", "nl") != ["1.5"]
    assert nums("3.200 m2", "fr") != ["3200", "2"]                            # "." is no French group
    en = json.loads((DATA / "register.json").read_text())
    why = next(c["why"] for c in en["contracts"] if c["id"] == 60)
    assert "3.200 m2" in why
    fr = "Le contrat s’engage à « aménager un parc de 3.200 m2 en intérieur d'îlot »."
    assert nums(fr, "fr") == [] and nums("commits to \"aménager un parc de 3.200 m2\"", "en") == []
    # the cases the site's numbersOf reads too (tests/catalogues.test.ts): one list, so the two rules never drift
    cases = json.loads((ROOT / "site/web/scripts/numbers-cases.json").read_text())["cases"]
    assert len(cases) >= 20
    for text, lang, want, why in cases:
        assert nums(text, lang) == want, f"{text!r} ({lang}): {why}"


@pytest.fixture(scope="module")
def index():
    from scripts.site import downloads
    return downloads.build_index()


def test_the_english_downloads_and_register_are_what_the_site_had(index):
    from scripts.site import register
    doc, _files = index
    assert render(doc, "en") == json.loads((DATA / "downloads.json").read_text())
    assert render(register.build(), "en") == json.loads((DATA / "register.json").read_text())


def test_the_english_files_are_the_same_bytes(index):
    """Byte for byte: downloads.json, every city's CSVs, GeoPackages and manifest.json as build_index holds them."""
    from scripts.site import downloads
    doc, files = index
    assert downloads._index_json(render(doc, "en")).encode("utf-8") == (DATA / "downloads.json").read_bytes()
    for p, data in files.items():
        assert p.read_bytes() == data, p
    for city, v in render(doc, "en").items():
        assert v["manifest_bytes"] == (ROOT / f"site/public/downloads/{city}/manifest.json").stat().st_size


def test_building_the_index_writes_nothing(monkeypatch):
    """Ruling T7: manifest_bytes is measured on the manifest serialised in memory, not on a file written first."""
    from scripts.site import downloads

    def refuse(*a, **k):
        raise AssertionError("build_index wrote a file")
    for name in ("write_bytes", "write_text", "mkdir", "touch", "unlink"):
        monkeypatch.setattr(Path, name, refuse)
    doc, files = downloads.build_index()
    for city in downloads.CITY_NAME:
        man = files[downloads.SITE / "downloads" / city / "manifest.json"]
        assert doc[city]["manifest_bytes"] == len(man)
        assert json.loads(man)["name"] == texts.CITY[city]["en"]


def test_every_data_text_has_a_key_by_the_plan(index):
    from scripts.site import register
    register.build()
    prefixes = ("layer.", "column.", "threshold.", "osm.", "register.kind.", "register.status.", "register.label.",
                "register.why.", "register.model_why.", "register.check_why.")
    assert texts.UNITS and all(k.startswith(prefixes) for k in texts.UNITS)
    assert {"threshold.article8", "threshold.monitoring", "threshold.balance", "threshold.groenkaart", "threshold.trees",
            "threshold.level", "threshold.none", "column.id", "column.name"} <= texts.UNITS.keys()
    # one translation serves five cities: no English template carries a city's own value
    for en in texts.UNITS.values():
        assert not any(op in en for op in ("STIB-MIVB", "De Lijn", "TEC ")), en


def test_a_language_is_generated_with_its_numbers_in_its_notation(index, monkeypatch):
    """A complete catalogue made of the English itself (each entry marked "same", as such a text must be): the
    language's file differs from the English only where code put a number, a city or a commune in."""
    from scripts.site import register
    reg = register.build()
    doc, _ = index
    cat = {k: {"en": h(en), "text": en, "same": True} for k, en in texts.UNITS.items()}
    nl = render(doc, "nl", cat)
    gh = next(l for l in nl["ghent"]["layers"] if l["key"] == "article8_2024")
    assert nl["ghent"]["name"] == "Gent" and gh["threshold_from"].startswith("Greenness 0,0")
    assert gh["threshold"] == next(l for l in render(doc, "en")["ghent"]["layers"] if l["key"] == "article8_2024")["threshold"]
    communes = {c["commune"] for c in render(reg, "nl", cat)["contracts"]}
    assert {"Brussel", "Sint-Agatha-Berchem"} <= communes


def test_sync_keeps_same_only_while_the_text_is_the_english(tmp_path, monkeypatch):
    """Ruling P25: apply rewrites a key with the current English's hash; a hand-set "same": true survives only while
    the text still equals the English; a vanished key is dropped; a key the documents do not have is refused."""
    from scripts.site import i18n_sync
    monkeypatch.setattr(texts, "I18N", tmp_path)
    units = {"a": "NDVI", "b": "Greenness.", "c": "Canopy."}
    (tmp_path / "nl.json").write_text(json.dumps({
        "a": {"en": h("NDVI"), "text": "NDVI", "same": True},
        "b": {"en": h("Greenness."), "text": "Greenness.", "same": True},
        "gone": {"en": h("x"), "text": "y"}}))
    assert i18n_sync.todo("nl", units) == {"c": {"en": "Canopy.", "h": h("Canopy.")}}
    removed = i18n_sync.apply("nl", {"a": "NDVI", "b": "Groenheid.", "c": "Kroon."}, units)
    cat = json.loads((tmp_path / "nl.json").read_text())
    assert removed == ["gone"] and list(cat) == ["a", "b", "c"]
    assert cat["a"] == {"en": h("NDVI"), "text": "NDVI", "same": True}
    assert cat["b"] == {"en": h("Greenness."), "text": "Groenheid."}
    assert i18n_sync.todo("nl", units) == {} and i18n_sync.problems(units, published=[]) == []
    # the English changes: the entry is todo again, its "same" no help
    units2 = {**units, "a": "NDVI, the greenness index"}
    assert list(i18n_sync.todo("nl", units2)) == ["a"]
    assert i18n_sync.problems(units2, published=[])
    with pytest.raises(SystemExit, match="nope"):
        i18n_sync.apply("nl", {"nope": "x"}, units)


def test_check_fails_for_a_published_language_without_texts_and_not_for_a_preview_one(tmp_path, monkeypatch):
    from scripts.site import i18n_sync
    monkeypatch.setattr(texts, "I18N", tmp_path)
    units = {"a": "Greenness."}
    assert i18n_sync.problems(units, published=[]) == []              # nl, fr in preview, no files: nothing to check
    assert i18n_sync.problems(units, published=["nl"])                # published without its data texts
    (tmp_path / "fr.json").write_text("{}")                            # a file: the language is generated, so complete
    assert i18n_sync.problems(units, published=[])
    # the site's registry: English alone, or nl and fr together (plan 5, task 15's one commit, which `git revert` undoes)
    assert i18n_sync.published() in ([], ["nl", "fr"])


# ── fix round 1: what a translation may not do, and a bad catalogue changes no file ──────────────────

UNITS_FIX = {"thr": "{thr}: the 95th percentile.", "city": "Greenness in Ghent.", "far": "None closer than 1.5 km.",
             "quote": "The {model} said so."}


@pytest.mark.parametrize("key,text,why", [
    ("city", "Groenheid in {city}.", "placeholders"),           # a placeholder the English has not (and no value)
    ("thr", "{thr:>12}: het 95e percentiel.", "placeholders"),  # a format spec
    ("thr", "{thr!r}: het 95e percentiel.", "placeholders"),    # a conversion
    ("thr", "{thr}: het 95e percentiel {thr}.", "placeholders"),  # twice
    ("quote", "Het model zei het.", "placeholders"),            # a literal brace of a text without values, lost
    ("far", "Niet dichter dan 2 km.", "numbers"),               # an invented number
    ("far", "Niet dichter dan 1.5 km.", "numbers"),             # the English notation in Dutch
    ("thr", "{thr}: het 95e percentiel, 2026.", "numbers"),
    ("city", "", "empty"), ("city", "   ", "empty"),
])
def test_apply_refuses_a_bad_translation_and_writes_nothing(tmp_path, monkeypatch, key, text, why):
    from scripts.site import i18n_sync
    monkeypatch.setattr(texts, "I18N", tmp_path)
    with pytest.raises(SystemExit, match=why):
        i18n_sync.apply("nl", {key: text}, UNITS_FIX)
    assert not (tmp_path / "nl.json").exists()


def test_apply_takes_good_texts_with_or_without_the_hash_and_refuses_another_englishs_hash(tmp_path, monkeypatch):
    from scripts.site import i18n_sync
    monkeypatch.setattr(texts, "I18N", tmp_path)
    i18n_sync.apply("nl", {"far": "Niet dichter dan 1,5 km.", "thr": {"text": "{thr}: het 95e percentiel.",
                                                                          "h": h(UNITS_FIX["thr"])}}, UNITS_FIX)
    assert json.loads((tmp_path / "nl.json").read_text())["far"]["text"] == "Niet dichter dan 1,5 km."
    with pytest.raises(SystemExit, match="another English"):
        i18n_sync.apply("nl", {"city": {"text": "Groenheid in Gent.", "h": h("Greenness in Brussels.")}}, UNITS_FIX)


def test_a_text_equal_to_the_english_needs_same_true_in_apply_check_and_render(tmp_path, monkeypatch):
    """Final review M2: a draft that hands the English back is English on a Dutch page. apply refuses it unless the draft
    entry (or the file) marks it "same": true; check and the render refuse an unmarked one written by hand; a text with
    no letters outside its placeholders is the same in every language and needs no mark."""
    from scripts.site import i18n_sync
    monkeypatch.setattr(texts, "I18N", tmp_path)
    units = {"name": "Greenness.", "bare": "{n}", "ndvi": "NDVI"}
    with pytest.raises(SystemExit, match="the English itself"):
        i18n_sync.apply("nl", {"name": "Greenness."}, units)
    with pytest.raises(SystemExit, match="the English itself"):
        i18n_sync.apply("nl", {"name": {"text": "Greenness.", "h": h("Greenness.")}}, units)
    assert not (tmp_path / "nl.json").exists()
    # marked in the draft: taken, and the mark is kept
    i18n_sync.apply("nl", {"ndvi": {"text": "NDVI", "same": True}, "bare": "{n}", "name": "Groenheid."}, units)
    cat = json.loads((tmp_path / "nl.json").read_text())
    assert cat["ndvi"] == {"en": h("NDVI"), "text": "NDVI", "same": True}
    assert "same" not in cat["bare"] and "same" not in cat["name"]
    assert i18n_sync.problems(units, published=[]) == []
    # marked in the file already: a draft may hand the same English back
    i18n_sync.apply("nl", {"ndvi": "NDVI"}, units)
    assert json.loads((tmp_path / "nl.json").read_text())["ndvi"]["same"] is True
    # a hand edit that copies the English without the mark: check and the render both refuse it
    cat = json.loads((tmp_path / "nl.json").read_text())
    cat["name"] = {"en": h("Greenness."), "text": "Greenness."}
    (tmp_path / "nl.json").write_text(json.dumps(cat))
    found = i18n_sync.problems(units, published=[])
    assert len(found) == 1 and "name" in found[0] and "the English itself" in found[0]
    with pytest.raises(Missing, match="the English itself"):
        render(tx("name", "Greenness."), "nl", cat)
    assert render(tx("ndvi", "NDVI"), "nl", cat) == "NDVI"


def test_check_catches_a_hand_edited_catalogue(tmp_path, monkeypatch):
    from scripts.site import i18n_sync
    monkeypatch.setattr(texts, "I18N", tmp_path)
    cat = {k: {"en": h(en), "text": t} for (k, en), t in zip(UNITS_FIX.items(), (
        "{thr}: het 95e percentiel.", "Groenheid in Gent.", "Niet dichter dan 3 km.", "Het {model} zei het."))}
    (tmp_path / "nl.json").write_text(json.dumps(cat))
    found = i18n_sync.problems(UNITS_FIX, published=[])
    assert len(found) == 1 and "far" in found[0] and "numbers" in found[0]
    with pytest.raises(Missing, match="numbers"):
        render(tx("far", UNITS_FIX["far"]), "nl", cat)


def test_a_partial_catalogue_stops_site_data_before_it_writes_anything(tmp_path, monkeypatch):
    from scripts.site import site_data
    monkeypatch.setattr(texts, "I18N", tmp_path)
    (tmp_path / "nl.json").write_text(json.dumps({"threshold.none": {"en": "x", "text": "y"}}))

    def refuse(*a, **k):
        raise AssertionError("site_data wrote a file")
    for name in ("write_bytes", "write_text", "mkdir", "touch", "unlink"):
        monkeypatch.setattr(Path, name, refuse)
    assert site_data.main() == 1


def test_numbers_are_not_grouped_in_any_language():
    """Known and left as is (fix round 1): Num never groups, so a count ≥ 1000 put in as Num reads "1310" in Dutch and
    French as in English, not "1.310" / "1 310". The data's counts today are put in as plain strings."""
    assert [render(Num(1310, 0), loc) for loc in ("en", "nl", "fr")] == ["1310", "1310", "1310"]
    assert render(Num(-1310.5, 1), "fr") == "−1310,5"


# ── Task 13: the Dutch and French documents ─────────────────────────────────────────────────────────

LOCS = ["nl", "fr"]


@pytest.mark.parametrize("loc", LOCS)
def test_every_unit_is_translated_from_the_current_english(loc):
    from scripts.site import downloads, register
    downloads.build_index(); register.build()
    cat = texts.Catalog.load(loc)
    missing = [k for k, en in texts.UNITS.items() if k not in cat or cat[k]["en"] != h(en)]
    assert not missing, missing[:10]


def _same_shape(a, b, path=""):
    assert type(a) is type(b), path
    if isinstance(a, dict):
        assert a.keys() == b.keys(), path
        for k in a:
            _same_shape(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            _same_shape(x, y, f"{path}[{i}]")


@pytest.mark.parametrize("loc", LOCS)
@pytest.mark.parametrize("name", ["downloads", "register"])
def test_a_language_file_has_the_english_shape_and_the_same_non_text_values(loc, name):
    en = json.loads((DATA / f"{name}.json").read_text())
    tr = json.loads((DATA / f"{name}.{loc}.json").read_text())
    _same_shape(en, tr)
    if name == "downloads":
        for c in en:
            for a, b in zip(en[c]["layers"], tr[c]["layers"]):
                for k in ("key", "group", "file", "rows", "bytes", "computed", "threshold", "licence", "credit"):
                    assert a.get(k) == b.get(k), (c, a["key"], k)
    else:
        for a, b in zip(en["contracts"], tr["contracts"]):
            assert (a["id"], a["name"], a["url"], a["label"], a["measures"]) == (b["id"], b["name"], b["url"], b["label"], b["measures"])


@pytest.mark.parametrize("loc", LOCS)
@pytest.mark.parametrize("name", ["downloads", "register"])
def test_the_committed_language_files_are_a_fresh_render(index, loc, name):
    """downloads.<loc>.json and register.<loc>.json are what site_data would write today, byte for byte: a catalogue
    edited without rerunning site_data.py fails here."""
    from scripts.site import downloads, register
    cat = texts.Catalog.load(loc)
    if name == "downloads":
        want = downloads._index_json(render(index[0], loc, cat))
    else:
        want = register._json(render(register.build(), loc, cat))
    assert (DATA / f"{name}.{loc}.json").read_text(encoding="utf-8") == want


@pytest.mark.parametrize("loc", LOCS)
def test_translations_keep_their_literal_numbers_and_the_glossary(loc):
    import re
    cat = texts.Catalog.load(loc)
    from scripts.site import downloads, register
    downloads.build_index(); register.build()
    terms = texts.glossary_terms()
    assert len(terms) >= 20
    for k, en in texts.UNITS.items():
        t = cat[k]["text"]
        assert nums(t, "en" if t == en else loc) == nums(en, "en"), k
        if t == en:
            assert cat[k].get("same"), f"{k} is still English"
        for g in terms:
            if g["en"].search(en):
                assert g[loc].search(t), (k, g["en"].pattern)
        assert not re.search(r"[“”]", t) and not re.search(r"\w'\w", t), k


def test_the_register_names_its_communes_in_the_language():
    nl = json.loads((DATA / "register.nl.json").read_text())
    assert {c["commune"] for c in nl["contracts"]} >= {"Brussel", "Sint-Agatha-Berchem"}


def test_the_glossary_parse_matches_the_sites():
    """texts.glossary_terms reads the table as site/web/tests/glossary.ts does: a code row is a check, "\\|" is the
    alternation, a plain row is guidance, a half-coded row is refused."""
    md = "## Terms\n\n| en | nl | fr | source | why |\n|---|---|---|---|---|\n" \
         "| `\\bnoise\\b` | `ruis` | `bruit\\|bruits` | method | x |\n| lens | weergave | vue | method | y |\n## Next\n"
    (g,) = texts.glossary_terms(md)
    assert g["fr"].search("Les BRUITS") and g["en"].search("Noise") and not g["en"].search("noises")
    with pytest.raises(SystemExit):
        texts.glossary_terms("## Terms\n| `a` | b | `c` | s | w |\n")
