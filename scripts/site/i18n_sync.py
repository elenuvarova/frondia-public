"""Keeps the data texts' translations (scripts/site/i18n/<loc>.json) in step with the English templates (plan 5, L5).

    python -m scripts.site.i18n_sync todo --loc nl              # {key: English} of what nl lacks or has out of date
    python -m scripts.site.i18n_sync apply --loc nl draft.json  # writes {key: text} with the current English's hash
    python -m scripts.site.i18n_sync check                      # exit 1 if a language is incomplete

Only what changed is touched: a translation stays as long as the English it was made from (its hash) does. `apply` keeps
every other entry, refuses a key the documents do not have, drops entries of keys that are gone (and says which), and
keeps a "same": true (a text that rightly stays English) only while the text still equals the English, and refuses a
text equal to the English that neither the draft nor the file marks "same": true. `check` covers every language with
a file — a file means the pipeline generates that language, so it must be complete — and a language the site publishes
(site/web/i18n/locales.ts) must have its file. A preview language without one passes: the site reads the English data
texts until it is translated.

The units are collected by building the documents (downloads.build_index, register.build) without writing a file.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.site import texts  # noqa: E402
from scripts.site.texts import h, stale  # noqa: E402

LOCALES_TS = ROOT / "site/web/i18n/locales.ts"


def collect() -> dict[str, str]:
    from scripts.site import downloads, register
    downloads.build_index()
    register.build()
    return dict(texts.UNITS)


def published() -> list[str]:
    """The data languages the site publishes: `published: true` in the registry of languages (lib i18n/locales.ts)."""
    src = LOCALES_TS.read_text(encoding="utf-8")
    return [loc for loc in texts.LOCS
            if re.search(rf"\{{\s*code:\s*'{loc}'[^}}]*?\bpublished:\s*true\b", src)]


_published = published


def todo(loc: str, units: dict[str, str]) -> dict[str, dict[str, str]]:
    """{key: {"en": English, "h": its hash}} of what the language lacks or has out of date; a draft may hand the hash
    back with its text, so a draft made from an older English is refused."""
    cat = texts.Catalog.load(loc)
    return {k: {"en": en, "h": h(en)} for k, en in sorted(units.items()) if stale(k, en, cat)}


def invalid(loc: str, units: dict[str, str]) -> list[str]:
    """Entries of the language's file, current by their hash, that cannot stand (texts.entry_problem): a hand-edited
    catalogue is held to the same rules as `apply`."""
    cat = texts.Catalog.load(loc)
    out = []
    for k, en in sorted(units.items()):
        if k in cat and not stale(k, en, cat) and (why := texts.entry_problem(en, cat[k]["text"], loc, bool(cat[k].get("same")))):
            out.append(f"{k}: {why}")
    return out


def _save(loc: str, cat: dict) -> None:
    p = texts.Catalog.path(loc)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(sorted(cat.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def apply(loc: str, draft: dict, units: dict[str, str]) -> list[str]:
    """Writes the draft's translations into the language's file; returns the keys dropped because they are gone. A draft
    entry is the text, or {"text": …, "h": the hash `todo` gave, "same": true when the text rightly stays English}.
    Nothing is written if any entry is refused: a key the documents do not have, a hash of another English, an empty
    text, the English itself unmarked (neither the draft nor the file says "same": true), other placeholders or other
    numbers."""
    unknown = sorted(k for k in draft if k not in units)
    if unknown:
        raise SystemExit(f"{loc}: not a data text (no such key in the documents): {', '.join(unknown)}")
    cat = texts.Catalog.load(loc)
    texts_ = {}
    same = set()
    bad = []
    for k, v in draft.items():
        marked = bool(cat.get(k, {}).get("same"))
        if isinstance(v, dict):
            if "h" in v and v["h"] != h(units[k]):
                bad.append(f"{k}: made from another English (hash {v['h']}, now {h(units[k])})")
                continue
            marked = marked or v.get("same") is True
            v = v.get("text")
        why = texts.entry_problem(units[k], v, loc, marked)
        if why:
            bad.append(f"{k}: {why}")
        texts_[k] = v
        if marked:
            same.add(k)
    if bad:
        raise SystemExit(f"{loc}: refused, nothing written —\n  " + "\n  ".join(sorted(bad)))
    draft = texts_
    for k, text in draft.items():
        e = {"en": h(units[k]), "text": text}
        if k in same and text == units[k]:
            e["same"] = True
        cat[k] = e
    removed = sorted(k for k in cat if k not in units)
    for k in removed:
        del cat[k]
    _save(loc, cat)
    return removed


def problems(units: dict[str, str], published: list[str] | None = None) -> list[str]:
    out = []
    for loc in sorted(set(texts.available()) | set(published if published is not None else _published())):
        if not texts.Catalog.path(loc).exists():
            out.append(f"{loc}: published on the site, but scripts/site/i18n/{loc}.json does not exist")
            continue
        missing = list(todo(loc, units))
        if missing:
            out.append(f"{loc}: {len(missing)} data texts missing or out of date — python -m scripts.site.i18n_sync todo --loc {loc}: "
                       + ", ".join(missing[:20]) + (" …" if len(missing) > 20 else ""))
        out += [f"{loc}: {x}" for x in invalid(loc, units)]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m scripts.site.i18n_sync")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("todo")
    t.add_argument("--loc", required=True, choices=texts.LOCS)
    a = sub.add_parser("apply")
    a.add_argument("--loc", required=True, choices=texts.LOCS)
    a.add_argument("draft", type=Path)
    sub.add_parser("check")
    args = ap.parse_args(argv)
    units = collect()
    if args.cmd == "todo":
        print(json.dumps(todo(args.loc, units), ensure_ascii=False, indent=1))
        return 0
    if args.cmd == "apply":
        removed = apply(args.loc, json.loads(args.draft.read_text(encoding="utf-8")), units)
        for k in removed:
            print(f"removed {k} (no longer a data text)")
        left = len(todo(args.loc, units))
        print(f"{args.loc}: {left} data texts still to translate")
        return 0
    found = problems(units)
    for p in found:
        print(p, file=sys.stderr)
    if not found:
        print(f"data texts complete for: {', '.join(texts.available()) or 'no language yet'}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
