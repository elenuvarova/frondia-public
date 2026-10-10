#!/usr/bin/env python3
"""
Реестры деревьев коммун как линия выполнения (фаза 2c, пункт 6).

Зачем
─────
Спутник не видит молодых посадок годами (PBL: дерево различимо от 2,5–3 м высоты), а коммуна знает, где
сажала. Cobra в Нидерландах подмешивает данные коммун о посадках и вырубке, Ecoteka ведёт реестр деревьев
для мэрий. Здесь реестр — не доказательство эффекта, а линия выполнения, как у урн и скамеек: где сажали и
сохранились ли деревья. Эффекта не утверждаем.

Что есть в открытых данных (проверено 27.09.2026)
─────────────────────────────────────────────────
· Гент — `locaties-bomen-gent` (data.stad.gent, Modellicentie Gratis Hergebruik, обновляется ежедневно):
  68 240 деревьев, стабильный `gis_id`, год посадки `aanlegjaar` у 18 085; посажено 2020–2025 — 7 716.
· Антверпен — слой `boom` (geodata.antwerpen.be, 134 873 дерева, `OBJECT_GUID`, обхват ствола) и
  `toekomstboom` (1 880 «деревьев будущего»). Года посадки нет.
· Брюссель — `arbres-bomen-vbx-be-bm` (opendata.bruxelles.be, CC BY 4.0): 31 674 дерева на территории
  коммуны Bruxelles (город, Bruxelles Environnement, Bruxelles Mobilité), стабильный `id`. Года посадки нет.

Что считается
─────────────
1. Снимок каждого реестра — `data/registry/snapshots/trees_<city>_<дата>.csv.gz` (id, долгота, широта, год
   посадки или обхват, сектор). Со следующего снимка видно, какие деревья исчезли из реестра: срублены,
   погибли или переучтены — реестр не говорит, что именно, и страница так и пишет.
2. Слой `cities/<city>/layers/trees_register.csv` по секторам: деревьев в реестре; у Гента — посажено по
   годам 2020–2025; при наличии прошлого снимка — сколько исчезло и появилось.
3. Гент: куда шли посадки 2020–2025 — доля посадок в трети секторов с наименьшей кроной (крона 2024 из
   слоя ст. 8), в беднейшей трети по доходу, в самой жаркой трети — против доли жителей в той же трети.
   Тот же вопрос, что у линии выполнения: сажали там, где нужнее, или где удобнее. Реестр покрывает
   деревья, которыми управляет город: сады и частные участки не в нём.

Запуск:
    .venv/bin/python scripts/registry/tree_registers.py --city ghent
"""
from __future__ import annotations

import argparse
import collections
import csv
import gzip
import hashlib
import io
import json
import statistics
import subprocess
import sys
from datetime import date
from pathlib import Path

import shapely
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402

SNAPS = ROOT / "data/registry/snapshots"
YEARS = tuple(range(2020, 2026))
SOURCES = {
    "ghent": "https://data.stad.gent/api/explore/v2.1/catalog/datasets/locaties-bomen-gent/exports/json"
             "?select=gis_id,aanlegjaar,geo_point_2d",
    "brussels": "https://opendata.bruxelles.be/api/explore/v2.1/catalog/datasets/arbres-bomen-vbx-be-bm/exports/json"
                "?select=id,geo_point_2d",
    "antwerp": "https://geodata.antwerpen.be/arcgissql/rest/services/P_Portal/portal_publiek6/MapServer/676/query",
}
# the commune whose trees the register holds: a sector elsewhere is not "0 trees", it is not in the register
COVERS = {"ghent": "44021", "brussels": "21004", "antwerp": "11002"}
LICENCE = {"ghent": "Modellicentie Gratis Hergebruik (Stad Gent)", "brussels": "CC BY 4.0 (Ville de Bruxelles)",
           "antwerp": "Stad Antwerpen open data"}


def curl(url: str) -> bytes:
    return subprocess.run(["curl", "-sS", "--fail", "--retry", "4", "--retry-delay", "10", "--max-time", "600", url],
                          check=True, capture_output=True).stdout


