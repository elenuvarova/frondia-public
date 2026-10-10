#!/usr/bin/env python3
"""
Данные для сайта (site/): пакеты городов и дела аудита → JSON для лендинга и атласа.

Сайт — английская витрина того же пакета. Правило то же, что у русских страниц:
числа берутся из слоёв, сводок и дел, слова пишутся в коде сайта. Здесь ничего не
пересчитывается заново, кроме того, что уже считают соседние генераторы, — и теми
же функциями: фон города (`background`), воронка мониторинга (`monitoring_html`),
вердикты пакетного аудита парков.

Выход:
  site/public/data/<city>.json   секторы атласа (пути SVG из atlas_data.py) + слой ст. 8
                                  + гистограммы шума и сырого изменения + следы дел
  site/public/data/facts.json    числа лендинга: фон, пороги, отказы, закон, справедливость
  site/public/data/cases.json    три дела аудита: эффекты, пороги, контроль поимённо, ряды
  site/public/data/points-<city>.json  City Planner: 14 типов, по 40 точек с рангом и ролью
                                  (названная / контрольная), покрытие до → после, сектор точки

Объединённая Frondia (docs/07-unified-frondia.md): к каждому сектору добавлены слои соседних
проектов, уже лежащие в пакете города, — чего не хватает (Fit Score, SpotFinder, жара,
3-30-300, возраст) — под короткими ключами; нет слоя в городе — нет ключа.
  site/public/cases/*.png        снимки «до/после» дел, где они есть

Поле-подложку (site/public/field/) выгружает field.py — ему нужен Earth Engine, этому скрипту нет.

Запуск (после atlas_data.py и, для подложки, field.py):
    .venv/bin/python scripts/site/site_data.py
"""
from __future__ import annotations

import collections
import csv
import functools
import json
import math
import re
import shutil
import statistics
import subprocess
import sys
from bisect import bisect_left, bisect_right
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.calibrate import percentile  # noqa: E402
from engine.config import CONTROL, QUALITY  # noqa: E402
from engine.manifest import Manifest  # noqa: E402
from scripts.report.background import background  # noqa: E402
from scripts.report.paths import DERIVED  # noqa: E402
from scripts.site.field import frames  # noqa: E402

SITE = ROOT / "site" / "public"
CITIES = {"brussels": "Brussels", "antwerp": "Antwerp", "ghent": "Ghent", "liege": "Liège", "charleroi": "Charleroi"}
CITY_RU = {"Брюссель": "brussels", "Антверпен": "antwerp", "Гент": "ghent", "Льеж": "liege", "Шарлеруа": "charleroi"}
VERDICT = {"рост": "up", "потеря": "down", "шум": "noise", "контроль несопоставим": "refused"}
CASES = ["ninove", "droogdokkenpark", "spoor-noord"]
SERVICES = ["cafe", "childcare", "convenience", "gp", "hospital", "library", "park", "pharmacy",
            "playground", "restaurant", "school", "sport", "supermarket", "transit"]
SHOPS = ["bakery", "cafe", "confectionery"]
ADAPTERS = {"brussels": ("engine.adapters.brussels", "BrusselsAdapter"),
            "antwerp": ("engine.adapters.antwerp", "AntwerpAdapter"),
            "ghent": ("engine.adapters.ghent", "GhentAdapter"),
            "liege": ("engine.adapters.liege", "LiegeAdapter"),
            "charleroi": ("engine.adapters.charleroi", "CharleroiAdapter")}


def fl(r: dict, k: str, nd: int = 4):
    try:
        return round(float(r.get(k, "")), nd)
    except (TypeError, ValueError):
        return None


def rows(path) -> list[dict]:
    p = ROOT / path
    return list(csv.DictReader(p.open())) if p.exists() else []


def hist(values, lo, hi, n) -> list[int]:
    out, w = [0] * n, (hi - lo) / n
    for v in values:
        out[min(n - 1, max(0, int((v - lo) / w)))] += 1
    return out


class Proj:
    """Проекция атласа: lon/lat → координаты SVG (та же, что atlas_data.py)."""

    def __init__(self, city: str):
        a = frames(city)["atlas"]
        (self.x0, self.x1), (self.y0, self.y1) = a["lon"], a["lat"]
        self.W, self.H = a["svg"][2], a["svg"][3]

    def __call__(self, lon, lat):
        return ((lon - self.x0) / (self.x1 - self.x0) * self.W,
                (self.y1 - lat) / (self.y1 - self.y0) * self.H)


def footprint(city: str, osm: str, proj: Proj) -> dict | None:
    fc = json.loads((ROOT / f"data/perimeters/parks_{city}.geojson").read_text())
    for f in fc["features"]:
        if f["properties"].get("osm") == osm:
            g = f["geometry"]
            polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            d, pts = "", []
            for poly in polys:
                ring = [proj(*p) for p in poly[0]]
                pts += ring
                d += "M" + " ".join(f"{x:.1f},{y:.1f}" for x, y in ring) + "Z"
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            return {"d": d, "x": round(cx, 1), "y": round(cy, 1)}
    return None


def extras(city: str) -> dict[str, dict]:
    """Слои «чего не хватает» по секторам, из пакета города. Ключ есть, только если слой есть."""
    out: dict[str, dict] = collections.defaultdict(dict)
    for r in rows(f"cities/{city}/layers/fit_score.csv"):
        s, sc = out[r["id"]], r["scenario"]
        s.setdefault("fit", {})[sc] = int(round(float(r["score"])))
        s.setdefault("fitp", {})[sc] = int(round(float(r["percentile"])))
        s.setdefault("_fitraw", {})[sc] = float(r["score"])   # for the fifths below, then dropped
        vals = [(float(r[k]), k) for k in SERVICES if r.get(k) not in (None, "")]
        s.setdefault("low", {})[sc] = [k for _, k in sorted(vals)[:3]]
    for r in rows(f"cities/{city}/layers/heat_2022_2025.csv"):
        out[r["id"]].update(hot=fl(r, "excess_over_city_c", 2), lst=fl(r, "lst_summer_c", 1))
    for r in rows(f"cities/{city}/layers/rule_3_30_300.csv"):
        # the layer's own pass flags ride along: a share rounded to 0.300 may belong to a sector that fails
        out[r["id"]].update(cs=fl(r, "canopy_share", 3), np=fl(r, "near_park_share", 3),
                            r3=int(r["passes_30"]) + int(r["passes_300"]),
                            p30=int(r["passes_30"]), p300=int(r["passes_300"]))
    for r in rows(f"cities/{city}/layers/population_age.csv"):
        out[r["id"]].update(kid=fl(r, "share_children", 3), old=fl(r, "share_seniors", 3),
                            k15=int(r["children_0_14"]), o65=int(r["seniors_65_plus"]), o80=int(r["seniors_80_plus"]))
    for r in rows(f"cities/{city}/layers/shops_access.csv"):
        out[r["id"]]["shop"] = {t: int(round(float(r[f"{t}_m"]))) for t in SHOPS}
    # where to plant first (scripts/registry/tree_priority.py): ranks 1–10 named before any planting, 11–20 their comparison
    for r in rows(f"cities/{city}/layers/tree_priority.csv"):
        if r.get("role") in ("named", "control"):
            out[r["id"]].update(tr=int(r["rank"]), trl=r["role"])
    return out


