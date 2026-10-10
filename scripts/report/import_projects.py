#!/usr/bin/env python3
"""Импорт слоёв и точек из соседних проектов Елены в городской пакет.

Этап 3 архитектуры: пакет как формат обмена. Соседние репозитории считают своё,
экспортёр приводит результат к одной единице (сектор Statbel) и регистрирует
в манифесте — иначе по нашему же правилу слой в отчёт не попадает.

Что берётся:

  **City Planner** (`public_realm_planner_multicity`) — кандидаты размещения
  8 типов точечных объектов по Антверпену: балл, разрыв покрытия, индекс
  справедливости, ранг. Идут в `cities/antwerp/points/<тип>.geojson`.
  Это ответ на вопрос «что и где стоит сделать», которого у нас не было.

  **Neighbourhood Fit Score** (`neighbourhood_fit_score`) — балл пригодности
  724 брюссельских секторов по трём сценариям (семья, удалёнка, пожилые) с
  разбивкой по 14 сервисам. Идёт в `cities/brussels/layers/fit_score.csv`.
  Плюс 4533 предложения улучшений с координатами → `points/improvements.geojson`.

⚠️ Границы, которые печатаются рядом со слоями:
  · балл пригодности и балл размещения — НЕ измерение изменений: это состояние
    и рекомендация. Смешивать их с эффектом нельзя, единица общая, вопрос разный;
  · точки кандидатов сами по себе ничего не доказывают — они становятся
    доказательством, только если названы ДО работ (линия выполнения);
  · POI-слои OSM неполны неравномерно: у Fit Score это состояние карты, а не города.

  **SpotFinder** (`spot-finder-geo`) — расстояние от сектора до ближайшей пекарни, кофейни
  и кондитерской по Антверпену (метры, OSM) и число таких заведений в секторе. Берётся взгляд
  жителя — «далеко ли до пекарни», а не бизнес-оценка «есть ли место для ещё одной»: Frondia
  читает город глазами жителя и ведомства. Идёт в `cities/antwerp/layers/shops_access.csv`.

    .venv/bin/python scripts/report/import_projects.py --what planner --city antwerp
    .venv/bin/python scripts/report/import_projects.py --what fitscore --city brussels
    .venv/bin/python scripts/report/import_projects.py --what spotfinder --city antwerp
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.manifest import LayerEntry, Manifest  # noqa: E402

HOME = Path.home() / "git projects"
# the pipelines of the merged projects live in this repository (pipelines/README.md); a result they
# wrote here comes first, the sibling repository's copy is the fallback
PIPELINES = Path(__file__).resolve().parents[2] / "pipelines"


def source(here: Path, sibling: Path) -> Path:
    return here if here.exists() else sibling


PLANNER = source(PIPELINES / "city_planner" / "frontend" / "public" / "data",
                 HOME / "public_realm_planner_multicity" / "frontend" / "public" / "data")
FITSCORE = HOME / "neighbourhood_fit_score" / "backend" / "data.sqlite"
SPOTFINDER = source(PIPELINES / "spotfinder" / "backend" / "data", HOME / "spot-finder-geo" / "backend" / "data")
SPOT_CITY = {"antwerp": "antwerpen", "brussels": "brussels", "ghent": "ghent",
             "liege": "liege", "charleroi": "charleroi"}
SHOP_TYPES = ["bakery", "cafe", "confectionery"]

ASSET_RU = {"toilets": "туалеты", "benches": "скамейки", "waste_bins": "урны",
            "drinking_water": "питьевые фонтанчики", "bike_parking": "велопарковки",
            "defibrillators": "дефибрилляторы", "fitness_stations": "тренажёры",
            "dog_areas": "площадки для собак", "playgrounds": "детские площадки",
            "shelters": "навесы и укрытия", "recycling": "контейнеры для раздельного сбора",
            "bicycle_repair": "велоремонтные станции", "public_bookcases": "уличные книжные шкафы",
            "picnic_tables": "столы для пикника"}
SCEN_RU = {"family": "семья с детьми", "remote": "удалённая работа", "senior": "пожилые"}


def osm_line(prov: dict | None) -> str:
    """Where a run's OpenStreetMap came from, as the pipeline recorded it (added 27 Sep 2026): a Geofabrik
    extract with the data's own timestamp, or live Overpass with the day of the query."""
    if not prov:
        return "источник OSM при прогоне не записан"
    if prov.get("file"):
        return (f"OSM из выгрузки Geofabrik {prov['file']}, данные на "
                f"{prov.get('osm_timestamp') or 'неизвестную дату'}")
    return f"OSM из живого Overpass ({prov.get('overpass')}), запрос {prov.get('fetched')}"