def fetch(city: str) -> list[dict]:
    """Все деревья реестра: id, lon, lat и то, что реестр знает о возрасте."""
    if city == "antwerp":
        out, last = [], -1
        while True:   # постранично по OBJECTID: у слоя предел 2000 записей на ответ
            q = (f"{SOURCES[city]}?where=OBJECTID%3E{last}&outFields=OBJECTID,OBJECT_GUID,STAMOMTREK&orderByFields=OBJECTID"
                 f"&returnGeometry=true&outSR=4326&f=json&resultRecordCount=2000")
            feats = json.loads(curl(q))["features"]
            if not feats:
                break
            for f in feats:
                a, g = f["attributes"], f.get("geometry") or {}
                if "x" in g:
                    # a GUID is 36 characters and the snapshot repeats every season: 12 of its SHA-1 are enough to match
                    # 135 000 trees between snapshots (collision odds ~1e-5)
                    gid = hashlib.sha1(a["OBJECT_GUID"].encode()).hexdigest()[:12]
                    out.append({"id": gid, "lon": g["x"], "lat": g["y"], "girth": a.get("STAMOMTREK")})
            last = feats[-1]["attributes"]["OBJECTID"]
            print(f"  {len(out)} деревьев…", flush=True)
        return out
    rows = json.loads(curl(SOURCES[city]))
    out = []
    for r in rows:
        p = r.get("geo_point_2d") or {}
        if p.get("lon") is None:
            continue
        rid = r.get("gis_id") or r.get("id")
        y = r.get("aanlegjaar")
        out.append({"id": rid, "lon": p["lon"], "lat": p["lat"], "planted": int(str(y)[:4]) if y else None})
    return out


def assign(city: str, trees: list[dict]) -> None:
    units = ADAPTERS[city]().units()
    geoms = [shape(u.geometry) for u in units]
    tree = shapely.STRtree(geoms)
    pts = shapely.points([t["lon"] for t in trees], [t["lat"] for t in trees])
    idx = tree.query(pts, predicate="within")
    sec = {}
    for p, g in zip(*idx):
        sec.setdefault(int(p), units[int(g)].id)
    for i, t in enumerate(trees):
        t["sector"] = sec.get(i, "")