def tree_register_copy(city: str) -> str | None:
    """The base of the planting check: the latest copy of the city's register taken no later than the day the list was
    named — never a later one, which would move the base after the record (re-check 3)."""
    named = tree_named_at(city)
    days = sorted(p.name.split("_")[-1].split(".")[0] for p in (ROOT / "data/registry/snapshots").glob(f"trees_{city}_*.csv.gz"))
    days = [d for d in days if named is None or d <= named]
    return days[-1] if days else None


def tree_named_at(city: str) -> str | None:
    p = ROOT / f"data/registry/tree_priority_{city}.json"
    if not p.exists():
        return None
    dates = {r["registered_at"] for r in json.loads(p.read_text())}
    return min(dates) if dates else None


def _rings(geom: dict) -> list:
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [poly[0] for poly in polys]


def _inside(pt, ring) -> bool:
    x, y = pt
    inside = False
    for i in range(len(ring) - 1):
        (x1, y1), (x2, y2) = ring[i][:2], ring[i + 1][:2]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def points_data(city: str) -> dict | None:
    """City Planner: кандидаты по типам, их ранг, роль в реестре выполнения и сектор точки."""
    pdir = ROOT / f"cities/{city}/points"
    man = Manifest.read(city)
    reg = ROOT / f"data/registry/named_points_{city}.json"
    roles = {}
    if reg.exists():
        for x in json.loads(reg.read_text()):
            t, _, rank = x["unit_id"].partition("#")
            roles[(t, int(rank))] = x["role"]
    import importlib
    mod, cls = ADAPTERS[city]
    units = getattr(importlib.import_module(mod), cls)().units()
    boxes = []
    for u in units:
        for ring in _rings(u.geometry):
            xs, ys = [p[0] for p in ring], [p[1] for p in ring]
            boxes.append((min(xs), min(ys), max(xs), max(ys), ring, u.id))

    def sector_of(lon, lat):
        for x0, y0, x1, y1, ring, sid in boxes:
            if x0 <= lon <= x1 and y0 <= lat <= y1 and _inside((lon, lat), ring):
                return sid
        return None

    proj = Proj(city)
    types, pts = [], []
    for f in sorted(pdir.glob("*.geojson")):
        t = f.stem
        if t == "improvements":
            continue
        e = man.layers.get(f"points_{t}")
        m = re.search(r"покрытие ([\d.]+) → ([\d.]+)", e.method if e else "")
        pool = re.search(r"пул кандидатов (\d+)", e.method if e else "")
        gj = json.loads(f.read_text())
        feats = gj["features"]
        steps = (gj.get("properties") or {}).get("coverage_steps")
        types.append({"key": t, "n": len(feats), "before": m and float(m.group(1)),
                      "after": m and float(m.group(2)), "pool": pool and int(pool.group(1)),
                      # coverage after each rank, 0…40: "what if N more?"
                      **({"steps": [round(v, 4) for v in steps]} if steps else {})})
        for ft in feats:
            lon, lat = ft["geometry"]["coordinates"][:2]
            rank = int(ft["properties"]["rank"])
            x, y = proj(lon, lat)
            pts.append({"t": t, "r": rank, "x": round(x, 1), "y": round(y, 1),
                        "role": roles.get((t, rank)), "s": sector_of(lon, lat)})
    if not types:
        return None
    named = next((x for x in json.loads(reg.read_text())), {}) if reg.exists() else {}
    # the city's own register at the named points (scripts/registry/object_registers.py): per kind, how many named and
    # comparison points already have an official object within their radius (taken out of the check), and how many have
    # one within 500 m that the planner's OpenStreetMap lacked (None where that OSM was not kept)
    summ = ROOT / f"data/registry/named_points_{city}_official_summary.json"
    if summ.exists():
        from engine.registries.points import PLANNER_KINDS
        S = json.loads(summ.read_text())
        for t in types:
            k = S["kinds"].get(PLANNER_KINDS.get(t["key"], ""))
            if k:
                t["official"] = {"date": S["date"], **{role: {"n": k[role]["n"], "at": k[role]["official_at_point"],
                                                             "gap": k[role]["map_gap_500m"]} for role in ("named", "control")}}
    return {"city": city, "registered_at": named.get("registered_at"), "types": types, "points": pts}


def city_data(city: str) -> dict:
    atlas = json.loads((DERIVED / f"atlas-{city}.json").read_text())
    nh = json.loads((DERIVED / f"atlas-hist-{city}.json").read_text())
    a8 = {r["id"]: r for r in rows(f"cities/{city}/layers/article8_2024.csv")}
    s8 = json.loads((ROOT / f"cities/{city}/layers/article8_2024_summary.json").read_text())
    bg = background(city)
    ex = extras(city)

    sectors = []
    for s in atlas["sectors"]:
        r = a8.get(s["id"], {})
        comparable = r.get("comparable") == "True"
        sectors.append({
            "id": s["id"], "n": s["n"], "c": s["c"], "d": s["d"],
            "pop": s.get("pop"), "inc": s.get("inc"),
            "ne": fl(r, "ndvi_eff"), "raw": fl(r, "ndvi_raw"),
            "nv": VERDICT.get(r.get("ndvi_verdict", "")),
            "te": fl(r, "trees_eff"), "tv": VERDICT.get(r.get("trees_verdict", "")),
            # запечатывание: класс built против тех же 12 мест, порог этого же прогона (article8_data --from-layer)
            "be": fl(r, "built_eff"), "bv": VERDICT.get(r.get("built_verdict", "")),
            "n24": fl(r, "ndvi_2024", 3), "t24": fl(r, "trees_2024"), "b24": fl(r, "built_2024", 3),
            "ha": fl(r, "area_ha", 1),
            "gap": fl(r, "gap"), "cmp": comparable,
            **ex.get(s["id"], {}),
            **place_variants(city, s["id"], s["n"], s["c"]),
        })
    services_fifths(sectors)
    raw = [x["raw"] for x in sectors if x["raw"] is not None and x["cmp"]]
    proj = Proj(city)
    cases = []
    for slug in CASES:
        c = json.loads((ROOT / f"data/registry/cases/{slug}.json").read_text())
        if CITY_RU.get(c["city"]) == city:
            fp = footprint(city, c["osm"], proj)
            if fp:
                cases.append({"slug": slug, "name": c["name"].split(",")[0], **fp})

    field = SITE / "field" / f"field-{city}.json"
    fj = json.loads(field.read_text()) if field.exists() else None
    return {
        "city": city, "name": CITIES[city],
        "svg": {"W": atlas["meta"]["W"], "H": atlas["meta"]["H"]},
        "window": s8["window"],
        "units": {"total": s8["units_total"], "measured": s8["units_measured"],
                  "comparable": s8["units_comparable"], "population": s8["population"]},
        "thresholds": s8["thresholds"],
        "null_mean": s8.get("thresholds_mean"),
        "counts": {"up": sum(x["nv"] == "up" for x in sectors), "down": sum(x["nv"] == "down" for x in sectors),
                   "noise": sum(x["nv"] == "noise" for x in sectors),
                   "refused": sum(x["nv"] == "refused" for x in sectors)},
        # «up» — застроили (класс built вырос сверх шума), «down» — раскрыли
        "built": built_block(sectors, s8),
        # баланс после базы 2024 в гектарах (art8_balance.py): сверх шума против 12 мест, по городу и коммунам
        "balance": balance(city),
        # the detector against Groenkaart Vlaanderen, where it exists (Antwerp, Ghent)
        "check": ((groenkaart_check() or {}).get("cities") or {}).get(city),
        "background": bg and {k: round(v, 5) if isinstance(v, float) else v for k, v in bg.items()},
        "hist": {"lo": nh["lo"], "hi": nh["hi"], "n": nh["n"], "effect": nh["counts"],
                 "raw": hist(raw, nh["lo"], nh["hi"], nh["n"])},
        # подложка: резкое летнее поле в рамке `wide` (field.py), координаты — в SVG атласа
        "field": fj and {"src": f"field/{city}-context-{fj['base_year']}-light.jpg",
                         "box": fj["frames"]["wide"]["svg"], "year": fj["base_year"]},
        # «весь город до и после»: два лета в естественных цветах (field.py --photos), та же рамка `wide`
        "photos": photos(city, fj),
        "cases": cases,
        "heat_canopy_r": heat_canopy_r(sectors),
        "equity": equity(sectors),
        "communes": communes(city, proj, sectors),
        "dossier": dossier(city, sectors, s8),
        "registered": registered(city, proj),
        # the day the tree-planting priority was named (data/registry/tree_priority_<city>.json)
        "tree_named_at": tree_named_at(city),
        # the canopy share the planting priority counts short of (tree_priority.py TARGET, the 3-30-300 rule's 30 %)
        "tree_target": 0.30,
        # the copy of the city's own tree register the planting check starts from (data/registry/snapshots), or None
        # where the city publishes none (Liège, Charleroi): there the check is the canopy against twelve places only
        "tree_register_copy": tree_register_copy(city),
        "sectors": sectors,
    }


