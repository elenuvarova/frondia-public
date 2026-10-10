"""
Known-answer тесты движка — без Earth Engine.

Гардрейл из CLAUDE.md: «known-answer тесты на каждый количественный шаг».
Каждый тест закрепляет число или поведение, которое было ПРОВЕРЕНО в ходе
работы и записано. Если тест падает — либо сломан код, либо изменились данные;
и то и другое надо заметить, а не узнать из отчёта.

Запуск:  .venv/bin/python -m pytest tests -q
"""
from __future__ import annotations

import collections
import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SECTOR_TABLE = ROOT / "data/sector_change_2017_2024.csv"


# ── калибровка и подбор: числа, которые нельзя потерять ──────────────────────

@pytest.fixture(scope="module")
def brussels_units():
    rows = list(csv.DictReader(SECTOR_TABLE.open()))
    return [{
        "id": r["id"],
        "ndvi_before": float(r["ndvi_before"]),
        "lst_before": float(r["lst_before"]),
        "ndvi_delta": float(r["d_ndvi_raw"]),
        "centroid": (float(r["lon"]), float(r["lat"])),
        "_saved_effect": float(r["ndvi_effect"]),
    } for r in rows]


def test_calibration_reproduces_brussels_threshold(brussels_units):
    from engine.calibrate import calibrate
    c = calibrate(brussels_units, "ndvi", "ndvi_before", "lst_before")
    assert c.n == 686
    assert abs(c.threshold - 0.0373) < 0.0005, c.threshold
    assert c.unbiased, f"среднее {c.mean:+.5f} при sd {c.sd:.5f}"


def test_match_all_reproduces_saved_effects(brussels_units):
    """Регрессия против placebo_band с ЧЕСТНЫМ допуском.

    Сохранённая таблица округлена до 4 знаков (шум ~5e-5), а у ~8 % секторов
    равноудалённые кандидаты в контроль ранжируются по порядку входа — таблица
    отсортирована по эффекту, порядок другой, 12-й контроль иногда другой.
    Это не ошибка логики: порог (тест выше) воспроизводится точно. Поэтому
    требуем ≥ 90 % совпадений в пределах округления и максимум < 0,005
    (≈ 1/8 порога) — а не «все точно», как хотелось бы.
    """
    from engine.controls import match_all
    scored = {r["id"]: r for r in match_all(brussels_units, "ndvi_before", "lst_before", ["ndvi_delta"])}
    diffs = [abs(scored[u["id"]]["ndvi_delta_eff"] - u["_saved_effect"])
             for u in brussels_units if scored.get(u["id"], {}).get("ndvi_delta_eff") is not None]
    assert len(diffs) == 686
    exact = sum(d < 1e-4 for d in diffs)
    assert exact >= 0.90 * len(diffs), f"в пределах округления только {exact}/{len(diffs)}"
    assert max(diffs) < 0.005, f"макс. расхождение {max(diffs):.6f} — это уже не порядок входа"


def test_match_all_uses_twelve_controls_and_reports_gap(brussels_units):
    from engine.controls import match_all
    row = match_all(brussels_units[:200], "ndvi_before", "lst_before", ["ndvi_delta"])[0]
    assert len(row["control_ids"]) == 12
    assert "gap" in row and isinstance(row["comparable"], bool)


# ── аудит: пять отказов, каждый по своей причине ──────────────────────────────

def _fp(**kw):
    base = {"id": "x", "name": "Тест", "area_ha": 5.0, "in_city": True,
            "geometry": {"type": "Polygon", "coordinates": [[[4.35, 50.85], [4.36, 50.85], [4.36, 50.86], [4.35, 50.85]]]},
            "centroid": (4.35, 50.85)}
    base.update(kw)
    return base


@pytest.mark.parametrize("fp, fragment", [
    (_fp(area_ha=0.5), "меньше 1 га"),
    (_fp(in_city=False), "вне города"),
    (_fp(completed_year=2012), "до конца окна «до»"),
    (_fp(completed_year=2024), "внутри окна «после»"),
    (_fp(completed_year=2020), "опорный прибор"),
])
def test_audit_refuses_with_named_reason(fp, fragment):
    from engine.audit import audit_footprint
    res = audit_footprint(fp, pool=[], instruments={}, thresholds={})
    assert res.refusal and fragment in res.refusal, res.refusal
    assert not res.claimable


# ── окна ──────────────────────────────────────────────────────────────────────

def test_windows_shrink_before_window_for_2019_but_not_below_two_years():
    from engine.audit import windows_for_completion
    w = windows_for_completion(2019)
    assert w and w["before"] == ("2017-01-01", "2018-12-31") and w["before_years"] == 2
    assert windows_for_completion(2018) is None          # окно «до» упёрлось бы в 2016
    w20 = windows_for_completion(2020)
    assert w20["before"] == ("2017-01-01", "2019-12-31") and w20["after"] == ("2022-01-01", "2025-12-31")


def test_windows_for_old_projects_open_with_landsat():
    """Sentinel не берёт сданное до 2018; с data_from=2000 (Landsat) окно есть —
    так проверялись семь реставраций 2009–2016."""
    from engine.audit import windows_for_completion
    assert windows_for_completion(2012) is None
    w = windows_for_completion(2012, data_from=2000)
    assert w["before"] == ("2009-01-01", "2011-12-31") and w["after"] == ("2014-01-01", "2017-12-31")
    assert windows_for_completion(2006, data_from=2000)["before"][0] == "2003-01-01"


def test_annual_windows_roll_three_years_against_one_season():
    from engine.audit import annual_windows
    w = annual_windows(2024)
    assert w["before"] == ("2021-01-01", "2023-12-31") and w["after"] == ("2024-01-01", "2024-12-31")
    assert annual_windows(2019) is None


# ── манифест: порог без происхождения не публикуется ─────────────────────────

def test_manifest_rejects_threshold_without_source():
    from engine.manifest import LayerEntry, Manifest
    m = Manifest("brussels")
    with pytest.raises(ValueError, match="threshold_source"):
        m.add(LayerEntry(layer="lst", measures="t", unit="°C", method="DiD",
                         source="Landsat", computed="2026-09-01", threshold=1.32))


def test_brussels_manifest_has_seven_calibrated_layers():
    from engine.manifest import Manifest
    m = Manifest.read("brussels")
    assert set(m.layers) >= {"ndvi", "built", "trees", "grass", "bare", "shrub", "ndvi_landsat"}
    assert abs(m.layers["ndvi"].threshold - 0.0373) < 0.0005
    # Провенанс обязателен у КАЖДОГО слоя, включая те, у кого нет одного порога на
    # слой: у аудитов с окнами под проект порог свой на каждом окне, и в манифесте
    # должно стоять, откуда он берётся, а не пустое поле.
    assert all(v.threshold_source for v in m.layers.values())
    # Слоёв без единого порога два вида, и оба обязаны объяснить отсутствие:
    #   · аудит с окном под проект — порог свой на каждом окне;
    #   · импортированное состояние или рекомендация — порога нет по смыслу.
    # Пустое поле недопустимо: иначе читатель примет балл за измеренный эффект.
    thresholdless = [k for k, v in m.layers.items() if v.threshold is None]
    assert thresholdless, "слои без единого порога должны быть в пакете"
    # Проверяем смысл, а не мою формулировку: источник обязан упомянуть порог и
    # объяснить, почему единого значения нет — «порога нет», «порога значимости
    # нет», «свой на каждом окне». Жёсткая строка ловила бы синонимы как ошибку.
    for k in thresholdless:
        src = (m.layers[k].threshold_source or "").lower()
        assert "порог" in src and ("нет" in src or "каждом окне" in src), \
            f"{k}: отсутствие порога не объяснено ({src!r})"


def test_antwerp_threshold_is_its_own_not_brussels():
    """Порог — свойство пары (город, прибор): Антверпен шумнее на ~23 %."""
    from engine.manifest import Manifest
    a, b = Manifest.read("antwerp"), Manifest.read("brussels")
    assert a.layers["ndvi"].threshold > b.layers["ndvi"].threshold * 1.15


# ── приборы: вердикт ──────────────────────────────────────────────────────────

def test_judge_outcomes():
    from engine.instruments import REGISTRY
    j = REGISTRY["ndvi"].judge
    assert j(0.05, 0.0373).outcome == "significant_up"
    assert j(-0.05, 0.0373).outcome == "significant_down"
    assert j(0.01, 0.0373).outcome == "noise"
    assert j(0.05, 0.0373, control_gap=0.09, max_gap=0.04).outcome == "control_incomparable"
    assert j(None, 0.0373).outcome == "insufficient_data"
    assert j(0.05, None).outcome == "insufficient_data"      # без калибровки — не значимо


# ── предрегистрация: четыре защиты ────────────────────────────────────────────

GEOM = {"type": "Polygon", "coordinates": [[[4.3, 50.8], [4.31, 50.8], [4.31, 50.81], [4.3, 50.8]]]}


def test_preregistration_accepts_fixation_before_works():
    from engine.registries.preregistration import register
    r = register("P", "brussels", GEOM, "osm:way/1", "beliris:x", "park_creation",
                 works_start="2018-01-01", registered_at="2017-06-01")
    assert r.defensible


@pytest.mark.parametrize("kw, fragment", [
    (dict(works_start="2018-01-01", registered_at="2019-06-01"), "не раньше начала работ"),
    (dict(geometry_source="manual", works_start="2027-01-01"), "без пояснения"),
])
def test_preregistration_refuses(kw, fragment):
    from engine.registries.preregistration import register
    args = dict(name="P", city="brussels", geometry=GEOM, geometry_source="osm:way/1",
                signal_source="contract:90", intervention_type="square_depaving")
    args.update(kw)
    with pytest.raises(ValueError, match=fragment):
        register(**args)


