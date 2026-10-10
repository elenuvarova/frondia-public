"""The data's own words in every language of the site (plan 5, L5 and L6).

L5 — a text of the data is a template, not a finished string. The unit of translation is the English template with named
placeholders ("Greenness {ndvi}, canopy {trees} …"), under a stable key (`layer.<key>.<field>`, `register.why.<id>`); a
translation in `scripts/site/i18n/<loc>.json` is bound to the English it was made from by the first 12 hex digits of the
SHA-256 of that English. The values — thresholds, counts, the city, the transit operator, the commune — are put in by
`render()`, in the reader's notation (0.0373 · 0,0373), never by the translator: one translation serves five cities, and a
new threshold needs no new translation. No file for a language: the language is not generated. A file, but a key missing
or its English changed since: generation stops (`Missing`). The English output is the one the site has always had, byte for
byte (tests/test_texts.py).

L6 — what is not translated: the sources' credits (the rights holders' own wording), licence names, the contracts' quotes
(the French original), the names of projects and contracts, a layer's `group` (an identifier, not a word), and the
downloadable files themselves — the CSVs, `manifest.json`, `register.csv` stay English; /data says so in one line.

    python -m scripts.site.i18n_sync todo --loc nl     # what a language still lacks (scripts/site/i18n_sync.py)
"""
from __future__ import annotations

import csv
import functools
import hashlib
import json
import re
import string
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / "scripts/site/i18n"
LOCS = ("nl", "fr")                  # the languages that can have data texts; English is the template itself
MINUS = "−"

CITY = {"brussels": {"en": "Brussels", "nl": "Brussel", "fr": "Bruxelles"},
        "antwerp": {"en": "Antwerp", "nl": "Antwerpen", "fr": "Anvers"},
        "ghent": {"en": "Ghent", "nl": "Gent", "fr": "Gand"},
        "liege": {"en": "Liège", "nl": "Luik", "fr": "Liège"},
        "charleroi": {"en": "Charleroi", "nl": "Charleroi", "fr": "Charleroi"}}

# every key a language must translate, with its English template (filled by T() as the documents are built), and the
# placeholders of each template that has values
UNITS: dict[str, str] = {}
FIELDS: dict[str, frozenset[str]] = {}


class Missing(SystemExit):
    """A language's file lacks the translation of a text's current English (or the translation lost a placeholder)."""


@dataclass(frozen=True)
class Num:
    """A number with d decimals: English as the f-string always wrote it, Dutch and French with a decimal comma and a
    true minus. No grouping in any language, as the English never had one: 1310 stays "1310", not "1.310" or
    "1 310" (known, left as is: tests/test_texts.py)."""
    v: float
    d: int

    def render(self, loc: str) -> str:
        s = f"{self.v:.{self.d}f}"
        return s if loc == "en" else s.replace(".", ",").replace("-", MINUS)


@dataclass(frozen=True)
class Place:
    """A city by its key, named in the language."""
    city: str

    def render(self, loc: str) -> str:
        return CITY[self.city][loc]


@dataclass(frozen=True)
class Munty:
    """A commune by the name the register of contracts gives it (French, or the English site's short form: "Molenbeek",
    "Saint-Josse"), named in the language by Statbel's register 2024 (data/statbel_names_2024.csv). English: as given."""
    name: str

    def render(self, loc: str) -> str:
        if loc == "en":
            return self.name
        t = _munty_table()
        if self.name not in t:
            raise SystemExit(f"texts.Munty: no commune {self.name!r} in data/statbel_names_2024.csv nor among Brussels's short forms")
        return t[self.name][loc]


@functools.cache
def _munty_table() -> dict[str, dict[str, str]]:
    """munty_fr and munty_nl of every row → both names; plus the English site's short forms of Brussels's communes (the
    adapter's commune of each sector, the `c` of brussels.json), resolved by the sector's code."""
    with (ROOT / "data/statbel_names_2024.csv").open(encoding="utf-8") as f:
        rows = {r["id"]: r for r in csv.DictReader(f)}
    out: dict[str, dict[str, str]] = {}
    for r in rows.values():
        names = {"nl": r["munty_nl"], "fr": r["munty_fr"]}
        out.setdefault(r["munty_fr"], names)
        out.setdefault(r["munty_nl"], names)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from engine.adapters import ADAPTERS
    for u in ADAPTERS["brussels"]().units():
        r = rows[u.id]
        out.setdefault(u.commune, {"nl": r["munty_nl"], "fr": r["munty_fr"]})
    return out