BAL_CLASSES = ("green", "trees", "built")


def balance(city: str) -> dict | None:
    """Гектары после базы 2024: потеряно и прибавлено сверх шума, чистый итог, сырой итог по городу — из
    сводки слоя; по коммунам — суммы тех же секторов (коммуна = первые пять знаков кода сектора)."""
    p = ROOT / f"cities/{city}/layers/art8_balance_summary.json"
    if not p.exists():
        return None
    S = json.loads(p.read_text())
    out = {"base": S["base"], "seasons": {}, "preliminary": S["preliminary"], "scenes": S["scenes"]}
    for season, b in S["seasons"].items():
        by = collections.defaultdict(lambda: {k: {"lost": 0.0, "gained": 0.0} for k in BAL_CLASSES})
        for r in rows(f"cities/{city}/layers/art8_balance_{season}.csv"):
            for k in BAL_CLASSES:
                v = r[f"{k}_verdict"]
                if v in ("потеря", "рост"):
                    by[r["id"][:5]][k]["lost" if v == "потеря" else "gained"] += float(r[f"{k}_eff_ha"])
        out["seasons"][season] = {
            "thresholds": b["thresholds"], "comparable": b["units_comparable"],
            **{k: {x: b[k][x] for x in ("lost_ha", "gained_ha", "net_ha", "raw_net_ha", "lost_sectors", "gained_sectors")}
               for k in BAL_CLASSES},
            "by_commune": {c: {k: {"lost": round(v[k]["lost"], 1), "gained": round(v[k]["gained"], 1),
                                   "net": round(v[k]["lost"] + v[k]["gained"], 1)} for k in BAL_CLASSES}
                           for c, v in sorted(by.items())},
        }
    out["latest"] = max(out["seasons"])
    return out


def built_block(sectors: list[dict], s8: dict) -> dict:
    """Запечатывание для атласа: счёт вердиктов слоя и гистограмма тех же эффектов, что на карте
    (сопоставимые секторы), шагом 0,005, как у зелёности, в рамке, кратной 0,01."""
    vals = [x["be"] for x in sectors if x["cmp"] and x["be"] is not None]
    lo = math.floor(min(vals) / 0.01) * 0.01
    hi = math.ceil(max(vals) / 0.01) * 0.01
    n = round((hi - lo) / 0.005)
    h = hist(vals, lo, hi, n)
    tr = s8["trend"]
    return {"threshold": s8["thresholds"]["built"],
            "counts": {k: sum(x["bv"] == k for x in sectors) for k in ("up", "down", "noise", "refused")},
            "pop": {"up": tr["built_up_pop"], "down": tr["built_down_pop"]},
            "hist": {"lo": round(lo, 2), "hi": round(hi, 2), "n": n, "effect": h, "raw": h}}


PHOTO_YEARS = (2017, 2024)   # the ends of the measurement windows: 2017–19 → 2021–24


def photos(city: str, fj: dict | None) -> dict | None:
    """The two true-colour summers of the atlas swipe, in the field's `wide` frame, or None."""
    src = [f"field/{city}-photo-{y}.jpg" for y in PHOTO_YEARS]
    if not fj or not all((SITE / s).exists() for s in src):
        return None
    return {"years": list(PHOTO_YEARS), "src": src, "box": fj["frames"]["wide"]["svg"]}


# The sector dossier (phase 2b, docs/07-unified-frondia.md): the site's page is the Russian
# `scripts/report/dossier_html.py` in English, and every number it prints comes from here or from the
# sector itself, computed the way that script computes it, so the two cannot disagree.
PICK_MIN_RESIDENTS, PICK_MIN_HEAT = 500, 1.0
AFTER_KINDS = ("construction", "confirmed", "unconfirmed", "gained")


