"""
Brussels-Capital Region adapter.

Sources:
  - Assets + POIs: OpenStreetMap via OSMnx (no single authoritative regional API
    for street furniture; Brussels Open Data publishes per-commune, not region-wide).
  - Deprivation: Statbel BIMD 2011 at statistical-sector level — the same nationwide
    source used for Antwerp, filtered to the 19 Brussels communes (NIS 21001–21019).
"""

from __future__ import annotations

import geopandas as gpd

from .base import CityAdapter


class BrusselsAdapter(CityAdapter):
    def __init__(self):
        from ..config import CITIES
        cfg = CITIES["brussels"]
        super().__init__("brussels", cfg["crs"], cfg["osm_place"])

    def load_assets(
        self, asset_type: str, city_boundary_wgs: gpd.GeoDataFrame | None = None
    ) -> gpd.GeoDataFrame:
        return self._osm_assets(city_boundary_wgs, asset_type)
