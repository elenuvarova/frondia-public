#!/usr/bin/env python3
"""
Как часто детектор изменений ошибается — сверка с независимой картой зелени (фаза 2c, пункт 5).

Внешний прибор
──────────────
Groenkaart Vlaanderen (ANB / Digitaal Vlaanderen, Modellicentie gratis hergebruik): классификация летних
аэрофото 1 м — 1 «высокая зелень» (выше 3 м), 2 «низкая зелень», 3 «сельское хозяйство», 4 «не зелень»,
0 — без класса. Выпуски 2009…2024 каждые три года, WCS geo.api.vlaanderen.be/ANB/wcs (Grnkrt18, Grnkrt21,
Grnkrt24). Другой сенсор (аэрофото против Sentinel-2), другое разрешение (1 м против 10 м), другой способ
(сегментация по высоте против вероятностей классов). Покрывает только Фландрию: Антверпен и Гент.

Правило сверки — записано ДО результата (26.09.2026)
────────────────────────────────────────────────────
· Окна как у детектора (слой ст. 8, 2017–2019 → 2021–2024): «до» — Groenkaart 2018, «после» — среднее
  2021 и 2024. Доли классов по сектору — пиксели 4 м (WCS scalefactor=4, ближайший сосед), центр пикселя
  в полигоне сектора Statbel (EPSG:31370). Сектор берётся, если классифицировано ≥ 90 % его пикселей
  во всех трёх выпусках.
· Groenkaart проходит через тот же метод: изменение доли минус среднее изменение 12 мест, самых похожих
  до работ по зелёности и температуре (NDVI и LST «до» из слоя ст. 8 — та же схема подбора), свой порог —
  нулевое распределение этого же прогона, отказ при разрыве > 0,04. Карта сама шумит от выпуска к выпуску
  (другой пролёт, засуха лета 2018), поэтому «истиной» служит не её сырая разница, а её вердикт.
· Пары: наша крона (Dynamic World trees) ↔ высокая зелень Groenkaart; наша зелёность (NDVI) ↔ зелень
  Groenkaart (высокая + низкая).
· Числа: чувствительность — из секторов, где Groenkaart видит изменение сверх своего шума, доля, где
  детектор видит его в ту же сторону; специфичность — из секторов в шуме Groenkaart доля, где детектор
  тоже в шуме; согласие вердиктов «изменился» (когда детектор говорит «изменился», доля, где Groenkaart
  согласна по направлению); противоположные знаки — отдельно. Интервалы Уилсона 95 %. Ранговая
  корреляция эффектов (Спирмен) — по всем сопоставимым секторам.
· Это согласие двух независимых приборов, а не ошибка против истины: у Groenkaart свои ошибки.

Запуск:
    .venv/bin/python scripts/official/groenkaart_check.py --city ghent --fetch   # загрузка и доли (сеть)
    .venv/bin/python scripts/official/groenkaart_check.py --city ghent           # сверка (без сети)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import struct
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/registry"))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.calibrate import from_effects  # noqa: E402
from engine.config import CONTROL  # noqa: E402
from engine.controls import match_all  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402
from eval_greening import wilson  # noqa: E402
from scripts.report.paths import OUT  # noqa: E402

WCS = "https://geo.api.vlaanderen.be/ANB/wcs"
YEARS = (2018, 2021, 2024)
RES = 4          # м: scalefactor=4 от 1 м. Ответы по 4 МБ сервер отдаёт по минуте, по 1 МБ — за полсекунды;
                 # сектор от 4 га — от 2 500 пикселей, выборочный шум доли уходит в порог Groenkaart
TILE = 4000      # м на плитку: 1000 × 1000 пикселей, ~1 МБ
MIN_VALID = 0.90
CACHE = OUT / "official-cache" / "groenkaart"


def fetch_tile(year: int, x0: int, y0: int) -> Path:
    """Плитка как её отдаёт WCS: multipart (GML + TIFF). Шлюз Azure режет URI в параметрах, поэтому только
    subset по x/y в родной системе и scalefactor — без outputCrs и interpolation."""
    dest = CACHE / f"gk{year % 100:02d}_{RES}m_{x0}_{y0}.bin"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = (f"{WCS}?service=WCS&version=2.0.1&request=GetCoverage&coverageId=Grnkrt{year % 100:02d}&format=image/tiff"
           f"&subset=x({x0},{x0 + TILE})&subset=y({y0},{y0 + TILE})&scalefactor={RES}")
    tmp = dest.with_name(dest.name + ".part")
    subprocess.run(["curl", "-sS", "--fail", "--retry", "6", "--retry-all-errors", "--retry-delay", "15", "--max-time", "300", "-o", str(tmp), url], check=True)
    tmp.replace(dest)
    return dest


def read_tiff_u8(raw: bytes) -> np.ndarray:
    """Несжатый однополосный uint8 TIFF (плитки или полосы) — ровно то, что отдаёт этот WCS."""
    b = raw[raw.find(b"II*\x00"):] if b"II*\x00" in raw else raw[raw.find(b"MM\x00*"):]
    bo = "<" if b[:2] == b"II" else ">"
    off = struct.unpack(bo + "I", b[4:8])[0]
    n = struct.unpack(bo + "H", b[off:off + 2])[0]
    size = {1: 1, 2: 1, 3: 2, 4: 4, 16: 8}
    fmt = {1: "B", 2: "c", 3: "H", 4: "I", 16: "Q"}
    tags = {}
    for k in range(n):
        e = off + 2 + 12 * k
        tag, typ, cnt = struct.unpack(bo + "HHI", b[e:e + 8])
        if typ not in size:
            continue
        nb = size[typ] * cnt
        data = b[e + 8:e + 8 + nb] if nb <= 4 else b[struct.unpack(bo + "I", b[e + 8:e + 12])[0]:][:nb]
        tags[tag] = struct.unpack(bo + fmt[typ] * cnt, data)
    W, H = tags[256][0], tags[257][0]
    if tags.get(259, (1,))[0] != 1 or tags.get(258, (8,))[0] != 8 or tags.get(277, (1,))[0] != 1:
        raise SystemExit("ждали несжатый однополосный uint8 TIFF")
    out = np.zeros((H, W), np.uint8)
    if 322 in tags:
        tw, th = tags[322][0], tags[323][0]
        across = (W + tw - 1) // tw
        for i, o in enumerate(tags[324]):
            ty, tx = divmod(i, across)
            t = np.frombuffer(b[o:o + tw * th], np.uint8).reshape(th, tw)
            y0, x0 = ty * th, tx * tw
            out[y0:y0 + th, x0:x0 + tw] = t[:min(th, H - y0), :min(tw, W - x0)]
    else:
        rps = tags.get(278, (H,))[0]
        for i, o in enumerate(tags[273]):
            rows = min(rps, H - i * rps)
            out[i * rps:i * rps + rows] = np.frombuffer(b[o:o + rows * W], np.uint8).reshape(rows, W)
    return out


def sectors_31370(city: str) -> dict[str, object]:
    fc = json.loads((ROOT / f"data/{city}_sectors_31370.geojson").read_text())
    return {f["properties"]["id"]: shape(f["geometry"]) for f in fc["features"]}


def fetch_and_aggregate(city: str) -> Path:
    geoms = sectors_31370(city)
    b = shapely.total_bounds(list(geoms.values()))
    X0, Y0 = int(b[0] // TILE * TILE), int(b[1] // TILE * TILE)
    X1, Y1 = int(-(-b[2] // TILE) * TILE), int(-(-b[3] // TILE) * TILE)
    W, H = (X1 - X0) // RES, (Y1 - Y0) // RES
    tiles = [(x, y) for y in range(Y0, Y1, TILE) for x in range(X0, X1, TILE)]
    print(f"{city}: рамка {X0}–{X1} × {Y0}–{Y1} (EPSG:31370), {len(tiles)} плиток × {len(YEARS)} выпуска, {W}×{H} пикс. по {RES} м")
    counts = {sid: {} for sid in geoms}
    for year in YEARS:
        mosaic = np.zeros((H, W), np.uint8)
        for i, (x, y) in enumerate(tiles, 1):
            a = read_tiff_u8(fetch_tile(year, x, y).read_bytes())
            if a.shape != (TILE // RES, TILE // RES):
                raise SystemExit(f"плитка {year} {x} {y}: {a.shape}")
            r0, c0 = (Y1 - (y + TILE)) // RES, (x - X0) // RES
            mosaic[r0:r0 + a.shape[0], c0:c0 + a.shape[1]] = a
            if i % 10 == 0 or i == len(tiles):
                print(f"  {year}: {i}/{len(tiles)} плиток", flush=True)
        for sid, g in geoms.items():
            gx0, gy0, gx1, gy1 = g.bounds
            c0, c1 = max(0, int((gx0 - X0) // RES)), min(W, int(-(-(gx1 - X0) // RES)))
            r0, r1 = max(0, int((Y1 - gy1) // RES)), min(H, int(-(-(Y1 - gy0) // RES)))
            xs = X0 + (np.arange(c0, c1) + 0.5) * RES
            ys = Y1 - (np.arange(r0, r1) + 0.5) * RES
            gx, gy = np.meshgrid(xs, ys)
            inside = shapely.contains_xy(g, gx, gy)
            vals = mosaic[r0:r1, c0:c1][inside]
            counts[sid][year] = {"n": int(inside.sum()), **{k: int((vals == k).sum()) for k in (0, 1, 2, 3, 4)}}
        print(f"  {year}: доли по {len(geoms)} секторам посчитаны", flush=True)
    out = ROOT / f"cities/{city}/layers/groenkaart_2018_2024.csv"
    with out.open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["id", "px"] + [f"{k}_{y}" for y in YEARS for k in ("valid", "high", "low", "agri", "none")])
        for sid in sorted(geoms):
            row = [sid, counts[sid][YEARS[0]]["n"]]
            for y in YEARS:
                c = counts[sid][y]
                v = c[1] + c[2] + c[3] + c[4]
                row += [round(v / c["n"], 6) if c["n"] else ""] + [round(c[k] / v, 6) if v else "" for k in (1, 2, 3, 4)]
            w.writerow(row)
    print(f"→ {out}")
    return out


def spearman(a: list[float], b: list[float]) -> float:
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def rate(k: int, n: int) -> dict:
    return {"k": k, "n": n, "value": round(k / n, 3) if n else None, "ci95": wilson(k, n)}


def verdict(e, t, comp):
    if not comp:
        return "refused"
    return "up" if e > t else "down" if e < -t else "noise"


def analyse(city: str) -> dict:
    VW = {"рост": "up", "потеря": "down", "шум": "noise", "контроль несопоставим": "refused"}
    gk = {r["id"]: r for r in csv.DictReader((ROOT / f"cities/{city}/layers/groenkaart_2018_2024.csv").open())}
    a8 = {r["id"]: r for r in csv.DictReader((ROOT / f"cities/{city}/layers/article8_2024.csv").open())}
    cen = {u.id: u.centroid for u in ADAPTERS[city]().units()}
    units, dropped = [], 0
    for sid, r in a8.items():
        g = gk.get(sid)
        if not g or any(not g[f"valid_{y}"] or float(g[f"valid_{y}"]) < MIN_VALID for y in YEARS):
            dropped += 1
            continue
        f = lambda k, y: float(g[f"{k}_{y}"])
        hi = {y: f("high", y) for y in YEARS}
        gr = {y: f("high", y) + f("low", y) for y in YEARS}
        units.append({"id": sid, "centroid": cen[sid], "ndvi_b": float(r["ndvi_b"]), "lst_b": float(r["lst_b"]),
                      "hg_d": (hi[2021] + hi[2024]) / 2 - hi[2018], "gr_d": (gr[2021] + gr[2024]) / 2 - gr[2018],
                      "our_trees": (float(r["trees_eff"]) if r["trees_eff"] else None, VW[r["trees_verdict"]]),
                      "our_ndvi": (float(r["ndvi_eff"]), VW[r["ndvi_verdict"]])})
    scored = match_all(units, "ndvi_b", "lst_b", ["hg_d", "gr_d"])
    cal = {k: from_effects(k, [s[f"{k}_eff"] for s in scored if s[f"{k}_eff"] is not None]) for k in ("hg_d", "gr_d")}
    res = {"city": city, "computed": date.today().isoformat(), "units": len(units), "dropped": dropped,
           "rule": "Groenkaart 2018 → mean(2021, 2024), 4 m pixels, same 12-place matching, own null distribution",
           "gk_thresholds": {k: round(c.threshold, 5) for k, c in cal.items()},
           "gk_unbiased": {k: c.unbiased for k, c in cal.items()}, "pairs": {}}
    for pair, gk_key, ours in (("canopy", "hg_d", "our_trees"), ("green", "gr_d", "our_ndvi")):
        t = cal[gk_key].threshold
        rows = []
        for s in scored:
            gv = verdict(s[f"{gk_key}_eff"], t, s["comparable"]) if s[f"{gk_key}_eff"] is not None else "refused"
            oe, ov = s[ours]
            if gv == "refused" or ov == "refused" or oe is None:
                continue
            rows.append((gv, ov, s[f"{gk_key}_eff"], oe, s["id"]))
        changed = [r for r in rows if r[0] != "noise"]
        quiet = [r for r in rows if r[0] == "noise"]
        ours_changed = [r for r in rows if r[1] != "noise"]
        table = {g: {o: sum(1 for r in rows if r[0] == g and r[1] == o) for o in ("down", "noise", "up")} for g in ("down", "noise", "up")}
        res["pairs"][pair] = {
            "n": len(rows), "table_gk_by_ours": table,
            "sensitivity": rate(sum(1 for r in changed if r[1] == r[0]), len(changed)),
            "specificity": rate(sum(1 for r in quiet if r[1] == "noise"), len(quiet)),
            "agreement_when_ours_changed": rate(sum(1 for r in ours_changed if r[0] == r[1]), len(ours_changed)),
            # the same direction, whatever Groenkaart's own (higher) threshold says: its effect has the sign of ours
            "direction_when_ours_changed": rate(sum(1 for r in ours_changed
                                                    if (r[2] > 0) == (r[1] == "up") and r[2] != 0), len(ours_changed)),
            "opposite": sum(1 for r in rows if {r[0], r[1]} == {"up", "down"}),
            "spearman": round(spearman([r[2] for r in rows], [r[3] for r in rows]), 3),
            "examples_missed": sorted([r[4] for r in changed if r[1] == "noise"])[:8],
            "examples_unseen": sorted([r[4] for r in ours_changed if r[0] == "noise"])[:8],
        }
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True, choices=["antwerp", "ghent"])
    ap.add_argument("--fetch", action="store_true", help="скачать Groenkaart и посчитать доли по секторам (сеть)")
    args = ap.parse_args()
    if args.fetch:
        fetch_and_aggregate(args.city)
    res = analyse(args.city)
    out = ROOT / f"cities/{args.city}/layers/groenkaart_check_summary.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    m = Manifest.read(args.city)
    m.add(LayerEntry(
        layer="groenkaart_2018_2024", computed=date.today().isoformat(), n_units=res["units"],
        measures="доли высокой зелени (> 3 м), низкой зелени, сельского хозяйства и «не зелени» по секторам по "
                 "Groenkaart Vlaanderen 2018, 2021, 2024; сверка с вердиктами детектора — groenkaart_check_summary.json",
        unit="доля классифицированной площади",
        method="WCS ANB, 4 м (ближайший сосед от 1 м), центр пикселя в полигоне сектора; сверка: тот же подбор "
               "12 мест, порог — нулевое распределение этого же прогона",
        source="Groenkaart Vlaanderen 2018, 2021, 2024 (ANB / Digitaal Vlaanderen), Modellicentie gratis hergebruik",
        threshold=res["gk_thresholds"]["hg_d"],
        threshold_source=f"высокая зелень — {cal_line(res, 'hg_d')}; вся зелень — {cal_line(res, 'gr_d')}",
        limits=["только Фландрия: Антверпен и Гент; для Брюсселя и Валлонии двух сопоставимых выпусков нет",
                "лето 2018 было засушливым: выпуск 2018 может занижать низкую зелень",
                "согласие двух приборов, а не ошибка против истины: у аэрофотокарты свои ошибки"]))
    m.write()
    for p, d in res["pairs"].items():
        s, sp, ag = d["sensitivity"], d["specificity"], d["agreement_when_ours_changed"]
        print(f"{args.city} · {p}: n={d['n']}  чувствительность {s['k']}/{s['n']} {s['ci95']}  специфичность {sp['k']}/{sp['n']} "
              f"{sp['ci95']}  согласие «изменился» {ag['k']}/{ag['n']} {ag['ci95']}  противоположных {d['opposite']}  "
              f"Спирмен {d['spearman']}")
    print(f"пороги Groenkaart {res['gk_thresholds']} несмещены {res['gk_unbiased']}; секторов {res['units']}, отброшено {res['dropped']}")
    return 0


def cal_line(res: dict, k: str) -> str:
    return f"нулевое распределение по {res['units']} единицам, 95-й процентиль, порог {res['gk_thresholds'][k]}"


if __name__ == "__main__":
    raise SystemExit(main())