def dossier(city: str, sectors: list[dict], s8: dict) -> dict:
    """City-wide numbers the dossier sets a sector against, and the sector the rule picks.

    Medians over every measured sector; income thirds by sectors (the Article 8 page's terciles, whose
    population-weighted canopy the summary already holds); the third of sectors with the least canopy
    (flagged on each sector as `lt3`) and the share of the city's children who live in it; the seasons
    of monitoring after the 2024 baseline, each sector's events written onto it as `after`."""
    from scripts.report.monitoring_html import apply_documents, funnel, load_layer

    def med(k):
        v = [x[k] for x in sectors if x.get(k) is not None]
        return round(statistics.median(v), 4) if v else None
    inc = sorted(x["inc"] for x in sectors if x.get("inc") and x.get("t24") is not None)
    cut_low, cut_high = inc[len(inc) // 3], inc[2 * len(inc) // 3]
    by_trees = sorted((x for x in sectors if x.get("t24") is not None), key=lambda x: x["t24"])
    third = {x["id"] for x in by_trees[:len(by_trees) // 3]}
    for x in sectors:
        if x["id"] in third:
            x["lt3"] = 1
    kids_all = sum(x.get("k15") or 0 for x in sectors)
    kids_third = sum(x.get("k15") or 0 for x in sectors if x["id"] in third)

    # the rule that picks a sector for a dossier (dossier_html.PICK_RULE), open so the choice can be checked
    lau = {r["lau_id"]: r for r in rows(f"cities/{city}/layers/art8_official_lau_2021.csv")}
    def fits(x):
        code = f"BE_{x['id'][:5]}"
        return (x.get("inc") and x["inc"] <= cut_low and x["id"] in third and (x.get("hot") or -99) >= PICK_MIN_HEAT
                and (x.get("pop") or 0) >= PICK_MIN_RESIDENTS and code in lau and lau[code]["exempt"] != "True")
    picked = sorted((x for x in sectors if fits(x)), key=lambda x: (-(x.get("k15") or 0), -(x.get("pop") or 0)))

    # after the baseline: the bulletin's own functions, documents applied
    man = Manifest.read(city)
    seasons = sorted(int(k.split("_")[1]) for k in man.layers if re.fullmatch(r"monitoring_\d{4}", k) and int(k.split("_")[1]) > 2024)
    byid = {x["id"]: x for x in sectors}
    for yr in seasons:
        F = funnel(apply_documents(load_layer(city, yr), city, yr), man.layers[f"monitoring_{yr}"].threshold)
        for kind in AFTER_KINDS:
            for r in F[kind]:
                if r["id"] in byid:
                    byid[r["id"]].setdefault("after", []).append([yr, kind, round(float(r["effect"]), 4)])

    terc = s8["equity_income_terciles"]
    return {
        "medians": {"n24": med("n24"), "t24": med("t24"), "b24": med("b24")},
        "cuts": [round(cut_low), round(cut_high)],
        "thirds": [{"income": round(t["income_median"]), "t24": round(t["trees_2024_wmean"], 4),
                    "n24": round(t["ndvi_2024_wmean"], 3)} for t in (terc[0], terc[-1])],
        "kids_third": round(kids_third / kids_all, 3) if kids_all else None,
        "seasons": seasons,
        "pick": {"n": len(picked), "ids": [x["id"] for x in picked[:6]],
                 "min_residents": PICK_MIN_RESIDENTS, "min_heat": PICK_MIN_HEAT},
        "rules": {"controls": CONTROL["n_controls"], "exclusion_m": CONTROL["exclusion_m"],
                  "max_gap": CONTROL["max_gap_ndvi"], "min_scenes": QUALITY["min_scenes"]},
    }


# the atlas shades a "what's missing" lens only where 200 people or more live (lib/lenses.js)
MIN_RESIDENTS = 200
SCENARIOS = ("family", "remote", "senior")


def services_fifths(sectors: list[dict]) -> None:
    """`fitq`: the fifth of the city's lived-in sectors a sector falls in, 1 best served … 5 worst.

    Fit Score's own percentile ranks every sector, forests and the port included, so its bottom
    fifth held only 10–16 % of the sectors the map colours. The legend says "fifth", so the fifths
    are counted among the coloured sectors; equal scores share a band."""
    lived = [x for x in sectors if (x.get("pop") or 0) >= MIN_RESIDENTS]
    for sc in SCENARIOS:
        scored = [x for x in lived if sc in x.get("_fitraw", {})]
        vals = sorted(x["_fitraw"][sc] for x in scored)
        for x in scored:
            v = x["_fitraw"][sc]
            mid = (bisect_left(vals, v) + bisect_right(vals, v) - 1) / 2   # mean rank from the worst
            x.setdefault("fitq", {})[sc] = 5 - min(4, int(5 * mid / len(vals)))
    for x in sectors:
        x.pop("_fitraw", None)


# "Who is short" (phase 2, docs/07): what each need lens reads in a sector, as in lib/lenses.js
LENS_READ = {
    "services": lambda s, o: (s.get("fit") or {}).get(o),
    "shops": lambda s, o: (s.get("shop") or {}).get(o),
    "heat": lambda s, o: s.get("hot"),
    "r3": lambda s, o: None if s.get("r3") is None else (1.0 if s["r3"] == 0 else 0.0),   # meets neither part
}
LENS_OPTIONS = {"services": SCENARIOS, "shops": tuple(SHOPS), "heat": ("_",), "r3": ("_",)}
MORE_IS_WORSE = {"services": False, "shops": True, "heat": True, "r3": True}


def equity(sectors: list[dict]) -> dict:
    """Who is short under each need lens: the lens for each third of residents by income, and who
    lives in the worst-off group (for 3-30-300, the sectors that meet neither part).

    Thirds of residents, not of sectors: the poorest sectors are the most populous (in Brussels the
    poorest third of sectors holds 40 % of residents), and "the poorest third" should be a third of
    people. The worst-off group is cut by the lens's own value, so equal values at the edge stay
    together and the group can be named by a number ("score 72 or less"). Only sectors where
    MIN_RESIDENTS or more live, as on the map; children and people over 65 from the 2021 census."""
    lived = [s for s in sectors if (s.get("pop") or 0) >= MIN_RESIDENTS]
    by_inc = sorted((s for s in lived if s.get("inc")), key=lambda s: s["inc"])
    total = sum(s["pop"] for s in by_inc)
    thirds, acc = ([], [], []), 0
    for s in by_inc:
        thirds[min(2, int(3 * (acc + s["pop"] / 2) / total))].append(s)
        acc += s["pop"]
    out: dict = {"income_cuts": [round(max(s["inc"] for s in thirds[0])), round(max(s["inc"] for s in thirds[1]))],
                 "income_share": [round(sum(s["pop"] for s in t) / total, 3) for t in thirds]}
    for lens, opts in LENS_OPTIONS.items():
        read, worse = LENS_READ[lens], MORE_IS_WORSE[lens]
        out[lens] = {}
        for o in opts:
            def wmean(group):
                pairs = [(read(s, o), s["pop"]) for s in group if read(s, o) is not None]
                w = sum(p for _, p in pairs)
                return sum(v * p for v, p in pairs) / w if w else None
            by_third = [wmean(t) for t in thirds]
            measured = [s for s in lived if read(s, o) is not None]
            if not measured or None in by_third:
                continue
            if lens == "r3":
                cut, group = None, [s for s in measured if read(s, o) == 1.0]
            else:
                ranked = sorted(measured, key=lambda s: read(s, o), reverse=worse)
                need, run, cut = sum(s["pop"] for s in ranked) / 3, 0, None
                for s in ranked:
                    run += s["pop"]
                    if run >= need:
                        cut = read(s, o); break
                group = [s for s in measured if (read(s, o) >= cut if worse else read(s, o) <= cut)]
            base = [s for s in measured if s.get("kid") is not None and s.get("old") is not None]
            ids = {s["id"] for s in group}

            def share(f):
                b = sum(f(s) for s in base)
                return round(sum(f(s) for s in base if s["id"] in ids) / b, 3) if b else None
            out[lens][o] = {
                "thirds": [round(v, 3) for v in by_third],
                "cut": None if cut is None else round(cut, 2),
                "all": share(lambda s: s["pop"]),
                "kid": share(lambda s: s["pop"] * s["kid"]),
                "old": share(lambda s: s["pop"] * s["old"]),
            }
    return out


# Communes (phase 2, docs/07): Article 8(1) by commune, and the projects registered before their works
SECTORS_GEO = {"brussels": ("data/brussels_sectors.geojson", "id"), "antwerp": ("data/antwerp_sectors.geojson", "CD_SECTOR"),
               "ghent": ("data/ghent_sectors.geojson", "CD_SECTOR"), "liege": ("data/liege_sectors.geojson", "CD_SECTOR"),
               "charleroi": ("data/charleroi_sectors.geojson", "CD_SECTOR")}


def _svg_path(geom) -> str:
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    d = ""
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)[:-1]
            d += "M" + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
    return d


def _flat(g: dict) -> dict:
    """Longitude and latitude only: Antwerp's sector file carries a third coordinate."""
    def walk(c):
        return c[:2] if isinstance(c[0], (int, float)) else [walk(k) for k in c]
    return {"type": g["type"], "coordinates": walk(g["coordinates"])}


# a city that is one municipality is named as the city, not after its most common district
CITY_LAU = {"44021": "Ghent", "62063": "Liège", "52011": "Charleroi"}

# Place names in the page's language (plan 5, L4): Statbel's register 2024 (scripts/registry/statbel_names.py writes
# the CSV), joined on the sector code; a Dutch or French name is written next to the English one only where it differs
NAMES_CSV = ROOT / "data/statbel_names_2024.csv"
# the English site's own district labels, which are not in Statbel's register (glossary)
DISTRICT_I18N = {"Liège (north)": {"nl": "Luik (noord)", "fr": "Liège (nord)"},
                 "Liège (south)": {"nl": "Luik (zuid)", "fr": "Liège (sud)"},
                 "Haven": {"nl": "Haven", "fr": "Port"}}
CITY_I18N = {"brussels": {"nl": "Brussel", "fr": "Bruxelles"}, "antwerp": {"nl": "Antwerpen", "fr": "Anvers"},
             "ghent": {"nl": "Gent", "fr": "Gand"}, "liege": {"nl": "Luik", "fr": "Liège"},
             "charleroi": {"nl": "Charleroi", "fr": "Charleroi"}}
REGION_KEY = {"brussels": "brussels", "antwerp": "flanders", "ghent": "flanders", "liege": "wallonia", "charleroi": "wallonia"}


@functools.cache
def statbel_names() -> dict[str, dict]:
    """Sector id → its official names (read when first needed, so importing this module never needs the CSV)."""
    with NAMES_CSV.open(encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def variants(key: str, en: str, nl: str | None, fr: str | None) -> dict:
    """`{key_nl: nl}` and/or `{key_fr: fr}` — only a name that is there and differs from the English one. Whitespace
    does not count as a difference: a few English names keep the double spaces of the source the register drops."""
    same = lambda a: " ".join(a.split()) == " ".join((en or "").split())
    return {f"{key}_{lang}": v for lang, v in (("nl", nl), ("fr", fr)) if v and not same(v)}


def munty_names(code: str) -> tuple[str, str] | tuple[None, None]:
    r = next((r for r in statbel_names().values() if r["refnis"] == code), None)
    return (r["munty_nl"], r["munty_fr"]) if r else (None, None)


def place_variants(city: str, sid: str, n: str, c: str) -> dict:
    """A sector's name (`n_*`) and its district or commune (`c_*`) in Dutch and French. The district: the site's own
    labels from DISTRICT_I18N; in Brussels the commune's official names (the English site writes the short forms,
    "Molenbeek", "Saint-Josse"); elsewhere the commune's names only where the label is the commune (Antwerpen → Anvers)
    — Ghent's and Antwerp's districts are the same in both languages."""
    r = statbel_names()[sid]
    out = variants("n", n, r["sector_nl"], r["sector_fr"])
    if c in DISTRICT_I18N:
        nl, fr = DISTRICT_I18N[c]["nl"], DISTRICT_I18N[c]["fr"]
    elif city == "brussels" or c in (r["munty_nl"], r["munty_fr"]):
        nl, fr = r["munty_nl"], r["munty_fr"]
    else:
        nl = fr = None
    return {**out, **variants("c", c, nl, fr)}


def commune_variants(city: str, code: str, name: str) -> dict:
    """`name_nl`/`name_fr` of a commune: a city that is one municipality by CITY_I18N, any other by Statbel."""
    if code in CITY_LAU:
        i18n = CITY_I18N[next(k for k, v in CITIES.items() if v == CITY_LAU[code])]
        return variants("name", name, i18n["nl"], i18n["fr"])
    return variants("name", name, *munty_names(code))


def communes(city: str, proj: "Proj", sectors: list[dict]) -> dict:
    """Each commune's outline, dissolved from its Statbel sectors and drawn in the atlas's coordinates,
    with the Commission's Article 8(1) test from `art8_official_lau_2021.csv`: more than 45 % green and
    10 % canopy in the commune's urban centres and clusters. What leaving out every exempt commune
    would take from the national total is counted as on the Article 8 page (article8_html.py)."""
    from shapely.geometry import MultiPolygon, Polygon, shape
    from shapely.ops import polylabel, transform, unary_union
    path, key = SECTORS_GEO[city]
    groups: dict[str, list] = collections.defaultdict(list)
    for f in json.loads((ROOT / path).read_text())["features"]:
        groups[str(f["properties"][key])[:5]].append(shape(_flat(f["geometry"])).buffer(0))
    names = {code: CITY_LAU.get(code) or collections.Counter(s["c"] for s in sectors if s["id"][:5] == code).most_common(1)[0][0]
             for code in groups}
    # shares from the summary (six decimals), not the layer's four: rounding 0.60848 to 0.6085 first and then to a
    # tenth of a per cent printed Uccle 60.9 % and Molenbeek 27.1 % against 60.8 and 27.0 on the Article 8 pages
    lau = {r["lau_id"][3:]: {k: str(v) for k, v in r.items()}
           for r in json.loads((ROOT / f"cities/{city}/layers/art8_official_2021_summary.json").read_text())["laus"]}
    out = []
    for code, polys in sorted(groups.items()):
        # sectors do not tile exactly: a 1-m buffer closes the slivers between them, and the holes and
        # crumbs it leaves are dropped, so no stray line is drawn inside a commune
        u = unary_union(polys).buffer(1e-5).buffer(-1e-5)
        parts = [u] if u.geom_type == "Polygon" else list(u.geoms)
        big = max(q.area for q in parts)
        parts = [Polygon(q.exterior) for q in parts if q.area > 0.01 * big]
        u = parts[0] if len(parts) == 1 else MultiPolygon(parts)
        g = transform(lambda x, y, z=None: proj(x, y), u).simplify(0.4, preserve_topology=True)
        main = g if g.geom_type == "Polygon" else max(g.geoms, key=lambda q: q.area)
        lp, r = polylabel(main, tolerance=1.0), lau.get(code)   # the point farthest from the edges
        out.append({"code": code, "name": names[code], **commune_variants(city, code, names[code]), "d": _svg_path(g), "x": round(lp.x, 1), "y": round(lp.y, 1),
                    "area": round(g.area),
                    **({"green": float(r["green_ucuc"]), "canopy": float(r["canopy_wvl_ucuc"]),
                        # the test's other readings of Article 3(20): farmland (CLCplus class 7) as green,
                        # and water left out; either can turn a verdict near the line
                        "green7": float(r["green_with7_ucuc"]), "green_nw": float(r["green_no_water_ucuc"]),
                        "exempt": r["exempt"] == "True", "stable": r["stable"] == "True",
                        "pop": int(float(r["population"]))} if r else {})})
    laus = list(lau.values())
    ex = [r for r in laus if r["exempt"] == "True"]
    region = json.loads((ROOT / f"cities/{city}/layers/art8_official_2021_summary.json").read_text())["region"]
    res = {"list": out, "tested": len(laus), "exempt": len(ex),
           "region": {"green": region["parts"]["ucuc"]["green"], "exempt": region["exempt"]} if len(laus) > 1 else None}
    if ex and len(laus) > 1:
        f = lambda rs, k: sum(float(r[k]) for r in rs)
        rest = [r for r in laus if r["exempt"] != "True"]
        res["leave_out"] = {
            "area": round(f(ex, "area_km2_all") / f(laus, "area_km2_all"), 3),
            "residents": round(f(ex, "population") / f(laus, "population"), 3),
            "woody": round(sum(float(r["canopy_wvl_all"]) * float(r["area_km2_all"]) for r in ex)
                           / sum(float(r["canopy_wvl_all"]) * float(r["area_km2_all"]) for r in laus), 3),
            "rest": len(rest),
            "rest_green": round(sum(float(r["green_ucuc"]) * float(r["area_km2_ucuc"]) for r in rest) / f(rest, "area_km2_ucuc"), 3),
        }
    return res


def registered(city: str, proj: "Proj") -> list[dict]:
    """The projects registered before their works (engine/registries/preregistration.py): footprint,
    date, the baseline taken then and the 12 control places named then, or the refusal fixed then."""
    from shapely.geometry import shape
    from shapely.ops import transform
    recs = [r for r in json.loads((ROOT / "data/registry/preregistered.json").read_text()) if r.get("city") == city]
    if not recs:
        return []
    ctrl = {c["id"]: c for c in json.loads((ROOT / "data/registry/preregistered_controls.json").read_text())}
    base = collections.defaultdict(dict)
    for r in rows("data/registry/preregistered_baseline.csv"):
        base[r["id"]][r["instrument"]] = float(r["value"])
    out = []
    for r in recs:
        g = transform(lambda x, y, z=None: proj(x, y), shape(_flat(r["geometry"]))).simplify(0.2, preserve_topology=True)
        c = g.centroid
        cc = ctrl.get(r["id"], {})
        out.append({"id": r["id"], "name": r["name"].strip(), "type": r["intervention_type"],
                    "registered": r["registered_at"], "hash": r["geometry_hash"],
                    "d": _svg_path(g), "x": round(c.x, 1), "y": round(c.y, 1),
                    "ndvi": round(base[r["id"]].get("ndvi"), 3) if "ndvi" in base[r["id"]] else None,
                    "comparable": bool(cc.get("comparable")), "controls": len(cc.get("control_ids") or []),
                    "gap": round(cc["gap"], 3) if cc.get("gap") is not None else None})
    return out


def heat_canopy_r(sectors: list[dict]) -> float | None:
    """How closely summer heat and canopy move together, over every sector with both (the heat lens's lede)."""
    pairs = [(x["hot"], x["cs"]) for x in sectors if x.get("hot") is not None and x.get("cs") is not None]
    return round(statistics.correlation(*zip(*pairs)), 2) if len(pairs) > 2 else None


def groenkaart_check() -> dict | None:
    """The detector against an independent aerial map (phase 2c, item 5; scripts/official/groenkaart_check.py):
    per Flemish city and pooled, canopy and greenness, how often the two agree on "changed" and on "noise"."""
    per = {}
    for c in ("antwerp", "ghent"):
        p = ROOT / f"cities/{c}/layers/groenkaart_check_summary.json"
        if p.exists():
            per[c] = json.loads(p.read_text())
    if not per:
        return None
    def pool(pair, key):
        k = sum(v["pairs"][pair][key]["k"] for v in per.values())
        n = sum(v["pairs"][pair][key]["n"] for v in per.values())
        return {"k": k, "n": n}
    return {"cities": {c: {pair: {key: {"k": v["pairs"][pair][key]["k"], "n": v["pairs"][pair][key]["n"]}
                                  for key in ("sensitivity", "specificity", "agreement_when_ours_changed", "direction_when_ours_changed")}
                           | {"spearman": v["pairs"][pair]["spearman"], "opposite": v["pairs"][pair]["opposite"]}
                           for pair in ("canopy", "green")} for c, v in per.items()},
            "pooled": {pair: {key: pool(pair, key) for key in ("sensitivity", "specificity", "agreement_when_ours_changed",
                                                                              "direction_when_ours_changed")}
                       for pair in ("canopy", "green")}}


def editions() -> dict:
    """Two editions of the official Article 8 layers, 2018 and 2021 (scripts/official/art8_official_change.py): what the
    official canopy says per city, its noise threshold per sector, and, in Flanders, what an independent aerial map
    says in the same years, with the sector where the two part most. Every number on the site about it comes from here."""
    out = {}
    for c in CITIES:
        s = json.loads((ROOT / f"cities/{c}/layers/art8_official_change_2018_2021_summary.json").read_text())
        e = {"years": [2018, 2021], "canopy_2018": round(s["city_mean"]["canopy_2018"], 4), "canopy_2021": round(s["city_mean"]["canopy_2021"], 4),
             "green_2018": round(s["city_mean"]["green_2018"], 4), "green_2021": round(s["city_mean"]["green_2021"], 4),
             "threshold_canopy": s["calibration"]["canopy"]["threshold"], "threshold_green": s["calibration"]["green"]["threshold"],
             "units": s["units"], "comparable": s["comparable"]}
        if "independent" in s:
            i = s["independent"]
            e["aerial"] = {"units": i["units"], **{k: round(i[k], 4) for k in
                           ("official_canopy_2018", "official_canopy_2021", "aerial_high_2018", "aerial_high_2021")},
                           "example": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in i["example"].items()}}
        out[c] = e
    return out


def facts() -> dict:
    man = {c: Manifest.read(c) for c in CITIES}
    out: dict = {"cities": {}}
    for c in CITIES:
        s8 = json.loads((ROOT / f"cities/{c}/layers/article8_2024_summary.json").read_text())
        off = json.loads((ROOT / f"cities/{c}/layers/art8_official_2021_summary.json").read_text())
        laus = off["laus"]
        terc = s8["equity_income_terciles"]
        out["cities"][c] = {
            "name": CITIES[c],
            "sectors": s8["units_total"], "measured": s8["units_measured"],
            "population": s8["population"],
            "threshold_ndvi": s8["thresholds"]["ndvi"],
            "null_mean_ndvi": s8["thresholds_mean"]["ndvi"],
            "background": background(c),
            "canopy_ratio_poor_rich": round(terc[0]["trees_2024_wmean"] / terc[-1]["trees_2024_wmean"], 2),
            "comparable": s8["units_comparable"],
            "art8": {"laus": len(laus), "exempt": [l["name"] for l in laus if l["exempt"]],
                     "green_ucuc": off["region"]["parts"]["ucuc"]["green"],
                     # the test's other reading of Article 3(20): farmland counted as green
                     "green7_ucuc": off["region"]["parts"]["ucuc"]["green_with7"],
                     # and water left out of green
                     "green_nw_ucuc": off["region"]["parts"]["ucuc"]["green_no_water"],
                     "stable": not off["checks"].get("unstable_laus"),
                     "canopy_r": sorted(v["r"] for v in off["correlations_canopy"].values())},
        }

    # температура: порог из того же нулевого распределения, что у NDVI Брюсселя
    lst = [float(r["lst_effect"]) for r in rows("cities/brussels/layers/sector_change_2017_2024.csv")
           if r.get("lst_effect")]
    out["lst_threshold_c"] = round(max(abs(percentile(lst, 2.5)), abs(percentile(lst, 97.5))), 2)

    # отказы и молчание — теми же подсчётами, что страница метода
    def verdicts(path, key="verdict"):
        return collections.Counter(r.get(key, "") for r in rows(path))
    pv = [verdicts("data/park_audit_2017_2024.csv")] + [verdicts(f"data/park_audit_{c}_2017_2024.csv") for c in CITIES if c != "brussels"]
    out["parks"] = {"total": sum(sum(p.values()) for p in pv),
                    "refused": sum(p["контроль несопоставим"] for p in pv),
                    "brussels_total": sum(v for k, v in pv[0].items()),
                    "brussels_refused": pv[0]["контроль несопоставим"],
                    "max_gap": CONTROL["max_gap_ndvi"]}
    out["restorations_noise"] = verdicts("cities/brussels/layers/park_audit_landsat.csv")["шум"]

    from scripts.report.monitoring_html import apply_documents, funnel, load_layer
    mon = []
    for c in CITIES:
        for k in sorted(man[c].layers):
            if not k.startswith("monitoring_"):
                continue
            s = int(k.split("_")[1])
            if not (ROOT / f"cities/{c}/layers/monitoring_{s}.csv").exists():
                continue
            F = funnel(apply_documents(load_layer(c, s), c, s), man[c].layers[k].threshold)
            mon.append({"city": c, "season": s, "candidates": len(F["lost"]),
                        "construction": len(F["construction"]), "confirmed": len(F["confirmed"]),
                        "confirmed_names": [r["name"].title() for r in F["confirmed"]]})
    out["monitoring"] = mon
    out["controls_n"] = CONTROL["n_controls"]
    out["min_scenes"] = QUALITY["min_scenes"]
    # тесты — как их считает pytest: параметризованные раскрываются в отдельные случаи
    col = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
                         cwd=ROOT, capture_output=True, text=True).stdout
    m = re.search(r"(\d+) tests? collected", col)
    out["tests"] = int(m.group(1)) if m else None
    out["layers"] = {c: len(man[c].layers) for c in CITIES}
    out["check"] = groenkaart_check()
    out["editions"] = editions()
    bv = json.loads((ROOT / "cities/brussels/layers/be_vegetation_2021_2023_summary.json").read_text())
    # the region's own vegetation map, 2021 and 2023, through the same threshold (scripts/official/brussels_vegetation_check.py)
    out["be_vegetation"] = {"years": [2021, 2023], "share_2021": bv["region_share_2021"], "share_2023": bv["region_share_2023"],
                            "threshold": bv["calibration"]["threshold"], "verdicts": bv["verdicts"],
                            "loss_ha": bv["loss_beyond_noise_ha"], "gain_ha": bv["gain_beyond_noise_ha"],
                            "raw_change_ha": bv["raw_change_ha_comparable"], "example": bv.get("example")}
    return out


def case_data(slug: str) -> dict:
    c = json.loads((ROOT / f"data/registry/cases/{slug}.json").read_text())
    city = CITY_RU[c["city"]]
    imgs = {}
    for k, src in (c.get("images") or {}).items():
        p = ROOT / src
        if p.exists():
            (SITE / "cases").mkdir(parents=True, exist_ok=True)
            dst = SITE / "cases" / f"{slug}-{k}.png"
            shutil.copyfile(p, dst)
            imgs[k] = f"cases/{dst.name}"
    ot = c.get("over_time") or {}
    years = [int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", str(c.get("completed", "")))]
    return {
        "slug": slug, "city": city, "name": c["name"].split(",")[0],
        "area_ha": c["area_ha"], "completed": max(years) if years else None,
        "window_before": c["window_before"], "window_after": c["window_after"],
        "calibration_n": int(c["calibration_n"]),
        "instruments": [{k: i.get(k) for k in ("key", "before", "after", "effect", "threshold", "significant")}
                        for i in c["instruments"]],
        "controls": [{"id": x["id"], "name": x["name"],
                      **variants("name", x["name"], statbel_names()[x["id"]]["sector_nl"], statbel_names()[x["id"]]["sector_fr"]),
                      "dist_km": x.get("dist_km")} for x in c["controls"]],
        "control_gap": c.get("control_gap"),
        "defensible_effect": c.get("defensible_effect"),
        "series": {"threshold": ot.get("threshold_audit"),
                   "seasons": [{"season": s["season"], "effect": s["effect"], "scenes": s.get("scenes")}
                               for s in ot.get("seasons", [])]},
        "images": imgs,
        "second_instrument": c.get("second_instrument") is None,
    }


REGION = {"brussels": "Brussels-Capital Region", "antwerp": "Flemish Region", "ghent": "Flemish Region",
          "liege": "Walloon Region", "charleroi": "Walloon Region"}
BV = {"рост": "up", "потеря": "down", "шум": "noise", "контроль несопоставим": "refused"}


def commune_pages(city: str, d: dict) -> list[dict]:
    """The commune page (phase 2c, item 3): for each commune the Commission's test was run on, what the law counts
    there and what changed. Every number is already in the packages: the test and its readings
    (art8_official, art8_sensitivity), the zero measurement in hectares (art8_baseline), the balance since the
    2024 base (art8_balance, the city's `balance`), the 2017–2024 verdicts of the sectors, the seasons after the
    base as the bulletins read them, the projects registered before their works and the audit cases."""
    from shapely.geometry import shape
    from scripts.site.downloads import _monitoring
    tested = [c for c in d["communes"]["list"] if c.get("green") is not None]
    if not tested:
        return []
    lau = {r["lau_id"][3:]: r for r in rows(f"cities/{city}/layers/art8_official_lau_2021.csv")}
    base = {r["lau_id"].rsplit(".", 1)[1]: r for r in rows(f"cities/{city}/layers/art8_baseline_2021.csv") if r["lau_id"]}
    sens = collections.defaultdict(list)
    for r in rows(f"cities/{city}/layers/art8_sensitivity_2021.csv"):
        sens[r["lau_id"].rsplit(".", 1)[1]].append({"reading": r["reading"], "green": fl(r, "green_pct", 2),
                                                    "canopy": fl(r, "canopy_pct", 2),
                                                    "exempt": None if r["exempt"] == "" else r["exempt"] == "True"})
    region_row = next((r for r in rows(f"cities/{city}/layers/art8_baseline_2021.csv") if not r["lau_id"]), None)
    # the seasons after the base, as the bulletins read them (after the documents)
    events = collections.defaultdict(list)
    for season in (2025, 2026):
        if not (ROOT / f"cities/{city}/layers/monitoring_{season}.csv").exists():
            continue
        for r in _monitoring(city, season):
            if r["bulletin"] in ("canopy loss", "construction"):
                nm = statbel_names()[r["id"]]
                events[r["id"][:5]].append({"season": season, "id": r["id"], "name": r["name"],
                                            **variants("name", r["name"], nm["sector_nl"], nm["sector_fr"]),
                                            "kind": r["bulletin"], "effect": fl(r, "effect")})
    # registered footprints: the commune of the sector their centroid falls in
    path, key = SECTORS_GEO[city]
    geo = [(str(f["properties"][key]), shape(_flat(f["geometry"]))) for f in json.loads((ROOT / path).read_text())["features"]]
    reg_by = collections.defaultdict(list)
    for rec in json.loads((ROOT / "data/registry/preregistered.json").read_text()):
        if CITY_RU.get(rec.get("city")) != city and rec.get("city") != city:
            continue
        pt = shape(rec["geometry"]).representative_point()
        hit = next((sid for sid, g in geo if g.contains(pt)), None)
        if hit:
            reg_by[hit[:5]].append(rec["id"])
    reg = {r["id"]: r for r in d.get("registered") or []}
    names = {c["code"]: c["name"] for c in d["communes"]["list"]}
    case_by = collections.defaultdict(list)
    for slug in CASES:
        c = json.loads((ROOT / f"data/registry/cases/{slug}.json").read_text())
        if CITY_RU.get(c["city"]) != city:
            continue
        parts = [x.strip().split("-Ville")[0] for x in c.get("commune", "").split("·")]
        for code, n in names.items():
            if code in lau and (len(tested) == 1 or any(n.split("-")[0].split(" ")[0] == x.split(" ")[0] for x in parts)):
                case_by[code].append(slug)
    bal = d.get("balance")
    trees = {}
    tp = ROOT / f"cities/{city}/layers/trees_register_summary.json"
    if tp.exists():
        T = json.loads(tp.read_text())
        trees[T["commune"]] = {k: T[k] for k in ("date", "trees", "planted", "where", "previous", "licence") if k in T}
    out = []
    for c in tested:
        code, r, b = c["code"], lau[c["code"]], base.get(c["code"], {})
        secs = [x for x in d["sectors"] if x["id"][:5] == code]
        meas = [x for x in secs if x.get("nv")]
        nv = lambda x: {k: x[k] for k in ("n_nl", "n_fr") if k in x}   # the sector's own variants (place_variants)
        top = lambda key, vk, ks: [{"id": x["id"], "n": x["n"], **nv(x), "e": x[key], "v": x[vk]}
                                   for x in sorted((x for x in secs if x.get(vk) in ks and x.get(key) is not None),
                                                   key=lambda x: -abs(x[key]))[:6]]
        pop = int(float(r["population"]))
        canopy_ha = float(b["canopy_lau_ha"]) if b else None
        name = CITIES[city] if len(tested) == 1 else c["name"]
        i18n = CITY_I18N[city] if len(tested) == 1 else {"nl": c.get("name_nl"), "fr": c.get("name_fr")}
        out.append({
            "code": code, "city": city, "city_name": CITIES[city], "region": REGION[city], "region_key": REGION_KEY[city],
            "name": name, **variants("name", name, i18n["nl"], i18n["fr"]), "official": r["name"],
            "lau_id": f"lau2024.BE.{code}", "pop": pop, "area_km2": float(r["area_km2_official"]),
            "sectors": len(secs), "measured": len(meas),
            "art8": {"green": c["green"], "canopy": c["canopy"], "exempt": c["exempt"], "stable": c["stable"],
                     "readings": sens.get(code, []),
                     "canopy_m2_per_resident": round(canopy_ha * 10000 / pop, 1) if canopy_ha and pop else None,
                     "region": ({"green": float(region_row["green_ucuc_pct"]) / 100, "canopy": float(region_row["canopy_ucuc_pct"]) / 100,
                                 "exempt": region_row["exempt"] == "True", "n": len(tested)} if region_row else None)},
            "baseline": {k: fl(b, k, 4) for k in ("uea_ucuc_ha", "green_ucuc_ha", "green_ucuc_pct", "canopy_ucuc_ha", "canopy_ucuc_pct",
                                                  "uea_lau_ha", "green_lau_ha", "green_lau_pct", "canopy_lau_ha", "canopy_lau_pct")} if b else None,
            "balance": ({"base": bal["base"], "latest": bal["latest"], "preliminary": bal["preliminary"],
                         "seasons": {sn: sv["by_commune"].get(code, {k: {"lost": 0.0, "gained": 0.0, "net": 0.0} for k in BAL_CLASSES})
                                     for sn, sv in bal["seasons"].items()}} if bal else None),
            "change": {"window": d["window"],
                       "counts": {k: sum(x.get("nv") == k for x in secs) for k in ("up", "down", "noise", "refused")},
                       "built": {k: sum(x.get("bv") == k for x in secs) for k in ("up", "down")},
                       "top": top("ne", "nv", ("up", "down")), "top_built": top("be", "bv", ("up", "down"))},
            "events": sorted(events.get(code, []), key=lambda e: (e["season"], e["name"])),
            "registered": [{"id": i, "name": reg[i]["name"], "type": reg[i]["type"], "comparable": reg[i]["comparable"]}
                           for i in reg_by.get(code, []) if i in reg],
            "cases": case_by.get(code, []),
            # the city's tree register, where it covers this commune (scripts/registry/tree_registers.py)
            "trees": trees.get(code),
            "dossier": next(({"id": x["id"], "n": x["n"], **nv(x)} for x in secs if d["dossier"]["pick"]["ids"] and x["id"] == d["dossier"]["pick"]["ids"][0]), None),
        })
    return out


def main() -> int:
    # plan 5, L5: every language with data texts must be complete and valid before anything is written — a partial or
    # bad catalogue (scripts/site/i18n/<loc>.json) stops the run here and leaves the tree as it was
    from scripts.site import i18n_sync
    found = i18n_sync.problems(i18n_sync.collect())
    if found:
        print("data texts not ready, nothing written:\n  " + "\n  ".join(found), file=sys.stderr)
        return 1
    (SITE / "data").mkdir(parents=True, exist_ok=True)
    pages = []
    for c in CITIES:
        d = city_data(c)
        pages += commune_pages(c, d)
        (SITE / "data" / f"{c}.json").write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")))
        print(f"  {c}.json  {len(d['sectors'])} секторов, дел {len(d['cases'])}, "
              f"{(SITE / 'data' / f'{c}.json').stat().st_size // 1024} КБ")
    (SITE / "data" / "communes.json").write_text(json.dumps(pages, ensure_ascii=False, separators=(",", ":")))
    print(f"  communes.json  {len(pages)} коммун, {(SITE / 'data' / 'communes.json').stat().st_size // 1024} КБ")
    f = facts()
    (SITE / "data" / "facts.json").write_text(json.dumps(f, ensure_ascii=False, indent=1))
    print(f"  facts.json  тестов {f['tests']}, порог температуры {f['lst_threshold_c']} °C, "
          f"отказов по контролю {f['parks']['refused']} из {f['parks']['total']}")
    for c in CITIES:
        pd = points_data(c)
        if pd:
            (SITE / "data" / f"points-{c}.json").write_text(json.dumps(pd, ensure_ascii=False, separators=(",", ":")))
            print(f"  points-{c}.json  {len(pd['types'])} типов, {len(pd['points'])} точек, "
                  f"вне секторов {sum(p['s'] is None for p in pd['points'])}")
    cases = [case_data(s) for s in CASES]
    (SITE / "data" / "cases.json").write_text(json.dumps(cases, ensure_ascii=False, indent=1))
    print(f"  cases.json  {', '.join(c['slug'] for c in cases)}")
    # the data download with its English manifest (phase 2b): after the points, which it reads
    from scripts.site.downloads import write_all
    for c, v in write_all().items():
        print(f"  downloads/{c}  {len(v['layers'])} слоёв, {sum(l['bytes'] for l in v['layers']) // 1024} КБ")
    # the register of interventions read by a language model (phase 2b)
    from scripts.site.register import write as write_register
    r = write_register()
    print(f"  register.json  {len(r['contracts'])} контрактов {r['counts']}, "
          f"проверка {'есть' if r['eval'] else 'ждёт меток'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
