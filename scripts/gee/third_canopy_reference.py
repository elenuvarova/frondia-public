#!/usr/bin/env python3
"""Третий прибор на крону: Copernicus Global Land (Proba-V), 100 м — независимо от ESA и Google.

Зачем. Долю кроны мы уже меряем двумя способами, и оба принадлежат по сути
одной школе: `trees_2024` — средняя вероятность класса Dynamic World (Google,
классификатор по Sentinel-2), `wc_trees` — доля площади ESA WorldCover (ESA, тот
же Sentinel-2, жёсткая классификация). Согласие двух приборов на одном сенсоре и
близких методах — слабое свидетельство. Нужен третий производитель с другим
определением кроны, чтобы понять, где расхождение — свойство сектора, а где
свойство метода.

Что берём. `COPERNICUS/Landcover/100m/Proba-V-C3/Global`, полоса
`tree-coverfraction` — Copernicus Global Land Service, производитель VITO (тот
самый, чьи тепловые карты мы берём как вход). Эпоха 2019, 100 м, НЕПРЕРЫВНАЯ
доля кроны 0–100 %, а не класс: продукт прямо отвечает на вопрос «какой процент
занят деревьями». Сенсор другой — PROBA-V, а не Sentinel-2, то есть третий
прибор независим и по производителю, и по съёмке.

Второй кандидат, `JRC/GFC2020/V3` (Global Forest Cover 2020, 10 м, JRC, под
регламент EUDR), пробовался и основным НЕ стал: изображение маскировано вне
леса, поэтому по секторам Антверпена оно отдаёт данные лишь для 58 из 458 — и
там, где отдаёт, среднее ровно 1,0. Без `unmask(0)` это не измерение, а список
секторов, куда попал лесной пиксель; с `unmask(0)` (как здесь, `--product gfc`)
считается честно, но прогон 10 м по 458 секторам не укладывается в разумное время
одного `getInfo`. Оставлен как опция, не как поставленный слой.

    .venv/bin/python scripts/gee/third_canopy_reference.py \
        --project my-project-maps-507221 --city antwerp [--product gfc|probav]

Пишет `data/external/third_canopy_<city>_sectors.csv` (id, name, canopy_share) и
печатает сверку с двумя нашими слоями: корреляции, средние, пять сильнейших
расхождений поимённо.

⚠️ Ограничения — читать до того, как цитировать числа.

  · **Год — 2019, и ряд закрыт.** Коллекция существует на 2015–2019, дальше не
    продолжается. Ни базой статьи 8 (2024), ни измерением изменений этот слой
    быть не может: это сверка СОСТОЯНИЯ, у неё нет ни окна, ни контроля, ни
    порога значимости. И он на пять лет старше нашей базы — часть расхождений
    с `trees_2024` объясняется просто временем.

  · **Разрешение 100 м — грубее наших приборов на порядок по площади пикселя.**
    Сектор Антверпена медианой в несколько десятков гектаров — это десятки
    пикселей. Величину по отдельному сектору читать нельзя, тем более по мелкому;
    слой годен для ранга и для агрегатов, а не для приговора одному сектору.
    Ноль в секторе значит «на 100-метровой сетке кроны не набралось», а не
    «деревьев нет».

  · **Определение кроны — главное расхождение, а не шум.** Proba-V считает долю
    кроны глобальной моделью по 100-метровым композитам, WorldCover — жёсткий
    класс 10 на 10 м, Dynamic World — среднюю вероятность класса. Три разные
    величины. По абсолютной величине они сходиться НЕ должны: измерено, что
    Proba-V даёт вдвое меньше WorldCover. Сравнивать корректно по рангу секторов
    (корреляция), а не по разнице долей.

  · **Городская крона систематически занижена.** На 100 м уличные посадки,
    дворовые деревья и узкие аллеи растворяются в смешанном пикселе с крышами.
    Поэтому расхождения концентрируются в плотных зелёных секторах, а не
    распределены равномерно.

  · Слой в манифест этим скриптом не пишется: манифест правится отдельно и
    осознанно, по правилу «слой без манифеста в отчёт не попадает».
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path

import ee

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.adapters import ADAPTERS  # noqa: E402
from engine.config import CITIES  # noqa: E402

PRODUCTS = {
    # имя: (описание, функция-конструктор изображения, масштаб)
    "gfc": ("JRC/GFC2020/V3 (JRC Global Forest Cover, эпоха 2020, 10 м) — "
            "не поставленный слой, см. докстринг", 10),
    "probav": ("COPERNICUS/Landcover/100m/Proba-V-C3/Global, tree-coverfraction "
               "(Copernicus Global Land / VITO, эпоха 2019, 100 м)", 100),
}


def build_image(product: str) -> ee.Image:
    if product == "gfc":
        # Изображение маскировано вне леса. Без unmask(0) среднее по сектору
        # считается только по лесным пикселям и всегда равно 1 — это не доля.
        return ee.Image("JRC/GFC2020/V3").unmask(0).gt(0).rename("canopy")
    coll = ee.ImageCollection("COPERNICUS/Landcover/100m/Proba-V-C3/Global")
    img = coll.filter(ee.Filter.eq("system:index", "2019")).first()
    return img.select("tree-coverfraction").divide(100).rename("canopy")


def read_col(path: Path, col: str) -> dict[str, float]:
    if not path.exists():
        return {}
    out: dict[str, float] = {}
    for r in csv.DictReader(path.open()):
        v = r.get(col)
        if v not in ("", None):
            out[r["id"]] = float(v)
    return out


def compare(label: str, ours: dict[str, float], theirs: dict[str, float],
            names: dict[str, str]) -> None:
    """Сверка по рангу. Величины трёх приборов не совпадают по построению."""
    pairs = [(theirs[k], ours[k], k) for k in theirs if k in ours]
    if len(pairs) < 30:
        print(f"  {label}: сопоставимых секторов {len(pairs)} — сверка не проводится")
        return
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    r = statistics.correlation(xs, ys)
    print(f"\n  сверка с {label}: r = {r:.3f} на {len(pairs)} секторах")
    print(f"    третий прибор (доля площади): {statistics.mean(xs):.4f}")
    print(f"    {label:<28} {statistics.mean(ys):.4f}")
    diffs = sorted(pairs, key=lambda t: -abs(t[0] - t[1]))
    print("    сильнейшие расхождения:")
    for new, old, uid in diffs[:5]:
        nm = names.get(uid) or uid
        print(f"      {uid} {nm[:28]:<30} третий {new:.3f} · {label} {old:.3f} · "
              f"разница {new - old:+.3f}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--city", default="antwerp", choices=list(CITIES))
    ap.add_argument("--product", default="probav", choices=list(PRODUCTS))
    args = ap.parse_args()
    ee.Initialize(project=args.project)
    city = args.city

    desc, scale = PRODUCTS[args.product]
    ad = ADAPTERS[city]()
    units = ad.units()
    meta = {u.id: u for u in units}
    print(f"{city}: секторов {len(units)}, продукт {desc}")

    fc = ee.FeatureCollection([ee.Feature(ee.Geometry(u.geometry), {"id": u.id}) for u in units])
    rows = build_image(args.product).reduceRegions(fc, ee.Reducer.mean(), scale).getInfo()["features"]

    got: dict[str, float] = {}
    for f in rows:
        p = f["properties"]
        # у изображения одна полоса: reduceRegions зовёт результат "mean"
        v = p.get("canopy", p.get("mean"))
        if v is None:
            continue
        got[p["id"]] = float(v)

    out = Path(f"data/external/third_canopy_{city}_sectors.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "name", "canopy_share"])
        for u in units:
            if u.id in got:
                w.writerow([u.id, u.name or "", round(got[u.id], 6)])
    print(f"  измерено секторов: {len(got)} · среднее {statistics.mean(got.values()):.4f} · "
          f"медиана {statistics.median(got.values()):.4f} · нулей "
          f"{sum(1 for v in got.values() if v == 0)}")

    pop = {u.id: u.population for u in units}
    tot = sum(pop[k] for k in got if pop.get(k))
    if tot:
        wm = sum(got[k] * (pop.get(k) or 0) for k in got) / tot
        print(f"  взвешено по населению: {wm:.4f}")

    # У секторов Антверпена в источнике нет названий. Чтобы расхождения были
    # опознаваемы, подписываем их коммуной и площадью из слоя статьи 8.
    labels: dict[str, str] = {}
    a8path = Path(f"cities/{city}/layers/article8_2024.csv")
    if a8path.exists():
        for r in csv.DictReader(a8path.open()):
            labels[r["id"]] = f"{r.get('commune', '')} {r.get('area_ha', '')} га".strip()
    # у Антверпена u.name совпадает с id — тогда подпись бесполезна
    names = {u.id: (u.name if u.name and u.name != u.id else labels.get(u.id) or u.id)
             for u in units}
    compare("wc_trees", read_col(Path(f"cities/{city}/layers/worldcover_2021.csv"), "wc_trees"),
            got, names)
    compare("trees_2024", read_col(Path(f"cities/{city}/layers/article8_2024.csv"), "trees_2024"),
            got, names)
    print(f"\n→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
