#!/usr/bin/env python3
"""
A second reading of the register's test contracts (phase 2b, docs/07-unified-frondia.md).

The register's error rate needs labels that do not come from the reader being checked. With no person at
hand who reads French planning texts, the 30 test contracts (and the ten development ones) are read again
by a second model, Claude Opus 5.5, with its own prompt and its own task: one label per contract, the
quote that decides it and a reason, from the contract's own words only (the text before its budget table,
as a person would have been shown). It runs in a fresh process from an empty folder with tools,
connectors and session history off, so it never sees the first reader's answers.

This is weaker than a person's check: two models of one family can err alike, so their agreement
overstates accuracy. The labels are written as the second reader's, never as a person's, and the page
says so. A person's labels (the labelling page, `eval_greening.py --import`) replace them.

    .venv/bin/python scripts/registry/check_greening_llm.py
    .venv/bin/python scripts/registry/eval_greening.py
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_greening_llm import ROOT, ask, sha, verbatim  # noqa: E402

RAW = ROOT / "data/registry/contracts_raw.json"
TESTSET = ROOT / "data/registry/greening_testset.json"
PROMPT = ROOT / "scripts/registry/prompts/greening_check_v1.md"
SCHEMA = ROOT / "scripts/registry/prompts/greening_check_v1.schema.json"
VERSION = "greening_check_v1"
CACHE = ROOT / "data/registry/llm" / VERSION
GOLD = ROOT / "data/registry/greening_gold_test.json"
MODEL = "claude-opus-5-5"


def own_words(text: str) -> str:
    """The contract's own text: before its budget table and the site's navigation."""
    i = text.find(" Budgets ")
    return (text[:i] if i >= 0 else text).strip()


def read_one(c: dict, prompt: str, schema: str, cwd: str) -> dict:
    text = own_words(c["description"])
    key = {"prompt_sha": sha(prompt), "schema_sha": sha(schema), "text_sha": sha(text)}
    path = CACHE / f"{c['id']}.json"
    if path.exists():
        cached = json.loads(path.read_text())
        if all(cached.get(k) == v for k, v in key.items()):
            return cached
    got = ask(text, prompt, schema, cwd, model=MODEL)
    rec = {"id": c["id"], "version": VERSION, **key, "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **got}
    q = rec["output"]["quote"]
    rec["output"]["quote_verbatim"] = (not q) or verbatim(q, text)
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    return rec


def main() -> int:
    raw = {c["id"]: c for c in json.loads(RAW.read_text())}
    ts = json.loads(TESTSET.read_text())
    ids = ts["test"] + ts["development"]
    prompt, schema = PROMPT.read_text(), json.dumps(json.loads(SCHEMA.read_text()))
    CACHE.mkdir(parents=True, exist_ok=True)
    cwd = tempfile.mkdtemp(prefix="frondia-check-")   # an empty folder: no project file enters the context
    recs, failed = {}, []
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        futs = {pool.submit(read_one, raw[i], prompt, schema, cwd): i for i in ids}
        for f in cf.as_completed(futs):
            i = futs[f]
            try:
                recs[i] = f.result()
                print(f"  {i:>3} read", flush=True)            # no label printed: the run is watched blind
            except Exception as e:
                failed.append(i)
                print(f"  {i:>3} FAILED {e}", flush=True)
    if failed:
        print(f"failed: {failed}")
        return 1
    runs = sorted(r["run_at"] for r in recs.values())
    entry = lambda i: {"label": recs[i]["output"]["label"], "note": recs[i]["output"]["why"],
                       "quote": recs[i]["output"]["quote"], "quote_verbatim": recs[i]["output"]["quote_verbatim"],
                       "at": recs[i]["run_at"]}
    GOLD.write_text(json.dumps({
        "kind": "model",
        "labelled_by": "Claude Opus 5.5",
        "how": ("a second model with its own prompt (greening_check_v1: one label, the deciding quote and a reason), "
                "in a fresh process with tools, connectors and project files off, shown each contract's own text; "
                "it never saw the first reader's answers"),
        "model": sorted({recs[i]["model"] for i in recs}), "prompt_sha": sha(prompt), "schema_sha": sha(schema),
        "labelled_from": runs[0][:10], "labelled_to": runs[-1][:10],
        "test": {str(i): entry(i) for i in sorted(ts["test"])},
        "development": {str(i): entry(i) for i in sorted(ts["development"])},
    }, ensure_ascii=False, indent=1))
    bad = [i for i in recs if not recs[i]["output"]["quote_verbatim"]]
    print(f"→ {GOLD.relative_to(ROOT)}: {len(ts['test'])} test + {len(ts['development'])} development contracts; "
          f"quotes not found word for word: {bad or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
