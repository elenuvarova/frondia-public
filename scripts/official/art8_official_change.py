#!/usr/bin/env python3
"""Порог шума официального индикатора ст. 8: изменение кроны и зелени 2018 → 2021 на слоях Copernicus.

Зачем. Методичка EEA к ст. 8 (v2, 07.07.2026) считает индикатор суммой пикселей и ничего не говорит
о погрешности изменения; INBO (2026) пишет, что разница между методами бывает больше разницы между
годами. Вопрос: какое изменение официального слоя между двумя его выпусками отличимо от шума?
Ответ даёт та же калибровка, что у наших приборов: каждый сектор по очереди играет «вмешательство»
против 12 подобранных мест, разброс эффектов — шум метода, порог — где кончаются 95 %.

Что берём. Две эпохи каждого слоя с сервера EEA, сырыми байтами, без передискретизации:
  · крона — HRL Woody Vegetation Layer 2018 и 2021, 5 м (FAQ Комиссии разрешает WVL для черновиков);
  · зелень — CLCplus Backbone 2018 (снимки 07.2017–06.2019) и 2021 (10.2020–03.2022), 10 м,
    классы ст. 3(20), как в art8_official.py.
Tree Cover Density есть только за 2018 — второй эпохи на сервере нет, её не мерим.

Контроль. Тот же, что в калибровке атласа (`sector_change_2017_2024.csv`): подбор по NDVI и
температуре поверхности лета 2017–19 — ближе всего к эпохе 2018, — не ближе 1,5 км. Один контроль на
все приборы, поэтому эффект NDVI против тех же мест печатается рядом и приборы сравнимы между собой.
Порог считается этим же прогоном (`engine.calibrate.from_effects`), из чужой схемы не переносится.

Чего здесь нет. Изменения от базы 2024: слоёв 2024 года на сервере нет. Сопоставимость выпусков
2018 и 2021 производитель может не гарантировать — это и есть то, что проверяет порог.

    .venv/bin/python scripts/official/art8_official_change.py --city brussels

Пишет `cities/<city>/layers/art8_official_change_2018_2021.csv` и `…_summary.json` (во Фландрии — со сверкой
по Groenkaart и сектором-примером с наибольшим расхождением) и запись в манифест города.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/official"))
import art8_official as off  # noqa: E402
from engine.adapters import ADAPTERS  # noqa: E402
from engine.calibrate import from_effects  # noqa: E402
from engine.config import CONTROL  # noqa: E402
from engine.controls import match_all  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402

IMG = off.IMG
EPOCHS = {  # ключ → (ImageServer, шаг сетки)
    "wvl2018": (f"{IMG}/GioLandPublic/HRL_WoodyVegetationLayer_2018/ImageServer", 5),
    "wvl2021": (f"{IMG}/GioLandPublic/HRL_WoodyVegetationLayer_2021/ImageServer", 5),
    "clc2018": (f"{IMG}/CLC_plus/CLMS_CLCplus_RASTER_2018_010m_eu/ImageServer", 10),
    "clc2021": (f"{IMG}/CLC_plus/CLMS_CLCplus_RASTER_2021_010m_eu/ImageServer", 10),
}
off.RASTERS.update(EPOCHS)       # export_grid берёт адрес и шаг из этого словаря


def canopy(grid, rings):
    t, _, _ = grid.tally(rings, (0, 1))
    return off.share(t[1], t[0] + t[1])


def green(grid, rings):
    t, _, _ = grid.tally(rings, off.CLC_VALID)
    valid = sum(t.values())
    return off.share(sum(t[v] for v in off.GREEN), valid)


def histogram(grid, rings) -> dict[int, int]:
    """Какие значения вообще есть в слое внутри города — проверка кодировки эпох."""
    t, _, _ = grid.tally(rings, tuple(range(256)))
    return {v: c for v, c in t.items() if c}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="brussels", choices=list(off.LAUS))
    city = ap.parse_args().city

    base = {r["id"]: r for r in csv.DictReader((ROOT / f"cities/{city}/layers/sector_change_2017_2024.csv").open())}
    units = [u for u in ADAPTERS[city]().units() if u.id in base]
    rings = {u.id: off.rings_3035(u.geometry) for u in units}
    bbox = off.bbox_of(list(rings.values()))
    print(f"{city}: секторов в калибровке атласа {len(base)}, с геометрией {len(units)}, рамка {bbox}")

    grids = {k: off.export_grid(k, bbox, city) for k in EPOCHS}
    allr = [r for rs in rings.values() for r in rs]
    hist = {k: histogram(g, allr) for k, g in grids.items()}
    for k, h in hist.items():
        print(f"  {k}: значения в секторах {sorted(h)[:20]}")

    rows = []
    for u in units:
        b = base[u.id]
        r = {"id": u.id, "name": u.name or "", "area_ha": round(u.area_ha, 2),
             "centroid": (float(b["lon"]), float(b["lat"])),
             "ndvi_before": float(b["ndvi_before"]), "lst_before": float(b["lst_before"]),
             "ndvi_delta": float(b["d_ndvi_raw"]),
             "canopy_2018": canopy(grids["wvl2018"], rings[u.id]),
             "canopy_2021": canopy(grids["wvl2021"], rings[u.id]),
             "green_2018": green(grids["clc2018"], rings[u.id]),
             "green_2021": green(grids["clc2021"], rings[u.id])}
        for k in ("canopy", "green"):
            a, z = r[f"{k}_2018"], r[f"{k}_2021"]
            r[f"{k}_delta"] = None if a is None or z is None else z - a
        rows.append(r)

    scored = match_all(rows, "ndvi_before", "lst_before", ["ndvi_delta", "canopy_delta", "green_delta"])
    cal = {k: from_effects(k, [s[f"{k}_delta_eff"] for s in scored if s[f"{k}_delta_eff"] is not None])
           for k in ("ndvi", "canopy", "green")}

    def verdict(v, thr):
        return "нет данных" if v is None else ("прирост" if v > thr else "потеря" if v < -thr else "шум")

    out = []
    for s in scored:
        row = {k: s[k] for k in ("id", "name", "area_ha", "ndvi_before", "lst_before",
                                 "canopy_2018", "canopy_2021", "green_2018", "green_2021")}
        row.update({"gap": s["gap"], "comparable": s["comparable"]})
        for k in ("ndvi", "canopy", "green"):
            raw = s[f"{k}_delta"]
            eff = s[f"{k}_delta_eff"]
            row[f"{k}_raw"] = raw
            row[f"{k}_eff"] = eff
            row[f"{k}_verdict"] = verdict(eff, cal[k].threshold) if s["comparable"] else "несопоставимо"
        out.append(row)

    comp = [r for r in out if r["comparable"]]

    def tally(k):
        c = {}
        for r in comp:
            c[r[f"{k}_verdict"]] = c.get(r[f"{k}_verdict"], 0) + 1
        return c

    def raw_beyond(k):
        """Сколько секторов «изменились» по сырому выпуск-к-выпуску сверх порога — без вычитания мест."""
        thr = cal[k].threshold
        return sum(1 for r in comp if r[f"{k}_raw"] is not None and abs(r[f"{k}_raw"]) > thr)

    def agree(k):
        both = [r for r in comp if r[f"{k}_verdict"] != "нет данных" and r["ndvi_verdict"] != "нет данных"]
        changed = [r for r in both if r[f"{k}_verdict"] != "шум" or r["ndvi_verdict"] != "шум"]
        same = sum(1 for r in changed if r[f"{k}_verdict"] == r["ndvi_verdict"])
        noise_both = sum(1 for r in both if r[f"{k}_verdict"] == "шум" and r["ndvi_verdict"] == "шум")
        noise_any = sum(1 for r in both if r[f"{k}_verdict"] == "шум" or r["ndvi_verdict"] == "шум")
        return {"n": len(both), "changed_either": len(changed), "changed_same": same,
                "noise_both": noise_both, "noise_either": noise_any}

    def wmean(k, year):
        num = sum(r[f"{k}_{year}"] * r["area_ha"] for r in out if r[f"{k}_{year}"] is not None)
        den = sum(r["area_ha"] for r in out if r[f"{k}_{year}"] is not None)
        return num / den if den else None

    pair = [(r["canopy_eff"], r["ndvi_eff"]) for r in comp if r["canopy_eff"] is not None and r["ndvi_eff"] is not None]
    summary = {
        "city": city, "computed": date.today().isoformat(),
        "units": len(out), "comparable": len(comp), "max_gap": CONTROL["max_gap_ndvi"],
        "inputs": {k: v[0] for k, v in EPOCHS.items()},
        "values_present": {k: sorted(h) for k, h in hist.items()},
        "calibration": {k: {"threshold": round(c.threshold, 6), "mean": round(c.mean, 6), "sd": round(c.sd, 6),
                            "n": c.n, "unbiased": c.unbiased} for k, c in cal.items()},
        "city_mean": {"canopy_2018": wmean("canopy", 2018), "canopy_2021": wmean("canopy", 2021),
                      "green_2018": wmean("green", 2018), "green_2021": wmean("green", 2021)},
        "raw_median": {k: statistics.median([r[f"{k}_raw"] for r in comp if r[f"{k}_raw"] is not None])
                       for k in ("ndvi", "canopy", "green")},
        "raw_beyond_threshold": {k: raw_beyond(k) for k in ("ndvi", "canopy", "green")},
        "verdicts": {k: tally(k) for k in ("ndvi", "canopy", "green")},
        "agreement_with_ndvi": {k: agree(k) for k in ("canopy", "green")},
        "r_canopy_eff_vs_ndvi_eff": round(statistics.correlation(*zip(*pair)), 3) if len(pair) > 30 else None,
    }
    # Независимая карта, где она есть (Groenkaart Vlaanderen, аэрофото 1 м): высокая зелень тех же секторов в те же
    # годы. Секторы, классифицированные ≥ 90 % в обоих выпусках. Пример для текста — сектор, где официальная крона
    # прибавила больше всего сверх того, что прибавила крона по аэрофото (знаковая разность, не модуль: вопрос в том,
    # где официальный выпуск «вырастил» лес, которого нет на снимках). Число берётся отсюда, а не пишется руками.
    gk_path = ROOT / f"cities/{city}/layers/groenkaart_2018_2024.csv"
    both = []
    if gk_path.exists():
        gk = {r["id"]: r for r in csv.DictReader(gk_path.open())}
        both = [(r, gk[r["id"]]) for r in out
                if r["id"] in gk and r["canopy_2018"] is not None and r["canopy_2021"] is not None
                and all(float(gk[r["id"]][f"valid_{y}"]) >= 0.9 for y in (2018, 2021))]
        area = sum(r["area_ha"] for r, _ in both)
    if both:

        def gmean(f):
            return sum(f(r, g) * r["area_ha"] for r, g in both) / area
        top = max(both, key=lambda p: (p[0]["canopy_2021"] - p[0]["canopy_2018"])
                  - (float(p[1]["high_2021"]) - float(p[1]["high_2018"])))
        summary["independent"] = {
            "source": "Groenkaart Vlaanderen 2018 и 2021, высокая зелень (> 3 м), аэрофото 1 м",
            "units": len(both),
            "official_canopy_2018": gmean(lambda r, g: r["canopy_2018"]),
            "official_canopy_2021": gmean(lambda r, g: r["canopy_2021"]),
            "aerial_high_2018": gmean(lambda r, g: float(g["high_2018"])),
            "aerial_high_2021": gmean(lambda r, g: float(g["high_2021"])),
            "example": {"id": top[0]["id"], "name": top[0]["name"], "area_ha": top[0]["area_ha"],
                        "official_2018": top[0]["canopy_2018"], "official_2021": top[0]["canopy_2021"],
                        "aerial_2018": float(top[1]["high_2018"]), "aerial_2021": float(top[1]["high_2021"])},
        }

    layers = ROOT / f"cities/{city}/layers"
    with (layers / "art8_official_change_2018_2021.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        for r in out:
            w.writerow({k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()})
    def r6(o):   # json's default= never sees floats: round them on the way in
        return {k: r6(v) for k, v in o.items()} if isinstance(o, dict) else [r6(v) for v in o] if isinstance(o, list) \
            else round(o, 6) if isinstance(o, float) else o
    (layers / "art8_official_change_2018_2021_summary.json").write_text(json.dumps(r6(summary), ensure_ascii=False, indent=1))

    cm = summary["city_mean"]
    m = Manifest.read(city)
    m.add(LayerEntry(
        layer="art8_official_change_2018_2021", computed=date.today().isoformat(), n_units=len(out),
        measures="изменение официальных слоёв ст. 8 между выпусками 2018 и 2021 по сектору — кроны (HRL Woody "
                 "Vegetation) и зелени (CLCplus) — против 12 подобранных мест, с порогом шума этого прогона",
        unit="доля площади 0–1",
        method="разность разностей: изменение доли сектора минус среднее изменение 12 мест, подобранных по NDVI и "
               "температуре 2017–19 (контроль атласа), не ближе 1,5 км; порог — 95 % нулевого распределения этого же "
               "прогона; разрыв подбора > 0,04 — отказ",
        source="Copernicus HRL Woody Vegetation 2018 и 2021 (5 м), CLCplus Backbone 2018 и 2021 (10 м); сверка — "
               "Groenkaart Vlaanderen (во Фландрии)",
        threshold=round(cal["canopy"].threshold, 6),
        threshold_source=f"крона: {cal['canopy'].source_line}; зелень: порог {cal['green'].threshold:.4f}, "
                         f"{cal['green'].source_line}",
        limits=["WVL 2018 вырезает участки, похожие на лес (лесная маска 2018, PUM HRL SWF 2018), WVL 2021 — нет: "
                "разность выпусков кроны — смена определения, а не изменение кроны",
                f"по городу крона WVL {cm['canopy_2018'] * 100:.1f} → {cm['canopy_2021'] * 100:.1f} %",
                "слоёв 2024 на сервере EEA нет — изменение от базы закона этим слоем не измерить",
                "порог кроны велик, потому что он включает смену определения: это свойство пары выпусков, не города"]))
    m.write()

    print(f"\nсекторов {len(out)}, сопоставимых {len(comp)}")
    for k, c in cal.items():
        print(f"  {c.describe()}")
    print(f"  город, доля по площади: {summary['city_mean']}")
    print(f"  сырая медиана изменения: {summary['raw_median']}")
    print(f"  сырое изменение сверх порога (без мест): {summary['raw_beyond_threshold']}")
    print(f"  вердикты против мест: {summary['verdicts']}")
    print(f"  согласие с NDVI: {summary['agreement_with_ndvi']}, r(крона, NDVI) = {summary['r_canopy_eff_vs_ndvi_eff']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
