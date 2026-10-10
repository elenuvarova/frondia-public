"""The register of interventions on the site (phase 2b, docs/07-unified-frondia.md).

Reads what `scripts/registry/extract_greening_llm.py` and `eval_greening.py` wrote and gives the page
`/register` one JSON, and the download a CSV with one row per quoted measure. Nothing is re-read or
re-judged here: labels, quotes and rates are copied, and the two HTML entities the scraped texts keep
(`&euro;`, `&copy;`) are decoded for display. A person's working notes stay in the repository (the page
shows the labels); a second model's reasons are published with its labels.

    .venv/bin/python -m scripts.site.register        # also run by site_data.py

The page's words — the labels, the model's reasons — are texts.Text (plan 5, L5): register.json is the English, and
register.<loc>.json the same document in Dutch or French for every language with data texts; a commune is named in the
language (texts.Munty). The quotes and the contracts' names stay as the source wrote them, and the CSV stays English (L6).
"""
from __future__ import annotations

import csv
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site" / "public"
REG = ROOT / "data/registry"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.site.texts import LOCS, Catalog, Munty, T, available, render  # noqa: E402
FETCHED = "2026-09-01"          # quartiers.brussels read by scripts/registry/fetch_contracts.py (CLAUDE.md)
KIND = {"new_green_space": "New green space", "park_redesign": "Park redesign", "restoration": "Restoration",
        "unsealing": "Unsealing", "street_greening": "Street greening",
        "gardens_agriculture": "Gardens and urban farming", "green_roofs_facades": "Green roofs and façades",
        "other_greening": "Other greening"}
# four pages of 2022–23 whose header the scraper did not parse; each description names its commune
COMMUNE = {94: "Bruxelles",               # "Le périmètre du CQD Versailles se situe à Neder-Over-Heembeek"
           95: "Berchem-Sainte-Agathe",   # "Ce contrat de quartier se situe sur le territoire de Berchem-Sainte-Agathe"
           96: "Ganshoren",               # "au nord-ouest de la commune … secteur statistique des « Villas de Ganshoren »"
           97: "Evere"}                   # "se situe au centre de la commune d'Evere"
STATUS = {"action": "Committed", "intention": "An aim", "state": "A description"}
LABEL = {"yes": "Commits to greening", "weak": "Greening only as an aim", "no": "No greening measure"}


def grouped(measures: list[dict]) -> list[dict]:
    """For the page: a quote the model gave twice (one clause, two kinds of measure: "la déminéralisation
    et verdurisation") is shown once with both kinds. The CSV keeps the model's measures as it gave them."""
    out: dict[tuple, dict] = {}
    for m in measures:
        k = (html.unescape(m["quote"]), m["status"])
        g = out.setdefault(k, {"q": k[0], "status": m["status"], "kinds": [], "places": []})
        if m["kind"] not in g["kinds"]:
            g["kinds"].append(m["kind"])
        p = html.unescape(m["place"]) if m["place"] else None
        if p and p not in g["places"]:
            g["places"].append(p)
    return list(out.values())


def described(text: str) -> bool:
    """Whether the page describes the contract at all: its own words come before the budget table and
    the photo credits ("© name - urban.brussels - year"). 41 pages, all of 1994–2006, carry only those."""
    i = text.find(" Budgets ")
    return bool(html.unescape(text[:i] if i >= 0 else text).split("©")[0].strip())


def _t(key: str, en: str | None):
    """A model's reason as a text to translate; an empty one stays as it is."""
    return T(key, en) if en else en


