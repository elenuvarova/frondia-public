#!/usr/bin/env python3
"""
Данные для атласа: секторы города → упрощённые SVG-пути + атрибуты слоя ст. 8,
и гистограмма нулевого распределения из ТОГО ЖЕ слоя — чтобы легенда была
распределением ровно тех чисел, что на карте.

Проекция равнопромежуточная (метры), упрощение Дугласа–Пекера с допуском 8 м,
холст шириной 1000. Детерминировано: тот же вход — тот же файл.

Запуск:
    .venv/bin/python scripts/report/atlas_data.py --city brussels
"""
from __future__ import annotations
import argparse, csv, json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS
from engine.config import CITIES
from engine.manifest import Manifest

from scripts.report.paths import DERIVED, OUT as SCRATCH  # noqa: E402
HIST = {"brussels": (-0.10, 0.13, 46), "antwerp": (-0.12, 0.16, 56), "ghent": (-0.09, 0.10, 38),
        "liege": (-0.14, 0.06, 40), "charleroi": (-0.11, 0.08, 38)}


def rings(g):
    return [g["coordinates"][0]] if g["type"] == "Polygon" else [pp[0] for pp in g["coordinates"]]


def dp(pts, eps):
    """Дуглас–Пекер для ОТКРЫТОЙ линии. Кольца идут через `dp_ring`, не сюда."""
    if len(pts) < 3: return pts
    (ax, ay), (bx, by) = pts[0], pts[-1]; dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy); dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        # при совпадающих концах «до линии» не бывает — меряем до точки
        d = abs(dy * px - dx * py + bx * ay - by * ax) / L if L > 1e-9 else math.hypot(px - ax, py - ay)
        if d > dmax: dmax, idx = d, i
    return dp(pts[:idx + 1], eps)[:-1] + dp(pts[idx:], eps) if dmax > eps else [pts[0], pts[-1]]


def dp_ring(ring, eps):
    """Упрощение ЗАМКНУТОГО кольца.

    ⚠️ Дефект, из-за которого написана эта функция (найден 24.09.2026): кольцо
    отдавалось прямо в `dp`. У замкнутого кольца первая и последняя точка
    совпадают, базовая линия нулевой длины, все расстояния до неё выходили
    нулевыми — и КАЖДЫЙ сектор схлопывался в две одинаковые точки. Карта атласа
    с 2 сентября рисовала пустоту, а подписи, гистограмма и таблицы вокруг неё
    выглядели полными, поэтому дефект не бросался в глаза.

    Кольцо режется в самой дальней от начала точке, половины упрощаются отдельно.
    Если упрощение оставило меньше трёх точек, берётся исходное кольцо.
    """
    pts = ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else list(ring)
    if len(pts) < 4:
        return pts
    x0, y0 = pts[0]
    k = max(range(len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
    out = dp(pts[:k + 1], eps)[:-1] + dp(pts[k:] + [pts[0]], eps)[:-1]
    return out if len(out) >= 3 else pts


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--city", choices=list(CITIES), required=True)
    args = ap.parse_args()
    units = ADAPTERS[args.city]().units()
    a8 = {r["id"]: r for r in csv.DictReader(open(f"cities/{args.city}/layers/article8_2024.csv"))}
    lat0 = sum(u.centroid[1] for u in units) / len(units)
    kx = 111320 * math.cos(math.radians(lat0)); ky = 110540
    xs = [p[0] for u in units for r in rings(u.geometry) for p in r]
    ys = [p[1] for u in units for r in rings(u.geometry) for p in r]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    W = 1000.0; scale = W / ((x1 - x0) * kx); H = (y1 - y0) * ky * scale
    P = lambda p: ((p[0] - x0) * kx * scale, (y1 - p[1]) * ky * scale)
    eps = 8 * scale

    def fl(r, k):
        try: return round(float(r.get(k, "")), 4)
        except (TypeError, ValueError): return None

    out, n = [], 0
    for u in units:
        d = ""
        for r in rings(u.geometry):
            pts = dp_ring([P(p) for p in r], eps); n += len(pts)
            d += "M" + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
        r = a8.get(u.id, {})
        # Отказ считать — отказ и на карте: сектор с несопоставимым контролем
        # не красится и не входит в легенду. Иначе атлас показывал 16 «сверх
        # порога», а тренд ст. 8 — 14, и два числа на одной странице расходились.
        comparable = str(r.get("comparable", "")).lower() in ("true", "1", "yes")
        ne = fl(r, "ndvi_eff") if comparable else None
        te = fl(r, "trees_eff") if comparable else None
        # вердикт берём из слоя, а не пересчитываем из округлённого эффекта:
        # округление до 4 знаков сдвигало сектор на границе порога через неё
        nv_raw = r.get("ndvi_verdict", "")
        out.append({"id": u.id, "n": u.name, "c": u.commune, "d": d, "pop": u.population,
                    "inc": fl(r, "income"), "ne": ne, "te": te, "cmp": comparable,
                    "nv": nv_raw, "tv": r.get("trees_verdict", ""),
                    "n24": fl(r, "ndvi_2024"), "t24": fl(r, "trees_2024")})
    # «измерено» = попал в слой; «отказ» = измерен, но контроль несопоставим.
    # Раньше «измерено» считало только сопоставимые, и на странице стояло 667
    # против 686 в отчёте ст. 8 — два числа об одном не совпадали.
    meta = {"W": round(W), "H": round(H), "n": len(out),
            "measured": sum(1 for o in out if o["id"] in a8),
            "refused": sum(1 for o in out if o["id"] in a8 and not o["cmp"])}
    json.dump({"meta": meta, "sectors": out}, open(DERIVED / f"atlas-{args.city}.json", "w"), ensure_ascii=False)

    # Порог — тот же, по которому слой ст. 8 вынес вердикты: он считается тем же прогоном,
    # что и эффекты. Порог прибора из манифеста посчитан другой схемой подбора.
    s8 = Path(f"cities/{args.city}/layers/article8_2024_summary.json")
    thr = ((json.loads(s8.read_text()).get("thresholds") or {}).get("ndvi") if s8.exists() else None) \
        or Manifest.read(args.city).layers["ndvi"].threshold
    eff = [o["ne"] for o in out if o["ne"] is not None]
    lo, hi, nb = HIST[args.city]; bins = [0] * nb
    for e in eff:
        bins[min(max(int((e - lo) / (hi - lo) * nb), 0), nb - 1)] += 1
    # счётчики хвостов — по вердикту слоя, тому же, что в отчёте ст. 8
    above = sum(1 for o in out if o["nv"] == "рост"); below = sum(1 for o in out if o["nv"] == "потеря")
    json.dump({"lo": lo, "hi": hi, "n": nb, "counts": bins, "threshold": thr, "total": len(eff),
               "above": above, "below": below},
              open(DERIVED / f"atlas-hist-{args.city}.json", "w"))
    print(f"{args.city}: {len(out)} секторов, измерено {meta['measured']}, вершин {n:,}, холст {meta['W']}×{meta['H']}, "
          f"сверх {above} / ниже {below} · отказ {meta['refused']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
