"""The register of interventions read by a language model (phase 2b, docs/07-unified-frondia.md).

Guards what makes the reading checkable: every quote is found word for word in its contract, the
register is one version of one frozen prompt and its labels follow the prompt's own rule, the test set
is the seeded draw fixed before any label, and the evaluation's arithmetic gives known answers.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "registry"))

import eval_greening as ev  # noqa: E402
from extract_greening_llm import CACHE, PROMPT, SCHEMA, sha, verbatim  # noqa: E402

RAW = {c["id"]: c for c in json.loads(ev.RAW.read_text())}
REG = json.loads(ev.LLM.read_text())
TESTSET = json.loads(ev.TESTSET.read_text())


def test_every_contract_is_read_and_every_quote_is_in_it_word_for_word():
    assert sorted(r["id"] for r in REG["contracts"]) == sorted(RAW)
    for r in REG["contracts"]:
        for m in r["measures"]:
            assert verbatim(m["quote"], RAW[r["id"]]["description"]), (r["id"], m["quote"][:60])
            assert m["verbatim"] is True, r["id"]


def test_the_register_is_one_version_of_the_frozen_prompt():
    prompt, schema = PROMPT.read_text(), json.dumps(json.loads(SCHEMA.read_text()))
    assert (REG["prompt_sha"], REG["schema_sha"]) == (sha(prompt), sha(schema))
    cached = sorted(CACHE.glob("*.json"))
    assert len(cached) == len(RAW)
    for p in cached:
        rec = json.loads(p.read_text())
        assert (rec["prompt_sha"], rec["schema_sha"]) == (REG["prompt_sha"], REG["schema_sha"]), p.name
        assert rec["text_sha"] == sha(RAW[rec["id"]]["description"]), p.name


def test_labels_follow_the_prompts_own_rule():
    # "yes" needs a committed measure, "weak" only aims or access, "no" only states (or nothing)
    for r in REG["contracts"]:
        st = {m["status"] for m in r["measures"]}
        expect = "yes" if "action" in st else "weak" if "intention" in st else "no"
        assert r["label"] == expect, r["id"]


def test_the_test_set_is_the_seeded_draw():
    test, pool = ev.draw(list(RAW.values()), TESTSET["seed"], TESTSET["development"])
    assert (test, pool) == (TESTSET["test"], TESTSET["pool"])
    assert len(test) == 30 and not set(test) & set(TESTSET["development"])


def test_wilson_interval_known_answers():
    assert ev.wilson(3, 9) == [0.121, 0.646]
    assert ev.wilson(0, 10) == [0.0, 0.278]
    assert ev.wilson(0, 0) is None


def test_binary_and_kappa_known_answers():
    gold = {1: "yes", 2: "weak", 3: "no", 4: "yes"}
    pred = {1: "yes", 2: "yes", 3: "no", 4: "no"}
    b = ev.binary(gold, pred, {"yes"})
    assert (b["tp"], b["fp"], b["fn"]) == (1, 1, 1)
    assert b["precision"]["value"] == 0.5 and b["recall"]["value"] == 0.5 and b["error"]["k"] == 2
    a = ev.binary(gold, pred, {"yes", "weak"})
    assert (a["tp"], a["fp"], a["fn"]) == (2, 0, 1)
    assert ev.kappa({1: "yes", 2: "yes", 3: "no", 4: "no"}, {1: "yes", 2: "no", 3: "no", 4: "no"}) == 0.5


def test_the_rule_baseline_reproduces_its_published_numbers():
    # 33 % precision at 100 % recall on the ten development contracts (CLAUDE.md, 1 September)
    dev = {int(k): v["label"] for k, v in json.loads(ev.DEV_GOLD.read_text())["verdicts"].items()}
    b = ev.binary(dev, ev.rule_labels(json.loads(ev.BASELINE.read_text())), {"yes"})
    assert (b["precision"]["k"], b["precision"]["n"], b["recall"]["k"], b["recall"]["n"]) == (3, 9, 3, 3)


def test_labels_import_refuses_an_unfinished_set(tmp_path):
    (tmp_path / "labels").mkdir()
    for i in TESTSET["test"][:-1]:
        (tmp_path / "labels" / f"c{i}.json").write_text(json.dumps({"id": i, "label": "no", "note": ""}))
    with pytest.raises(SystemExit, match="1 missing"):
        ev.import_labels(tmp_path, TESTSET)
    last = TESTSET["test"][-1]
    (tmp_path / "labels" / f"c{last}.json").write_text(json.dumps({"id": last, "label": "yes", "note": " x "}))
    g = ev.import_labels(tmp_path, TESTSET)
    assert len(g["test"]) == 30 and g["test"][str(last)] == {"label": "yes", "note": "x", "at": None}


def test_the_published_evaluation_recomputes_from_the_labels():
    out = json.loads(ev.OUT.read_text())
    assert out["register"]["prompt_sha"] == REG["prompt_sha"]
    if out.get("test") is None:
        pytest.skip("the test labels are not in yet")
    gold = {int(k): v["label"] for k, v in json.loads(ev.GOLD.read_text())["test"].items()}
    model = {r["id"]: r["label"] for r in REG["contracts"]}
    assert sorted(gold) == TESTSET["test"]
    wrong = sum(1 for i in gold if gold[i] != model[i])
    assert out["test"]["model"]["error"]["k"] == wrong == len(out["test"]["disagreements"])


def test_the_site_register_carries_every_measure_and_says_which_pages_are_empty():
    import csv
    site = json.loads((ROOT / "site/public/data/register.json").read_text())
    assert len(site["contracts"]) == len(RAW) and site["counts"]["undescribed"] == 41
    assert sum(site["counts"][k] for k in ("yes", "weak", "no", "undescribed")) == len(RAW)
    rows = 0
    for c in site["contracts"]:
        assert c["commune"], c["id"]
        assert c["test"] == (c["id"] in TESTSET["test"])
        if not c["described"]:   # nothing to read: the model had nothing to quote
            assert c["label"] == "no" and not c["measures"], c["id"]
        flat = {(m["q"], m["status"], m["kind"]) for m in c["measures"]}
        shown = {(g["q"], g["status"], k) for g in c["shown"] for k in g["kinds"]}
        assert flat == shown, c["id"]
        rows += max(1, len(c["measures"]))
    with (ROOT / "site/public/downloads/brussels/register.csv").open(encoding="utf-8") as f:
        assert sum(1 for _ in csv.DictReader(f)) == rows
    if site["eval"]:   # the page shows the hand labels and nothing of the labeller's notes
        assert all("note" not in d for d in site["eval"]["disagreements"])
        assert sum(1 for c in site["contracts"] if c["gold"]) == site["eval"]["n"]


def test_the_second_reading_is_one_frozen_prompt_and_quotes_its_contract():
    import check_greening_llm as ch
    gold = json.loads(ev.GOLD.read_text())
    if gold.get("kind") != "model":
        pytest.skip("the reference labels are a person's")
    prompt, schema = ch.PROMPT.read_text(), json.dumps(json.loads(ch.SCHEMA.read_text()))
    assert (gold["prompt_sha"], gold["schema_sha"]) == (sha(prompt), sha(schema))
    assert sorted(int(k) for k in gold["test"]) == TESTSET["test"]
    for part in ("test", "development"):
        for k, v in gold[part].items():
            rec = json.loads((ch.CACHE / f"{k}.json").read_text())
            assert rec["prompt_sha"] == gold["prompt_sha"] and rec["output"]["label"] == v["label"], k
            assert not v["quote"] or verbatim(v["quote"], ch.own_words(RAW[int(k)]["description"])), k
    site = json.loads((ROOT / "site/public/data/register.json").read_text())
    assert site["eval"]["kind"] == "model" and site["eval"]["labelled_by"] == "Claude Opus 5.5"
