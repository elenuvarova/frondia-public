"""Адаптеры городов. Город знает, откуда брать свои единицы и следы работ."""

from .base import CityAdapter, Unit, area_ha_of, centroid_of, dist_m  # noqa: F401
from .brussels import BrusselsAdapter  # noqa: F401
from .antwerp import AntwerpAdapter  # noqa: F401
from .ghent import GhentAdapter  # noqa: F401
from .liege import LiegeAdapter  # noqa: F401
from .charleroi import CharleroiAdapter  # noqa: F401

ADAPTERS = {"brussels": BrusselsAdapter, "antwerp": AntwerpAdapter, "ghent": GhentAdapter,
            "liege": LiegeAdapter, "charleroi": CharleroiAdapter}

__all__ = ["CityAdapter", "Unit", "BrusselsAdapter", "AntwerpAdapter", "GhentAdapter", "ADAPTERS",
           "area_ha_of", "centroid_of", "dist_m"]