def build() -> dict:
    raw = {c["id"]: c for c in json.loads((REG / "contracts_raw.json").read_text())}
    llm = json.loads((REG / "greening_llm.json").read_text())
    ev = json.loads((REG / "greening_eval.json").read_text())
    ts = json.loads((REG / "greening_testset.json").read_text())
    gold_path = REG / "greening_gold_test.json"
    gold = ({int(k): v["label"] for k, v in json.loads(gold_path.read_text())["test"].items()}
            if gold_path.exists() else {})
    rule = {b["id"]: "yes" if b["has_greening_measure"] else "no"
            for b in json.loads((REG / "greening_baseline.json").read_text())}
    runs = sorted(r["run_at"] for r in llm["contracts"])

    contracts = []
    for r in llm["contracts"]:
        c = raw[r["id"]]
        contracts.append({
            "id": r["id"], "name": c["name"], "commune": Munty(c["commune"] or COMMUNE[r["id"]]), "years": [c["year_start"], c["year_end"]],
            "url": c["url"], "label": r["label"], "why": _t(f"register.why.{r['id']}", r["why"]), "rule": rule[r["id"]],
            "measures": [{"q": html.unescape(m["quote"]), "status": m["status"], "kind": m["kind"],
                          "place": html.unescape(m["place"]) if m["place"] else None} for m in r["measures"]],
            "shown": grouped(r["measures"]),
            "described": described(c["description"]), "test": r["id"] in ts["test"], "gold": gold.get(r["id"]),
        })
    contracts.sort(key=lambda x: (-x["years"][0], x["name"]))   # newest first

    test = ev.get("test")
    if test:
        model_ref = test.get("kind") == "model"
        # a second model's reason is published with it; a person's working notes stay in the repository
        test = {k: test[k] for k in ("kind", "labelled_by", "labelled_from", "labelled_to", "n", "gold", "model", "rule")} | {
            "disagreements": [{k: d[k] for k in ("id", "name", "gold", "model", "rule")}
                              | {"model_why": _t(f"register.model_why.{d['id']}", d["model_why"])}
                              | ({"check_why": _t(f"register.check_why.{d['id']}", d["note"])} if model_ref else {})
                              for d in test["disagreements"]]}
    return {
        "version": llm["version"], "model": llm["model"], "prompt_sha": llm["prompt_sha"], "schema_sha": llm["schema_sha"],
        "read_from": runs[0][:10], "read_to": runs[-1][:10], "fetched": FETCHED, "source": "quartiers.brussels",
        "counts": {**{k: sum(1 for c in contracts if c["described"] and c["label"] == k) for k in ("yes", "weak", "no")},
                   "undescribed": sum(1 for c in contracts if not c["described"])},
        "quotes": ev["quotes_word_for_word"],
        "testset": {"seed": ts["seed"], "pool": ts["pool"], "n": len(ts["test"]), "development": len(ts["development"])},
        "eval": test,
        "development": {"n": ev["development"]["model_vs_claude"]["agree"]["n"],
                        "rule_precision": ev["development"]["rule_vs_claude"]["yes"]["precision"],
                        "rule_recall": ev["development"]["rule_vs_claude"]["yes"]["recall"]},
        "labels": {g: {k: T(f"register.{g}.{k}", v) for k, v in m.items()}
                   for g, m in (("kind", KIND), ("status", STATUS), ("label", LABEL))},
        "contracts": contracts,
    }


def _json(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False, separators=(",", ":"))


def write() -> dict:
    doc = build()
    d = render(doc, "en")
    langs = {loc: render(doc, loc, Catalog.load(loc)) for loc in available()}   # a Missing stops the run before any write
    (SITE / "data").mkdir(parents=True, exist_ok=True)
    (SITE / "data" / "register.json").write_text(_json(d))
    for loc in LOCS:            # a language without data texts has no file: the site reads the English one in preview
        p = SITE / "data" / f"register.{loc}.json"
        if loc in langs:
            p.write_text(_json(langs[loc]))
        else:
            p.unlink(missing_ok=True)
    out = SITE / "downloads" / "brussels"
    out.mkdir(parents=True, exist_ok=True)
    cols = ["contract_id", "contract", "commune", "year_start", "year_end", "source_url", "described", "label", "rule_label",
            "checked_label", "measure", "quote", "status", "kind", "place", "model_reason"]
    with (out / "register.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for c in d["contracts"]:
            base = [c["id"], c["name"], c["commune"], c["years"][0], c["years"][1], c["url"], int(c["described"]),
                    c["label"], c["rule"],
                    c["gold"] or ""]
            for i, m in enumerate(c["measures"] or [None], 1):
                w.writerow(base + ([i, m["q"], m["status"], m["kind"], m["place"] or ""] if m else ["", "", "", "", ""])
                           + [c["why"]])
    ev = json.loads((REG / "greening_eval.json").read_text())
    if ev.get("test") and ev["test"].get("kind") != "model":   # a person's working notes stay in the repository
        for x in ev["test"]["disagreements"]:
            x.pop("note", None)
    (out / "register_check.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1))
    return d


if __name__ == "__main__":
    d = write()
    print(f"register.json  {len(d['contracts'])} contracts {d['counts']}, check "
          f"{'in' if d['eval'] else 'pending'}; downloads/brussels/register.csv, register_check.json")
