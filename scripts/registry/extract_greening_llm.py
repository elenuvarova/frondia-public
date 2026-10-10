#!/usr/bin/env python3
"""
The register of interventions read by a language model (phase 2b, docs/07-unified-frondia.md).

The rule baseline (`extract_greening.py`) cannot tell a planned measure from a description of what
already exists: 6 of its 9 "greening" contracts in the gold set were diagnoses, place names or a word
inside another word. This script gives the same 98 contract descriptions to a language model with
one fixed prompt and one fixed output schema, and keeps what it reads only where it can be checked:

  * every measure carries a quote, and a quote counts only if it appears word for word in the
    contract's text (whitespace and apostrophes aside); an unmatched quote is kept, flagged, and
    never shown as the model's reading;
  * the model never counts, estimates or ranks: numbers stay with the engine;
  * the prompt, the schema and the model are fixed and hashed, and every answer is cached with them,
    so a run can be repeated, and a changed prompt shows as a new version rather than a silent edit.

The model runs through Claude Code in print mode on the author's own account (no API key in the
project): tools, MCP servers and session history off, run from an empty folder so no project file
enters its context.

    .venv/bin/python scripts/registry/extract_greening_llm.py            # cached answers are reused
    .venv/bin/python scripts/registry/extract_greening_llm.py --ids 87 89 --fresh
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/registry/contracts_raw.json"
PROMPT = ROOT / "scripts/registry/prompts/greening_v1.md"
SCHEMA = ROOT / "scripts/registry/prompts/greening_v1.schema.json"
VERSION = "greening_v1"
CACHE = ROOT / "data/registry/llm" / VERSION
OUT = ROOT / "data/registry/greening_llm.json"
MODEL = "claude-sonnet-5"


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def norm(s: str) -> str:
    """For matching a quote to its source: Unicode composed, one kind of apostrophe and quote mark,
    single spaces. Nothing else is forgiven."""
    s = unicodedata.normalize("NFC", s).replace("’", "'").replace("‘", "'")
    s = s.replace(" ", " ").replace("« ", "« ").replace(" »", " »")
    return re.sub(r"\s+", " ", s).strip()


def verbatim(quote: str, text: str) -> bool:
    q = norm(quote).rstrip(" .;,")
    return bool(q) and q in norm(text)


def ask(text: str, prompt: str, schema: str, cwd: str, model: str = MODEL) -> dict:
    cmd = ["claude", "-p", "--model", model, "--tools", "", "--strict-mcp-config", "--no-session-persistence",
           "--output-format", "json", "--json-schema", schema, "--system-prompt", prompt,
           f"Contract text:\n{text}"]
    for attempt in range(3):
        r = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
        try:
            d = json.loads(r.stdout)
        except json.JSONDecodeError:
            d = {}
        out = d.get("structured_output")
        if not d.get("is_error") and isinstance(out, dict):
            family = "-".join(model.split("-")[:2])          # "claude-sonnet", "claude-opus"
            used = [m for m in (d.get("modelUsage") or {}) if m.startswith(family) or m == model]
            return {"output": out, "model": used[0] if used else model, "cost_usd": d.get("total_cost_usd"),
                    "duration_ms": d.get("duration_ms")}
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"no structured answer after three tries: {r.stderr[-300:]}")


def read_one(c: dict, prompt: str, schema: str, cwd: str, fresh: bool) -> dict:
    text = c["description"]
    key = {"prompt_sha": sha(prompt), "schema_sha": sha(schema), "text_sha": sha(text)}
    path = CACHE / f"{c['id']}.json"
    if path.exists() and not fresh:
        cached = json.loads(path.read_text())
        if all(cached.get(k) == v for k, v in key.items()):
            return cached
    got = ask(text, prompt, schema, cwd)
    rec = {"id": c["id"], "version": VERSION, **key, "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           **got}
    for m in rec["output"]["measures"]:
        m["verbatim"] = verbatim(m["quote"], text)
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", type=int, nargs="*", help="only these contracts")
    ap.add_argument("--fresh", action="store_true", help="ask again even when a cached answer matches")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    contracts = json.loads(RAW.read_text())
    if args.ids:
        contracts = [c for c in contracts if c["id"] in set(args.ids)]
    prompt, schema = PROMPT.read_text(), json.dumps(json.loads(SCHEMA.read_text()))
    CACHE.mkdir(parents=True, exist_ok=True)
    cwd = tempfile.mkdtemp(prefix="frondia-llm-")   # an empty folder: no project instructions in the context

    done, failed = {}, []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {pool.submit(read_one, c, prompt, schema, cwd, args.fresh): c for c in contracts}
        for f in cf.as_completed(futs):
            c = futs[f]
            try:
                done[c["id"]] = f.result()
                print(f"  {c['id']:>3} {c['name'][:32]:<32} {done[c['id']]['output']['label']:<5} "
                      f"{len(done[c['id']]['output']['measures'])} measures", flush=True)
            except Exception as e:     # a contract that fails is reported, never guessed
                failed.append(c["id"])
                print(f"  {c['id']:>3} {c['name'][:32]:<32} FAILED {e}", flush=True)

    # the register as one file, from every cached answer of this version
    rows = []
    for c in json.loads(RAW.read_text()):
        p = CACHE / f"{c['id']}.json"
        if not p.exists():
            continue
        rec = json.loads(p.read_text())
        o = rec["output"]
        rows.append({"id": c["id"], "name": c["name"], "commune": c["commune"], "years": [c["year_start"], c["year_end"]],
                     "url": c["url"], "label": o["label"], "why": o["why"],
                     "measures": o["measures"], "quotes_verbatim": all(m["verbatim"] for m in o["measures"]),
                     "model": rec["model"], "run_at": rec["run_at"]})
    OUT.write_text(json.dumps({"version": VERSION, "model": MODEL, "prompt_sha": sha(prompt), "schema_sha": sha(schema),
                               "contracts": rows}, ensure_ascii=False, indent=1))
    n_q = sum(len(r["measures"]) for r in rows)
    n_bad = sum(1 for r in rows for m in r["measures"] if not m["verbatim"])
    print(f"→ {OUT.relative_to(ROOT)}: {len(rows)} contracts, {n_q} quotes, {n_bad} not found word for word"
          + (f"; failed {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
