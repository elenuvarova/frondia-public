"""Первые настоящие записи предрегистрации — из проектов Beliris в статусе «в проекте».

След фиксируется ДО работ и ДО измерения: либо собственный полигон Beliris
(`mapShapes` на карте проекта — геометрия заказчика, ступень 2 правила следа),
либо именованный парк OSM ≥ 1 га с прямым совпадением по названию (ступень 1).
Совпадения «по близости» не берутся: точка Beliris рядом с чужим парком — не след.

Каждая запись несёт ОЖИДАЕМЫЙ исход, записанный до измерения: у реставрации
ожидание «NDVI не изменится», у нового квартала на фрише — «потеря зелени».
Проект, где работы уже идут (`en_execution`), контракт отвергает — это печатается
как отказ, не как запись.

Запуск: python scripts/registry/preregister_beliris.py  → data/registry/preregistered.json
"""
from __future__ import annotations
import json, sys, urllib.request, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.registries.preregistration import register, load, save, REGISTRY

BELIRIS = json.load(open("data/registry/beliris_projects.json"))
PARKS = json.load(open("data/perimeters/parks_brussels.geojson"))["features"]
TODAY = "2026-09-02"

def beliris_polygon(shape):
    ring = [[float(s.split(",")[1]), float(s.split(",")[0])] for s in shape]   # "lat,lon" → [lon, lat]
    if ring[0] != ring[-1]: ring.append(ring[0])
    return {"type": "Polygon", "coordinates": [ring]}

def osm_park(name_part):
    for f in PARKS:
        if name_part.lower() in (f["properties"].get("name") or "").lower():
            return f
    return None

def project(title_part):
    for p in BELIRIS:
        if title_part.lower() in p["cleanTitle"].lower():
            return p
    raise KeyError(title_part)

HOSTS = ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter")

def _overpass(q):
    """Запрос к Overpass с обходом зеркал. Исключение, если все недоступны."""
    last = None
    for host in HOSTS:
        try:
            req = urllib.request.Request(host, data=urllib.parse.urlencode({"data": q}).encode(),
                                         headers={"User-Agent": "frondia-preregistration/0.1 (research)"})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            last = e
    raise last

def overpass_relation(rel_id):
    """Мультиполигон OSM по id отношения: внешние контуры (role=outer) берутся по id
    участников — запрос `way(r:…)` на зеркалах отдаёт пусто. None при сетевой ошибке."""
    try:
        rel = next(e for e in _overpass(f"[out:json][timeout:40];relation({rel_id});out body;")["elements"]
                   if e["type"] == "relation")
        outer = [m["ref"] for m in rel["members"] if m["type"] == "way" and m["role"] == "outer"]
        ways = [[[n["lon"], n["lat"]] for n in e["geometry"]]
                for e in _overpass(f"[out:json][timeout:40];way(id:{','.join(map(str, outer))});out geom;")["elements"]
                if e["type"] == "way" and "geometry" in e]
        rings, pool = [], [w for w in ways if len(w) > 1]
        while pool:                                   # склейка незамкнутых сегментов в кольца
            ring = pool.pop(0)
            while ring[0] != ring[-1] and pool:
                for i, w in enumerate(pool):
                    if w[0] == ring[-1]: ring += w[1:]; pool.pop(i); break
                    if w[-1] == ring[-1]: ring += w[::-1][1:]; pool.pop(i); break
                else:
                    break
            if ring[0] == ring[-1] and len(ring) > 3:
                rings.append(ring)
        if not rings:
            print("  overpass: контуры не замкнулись", [len(w) for w in ways]); return None
        rings.sort(key=len, reverse=True)
        geom = {"type": "Polygon", "coordinates": [rings[0]]} if len(rings) == 1 else \
               {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}
        return geom, f"osm:relation/{rel_id}", rel.get("tags", {})
    except Exception as e:
        print("  overpass:", e)
        return None

