#!/usr/bin/env python3
"""
Аудит парков с ИЗВЕСТНОЙ датой сдачи — окно под проект, порог под окно, второй прибор.

Зачем
─────
Пакетный аудит парков (`audit_parks_city.py`) даты не знает и меряет всех одним
окном 2017–2019 → 2021–2024. Урок Droogdokkenpark: стандартная база поймала
стройплощадку, эффект оказался раздут вдвое (+0,29 → +0,15). Для парка с датой
сдачи окно обязано строиться от даты: `windows_for_completion(year)`.

Порог — под окно: на каждом окне все секторы города по очереди играют плацебо
(тот же прогон, тот же подбор контроля), как в `audit_beliris_landsat.py`.

Второй прибор — классы Dynamic World с порогами из манифеста города: словарь
исходов «раскрыли и озеленили / крона выросла / голый грунт → трава / стройка».

Вход: `data/registry/<city>_park_links.csv` — связи проект→парк с полями
`park`, `completed_year`, `completed_basis`, `name_match` (берутся только
совпадения по имени). Для Антверпена это `agvespa_park_links.csv`.
Проекты, сданные до 2018-го, Sentinel-2 не берёт — печатаются как
«нужен Landsat», не считаются.

Запуск:  .venv/bin/python scripts/gee/audit_parks_dated.py --project <id> --city antwerp
"""
from __future__ import annotations
import argparse, csv, json, statistics, sys
from collections import Counter, defaultdict
from pathlib import Path
import ee
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS, dist_m
from engine.audit import instrument_for, windows_for_completion
from engine.calibrate import calibrate
from engine.config import CITIES, CONTROL, QUALITY, SUMMER_MONTHS
from engine.instruments import REGISTRY
from engine.manifest import Manifest
from engine.instruments.landsat import LEGACY, MODERN, _prep

LINKS = {"antwerp": Path("data/registry/agvespa_park_links.csv"),
         "brussels": Path("data/registry/beliris_park_links.csv")}
DW = ("built", "trees", "grass", "bare")


