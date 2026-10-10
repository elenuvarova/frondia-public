from .base import CityAdapter
from .paris import ParisAdapter
from .antwerp import AntwerpAdapter
from .london import LondonAdapter
from .brussels import BrusselsAdapter
from .ghent import GhentAdapter
from .liege import LiegeAdapter
from .charleroi import CharleroiAdapter

_REGISTRY: dict[str, type[CityAdapter]] = {
    "paris":   ParisAdapter,
    "antwerp": AntwerpAdapter,
    "london":  LondonAdapter,
    "brussels": BrusselsAdapter,
    "ghent": GhentAdapter,
    "liege": LiegeAdapter,
    "charleroi": CharleroiAdapter,
}


def get_adapter(city: str) -> CityAdapter:
    cls = _REGISTRY.get(city)
    if cls is None:
        raise ValueError(
            f"No adapter for city '{city}'. Available: {list(_REGISTRY)}"
        )
    return cls()
