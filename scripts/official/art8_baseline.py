#!/usr/bin/env python3
"""
Нулевой замер по статье 8 в форме, в которой его сдают дальше (фаза 2c, пункт 4).

Числа не пересчитываются: их уже посчитал `art8_official.py` — повтор скрипта EEA/JRC NRR_Art8 на
открытых данных (LAU 2024, сетка центров и кластеров 2021, CLCplus 2021, WVL 2021). Этот скрипт только
упаковывает их тремя способами, которые просят покупатели:

1. **Таблица коммун в гектарах и процентах** (`art8_baseline_2021.csv`) — форма голландской
   «Definitieve nulmeting groen» PBL (25.08.2026): одна строка на коммуну, площадь городской
   экосистемы, зелень и крона в га и в %, вердикт исключения. Оба варианта границ, которые
   Комиссия оставляет стране: только центры и кластеры внутри LAU («ucuc») и вся LAU («lau»).
   Для города из нескольких коммун — строка «все вместе».
2. **Таблица чувствительности** (`art8_sensitivity_2021.csv`) — вердикт 45/10 при каждом прочтении,
   которое уже проверял `art8_official.py`: официальное, пашня как зелень, без воды, коммуна из
   секторов Statbel вместо границ 1:1M. PBL пишет, что результат «сильно зависит от метода», — здесь
   это видно строкой на прочтение.
3. **`t8_UEAPolygons`** — файл, который страна загружает в Reportnet 3, по схеме образца EEA/JRC
   (github.com/eea/NRR_Art8, коммит от 22.09.2026, прочитан 26.09.2026): GeoPackage, EPSG:3035,
   MULTIPOLYGON, поля fid, uea_id, lau_id («lau2024.BE.21001»), area_tcc (км² кроны, текстом, 5 знаков),
   area_ugs (км² зелени). Геометрия — полигон LAU из GISCO, fid унаследован от GISCO, как в образце.
   Два файла, `_ucuc` и `_lau`, — по варианту границ.

Чего здесь нет и не будет: погрешности, сравнения лет и порога — их нет и в формате Комиссии.
«Изменилось ли сверх шума» — отдельный слой со своим манифестом (article8_2024), официальную цифру он
не подменяет. `area_ugs` в образце Комиссии пусто; мы заполняем его своим прочтением ст. 3(20) по
классам CLCplus и пишем это в манифесте. WVL 2021 разрешён только для черновиков планов.

Запуск (без сети, если кеш art8_official.py на месте; иначе скачает LAU GISCO):
    .venv/bin/python scripts/official/art8_baseline.py --city brussels
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/official"))
from art8_official import CACHE, CANOPY_MIN, GREEN_MIN, LAU_GPKG, LAUS, fetch  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402

SRS = 3035
TABLE = "t8_UEAPolygons"
# прочтения, которые проверял art8_official.py: ключ доли зелени, ключ доли кроны, подпись
READINGS = [
    ("official", "green_ucuc", "canopy_wvl_ucuc", "официальное: CLCplus 2021, классы ст. 3(20), границы LAU 1:1M"),
    ("with_arable", "green_with7_ucuc", "canopy_wvl_ucuc", "пашня (класс 7) засчитана зеленью"),
    ("without_water", "green_no_water_ucuc", "canopy_wvl_ucuc", "вода не засчитана зеленью"),
    ("statbel_sectors", "green_ucuc_statbel", "canopy_wvl_ucuc_statbel", "коммуна из секторов Statbel вместо границ 1:1M"),
]


def lau_code(gid: str) -> str:
    """BE_21001 → lau2024.BE.21001, как в образце Комиссии (paste('lau2024', страна, код))."""
    c, n = gid.split("_", 1)
    return f"lau2024.{c}.{n}"


def exempt(g, c) -> bool | None:
    if g is None or c is None:
        return None
    return g > GREEN_MIN and c > CANOPY_MIN


def pct(v) -> float | None:
    """Четыре знака: округлять дважды нельзя — 60,848 % до сотых даёт 60,85 и потом 60,9 вместо 60,8."""
    return None if v is None else round(100 * v, 4)


def ha(share, area_km2) -> float | None:
    return None if share is None or area_km2 is None else round(100 * share * area_km2, 2)


def gisco_geoms(ids: list[str]) -> dict[str, tuple[int, bytes]]:
    """fid и геометрия LAU как есть: блоб GeoPackage GISCO уже MULTIPOLYGON в EPSG:3035."""
    path = fetch(LAU_GPKG, CACHE / "LAU_RG_01M_2024_3035.gpkg")
    con = sqlite3.connect(path)
    tbl = con.execute("select table_name from gpkg_contents where data_type='features'").fetchone()[0]
    gcol, gtype, srs = con.execute("select column_name, geometry_type_name, srs_id from gpkg_geometry_columns "
                                   "where table_name=?", (tbl,)).fetchone()
    if (gtype, srs) != ("MULTIPOLYGON", SRS):
        raise SystemExit(f"GISCO LAU: ждали MULTIPOLYGON в {SRS}, получили {gtype} в {srs}")
    q = f'select GISCO_ID, fid, "{gcol}" from "{tbl}" where GISCO_ID in ({",".join("?" * len(ids))})'
    out = {gid: (fid, blob) for gid, fid, blob in con.execute(q, ids)}
    srs_rows = con.execute("select srs_name, srs_id, organization, organization_coordsys_id, definition, description "
                           "from gpkg_spatial_ref_sys").fetchall()
    con.close()
    missing = set(ids) - set(out)
    if missing:
        raise SystemExit(f"LAU нет в GISCO 2024: {sorted(missing)}")
    for gid, (_, blob) in out.items():
        if blob[:2] != b"GP" or int.from_bytes(blob[4:8], "little" if blob[3] & 1 else "big") != SRS:
            raise SystemExit(f"{gid}: геометрия не GeoPackage в EPSG:{SRS}")
    return out, srs_rows


def envelope(blob: bytes) -> tuple[float, float, float, float]:
    """minx, maxx, miny, maxy из заголовка (тип конверта 1 и больше)."""
    import struct
    if (blob[3] >> 1) & 0b111 == 0:
        raise SystemExit("у геометрии нет конверта в заголовке")
    return struct.unpack(("<" if blob[3] & 1 else ">") + "4d", blob[8:40])


def write_gpkg(path: Path, rows: list[dict], srs_rows: list[tuple]) -> None:
    """GeoPackage 1.2 по спецификации OGC: служебные таблицы и одна таблица признаков, схема — как в
    образце EEA/JRC (без R-дерева: оно необязательно и требует функций SpatiaLite в триггерах)."""
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript(f"""
        PRAGMA application_id = 1196444487;
        PRAGMA user_version = 10200;
        CREATE TABLE gpkg_spatial_ref_sys (srs_name TEXT NOT NULL, srs_id INTEGER NOT NULL PRIMARY KEY,
            organization TEXT NOT NULL, organization_coordsys_id INTEGER NOT NULL, definition TEXT NOT NULL,
            description TEXT);
        CREATE TABLE gpkg_contents (table_name TEXT NOT NULL PRIMARY KEY, data_type TEXT NOT NULL,
            identifier TEXT UNIQUE, description TEXT DEFAULT '',
            last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE, srs_id INTEGER,
            CONSTRAINT fk_gc_r_srs_id FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id));
        CREATE TABLE gpkg_geometry_columns (table_name TEXT NOT NULL, column_name TEXT NOT NULL,
            geometry_type_name TEXT NOT NULL, srs_id INTEGER NOT NULL, z TINYINT NOT NULL, m TINYINT NOT NULL,
            CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name),
            CONSTRAINT uk_gc_table_name UNIQUE (table_name),
            CONSTRAINT fk_gc_tn FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name),
            CONSTRAINT fk_gc_srs FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys (srs_id));
        CREATE TABLE "{TABLE}" ("fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "geom" MULTIPOLYGON,
            "uea_id" TEXT, "lau_id" TEXT, "area_tcc" TEXT, "area_ugs" REAL);
    """)
    con.executemany("insert into gpkg_spatial_ref_sys values (?,?,?,?,?,?)", srs_rows)
    envs = [envelope(r["geom"]) for r in rows]
    bbox = (min(e[0] for e in envs), min(e[2] for e in envs), max(e[1] for e in envs), max(e[3] for e in envs))
    con.execute("insert into gpkg_contents (table_name, data_type, identifier, description, min_x, min_y, max_x, max_y, srs_id) "
                "values (?,?,?,?,?,?,?,?,?)", (TABLE, "features", TABLE,
                                             "Article 8 NRR urban ecosystem areas (Frondia, draft on 2021 data)", *bbox, SRS))
    con.execute("insert into gpkg_geometry_columns values (?,?,?,?,?,?)", (TABLE, "geom", "MULTIPOLYGON", SRS, 0, 0))
    con.executemany(f'insert into "{TABLE}" (fid, geom, uea_id, lau_id, area_tcc, area_ugs) values (?,?,?,?,?,?)',
                    [(r["fid"], r["geom"], None, r["lau_id"], r["area_tcc"], r["area_ugs"]) for r in rows])
    con.commit()
    con.close()


def km2_text(v: float) -> str:
    """Как round(x, 5) в R, записанное текстом: без хвостовых нулей."""
    s = f"{round(v, 5):.5f}".rstrip("0").rstrip(".")
    return s or "0"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", required=True, choices=list(LAUS))
    city = ap.parse_args().city
    layers = ROOT / f"cities/{city}/layers"
    S = json.loads((layers / "art8_official_2021_summary.json").read_text())
    laus = S["laus"]
    geoms, srs_rows = gisco_geoms([r["lau_id"] for r in laus])

    base = []
    for r in laus:
        base.append({
            "lau_id": lau_code(r["lau_id"]), "name": r["name"], "population": r["population"],
            "uea_ucuc_ha": round(100 * r["area_km2_ucuc"], 2),
            "green_ucuc_ha": ha(r["green_ucuc"], r["area_km2_ucuc"]), "green_ucuc_pct": pct(r["green_ucuc"]),
            "canopy_ucuc_ha": ha(r["canopy_wvl_ucuc"], r["area_km2_ucuc"]), "canopy_ucuc_pct": pct(r["canopy_wvl_ucuc"]),
            "uea_lau_ha": round(100 * r["area_km2_all"], 2),
            "green_lau_ha": ha(r["green_all"], r["area_km2_all"]), "green_lau_pct": pct(r["green_all"]),
            "canopy_lau_ha": ha(r["canopy_wvl_all"], r["area_km2_all"]), "canopy_lau_pct": pct(r["canopy_wvl_all"]),
            "exempt": r["exempt"], "stable": r["stable"],
        })
    if len(laus) > 1:
        p = S["region"]["parts"]
        base.append({
            "lau_id": "", "name": f"all {len(laus)} together", "population": sum(r["population"] or 0 for r in laus),
            "uea_ucuc_ha": round(100 * p["ucuc"]["area_km2"], 2),
            "green_ucuc_ha": ha(p["ucuc"]["green"], p["ucuc"]["area_km2"]), "green_ucuc_pct": pct(p["ucuc"]["green"]),
            "canopy_ucuc_ha": ha(p["ucuc"]["canopy_wvl"], p["ucuc"]["area_km2"]), "canopy_ucuc_pct": pct(p["ucuc"]["canopy_wvl"]),
            "uea_lau_ha": round(100 * p["all"]["area_km2"], 2),
            "green_lau_ha": ha(p["all"]["green"], p["all"]["area_km2"]), "green_lau_pct": pct(p["all"]["green"]),
            "canopy_lau_ha": ha(p["all"]["canopy_wvl"], p["all"]["area_km2"]), "canopy_lau_pct": pct(p["all"]["canopy_wvl"]),
            "exempt": S["region"]["exempt"], "stable": "",
        })

    sens = []
    for r in laus:
        for key, gk, ck, _ in READINGS:
            g, c = r.get(gk), r.get(ck)
            sens.append({"lau_id": lau_code(r["lau_id"]), "name": r["name"], "reading": key,
                         "green_pct": pct(g), "canopy_pct": pct(c), "exempt": exempt(g, c)})

    for path, rows in ((layers / "art8_baseline_2021.csv", base), (layers / "art8_sensitivity_2021.csv", sens)):
        with path.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows([{k: ("" if v is None else v) for k, v in x.items()} for x in rows])

    for uea, part in (("ucuc", "ucuc"), ("lau", "all")):
        feats = [{"fid": geoms[r["lau_id"]][0], "geom": geoms[r["lau_id"]][1], "lau_id": lau_code(r["lau_id"]),
                  "area_tcc": km2_text(r[f"canopy_wvl_{part}"] * r[f"area_km2_{part}"]),
                  "area_ugs": round(r[f"green_{part}"] * r[f"area_km2_{part}"], 5)} for r in laus]
        write_gpkg(layers / f"t8_UEAPolygons_{uea}.gpkg", feats, srs_rows)

    m = Manifest.read(city)
    today = date.today().isoformat()
    src = ("числа — art8_official_lau_2021 (повтор NRR_Art8 EEA/JRC: LAU 2024 GISCO 1:1M, центры и кластеры 2021, "
           "CLCplus Backbone 2021, HRL WVL 2021); форма — PBL «Definitieve nulmeting groen» (25.08.2026) и образец "
           "t8_UEAPolygons EEA/JRC (22.09.2026)")
    no_thr = "уровень одного года, не изменение: порога значимости нет по смыслу — как и в формате Комиссии"
    m.add(LayerEntry(
        layer="art8_baseline_2021", computed=today, n_units=len(base),
        measures="нулевой замер по коммунам: площадь городской экосистемы, зелень и крона в га и в %, вердикт 45/10; "
                 "границы — центры и кластеры внутри LAU и вся LAU; чувствительность вердикта — art8_sensitivity_2021",
        unit="га; %", method="доли art8_official × площадь зоны", source=src, threshold_source=no_thr,
        limits=["данные 2021 года: WVL 2021 Комиссия разрешила только для черновиков планов",
                "соответствие классов CLCplus ст. 3(20) — наше прочтение; поэтому таблица чувствительности",
                "гектары — площадь пикселей внутри полигона 1:1M, не кадастр"]))
    m.add(LayerEntry(
        layer="art8_sensitivity_2021", computed=today, n_units=len(sens),
        measures="вердикт исключения ст. 8(1) при каждом прочтении: официальное, пашня как зелень, без воды, "
                 "коммуна из секторов Statbel",
        unit="%; да/нет", method="пороги ст. 8(1) к долям art8_official", source=src, threshold_source=no_thr,
        limits=["прочтения — те, что проверяет art8_official.py; другие допустимые границы UEA не перебирались"]))
    m.add(LayerEntry(
        layer="t8_UEAPolygons", computed=today, n_units=len(laus),
        measures="файл для Reportnet 3 по схеме образца EEA/JRC: полигон LAU, lau_id, area_tcc (км² кроны WVL), "
                 "area_ugs (км² зелени CLCplus); два файла — границы «ucuc» и «lau»",
        unit="км²", method="площадь = доля art8_official × площадь зоны, 5 знаков, как round() в скрипте",
        source=src, threshold_source=no_thr,
        limits=["черновик на данных 2021 года (WVL 2021 — только для черновиков)",
                "area_ugs в образце Комиссии пусто; здесь — наше прочтение ст. 3(20) по классам CLCplus",
                "uea_id пусто, как в образце: идентификатор UEA назначает страна",
                "без R-дерева пространственного индекса (необязательно по спецификации GeoPackage)"]))
    m.write()

    ex = sum(1 for r in laus if r["exempt"])
    print(f"{city}: {len(laus)} LAU, освобождены {ex}; → art8_baseline_2021.csv ({len(base)} строк), "
          f"art8_sensitivity_2021.csv ({len(sens)}), t8_UEAPolygons_ucuc.gpkg, t8_UEAPolygons_lau.gpkg")
    for r in base:
        print(f"  {r['lau_id'] or '—':<20} {r['name'][:28]:<28} UEA {r['uea_ucuc_ha']:>8} га  зелень {r['green_ucuc_pct']}%  "
              f"крона {r['canopy_ucuc_pct']}%  {'освобождена' if r['exempt'] else 'считается'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