# (проект Beliris, откуда след, тип, ожидаемый исход)
PLAN = [
    ("Rénovation du parc du Cinquantenaire", ("osm", "Cinquantenaire"), "restoration",
     "ожидание: NDVI и классы DW в пределах шума — реставрация не меняет растительность (проверено на 7 реставрациях 2009–2016)"),
    ("Réaménagement du parc à Neerpede", ("osm", "Pedepark"), "park_redesign",
     "ожидание: без смены покрытия — шум; при раскрытии дорожек/пруда — built вниз. Совпадение парк↔проект по названию Neerpede/Pede, не по расстоянию"),
    ("Axe Toison d'Or", ("beliris", 0), "boulevard_redesign",
     "ожидание: built вниз, grass/trees вверх при озеленении оси; полигон — карта проекта Beliris"),
    ("boulevard Emile Bockstael", ("beliris", 0), "boulevard_redesign",
     "ожидание: built вниз при деминерализации; полигон — карта проекта Beliris"),
    ("esplanade et des pavillons Simonis", ("beliris", 0), "square_redesign",
     "ожидание: built вниз, grass вверх; 1,2 га — на пределе площади, Landsat непригоден, только Sentinel-2 и DW"),
]

def main():
    existing = {r.signal_source for r in load()}
    records = load()
    made, refused = [], []
    for title, (kind, key), itype, note in PLAN:
        p = project(title)
        src = f"beliris:{p['url']}"
        if src in existing:
            print("уже есть:", p["cleanTitle"]); continue
        if p["project_status"] != "en_projet":
            refused.append((p["cleanTitle"], f"статус {p['project_status']} — работы начаты, фиксация опоздала")); continue
        if kind == "osm":
            f = osm_park(key)
            geom, gsrc = f["geometry"], f"osm:{f['properties']['osm']}"
        else:
            geom, gsrc = beliris_polygon(p["mapShapes"][key]), "beliris:mapShapes"
        rec = register(name=p["cleanTitle"], city="brussels", geometry=geom, geometry_source=gsrc,
                       signal_source=src, intervention_type=itype, works_start=None,
                       expected_checks=("coverage",), note=note, registered_at=TODAY)
        records.append(rec); made.append(rec)
        print(f"зафиксировано: {rec.name[:50]:50} {gsrc:22} hash {rec.geometry_hash}")

    # Фриш Josaphat: новый квартал на пустыре — ожидаемая ПОТЕРЯ зелени, фиксируем до стройки
    p = project("Josaphat : un nouveau quartier")
    src = f"beliris:{p['url']}"
    if src not in existing:
        got = overpass_relation(12579711)   # «Friche Josaphat - Josaphatsite», natural=grassland
        if got:
            geom, gsrc, tags = got
            rec = register(name=p["cleanTitle"], city="brussels", geometry=geom, geometry_source=gsrc,
                           signal_source=src, intervention_type="urban_development", works_start=None,
                           expected_checks=("coverage",), registered_at=TODAY,
                           note=f"ожидание: ПОТЕРЯ — NDVI и grass вниз, built вверх: застройка фриша. OSM {tags.get('natural') or tags.get('landuse')} «{tags.get('name')}»; честный минус, не провал метода")
            records.append(rec); made.append(rec)
            print(f"зафиксировано: {rec.name[:50]:50} {gsrc:22} hash {rec.geometry_hash}")
        else:
            refused.append((p["cleanTitle"], "полигон фриша в OSM не получен — без защитимого следа записи нет"))

    # Canal-Midi: полигон есть, но статус en_execution — контракт должен отказать
    p = project("Canal-Midi")
    try:
        register(name=p["cleanTitle"], city="brussels", geometry=beliris_polygon(p["mapShapes"][0]),
                 geometry_source="beliris:mapShapes", signal_source=f"beliris:{p['url']}",
                 intervention_type="park_creation", works_start="2025-01-01", registered_at=TODAY)
    except ValueError as e:
        refused.append((p["cleanTitle"], str(e)))

    save(records)
    print(f"\nзаписей всего: {len(records)} (новых {len(made)}) → {REGISTRY}")
    for n, why in refused:
        print(f"отказ: {n[:45]:45} — {why}")

if __name__ == "__main__":
    main()
