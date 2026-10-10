#!/usr/bin/env python3
"""
Сборка дела аудита: всё числовое — движком, всё человеческое — не трогаем.

Дело (`data/registry/cases/<slug>.json`) состоит из двух слоёв:
  · ВЫЧИСЛЯЕМОЕ — контроль поимённо, эффект, разрыв, база до работ, пять классов
    покрытия, пороги, число сцен. Этот скрипт их считает и перезаписывает.
  · ЧЕЛОВЕЧЕСКОЕ — документы, кластер, границы, чтения, однострочный вывод.
    Скрипт их сохраняет как есть; если дела ещё нет — оставляет пустыми.

Так страница воспроизводима и при этом не превращается в шаблонный текст:
числа нельзя подправить руками, слова нельзя сгенерировать мимо человека.

Контроль: 12 ближайших по NDVI «до» секторов не ближе 1500 м — как на обеих
опубликованных страницах. Эффект считается против ИМЕННО этих двенадцати,
чтобы число на странице можно было пересчитать по ней самой.

Порог — схемой самого дела, тем же прогоном (с 26.09.2026)
──────────────────────────────────────────────────────────
Раньше порог брался у прибора из манифеста, а там подбор другой: в Брюсселе
по зелёности и температуре «до», у дела — по одной зелёности. Порог обязан
отвечать измерению, поэтому теперь каждый сектор той же таблицы по очереди
играет «вмешательство», ему подбираются 12 мест по правилам дела, и 95-й
процентиль этих эффектов и есть порог (`engine.calibrate`).

Классы Dynamic World раньше сравнивались сырой разницей на следе с порогом,
откалиброванным на эффектах против контроля. Теперь и они считаются против тех
же двенадцати мест: изменения классов по всем секторам берутся из таблицы
`scripts/gee/sector_landcover.py`, из неё же строится их нулевое распределение.

Запуск:
    .venv/bin/python scripts/report/audit_case.py --project <id> --city antwerp \\
        --osm way/572550498 --slug droogdokkenpark --base 2016
    .venv/bin/python scripts/report/audit_case.py --city brussels --slug ninove --recalibrate
        без Earth Engine: замеры на следе остаются из дела, пороги и классы — заново
"""
from __future__ import annotations
import argparse, csv, json, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import dist_m
from engine.calibrate import Calibration, calibrate
from engine.config import CONTROL, WINDOWS

HUMAN = ("title", "name", "city", "type", "commune", "completed", "budget", "source_url", "source_label",
         "population_note", "verdict", "one_line", "reading", "documents", "cluster", "limits", "over_time")
LABELS = {"ndvi": "Зелёность (NDVI)", "built": "Застройка / запечатанность", "grass": "Травяной покров",
          "trees": "Древесная крона", "bare": "Голая поверхность", "shrub": "Кустарник"}
DW = ("built", "grass", "trees", "bare", "shrub")
N_CTRL, EXCL_M = CONTROL["n_controls"], CONTROL["exclusion_m"]
SCHEME = (f"схема самого дела: каждый сектор таблицы по очереди «вмешательство», {N_CTRL} ближайших по NDVI «до», "
          f"не ближе {str(EXCL_M / 1000).replace('.', ',')} км; 95-й процентиль модуля эффекта; тем же прогоном, "
          "что эффект; классы Dynamic World — против тех же мест")


def sector_table(city: str) -> Path:
    for p in (Path(f"data/{city}_sector_change_2017_2024.csv"), Path("data/sector_change_2017_2024.csv")):
        if p.exists() and (city != "antwerp" or "antwerp" in p.name):
            return p
    raise SystemExit(f"нет таблицы секторов для {city}")


def landcover(city: str, window: str) -> dict[str, dict]:
    p = Path(f"data/{city}_sector_landcover_{window}.csv")
    if not p.exists():
        raise SystemExit(f"нет {p}: сначала scripts/gee/sector_landcover.py --city {city} --window {window}")
    return {r["id"]: r for r in csv.DictReader(p.open())}


def change(row: dict | None, k: str) -> float | None:
    if not row or not row.get(f"a_{k}") or not row.get(f"b_{k}"):
        return None
    return float(row[f"a_{k}"]) - float(row[f"b_{k}"])


def pool_units(city: str, lc: dict[str, dict]) -> list[dict]:
    """Секторы одной таблицы: зелёность «до», сырое изменение NDVI и классов, центр."""
    pool = []
    for r in csv.DictReader(sector_table(city).open()):
        o = {"id": r["id"], "name": r.get("name") or r["id"], "nb": float(r["ndvi_before"]),
             "d": float(r["d_ndvi_raw"]), "c": (float(r["lon"]), float(r["lat"]))}
        for k in DW:
            o[k] = change(lc.get(r["id"]), k)
        pool.append(o)
    return pool


