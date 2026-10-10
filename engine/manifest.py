"""
Манифест городского пакета.

Зачем он существует
───────────────────
Правило продукта: у любого числа виден источник. Манифест — техническое
воплощение этого правила. Слой без записи в манифесте в отчёт не попадает,
и это проверяется кодом, а не дисциплиной.

Что обязан объявить каждый слой: что меряет, каким методом, из какого источника,
когда посчитан, с каким порогом значимости, откуда взят порог и чего он НЕ умеет.
Последнее так же обязательно, как первое: инструмент, не перечисляющий своих
границ, продаёт впечатление, а не измерение.

Устройство пакета (см. `docs/03-architecture.md`):

    cities/<city>/
      units.geojson          — единицы решения
      layers/<layer>.csv     — значения на единицу
      points/<asset>.geojson — точечные объекты и кандидаты
      manifest.json          — ЧТО, КАК и ОТКУДА
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path

from .config import CITIES, LIMITS, WINDOWS


@dataclass
class LayerEntry:
    """Запись о слое. Без неё слой не публикуется."""

    layer: str
    measures: str
    unit: str
    method: str
    source: str
    computed: str
    threshold: float | None = None
    threshold_source: str | None = None
    limits: list[str] = field(default_factory=list)
    n_units: int | None = None

    def validate(self) -> list[str]:
        """Чего не хватает, чтобы слой можно было печатать в отчёте."""
        missing = []
        for f in ("measures", "method", "source", "computed"):
            if not getattr(self, f):
                missing.append(f)
        if self.threshold is not None and not self.threshold_source:
            missing.append("threshold_source: порог без происхождения недопустим")
        return missing


class Manifest:
    """Манифест одного города."""

    def __init__(self, city: str):
        if city not in CITIES:
            raise ValueError(f"город {city!r} не описан в config.CITIES")
        self.city = city
        self.layers: dict[str, LayerEntry] = {}

    def add(self, entry: LayerEntry) -> "Manifest":
        problems = entry.validate()
        if problems:
            raise ValueError(
                f"слой {entry.layer!r} нельзя опубликовать, не хватает: "
                + ", ".join(problems))
        self.layers[entry.layer] = entry
        return self

    def from_instrument(self, instrument, method: str, threshold: float | None,
                        threshold_source: str | None, n_units: int | None = None,
                        computed: str | None = None) -> "Manifest":
        """Собрать запись из прибора — прибор уже знает про себя всё нужное."""
        return self.add(LayerEntry(
            layer=instrument.name,
            measures=instrument.measures,
            unit=instrument.unit,
            method=method,
            source=instrument.source,
            computed=computed or date.today().isoformat(),
            threshold=threshold,
            threshold_source=threshold_source,
            limits=list(instrument.limits),
            n_units=n_units,
        ))

    def publishable(self, layer: str) -> bool:
        """Можно ли печатать число этого слоя в отчёте."""
        return layer in self.layers

    def to_dict(self) -> dict:
        cfg = CITIES[self.city]
        return {
            "city": self.city,
            "display_name": cfg["display_name"],
            "crs": cfg["crs"],
            "units": cfg["units"],
            "windows": WINDOWS,
            "generated": date.today().isoformat(),
            "layers": {k: asdict(v) for k, v in self.layers.items()},
            # Границы применимости всего движка, не отдельного слоя.
            # Печатаются в каждом отчёте рядом с числами.
            "engine_limits": LIMITS,
        }

    def write(self, root: str | Path = "cities") -> Path:
        path = Path(root) / self.city / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=1))
        return path

    @classmethod
    def read(cls, city: str, root: str | Path = "cities") -> "Manifest":
        data = json.loads((Path(root) / city / "manifest.json").read_text())
        m = cls(city)
        for k, v in data.get("layers", {}).items():
            m.layers[k] = LayerEntry(**v)
        return m
