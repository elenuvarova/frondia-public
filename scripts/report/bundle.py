#!/usr/bin/env python3
"""
Городской пакет: измеренные слои в `cities/<city>/layers/` с записью в манифесте.

Правило проекта: слой без манифеста в отчёт не попадает. До этого скрипта оно
выполнялось только для слоя ст. 8 — остальные измерения (изменение по секторам,
аудит парков, мониторинг сезона) лежали в `data/` без записи о методе, источнике
и происхождении порога. Здесь они переезжают в пакет и регистрируются.

Пакет — формат обмена между проектами (`docs/03-architecture.md`): единицы,
слои по единице, точки, манифест. Другой проект читает пакет, не наш код.

Запуск:  .venv/bin/python scripts/report/bundle.py --city brussels
"""
from __future__ import annotations
import argparse, csv, shutil, sys, json
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.manifest import LayerEntry, Manifest

# Порог сезона — свой на каждую пару (город, сезон), окно (сезон−3 … сезон−1) → сезон.
# С сезона 2026 его пишет сам monitor_season.py в data/monitoring_<city>_<season>_calibration.json;
# вписанные руками значения остались только для двух первых сезонов, у которых такого файла нет.
SEASON_THR = {("brussels", 2024): 0.0312, ("antwerp", 2024): 0.0477,
              ("brussels", 2025): 0.0280, ("antwerp", 2025): 0.0395}
SEASON_NOTE = {2024: "подтверждённых потерь кроны в 2024 — ноль в обоих городах",
               2025: "2025: Брюссель — одна подтверждённая потеря кроны (Wolvendael, буря 09.07.2024, ~100 деревьев спилено); Антверпен — ноль",
               2026: "2026: Брюссель — три потери кроны по двум приборам, одна из них по документам стройплощадка "
                     "(Peterbos, работы с 04.2026); Wolvendael — повторная регистрация бури 2024; Антверпен — ноль"}
# Гент (третий город, 26.09.2026): свои итоги сезонов, общая строка выше говорит о двух первых городах
SEASON_NOTE_CITY = {("ghent", 2024): "2024: подтверждённых потерь кроны — ноль, строек — ноль",
                    ("ghent", 2025): "2025: одна стройка (Kiekebossen), подтверждённых потерь кроны — ноль",
                    ("ghent", 2026): "2026: две стройки (Kiekebossen повторно, Klosse) и одна потеря кроны по двум приборам "
                                     "(Lake, 40 га, жителей нет); причина по документам не установлена",
                    ("liege", 2024): "2024: одна потеря кроны по двум приборам (Le Werihet, лес, жителей нет); строек — ноль",
                    ("liege", 2025): "2025: Le Werihet теряет крону второй сезон подряд, одна стройка (Verhaeren); "
                                     "причина потери по документам не установлена",
                    ("liege", 2026): "2026: подтверждённых потерь кроны — ноль, строек — ноль",
                    ("charleroi", 2024): "2024: подтверждённых потерь кроны — ноль, строек — ноль",
                    ("charleroi", 2025): "2025: одна стройка (Sart les Moines), подтверждённых потерь кроны — ноль",
                    ("charleroi", 2026): "2026: одна стройка (La Providence), подтверждённых потерь кроны — ноль"}