@dataclass(frozen=True)
class Text:
    key: str
    en: str
    values: tuple[tuple[str, object], ...] = ()


def T(key: str, en: str, **values) -> Text:
    """A text of the data: its key, its English template and the values to put in. Registers the key as a unit to
    translate; one key with two different English templates is an error in the code, not a second unit."""
    if UNITS.get(key, en) != en:
        raise SystemExit(f"texts.T: {key} has two English templates:\n  {UNITS[key]!r}\n  {en!r}")
    UNITS[key] = en
    if values:
        FIELDS[key] = fields(en)
    return Text(key, en, tuple(sorted(values.items())))


@dataclass(frozen=True)
class Join:
    """Parts rendered and joined with sep; an empty or None part is dropped first (no stray space when a layer has no
    OpenStreetMap line), then `fix` = (old, new) is replaced in the whole (".." → "." where a source ends in a stop)."""
    parts: tuple
    sep: str = " "
    fix: tuple[str, str] | None = None


def h(en: str) -> str:
    return hashlib.sha256(en.encode("utf-8")).hexdigest()[:12]


def fields(s: str) -> frozenset[str]:
    """The named placeholders of a template ({ndvi}, {city}); ValueError on a stray brace."""
    return frozenset(f for _, f, _, _ in string.Formatter().parse(s) if f is not None)


def available() -> list[str]:
    """The languages whose data texts exist (scripts/site/i18n/<loc>.json): only these are generated."""
    return [loc for loc in LOCS if (I18N / f"{loc}.json").exists()]


class Catalog:
    @staticmethod
    def path(loc: str) -> Path:
        return I18N / f"{loc}.json"

    @staticmethod
    def load(loc: str) -> dict[str, dict]:
        """{key: {"en": hash of the English it translates, "text": the translation, "same"?: true}}; {} without a file."""
        p = Catalog.path(loc)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def stale(key: str, en: str, cat: dict) -> bool:
    """Whether a language lacks the translation of this English: no entry, or one made from another English."""
    e = cat.get(key)
    return not e or e.get("en") != h(en) or not isinstance(e.get("text"), str)


SPAN = re.compile(r"\{[^{}]*\}")


def placeholders_match(text: str, en: str) -> bool:
    """The translation carries exactly the English's braces — every span `{…}` as many times, with the same format spec
    and conversion (`{thr:>12}` or `{thr!r}` is not `{thr}`) — and, where the English is a format string, is one too."""
    if sorted(SPAN.findall(text)) != sorted(SPAN.findall(en)):
        return False
    try:
        fields(en)
    except ValueError:          # an English with a stray brace (a model's quote) is never formatted
        return True
    try:
        fields(text)
    except ValueError:
        return False
    return True


def entry_problem(en: str, text: object, loc: str, same: bool = False) -> str | None:
    """Why a translation of `en` cannot stand, or None: not a string, empty, the English itself without `"same": true`,
    other placeholders, or other literal numbers than the English (the translator never types a number: L5). A text kept
    as the English itself is read in the English notation. `same` is the entry's mark that the text rightly stays
    English (a product name, NDVI): without it a draft that hands the English back would ship English on a Dutch or
    French page (final review M2). A text with no letters outside its placeholders (`{n}`) is the same in every language."""
    if not isinstance(text, str):
        return "not a string"
    if en and not text.strip():
        return "empty"
    if text == en and not same and any(c.isalpha() for c in SPAN.sub("", en)):
        return 'the English itself; mark the entry "same": true if it rightly stays English'
    if not placeholders_match(text, en):
        return f"placeholders differ from the English {sorted(SPAN.findall(en))}"
    if nums(text, "en" if text == en else loc) != nums(en, "en"):
        return f"numbers differ from the English {nums(en, 'en')}: {nums(text, loc)}"
    return None


CHECK = "python -m scripts.site.i18n_sync check lists every key"