def s2_ndvi(geom, start, end):
    cs = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    def f(img):
        return (img.normalizedDifference(["B8", "B4"]).rename("ndvi")
                .updateMask(img.select("cs_cdf").gte(QUALITY["cloud_score_plus_min"])))
    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(geom).filterDate(start, end)
            .filter(ee.Filter.calendarRange(SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", QUALITY["max_cloud_pct"]))
            .linkCollection(cs, ["cs_cdf"]).map(f).median())


def landsat_ndvi(geom, start, end):
    modern = ee.ImageCollection(MODERN[0]).merge(ee.ImageCollection(MODERN[1]))
    legacy = ee.ImageCollection(LEGACY[0]).merge(ee.ImageCollection(LEGACY[1]))
    def win(c):
        return (c.filterBounds(geom).filterDate(start, end)
                .filter(ee.Filter.calendarRange(SUMMER_MONTHS[0], SUMMER_MONTHS[1], "month"))
                .filter(ee.Filter.lt("CLOUD_COVER", QUALITY["max_cloud_pct"])))
    return (win(modern).map(lambda i: _prep(i, "SR_B5", "SR_B4"))
            .merge(win(legacy).map(lambda i: _prep(i, "SR_B4", "SR_B3"))).median())


def qualify(verdict: str, n_before: int | None, n_after: int | None,
            min_scenes: int = QUALITY["min_scenes"]) -> str:
    """Понизить вердикт до предварительного, если сцен в окне меньше порога качества.

    Нужно потому, что приоритет Sentinel-2 на мелком следе сжимает окно «до» до
    одного года, а один летний сезон 2017-го — это 1–2 годные сцены. Движок в
    `audit_footprint` такой аудит отказывается считать; здесь объект не выбрасывается,
    но и в один ряд с полноценными не ставится: число сцен печатается рядом.
    """
    if verdict not in ("ПОЗЕЛЕНЕЛ", "ПОТЕРЯЛ"):
        return verdict
    if (n_before or 0) < min_scenes or (n_after or 0) < min_scenes:
        return f"предварительно: {verdict.lower()}"
    return verdict


def outcome(d: dict, thr: dict) -> str:
    """Словарь исходов по второму прибору — те же правила, что в audit_parks_city."""
    sig = {k: (v is not None and abs(v) > thr[k]) for k, v in d.items()}
    up = lambda k: sig[k] and d[k] > 0
    dn = lambda k: sig[k] and d[k] < 0
    if up("built"):
        return "стройка / застройка"
    if dn("built") and (up("grass") or up("trees")):
        return "раскрыли и озеленили"
    if dn("built") and not (up("grass") or up("trees")):
        return "раскрыли, но не засадили"
    if dn("bare") and up("grass"):
        return "голый грунт → трава"
    if up("trees") and not sig["built"]:
        return "крона выросла без смены покрытия"
    return "неоднозначно"


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--project", required=True)
    ap.add_argument("--city", choices=list(CITIES), default="antwerp")
    args = ap.parse_args(); ee.Initialize(project=args.project)
    city = args.city; cfg = CITIES[city]
    out = Path(f"data/registry/{city}_park_audit_dated.csv")

    links = [r for r in csv.DictReader(LINKS[city].open()) if r["name_match"] == "True"]
    parks = {f["properties"]["name"]: f for f in json.load(Path(f"data/perimeters/parks_{city}.geojson").open())["features"]}
    thr_dw = {k: v.threshold for k, v in Manifest.read(city).layers.items() if k in DW}
    ad = ADAPTERS[city](); units = ad.units(); meta = {u.id: u for u in units}
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(u.geometry), {"id": u.id}) for u in units])
    b = cfg["bbox"]; region = ee.Geometry.Rectangle([b[0], b[1], b[2], b[3]])

    todo, skipped = [], Counter()
    seen = set()
    for r in links:
        y = int(r["completed_year"]) if r["completed_year"] not in ("", "None") else None
        key = (r["project"], r["park"])
        if key in seen: continue
        seen.add(key)
        if y is None: skipped["срок неизвестен"] += 1; continue
        if r["park"] not in parks: skipped["парк не в перечне"] += 1; continue
        area = float(parks[r["park"]]["properties"].get("area_ha") or 0)
        choice = instrument_for(y, area)      # прибор выбирает движок: год И размер следа
        if not choice:
            skipped["окно «после» ещё не наступило"] += 1; continue
        instr, w, caveat = choice
        todo.append((r["project"], y, r["completed_basis"], r["park"], w, instr, caveat))
    print(f"связей по имени: {len(links)}; пригодных к аудиту S2: {len(todo)}; пропущено: {dict(skipped)}")
    by_win = defaultdict(list)
    for t in todo: by_win[(t[4]["before"], t[4]["after"], t[5])].append(t)
    print(f"различных окон: {len(by_win)}\n")

    rows_out = []
    for (bw, aw, instr), items in sorted(by_win.items()):
        label = f"{bw[0][:4]}–{bw[1][:4]} → {aw[0][:4]}–{aw[1][:4]}"
        med = s2_ndvi if instr == "ndvi" else landsat_ndvi; scale = 10 if instr == "ndvi" else 30
        stack = med(region, *bw).rename("nb").addBands(med(region, *aw).rename("na"))
        rows = stack.reduceRegions(fc, ee.Reducer.mean(), scale).getInfo()["features"]
        table = []
        for q in (x["properties"] for x in rows):
            u = meta[q["id"]]
            if q.get("nb") is None or q.get("na") is None or u.area_ha < CONTROL["min_area_ha"]: continue
            table.append({"id": u.id, "name": u.name, "ndvi_before": q["nb"], "lst_before": q["nb"],
                          "ndvi_delta": q["na"] - q["nb"], "centroid": u.centroid})
        cal = calibrate(table, "ndvi", "ndvi_before", "lst_before")
        print(f"[{instr}] ", end="")
        if len(table) < 0.9 * len(units):
            print(f"⚠ пул сжался до {len(table)} из {len(units)} — маска облаков; ", end="")
        print(f"окно {label}: секторов {cal.n}, порог {cal.threshold:.4f}, среднее {cal.mean:+.5f} {'(несмещён)' if cal.unbiased else '⚠ смещён'}")
        for title, y, basis, pname, w, instr, caveat in items:
            park = parks[pname]; g = ee.Geometry(park["geometry"])
            nd = REGISTRY[instr]; bb = nd.measure(g, *bw); aa = nd.measure(g, *aw)
            if bb.value is None or aa.value is None:
                print(f"   {title[:40]:<42} нет данных"); continue
            c = park["geometry"]["coordinates"]
            while isinstance(c[0][0], list): c = c[0]
            cen = (sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c))
            cands = sorted((o for o in table if dist_m(cen, o["centroid"]) >= CONTROL["exclusion_m"]),
                           key=lambda o: abs(o["ndvi_before"] - bb.value))[:CONTROL["n_controls"]]
            ctrl_nb = statistics.mean(o["ndvi_before"] for o in cands)
            eff = (aa.value - bb.value) - statistics.mean(o["ndvi_delta"] for o in cands)
            gap = bb.value - ctrl_nb
            if abs(gap) > CONTROL["max_gap_ndvi"]: verdict = "контроль несопоставим"
            elif eff > cal.threshold: verdict = "ПОЗЕЛЕНЕЛ"
            elif eff < -cal.threshold: verdict = "ПОТЕРЯЛ"
            else: verdict = "шум"
            dwd = {}
            if verdict in ("ПОЗЕЛЕНЕЛ", "ПОТЕРЯЛ") and bw[0] >= "2016":   # Dynamic World есть с середины 2015
                ctrl_geoms = ee.FeatureCollection([ee.Feature(ee.Geometry(meta[o["id"]].geometry)) for o in cands])
                for k in DW:
                    inst = REGISTRY[k]
                    sb, sa = inst.measure(g, *bw).value, inst.measure(g, *aw).value
                    cb = inst.measure(ctrl_geoms.geometry(), *bw).value; ca = inst.measure(ctrl_geoms.geometry(), *aw).value
                    dwd[k] = ((sa - sb) - (ca - cb)) if None not in (sb, sa, cb, ca) else None
                dw_out = outcome(dwd, thr_dw)
            else:
                dw_out = ""
            # Landsat 30 м на объекте < 3 га — 11–30 пикселей: вердикт предварительный.
            # Тот же порог, что в аудите Beliris; помечается, а не прячется.
            if instr == "ndvi_landsat" and park["properties"]["area_ha"] < 3:
                verdict = "мелкий для 30 м"
            verdict = qualify(verdict, bb.n_scenes, aa.n_scenes)
            print(f"   {title[:40]:<42} {y} ({basis:<10}) {pname[:24]:<26}{park['properties']['area_ha']:>6.1f} га  "
                  f"сцен {bb.n_scenes}/{aa.n_scenes}  {eff:+.4f}  {verdict}  {dw_out}")
            if caveat:
                print(f"      ⚠ {caveat}")
            rows_out.append({"project": title, "completed_year": y, "completed_basis": basis, "park": pname, "instrument": instr,
                             "osm": park["properties"]["osm"], "area_ha": park["properties"]["area_ha"], "window": label,
                             "scenes_before": bb.n_scenes, "scenes_after": aa.n_scenes,
                             "ndvi_before": round(bb.value, 4), "ndvi_after": round(aa.value, 4),
                             "effect": round(eff, 4), "threshold": round(cal.threshold, 4), "gap": round(gap, 4),
                             "verdict": verdict, "dw_outcome": dw_out, "caveat": caveat,
                             **{f"dw_{k}": (round(v, 4) if v is not None else "") for k, v in dwd.items()},
                             "control_ids": ";".join(o["id"] for o in cands)})
    if rows_out:
        keys = sorted({k for r in rows_out for k in r}, key=lambda k: (k.startswith("dw_"), k))
        with out.open("w", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=keys); wr.writeheader(); wr.writerows(rows_out)
    print(f"\nвердикты: {dict(Counter(r['verdict'] for r in rows_out))}\n→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
