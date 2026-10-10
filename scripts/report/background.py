"""Фон города: насколько город зеленел сам по себе и сколько секторов «значимы» без контроля.

Зачем отдельный модуль. До 25.09.2026 пять страниц печатали одну фразу: «медиана
изменения по всему Брюсселю +0,043 — больше порога 0,037, без контроля значимым
выглядел бы почти каждый сектор». Число +0,043 — медиана по пикселям 100 м
(`export_before_after.py`), а порог откалиброван на эффектах СЕКТОРОВ. По секторам
медиана сырого изменения +0,033 — меньше порога, и «почти каждый» было
преувеличением: без контроля за порог выходит треть секторов, с контролем — единицы.
Довод за разность разностей остаётся и становится сильнее, но теперь его считают
здесь, из тех же слоёв, что атлас, — и для каждого города свой.

Всё из одного прогона слоя `article8_2024.csv`: сырое изменение `ndvi_raw`, вердикт
против контроля (только сопоставимые секторы) и порог из сводки слоя — тот, что посчитан
тем же прогоном. Смешивать снимки архива разных дней нельзя: сырые изменения у самого
порога, и счёт «без контроля» чувствителен к любому сдвигу.
"""
from __future__ import annotations

import csv
import statistics
from pathlib import Path

from engine.manifest import Manifest

ROOT = Path(__file__).resolve().parents[2]
GEN = {"brussels": "Брюсселя", "antwerp": "Антверпена", "ghent": "Гента", "liege": "Льежа", "charleroi": "Шарлеруа"}


def plural(n: int, one: str, few: str, many: str) -> str:
    n10, n100 = n % 10, n % 100
    return one if n10 == 1 and n100 != 11 else few if 2 <= n10 <= 4 and not 12 <= n100 <= 14 else many


def background(city: str) -> dict | None:
    chg = ROOT / f"cities/{city}/layers/sector_change_2017_2024.csv"
    a8 = ROOT / f"cities/{city}/layers/article8_2024.csv"
    if not a8.exists():
        return None
    # сырое изменение — из того же прогона, что и вердикты (слой ст. 8 хранит свои входы);
    # таблица калибровки — запасной путь для слоя, посчитанного до 25.09.2026
    a8_rows = list(csv.DictReader(a8.open()))
    if a8_rows and a8_rows[0].get("ndvi_raw") not in (None, ""):
        raw = {r["id"]: float(r["ndvi_raw"]) for r in a8_rows if r.get("ndvi_raw")}
    else:
        raw = {r["id"]: float(r["d_ndvi_raw"]) for r in csv.DictReader(chg.open()) if r.get("d_ndvi_raw")}
    # вердикт — из слоя: он вынесен по полной точности, а эффект в CSV округлён до 4 знаков,
    # и сектор у самого порога при повторном сравнении переходил бы через него
    verdict = {r["id"]: r.get("ndvi_verdict", "") for r in csv.DictReader(a8.open())
               if r.get("ndvi_eff") and r.get("comparable") == "True"}
    ids = sorted(set(raw) & set(verdict))
    if not ids:
        return None
    # порог — тот же, по которому слой ст. 8 выносит вердикты (посчитан тем же прогоном)
    import json
    s8 = ROOT / f"cities/{city}/layers/article8_2024_summary.json"
    thr = ((json.loads(s8.read_text()).get("thresholds") or {}).get("ndvi") if s8.exists() else None) \
        or Manifest.read(city, root=ROOT / "cities").layers["ndvi"].threshold
    k_raw = sum(raw[i] > thr for i in ids)
    k_eff = sum(verdict[i] == "рост" for i in ids)
    return {"n": len(ids), "thr": thr, "raw_median": statistics.median(raw[i] for i in ids),
            "k_raw": k_raw, "k_eff": k_eff, "share_raw": k_raw / len(ids)}


def sentence(city: str, with_threshold: bool = True) -> str:
    """Одна фраза для любой страницы: фон, порог и цена отказа от контроля.

    `with_threshold=False` — для страниц аудита: там свой порог, посчитанный под схему
    подбора аудита, и второе число рядом только путает. Счёт от этого не меняется."""
    b = background(city)
    if not b:
        return "Город зеленеет и без вмешательств, поэтому эффект считается против контроля, а не против прошлого."
    word = plural(b["k_raw"], "сектор", "сектора", "секторов")
    thr_txt = f" при пороге {b['thr']:.3f}" if with_threshold else ""
    return (f"За 2017–2024 годы медиана сырого изменения зелёности по секторам {GEN.get(city, city)} "
            f"{b['raw_median']:+.3f}{thr_txt}: зеленел весь город. Без вычитания контроля "
            f"«значимо позеленевшими» оказались бы {b['k_raw']} {word} из {b['n']} — "
            f"{100 * b['share_raw']:.0f} %; против контроля — {b['k_eff']}.")