def previous(city: str, today: str) -> Path | None:
    snaps = sorted(p for p in SNAPS.glob(f"trees_{city}_*.csv.gz") if p.stem.split("_")[-1].split(".")[0] < today)
    return snaps[-1] if snaps else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True, choices=list(SOURCES))
    city = ap.parse_args().city
    today = date.today().isoformat()
    trees = fetch(city)
    assign(city, trees)
    SNAPS.mkdir(parents=True, exist_ok=True)
    snap = SNAPS / f"trees_{city}_{today}.csv.gz"
    cols = ["id", "lon", "lat", "sector"] + (["girth"] if city == "antwerp" else ["planted"])
    with gzip.open(snap, "wt", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for t in sorted(trees, key=lambda t: str(t["id"])):
            w.writerow({**t, "lon": round(t["lon"], 5), "lat": round(t["lat"], 5)})   # ~1 m
    print(f"{city}: {len(trees)} деревьев, в секторах пакета {sum(1 for t in trees if t['sector'])} → {snap.name}")

    prev = previous(city, today)
    gone = came = None
    if prev:
        old = {r["id"]: r for r in csv.DictReader(io.TextIOWrapper(gzip.open(prev), newline=""))}
        now = {str(t["id"]): t for t in trees}
        gone = collections.Counter(old[i]["sector"] for i in set(old) - set(now))
        came = collections.Counter(now[i]["sector"] for i in set(now) - set(old))
        print(f"  с прошлого снимка {prev.name}: исчезло {sum(gone.values())}, появилось {sum(came.values())}")

    by = collections.defaultdict(lambda: {"trees": 0, **{f"planted_{y}": 0 for y in YEARS}})
    for t in trees:
        if not t["sector"]:
            continue
        b = by[t["sector"]]
        b["trees"] += 1
        if t.get("planted") in YEARS:
            b[f"planted_{t['planted']}"] += 1
    out = ROOT / f"cities/{city}/layers/trees_register.csv"
    fields = ["id", "trees"] + ([f"planted_{y}" for y in YEARS] if city == "ghent" else []) + (["gone", "came"] if prev else [])
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for u in ADAPTERS[city]().units():
            if not u.id.startswith(COVERS[city]):
                continue
            row = {"id": u.id, **by.get(u.id, {"trees": 0, **{f"planted_{y}": 0 for y in YEARS}})}
            if prev:
                row.update({"gone": gone.get(u.id, 0), "came": came.get(u.id, 0)})
            w.writerow(row)

    summary = {"city": city, "snapshot": snap.name, "date": today, "trees": len(trees), "commune": COVERS[city],
               "in_sectors": sum(1 for t in trees if t["sector"]), "previous": prev.name if prev else None,
               "licence": LICENCE[city]}
    if city == "ghent":
        summary["planted"] = {y: sum(1 for t in trees if t.get("planted") == y) for y in YEARS}
        summary["where"] = where_planted(city, by)
    (ROOT / f"cities/{city}/layers/trees_register_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))

    m = Manifest.read(city)
    m.add(LayerEntry(
        layer="trees_register", computed=today, n_units=len(by),
        measures="деревья в реестре коммуны по секторам" + ("; посадки по годам 2020–2025" if city == "ghent" else "")
                 + "; снимок для учёта исчезнувших со следующего прогона",
        unit="деревья", method="точка дерева в полигоне сектора Statbel; снимок реестра со стабильными идентификаторами",
        source=f"{SOURCES[city].split('?')[0]} — {LICENCE[city]}",
        threshold_source="линия выполнения, не изменение: порога нет — реестр говорит, что сделано, а не какой эффект",
        limits=["в реестре только деревья, которыми управляет город: частные сады и участки не учтены",
                "исчезновение из реестра — вырубка, гибель или переучёт; реестр не различает",
                "год посадки есть только в реестре Гента, и не у всех деревьев"]))
    m.write()
    print(json.dumps({k: v for k, v in summary.items() if k != "where"}, ensure_ascii=False))
    if city == "ghent":
        print(json.dumps(summary["where"], ensure_ascii=False, indent=1))
    return 0


def where_planted(city: str, by: dict) -> dict:
    """Куда шли посадки 2020–2025: доля в трети секторов с наименьшей кроной, беднейшей и самой жаркой — против
    доли жителей там же. Трети — по секторам с жителями (≥ 200), как в «кто в нехватке» атласа."""
    a8 = {r["id"]: r for r in csv.DictReader((ROOT / f"cities/{city}/layers/article8_2024.csv").open())}
    heat = {r["id"]: float(r["excess_over_city_c"]) for r in csv.DictReader((ROOT / f"cities/{city}/layers/heat_2022_2025.csv").open())
            if r.get("excess_over_city_c")}
    units = [u for u in ADAPTERS[city]().units() if (u.population or 0) >= 200 and u.id in a8]
    planted = lambda sid: sum(by.get(sid, {}).get(f"planted_{y}", 0) for y in YEARS)
    total_p = sum(planted(u.id) for u in units) or 1
    total_r = sum(u.population for u in units) or 1
    out = {"sectors": len(units), "planted": total_p, "residents": total_r}
    for key, val, low_is_short in (("least_canopy", lambda u: float(a8[u.id]["trees_2024"] or 0), True),
                                   ("poorest", lambda u: float(a8[u.id]["income"]) if a8[u.id]["income"] else None, True),
                                   ("hottest", lambda u: heat.get(u.id), False)):
        us = [u for u in units if val(u) is not None]
        us.sort(key=val, reverse=not low_is_short)
        k = len(us) // 3
        third = us[:k]
        out[key] = {"sectors": len(third),
                    "planted_share": round(sum(planted(u.id) for u in third) / (sum(planted(u.id) for u in us) or 1), 3),
                    "residents_share": round(sum(u.population for u in third) / (sum(u.population for u in us) or 1), 3),
                    "per_1000_in_third": round(1000 * sum(planted(u.id) for u in third) / (sum(u.population for u in third) or 1), 1),
                    "per_1000_elsewhere": round(1000 * sum(planted(u.id) for u in us[k:]) / (sum(u.population for u in us[k:]) or 1), 1),
                    # per hectare too: a dense centre has less room to plant than an outskirt, and per resident alone
                    # would blame the planting for the density
                    "per_10ha_in_third": round(10 * sum(planted(u.id) for u in third) / (sum(u.area_ha for u in third) or 1), 2),
                    "per_10ha_elsewhere": round(10 * sum(planted(u.id) for u in us[k:]) / (sum(u.area_ha for u in us[k:]) or 1), 2)}
    return out


if __name__ == "__main__":
    raise SystemExit(main())
