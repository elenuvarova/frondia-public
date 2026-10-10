"""
Адаптер Гента — третий город, принят 26.09.2026 (фаза 2b, docs/07-unified-frondia.md).

Почему именно он
────────────────
Обязанность по ст. 8 регламента 2024/1991 кусает во Фландрии, и Гент, как Антверпен, слаб по норме
3-30-300. Третий город проверяет переносимость ещё раз: порог — свойство пары (город, прибор), и у Гента
он будет свой.

Откуда данные
─────────────
Гент — это сама коммуна (REFNIS 44021), а не прямоугольник вокруг неё: 201 сектор реестра Statbel 2024,
население на 1 января 2024 (`scripts/registry/ghent_sectors.py` → `data/ghent_sectors.geojson`,
названия и бывшие коммуны — `data/ghent_sector_names.csv`). Медианный облагаемый доход Statbel 2023 —
`data/ghent_income.csv` (`scripts/registry/statbel_income.py --city ghent`). Следы работ — парки OSM
≥ 1 га (`fetch_park_perimeters.py --city ghent`).

Устроен как антверпенский адаптер (тот же формат файла секторов), отличаются только пути и район по
умолчанию.
"""

from __future__ import annotations

from pathlib import Path

from .antwerp import AntwerpAdapter


class GhentAdapter(AntwerpAdapter):
    SLUG, BBOX = "ghent", (3.57, 50.97, 3.86, 51.20)
    SECTORS = Path("data/ghent_sectors.geojson")
    NAMES = Path("data/ghent_sector_names.csv")
    INCOME = Path("data/ghent_income.csv")      # Statbel, медианный облагаемый доход, 2023
    PARKS = Path("data/perimeters/parks_ghent.geojson")
    DEFAULT_DISTRICT = "Gent"
