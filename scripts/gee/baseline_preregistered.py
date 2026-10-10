"""Базовое состояние предрегистрированных следов — снимается СЕЙЧАС, до работ.

Для каждой записи `data/registry/preregistered.json` по всем шести приборам
(NDVI Sentinel-2 + пять классов Dynamic World) считается летнее «до» за три
сезона 2023–2025. Результат привязан к id и хешу записи: будущий аудит берёт
«до» отсюда, а не восстанавливает его задним числом.

Только дописывает: у записи, чья база уже снята, база не пересчитывается — иначе «до», снятое в
день записи, заменилось бы снятым позже (Sentinel-2 перерабатывают, и значения сдвигаются).

Запуск: python scripts/gee/baseline_preregistered.py → data/registry/preregistered_baseline.csv
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import os

import ee
from engine.instruments.base import REGISTRY
import engine.instruments.vegetation  # noqa: F401 — регистрирует приборы
from engine.registries.preregistration import load

ee.Initialize(project=os.environ.get("EE_PROJECT", "my-project-maps-507221"))
BASE = ("2023-01-01", "2025-12-31")
OUT = Path("data/registry/preregistered_baseline.csv")
INSTR = ["ndvi", "built", "trees", "grass", "bare", "shrub"]

def main():
    rows = list(csv.DictReader(OUT.open())) if OUT.exists() else []
    done = {r["id"] for r in rows}
    for rec in load():
        if rec.id in done:
            continue
        geom = ee.Geometry(rec.geometry)
        area = geom.area(1).getInfo() / 1e4
        line = [f"{rec.name[:44]:44} {area:5.1f} га"]
        for name in INSTR:
            r = REGISTRY[name].measure(geom, *BASE)
            rows.append({"id": rec.id, "geometry_hash": rec.geometry_hash, "name": rec.name,
                         "area_ha": round(area, 2), "instrument": name, "window": f"{BASE[0][:4]}–{BASE[1][:4]} лето",
                         "value": None if r.value is None else round(r.value, 4), "scenes": r.n_scenes, "note": r.note or ""})
            line.append(f"{name} {r.value:.3f}" if r.value is not None else f"{name} —")
        print("  ".join(line))
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"→ {OUT} · {len(rows)} строк")

if __name__ == "__main__":
    main()
