#!/usr/bin/env python3
"""Карта растительности Bruxelles Environnement 2021 → 2023: сколько в её изменении шума.

Зачем. Bruxelles Environnement объявил падение растительного покрова региона (~55 % в 2016 → 48,7 % в 2023)
и назвал главной причиной урбанизацию, смену картирования — второстепенной (bx1, 24.06.2026). Ряд Sentinel-2
с одним методом падения на ~6 пунктов не показывает (`scripts/gee/vegetation_series.py`). Здесь — их же
карта, один производитель, две эпохи, через нашу калибровку: какое изменение сектора отличимо от шума?

Данные. Набор GeoBru «Couverture végétale» (CC BY 4.0), архив app.bruxellesenvironnement.be/carto/vegetation.zip:
`veget_21.tif` и `veget_23.tif`, 2 м, Lambert 72 (EPSG:31370), начало x 140000, y 179000, LZW.
Кодировка разная — это уже признак смены продукта:
  · 2021: 0 и 1 — растительность двух видов (из пикселей 0 в 2023 растительностью остаются 86 %, из 1 — 96 %),
    255 — не растительность и вне региона;
  · 2023: 1 — растительность, 0 — нет.
Проверка привязки: по карте 2023 доля растительности региона — 48,7 %, ровно объявленная цифра.

Метод. Доля растительности каждого сектора в обе эпохи (центры пикселей в полигоне сектора, EPSG:31370 —
`data/brussels_sectors_31370.geojson`, переведён pyproj из WGS84, сверка на Антверпене ≤ 8 см). Контроль —
тот же, что в атласе (12 мест по NDVI и температуре 2017–19, не ближе 1,5 км), порог — этот же прогон.

    .venv/bin/python scripts/official/brussels_vegetation_check.py --zip <путь к vegetation.zip>

Пишет `cities/brussels/layers/be_vegetation_2021_2023.csv` и `…_summary.json` и запись в манифест Брюсселя.
Нужны numpy, shapely, tifffile, imagecodecs.
"""
from __future__ import annotations

import argparse
import hashlib
import csv
import io
import json
import statistics
import sys
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
import shapely
import tifffile
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.calibrate import from_effects  # noqa: E402
from engine.controls import match_all  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402

