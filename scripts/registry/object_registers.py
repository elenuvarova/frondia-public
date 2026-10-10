#!/usr/bin/env python3
"""
Официальные реестры уличных объектов как второй прибор линии выполнения (обзор игроков, 27.09.2026,
docs/research/2026-09-26-point-objects-players.md, пункты 1–3 «что взять»).

Зачем
─────
Линия выполнения проверяет, появился ли объект в 50 м от точки, названной 5 сентября, — по OSM, чья
карта пополняется сама (урн в Брюсселе ×3,3 за восемь лет). У городов есть свои реестры: у части — с датой
установки. Публичной истории версий нет ни у одного портала, поэтому датированный дифф будет только у
того, кто копит снимки сам — с сегодняшнего дня.

Что делает
──────────
1. Снимок открытых реестров объектов пяти городов — `data/registry/snapshots/objects_<city>_<дата>.csv.gz`
   (источник, вид, id, координаты, дата из реестра и что она значит, статус) и индекс
   `objects_<дата>.json` (адрес, лицензия, число записей, хеш нормализованных строк).
2. Вторая колонка линии выполнения: для каждой названной и контрольной точки — ближайший объект того же вида
   по реестру города, объекты в радиусе проверки (50 м) с их датами.
3. Пометки, где пробел — пробел карты: (а) объект по реестру уже стоит в радиусе проверки точки — появление
   в OSM там будет картографией, а не установкой; (б) в 500 м от точки (радиус обслуживания City Planner)
   стоит объект по реестру, которого OSM, прочитанный планировщиком при выборе точек, не знал в 50 м от
   него — часть «разрыва покрытия» была разрывом карты. (б) — только где сохранился OSM того прогона
   (Антверпен и Брюссель, прогоны 4–5 сентября; копия — `data/registry/planner_existing_<city>.csv.gz`).

Точки, их хеши и дата регистрации не трогаются: всё здесь — рядом с реестром точек, а не в нём.

Запуск:
    .venv/bin/python scripts/registry/object_registers.py
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import subprocess
import sys
import urllib.parse
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.manifest import LayerEntry, Manifest  # noqa: E402

SNAPS = ROOT / "data/registry/snapshots"
AGS = "https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal"
ODS = {"bxl": "https://opendata.brussels.be", "gent": "https://data.stad.gent", "liege": "https://opendata.liege.be",
       "odwb": "https://www.odwb.be"}
WFS = "https://data.mobility.brussels/geoserver"
PLANNER_DATA = ROOT.parent / "public_realm_planner_multicity/frontend/public/data"
PLANNER_KIND = {"benches": "bench", "waste_bins": "waste_basket", "toilets": "toilets", "drinking_water": "drinking_water",
                "bike_parking": "bicycle_parking", "defibrillators": "defibrillator", "dog_areas": "dog_park",
                "fitness_stations": "fitness_station", "playgrounds": "playground", "shelters": "shelter",
                "recycling": "recycling", "bicycle_repair": "bicycle_repair_station", "public_bookcases": "public_bookcase",
                "picnic_tables": "picnic_table"}
LIC_ANT = "Gratis Open Data Licentie (Stad Antwerpen)"
FIT = ("calisthenics", "fitness")

# (city, source key, kind or {category → kind}, fetch spec, id field, date field, what the date means, status field, licence)
SOURCES = [
    ("antwerp", "ant_aed", "defibrillator", ("ags", "portal_publiek11/MapServer/1049"), "Planonnr_toestel", "datum_installatie", "installed", None, LIC_ANT),
    ("antwerp", "ant_papiermand", "waste_basket", ("ags", "portal_publiek1/MapServer/7"), "GISID", "EBDD", "recorded", None, LIC_ANT),
    ("antwerp", "ant_zitmeubilair", "bench", ("ags", "portal_publiek4/MapServer/282"), "Objectcode", None, None, None, LIC_ANT),
    ("antwerp", "ant_wachthuisje", "shelter", ("ags", "portal_publiek4/MapServer/270"), "Objectcode", "Plaats_Dat", "installed", None, LIC_ANT),
    ("antwerp", "ant_fietsenstalling", "bicycle_parking", ("ags", "portal_publiek2/MapServer/145"), "Objectcode", None, None, None, LIC_ANT),
    ("antwerp", "ant_speelterrein", "playground", ("ags", "portal_publiek3/MapServer/229"), "GISID", "BEGINDATUM", "opened", None, LIC_ANT),
    ("antwerp", "ant_buurtsport", {"CATEGORIE": {"calisthenics": "fitness_station", "calisthenicsterrein": "fitness_station", "fitnesszone": "fitness_station"}},
     ("ags", "portal_publiek6/MapServer/629"), "GISID", "BEGINDATUM", "opened", None, LIC_ANT),
    ("antwerp", "ant_hondenloopzone", "dog_park", ("ags", "portal_publiek6/MapServer/622"), "ID", "EBDD", "opened", None, LIC_ANT),
    ("antwerp", "ant_toilet", "toilets", ("ags", "portal_publiek1/MapServer/8"), "ID", "OBDD", "opened", None, LIC_ANT),
    ("antwerp", "ant_drinkfontein", "drinking_water", ("ags", "portal_publiek4/MapServer/265"), "Objectcode", None, None, None, LIC_ANT),
    ("antwerp", "ant_glascontainer", "recycling", ("ags", "portal_publiek1/MapServer/10"), "GISID", "EBDD", "recorded", None, LIC_ANT),
    ("antwerp", "ant_parkmeubilair", {"CATEGORIE": {"bank": "bench", "openbarevuilnisbak": "waste_basket", "tafel": "picnic_table",
                                                   "fietsenstalling": "bicycle_parking"}},
     ("ags", "portal_publiek6/MapServer/680"), "OBJECT_GUID", None, None, None, LIC_ANT),
    ("brussels", "bxl_urbis_furniture", {"topo_type": {"cr3701p": "waste_basket", "cr3901p": "bench"}},
     ("wfs", "bm_urbis_topo", "bm_urbis_topo:street_furniture_point"), "urbis_id", None, None, None,
     "UrbIS, Paradigm / Brussels Mobility (free use, terms not verified)"),
    ("brussels", "bxl_parking_bike", "bicycle_parking", ("wfs", "bm_bike", "bm_bike:assets_parking_bike"), "id", "date_realisation", "installed", "statut",
     "Brussels Mobility (licence not found)"),
    ("brussels", "bxl_aed", "defibrillator", ("ods", "bxl", "defibrillateurs-installes-par-la-ville-de-bruxelles"), None, None, None, None, "CC0 1.0 (Ville de Bruxelles)"),
    ("brussels", "bxl_toilets", "toilets", ("ods", "bxl", "toilettes-urinoirs-publics-openbare-toiletten-urinoirs-vbx"), "ref_id", None, None, None, "CC BY 4.0 (Ville de Bruxelles)"),
    ("brussels", "bxl_water_vivaqua", "drinking_water", ("ods", "bxl", "bornes-d-eau-potable-gerees-par-la-region-drinkwatertappunten-beheerd-door-het-gewest-vivaqua"),
     "id_vivaqua", None, None, None, "CC BY 4.0"),
    ("brussels", "bxl_water_sncb", "drinking_water", ("ods", "bxl", "bornes-eau-potable-gratuite-des-gares-sncb-gratis-drinkwatertappunten-van-nmbs-stations"),
     None, None, None, None, "CC BY 4.0"),
    ("brussels", "bxl_playgrounds", {"type": {"plaine": "playground", "ilot": "playground"}},
     ("ods", "bxl", "aires-de-jeux-et-espaces-sportifs-geres-par-la-ville-de-bruxelles"), "elementid", None, None, "statut", "CC BY 4.0 (Ville de Bruxelles)"),
    ("brussels", "bxl_glass", "recycling", ("ods", "bxl", "bulles-a-verre-glasbollen"), None, None, None, None, "CC BY 4.0 (Bruxelles-Propreté)"),
    ("ghent", "gent_fietsenstallingen", "bicycle_parking", ("ods", "gent", "fietsenstallingen-gent"), "urid", None, None, "status",
     "Modellicentie Gratis Hergebruik (Stad Gent)"),
    ("ghent", "gent_sanitair", "toilets", ("ods", "gent", "publiek-sanitair-gent"), "identifier", None, None, None, "Modellicentie Gratis Hergebruik (Stad Gent)"),
    ("ghent", "gent_drinkwater", "drinking_water", ("ods", "gent", "drinkwaterplekken-gent"), "crmid", None, None, None, "Modellicentie Gratis Hergebruik (Stad Gent)"),
    ("ghent", "gent_speelterreinen", "playground", ("ods", "gent", "speelterreinen-gent"), "urid", None, None, None, "Modellicentie Gratis Hergebruik (Stad Gent)"),
    ("ghent", "gent_buurtsport", {"sport": "fitness"}, ("ods", "gent", "infrastructuur-buurtsport-gent"), "gentid", None, None, "status",
     "Modellicentie Gratis Hergebruik (Stad Gent)"),
    ("liege", "liege_aed", "defibrillator", ("ods", "odwb", "defibrillateurs"), "gid", "created", "recorded", None, "CC BY (Ville de Liège, ODWB)"),
    ("liege", "liege_arceaux", "bicycle_parking", ("ods", "liege", "arceaux-velos"), None, "created", "recorded", None, "CC BY (Ville de Liège)"),
    ("liege", "liege_velocite_box", "bicycle_parking", ("ods", "liege", "velocite-box-velos"), None, "commissioning_date", "installed", None, "CC BY (Ville de Liège)"),
    ("liege", "liege_toilettes", "toilets", ("ods", "liege", "toilettes-publiques"), None, None, None, None, "CC BY (Ville de Liège)"),
    ("liege", "liege_verre", "recycling", ("ods", "liege", "bulles-a-verre"), None, None, None, None, "CC BY (Ville de Liège)"),
    ("liege", "liege_textile", "recycling", ("ods", "liege", "bulles-textile"), None, None, None, None, "CC BY (Ville de Liège)"),
]


def curl_json(url: str, tries: int = 4):
    """A portal now and then answers with a cut-off body: fetch again rather than trust a partial page."""
    for i in range(tries):
        out = subprocess.run(["curl", "-sS", "--fail", "--retry", "5", "--retry-all-errors", "--retry-delay", "10", "--max-time", "300", url],
                             check=True, capture_output=True).stdout
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            if i == tries - 1:
                raise


def centroid(geom: dict) -> tuple[float, float] | None:
    t, c = geom.get("type"), geom.get("coordinates")
    if t == "Point":
        return c[0], c[1]
    pts = []
    def walk(x):
        if isinstance(x, (list, tuple)) and x and isinstance(x[0], (int, float)):
            pts.append(x)
        elif isinstance(x, (list, tuple)):
            for y in x:
                walk(y)
    walk(c)
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)) if pts else None


def fetch_ags(layer: str) -> list[tuple[dict, tuple[float, float]]]:
    out, last = [], -1
    while True:
        q = urllib.parse.urlencode({"where": f"OBJECTID>{last}", "outFields": "*", "orderByFields": "OBJECTID", "returnGeometry": "true",
                                    "outSR": "4326", "f": "json", "resultRecordCount": "1000"})
        feats = curl_json(f"{AGS}/{layer}/query?{q}").get("features", [])
        if not feats:
            return out
        for f in feats:
            g = f.get("geometry") or {}
            if "x" in g:
                xy = (g["x"], g["y"])
            elif "rings" in g:
                ring = g["rings"][0]
                xy = (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring))
            else:
                continue
            out.append((f["attributes"], xy))
        last = feats[-1]["attributes"]["OBJECTID"]


def fetch_wfs(ws: str, typename: str) -> list[tuple[dict, tuple[float, float]]]:
    q = urllib.parse.urlencode({"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": typename,
                                "outputFormat": "application/json", "srsName": "EPSG:4326", "count": "100000"})
    fc = curl_json(f"{WFS}/{ws}/wfs?{q}")
    out = []
    for f in fc["features"]:
        xy = centroid(f.get("geometry") or {})
        if xy:
            if xy[0] > 45:            # a GeoServer answering lat, lon for EPSG:4326: Brussels is lon 4, lat 50
                xy = (xy[1], xy[0])
            out.append((f["properties"], xy))
    return out


def fetch_ods(portal: str, dataset: str) -> list[tuple[dict, tuple[float, float]]]:
    rows = curl_json(f"{ODS[portal]}/api/explore/v2.1/catalog/datasets/{dataset}/exports/json")
    out = []
    for r in rows:
        xy = None
        for k in ("geo_point_2d", "geopoint", "geo_point", "coordonnees_geographiques"):
            p = r.get(k)
            if isinstance(p, dict) and p.get("lon") is not None:
                xy = (p["lon"], p["lat"])
                break
        if xy is None:
            for k in ("geometry", "geo_shape"):
                g = r.get(k)
                if isinstance(g, dict):
                    g = g.get("geometry", g)
                    xy = centroid(g)
                    if xy:
                        break
        if xy:
            out.append((r, xy))
    return out


def as_date(v) -> str:
    if v in (None, "", 0):
        return ""
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v / 1000, tz=timezone.utc).date().isoformat()
    s = str(v)
    return s[:10] if len(s) >= 10 and s[4] == "-" else s


def kind_of(kind, props: dict) -> str | None:
    if isinstance(kind, str):
        return kind
    (field, rule), = kind.items()
    val = str(props.get(field) or "").strip().lower()
    if isinstance(rule, dict):
        return rule.get(val)
    return "fitness_station" if any(w in val for w in FIT) else None     # a substring rule (Ghent's sport field)


def snapshot(today: str) -> dict:
    SNAPS.mkdir(parents=True, exist_ok=True)
    index, by_city = {"date": today, "sources": []}, {}
    for city, key, kind, spec, idf, datef, meaning, statusf, licence in SOURCES:
        try:
            rows = fetch_ags(spec[1]) if spec[0] == "ags" else fetch_wfs(spec[1], spec[2]) if spec[0] == "wfs" else fetch_ods(spec[1], spec[2])
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            print(f"  {key}: не скачался ({type(e).__name__}) — пропущен, в индексе отмечен")
            index["sources"].append({"city": city, "key": key, "error": type(e).__name__})
            continue
        norm = []
        for props, (lon, lat) in rows:
            k = kind_of(kind, props)
            if not k:
                continue
            rid = str(props.get(idf)) if idf and props.get(idf) not in (None, "") else \
                hashlib.sha1(f"{key}:{lon:.6f}:{lat:.6f}".encode()).hexdigest()[:12]
            norm.append({"source": key, "kind": k, "id": rid, "lon": round(lon, 6), "lat": round(lat, 6),
                         "date": as_date(props.get(datef)) if datef else "", "date_means": meaning or "",
                         "status": str(props.get(statusf) or "") if statusf else ""})
        norm.sort(key=lambda r: (r["kind"], r["id"]))
        h = hashlib.sha256("\n".join(json.dumps(r, sort_keys=True) for r in norm).encode()).hexdigest()[:16]
        by_city.setdefault(city, []).extend(norm)
        kinds = {}
        for r in norm:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        index["sources"].append({"city": city, "key": key, "records": len(norm), "kinds": kinds, "dated": sum(1 for r in norm if r["date"]),
                                 "date_means": meaning, "licence": licence, "spec": list(spec), "sha256_16": h})
        print(f"  {city:<9} {key:<22} {len(norm):>6}  {kinds}  с датой {sum(1 for r in norm if r['date'])}")
    for city, rows in by_city.items():
        with gzip.open(SNAPS / f"objects_{city}_{today}.csv.gz", "wt", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["source", "kind", "id", "lon", "lat", "date", "date_means", "status"], lineterminator="\n")
            w.writeheader(); w.writerows(rows)
    (SNAPS / f"objects_{today}.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))
    return by_city


def planner_existing(city: str) -> list[dict]:
    """What OSM the planner read when it named the points (runs of 4–5 Sep 2026), copied once into the project."""
    dest = ROOT / f"data/registry/planner_existing_{city}.csv.gz"
    if not dest.exists():
        rows = []
        for folder, k in PLANNER_KIND.items():
            f = PLANNER_DATA / city / folder / "existing_assets.geojson"
            if not f.exists():
                continue
            for feat in json.loads(f.read_text())["features"]:
                xy = centroid(feat["geometry"])
                if xy:
                    rows.append({"kind": k, "lon": round(xy[0], 6), "lat": round(xy[1], 6)})
        if not rows:
            return []
        with gzip.open(dest, "wt", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["kind", "lon", "lat"], lineterminator="\n")
            w.writeheader(); w.writerows(rows)
    return list(csv.DictReader(io.TextIOWrapper(gzip.open(dest), newline="")))


def dist_m(a, b) -> float:
    kx = 111320 * math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * kx, (a[1] - b[1]) * 110540)


def check(city: str, objects: list[dict], today: str) -> dict | None:
    pts = json.loads((ROOT / f"data/registry/named_points_{city}.json").read_text())
    by_kind = {}
    for o in objects:
        by_kind.setdefault(o["kind"], []).append(o)
    osm = {}
    for o in planner_existing(city):
        osm.setdefault(o["kind"], []).append((float(o["lon"]), float(o["lat"])))
    have_osm = bool(osm)
    rows = []
    for p in pts:
        offic = by_kind.get(p["kind"])
        if not offic:
            continue
        here = (p["lon"], p["lat"])
        d = sorted(((dist_m(here, (o["lon"], o["lat"])), o) for o in offic), key=lambda t: t[0])
        at = [o for m, o in d if m <= p["radius_m"]]
        near = [o for m, o in d if m <= 500]
        gap = None
        if have_osm:
            known = osm.get(p["kind"], [])
            gap = sum(1 for o in near if not any(dist_m((o["lon"], o["lat"]), k) <= 50 for k in known))
        dates = sorted(o["date"] for o in at if o["date"])
        rows.append({"point": p["id"], "kind": p["kind"], "role": p["role"], "registered_at": p["registered_at"],
                     "nearest_official_m": round(d[0][0]) if d else "", "official_at_point": len(at),
                     "official_at_point_dates": ";".join(dates),
                     "official_at_point_after_registration": sum(1 for x in dates if x > p["registered_at"]),
                     "official_within_500m": len(near), "not_in_planner_osm_within_500m": "" if gap is None else gap,
                     "sources": ";".join(sorted({o["source"] for o in near}))})
    if not rows:
        return None
    out = ROOT / f"data/registry/named_points_{city}_official.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    summ = {"city": city, "date": today, "checked_points": len(rows), "planner_osm": have_osm, "kinds": {}}
    for k in sorted({r["kind"] for r in rows}):
        rk = [r for r in rows if r["kind"] == k]
        e = {"points": len(rk)}
        for role in ("named", "control"):
            rr = [r for r in rk if r["role"] == role]
            e[role] = {"n": len(rr), "official_at_point": sum(1 for r in rr if r["official_at_point"]),
                       "map_gap_500m": (sum(1 for r in rr if r["not_in_planner_osm_within_500m"] not in ("", 0))
                                        if have_osm else None)}
        summ["kinds"][k] = e
    (ROOT / f"data/registry/named_points_{city}_official_summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1))
    return summ


def main() -> int:
    today = date.today().isoformat()
    print("снимки реестров объектов…")
    by_city = snapshot(today)
    for city, objs in by_city.items():
        s = check(city, objs, today)
        if not s:
            continue
        print(f"\n{city}: точек сверено {s['checked_points']}, OSM планировщика {'есть' if s['planner_osm'] else 'нет'}")
        for k, e in s["kinds"].items():
            n, c = e["named"], e["control"]
            g = lambda x: "—" if x["map_gap_500m"] is None else f"{x['map_gap_500m']}/{x['n']}"
            print(f"  {k:<18} названные: объект по реестру в радиусе {n['official_at_point']}/{n['n']}, пробел карты в 500 м "
                  f"{g(n)} · контрольные: {c['official_at_point']}/{c['n']}, {g(c)}")
        m = Manifest.read(city)
        m.add(LayerEntry(
            layer="named_points_official", computed=today, n_units=s["checked_points"],
            measures="вторая колонка линии выполнения: объекты того же вида по реестру города у названных и контрольных "
                     "точек — в радиусе проверки (50 м) с датами и в 500 м; «пробел карты» — объект по реестру, которого "
                     "OSM планировщика не знал в 50 м",
            unit="объекты; метры",
            method="снимок открытых реестров города (scripts/registry/object_registers.py), расстояние от точки; "
                   "OSM планировщика — existing_assets прогонов 4–5 сентября 2026",
            source="; ".join(sorted({x[8] for x in SOURCES if x[0] == city})),
            threshold_source="линия выполнения, не изменение: порога нет — пометка говорит, что уже стоит, а не какой эффект",
            limits=["реестры покрывают только объекты города; частные и чужие (регион, транспорт) — не везде",
                    "дата в реестре бывает датой записи в ГИС, а не установки: смысл даты записан у каждого источника",
                    "пробел карты считается только где сохранился OSM прогона планировщика (Антверпен, Брюссель)"]))
        m.write()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
