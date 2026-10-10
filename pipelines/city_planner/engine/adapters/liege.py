"""
Liège adapter (added 26 Sep 2026 for Frondia, map_project).

Sources:
  - Assets + POIs: OpenStreetMap via OSMnx, as for Brussels and Ghent.
  - Deprivation: Statbel BIMD 2011 at statistical-sector level, the same nationwide source used for
    Antwerp, Brussels and Ghent, filtered to the municipality of Liège (NIS 62063).
"""

from __future__ import annotations

import geopandas as gpd

from .base import CityAdapter


class LiegeAdapter(CityAdapter):
    def __init__(self):
        from ..config import CITIES
        cfg = CITIES["liege"]
        super().__init__("liege", cfg["crs"], cfg["osm_place"])

    def load_assets(
        self, asset_type: str, city_boundary_wgs: gpd.GeoDataFrame | None = None
    ) -> gpd.GeoDataFrame:
        return self._osm_assets(city_boundary_wgs, asset_type)
