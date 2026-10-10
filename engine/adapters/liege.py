"""
Адаптер: Liège — валлонский город, принят 26.09.2026 (фаза 2b, docs/07-unified-frondia.md).

Решение Елены: после Гента взять Льеж и Шарлеруа, чтобы атлас стоял во всех трёх регионах Бельгии.
Обязанность по ст. 8 у Валлонии та же, а валлонская часть национального плана не сдана.

Liège — сама коммуна (REFNIS 62063), 184 секторов реестра Statbel 2024, 195 659 жителей на 1.1.2024
(`scripts/registry/city_sectors.py --city liege`). Названия — французские, как их пишет Statbel (прописными,
без ударений); районы — бывшие коммуны, приведённые к написанию (`DISTRICT_FR`). Доход — медианный
облагаемый Statbel 2023 (`statbel_income.py --city liege`). Устроен как адаптер Гента.
"""

from __future__ import annotations

from pathlib import Path

from .antwerp import AntwerpAdapter


class LiegeAdapter(AntwerpAdapter):
    SLUG, BBOX = "liege", (5.51, 50.55, 5.69, 50.70)
    SECTORS = Path("data/liege_sectors.geojson")
    NAMES = Path("data/liege_sector_names.csv")
    INCOME = Path("data/liege_income.csv")
    PARKS = Path("data/perimeters/parks_liege.geojson")
    DEFAULT_DISTRICT = "Liège"