def import_planner(city: str) -> int:
    src = PLANNER / city
    if not src.exists():
        print(f"нет данных планировщика для {city}: {src}", file=sys.stderr)
        return 1
    out_dir = Path(f"cities/{city}/points")
    out_dir.mkdir(parents=True, exist_ok=True)
    m = Manifest.read(city)
    today = date.today().isoformat()
    total = 0
    for asset_dir in sorted(p for p in src.iterdir() if p.is_dir()):
        asset = asset_dir.name
        sel = asset_dir / "selected.geojson"
        rep = asset_dir / "report.json"
        if not sel.exists() or not rep.exists():
            continue
        gj = json.loads(sel.read_text())
        r = json.loads(rep.read_text())
        # a re-import of the same points keeps the day they were first named: the execution line checks
        # appearance after that day, so re-dating unchanged points would move their registration
        named_at = today
        prev = out_dir / f"{asset}.geojson"
        if prev.exists():
            old = json.loads(prev.read_text())
            same = [f["geometry"]["coordinates"] for f in old["features"]] == \
                   [f["geometry"]["coordinates"] for f in gj["features"]]
            if same and old.get("properties", {}).get("named_at"):
                named_at = old["properties"]["named_at"]
        for f in gj["features"]:
            f["properties"]["asset"] = asset
            f["properties"]["named_at"] = named_at
        gj["properties"] = {"city": city, "asset": asset, "solver": r.get("solver"),
                            "service_radius_m": r.get("service_radius_m"),
                            "coverage_before": r.get("coverage_before"),
                            "coverage_after": r.get("coverage_after"),
                            # coverage after each rank, 0…budget: the atlas's "what if N more?" reads it
                            "coverage_steps": r.get("coverage_steps"),
                            "n_existing_assets": r.get("n_existing_assets"),
                            "n_candidates_pool": r.get("n_candidates_pool"),
                            "osm_source": r.get("osm_source"),
                            "named_at": named_at}
        (out_dir / f"{asset}.geojson").write_text(json.dumps(gj, ensure_ascii=False))
        n = len(gj["features"])
        total += n
        m.add(LayerEntry(
            layer=f"points_{asset}", computed=today, n_units=n,
            measures=f"кандидаты размещения: {ASSET_RU.get(asset, asset)} — где объект закроет "
                     f"наибольший разрыв покрытия с учётом депривации",
            unit="балл размещения 0–100",
            method=f"решатель {r.get('solver')}, радиус обслуживания {r.get('service_radius_m'):.0f} м, "
                   f"пул кандидатов {r.get('n_candidates_pool')}, покрытие "
                   f"{r.get('coverage_before'):.3f} → {r.get('coverage_after'):.3f}",
            source="City Planner (public_realm_planner_multicity): OSM объекты и точки спроса, "
                   f"сетка спроса, депривация по секторам; {osm_line(r.get('osm_source'))}",
            threshold=None,
            threshold_source="порога нет: это рекомендация, а не измерение изменения",
            limits=["рекомендация, а не эффект: доказательством точка становится только "
                    "после проверки появления, названной до работ",
                    "полнота OSM неравномерна: существующие объекты — состояние карты, не города",
                    "покрытие считается по сетке спроса, а не по населению сектора"]))
        print(f"  + points_{asset:<18} {n} точек · покрытие "
              f"{r.get('coverage_before'):.3f} → {r.get('coverage_after'):.3f}")
    m.write()      # без записи манифест правился бы только в памяти
    print(f"→ cities/{city}/points/ · всего точек {total} · слоёв в манифесте {len(m.layers)}")
    return 0


