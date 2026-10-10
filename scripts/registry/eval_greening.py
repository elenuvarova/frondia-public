#!/usr/bin/env python3
"""
How often the register's reader is wrong (phase 2b, docs/07-unified-frondia.md).

Two readers of the same contract descriptions are compared with reference labels given without seeing
either reader's answer, by a person when one can be found, otherwise by a second model
(`check_greening_llm.py`: Claude Opus 5.5, its own prompt, a fresh process). The file says which, and the
page words the check accordingly:

  * the language model (`extract_greening_llm.py`: one frozen prompt, version greening_v1);
  * the rule baseline (`extract_greening.py`: a greening term and a French marker of the future in
    one sentence).

The labels cover 30 contracts drawn by seed before any label was given and before the model was run on
them (`data/registry/greening_testset.json`); the draw is repeated here and must match the file. The
ten contracts the prompt was written against are the development set: their numbers are shown and
never published as an error rate. Thirty contracts give wide intervals, so every rate carries its
Wilson 95 % interval.

A person's labels come from the labelling page's database, saved as one JSON file per contract
(`ArtifactData list … out_dir`), and replace the second model's in `data/registry/greening_gold_test.json`:

    .venv/bin/python scripts/registry/eval_greening.py --import <dir with labels/c<ID>.json>
    .venv/bin/python scripts/registry/eval_greening.py              # writes data/registry/greening_eval.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/registry/contracts_raw.json"
TESTSET = ROOT / "data/registry/greening_testset.json"
LLM = ROOT / "data/registry/greening_llm.json"
BASELINE = ROOT / "data/registry/greening_baseline.json"
DEV_GOLD = ROOT / "data/registry/greening_gold.json"
GOLD = ROOT / "data/registry/greening_gold_test.json"
OUT = ROOT / "data/registry/greening_eval.json"
LABELS = ("yes", "weak", "no")


def prose(text: str) -> str:
    """The contract's own words: the page text before its budget table and the site's navigation."""
    i = text.find(" Budgets ")
    return text[:i] if i >= 0 else text


def draw(raw: list[dict], seed: str, development: list[int], n: int = 30, min_chars: int = 600) -> tuple[list[int], int]:
    """The test set: contracts with enough prose to judge, the development set left out, the first n by
    sha256(seed:id). Returns the sorted ids and the size of the pool they were drawn from."""
    pool = [c["id"] for c in raw if len(prose(c["description"])) >= min_chars and c["id"] not in set(development)]
    order = sorted(pool, key=lambda i: hashlib.sha256(f"{seed}:{i}".encode()).hexdigest())
    return sorted(order[:n]), len(pool)


def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 3), round(min(1.0, c + h), 3)]


def rate(k: int, n: int) -> dict:
    return {"k": k, "n": n, "value": round(k / n, 3) if n else None, "ci95": wilson(k, n)}


def binary(gold: dict[int, str], pred: dict[int, str], positive: set[str]) -> dict:
    """Precision and recall of `positive` (a set of labels read as one class) over the labelled ids."""
    ids = sorted(gold)
    tp = sum(1 for i in ids if gold[i] in positive and pred[i] in positive)
    fp = sum(1 for i in ids if gold[i] not in positive and pred[i] in positive)
    fn = sum(1 for i in ids if gold[i] in positive and pred[i] not in positive)
    wrong = sum(1 for i in ids if (gold[i] in positive) != (pred[i] in positive))
    return {"precision": rate(tp, tp + fp), "recall": rate(tp, tp + fn), "error": rate(wrong, len(ids)),
            "tp": tp, "fp": fp, "fn": fn}


def kappa(gold: dict[int, str], pred: dict[int, str]) -> float | None:
    ids = sorted(gold)
    n = len(ids)
    if not n:
        return None
    po = sum(1 for i in ids if gold[i] == pred[i]) / n
    g, p = Counter(gold[i] for i in ids), Counter(pred[i] for i in ids)
    pe = sum(g[k] * p[k] for k in LABELS) / (n * n)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else None


def confusion(gold: dict[int, str], pred: dict[int, str]) -> dict:
    """gold label -> predicted label -> count."""
    return {g: {p: sum(1 for i in gold if gold[i] == g and pred[i] == p) for p in LABELS} for g in LABELS}


def rule_labels(baseline: list[dict]) -> dict[int, str]:
    """The rule knows two answers: a measure was found (yes) or not (no)."""
    return {b["id"]: "yes" if b["has_greening_measure"] else "no" for b in baseline}


def import_labels(src: Path, testset: dict) -> dict:
    """The labelling page's documents (one per contract, `labels/c<ID>.json`) -> the gold file."""
    docs = {}
    for p in sorted((src / "labels").glob("c*.json")) or sorted(src.glob("c*.json")):
        d = json.loads(p.read_text())
        d = d.get("data", d) if isinstance(d, dict) else {}
        if isinstance(d.get("id"), int) and d.get("label") in LABELS:
            docs[d["id"]] = {"label": d["label"], "note": (d.get("note") or "").strip(), "at": d.get("at")}
    test, dev = set(testset["test"]), set(testset["development"])
    missing = sorted(test - set(docs))
    if missing:
        raise SystemExit(f"the test set is not fully labelled yet: {len(missing)} missing ({missing})")
    stamps = sorted(v["at"] for v in docs.values() if v.get("at"))
    return {
        "kind": "person",
        "labelled_by": "Elena Uvarova",
        "how": ("blind, on a labelling page that showed each contract's own text (before its budget table) "
                "and hid every machine answer; guidelines as in the prompt: yes = a committed measure that "
                "changes vegetation cover, weak = greening only as an aim, a need or access, no = no measure"),
        "labelled_from": stamps[0][:10] if stamps else None,
        "labelled_to": stamps[-1][:10] if stamps else None,
        "test": {str(i): docs[i] for i in sorted(test)},
        "development": {str(i): docs[i] for i in sorted(dev & set(docs))},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--import", dest="src", type=Path, help="folder saved from the labelling page's database")
    args = ap.parse_args()

    raw = json.loads(RAW.read_text())
    names = {c["id"]: c["name"] for c in raw}
    ts = json.loads(TESTSET.read_text())
    test, pool = draw(raw, ts["seed"], ts["development"])
    if test != ts["test"] or pool != ts["pool"]:
        raise SystemExit("the seeded draw no longer gives the fixed test set: the set or the contracts changed")

    if args.src:
        GOLD.write_text(json.dumps(import_labels(args.src, ts), ensure_ascii=False, indent=1))
        print(f"→ {GOLD.relative_to(ROOT)}")

    llm = json.loads(LLM.read_text())
    model = {r["id"]: r["label"] for r in llm["contracts"]}
    why = {r["id"]: r["why"] for r in llm["contracts"]}
    rule = rule_labels(json.loads(BASELINE.read_text()))
    quotes = [m for r in llm["contracts"] for m in r["measures"]]

    dev_gold = {int(k): v["label"] for k, v in json.loads(DEV_GOLD.read_text())["verdicts"].items()}
    out = {
        "register": {"version": llm["version"], "model": llm["model"], "prompt_sha": llm["prompt_sha"],
                     "schema_sha": llm["schema_sha"], "contracts": len(llm["contracts"]),
                     "labels": dict(Counter(model.values()))},
        "quotes_word_for_word": rate(sum(1 for m in quotes if m["verbatim"]), len(quotes)),
        "testset": {"seed": ts["seed"], "rule": ts["rule"], "pool": ts["pool"], "ids": ts["test"]},
        "development": {
            "note": ("the prompt was written against these ten contracts, labelled by Claude on 1 September; "
                     "their agreement is not an error rate"),
            "model_vs_claude": {"agree": rate(sum(1 for i in dev_gold if model[i] == dev_gold[i]), len(dev_gold)),
                                "confusion": confusion(dev_gold, model)},
            "rule_vs_claude": {"yes": binary(dev_gold, rule, {"yes"})},
        },
    }

    if not GOLD.exists():
        OUT.write_text(json.dumps({**out, "test": None}, ensure_ascii=False, indent=1))
        print(f"→ {OUT.relative_to(ROOT)}: development set only; the test labels are not in yet")
        return 0

    g = json.loads(GOLD.read_text())
    gold = {int(k): v["label"] for k, v in g["test"].items()}
    note = {int(k): v.get("note", "") for k, v in g["test"].items()}
    if sorted(gold) != ts["test"]:
        raise SystemExit("the gold file does not cover exactly the fixed test set")

    miss = [{"id": i, "name": names[i], "gold": gold[i], "model": model[i], "rule": rule[i],
             "note": note[i], "model_why": why[i]} for i in sorted(gold) if model[i] != gold[i]]
    out["test"] = {
        "kind": g.get("kind", "person"),
        "labelled_by": g["labelled_by"], "how": g["how"], "labelled_from": g["labelled_from"],
        "labelled_to": g["labelled_to"], "n": len(gold), "gold": dict(Counter(gold.values())),
        "model": {
            "error": rate(len(miss), len(gold)),                 # any disagreement over three labels
            "kappa": kappa(gold, {i: model[i] for i in gold}),
            "yes": binary(gold, model, {"yes"}),                 # a committed measure
            "any": binary(gold, model, {"yes", "weak"}),         # any greening, committed or not
            "confusion": confusion(gold, model),
        },
        "rule": {"yes": binary(gold, rule, {"yes"}), "any": binary(gold, rule, {"yes", "weak"})},
        "disagreements": miss,
    }
    if g.get("development"):
        dev_elena = {int(k): v["label"] for k, v in g["development"].items()}
        out["development"]["elena_vs_claude"] = rate(sum(1 for i in dev_elena if dev_elena[i] == dev_gold[i]), len(dev_elena))
        out["development"]["model_vs_elena"] = rate(sum(1 for i in dev_elena if model[i] == dev_elena[i]), len(dev_elena))
    out["evaluated_on"] = date.today().isoformat()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))

    t = out["test"]
    f = lambda r: f"{r['k']}/{r['n']} = {r['value']:.0%} (95 % {r['ci95'][0]:.0%}–{r['ci95'][1]:.0%})" if r["n"] else "—"
    print(f"→ {OUT.relative_to(ROOT)}: {t['n']} contracts, labels {t['gold']}")
    print(f"  model: wrong {f(t['model']['error'])}, kappa {t['model']['kappa']}")
    print(f"         'yes' precision {f(t['model']['yes']['precision'])}, recall {f(t['model']['yes']['recall'])}")
    print(f"  rule:  'yes' precision {f(t['rule']['yes']['precision'])}, recall {f(t['rule']['yes']['recall'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