def test_preregistration_detects_geometry_tampering():
    from dataclasses import replace
    from engine.registries.preregistration import register
    r = register("P", "brussels", GEOM, "osm:way/1", "beliris:x", "park_creation",
                 works_start="2018-01-01", registered_at="2017-06-01")
    assert "геометрия изменена" in " ".join(replace(r, geometry_hash="0" * 16).validate())


# ── адаптеры ──────────────────────────────────────────────────────────────────

def test_adapters_load_units_and_reject_outside_points():
    from engine.adapters import ADAPTERS
    b, a = ADAPTERS["brussels"](), ADAPTERS["antwerp"]()
    assert len(b.units()) == 724 and len(a.units()) == 458
    assert sum(u.population for u in b.units()) == 1_246_136
    assert len(b.income()) > 600 and len(a.income()) > 300
    assert not b.in_city_precise((4.10, 50.85))        # Dilbeek — вне Брюсселя
    assert b.in_city_precise((4.3616, 50.8684))        # Porte de Ninove — внутри
    # Гент — сама коммуна 44021, а не прямоугольник: 201 сектор, население 1.1.2024
    g = ADAPTERS["ghent"]()
    assert len(g.units()) == 201 and sum(u.population for u in g.units()) == 269_299
    assert all(u.id.startswith("44021") for u in g.units()) and len(g.income()) > 150
    assert g.in_city_precise((3.7250, 51.0540))        # Korenmarkt — внутри
    assert not g.in_city_precise((3.6486, 50.9947))    # De Pinte — соседняя коммуна
    assert not g.in_city_precise((3.7982, 51.0578))    # Destelbergen — тоже


def test_preregistered_records_on_disk_are_defensible():
    """Сохранённые записи предрегистрации: хеш геометрии сходится, источник назван,
    фиксация раньше работ. Изменённая на диске геометрия должна ловиться."""
    from engine.registries.preregistration import load, REGISTRY
    if not REGISTRY.exists():
        pytest.skip("реестр предрегистрации ещё не создан")
    recs = load()
    assert recs, "реестр есть, но пуст"
    for r in recs:
        assert r.defensible, f"{r.name}: {r.validate()}"
        assert r.registered_at <= "2026-12-31" and r.geometry["type"] in ("Polygon", "MultiPolygon")
        assert r.note, "запись без ожидаемого исхода — не предрегистрация, а закладка"


def test_preregistered_baseline_matches_records():
    """База «до» привязана к хешу записи: строка базы без записи или с чужим
    хешем — признак подмены следа после измерения."""
    import csv
    from engine.registries.preregistration import load, REGISTRY
    base = Path("data/registry/preregistered_baseline.csv")
    if not (REGISTRY.exists() and base.exists()):
        pytest.skip("база предрегистрации ещё не снята")
    by_id = {r.id: r for r in load()}
    rows = list(csv.DictReader(base.open()))
    assert rows
    for row in rows:
        assert row["id"] in by_id, f"база для несуществующей записи {row['id']}"
        assert by_id[row["id"]].geometry_hash == row["geometry_hash"], f"хеш разошёлся: {row['name']}"
    assert {r["instrument"] for r in rows} >= {"ndvi", "built", "trees", "grass"}


def test_preregistered_controls_named_before_works():
    """Контроль назван до работ и привязан к хешу записи; сопоставимость —
    по тому же порогу разрыва, что в аудите. Несопоставимый контроль пуст не обязан
    быть, но вердикт по нему запрещён."""
    import json
    from engine.config import CONTROL
    from engine.registries.preregistration import load, REGISTRY
    path = Path("data/registry/preregistered_controls.json")
    if not (REGISTRY.exists() and path.exists()):
        pytest.skip("контроль для предрегистрации ещё не назван")
    by_id = {r.id: r for r in load()}
    for c in json.loads(path.read_text()):
        assert c["id"] in by_id and by_id[c["id"]].geometry_hash == c["geometry_hash"]
        if c["comparable"]:
            assert abs(c["gap"]) <= CONTROL["max_gap_ndvi"] and len(c["control_ids"]) == CONTROL["n_controls"]


def test_preregistered_controls_avoid_other_footprints():
    """С 27.09.2026 контроль не берёт сектор, который задевает след другой записи того же города:
    начнутся там работы — сдвинется и контроль. Записи раньше правила (Josaphat, 02.09, в контроле
    сектор с 15 % следа Cinquantenaire) не переназываются — зафиксированный контроль не меняется."""
    import json
    from shapely.geometry import shape
    from engine.adapters import ADAPTERS
    from engine.registries.preregistration import load, REGISTRY
    path = Path("data/registry/preregistered_controls.json")
    if not (REGISTRY.exists() and path.exists()):
        pytest.skip("контроль для предрегистрации ещё не назван")
    recs = {r.id: r for r in load()}
    units = {}
    for c in json.loads(path.read_text()):
        rec = recs[c["id"]]
        if rec.registered_at < "2026-09-27":
            continue
        units.setdefault(rec.city, {u.id: u for u in ADAPTERS[rec.city]().units()})
        others = [shape(r.geometry) for r in recs.values() if r.city == rec.city and r.id != rec.id]
        for cid in c["control_ids"]:
            assert not any(shape(units[rec.city][cid].geometry).intersects(f) for f in others), \
                f"{rec.name}: контрольный сектор {cid} задевает чужой след"


def _fake_dossier(comparable=True, works_start="2027-03-01", tamper=False):
    from engine.registries.preregistration import Dossier, register
    geom = {"type": "Polygon", "coordinates": [[[4.35, 50.85], [4.36, 50.85], [4.36, 50.86], [4.35, 50.85]]]}
    rec = register("тест", "brussels", geom, "osm:way/1", "beliris:test", "square_redesign",
                   works_start=works_start, note="ожидание: built вниз", registered_at="2026-09-02")
    if tamper:
        rec = type(rec)(**{**rec.__dict__, "geometry_hash": "0000000000000000"})
    h = rec.geometry_hash
    baseline = {"ndvi": {"value": 0.30, "scenes": 20, "window": "2023–2025 лето", "geometry_hash": h},
                "built": {"value": 0.70, "scenes": 20, "window": "2023–2025 лето", "geometry_hash": h}}
    control = {"comparable": comparable, "gap": 0.002 if comparable else -0.118,
               "control_ids": [f"c{i}" for i in range(12)], "geometry_hash": h}
    return Dossier(rec, baseline, control)


def test_audit_preregistered_uses_fixed_baseline_and_named_control():
    from engine.audit import audit_preregistered
    from engine.instruments.base import REGISTRY, Reading
    import engine.instruments.vegetation  # noqa
    instr = {k: REGISTRY[k] for k in ("ndvi", "built")}
    thr = {"ndvi": 0.0373, "built": 0.0247}
    w = {"after": ("2031-01-01", "2034-12-31"), "label": "2023–2025 → 2031–2034"}
    res = audit_preregistered(_fake_dossier(), {"ndvi": Reading(0.42, 18), "built": Reading(0.60, 18)},
                              {"ndvi": 0.30, "built": 0.70}, {"ndvi": 0.31, "built": 0.70},
                              instr, thr, w, works_end_year=2029)
    assert res.refusal is None
    assert abs(res.results["ndvi"].effect - 0.11) < 1e-9 and res.results["ndvi"].verdict.outcome == "significant_up"
    assert abs(res.results["built"].effect + 0.10) < 1e-9 and res.results["built"].verdict.outcome == "significant_down"


@pytest.mark.parametrize("kw,works_end,phrase", [
    ({"comparable": False}, 2029, "несопоставимым до работ"),
    ({}, None, "срок сдачи неизвестен"),
    ({}, 2032, "не раньше окна «после»"),
    ({"works_start": "2025-05-01"}, 2029, "захватывает начало работ"),
    ({"tamper": True}, 2029, "не защитимо"),
])
def test_audit_preregistered_refusals(kw, works_end, phrase):
    from engine.audit import audit_preregistered
    from engine.instruments.base import REGISTRY, Reading
    import engine.instruments.vegetation  # noqa
    instr = {"ndvi": REGISTRY["ndvi"]}
    w = {"after": ("2031-01-01", "2034-12-31"), "label": "x"}
    if "works_start" in kw:   # фиксация 2026-09-02 раньше 2025 быть не может — обходим контракт регистрации
        d = _fake_dossier(works_start="2027-01-01")
        rec = type(d.record)(**{**d.record.__dict__, "works_start": kw["works_start"], "registered_at": "2024-01-01"})
        d = type(d)(rec, d.baseline, d.control)
    else:
        d = _fake_dossier(**kw)
    res = audit_preregistered(d, {"ndvi": Reading(0.4, 18)}, {"ndvi": 0.3}, {"ndvi": 0.3}, instr, {"ndvi": 0.0373}, w, works_end)
    assert res.refusal and phrase in res.refusal, res.refusal