FIT_SERVICES = ["cafe", "childcare", "convenience", "gp", "hospital", "library", "park", "pharmacy",
                "playground", "restaurant", "school", "sport", "supermarket", "transit"]


FIT_TRANSIT = {  # the operator each city's Fit Score reads (pipelines/neighbourhood_fit_score/pipeline/config.py)
    "delijn": ("De Lijn", "GTFS De Lijn (Mobility Database mdb-684)", "трамвай и автобус De Lijn"),
    "tec": ("TEC", "GTFS TEC (opendata.tec-wl.be)", "автобус, трамвай и лёгкое метро TEC"),
}
FIT_CITY_TRANSIT = {"antwerp": "delijn", "ghent": "delijn", "liege": "tec", "charleroi": "tec"}


def fitscore_entry(city: str, computed: str, n: int, prov: dict) -> LayerEntry:
    """The manifest entry of a Fit Score computed by the pipeline for one city: its own operator, its own
    service day and feed, and where its OSM came from, as steps 03 and 04 recorded them in provenance.json.
    Before 27 Sep 2026 the steps recorded nothing, so a missing day is said to be missing."""
    op, feed, modes = FIT_TRANSIT[prov.get("transit") or FIT_CITY_TRANSIT[city]]
    g = prov.get("gtfs") or {}
    day = g.get("service_day")
    day_txt = (f"в понедельник {day[6:8]}.{day[4:6]}.{day[:4]}" if day
               else "в понедельник с наибольшим числом рейсов в ленте (день при прогоне не записан)")
    feed_txt = f"{feed}, лента от {g['feed_start_date'][6:8]}.{g['feed_start_date'][4:6]}.{g['feed_start_date'][:4]}" \
        if g.get("feed_start_date") else feed
    osm = []
    if prov.get("osm_pois"):
        osm.append(f"точки: {osm_line(prov['osm_pois'])}")
    if prov.get("osm_graph"):
        osm.append(f"граф улиц: {osm_line(prov['osm_graph'])}")
    return LayerEntry(
        layer="fit_score", computed=computed, n_units=n,
        measures="балл пригодности сектора для сценария жизни: семья с детьми, удалённая работа, пожилые",
        unit="балл 0–100 и процентиль",
        method=f"доступность {len(FIT_SERVICES)} сервисов в пешей доступности по графу улиц OSM, взвешенная по "
               f"сценарию; транспорт — частота отправлений {op} {day_txt} (пик 7–9, день 6–22)",
        source=f"Neighbourhood Fit Score (neighbourhood_fit_score, конвейер 02–05 --city {city}): OSM Belgium, "
               f"секторы и население Statbel 2024, {feed_txt}; "
               + ("; ".join(osm) if osm else osm_line(None)),
        threshold=None,
        threshold_source="порога нет: это состояние, а не изменение против контроля",
        limits=["состояние, а не эффект: с измерением изменений не смешивать",
                "полнота OSM неравномерна — балл отражает карту, а не только город",
                "сценарные веса — редакционное решение автора, а не измерение",
                f"поезда NMBS в транспорт не входят, только {modes} (в Брюсселе — только STIB)"])


