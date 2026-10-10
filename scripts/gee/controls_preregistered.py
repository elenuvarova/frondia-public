"""Контроль для предрегистрированных следов — назван СЕЙЧАС, до работ.

Пул — секторы города записи ≥ 4 га, признаки состояния «до» те же, что в калибровке
(NDVI Sentinel-2 и LST Landsat, лето 2023–2025), подбор — `engine.controls.match`
с одной нормировкой на город, исключение 1,5 км, 12 контролей. Разрыв больше
0,04 — «контроль несопоставим», и это записывается заранее, а не после результата.

Только дописывает: контроль, названный в день записи, не переназывается позже.
Пул собирается только для городов, где есть записи без контроля, и без секторов, которые
пересекают след другой записи того же города: начнутся там работы — сдвинется и контроль.
(Правило с 27.09.2026. Раньше его не было: у Josaphat, 02.09, в контроле сектор CINQUANTENAIRE
(PARC), он покрывает 15 % следа реставрации Cinquantenaire; зафиксированный контроль не меняется.)

Запуск: python scripts/gee/controls_preregistered.py → data/registry/preregistered_controls.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import os

import ee
from shapely.geometry import shape
from engine.adapters import ADAPTERS
from engine.adapters.base import centroid_of
from engine.config import CITIES, CONTROL
from engine.controls import match
from engine.registries.preregistration import load
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "report"))
from article8_data import s2_ndvi, landsat_lst  # те же композиты, что в слое ст. 8

BASE = ("2023-01-01", "2025-12-31")
OUT = Path("data/registry/preregistered_controls.json")

def pool_for(city: str, stack, footprints):
    """Секторы города ≥ 4 га с NDVI и LST «до» — один прогон, одна нормировка на город.
    Секторы, задевающие чей-то зарегистрированный след, в пул не идут."""
    units = [u for u in ADAPTERS[city]().units() if not any(shape(u.geometry).intersects(f) for f in footprints)]
    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(u.geometry), {"id": u.id}) for u in units])
    print(f"{city}: секторный пул 2023–2025, NDVI + LST, один прогон…")
    rows = stack.reduceRegions(fc, ee.Reducer.mean(), 30).getInfo()["features"]
    by_id = {u.id: u for u in units}
    pool = []
    for r in rows:
        p = r["properties"]; u = by_id[p["id"]]
        if u.area_ha < CONTROL["min_area_ha"] or p.get("ndvi_b") is None or p.get("lst_b") is None: continue
        pool.append({"id": u.id, "name": u.name, "centroid": u.centroid, "ndvi_b": p["ndvi_b"], "lst_b": p["lst_b"], "ndvi_d": 0.0})
    ranges = (max(q["ndvi_b"] for q in pool) - min(q["ndvi_b"] for q in pool),
              max(q["lst_b"] for q in pool) - min(q["lst_b"] for q in pool))
    print(f"  пул: {len(pool)} секторов; размах NDVI {ranges[0]:.3f}, LST {ranges[1]:.2f} °C")
    return pool, ranges

def main():
    ee.Initialize(project=os.environ.get("EE_PROJECT", "my-project-maps-507221"))
    out = json.loads(OUT.read_text()) if OUT.exists() else []
    done = {c["id"] for c in out}
    todo = [r for r in load() if r.id not in done]
    for city in sorted({r.city for r in todo}):
        x0, y0, x1, y1 = CITIES[city]["bbox"]; box = ee.Geometry.Rectangle([x0, y0, x1, y1])
        stack = s2_ndvi(box, *BASE).rename("ndvi_b").addBands(landsat_lst(box, *BASE).rename("lst_b"))
        pool, ranges = pool_for(city, stack, [shape(r.geometry) for r in load() if r.city == city])
        for rec in (r for r in todo if r.city == city):
            g = ee.Geometry(rec.geometry)
            vals = stack.reduceRegion(ee.Reducer.mean(), g, scale=10, maxPixels=int(1e9), bestEffort=True).getInfo()
            nb, lb = vals.get("ndvi_b"), vals.get("lst_b")
            cs = match(nb, lb, centroid_of(rec.geometry), pool, "ndvi_b", "lst_b", "ndvi_d", ranges=ranges) if nb is not None and lb is not None else None
            comparable = cs is not None and abs(cs.gap) <= CONTROL["max_gap_ndvi"]
            out.append({"id": rec.id, "geometry_hash": rec.geometry_hash, "name": rec.name, "window": "2023–2025 лето",
                        "site_ndvi_b": nb, "site_lst_b": lb,
                        "gap": None if cs is None else cs.gap, "comparable": comparable,
                        "control_ids": [] if cs is None else [m["id"] for m in cs.members],
                        "control_names": [] if cs is None else [m["name"] for m in cs.members],
                        "control_ndvi_mean": None if cs is None else cs.baseline_mean})
            tag = "контроль назван" if comparable else "КОНТРОЛЬ НЕСОПОСТАВИМ — аудит без вердикта"
            print(f"{rec.name[:44]:44} NDVI {nb:.3f} LST {lb:5.1f}  разрыв {cs.gap if cs else float('nan'):+.4f}  {tag}")
            if cs: print("    " + ", ".join(m["name"] for m in cs.members[:6]) + " …")
    if not todo:
        print("новых записей без контроля нет")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"→ {OUT}")

if __name__ == "__main__":
    main()