def _text(t: Text, loc: str, cat: dict | None) -> str:
    if loc == "en":
        tmpl = t.en
    else:
        cat = cat or {}
        if stale(t.key, t.en, cat):
            raise Missing(f"{loc}: {t.key}: no translation of the current English — {CHECK}; "
                          f"python -m scripts.site.i18n_sync todo --loc {loc} gives them to translate")
        tmpl = cat[t.key]["text"]
        why = entry_problem(t.en, tmpl, loc, bool(cat[t.key].get("same")))
        if why:
            raise Missing(f"{loc}: {t.key}: {why} — {CHECK}")
    if not t.values:            # not formatted: braces in a model's quoted words stay as they are
        return tmpl
    return tmpl.format_map({k: render(v, loc, cat) for k, v in t.values})


def render(obj, loc: str, cat: dict | None = None):
    """The document with every Text, Join, Num, Place and Munty turned into a string of the language."""
    if isinstance(obj, Text):
        return _text(obj, loc, cat)
    if isinstance(obj, Join):
        parts = [render(p, loc, cat) for p in obj.parts]
        s = obj.sep.join(p for p in parts if p)
        return s.replace(*obj.fix) if obj.fix else s
    if isinstance(obj, (Num, Place, Munty)):
        return obj.render(loc)
    if isinstance(obj, dict):
        return {k: render(v, loc, cat) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [render(v, loc, cat) for v in obj]
    return obj


# ── the glossary's checked terms (site/web/i18n/glossary.md, the table under "## Terms") ─────────────
# The same parse as site/web/tests/glossary.ts parseTerms: a row whose first three cells are `code` is a check, each cell
# a regular expression matched without regard to case; inside a cell "\|" is the alternation and a bare "|" ends the
# cell. A row of plain cells is guidance only; a row half in code is a mistake in the glossary.
GLOSSARY = ROOT / "site/web/i18n/glossary.md"
_CODE = re.compile(r"^`(.+)`$")


def _cells(row: str) -> list[str]:
    row = re.sub(r"^\||\|$", "", row.strip())
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row)]


def glossary_terms(md: str | None = None) -> list[dict[str, re.Pattern]]:
    """[{"en": re, "nl": re, "fr": re}] of the glossary's checked terms, compiled with re.IGNORECASE."""
    md = GLOSSARY.read_text(encoding="utf-8") if md is None else md
    m = re.search(r"^## Terms\s*$", md, re.M)
    if not m:
        raise SystemExit('glossary: no "## Terms" section')
    rest = md[m.start():].split("\n")[1:]
    end = next((i for i, l in enumerate(rest) if l.startswith("## ")), len(rest))
    out = []
    for line in rest[:end]:
        if not line.startswith("|") or re.fullmatch(r"\|[\s|:-]+\|", line):
            continue
        c = _cells(line)
        coded = [(_CODE.match(x) or [None, None])[1] for x in c[:3]]
        if all(x is None for x in coded):
            continue
        if any(x is None for x in coded) or len(c) != 5:
            raise SystemExit(f"glossary: a row half in code, or not five cells: {line}")
        out.append({loc: re.compile(x, re.IGNORECASE) for loc, x in zip(("en", "nl", "fr"), coded)})
    return out


# ── the literal numbers of a text, in one notation (plan 5, ruling P29) ─────────────────────────────
# The same rule as site/web/scripts/numbers.mjs numbersOf: group marks (en ",", nl ".", fr U+202F or U+00A0) are removed
# only between a digit and exactly three digits not followed by a digit; then the decimal sign (en ".", nl/fr ",") is
# the point, and any other "." or "," between digits splits the number. Placeholders and quoted spans are dropped first:
# a quote keeps the original's notation by rule (L6: register 60 quotes the French "3.200 m2").
QUOTED = re.compile(r"«[^»]*»|“[^”]*”|„[^“”]*[“”]|‘[^’]*’|\"[^\"]*\"")
GROUP = {"en": ",", "nl": ".", "fr": "  "}


def nums(s: str, lang: str) -> list[str]:
    s = QUOTED.sub(" ", re.sub(r"\{[^{}]*\}", " ", s))
    s = re.sub(rf"(?<=\d)[{re.escape(GROUP[lang])}](?=\d{{3}}(?!\d))", "", s)
    if lang != "en":
        s = s.replace(".", " ").replace(",", ".")
    return sorted(re.findall(r"\d+(?:\.\d+)?", s))
