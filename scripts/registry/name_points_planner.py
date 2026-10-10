#!/usr/bin/env python3
"""Назвать точки линии выполнения из кандидатов City Planner: отсечка как контроль.

Почему это лучше моего правила отбора. Точки называет независимый движок с
опубликованным правилом: жадный решатель максимального покрытия по сетке спроса
с учётом депривации. Ранг присваивается по приросту покрытия, а не по тому,
где нам удобно.

**Контроль — кандидаты сразу ниже отсечки.** При бюджете 10 город получил бы
ранги 1–10; ранги 11–20 отобраны тем же движком из того же пула, но в
рекомендацию не попали. Сравнивать их честнее, чем «названные против случайных»:
отличие ровно одно — попал в отсечку или нет.

⚠️ Оговорка, которую нельзя опускать: жадный решатель добавляет точки по
убыванию прироста покрытия, поэтому ранги 11–20 по построению чуть хуже
рангов 1–10. Контроль не идеален — он консервативен: если объекты появятся
в названных точках чаще, часть разницы может объясняться тем, что они лучше.

    .venv/bin/python scripts/registry/name_points_planner.py --city antwerp
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.registries.points import PLANNER_KINDS, register, save  # noqa: E402

NAMED_TO, CONTROL_FROM, CONTROL_TO = 10, 11, 20
RADIUS_M = 50


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="antwerp")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = Path(args.out or f"data/registry/named_points_{args.city}.json")
    src = Path(f"cities/{args.city}/points")
    if not src.exists():
        print(f"нет точек в пакете: {src} — сначала импорт из планировщика", file=sys.stderr)
        return 1

    records = []
    for f in sorted(src.glob("*.geojson")):
        asset = f.stem
        kind = PLANNER_KINDS.get(asset)
        if kind is None:
            print(f"  {asset}: типа нет в белом списке — пропуск")
            continue
        gj = json.loads(f.read_text())
        meta = gj.get("properties", {})
        feats = sorted(gj["features"], key=lambda x: x["properties"]["rank"])
        if len(feats) < CONTROL_TO:
            print(f"  {asset}: рангов {len(feats)}, нужно {CONTROL_TO} — пропуск")
            continue
        rule = (f"City Planner, решатель {meta.get('solver')}, радиус обслуживания "
                f"{meta.get('service_radius_m'):.0f} м, пул {meta.get('n_candidates_pool')} кандидатов; "
                f"ранг по приросту покрытия с учётом депривации")
        n_named = 0
        for feat in feats:
            r = feat["properties"]["rank"]
            role = "named" if r <= NAMED_TO else ("control" if CONTROL_FROM <= r <= CONTROL_TO else None)
            if role is None:
                continue
            lon, lat = feat["geometry"]["coordinates"][:2]
            exp = (f"объект появится в {RADIUS_M} м от точки к следующей проверке, "
                   f"если город ставит там, где закрывается наибольший разрыв покрытия"
                   if role == "named" else
                   "контроль: тот же движок, тот же пул, ранг ниже отсечки бюджета — "
                   "рекомендацией не объявлен")
            records.append(register(
                id=f"{args.city[:3]}-pl-{asset}-{r:02d}", city=args.city,
                unit_id=f"{asset}#{r}", kind=kind, lon=lon, lat=lat, radius_m=RADIUS_M,
                role=role, rule=rule, expectation=exp,
                source=f"City Planner, {asset}, покрытие {meta.get('coverage_before')}"
                       f" → {meta.get('coverage_after')}",
                note=f"балл {feat['properties'].get('Score')}, разрыв "
                     f"{feat['properties'].get('GapScore')}, справедливость "
                     f"{feat['properties'].get('EquityIndex')}"))
            n_named += role == "named"
        print(f"  {asset:<18} {kind:<16} названных {n_named}, контрольных {CONTROL_TO - NAMED_TO}")

    save(records, out)
    n = sum(1 for r in records if r.role == "named")
    print(f"\nзарегистрировано {len(records)}: названных {n}, контрольных {len(records) - n}")
    print(f"→ {out}")
    csv_out = out.with_suffix(".csv")
    with csv_out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "unit_id", "role", "kind", "lon", "lat", "radius_m", "registered_at", "point_hash", "note"])
        for r in records:
            w.writerow([r.id, r.unit_id, r.role, r.kind, round(r.lon, 6), round(r.lat, 6),
                        r.radius_m, r.registered_at, r.point_hash, r.note])
    print(f"→ {csv_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