X0, Y1, RES = 140000, 179000, 2
URL = "https://app.bruxellesenvironnement.be/carto/vegetation.zip"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True, help=f"скачанный {URL}")
    path = ap.parse_args().zip
    # the archive is replaced in place when GeoBru republishes: its hash and size say which one these numbers come from
    blob = Path(path).read_bytes()
    archive = {"url": URL, "sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob), "read": date.today().isoformat()}
    z = zipfile.ZipFile(io.BytesIO(blob))
    a21 = tifffile.imread(io.BytesIO(z.read("veget_21.tif")))
    a23 = tifffile.imread(io.BytesIO(z.read("veget_23.tif")))
    veg21, veg23 = (a21 == 0) | (a21 == 1), a23 == 1
    H, W = a21.shape

    geoms = {f["properties"]["id"]: shape(f["geometry"])
             for f in json.loads((ROOT / "data/brussels_sectors_31370.geojson").read_text())["features"]}
    base = {r["id"]: r for r in csv.DictReader((ROOT / "cities/brussels/layers/sector_change_2017_2024.csv").open())}

    rows, n_all, v21_all, v23_all = [], 0, 0, 0
    for sid, g in geoms.items():
        gx0, gy0, gx1, gy1 = g.bounds
        c0, c1 = max(0, int((gx0 - X0) // RES)), min(W, int(-(-(gx1 - X0) // RES)))
        r0, r1 = max(0, int((Y1 - gy1) // RES)), min(H, int(-(-(Y1 - gy0) // RES)))
        gx, gy = np.meshgrid(X0 + (np.arange(c0, c1) + 0.5) * RES, Y1 - (np.arange(r0, r1) + 0.5) * RES)
        inside = shapely.contains_xy(g, gx, gy)
        n = int(inside.sum())
        v21 = int(veg21[r0:r1, c0:c1][inside].sum())
        v23 = int(veg23[r0:r1, c0:c1][inside].sum())
        n_all, v21_all, v23_all = n_all + n, v21_all + v21, v23_all + v23
        if sid not in base or not n:
            continue
        b = base[sid]
        rows.append({"id": sid, "name": b["name"], "area_ha": float(b["area_ha"]),
                     "centroid": (float(b["lon"]), float(b["lat"])),
                     "ndvi_before": float(b["ndvi_before"]), "lst_before": float(b["lst_before"]),
                     "veg_2021": v21 / n, "veg_2023": v23 / n, "veg_delta": (v23 - v21) / n})

    scored = match_all(rows, "ndvi_before", "lst_before", ["veg_delta"])
    cal = from_effects("be_veg", [s["veg_delta_eff"] for s in scored if s["veg_delta_eff"] is not None])
    thr = cal.threshold
    comp = [s for s in scored if s["comparable"]]

    def verdict(e):
        return "прирост" if e > thr else "потеря" if e < -thr else "шум"

    for s in scored:
        s["verdict"] = verdict(s["veg_delta_eff"]) if s["comparable"] else "несопоставимо"
    counts = {k: sum(1 for s in comp if s["verdict"] == k) for k in ("потеря", "шум", "прирост")}
    raw_beyond = sum(1 for s in comp if abs(s["veg_delta"]) > thr)
    # losses and gains beyond noise, apart: a sum would let 18 gains hide 10 losses
    loss_ha = sum(s["veg_delta_eff"] * s["area_ha"] for s in comp if s["verdict"] == "потеря")
    gain_ha = sum(s["veg_delta_eff"] * s["area_ha"] for s in comp if s["verdict"] == "прирост")
    raw_ha = sum(s["veg_delta"] * s["area_ha"] for s in comp)

    summary = {
        "computed": date.today().isoformat(), "source": URL,
        "region_share_2021": round(v21_all / n_all, 6), "region_share_2023": round(v23_all / n_all, 6),
        "units": len(scored), "comparable": len(comp),
        "calibration": {"threshold": round(thr, 6), "mean": round(cal.mean, 6), "sd": round(cal.sd, 6),
                        "unbiased": cal.unbiased, "n": cal.n},
        "raw_median_delta": round(statistics.median(s["veg_delta"] for s in comp), 4),
        "raw_beyond_threshold": raw_beyond, "verdicts": counts,
        "raw_change_ha_comparable": round(raw_ha, 1), "loss_beyond_noise_ha": round(loss_ha, 1),
        "gain_beyond_noise_ha": round(gain_ha, 1), "archive": archive,
    }
    # the strongest loss beyond noise, chosen by the numbers (the site's example; checked by hand on aerial photos)
    ex = min((s for s in comp if s["verdict"] == "потеря"), key=lambda s: s["veg_delta_eff"], default=None)
    if ex:
        summary["example"] = {"id": ex["id"], "name": ex["name"], "area_ha": ex["area_ha"],
                              "veg_2021": round(ex["veg_2021"], 4), "veg_2023": round(ex["veg_2023"], 4),
                              "effect": round(ex["veg_delta_eff"], 4)}
    out = ROOT / "cities/brussels/layers/be_vegetation_2021_2023.csv"
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "name", "area_ha", "veg_2021", "veg_2023", "veg_raw", "veg_eff", "gap", "verdict"])
        for s in scored:
            w.writerow([s["id"], s["name"], s["area_ha"], round(s["veg_2021"], 6), round(s["veg_2023"], 6),
                        round(s["veg_delta"], 6), "" if s["veg_delta_eff"] is None else round(s["veg_delta_eff"], 6),
                        "" if s["gap"] is None else round(s["gap"], 6), s["verdict"]])
    (out.with_name("be_vegetation_2021_2023_summary.json")).write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    m = Manifest.read("brussels")
    m.add(LayerEntry(
        layer="be_vegetation_2021_2023", computed=summary["computed"], n_units=len(scored),
        measures="изменение доли растительности сектора по карте Bruxelles Environnement 2021 → 2023 против 12 "
                 "подобранных мест, с порогом шума этого прогона",
        unit="доля площади 0–1",
        method="доля пикселей 2 м с растительностью в секторе (EPSG:31370), разность разностей против контроля атласа "
               "(NDVI и температура 2017–19, не ближе 1,5 км); порог — 95 % нулевого распределения; разрыв > 0,04 — отказ",
        source="Bruxelles Environnement, «Couverture végétale» 2021 и 2023 (GeoBru, CC BY 4.0)",
        threshold=summary["calibration"]["threshold"],
        threshold_source=f"нулевое распределение по {cal.n} секторам, 95-й процентиль, среднее {cal.mean:+.5f}",
        limits=["кодировка выпусков разная: 2021 — два класса растительности и 255 «нет», 2023 — двоичная",
                f"по региону {summary['region_share_2021'] * 100:.1f} → {summary['region_share_2023'] * 100:.1f} %; "
                "разность разностей вычитает общегородской сдвиг и сама не доказывает, что он ненастоящий",
                "цифра «~55 % в 2016» — из более ранней карты, её здесь нет",
                f"архив GeoBru sha256 {archive['sha256'][:16]}…, {archive['bytes']} байт (дата чтения — в сводке)"]))
    m.write()
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