def test_monitoring_funnel_reads_verdicts_from_layer_not_rounded_threshold():
    """Слой округлён до 4 знаков: сектор с эффектом −0,0280 при пороге 0,02797
    по пересчёту выпал бы, по слою (dw_label стоит) — остаётся кандидатом."""
    import importlib.util, sys
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("monitoring_html", Path("scripts/report/monitoring_html.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    rows = [
        {"id": "a", "name": "A", "effect": -0.0280, "population": 10, "area_ha": 5, "comparable": True, "dw_label": "не подтверждено", "dw_trees": 0.0, "dw_built": 0.0},
        {"id": "b", "name": "B", "effect": -0.0500, "population": 20, "area_ha": 5, "comparable": True, "dw_label": "ПОТЕРЯ КРОНЫ", "dw_trees": -0.05, "dw_built": 0.0},
        {"id": "c", "name": "C", "effect": -0.0600, "population": 30, "area_ha": 5, "comparable": True, "dw_label": "СТРОЙКА", "dw_trees": -0.01, "dw_built": 0.06},
        {"id": "d", "name": "D", "effect": -0.0900, "population": 40, "area_ha": 5, "comparable": False, "dw_label": "", "dw_trees": None, "dw_built": None},
        {"id": "e", "name": "E", "effect": +0.0400, "population": 50, "area_ha": 5, "comparable": True, "dw_label": "", "dw_trees": None, "dw_built": None},
    ]
    F = mod.funnel(rows, 0.02797)
    assert [r["id"] for r in F["lost"]] == ["c", "b", "a"]      # a остаётся: вердикт из слоя
    assert F["refused"] == 1 and [r["id"] for r in F["gained"]] == ["e"]
    assert len(F["confirmed"]) == 1 and len(F["construction"]) == 1 and len(F["unconfirmed"]) == 1
    assert F["lost_pop"] == 60


def _load(path):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(Path(path).stem, Path(path))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def test_agvespa_completion_year_prefers_opening_event_over_last_event():
    """Год сдачи — по событию открытия, а не по последнему событию: у Droogdokkeneiland
    хронология тянется до 2025 (доки, Havenwereld), а Belvédère открыт в 2018."""
    m = _load("scripts/registry/fetch_agvespa.py")
    ev = [{"when": "2016", "title": "Start werken", "body": "", "year": 2016},
          {"when": "september 2018", "title": "Opening Belvédère", "body": "", "year": 2018},
          {"when": "Augustus 2024", "title": "Start werken droogdokken", "body": "", "year": 2024}]
    assert m.completion(ev, "In realisatie") == (2018, "done_event")
    assert m.completion([ev[0], ev[2]], "Gerealiseerd") == (2024, "last_event")
    assert m.completion([ev[0]], "In realisatie") == (None, "unknown")
    assert m.year_of("24 oktober 2025") == 2025 and m.year_of("2007-2010") == 2010 and m.year_of("binnenkort") is None


def test_dated_audit_outcome_vocabulary_uses_city_thresholds():
    m = _load("scripts/gee/audit_parks_dated.py")
    thr = {"built": 0.0279, "trees": 0.0278, "grass": 0.0170, "bare": 0.0095}   # Антверпен
    assert m.outcome({"built": -0.097, "trees": 0.049, "grass": 0.073, "bare": -0.055}, thr) == "раскрыли и озеленили"
    assert m.outcome({"built": 0.327, "trees": -0.157, "grass": -0.027, "bare": 0.008}, thr) == "стройка / застройка"
    assert m.outcome({"built": -0.009, "trees": -0.024, "grass": 0.099, "bare": -0.152}, thr) == "голый грунт → трава"
    assert m.outcome({"built": 0.010, "trees": 0.040, "grass": 0.001, "bare": 0.0}, thr) == "крона выросла без смены покрытия"
    # Konijnenwei: built +0,021 выше плейсхолдера 0,02, но ниже калиброванного 0,0279 — не стройка
    assert m.outcome({"built": 0.021, "trees": 0.05, "grass": 0.0, "bare": 0.0}, thr) == "крона выросла без смены покрытия"


@pytest.mark.parametrize("year,area,want_instr,want_before,caveat", [
    (2020, 11.4, "ndvi", ("2017-01-01", "2019-12-31"), False),          # ряда хватает — Sentinel-2
    (2009, 19.5, "ndvi_landsat", ("2006-01-01", "2008-12-31"), False),  # до эры S2 — Landsat, объект крупный
    (2018, 1.6, "ndvi", ("2017-01-01", "2017-12-31"), True),            # Droogdokkenpark: мелкий → S2 с одним годом базы
    (2018, 16.0, "ndvi_landsat", ("2015-01-01", "2017-12-31"), False),  # тот же год, крупный → Landsat без оговорки
])
def test_instrument_choice_accounts_for_footprint_size_not_only_year(year, area, want_instr, want_before, caveat):
    """Дефект, найденный на Droogdokkenpark: правило «нет ряда S2 → Landsat» подменяло
    измерение видимостью на объекте 1,6 га. Размер следа теперь входит в выбор."""
    from engine.audit import instrument_for
    instr, w, note = instrument_for(year, area)
    assert instr == want_instr and w["before"] == want_before
    assert bool(note) is caveat
    if caveat:
        assert "сцен" in note and "1 год" in note


def test_instrument_choice_returns_none_when_after_window_has_not_arrived():
    from engine.audit import instrument_for
    assert instrument_for(2029, 20.0) is None


def test_short_before_window_downgrades_verdict_to_preliminary():
    """Приоритет Sentinel-2 на мелком следе сжимает окно «до» до года, и там
    бывает одна сцена. Движок такой аудит отказывается считать; страница обязана
    показать вердикт предварительным, а не в один ряд с полноценными."""
    m = _load("scripts/gee/audit_parks_dated.py")
    assert m.qualify("ПОЗЕЛЕНЕЛ", 1, 38) == "предварительно: позеленел"
    assert m.qualify("ПОТЕРЯЛ", 21, 3) == "предварительно: потерял"
    assert m.qualify("ПОЗЕЛЕНЕЛ", 13, 15) == "ПОЗЕЛЕНЕЛ"
    assert m.qualify("шум", 1, 1) == "шум" and m.qualify("мелкий для 30 м", 1, 1) == "мелкий для 30 м"


# ── линия выполнения: точечные объекты в названных заранее точках ─────────────

def test_named_point_contract_refuses_indefensible_records():
    from engine.registries.points import register
    ok = register("bxl-wb-001", "brussels", "21004D600", "waste_basket", 4.35, 50.85,
                  rule="сектор нижнего терциля дохода без урны в 150 м",
                  expectation="урна появится в 50 м от точки к сезону 2028")
    assert ok.point_hash and not ok.validate()
    for kw, phrase in [
        (dict(kind="fountain"), "не поддерживается"),
        (dict(rule="  "), "правило выбора"),
        (dict(expectation=""), "ожидание не записано"),
        (dict(radius_m=500), "вне допустимого"),
        (dict(role="whatever"), "роль"),
    ]:
        base = dict(id="x", city="brussels", unit_id="u", kind="waste_basket", lon=4.35, lat=50.85,
                    rule="правило", expectation="ожидание")
        base.update(kw)
        with pytest.raises(ValueError, match=phrase):
            register(**base)


def test_named_point_hash_catches_a_moved_point():
    from engine.registries.points import NamedPoint, register
    p = register("bxl-wb-002", "brussels", "u", "bench", 4.35, 50.85,
                 rule="правило", expectation="ожидание")
    moved = NamedPoint(**{**p.__dict__, "lon": 4.36})
    assert any("точку двигали" in x for x in moved.validate())
    rewidened = NamedPoint(**{**p.__dict__, "radius_m": 120})
    assert any("точку двигали" in x for x in rewidened.validate())


def test_appearance_subtracts_map_drift_and_refuses_on_thin_data():
    """Появление в названных точках само по себе ничего не значит: карта OSM
    пополняется сама. Значение имеет только разность с контрольными точками."""
    from engine.registries.points import AppearanceResult
    thin = AppearanceResult("waste_basket", "2020-01-01", "сейчас",
                            named_total=5, named_appeared=4, control_total=5, control_appeared=1)
    assert "отказ" in thin.verdict() and abs(thin.lift - 0.6) < 1e-9

    # Первый прогон по построению даёт нули: точки отбирались как пустые сегодня.
    # Называть это «неотличимо от дрейфа» — подмена: сравнивать нечего.
    baseline = AppearanceResult("waste_basket", "2020-01-01", "сейчас",
                                named_total=28, named_appeared=0, control_total=24, control_appeared=0)
    assert baseline.lift == 0 and "отбор подтверждён" in baseline.verdict()

    drift_only = AppearanceResult("waste_basket", "2020-01-01", "сейчас",
                                  named_total=40, named_appeared=12, control_total=40, control_appeared=12)
    assert drift_only.lift == 0 and drift_only.verdict() == "выполнение не отличается от дрейфа карты"

    real = AppearanceResult("waste_basket", "2020-01-01", "сейчас",
                            named_total=40, named_appeared=24, control_total=40, control_appeared=8)
    assert abs(real.lift - 0.4) < 1e-9 and "сверх дрейфа" in real.verdict()


def test_named_points_on_disk_are_defensible_and_split_is_reproducible():
    """Файл точек проверяется при каждом прогоне: подмена координат ломает хеш.
    Разделение на названные и контрольные воспроизводится из напечатанного зерна."""
    import hashlib
    from pathlib import Path
    from engine.registries.points import load
    pts = load(Path("data/registry/named_points.json"))
    assert len(pts) >= 40, f"точек всего {len(pts)}"
    for p in pts:
        assert not p.validate(), (p.id, p.validate())
    roles = {p.role for p in pts}
    assert roles == {"named", "control"}
    seed = "facta-2026-09-04"
    for p in pts:
        expected = "named" if int(hashlib.sha256((seed + p.unit_id).encode()).hexdigest(), 16) % 2 == 0 else "control"
        assert p.role == expected, f"{p.id}: разделение не воспроизводится зерном"
    # обе половины непусты и сопоставимы по размеру — иначе сравнение долей бессмысленно
    named = [p for p in pts if p.role == "named"]
    control = [p for p in pts if p.role == "control"]
    assert min(len(named), len(control)) / max(len(named), len(control)) > 0.6


def test_imported_layers_declare_no_threshold_but_state_why():
    """Слои из соседних проектов — состояние и рекомендация, а не изменение против
    контроля. Порога у них нет, но происхождение обязано это объяснять, иначе
    читатель примет балл размещения за измеренный эффект."""
    from engine.manifest import Manifest
    imported = {"brussels": ["fit_score", "points_improvements"],
                "antwerp": ["points_waste_bins", "points_toilets", "points_benches"]}
    for city, keys in imported.items():
        m = Manifest.read(city)
        for k in keys:
            e = m.layers[k]
            assert e.threshold is None, f"{city}/{k}: у рекомендации не может быть порога значимости"
            assert "порога нет" in (e.threshold_source or ""), f"{city}/{k}: не объяснено, почему порога нет"
            assert e.limits, f"{city}/{k}: границы применимости не записаны"
            assert any("не" in x for x in e.limits)


def test_planner_points_carry_score_and_naming_date():
    """Точка кандидата бесполезна без балла и даты: дата — то, что делает её
    проверяемой позже, балл — то, чем она отличается от произвольной точки."""
    import json
    from pathlib import Path
    gj = json.loads(Path("cities/antwerp/points/waste_bins.geojson").read_text())
    assert gj["properties"]["n_candidates_pool"] > len(gj["features"])
    assert gj["properties"]["coverage_after"] > gj["properties"]["coverage_before"]
    for f in gj["features"]:
        p = f["properties"]
        assert {"rank", "Score", "GapScore", "EquityIndex", "asset", "named_at"} <= set(p)
        assert f["geometry"]["type"] == "Point"


@pytest.mark.parametrize("city", ["antwerp", "brussels"])
def test_planner_named_points_use_the_budget_cut_as_control(city):
    """Контроль линии выполнения — кандидаты сразу ниже отсечки бюджета: тот же
    движок, тот же пул, отличие ровно одно — попал в рекомендацию или нет.
    Половины равны по размеру, все записи защитимы."""
    from pathlib import Path
    from engine.registries.points import PLANNER_KINDS, load
    # Число точек не зашито константой: типов объектов становится больше, и
    # жёсткое число ломалось бы при каждом расширении, скрывая настоящие дефекты.
    # Инвариант другой: по 20 точек на тип (10 названных + 10 контрольных),
    # ровно столько типов, сколько слоёв кандидатов лежит в пакете.
    pts = load(Path(f"data/registry/named_points_{city}.json"))
    kinds = {p.kind for p in pts}
    assert len(pts) == 20 * len(kinds), f"{len(pts)} точек на {len(kinds)} типов — не по 20 на тип"
    assert len(kinds) >= 7, "типов объектов стало меньше семи — проверить, не выпал ли слой"
    named = [p for p in pts if p.role == "named"]
    control = [p for p in pts if p.role == "control"]
    assert len(named) == len(control) == len(pts) // 2
    for p in pts:
        assert not p.validate(), (p.id, p.validate())
        rank = int(p.unit_id.split("#")[1])
        assert (rank <= 10) == (p.role == "named"), f"{p.id}: роль не соответствует рангу"
        assert "City Planner" in p.rule and "прирост" in p.rule
        assert p.city == city
    assert set(p.kind for p in pts) <= set(PLANNER_KINDS.values())


def test_worldcover_and_our_canopy_agree_in_rank_but_not_in_magnitude():
    """Ключевая оговорка проекта, ставшая измеренным фактом: Dynamic World даёт
    среднюю вероятность класса, а не долю площади. Ранги согласуются с официальным
    продуктом, величины расходятся втрое — и путать их нельзя."""
    import csv
    import statistics
    from pathlib import Path
    for city in ("brussels", "antwerp"):
        wc = {r["id"]: float(r["wc_trees"]) for r in
              csv.DictReader(Path(f"cities/{city}/layers/worldcover_2021.csv").open())}
        ours = {r["id"]: float(r["trees_2024"]) for r in
                csv.DictReader(Path(f"cities/{city}/layers/article8_2024.csv").open())
                if r.get("trees_2024") not in ("", None)}
        common = sorted(set(wc) & set(ours))
        assert len(common) > 400, f"{city}: секторов для сверки мало"
        xs = [ours[i] for i in common]
        ys = [wc[i] for i in common]
        r = statistics.correlation(xs, ys)
        assert r > 0.7, f"{city}: ранговое согласие потеряно, r={r:.3f}"
        assert statistics.mean(ys) > 2 * statistics.mean(xs), \
            f"{city}: расхождение величин исчезло — проверить, не подменён ли слой"


def test_rule_3_30_300_counts_only_what_is_measured():
    """Из трёх пунктов нормы измеримы два. Третий не имитируется, и слой не
    делает вид, что город проверен полностью."""
    import csv
    from pathlib import Path
    from engine.manifest import Manifest
    for city, both_max in (("brussels", 0.20), ("antwerp", 0.15)):
        rows = list(csv.DictReader(Path(f"cities/{city}/layers/rule_3_30_300.csv").open()))
        pop = sum(int(r["population"]) for r in rows)
        both = sum(int(r["population"]) for r in rows if r["passes_both"] == "1") / pop
        assert 0 < both < both_max, f"{city}: доля выполнивших оба пункта {both:.1%} неправдоподобна"
        for r in rows:
            assert (r["passes_30"] == "1") == (float(r["canopy_share"]) >= 0.30)
        limits = Manifest.read(city).layers["rule_3_30_300"].limits
        assert any("3 дерева" in x for x in limits), "неизмеренный пункт не объявлен"


def test_heat_layer_is_state_not_change_and_says_so():
    """Проект отказался измерять охлаждение от вмешательств: порог 1,32 °C больше
    реалистичного эффекта. Тепловой слой описывает СОСТОЯНИЕ и обязан это заявлять,
    иначе он тихо возвращает отвергнутое утверждение."""
    import csv
    import statistics
    from pathlib import Path
    from engine.manifest import Manifest
    for city in ("brussels", "antwerp"):
        e = Manifest.read(city).layers["heat_2022_2025"]
        assert e.threshold is None
        src = (e.threshold_source or "").lower()
        assert "состояние" in src and "1,32" in src, "слой не объясняет, почему порога нет"
        assert any("поверхности, а не воздуха" in x.lower() for x in e.limits)
        rows = list(csv.DictReader(Path(f"cities/{city}/layers/heat_2022_2025.csv").open()))
        assert len(rows) > 400
        # Превышение считается от медианы города: сумма отклонений около нуля по медиане
        exc = sorted(float(r["excess_over_city_c"]) for r in rows)
        assert abs(statistics.median(exc)) < 1e-6, "превышение отсчитано не от медианы"
        lst = [float(r["lst_summer_c"]) for r in rows]
        assert 20 < statistics.median(lst) < 50, "температура вне физически осмысленного диапазона"


def test_heat_and_canopy_are_strongly_anticorrelated():
    """Связка, ради которой слой и нужен: где нет кроны — там жарко. Если знак
    развернётся, слой подменён или маска сломана."""
    import csv
    import statistics
    from pathlib import Path
    for city, r_max in (("brussels", -0.6), ("antwerp", -0.4)):
        heat = {r["id"]: float(r["lst_summer_c"]) for r in
                csv.DictReader(Path(f"cities/{city}/layers/heat_2022_2025.csv").open())}
        can = {r["id"]: float(r["wc_trees"]) for r in
               csv.DictReader(Path(f"cities/{city}/layers/worldcover_2021.csv").open())}
        common = sorted(set(heat) & set(can))
        r = statistics.correlation([heat[i] for i in common], [can[i] for i in common])
        assert r < r_max, f"{city}: связь тепла и кроны потеряна, r={r:.3f}"


@pytest.mark.parametrize("city", ["antwerp", "brussels", "ghent", "liege", "charleroi"])
def test_three_canopy_instruments_agree_by_rank_and_differ_by_magnitude(city):
    """Три прибора, два производителя, два сенсора: ESA WorldCover (Sentinel-2),
    Dynamic World (Sentinel-2) и VITO Proba-V. Согласие по рангу высокое, величины
    расходятся — и так и должно быть: определения кроны и разрешение разные.
    Если величины сойдутся, значит слой подменён."""
    import csv
    import statistics
    from pathlib import Path
    root = Path(f"cities/{city}/layers")
    probav = {r["id"]: float(r["canopy_share"]) for r in csv.DictReader((root / "canopy_probav_2019.csv").open())}
    wc = {r["id"]: float(r["wc_trees"]) for r in csv.DictReader((root / "worldcover_2021.csv").open())}
    dw = {r["id"]: float(r["trees_2024"]) for r in csv.DictReader((root / "article8_2024.csv").open())
          if r.get("trees_2024")}
    # Брюссель с WorldCover 0,79 — ниже Антверпена: лесные секторы у Суаньского леса,
    # где наш прибор занижает крону, а 100-метровая сетка обнуляет плотную застройку.
    # Гент (26.09.2026): 0,71 и 0,85 на 201 секторе — в центре много мелких секторов, которые
    # 100-метровая сетка Proba-V почти не различает; страж стоит под измеренным значением.
    r_mins = {"ghent": (0.65, 0.80)}.get(city, (0.75, 0.85))
    for other, r_min in zip((wc, dw), r_mins):
        common = sorted(set(probav) & set(other))
        # the comparison covers nearly every sector both layers have (ours skips unmeasured ones)
        assert len(common) >= 0.95 * min(len(probav), len(other))
        r = statistics.correlation([probav[i] for i in common], [other[i] for i in common])
        assert r > r_min, f"согласие по рангу потеряно: r={r:.3f}"
    common = sorted(set(probav) & set(wc))
    assert statistics.mean(wc[i] for i in common) > 2 * statistics.mean(probav[i] for i in common), \
        "величины сошлись — проверить, не подменён ли один из слоёв"


# ── воспроизводимость страниц ────────────────────────────────────────────────

# Порядок важен ровно в одном месте: атлас читает данные атласа, лендинг — карту атласа.
PAGE_BUILD = [
    ("atlas_data.py --city brussels", None),
    ("atlas_data.py --city antwerp", None),
    ("atlas_html.py --city brussels", "atlas-brussels.html"),
    ("atlas_html.py --city antwerp", "atlas-antwerp.html"),
    ("landing_html.py", "frondia-landing.html"),
    ("method_html.py", "method.html"),
    ("points_html.py", "named-points.html"),
    ("registry_html.py", "registry-brussels.html"),
    ("registry_antwerp_html.py", "registry-antwerp.html"),
    ("article8_html.py --city brussels", "article8-brussels.html"),
    ("article8_html.py --city antwerp", "article8-antwerp.html"),
    ("monitoring_html.py --city brussels --season 2025", "monitoring-brussels-2025.html"),
    ("monitoring_html.py --city antwerp --season 2025", "monitoring-antwerp-2025.html"),
    ("monitoring_html.py --city brussels --season 2026", "monitoring-brussels-2026.html"),
    ("monitoring_html.py --city antwerp --season 2026", "monitoring-antwerp-2026.html"),
    ("audit_html.py --case data/registry/cases/ninove.json", "audit-ninove.html"),
    ("audit_html.py --case data/registry/cases/droogdokkenpark.json", "audit-droogdokkenpark.html"),
    ("audit_html.py --case data/registry/cases/spoor-noord.json", "audit-spoor-noord.html"),
    ("dossier_html.py --city brussels --sector 21012A152", "dossier-21012A152.html"),
    ("dossier_html.py --city antwerp --sector auto", "dossier-11002R13-.html"),
]


@pytest.fixture(scope="module")
def built_pages(tmp_path_factory):
    """Все страницы, собранные с нуля в пустые папки — один раз на модуль."""
    import os
    import subprocess
    import sys
    base = tmp_path_factory.mktemp("pages")
    out, derived = base / "out", base / "derived"
    env = {**os.environ, "FRONDIA_OUT": str(out), "FRONDIA_DERIVED": str(derived)}
    logs = []
    for cmd, page in PAGE_BUILD:
        r = subprocess.run([sys.executable, *f"scripts/report/{cmd}".split()], env=env,
                           capture_output=True, text=True, timeout=600)
        logs.append((cmd, page, r.returncode, r.stderr[-1500:]))
    return out, derived, logs


def test_every_page_rebuilds_from_a_clean_output_folder(built_pages):
    """Каждая опубликованная страница обязана собираться из файлов проекта в пустую
    папку. Дефект, ради которого тест написан: промежуточные данные атласа жили во
    временной папке, её очистили — и атлас с лендингом перестали собираться,
    хотя правило «страница пересобирается скриптом» считалось выполненным."""
    from pathlib import Path
    out, derived, logs = built_pages
    for cmd, page, code, err in logs:
        assert code == 0, f"{cmd}:\n{err}"
        if page:
            p = out / page
            assert p.exists() and p.stat().st_size > 5000, f"{cmd}: страница {page} не собралась"
            assert "<title>" in p.read_text(encoding="utf-8")[:4000], f"{page}: нет заголовка"
    assert not list(Path("data/derived").glob("*.tmp")), "промежуточное утекло мимо подменённой папки"
    assert any(derived.iterdir()), "атлас не записал промежуточные данные туда, откуда их читают"


def test_pages_have_no_visible_defects(built_pages):
    """Тест «страница собирается» не видит, что на ней написано. Все дефекты, найденные на
    живых страницах 24.09.2026, прошли мимо тестов: пустая карта атласа, «база — 2–0»,
    «в 3 раз», «playground / playground», идентификатор вместо имени сектора. Здесь —
    признаки этих классов ошибок в видимом тексте каждой страницы."""
    import html
    import re
    out, _, _ = built_pages
    from engine.registries.points import KIND_LABEL_RU, KINDS
    assert set(KINDS) <= set(KIND_LABEL_RU), f"типы без русского названия: {set(KINDS) - set(KIND_LABEL_RU)}"
    kinds = [k for k in KINDS if "_" in k or k in ("playground", "shelter", "recycling", "defibrillator")]
    problems = []
    for f in sorted(out.glob("*.html")):
        raw = f.read_text(encoding="utf-8")
        txt = re.sub(r"<(style|script|title)[^>]*>.*?</\1>", " ", raw, flags=re.S)
        txt = html.unescape(re.sub(r"<[^>]+>", " ", txt))
        checks = {
            "None/nan в тексте": re.findall(r"\b(?:None|nan|NaN|undefined)\b", txt),
            "неподставленные скобки": re.findall(r"\{[a-z_]+\}", txt),
            "пустая таблица": re.findall(r"<tbody>\s*</tbody>", raw),
            "цифры вместо лет": re.findall(r"(?:база|окно)\s*[—-]\s*\d{1,3}\s*[–-]\s*\d{1,3}\b", txt),
            "«в 2–4 раз»": re.findall(r"\bв [234] раз\b", txt),
            "схлопнутый сектор карты": re.findall(r'd="M([\d.]+,[\d.]+) \1Z"', raw),
            "идентификатор вместо имени": re.findall(r"<code>([0-9A-Z-]{9})</code></td><td>\1\b", raw),
            "английский ключ вместо названия": re.findall(r"<td>([a-z_]{4,})<small><code>\1</code>", raw),
            "ключ типа объекта в тексте": re.findall(
                r"\b(?:" + "|".join(kinds) + r")\b",
                html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(style|script|title|code)[^>]*>.*?</\1>", " ", raw, flags=re.S)))),
        }
        for name, hits in checks.items():
            if hits:
                problems.append(f"{f.name}: {name} ×{len(hits)} ({hits[:2]})")
    assert not problems, "\n".join(problems)


def test_ring_simplification_keeps_the_shape_of_a_closed_polygon():
    """Дефект 24.09.2026: замкнутое кольцо уходило в Дугласа–Пекера целиком, базовая
    линия от первой точки к последней имела нулевую длину, и каждый сектор атласа
    схлопывался в две одинаковые точки. Карта рисовала пустоту больше трёх недель."""
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("atlas_data", Path("scripts/report/atlas_data.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    square = [(0, 0), (5, 0), (10, 0), (10, 10), (0, 10), (0, 0)]   # лишняя точка на ребре
    out = mod.dp_ring(square, eps=0.5)
    assert sorted(out) == [(0, 0), (0, 10), (10, 0), (10, 10)], out
    tiny = [(0, 0), (0.1, 0), (0.1, 0.1), (0, 0)]                     # мельче допуска — остаётся как есть
    assert len(mod.dp_ring(tiny, eps=5)) >= 3


@pytest.mark.parametrize("city", ["brussels", "antwerp", "ghent", "liege", "charleroi"])
def test_atlas_sectors_are_polygons_not_points(city):
    """Каждый сектор на карте атласа — многоугольник хотя бы из трёх разных точек."""
    import json
    import re
    from pathlib import Path
    A = json.loads(Path(f"data/derived/atlas-{city}.json").read_text())
    degenerate = []
    for s in A["sectors"]:
        for ring in re.findall(r"M([^Z]*)Z", s["d"]):
            if len(set(ring.split())) < 3:
                degenerate.append(s["id"])
    assert not degenerate, f"{len(degenerate)} секторов схлопнуты в точку: {degenerate[:5]}"



@pytest.mark.parametrize("city", ["brussels", "antwerp", "ghent", "liege", "charleroi"])
def test_season_thresholds_come_from_the_run_not_from_hands(city):
    """С сезона 2026 порог мониторинга пишет сам прогон. Манифест обязан совпадать
    с файлом калибровки: вписанное руками число могло бы тихо разойтись с измерением."""
    import json
    from pathlib import Path
    from engine.manifest import Manifest
    m = Manifest.read(city)
    files = sorted(Path("data").glob(f"monitoring_{city}_*_calibration.json"))
    assert files, "ни одного файла калибровки сезона"
    for f in files:
        j = json.loads(f.read_text())
        layer = m.layers[f"monitoring_{j['season']}"]
        assert abs(layer.threshold - j["threshold"]) < 1e-9, (f.name, layer.threshold, j["threshold"])
        assert j["unbiased"], f"{f.name}: нулевое распределение смещено"
        assert abs(j["mean"]) < 0.1 * j["threshold"], f"{f.name}: среднее не около нуля"


def test_documents_can_move_a_canopy_loss_into_construction():
    """Третий фильтр после двух приборов — документы. Peterbos 2026: оба прибора видят
    потерю кроны, документ — стройплощадку (работы с апреля 2026). Сектор уходит в
    стройки, а не пропадает: перенос виден на странице и объяснён источником."""
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("monitoring_html", Path("scripts/report/monitoring_html.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    rows = mod.apply_documents(mod.load_layer("brussels", 2026), "brussels", 2026)
    peterbos = next(r for r in rows if r["id"] == "21001A83-")
    assert peterbos["dw_label"] == "СТРОЙКА" and peterbos["instrument_label"] == "ПОТЕРЯ КРОНЫ"
    F = mod.funnel(rows, 0.0214)
    assert "21001A83-" in {r["id"] for r in F["construction"]}
    assert "21001A83-" not in {r["id"] for r in F["confirmed"]}
    assert {"21016A193", "21001A982"} <= {r["id"] for r in F["confirmed"]}


@pytest.mark.parametrize("effects,expected", [
    ([0.11, 0.28, 0.06, 0.21, 0.32, 0.11, 0.12], "и держится все 7 сезонов"),                       # Ninove
    ([0.12, 0.10, 0.16, 0.12, 0.13, 0.18, 0.03], "держится до 2024-го и в 2025 уходит в шум"),      # провал в конце
    ([0.12, 0.10, 0.16, 0.12, 0.13, 0.18, 0.03, 0.10], "в шуме только 2025, после чего эффект возвращается"),
    ([0.12, 0.00, 0.16, 0.12, 0.13, 0.18, 0.03], "в шуме 2020 посреди ряда и 2025 в конце"),
])
def test_series_phrase_names_the_shape_of_the_series(effects, expected):
    """Дефект, найденный на Park Spoor Noord: фраза знала одну форму ряда и напечатала
    «держится до 2026-го и в 2018 уходит в шум» — провал посреди ряда описан как конец."""
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("audit_html", Path("scripts/report/audit_html.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    seasons = [{"season": 2019 + i, "effect": e} for i, e in enumerate(effects)]
    assert expected in mod.series_phrase(seasons, 0.0458)


# ── статья 8 по методике Комиссии: официальные слои Copernicus ─────────────────

def _art8():
    import importlib.util
    spec = importlib.util.spec_from_file_location("art8_official", ROOT / "scripts/official/art8_official.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def test_laea_projection_matches_the_epsg_worked_example():
    """EPSG Guidance Note 7-2, ETRS89 / LAEA Europe: 50° с. ш., 5° в. д. →
    E 3 962 799,45; N 2 999 718,85. Проекция своя, без pyproj, — значит, проверяется числом."""
    x, y = _art8().laea(5.0, 50.0)
    assert abs(x - 3962799.45) < 0.01 and abs(y - 2999718.85) < 0.01


def test_scanline_counts_the_pixels_of_a_square_exactly():
    """Квадрат 400×400 м на сетке 10 м — ровно 1600 пикселей; внутри клетки 1 км (0, 0)
    все они считаются в центрах и кластерах, вне её — ни один."""
    m = _art8()
    data = bytes([1]) * (100 * 100)
    g = m.Grid(data, (0, 0, 1000, 1000), 10)
    square = [[(100, 100), (500, 100), (500, 500), (100, 500), (100, 100)]]
    tot, inside, _ = g.tally(square, (0, 1), {(0, 0)})
    assert tot[1] == 1600 and inside[1] == 1600 and tot[0] == 0
    tot, inside, _ = g.tally(square, (0, 1), {(5, 5)})
    assert tot[1] == 1600 and inside[1] == 0


def test_exemption_needs_both_shares_strictly_above_the_thresholds():
    """Ст. 8(1): «больше 45 %» и «больше 10 %» — ровно на пороге исключения нет."""
    ex = _art8().exempt
    assert ex({"green": 0.46, "canopy_wvl": 0.11})[0]
    assert not ex({"green": 0.45, "canopy_wvl": 0.50})[0]
    assert not ex({"green": 0.90, "canopy_wvl": 0.10})[0]
    assert not ex({"green": None, "canopy_wvl": 0.30})[0]


@pytest.mark.parametrize("city", ["brussels", "antwerp", "ghent", "liege", "charleroi"])
def test_official_article8_layer_is_consistent_and_aligned(city):
    """Записанный вердикт обязан следовать правилу из записанных же долей; все LAU —
    города по DEGURBA; площадь по границам 1:1M близка к официальной. И страж сетки:
    если растр сдвинут или перевёрнут, официальная крона перестаёт совпадать с WorldCover
    по рангу — сейчас r ≥ 0,93, падение ниже 0,85 значит сломанное выравнивание."""
    import statistics
    lau = list(csv.DictReader((ROOT / f"cities/{city}/layers/art8_official_lau_2021.csv").open()))
    assert lau
    for r in lau:
        g, c = float(r["green_ucuc"]), float(r["canopy_wvl_ucuc"])
        assert (r["exempt"] == "True") == (g > 0.45 and c > 0.10), r["lau_id"]
        assert r["degurba"] == "1"
        assert 0.85 < float(r["area_km2_all"]) / float(r["area_km2_official"]) < 1.05, r["lau_id"]
    sec = {r["id"]: float(r["canopy_wvl"]) for r in
           csv.DictReader((ROOT / f"cities/{city}/layers/art8_official_2021.csv").open()) if r["canopy_wvl"]}
    wc = {r["id"]: float(r["wc_trees"]) for r in
          csv.DictReader((ROOT / f"cities/{city}/layers/worldcover_2021.csv").open())}
    ids = sorted(set(sec) & set(wc))
    assert statistics.correlation([sec[i] for i in ids], [wc[i] for i in ids]) > 0.85
    man = json.loads((ROOT / f"cities/{city}/manifest.json").read_text())["layers"]
    assert {"art8_official_lau_2021", "art8_official_2021"} <= set(man)


def test_no_page_repeats_the_pixel_median_as_the_city_background(built_pages):
    """Поправка 25.09.2026: «медиана по всему Брюсселю +0,043 — больше порога, значимым
    выглядел бы почти каждый сектор» стояло на пяти страницах. +0,043 — медиана по
    пикселям, порог — по секторам; по секторам медиана +0,033 и без контроля за порог
    выходит треть, а не «почти каждый». Фраза не должна вернуться ни на одну страницу."""
    out, _, _ = built_pages
    pages = list(out.glob("*.html"))
    assert pages
    for f in pages:
        t = f.read_text(encoding="utf-8")
        assert "0,043" not in t and "почти каждый" not in t, f.name


def test_city_background_is_counted_from_the_same_layers_as_the_atlas():
    """Фон считается из слоя сырого изменения и слоя эффекта: без контроля «значимо
    позеленевших» в разы больше, чем против контроля, а сама медиана фона меньше порога —
    именно это и было неверно записано раньше."""
    import sys
    sys.path.insert(0, str(ROOT))
    from scripts.report.background import background
    for city in ("brussels", "antwerp"):
        b = background(city)
        assert b and b["raw_median"] < b["thr"]
        assert b["k_raw"] >= 5 * max(b["k_eff"], 1)
    s8 = json.loads((ROOT / "cities/brussels/layers/article8_2024_summary.json").read_text())
    assert background("brussels")["k_eff"] == s8["trend"]["ndvi_gain_sectors"]


def test_dossier_sector_picked_by_rule_meets_every_condition(built_pages):
    """Сектор досье Антверпена выбран правилом, а не вручную. Проверяется каждое условие
    правила по слоям пакета — иначе «выбран правилом» было бы подписью, а не фактом."""
    import re
    out, _, _ = built_pages
    page = next(out.glob("dossier-11002*.html"))
    sid = re.search(r"сектор (11002[0-9A-Z-]+)", page.read_text(encoding="utf-8")).group(1)
    rows = {r["id"]: r for r in csv.DictReader((ROOT / "cities/antwerp/layers/article8_2024.csv").open())}
    inc = sorted(float(r["income"]) for r in rows.values() if r["income"])
    cut = inc[len(inc) // 3]
    trees = sorted(float(r["trees_2024"]) for r in rows.values() if r["trees_2024"])
    s = rows[sid]
    heat = {r["id"]: float(r["excess_over_city_c"]) for r in
            csv.DictReader((ROOT / "cities/antwerp/layers/heat_2022_2025.csv").open())}
    lau = {r["lau_id"]: r for r in csv.DictReader((ROOT / "cities/antwerp/layers/art8_official_lau_2021.csv").open())}
    assert float(s["income"]) <= cut
    assert float(s["trees_2024"]) <= trees[len(trees) // 3]
    assert heat[sid] >= 1.0 and int(float(s["population"])) >= 500
    assert lau[f"BE_{sid[:5]}"]["exempt"] == "False"


@pytest.mark.parametrize("city", ["brussels", "antwerp", "ghent", "liege", "charleroi"])
def test_article8_threshold_is_calibrated_by_the_same_run(city):
    """Поправка 25.09.2026: порог слоя ст. 8 брался из манифеста прибора, посчитанного другой
    схемой подбора (Брюссель — LST на 100 м, Антверпен — по одной зелёности), и расходился с
    измерением на 7–8 %. Теперь слой хранит свои входы, и калибровка, пересчитанная из них без
    Earth Engine, обязана дать порог сводки; вердикты обязаны сойтись со счётом тренда."""
    import sys
    sys.path.insert(0, str(ROOT))
    from engine.adapters import ADAPTERS
    from engine.calibrate import calibrate
    S = json.loads((ROOT / f"cities/{city}/layers/article8_2024_summary.json").read_text())
    rows = list(csv.DictReader((ROOT / f"cities/{city}/layers/article8_2024.csv").open()))
    cen = {u.id: u.centroid for u in ADAPTERS[city]().units()}
    table = [{"id": r["id"], "ndvi_b": float(r["ndvi_b"]), "lst_b": float(r["lst_b"]),
              "ndvi_delta": float(r["ndvi_raw"]), "centroid": cen[r["id"]]} for r in rows]
    c = calibrate(table, "ndvi", "ndvi_b", "lst_b")
    assert abs(c.threshold - S["thresholds"]["ndvi"]) < 0.0005, (c.threshold, S["thresholds"]["ndvi"])
    assert all(S["thresholds_unbiased"].values())
    gain = sum(1 for r in rows if r["comparable"] == "True" and r["ndvi_verdict"] == "рост")
    loss = sum(1 for r in rows if r["comparable"] == "True" and r["ndvi_verdict"] == "потеря")
    assert (gain, loss) == (S["trend"]["ndvi_gain_sectors"], S["trend"]["ndvi_loss_sectors"])
    man = json.loads((ROOT / f"cities/{city}/manifest.json").read_text())["layers"]["article8_2024"]
    assert man["threshold"] == S["thresholds"]["ndvi"] and "этого же прогона" in man["method"]


@pytest.mark.parametrize("city", ["brussels", "antwerp", "ghent", "liege", "charleroi"])
def test_article8_sealing_threshold_is_the_same_runs_noise(city):
    """Фаза 2c, пункт 1 (26.09.2026): запечатывание — класс built против тех же 12 мест, что у зелени.
    Эффекты застройки, записанные слоем, и есть нулевое распределение прибора: порог обязан
    воспроизводиться из них, прибор — быть несмещённым, вердикты — следовать порогу, а счёт —
    сходиться со сводкой. Порог прибора из манифеста (другой прогон) сюда не переносится."""
    import sys
    sys.path.insert(0, str(ROOT))
    from engine.calibrate import from_effects
    S = json.loads((ROOT / f"cities/{city}/layers/article8_2024_summary.json").read_text())
    rows = list(csv.DictReader((ROOT / f"cities/{city}/layers/article8_2024.csv").open()))
    c = from_effects("built", [float(r["built_eff"]) for r in rows if r["built_eff"]])
    t = S["thresholds"]["built"]
    assert abs(c.threshold - t) < 5e-5 and c.unbiased and S["thresholds_unbiased"]["built"]
    for r in rows:
        want = ("контроль несопоставим" if r["comparable"] != "True"
                else "рост" if float(r["built_eff"]) > t else "потеря" if float(r["built_eff"]) < -t else "шум")
        assert r["built_verdict"] == want, (r["id"], r["built_eff"], r["built_verdict"])
    up = sum(r["built_verdict"] == "рост" for r in rows)
    down = sum(r["built_verdict"] == "потеря" for r in rows)
    assert (up, down) == (S["trend"]["built_up_sectors"], S["trend"]["built_down_sectors"])
    man = json.loads((ROOT / f"cities/{city}/manifest.json").read_text())["layers"]["article8_2024"]
    assert f"застройка — нулевое распределение по {c.n} единицам" in man["threshold_source"]


def test_article8_sealing_known_answers():
    """Прибор узнаёт то, что известно по документам: Tour et Taxis и Chemin de Fer (Моленбек) —
    стройки 2021–2024, застройка сверх шума; Gare de Formation (Эвере) — сортировочная станция,
    застройки меньше сверх шума, а зелень в шуме (раскрыли, но не озеленили — снос читается так же)."""
    rows = {r["id"]: r for r in csv.DictReader((ROOT / "cities/brussels/layers/article8_2024.csv").open())}
    by_name = {(r["name"], r["commune"]): r for r in rows.values()}
    assert by_name[("TOUR ET TAXIS", "Bruxelles")]["built_verdict"] == "рост"
    assert by_name[("CHEMIN DE FER", "Molenbeek")]["built_verdict"] == "рост"
    g = rows["21006A073"]
    assert g["name"] == "GARE DE FORMATION" and g["built_verdict"] == "потеря" and g["ndvi_verdict"] == "шум"


@pytest.mark.parametrize("city", ["brussels", "antwerp", "ghent", "liege", "charleroi"])
def test_art8_baseline_is_the_official_layer_repackaged(city):
    """Фаза 2c, пункт 4: нулевой замер в форме PBL и файл t8_UEAPolygons по схеме EEA/JRC. Числа не
    пересчитываются — это доли art8_official × площадь зоны; вердикт и прочтения — те же, что в слое.
    GeoPackage: EPSG:3035, MULTIPOLYGON, поля образца Комиссии, lau_id вида lau2024.BE.<код>,
    area_tcc текстом с пятью знаками (как round() в их скрипте)."""
    import sqlite3
    S = json.loads((ROOT / f"cities/{city}/layers/art8_official_2021_summary.json").read_text())
    laus = {f"lau2024.BE.{r['lau_id'][3:]}": r for r in S["laus"]}
    base = list(csv.DictReader((ROOT / f"cities/{city}/layers/art8_baseline_2021.csv").open()))
    assert len(base) == len(laus) + (1 if len(laus) > 1 else 0)
    for b in base:
        if not b["lau_id"]:
            assert b["name"] == f"all {len(laus)} together" and b["exempt"] == str(S["region"]["exempt"])
            continue
        r = laus[b["lau_id"]]
        assert abs(float(b["green_ucuc_ha"]) - 100 * r["green_ucuc"] * r["area_km2_ucuc"]) < 0.01
        assert abs(float(b["canopy_lau_ha"]) - 100 * r["canopy_wvl_all"] * r["area_km2_all"]) < 0.01
        assert abs(float(b["green_ucuc_pct"]) - 100 * r["green_ucuc"]) < 0.006
        assert b["exempt"] == str(r["exempt"]) and b["stable"] == str(r["stable"])
    sens = list(csv.DictReader((ROOT / f"cities/{city}/layers/art8_sensitivity_2021.csv").open()))
    assert len(sens) == 4 * len(laus)
    for x in sens:
        r = laus[x["lau_id"]]
        want = {"official": r["exempt"], "with_arable": r["exempt_with7"], "without_water": r["exempt_no_water"],
                "statbel_sectors": r["exempt_statbel"]}[x["reading"]]
        assert x["exempt"] == ("" if want is None else str(want)), (x["lau_id"], x["reading"])
    for uea, part in (("ucuc", "ucuc"), ("lau", "all")):
        con = sqlite3.connect(ROOT / f"cities/{city}/layers/t8_UEAPolygons_{uea}.gpkg")
        assert con.execute("pragma application_id").fetchone()[0] == 0x47504B47
        assert con.execute("select table_name, column_name, geometry_type_name, srs_id from gpkg_geometry_columns").fetchall() \
            == [("t8_UEAPolygons", "geom", "MULTIPOLYGON", 3035)]
        assert [(c[1], c[2]) for c in con.execute('pragma table_info("t8_UEAPolygons")')] == \
            [("fid", "INTEGER"), ("geom", "MULTIPOLYGON"), ("uea_id", "TEXT"), ("lau_id", "TEXT"), ("area_tcc", "TEXT"), ("area_ugs", "REAL")]
        rows = con.execute('select lau_id, area_tcc, area_ugs, geom from "t8_UEAPolygons"').fetchall()
        con.close()
        assert {r[0] for r in rows} == set(laus)
        for lau_id, tcc, ugs, geom in rows:
            r = laus[lau_id]
            assert isinstance(tcc, str) and abs(float(tcc) - r[f"canopy_wvl_{part}"] * r[f"area_km2_{part}"]) < 1e-5
            assert len(tcc.split(".")[-1]) <= 5 and abs(ugs - r[f"green_{part}"] * r[f"area_km2_{part}"]) < 1e-5
            assert geom[:2] == b"GP" and int.from_bytes(geom[4:8], "little") == 3035
    man = json.loads((ROOT / f"cities/{city}/manifest.json").read_text())["layers"]
    for k in ("art8_baseline_2021", "art8_sensitivity_2021", "t8_UEAPolygons"):
        assert man[k]["threshold"] is None and "порог" in man[k]["threshold_source"]


@pytest.mark.parametrize("city", ["brussels", "antwerp", "ghent", "liege", "charleroi"])
@pytest.mark.parametrize("season", [2025, 2026])
def test_art8_balance_hectares_are_the_same_runs_noise(city, season):
    """Фаза 2c, пункт 2: баланс после базы 2024 в гектарах. Порог каждого класса — нулевое распределение
    этого же прогона: он воспроизводится из эффектов, записанных слоем; вердикты следуют порогу и
    сопоставимости; гектары сверх шума = эффект × площадь; суммы по городу сходятся со сводкой."""
    import sys
    sys.path.insert(0, str(ROOT))
    from engine.calibrate import from_effects
    S = json.loads((ROOT / f"cities/{city}/layers/art8_balance_summary.json").read_text())
    B = S["seasons"][str(season)]
    rows = list(csv.DictReader((ROOT / f"cities/{city}/layers/art8_balance_{season}.csv").open()))
    for k in ("green", "trees", "built"):
        c = from_effects(k, [float(r[f"{k}_eff"]) for r in rows if r[f"{k}_eff"]])
        t = B["thresholds"][k]
        assert abs(c.threshold - t) < 5e-5 and c.unbiased and B["thresholds_unbiased"][k], (k, c.threshold, t)
        lost = gained = 0.0
        for r in rows:
            e = float(r[f"{k}_eff"])
            want = ("контроль несопоставим" if r["comparable"] != "True" else "рост" if e > t else "потеря" if e < -t else "шум")
            assert r[f"{k}_verdict"] == want, (r["id"], k)
            assert abs(float(r[f"{k}_eff_ha"]) - e * float(r["area_ha"])) < 0.006   # га округлены до сотых
            if want == "потеря":
                lost += float(r[f"{k}_eff_ha"])
            elif want == "рост":
                gained += float(r[f"{k}_eff_ha"])
        assert abs(lost - B[k]["lost_ha"]) < 0.06 and abs(gained - B[k]["gained_ha"]) < 0.06
        assert abs(B[k]["net_ha"] - (B[k]["lost_ha"] + B[k]["gained_ha"])) < 0.11
    man = json.loads((ROOT / f"cities/{city}/manifest.json").read_text())["layers"][f"art8_balance_{season}"]
    assert man["threshold"] == B["thresholds"]["green"]
    assert all(w in man["threshold_source"] for w in ("зелень", "крона", "застройка"))


def test_art8_balance_known_answers():
    """Wolvendael (Uccle): буря 9 июля 2024, около сотни деревьев спилено — потеря кроны сверх шума в обоих
    сезонах после базы, как в бюллетенях мониторинга. Parc Forestier — слишком зелёный для подбора: отказ,
    а не вердикт."""
    for season in (2025, 2026):
        rows = {r["id"]: r for r in csv.DictReader((ROOT / f"cities/brussels/layers/art8_balance_{season}.csv").open())}
        w = rows["21016A193"]
        assert w["name"] == "WOLVENDAEL" and w["trees_verdict"] == "потеря" and float(w["trees_eff_ha"]) < -1
        assert rows["21001A982"]["trees_verdict"] == "контроль несопоставим"


@pytest.mark.parametrize("slug,city", [("ninove", "brussels"), ("droogdokkenpark", "antwerp")])
def test_audit_case_thresholds_follow_the_case_scheme(slug, city):
    """Поправка 26.09.2026: дело подбирает контроль по одной зелёности «до», а порог брало у прибора
    (в Брюсселе подбор по зелёности и температуре), классы Dynamic World сравнивались СЫРОЙ разницей
    на следе с порогом эффектов против контроля. Теперь порог каждого прибора — нулевое распределение
    схемы самого дела по той же таблице, классы — против тех же 12 мест. Пересчёт без Earth Engine
    обязан дать то, что записано в деле; порог ряда по сезонам — порог дела.
    Known answer: у Ninove кустарник +0,004 — шум (сырой разницей +0,005 он проходил порог прибора)."""
    import statistics
    import sys
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts/report"))
    from audit_case import DW, landcover, own_thresholds, pool_units
    C = json.loads((ROOT / f"data/registry/cases/{slug}.json").read_text())
    lc = landcover(city, "2017_2024")
    pool = pool_units(city, lc)
    thr = own_thresholds(pool)
    got = {i["key"]: i for i in C["instruments"]}
    by_id = {o["id"]: o for o in pool}
    ctrl = [by_id[c["id"]] for c in C["controls"]]
    fp = lc[f"osm:{C['osm']}"]
    for k in ("ndvi",) + DW:
        assert abs(got[k]["threshold"] - thr[k].threshold) < 5e-5, (k, got[k]["threshold"], thr[k].threshold)
        assert got[k]["significant"] == (abs(got[k]["effect"]) > got[k]["threshold"])
    for k in DW:
        did = (float(fp[f"a_{k}"]) - float(fp[f"b_{k}"])) - statistics.mean(o[k] for o in ctrl)
        assert abs(got[k]["effect"] - did) < 5e-4, (k, got[k]["effect"], did)
    assert C["over_time"]["threshold_audit"] == got["ndvi"]["threshold"]
    assert "схема самого дела" in C["threshold_scheme"]
    if slug == "ninove":
        assert not got["shrub"]["significant"] and got["grass"]["significant"] and got["built"]["significant"]


@pytest.mark.parametrize("city", ["antwerp", "ghent"])
def test_groenkaart_check_reproduces_and_is_aligned(city):
    """Фаза 2c, пункт 5: сверка детектора с Groenkaart Vlaanderen пересчитывается из хранимых слоёв без сети и даёт
    записанное в сводке; растр совмещён с секторами (уровень высокой зелени 2021 и крона WorldCover 2021 по
    секторам коррелируют сильно — при перевёрнутом растре было бы около нуля); пороги карты несмещены."""
    import statistics
    import sys
    sys.path.insert(0, str(ROOT / "scripts/official"))
    from groenkaart_check import analyse
    S = json.loads((ROOT / f"cities/{city}/layers/groenkaart_check_summary.json").read_text())
    R = analyse(city)
    assert R["gk_thresholds"] == S["gk_thresholds"] and all(R["gk_unbiased"].values())
    for pair in ("canopy", "green"):
        for key in ("sensitivity", "specificity", "agreement_when_ours_changed"):
            assert R["pairs"][pair][key] == S["pairs"][pair][key], (pair, key)
    gk = {r["id"]: float(r["high_2021"]) for r in csv.DictReader((ROOT / f"cities/{city}/layers/groenkaart_2018_2024.csv").open())}
    wc = {r["id"]: float(r["wc_trees"]) for r in csv.DictReader((ROOT / f"cities/{city}/layers/worldcover_2021.csv").open()) if r["wc_trees"]}
    ids = [i for i in gk if i in wc]
    assert statistics.correlation([gk[i] for i in ids], [wc[i] for i in ids]) > 0.8


@pytest.mark.parametrize("city,commune", [("ghent", "44021"), ("antwerp", "11002"), ("brussels", "21004")])
def test_tree_register_layer_matches_its_snapshot(city, commune):
    """Фаза 2c, пункт 6: слой по секторам — это снимок реестра, разложенный по секторам той коммуны, которую реестр
    покрывает (сектор другой коммуны — не «0 деревьев», его просто нет); у Гента посадки по годам сходятся со
    сводкой, а «куда шли посадки» — доли, а не выдумка."""
    import gzip
    import io
    T = json.loads((ROOT / f"cities/{city}/layers/trees_register_summary.json").read_text())
    rows = list(csv.DictReader((ROOT / f"cities/{city}/layers/trees_register.csv").open()))
    assert T["commune"] == commune and all(r["id"].startswith(commune) for r in rows)
    snap = list(csv.DictReader(io.TextIOWrapper(gzip.open(ROOT / "data/registry/snapshots" / T["snapshot"]), newline="")))
    assert len(snap) == T["trees"]
    in_commune = collections.Counter(r["sector"] for r in snap if r["sector"].startswith(commune))
    assert {r["id"]: int(r["trees"]) for r in rows if int(r["trees"])} == dict(in_commune)
    if city == "ghent":
        for y, n in T["planted"].items():
            assert sum(int(r[f"planted_{y}"]) for r in rows) == sum(1 for s in snap if s["planted"] == y and s["sector"].startswith(commune))
        assert T["planted"]["2024"] == 2258
        for k in ("least_canopy", "poorest", "hottest"):
            w = T["where"][k]
            assert 0 < w["planted_share"] < 1 and 0 < w["residents_share"] < 1


def test_city_registers_mark_the_named_points():
    """Обзор игроков, пункты 1–3 (27.09.2026): снимок открытых реестров объектов и пометки у названных точек.
    Known answers: у дефибрилляторов Антверпена пробел карты в 500 м (объект по реестру, которого OSM планировщика не
    знал) у 4 из 10 названных и 3 из 10 контрольных — ровно как посчитала облачная сессия независимо; скамейки и
    контейнеры, уже стоящие по реестру в 50 м от названной точки, выводят точку из будущего сравнения."""
    import sys
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "scripts/registry"))
    from engine.registries.points import KINDS, load
    from osm_appearance import official_flags, taken_out
    S = json.loads((ROOT / "data/registry/named_points_antwerp_official_summary.json").read_text())
    aed = S["kinds"]["defibrillator"]
    assert (aed["named"]["map_gap_500m"], aed["control"]["map_gap_500m"]) == (4, 3)
    path = ROOT / "data/registry/named_points_antwerp.json"
    flags = official_flags(path)
    out = {p.id for p in load(path) if taken_out(flags.get(p.id))}
    assert {"ant-pl-benches-01", "ant-pl-recycling-01"} <= out and not any("defibrillators" in i for i in out)
    L = json.loads((ROOT / "data/registry/named_points_liege_official_summary.json").read_text())
    assert L["planner_osm"] is False and L["kinds"]["defibrillator"]["named"]["map_gap_500m"] is None
    idx = sorted((ROOT / "data/registry/snapshots").glob("objects_2*.json"))[-1]
    I = json.loads(idx.read_text())
    ok = [s for s in I["sources"] if "error" not in s]
    assert len(ok) >= 25 and all(k in KINDS for s in ok for k in s["kinds"]) and all(len(s["sha256_16"]) == 16 for s in ok)


def test_appearance_verdict_warns_on_a_map_gap_imbalance():
    """Правило 27.09.2026: разница долей «пробела карты» у названных и контрольных ≥ 20 пунктов — оговорка в вердикте."""
    from engine.registries.points import AppearanceResult
    r = AppearanceResult(kind="toilets", date_before="2026-09-05", date_after="2027-09-05", named_total=20, named_appeared=6,
                         control_total=20, control_appeared=2, gap_named=14, gap_control=6)
    assert "оговорка" in r.verdict() and "сверх дрейфа" in r.verdict()
    r.gap_control = 12
    assert "оговорка" not in r.verdict()
    r.gap_named = r.gap_control = None
    assert r.gap_caution() == ""
