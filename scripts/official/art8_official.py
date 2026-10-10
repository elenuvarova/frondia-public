#!/usr/bin/env python3
"""Статья 8 по методике Комиссии: зелень и крона на официальных слоях Copernicus, исключение 45/10 по коммунам.

Зачем. FAQ Комиссии (портал NRR, раздел Urban ecosystems) назвал наборы данных для
ст. 8, а EEA и JRC выложили скрипт расчёта кроны (github.com/eea/NRR_Art8). Здесь
тот же расчёт повторён на открытых данных, чтобы закрыть вопрос, открытый с
1 сентября: подпадает ли Брюссель под исключение ст. 8(1).

Правило исключения. Городскую экосистему можно не включать в национальный итог,
если в её городских центрах и кластерах зелень больше 45 % И крона больше 10 %.
Сетка центров и кластеров 1 км² для исключения обязательна (FAQ). Единица — LAU,
в Бельгии это коммуна; объединять соседние LAU страна вправе, поэтому для Брюсселя
печатается и регион целиком.

Входы, все открытые:
  · LAU 2024, 1:1M, EPSG:3035 — GISCO (та же публичная версия, что в скрипте EEA);
  · DEGURBA 2024 — таблица Евростата EU-27-LAU-2024-NUTS-2024.xlsx;
  · городские центры и кластеры 2021, 1 км — Евростат (HDENS_CLST_2021, URBAN_CLST_2021);
  · зелень — CLCplus Backbone 2021, 10 м (регламент называет 2023; 2021 — последний
    год на открытом сервере EEA);
  · крона — HRL Woody Vegetation Layer 2021, 5 м (FAQ: разрешён для черновиков планов);
  · сверка — HRL Tree Cover Density 2018, 10 м (Bruxelles Environnement публикует
    по Copernicus 2018 года крону 37 % для региона).

Зелень по ст. 3(20) — деревья, кусты, постоянные травы, лишайники и мхи, водоёмы:
классы CLCplus 2, 3, 4, 5, 6, 8, 10. Не зелень: запечатанное (1), периодические
травы, то есть пашня (7), голое (9). Соответствие классов — наше прочтение
определения: пояснительные записки Комиссии к городской части плана закрыты логином.

Без numpy и GDAL: растры приходят с ImageServer EEA сырыми байтами (bsq) строго по
сетке EPSG:3035, полигоны растеризуются построчно по центрам пикселей, пиксели
считаются bytes.count. Сырые загрузки кешируются в OUT/official-cache.

    .venv/bin/python scripts/official/art8_official.py --city brussels
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sqlite3
import statistics
import struct
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.config import CITIES  # noqa: E402
from engine.manifest import LayerEntry, Manifest  # noqa: E402
from scripts.report.paths import OUT  # noqa: E402

CACHE = OUT / "official-cache"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")

IMG = "https://image.discomap.eea.europa.eu/arcgis/rest/services"
RASTERS = {  # ключ → (ImageServer, шаг сетки в метрах)
    "clcplus": (f"{IMG}/CLC_plus/CLMS_CLCplus_RASTER_2021_010m_eu/ImageServer", 10),
    "wvl": (f"{IMG}/GioLandPublic/HRL_WoodyVegetationLayer_2021/ImageServer", 5),
    "tcd": (f"{IMG}/GioLandPublic/HRL_TreeCoverDensity_2018/ImageServer", 10),
}
LAU_GPKG = "https://gisco-services.ec.europa.eu/distribution/v2/lau/gpkg/LAU_RG_01M_2024_3035.gpkg"
DEGURBA_XLSX = ("https://ec.europa.eu/eurostat/documents/345175/501971/EU-27-LAU-2024-NUTS-2024.xlsx/"
                "12971f56-c035-dbab-4d9f-ff1dcc617bb3?t=1737036272863")
CLUSTERS = {  # ключ → (архив Евростата, растр внутри)
    "hdens": ("https://ec.europa.eu/eurostat/documents/7116161/15125332/HDENS-CLST-2021.zip/"
              "64d30f03-acf2-c8f5-a530-02bbe62c0c43?t=1731944882446", "HDENS_CLST_2021"),
    "urban": ("https://ec.europa.eu/eurostat/documents/7116161/15125332/URBAN-CLST-2021.zip/"
              "649f23cf-1dcd-c089-9dd0-be4ac372af2f?t=1731944884719", "URBAN_CLST_2021"),
}

# LAU городов пакета. В Бельгии LAU = коммуна, код = REFNIS.
LAUS = {
    "brussels": [f"BE_210{i:02d}" for i in range(1, 20)],
    "antwerp": ["BE_11002"],
    "ghent": ["BE_44021"],
    "liege": ["BE_62063"],
    "charleroi": ["BE_52011"],
}

GREEN = (2, 3, 4, 5, 6, 8, 10)          # ст. 3(20) в классах CLCplus Backbone
CLC_VALID = tuple(range(1, 12))          # 0 — вне покрытия
GREEN_MIN, CANOPY_MIN = 0.45, 0.10       # ст. 8(1): строго больше
BXL_TCD_2018_PUBLISHED = 0.37            # Bruxelles Environnement, страница от 17.02.2026


# ── проекция: ETRS89 долгота/широта → EPSG:3035 (LAEA Europe), Snyder 1987 ──────────
_A = 6378137.0
_F = 1 / 298.257222101
_E2 = 2 * _F - _F * _F
_E = math.sqrt(_E2)
_LAT0, _LON0, _FE, _FN = math.radians(52.0), math.radians(10.0), 4321000.0, 3210000.0


def _q(phi: float) -> float:
    s = math.sin(phi)
    return (1 - _E2) * (s / (1 - _E2 * s * s) - (1 / (2 * _E)) * math.log((1 - _E * s) / (1 + _E * s)))


_QP = _q(math.pi / 2)
_RQ = _A * math.sqrt(_QP / 2)
_B0 = math.asin(_q(_LAT0) / _QP)
_D = _A * math.cos(_LAT0) / (math.sqrt(1 - _E2 * math.sin(_LAT0) ** 2) * _RQ * math.cos(_B0))


def laea(lon: float, lat: float) -> tuple[float, float]:
    """ETRS89 (≈ WGS84 до метра) → EPSG:3035. Проверено на примере EPSG (тест)."""
    beta = math.asin(_q(math.radians(lat)) / _QP)
    dl = math.radians(lon) - _LON0
    b = _RQ * math.sqrt(2 / (1 + math.sin(_B0) * math.sin(beta) + math.cos(_B0) * math.cos(beta) * math.cos(dl)))
    x = _FE + b * _D * math.cos(beta) * math.sin(dl)
    y = _FN + (b / _D) * (math.cos(_B0) * math.sin(beta) - math.sin(_B0) * math.cos(beta) * math.cos(dl))
    return x, y


def rings_3035(geometry: dict) -> list[list[tuple[float, float]]]:
    polys = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    return [[laea(p[0], p[1]) for p in ring] for poly in polys for ring in poly]


# ── растеризация: построчно по центрам пикселей, правило чёт-нечет ────────────────
def spans(rings, x0: float, ytop: float, res: float, W: int, H: int):
    """Отрезки (строка, столбец_от, столбец_до) пикселей, центры которых внутри полигона.

    Пиксель (i, j) имеет центр (x0 + (j+0.5)·res, ytop − (i+0.5)·res). Ребро
    пересекает строку, если ya ≤ yc < yb — полуоткрытый интервал не даёт двойного
    счёта в вершинах. Работа пропорциональна периметру, а не площади.
    """
    rows: dict[int, list[float]] = {}
    for ring in rings:
        n = len(ring)
        for k in range(n):
            xa, ya = ring[k]
            xb, yb = ring[(k + 1) % n]
            if ya == yb:
                continue
            if ya > yb:
                xa, ya, xb, yb = xb, yb, xa, ya
            i_lo = max(0, math.floor((ytop - yb) / res - 0.5) + 1)
            i_hi = min(H - 1, math.floor((ytop - ya) / res - 0.5))
            if i_lo > i_hi:
                continue
            slope = (xb - xa) / (yb - ya)
            for i in range(i_lo, i_hi + 1):
                yc = ytop - (i + 0.5) * res
                rows.setdefault(i, []).append(xa + (yc - ya) * slope)
    for i in sorted(rows):
        xs = sorted(rows[i])
        for a, b in zip(xs[0::2], xs[1::2]):
            j0 = max(0, math.ceil((a - x0) / res - 0.5))
            j1 = min(W, math.ceil((b - x0) / res - 0.5))
            if j1 > j0:
                yield i, j0, j1


class Grid:
    """Растр U8 в памяти, выровненный по сетке EPSG:3035 и по километровым клеткам."""

    def __init__(self, data: bytes, bbox: tuple[int, int, int, int], res: int):
        self.data, self.bbox, self.res = data, bbox, res
        self.W = int((bbox[2] - bbox[0]) / res)
        self.H = int((bbox[3] - bbox[1]) / res)
        assert len(data) == self.W * self.H, (len(data), self.W, self.H)
        self.step = 1000 // res            # пикселей в километровой клетке

    def tally(self, rings, values: tuple[int, ...], ucuc: set | None = None):
        """Счётчики значений внутри полигона: всего и внутри клеток центров/кластеров."""
        x0, _, _, ytop = self.bbox
        kx0, W, step = x0 // 1000, self.W, self.step
        tot = dict.fromkeys(values, 0)
        inside = dict.fromkeys(values, 0)
        sums = [0, 0]                       # сумма значений, всего и в центрах — для TCD
        d = self.data
        for i, j0, j1 in spans(rings, x0, ytop, self.res, W, self.H):
            base = i * W
            ky = math.floor((ytop - (i + 0.5) * self.res) / 1000)
            s = j0
            while s < j1:
                e = min(j1, (s // step + 1) * step)
                seg = d[base + s: base + e]
                hit = ucuc is not None and (kx0 + s // step, ky) in ucuc
                for v in values:
                    c = seg.count(v)
                    if c:
                        tot[v] += c
                        if hit:
                            inside[v] += c
                sv = sum(seg)
                sums[0] += sv
                if hit:
                    sums[1] += sv
                s = e
        return tot, inside, sums


# ── загрузки ──────────────────────────────────────────────────────────────────────
def fetch(url: str, dest: Path) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    subprocess.run(["curl", "-sL", "--fail", "--retry", "4", "--retry-delay", "10", "-A", UA,
                    "--max-time", "900", "-o", str(tmp), url], check=True)
    tmp.replace(dest)
    return dest


def export_grid(key: str, bbox: tuple[int, int, int, int], city: str) -> Grid:
    """Сырые байты ImageServer по полосам ≤ 4000 строк; в ответе после данных идёт
    битовая маска, она отрезается."""
    url, res = RASTERS[key]
    x0, y0, x1, y1 = bbox
    W, H = int((x1 - x0) / res), int((y1 - y0) / res)
    dest = CACHE / f"{city}_{key}_{x0}_{y0}_{x1}_{y1}.u8"
    if dest.exists() and dest.stat().st_size == W * H:
        return Grid(dest.read_bytes(), bbox, res)
    out = bytearray()
    for r0 in range(0, H, 4000):
        h = min(4000, H - r0)
        ytop = y1 - r0 * res
        q = urllib.parse.urlencode({
            "bbox": f"{x0},{ytop - h * res},{x1},{ytop}", "bboxSR": 3035, "imageSR": 3035,
            "size": f"{W},{h}", "format": "bsq", "pixelType": "U8",
            "interpolation": "RSP_NearestNeighbor", "f": "image"})
        part = CACHE / f"{dest.stem}_{r0}.bsq"
        fetch(f"{url}/exportImage?{q}", part)
        raw = part.read_bytes()
        mask = -(-W // 8) * h
        if len(raw) not in (W * h, W * h + mask, W * h + -(-W * h // 8)):
            raise SystemExit(f"{key}: неожиданный размер ответа {len(raw)} для {W}×{h}")
        out += raw[: W * h]
        part.unlink()
    dest.write_bytes(bytes(out))
    return Grid(bytes(out), bbox, res)


def read_tiled_tiff(path: Path, cols: range, rows: range) -> dict[tuple[int, int], float]:
    """Несжатый плиточный TIFF (так устроены растры центров и кластеров Евростата)."""
    with path.open("rb") as f:
        hdr = f.read(8)
        bo = "<" if hdr[:2] == b"II" else ">"
        f.seek(struct.unpack(bo + "I", hdr[4:8])[0])
        tags = {}
        for _ in range(struct.unpack(bo + "H", f.read(2))[0]):
            tag, typ, cnt, val = struct.unpack(bo + "HHI4s", f.read(12))
            tags[tag] = (typ, cnt, val)

        def arr(tag):
            typ, cnt, val = tags[tag]
            size, fmt = {3: (2, "H"), 4: (4, "I")}[typ]
            if cnt * size <= 4:
                data = val[: cnt * size]
            else:
                pos = f.tell()
                f.seek(struct.unpack(bo + "I", val)[0])
                data = f.read(cnt * size)
                f.seek(pos)
            return struct.unpack(bo + fmt * cnt, data)

        W = arr(256)[0]
        tw, th = arr(322)[0], arr(323)[0]
        if arr(259)[0] != 1 or arr(258)[0] != 32:
            raise SystemExit(f"{path.name}: ожидался несжатый 32-битный растр")
        fmt = {1: "I", 2: "i", 3: "f"}[arr(339)[0]]
        offs = arr(324)
        across = -(-W // tw)
        out = {}
        for r in rows:
            for c in cols:
                t = (r // th) * across + c // tw
                f.seek(offs[t] + ((r % th) * tw + c % tw) * 4)
                out[(c, r)] = struct.unpack(bo + fmt, f.read(4))[0]
    return out


def ucuc_cells(bbox: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    """Клетки 1 км (индексы x//1000, y//1000 нижнего левого угла), где есть центр или кластер."""
    cells = set()
    for key, (url, stem) in CLUSTERS.items():
        z = fetch(url, CACHE / f"{stem}.zip")
        tif = CACHE / f"{stem}.tif"
        with zipfile.ZipFile(z) as zf:
            names = {Path(n).name: n for n in zf.namelist()}
            if not tif.exists():
                tif.write_bytes(zf.read(names[f"{stem}.tif"]))
            tfw = zf.read(names[f"{stem}.tfw"]).decode().split()
        ox, oy = float(tfw[4]) - 500, float(tfw[5]) + 500      # центр → угол
        x0, y0, x1, y1 = bbox
        cols = range(int((x0 - ox) // 1000), int((x1 - ox) // 1000))
        rows = range(int((oy - y1) // 1000), int((oy - y0) // 1000))
        for (c, r), v in read_tiled_tiff(tif, cols, rows).items():
            if v > 0 and v == v:                                # NaN не проходит
                cells.add((int((ox + c * 1000) // 1000), int((oy - (r + 1) * 1000) // 1000)))
    return cells


def gpkg_rings(blob: bytes) -> list[list[tuple[float, float]]]:
    """Геометрия GeoPackage: заголовок GP + ISO WKB (Polygon / MultiPolygon)."""
    if blob[:2] != b"GP":
        raise ValueError("не геометрия GeoPackage")
    env = (blob[3] >> 1) & 0b111
    o = 8 + {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[env]
    rings: list[list[tuple[float, float]]] = []

    def poly(o: int) -> int:
        bo = "<" if blob[o] == 1 else ">"
        t = struct.unpack(bo + "I", blob[o + 1:o + 5])[0]
        o += 5
        base, zm = t % 1000, t // 1000
        dims = {0: 2, 1: 3, 2: 3, 3: 4}[zm]
        if base == 6:
            n = struct.unpack(bo + "I", blob[o:o + 4])[0]
            o += 4
            for _ in range(n):
                o = poly(o)
            return o
        if base != 3:
            raise ValueError(f"тип WKB {t} не поддержан")
        nr = struct.unpack(bo + "I", blob[o:o + 4])[0]
        o += 4
        for _ in range(nr):
            npt = struct.unpack(bo + "I", blob[o:o + 4])[0]
            o += 4
            pts = struct.unpack(bo + "d" * (npt * dims), blob[o:o + 8 * npt * dims])
            o += 8 * npt * dims
            rings.append([(pts[k], pts[k + 1]) for k in range(0, len(pts), dims)])
        return o

    poly(o)
    return rings


def read_laus(ids: list[str]) -> dict[str, tuple[str, list]]:
    path = fetch(LAU_GPKG, CACHE / "LAU_RG_01M_2024_3035.gpkg")
    con = sqlite3.connect(path)
    tbl = con.execute("select table_name from gpkg_contents where data_type='features'").fetchone()[0]
    gcol = con.execute("select column_name from gpkg_geometry_columns where table_name=?", (tbl,)).fetchone()[0]
    q = f'select GISCO_ID, LAU_NAME, "{gcol}" from "{tbl}" where GISCO_ID in ({",".join("?" * len(ids))})'
    out = {gid: (name, gpkg_rings(blob)) for gid, name, blob in con.execute(q, ids)}
    con.close()
    missing = set(ids) - set(out)
    if missing:
        raise SystemExit(f"LAU нет в GISCO 2024: {sorted(missing)}")
    return out


def read_degurba(ids: list[str]) -> dict[str, dict]:
    """Класс урбанизации и площадь LAU из таблицы Евростата (лист страны)."""
    path = fetch(DEGURBA_XLSX, CACHE / "EU-27-LAU-2024-NUTS-2024.xlsx")
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    out: dict[str, dict] = {}
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        sheets = {s.get("name"): rels[s.get(rel)] for s in wb.find("m:sheets", ns)}
        shared = ["".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t"))
                  for si in ET.fromstring(z.read("xl/sharedStrings.xml"))]
        for cc in sorted({i.split("_")[0] for i in ids}):
            target = sheets[cc]
            root = ET.fromstring(z.read(target if target.startswith("xl/") else "xl/" + target))
            rows = []
            for r in root.iter(f"{{{ns['m']}}}row"):
                vals = []
                for c in r.findall("m:c", ns):
                    v = c.find("m:v", ns)
                    vals.append("" if v is None else shared[int(v.text)] if c.get("t") == "s" else v.text)
                rows.append(vals)
            head = rows[0]
            for r in rows[1:]:
                rec = dict(zip(head, r))
                if rec.get("EU LAU CODE") in ids:
                    out[rec["EU LAU CODE"]] = {"degurba": int(rec["DEGURBA"]),
                                               "area_km2": float(rec["TOTAL AREA (m2)"]) / 1e6,
                                               "population": int(float(rec["POPULATION"])),
                                               "name": rec.get("LAU NAME LATIN") or rec.get("LAU NAME NATIONAL")}
    return out


# ── расчёт ───────────────────────────────────────────────────────────────────────
def share(num: int, den: int) -> float | None:
    return num / den if den else None


METRICS = ("area_km2", "green", "green_with7", "green_no_water", "sealed", "canopy_wvl", "tcd", "tcd_any")


def measure(rings, grids: dict[str, Grid], ucuc: set | None) -> dict:
    """Все показатели одного полигона: по всей площади и внутри центров/кластеров.

    Кроме основного прочтения ст. 3(20) считаются два соседних — с пашней (класс 7)
    и без воды (класс 10): вердикт, который меняется от прочтения, печатается как
    неустойчивый. TCD даёт и среднюю плотность, и долю пикселей с любой кроной.
    """
    c_tot, c_in, _ = grids["clcplus"].tally(rings, CLC_VALID + (0,), ucuc)
    w_tot, w_in, _ = grids["wvl"].tally(rings, (0, 1, 254, 255), ucuc)
    t_tot, t_in, t_sum = grids["tcd"].tally(rings, (0, 254, 255), ucuc)

    def part(c, w, t, tsum, n_px):
        valid = sum(c[v] for v in CLC_VALID)
        green = sum(c[v] for v in GREEN)
        tcd_valid = n_px - t[254] - t[255]
        return {
            "area_km2": valid * 100 / 1e6,
            "green": share(green, valid),
            "green_with7": share(green + c[7], valid),
            "green_no_water": share(green - c[10], valid),
            "sealed": share(c[1], valid),
            "canopy_wvl": share(w[1], w[0] + w[1]),
            "tcd": (tsum - 254 * t[254] - 255 * t[255]) / 100 / tcd_valid if tcd_valid else None,
            "tcd_any": share(tcd_valid - t[0], tcd_valid),
            "n_clc": valid,
        }

    out = {"all": part(c_tot, w_tot, t_tot, t_sum[0], sum(c_tot.values()))}
    if ucuc is not None:
        out["ucuc"] = part(c_in, w_in, t_in, t_sum[1], sum(c_in.values()))
    return out


def exempt(m: dict, green_key: str = "green") -> tuple[bool, str]:
    g, c = m.get(green_key), m.get("canopy_wvl")
    if g is None or c is None:
        return False, "нет клеток городских центров и кластеров"
    ok_g, ok_c = g > GREEN_MIN, c > CANOPY_MIN
    if ok_g and ok_c:
        return True, "зелень и крона выше порогов"
    miss = []
    if not ok_g:
        miss.append(f"зелень {g * 100:.1f} % ≤ 45 %")
    if not ok_c:
        miss.append(f"крона {c * 100:.1f} % ≤ 10 %")
    return False, "; ".join(miss)


def bbox_of(ring_sets) -> tuple[int, int, int, int]:
    xs = [x for rings in ring_sets for ring in rings for x, _ in ring]
    ys = [y for rings in ring_sets for ring in rings for _, y in ring]
    return (math.floor(min(xs) / 1000) * 1000 - 1000, math.floor(min(ys) / 1000) * 1000 - 1000,
            math.ceil(max(xs) / 1000) * 1000 + 1000, math.ceil(max(ys) / 1000) * 1000 + 1000)


def r4(v):
    return "" if v is None else round(v, 4)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="brussels", choices=list(LAUS))
    args = ap.parse_args()
    city = args.city
    ids = LAUS[city]

    laus = read_laus(ids)
    deg = read_degurba(ids)
    units = ADAPTERS[city]().units()
    unit_rings = {u.id: rings_3035(u.geometry) for u in units}
    bbox = bbox_of([r for _, r in laus.values()] + list(unit_rings.values()))
    print(f"{city}: LAU {len(laus)}, секторов {len(units)}, рамка EPSG:3035 {bbox}")

    grids = {k: export_grid(k, bbox, city) for k in RASTERS}
    for k, g in grids.items():
        print(f"  {k}: {g.W}×{g.H} px по {g.res} м")
    ucuc = ucuc_cells(bbox)
    print(f"  клеток городских центров и кластеров 2021 в рамке: {len(ucuc)}")

    # Точные границы коммун: объединение секторов Statbel. Сектора делят территорию без
    # перекрытий, общие рёбра дают парные пересечения и правило чёт-нечет их склеивает.
    # Считается только там, где пакет покрывает коммуну целиком (у Антверпена нет порта).
    by_commune: dict[str, list] = {}
    area_by_commune: dict[str, float] = {}
    for u in units:
        code = f"BE_{u.id[:5]}"
        by_commune.setdefault(code, []).extend(unit_rings[u.id])
        area_by_commune[code] = area_by_commune.get(code, 0) + u.area_ha / 100

    # По LAU — официальный расчёт и три проверки устойчивости вердикта
    shares = [k for k in METRICS if k != "area_km2"]
    lau_rows = []
    agg: dict[str, dict] = {"all": {}, "ucuc": {}}
    for gid in ids:
        name, rings = laus[gid]
        m = measure(rings, grids, ucuc)
        ok, why = exempt(m["ucuc"])
        row = {"lau_id": gid, "name": name, "degurba": deg.get(gid, {}).get("degurba"),
               "population": deg.get(gid, {}).get("population"),
               "area_km2_official": round(deg.get(gid, {}).get("area_km2", 0), 3),
               **{f"{k}_{part}": m[part][k] for part in ("all", "ucuc") for k in METRICS},
               "exempt": ok, "reason": why,
               "exempt_with7": exempt(m["ucuc"], "green_with7")[0],
               "exempt_no_water": exempt(m["ucuc"], "green_no_water")[0]}
        official = deg.get(gid, {}).get("area_km2")
        if gid in by_commune and official and area_by_commune[gid] / official > 0.98:
            ms = measure(by_commune[gid], grids, ucuc)["ucuc"]
            row.update({"green_ucuc_statbel": ms["green"], "canopy_wvl_ucuc_statbel": ms["canopy_wvl"],
                        "exempt_statbel": exempt(ms)[0]})
        else:
            row.update({"green_ucuc_statbel": None, "canopy_wvl_ucuc_statbel": None, "exempt_statbel": None})
        row["stable"] = all(v is None or v == ok
                            for v in (row["exempt_with7"], row["exempt_no_water"], row["exempt_statbel"]))
        lau_rows.append(row)
        for part in ("all", "ucuc"):
            a, w = agg[part], m[part]["area_km2"]
            a["area_km2"] = a.get("area_km2", 0) + w
            for k in shares:
                if m[part][k] is not None:
                    s = a.setdefault(k, [0.0, 0.0])
                    s[0] += m[part][k] * w
                    s[1] += w

    region = {part: {"area_km2": agg[part]["area_km2"],
                     **{k: (agg[part][k][0] / agg[part][k][1] if k in agg[part] and agg[part][k][1] else None)
                        for k in shares}}
              for part in ("all", "ucuc")}
    region_ok, region_why = exempt(region["ucuc"])

    # По секторам — диагностика и сверка с нашими приборами
    sec_rows = []
    for u in units:
        m = measure(unit_rings[u.id], grids, ucuc)
        a, b = m["all"], m["ucuc"]
        sec_rows.append({"id": u.id, "name": u.name or "", "commune": u.commune or "",
                         "area_ha": round(u.area_ha, 2), "population": u.population,
                         "green_clcplus": a["green"], "sealed_clcplus": a["sealed"],
                         "canopy_wvl": a["canopy_wvl"], "tcd_2018": a["tcd"],
                         "ucuc_share": share(b["n_clc"], a["n_clc"])})

    checks = {}
    for gid, row in zip(ids, lau_rows):
        off = row["area_km2_official"]
        if off:
            checks.setdefault("area_ratio", []).append(row["area_km2_all"] / off)
    checks["area_ratio_min"] = min(checks["area_ratio"])
    checks["area_ratio_max"] = max(checks.pop("area_ratio"))
    if city == "brussels":
        # Регион публикует «37 % по Copernicus, 2018». Способ расчёта не назван, поэтому
        # печатаются оба прочтения TCD: средняя плотность и доля пикселей с любой кроной.
        checks["tcd_2018_region_mean_density"] = region["all"]["tcd"]
        checks["tcd_2018_region_share_any"] = region["all"]["tcd_any"]
        checks["tcd_2018_published"] = BXL_TCD_2018_PUBLISHED
    checks["unstable_laus"] = [r["lau_id"] for r in lau_rows if not r["stable"]]

    corr = {}
    for layer, col in (("article8_2024", "trees_2024"), ("worldcover_2021", "wc_trees"),
                       ("canopy_probav_2019", "canopy_share")):
        p = ROOT / f"cities/{city}/layers/{layer}.csv"
        if not p.exists():
            continue
        other = {r["id"]: float(r[col]) for r in csv.DictReader(p.open()) if r.get(col) not in ("", None)}
        pairs = [(s["canopy_wvl"], other[s["id"]]) for s in sec_rows
                 if s["canopy_wvl"] is not None and s["id"] in other]
        if len(pairs) > 30:
            xs, ys = zip(*pairs)
            corr[layer] = {"r": round(statistics.correlation(xs, ys), 3), "n": len(pairs),
                           "mean_wvl": round(statistics.mean(xs), 4), "mean_other": round(statistics.mean(ys), 4)}

    # Запись
    layers = ROOT / f"cities/{city}/layers"
    layers.mkdir(parents=True, exist_ok=True)
    with (layers / "art8_official_lau_2021.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(lau_rows[0]))
        w.writeheader()
        for r in lau_rows:
            w.writerow({k: (r4(v) if isinstance(v, float) else v) for k, v in r.items()})
    with (layers / "art8_official_2021.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(sec_rows[0]))
        w.writeheader()
        for r in sec_rows:
            w.writerow({k: (r4(v) if isinstance(v, float) else v) for k, v in r.items()})
    summary = {
        "city": city, "computed": date.today().isoformat(),
        "rule": "ст. 8(1): зелень > 45 % и крона > 10 % в городских центрах и кластерах (сетка 1 км², 2021)",
        "inputs": {"lau": LAU_GPKG, "degurba": DEGURBA_XLSX,
                   "clusters": {k: v[0] for k, v in CLUSTERS.items()},
                   **{k: v[0] for k, v in RASTERS.items()}},
        "green_classes_clcplus": list(GREEN),
        "bbox_3035": bbox, "ucuc_cells": len(ucuc),
        "laus": [{k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()} for r in lau_rows],
        "region": {"parts": {p: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in d.items()}
                             for p, d in region.items()},
                   "exempt": region_ok, "reason": region_why},
        "checks": {k: round(v, 4) if isinstance(v, float) else v for k, v in checks.items()},
        "correlations_canopy": corr,
    }
    (layers / "art8_official_2021_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))

    n_ex = sum(r["exempt"] for r in lau_rows)
    m = Manifest.read(city)
    m.add(LayerEntry(
        layer="art8_official_lau_2021", computed=date.today().isoformat(), n_units=len(lau_rows),
        measures="доля городской зелени и кроны по LAU и в клетках городских центров и кластеров; "
                 "исключение ст. 8(1) — зелень > 45 % и крона > 10 %",
        unit="доля площади 0–1",
        method="повтор скрипта EEA/JRC NRR_Art8: LAU 2024 (GISCO 1:1M) × сетка центров и кластеров 2021 "
               "(1 км²), доля пикселей класса внутри полигона по центрам пикселей",
        source="Copernicus CLCplus Backbone 2021 (10 м), HRL Woody Vegetation Layer 2021 (5 м), "
               "HRL Tree Cover Density 2018 (10 м); Евростат LAU 2024, DEGURBA 2024, кластеры 2021",
        threshold=None,
        threshold_source="порога значимости нет: это официальный уровень, а не изменение; пороги 45 % и 10 % — "
                         "правило исключения ст. 8(1), а не порог шума",
        limits=["зелень по CLCplus 2021, а регламент называет 2023; крона по WVL 2021 — разрешён для "
                "черновиков планов, для окончательных нужен WVL 2024 (у стран, не в открытом доступе)",
                "соответствие классов CLCplus определению ст. 3(20) — наше прочтение; вердикт "
                "перепроверен с пашней как зеленью и без воды",
                "границы LAU 1:1M: у мелких коммун площадь расходится с официальной на проценты; "
                "вердикт перепроверен на точных границах секторов Statbel, где пакет покрывает коммуну",
                f"исключение проходят {n_ex} из {len(lau_rows)} LAU; меняется от прочтения — "
                f"{len(checks['unstable_laus'])}; решение об объединении LAU принимает государство"]))
    m.add(LayerEntry(
        layer="art8_official_2021", computed=date.today().isoformat(), n_units=len(sec_rows),
        measures="доля городской зелени (CLCplus) и кроны (WVL, TCD) по сектору на официальных слоях Copernicus",
        unit="доля площади 0–1",
        method="доля пикселей класса внутри сектора по центрам пикселей, сетка EPSG:3035 без передискретизации",
        source="Copernicus CLCplus Backbone 2021, HRL Woody Vegetation Layer 2021, HRL Tree Cover Density 2018",
        threshold=None,
        threshold_source="порога нет: официальное состояние для сверки с нашими приборами, изменение по нему не меряется",
        limits=["один год на слой, ряда нет — изменения этим слоем не измерить",
                "WVL — любая древесная растительность без порога высоты, кусты входят",
                "сверка с нашими приборами — по рангу: "
                + "; ".join(f"{k} r = {v['r']}" for k, v in corr.items())]))
    m.write()

    print("\nLAU (исключение считается в клетках центров и кластеров):")
    print(f"  {'LAU':<10} {'название':<34} {'зелень':>7} {'+пашня':>7} {'−вода':>6} {'Statbel':>7} "
          f"{'крона':>6}  исключение")

    def fmt(v):
        return "—" if v is None else f"{v * 100:.1f}"

    for r in lau_rows:
        print(f"  {r['lau_id']:<10} {r['name'][:34]:<34} {fmt(r['green_ucuc']):>7} "
              f"{fmt(r['green_with7_ucuc']):>7} {fmt(r['green_no_water_ucuc']):>6} "
              f"{fmt(r['green_ucuc_statbel']):>7} {fmt(r['canopy_wvl_ucuc']):>6}  "
              f"{'ДА' if r['exempt'] else 'нет'}{'' if r['stable'] else ' (НЕУСТОЙЧИВО)'} · {r['reason']}")
    if len(lau_rows) > 1:
        rg = region["ucuc"]
        print(f"  {'вместе':<10} {'все LAU как одна экосистема':<34} {fmt(rg['green']):>7} "
              f"{fmt(rg['green_with7']):>7} {fmt(rg['green_no_water']):>6} {'—':>7} "
              f"{fmt(rg['canopy_wvl']):>6}  {'ДА' if region_ok else 'нет'} · {region_why}")
    print(f"\nпроверки: {summary['checks']}")
    print(f"корреляции кроны WVL с нашими приборами по секторам: {corr}")
    print(f"→ {layers}/art8_official_lau_2021.csv, art8_official_2021.csv, _summary.json · слоёв в манифесте {len(m.layers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
