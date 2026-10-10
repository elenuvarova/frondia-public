"""
Ghent adapter (added 26 Sep 2026 for Frondia, map_project).

Sources:
  - Assets + POIs: OpenStreetMap via OSMnx, as for Brussels.
  - Deprivation: Statbel BIMD 2011 at statistical-sector level, the same nationwide source used for
    Antwerp and Brussels, filtered to the municipality of Ghent (NIS 44021).
"""

from __future__ import annotations

import geopandas as gpd

from .base import CityAdapter


class GhentAdapter(CityAdapter):
    def __init__(self):
        from ..config import CITIES
        cfg = CITIES["ghent"]
        super().__init__("ghent", cfg["crs"], cfg["osm_place"])

    def load_assets(
        self, asset_type: str, city_boundary_wgs: gpd.GeoDataFrame | None = None
    ) -> gpd.GeoDataFrame:
        return self._osm_assets(city_boundary_wgs, asset_type)