def season_calibration(city: str) -> dict[int, tuple[float, str]]:
    """Сезон → (порог, происхождение). Файл калибровки прогона важнее вписанного числа."""
    out = {s: (thr, f"нулевое распределение мониторинга, окно {s-3}–{s-1} → {s}, {city}")
           for (c, s), thr in SEASON_THR.items() if c == city}
    for f in sorted(Path("data").glob(f"monitoring_{city}_*_calibration.json")):
        j = json.loads(f.read_text())
        out[int(j["season"])] = (float(j["threshold"]), j["source"] + (f"; среднее {j['mean']:+.5f}, n = {j['n']}"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--city", required=True); args = ap.parse_args()
    city = args.city; pre = "" if city == "brussels" else f"{city}_"
    src = {
        "sector_change_2017_2024": Path(f"data/{pre}sector_change_2017_2024.csv"),
        "park_audit_2017_2024": Path(f"data/park_audit_{city}_2017_2024.csv") if city != "brussels" else Path("data/park_audit_2017_2024.csv"),
    }
    seasons = season_calibration(city)
    for season in sorted(seasons):
        p24 = Path("data/monitoring_2024.csv") if (city == "brussels" and season == 2024) else Path(f"data/monitoring_{city}_{season}.csv")
        src[f"monitoring_{season}"] = p24
    dated = Path(f"data/registry/{city}_park_audit_dated.csv")
    if dated.exists():
        src["park_audit_dated"] = dated
    # Брюссель: аудит старых проектов Landsat-ом. Страница реестра печатает эти
    # вердикты — значит слой обязан быть в манифесте, иначе нарушено собственное
    # правило «слой без манифеста в отчёт не попадает».
    lnd = Path("data/registry/beliris_landsat_audit.csv")
    if city == "brussels" and lnd.exists():
        src["park_audit_landsat"] = lnd
    m = Manifest.read(city); ndvi_thr = m.layers["ndvi"].threshold; ndvi_src = m.layers["ndvi"].threshold_source
    layers_dir = Path(f"cities/{city}/layers"); layers_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat(); added = []
    meta = {
        "sector_change_2017_2024": dict(
            measures="изменение зелёности по единицам против подобранного контроля, 2017–2019 → 2021–2024",
            unit="ед. NDVI", method="разность разностей, 12 контролей по (NDVI, LST) «до», одна нормировка на город",
            source="Sentinel-2 SR Harmonized, летние медианы; Landsat C2 L2 для LST «до»",
            threshold=ndvi_thr, threshold_source=ndvi_src,
            limits=["сохранённые значения округлены до 4 знаков", "единица — сектор: рассеянные посадки тонут в площади"]),
        "park_audit_2017_2024": dict(
            measures="изменение зелёности по именованным паркам OSM ≥ 1 га против подобранного контроля",
            unit="ед. NDVI", method="разность разностей, контроль — 12 секторов по NDVI «до», отказ при разрыве > 0,04",
            source="Sentinel-2 + Dynamic World (второй прибор), периметры OSM",
            threshold=ndvi_thr, threshold_source=ndvi_src,
            limits=["порог калиброван на секторах, парки мельче — порог оптимистичен",
                    "стандартное окно; для парков с известной датой сдачи нужны окна под проект",
                    "детектор изменений, не аудит вмешательств: причина — из документов"]),
    }
    for season, (thr, thr_src) in sorted(seasons.items()):
        meta[f"monitoring_{season}"] = dict(
            measures=f"изменение зелёности за сезон {season} против базы {season-3}–{season-1}, по единицам",
            unit="ед. NDVI", method="разность разностей, скользящая база, свой порог сезона; потеря публикуется только при согласии DW, "
                                   "причина — по документам",
            source="Sentinel-2, Dynamic World (trees, built) для корроборации",
            threshold=thr, threshold_source=thr_src,
            limits=["один сезон шумнее четырёхлетнего окна",
                    SEASON_NOTE_CITY.get((city, season)) or SEASON_NOTE.get(season, f"{season}: итог сезона — в бюллетене мониторинга")])
    if "park_audit_dated" in src:
        meta["park_audit_dated"] = dict(
            measures="эффект по паркам с известной датой сдачи: окно под проект, порог под окно",
            unit="ед. NDVI", method=("разность разностей, 12 контролей по NDVI «до»; прибор выбирает движок по году И площади следа "
                                     "(engine.audit.instrument_for); вердикт понижается до предварительного, если сцен меньше 8"),
            source="Sentinel-2 и Landsat C2 L2, Dynamic World для словаря исходов; даты — реестр проектов города",
            threshold=None,
            threshold_source="нулевое распределение по всем секторам города, пересчитанное на КАЖДОМ окне; значение порога — в поле threshold строки",
            limits=["порог свой у каждого окна — общий порог города сюда не переносится",
                    "объекты < 3 га на Landsat 30 м не измеряются, помечены отдельно",
                    "привязка проект→парк по имени и расстоянию: точка рядом с чужим парком следом не считается"])

    if "park_audit_landsat" in src:
        meta["park_audit_landsat"] = dict(
            measures="эффект по проектам, сданным до эры Sentinel-2: окно под проект, порог под окно",
            unit="ед. NDVI", method=("разность разностей, 12 контролей по NDVI «до»; Landsat C2 L2, 30 м; "
                                     "порог считается заново на каждом окне по всем секторам города"),
            source="Landsat 5/7/8/9 Collection 2 Level 2, летние медианы; даты и координаты — реестр Beliris",
            # порога на слой нет: он свой у каждого окна и напечатан в строке.
            # Происхождение всё равно обязано быть названо — иначе слой без провенанса.
            threshold=None,
            threshold_source="нулевое распределение по всем секторам города, пересчитанное на КАЖДОМ окне; значение порога — в поле threshold строки",
            limits=["объекты < 3 га на 30 м — 11–30 пикселей: вердикт не измерение, а видимость",
                    "сопоставление проект→парк по координате в 500 м: на мелких объектах не работает",
                    "порог свой у каждого окна — общий порог города сюда не переносится"])

    # слой ст. 8 уже лежит в пакете — регистрируем, иначе он «не публикуем» по нашему же правилу
    a8 = layers_dir / "article8_2024.csv"
    if a8.exists() and "article8_2024" not in m.layers:
        n = sum(1 for _ in csv.DictReader(a8.open()))
        m.add(LayerEntry(layer="article8_2024", computed=today, n_units=n,
            measures="уровни 2024 (NDVI, крона, трава, застройка) и тренд к базе против контроля, по единицам",
            unit="ед. NDVI / вероятность класса", method="уровни — летние средние 2024; тренд — разность разностей, 12 контролей по (NDVI, LST) «до»",
            source="Sentinel-2, Dynamic World, Landsat LST «до»; доход — Statbel 2023",
            threshold=ndvi_thr, threshold_source=ndvi_src,
            limits=["значения классов — вероятности, не доли площади", "освобождение по 45 %/10 % решает делинеация государства"]))
        added.append(("article8_2024", n))
    for name, p in src.items():
        if not p.exists():
            print(f"  {name}: нет источника {p} — пропуск"); continue
        dst = layers_dir / f"{name}.csv"; shutil.copyfile(p, dst)
        n = sum(1 for _ in csv.DictReader(dst.open()))
        m.add(LayerEntry(layer=name, computed=today, n_units=n, **meta[name]))
        added.append((name, n))
    path = m.write()
    print(f"{city}: пакет обновлён → {path}")
    for name, n in added: print(f"  + {name:<26} {n:>4} строк")
    print(f"  слоёв в манифесте: {len(m.layers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
