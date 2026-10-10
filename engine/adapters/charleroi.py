"""
Адаптер: Charleroi — валлонский город, принят 26.09.2026 (фаза 2b, docs/07-unified-frondia.md).

Решение Елены: после Гента взять Льеж и Шарлеруа, чтобы атлас стоял во всех трёх регионах Бельгии.
Обязанность по ст. 8 у Валлонии та же, а валлонская часть национального плана не сдана.

Charleroi — сама коммуна (REFNIS 52011), 291 секторов реестра Statbel 2024, 204 205 жителей на 1.1.2024
(`scripts/registry/city_sectors.py --city charleroi`). Названия — французские, как их пишет Statbel (прописными,
без ударений); районы — бывшие коммуны, приведённые к написанию (`DISTRICT_FR`). Доход — медианный
облагаемый Statbel 2023 (`statbel_income.py --city charleroi`). Устроен как адаптер Гента.
"""

from __future__ import annotations

from pathlib import Path

from .antwerp import AntwerpAdapter


class CharleroiAdapter(AntwerpAdapter):
    SLUG, BBOX = "charleroi", (4.34, 50.34, 4.52, 50.50)
    SECTORS = Path("data/charleroi_sectors.geojson")
    NAMES = Path("data/charleroi_sector_names.csv")
    INCOME = Path("data/charleroi_income.csv")
    PARKS = Path("data/perimeters/parks_charleroi.geojson")
    DEFAULT_DISTRICT = "Charleroi"