def own_thresholds(pool: list[dict]) -> dict[str, Calibration]:
    """Нулевое распределение ТОЙ ЖЕ схемы подбора, что у дела (одна зелёность «до», 12 мест, 1,5 км)."""
    out = {}
    for k in ("ndvi",) + DW:
        src = "d" if k == "ndvi" else k
        units = [{"id": o["id"], "nb": o["nb"], "centroid": o["c"], f"{k}_delta": o[src]}
                 for o in pool if o[src] is not None]
        # один признак дважды: оси равны, порядок — по близости зелёности «до», как у дела
        cal = calibrate(units, k, "nb", "nb", n_controls=N_CTRL, exclusion_m=EXCL_M)
        if not cal.unbiased:
            raise SystemExit(f"нулевое распределение {k} смещено (среднее {cal.mean:+.5f}) — порог недействителен")
        out[k] = cal
    return out


def instrument(k: str, before: float, after: float, effect: float, thr: Calibration, reading: str = "") -> dict:
    return {"key": k, "label": LABELS[k], "before": round(before, 3), "after": round(after, 3),
            "effect": round(effect, 4), "threshold": round(thr.threshold, 5),
            "significant": abs(effect) > thr.threshold, "reading": reading}


def class_rows(ctrl: list[dict], footprint: dict[str, tuple[float, float]], thr: dict[str, Calibration],
               readings: dict[str, str]) -> list[dict]:
    """Классы покрытия: изменение на следе минус среднее изменение тех же двенадцати мест."""
    out = []
    for k in DW:
        x, y = footprint[k]
        vals = [o[k] for o in ctrl if o[k] is not None]
        if len(vals) < len(ctrl):
            raise SystemExit(f"у контроля нет значений класса {k}: {len(vals)} из {len(ctrl)}")
        out.append(instrument(k, x, y, (y - x) - statistics.mean(vals), thr[k], readings.get(k, "")))
    return out