def import_fitscore_csv(city: str) -> int:
    """Fit Score, посчитанный конвейером соседнего проекта для другого города (26.09.2026: Антверпен,
    те же 458 секторов, что в пакете Frondia; транспорт — GTFS De Lijn). Та же схема слоя, что у Брюсселя:
    балл 0–100, процентиль внутри города, доступность 14 сервисов по сценарию."""
    src = source(PIPELINES / "neighbourhood_fit_score" / "pipeline" / "data" / "processed" / city / "scores.csv",
                 HOME / "neighbourhood_fit_score" / "backend" / "pipeline" / "data" / "processed" / city / "scores.csv")
    if not src.exists():
        print(f"нет расчёта Fit Score для {city}: {src}", file=sys.stderr)
        return 1
    rows = list(csv.DictReader(src.open()))
    layers = Path(f"cities/{city}/layers")
    layers.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    with (layers / "fit_score.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "scenario", "score", "percentile", *FIT_SERVICES])
        for r in rows:
            b = json.loads(r["breakdown"])
            w.writerow([r["sector_id"], r["scenario"], round(float(r["score"]) * 100, 1), r["percentile"],
                        *[b.get(k, "") for k in FIT_SERVICES]])
    scen = {r["scenario"] for r in rows}
    print(f"  + fit_score.csv · {len(rows)} строк ({len(rows) // len(scen)} секторов × {len(scen)} сценария)")
    prov_path = src.parent / "provenance.json"
    prov = json.loads(prov_path.read_text()) if prov_path.exists() else {}
    m = Manifest.read(city)
    m.add(fitscore_entry(city, today, len(rows), prov))
    m.write()
    print(f"→ cities/{city}/ · слоёв в манифесте {len(m.layers)}")
    return 0


def import_fitscore(city: str) -> int:
    if city != "brussels":
        return import_fitscore_csv(city)
    if not FITSCORE.exists():
        print(f"нет базы Fit Score: {FITSCORE}", file=sys.stderr)
        return 1
    con = sqlite3.connect(FITSCORE)
    layers = Path(f"cities/{city}/layers")
    points = Path(f"cities/{city}/points")
    layers.mkdir(parents=True, exist_ok=True)
    points.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    rows = list(con.execute(
        "select sector_id, scenario, score, percentile, breakdown from sector_score order by sector_id, scenario"))
    services = sorted(json.loads(rows[0][4]))
    out = layers / "fit_score.csv"
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "scenario", "score", "percentile", *services])
        for sid, scen, score, pct, br in rows:
            b = json.loads(br)
            w.writerow([sid, scen, score, pct, *[b.get(s, "") for s in services]])
    scen_n = len({r[1] for r in rows})
    print(f"  + fit_score.csv · {len(rows)} строк ({len(rows) // scen_n} секторов × {scen_n} сценария)")

    imp = list(con.execute(
        "select sector_id, scenario, rank, title, category, score_delta, from_score, to_score, "
        "suggested_lat, suggested_lng from improvement where suggested_lat is not null"))
    feats = []
    for sid, scen, rank, title, cat, delta, frm, to, lat, lng in imp:
        feats.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lng, lat]},
                      "properties": {"sector_id": sid, "scenario": scen, "rank": rank, "title": title,
                                     "category": cat, "score_delta": delta, "from_score": frm,
                                     "to_score": to, "named_at": today}})
    (points / "improvements.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": feats,
                    "properties": {"city": city, "source": "neighbourhood_fit_score", "named_at": today}},
                   ensure_ascii=False))
    print(f"  + improvements.geojson · {len(feats)} предложений")

    m = Manifest.read(city)
    m.add(LayerEntry(
        layer="fit_score", computed=today, n_units=len(rows),
        measures="балл пригодности сектора для сценария жизни: семья с детьми, удалённая работа, пожилые",
        unit="балл 0–100 и процентиль",
        method=f"доступность {len(services)} сервисов в пешей доступности, взвешенная по сценарию; "
               "разбивка по каждому сервису сохранена",
        source="Neighbourhood Fit Score (neighbourhood_fit_score): OSM POI + секторы Statbel",
        threshold=None,
        threshold_source="порога нет: это состояние, а не изменение против контроля",
        limits=["состояние, а не эффект: с измерением изменений не смешивать",
                "полнота OSM неравномерна — балл отражает карту, а не только город",
                "сценарные веса — редакционное решение автора, а не измерение"]))
    m.add(LayerEntry(
        layer="points_improvements", computed=today, n_units=len(feats),
        measures="предложения улучшений по секторам: какого сервиса не хватает и насколько вырастет балл",
        unit="прирост балла",
        method="для каждого сектора и сценария — сервисы с наибольшим дефицитом, координата предложена",
        source="Neighbourhood Fit Score, таблица improvement",
        threshold=None,
        threshold_source="порога нет: это рекомендация, а не измерение",
        limits=["координата предложения приблизительная: центр дефицита, а не участок",
                "рекомендация становится проверяемой, только если зафиксирована до работ"]))
    m.write()
    print(f"→ cities/{city}/ · слоёв в манифесте {len(m.layers)}")
    return 0


def import_spotfinder(city: str) -> int:
    src = SPOTFINDER / f"{SPOT_CITY.get(city, city)}.geojson"
    if not src.exists():
        print(f"нет данных SpotFinder для {city}: {src}", file=sys.stderr)
        return 1
    feats = json.loads(src.read_text())["features"]
    prov_path = PIPELINES / "spotfinder" / "pipeline" / "data" / f"{SPOT_CITY.get(city, city)}_osm_source.json"
    spot_prov = json.loads(prov_path.read_text()) if src.is_relative_to(PIPELINES) and prov_path.exists() else None
    # SpotFinder clips by a box, so its file can carry neighbouring municipalities' sectors: only the
    # city's own units go into the bundle (for Ghent the box holds 474 sectors, the city 201)
    from engine.adapters import ADAPTERS
    own = {u.id for u in ADAPTERS[city]().units()}
    extra = sum(1 for f in feats if f["properties"]["unit_id"] not in own)
    feats = [f for f in feats if f["properties"]["unit_id"] in own]
    if extra:
        print(f"  outside {city}: {extra} sectors left out")
    layers = Path(f"cities/{city}/layers")
    layers.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    out = layers / "shops_access.csv"
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", *[f"{t}_m" for t in SHOP_TYPES], *[f"{t}_in_sector" for t in SHOP_TYPES]])
        for f in feats:
            p = f["properties"]
            w.writerow([p["unit_id"], *[round(float(p[f"gap_{t}"]), 1) for t in SHOP_TYPES],
                        *[int(p[f"comp_{t}"]) for t in SHOP_TYPES]])
    print(f"  + shops_access.csv · {len(feats)} секторов")
    m = Manifest.read(city)
    m.add(LayerEntry(
        layer="shops_access", computed=today, n_units=len(feats),
        measures="расстояние от сектора до ближайшей пекарни, кофейни и кондитерской и их число в секторе",
        unit="метры и число заведений",
        method="ближайшее заведение каждого типа от сектора по объектам OSM (SpotFinder, pipeline/compute.py, "
               "поле gap_<тип>); бизнес-оценка SpotFinder opp_<тип> сознательно не взята",
        source=f"SpotFinder (spot-finder-geo): OSM, секторы Statbel; {osm_line(spot_prov)}",
        threshold=None,
        threshold_source="порога нет: это состояние, а не изменение против контроля",
        limits=["состояние, а не эффект: с измерением изменений не смешивать",
                "полнота OSM неравномерна — расстояние отражает карту, а не только город",
                "расстояние по прямой, а не по улицам"]))
    m.write()
    print(f"→ cities/{city}/ · слоёв в манифесте {len(m.layers)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--what", required=True, choices=["planner", "fitscore", "spotfinder", "all"])
    ap.add_argument("--city", default="antwerp")
    args = ap.parse_args()
    if args.what in ("planner", "all"):
        print(f"City Planner → пакет {args.city}")
        import_planner(args.city)
    if args.what in ("fitscore", "all"):
        c = args.city if args.what == "fitscore" else "brussels"
        print(f"Neighbourhood Fit Score → пакет {c}")
        import_fitscore(c)
    if args.what in ("spotfinder", "all"):
        print(f"SpotFinder → пакет {args.city}")
        import_spotfinder(args.city)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