def recalibrate(args) -> int:
    """Пороги и классы заново — без нового замера на следе и без Earth Engine."""
    path = Path(f"data/registry/cases/{args.slug}.json")
    case = json.loads(path.read_text())
    lc = landcover(args.city, args.window)
    pool = pool_units(args.city, lc)
    thr = own_thresholds(pool)
    by_id = {o["id"]: o for o in pool}
    ctrl = [by_id[c["id"]] for c in case["controls"]]
    readings = {i["key"]: i.get("reading", "") for i in case["instruments"]}
    nd = next(i for i in case["instruments"] if i["key"] == "ndvi")
    # эффект NDVI не пересчитывается: след и контроль из одного прогона уже в деле
    check = (nd["after"] - nd["before"]) - statistics.mean(o["d"] for o in ctrl)
    if abs(check - nd["effect"]) > 0.002:
        raise SystemExit(f"эффект NDVI в деле {nd['effect']:+.4f} не сходится с таблицей ({check:+.4f})")
    fp = lc.get(f"osm:{case['osm']}")
    if not fp:
        raise SystemExit(f"следа osm:{case['osm']} нет в таблице классов — перезапустить sector_landcover.py")
    footprint = {k: (float(fp[f"b_{k}"]), float(fp[f"a_{k}"])) for k in DW}
    nd_new = {**nd, "threshold": round(thr["ndvi"].threshold, 5), "significant": abs(nd["effect"]) > thr["ndvi"].threshold}
    case["instruments"] = [nd_new] + class_rows(ctrl, footprint, thr, readings)
    case["calibration_n"] = str(thr["ndvi"].n)
    case["threshold_scheme"] = SCHEME
    if case.get("over_time"):
        case["over_time"]["threshold_audit"] = round(thr["ndvi"].threshold, 5)
    path.write_text(json.dumps(case, ensure_ascii=False, indent=1))
    for i in case["instruments"]:
        print(f"  {i['key']:<6} {i['before']:.3f}→{i['after']:.3f}  эффект {i['effect']:+.4f}  порог {i['threshold']:.5f}  "
              f"{'значимо' if i['significant'] else 'шум'}")
    print(f"→ {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project"); ap.add_argument("--city", required=True)
    ap.add_argument("--osm"); ap.add_argument("--slug", required=True)
    ap.add_argument("--base", type=int, default=2016, help="год базы до работ для проверки на стройку")
    ap.add_argument("--window", default="2017_2024")
    ap.add_argument("--recalibrate", action="store_true",
                    help="без Earth Engine: пороги схемой дела и классы против тех же мест по сохранённым таблицам")
    args = ap.parse_args()
    if args.recalibrate:
        return recalibrate(args)
    if not (args.project and args.osm):
        ap.error("для полного прогона нужны --project и --osm")

    import ee
    from engine.instruments import REGISTRY
    ee.Initialize(project=args.project)

    w = WINDOWS[args.window]
    parks = json.loads(Path(f"data/perimeters/parks_{args.city}.geojson").read_text())["features"]
    park = next(f for f in parks if f["properties"]["osm"] == args.osm)
    c = park["geometry"]["coordinates"]
    while isinstance(c[0][0], list): c = c[0]
    cen = (sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c))

    pool = pool_units(args.city, landcover(args.city, args.window))
    thr = own_thresholds(pool)

    g = ee.Geometry(park["geometry"]); ndvi = REGISTRY["ndvi"]
    b = ndvi.measure(g, *w["before"]); a = ndvi.measure(g, *w["after"])
    b16 = ndvi.measure(g, f"{args.base}-01-01", f"{args.base}-12-31")

    cands = sorted((o for o in pool if dist_m(cen, o["c"]) >= EXCL_M), key=lambda o: abs(o["nb"] - b.value))
    ctrl = cands[:N_CTRL]
    ctrl_nb = statistics.mean(o["nb"] for o in ctrl); ctrl_d = statistics.mean(o["d"] for o in ctrl)
    eff = (a.value - b.value) - ctrl_d; gap = b.value - ctrl_nb
    eff16 = (a.value - b16.value) - ctrl_d if b16.value is not None else None
    gap16 = b16.value - ctrl_nb if b16.value is not None else None

    footprint = {k: (REGISTRY[k].measure(g, *w["before"]).value, REGISTRY[k].measure(g, *w["after"]).value) for k in DW}
    inst = [instrument("ndvi", b.value, a.value, eff, thr["ndvi"])] + class_rows(ctrl, footprint, thr, {})

    key = args.osm.replace("/", "_")
    computed = {
        "slug": args.slug, "osm": args.osm, "area_ha": park["properties"]["area_ha"],
        "window_before": w["label"].split(" → ")[0], "window_after": w["label"].split(" → ")[1],
        "image_note": f"Сцен: {b.n_scenes} в окне «до», {a.n_scenes} в окне «после».",
        "calibration_n": str(thr["ndvi"].n),
        "threshold_scheme": SCHEME,
        "instruments": inst,
        "controls": [{"id": o["id"], "name": o["name"], "ndvi_before": round(o["nb"], 3),
                      "d_ndvi_raw": round(o["d"], 4), "dist_km": round(dist_m(cen, o["c"]) / 1000, 1)} for o in ctrl],
        "control_gap": round(gap, 4),
        "timing_rows": [
            {"window": f"{w['label'].split(' → ')[0]}, стандарт", "scenes": b.n_scenes, "ndvi_before": round(b.value, 3),
             "effect": round(eff, 4), "gap": round(gap, 4)},
            {"window": f"{args.base}, до работ", "scenes": b16.n_scenes, "ndvi_before": round(b16.value, 3) if b16.value else None,
             "effect": round(eff16, 4) if eff16 is not None else None, "gap": round(gap16, 4) if gap16 is not None else None}],
        "images": {"before": f"data/exports/{key}_before.png", "after": f"data/exports/{key}_after.png",
                   "delta": f"data/exports/{key}_delta_relative.png"},
        "_ctrl_d": round(ctrl_d, 4),
    }

    path = Path(f"data/registry/cases/{args.slug}.json"); path.parent.mkdir(parents=True, exist_ok=True)
    case = json.loads(path.read_text()) if path.exists() else {}
    # человеческое — сохраняем; вычисляемое — перезаписываем
    for k, v in computed.items():
        if k == "timing_rows":
            tc = case.setdefault("timing_check", {"why": "", "rows": [], "conclusion": ""}); tc["rows"] = v
        elif k == "instruments" and case.get("instruments"):
            old = {i["key"]: i.get("reading", "") for i in case["instruments"]}
            for i in v: i["reading"] = old.get(i["key"], "")
            case[k] = v
        else:
            case[k] = v
    for k in HUMAN:
        case.setdefault(k, [] if k in ("documents", "cluster", "limits") else "")
    if case.get("over_time"):
        case["over_time"]["threshold_audit"] = round(thr["ndvi"].threshold, 5)
    path.write_text(json.dumps(case, ensure_ascii=False, indent=1))
    print(f"{park['properties']['name']} · NDVI {b.value:.3f}→{a.value:.3f} · эффект {eff:+.4f} · порог {thr['ndvi'].threshold:.4f} · "
          f"разрыв {gap:+.4f} · база {args.base}: {eff16:+.4f} (разрыв {gap16:+.4f}, {b16.n_scenes} сцен)")
    print(f"→ {path}   снимки: export_before_after.py --city {args.city} --footprint <имя> --baseline {ctrl_d:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
