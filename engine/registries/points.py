"""Линия выполнения: проверка появления объекта в НАЗВАННОЙ ЗАРАНЕЕ точке.

Зачем отдельная линия. Урны, скамейки, туалеты и фонтанчики не меняют ни NDVI,
ни запечатанность: эффект от них не измеряется ничем, и притворяться нельзя.
Но проверяется другое — выполнение: появился объект там, где его назвали, или нет.

Почему без контроля нельзя. OSM — не перепись города, а карта, которую рисуют
люди. В центральном квадрате Брюсселя урн в OSM: 53 в 2016 году, 114 в 2020,
205 сейчас. Рост втрое — это активность картографов, а не установка урн.
Поэтому появление в названной точке сравнивается с появлением в контрольных
точках, названных тогда же и в тех же условиях: если объекты появляются
одинаково часто, выполнение неотличимо от дрейфа карты.

Дисциплина ровно та же, что у предрегистрации следа:
точки называются ДО проверки, геометрия фиксируется хешем, правка = новая запись.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

REGISTRY = Path("data/registry/named_points.json")

# Типы точечных объектов, которые линия выполнения умеет проверять.
# Ключ — наш тип, значение — тег OSM, по которому объект ищется.
KINDS = {
    "waste_basket": 'amenity"="waste_basket',
    "bench": 'amenity"="bench',
    "drinking_water": 'amenity"="drinking_water',
    "toilets": 'amenity"="toilets',
    "bicycle_parking": 'amenity"="bicycle_parking',
    "defibrillator": 'emergency"="defibrillator',
    "dog_park": 'leisure"="dog_park',
    "fitness_station": 'leisure"="fitness_station',
    "playground": 'leisure"="playground',
    "shelter": 'amenity"="shelter',
    "recycling": 'amenity"="recycling',
    "bicycle_repair_station": 'amenity"="bicycle_repair_station',
    "public_bookcase": 'amenity"="public_bookcase',
    "picnic_table": 'leisure"="picnic_table',
    # Дерево — единственный тип, где сходятся обе линии: появление проверяется
    # по карте, а прижилось ли оно — по кроне через несколько сезонов. В
    # планировщике его нет намеренно: там спрос считается от точек притяжения
    # (школы, рынки, остановки), а деревья сажают там, где не хватает кроны и
    # жарко. Это другая модель спроса, и подменять её было бы враньём.
    "tree": 'natural"="tree',
}

# Соответствие типов City Planner нашим: планировщик называет объекты по-своему.
PLANNER_KINDS = {"benches": "bench", "waste_bins": "waste_basket", "toilets": "toilets",
                 "drinking_water": "drinking_water", "bike_parking": "bicycle_parking",
                 "defibrillators": "defibrillator", "dog_areas": "dog_park",
                 "fitness_stations": "fitness_station", "playgrounds": "playground",
                 "shelters": "shelter", "recycling": "recycling",
                 "bicycle_repair": "bicycle_repair_station",
                 "public_bookcases": "public_bookcase", "picnic_tables": "picnic_table"}

# Русские названия — рядом с белым списком, чтобы новый тип не попал на страницу
# английским ключом (так было: «playground / playground», «waste_basket (названа)»).
KIND_LABEL_RU = {"waste_basket": "урна", "bench": "скамейка", "toilets": "туалет",
                 "drinking_water": "питьевой фонтанчик", "bicycle_parking": "велопарковка",
                 "defibrillator": "дефибриллятор", "dog_park": "площадка для собак",
                 "fitness_station": "уличный тренажёр", "playground": "детская площадка",
                 "shelter": "навес или укрытие", "recycling": "контейнер раздельного сбора",
                 "bicycle_repair_station": "велоремонтная станция", "public_bookcase": "уличный книжный шкаф",
                 "picnic_table": "стол для пикника", "tree": "дерево"}

# Радиус, в котором объект считается «появившимся в этой точке».
# Не больше: на 50 м в плотном городе в круг попадает чужая улица.
DEFAULT_RADIUS_M = 50


def point_hash(lon: float, lat: float, radius_m: int, kind: str) -> str:
    """Хеш точки проверки. Меняется от сдвига точки, радиуса или типа объекта —
    то есть от любой правки, которой можно подогнать результат."""
    payload = json.dumps({"lon": round(lon, 6), "lat": round(lat, 6),
                          "radius_m": radius_m, "kind": kind}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class NamedPoint:
    """Точка, названная до проверки. Роль — `named` (проверяемая) либо `control`."""

    id: str
    city: str
    unit_id: str
    kind: str
    lon: float
    lat: float
    radius_m: int
    role: str                 # named | control
    rule: str                 # правило, по которому точка выбрана — словами
    expectation: str          # что мы ожидаем увидеть, записано ДО проверки
    registered_at: str
    point_hash: str = ""
    source: str = ""
    note: str = ""

    def validate(self) -> list[str]:
        problems = []
        if self.kind not in KINDS:
            problems.append(f"тип {self.kind} не поддерживается линией выполнения")
        if self.role not in ("named", "control"):
            problems.append(f"роль {self.role} неизвестна: только named или control")
        if not self.rule.strip():
            problems.append("правило выбора точки не записано — точку нельзя защитить")
        if not self.expectation.strip():
            problems.append("ожидание не записано до проверки")
        if self.radius_m <= 0 or self.radius_m > 150:
            problems.append(f"радиус {self.radius_m} м вне допустимого: 1–150")
        h = point_hash(self.lon, self.lat, self.radius_m, self.kind)
        if self.point_hash and self.point_hash != h:
            problems.append("хеш не сходится с координатами: точку двигали после регистрации")
        return problems


def register(id: str, city: str, unit_id: str, kind: str, lon: float, lat: float,
             rule: str, expectation: str, role: str = "named",
             radius_m: int = DEFAULT_RADIUS_M, registered_at: str | None = None,
             source: str = "", note: str = "") -> NamedPoint:
    """Создать запись. Отказывает, если запись нечем защитить."""
    p = NamedPoint(id=id, city=city, unit_id=unit_id, kind=kind, lon=lon, lat=lat,
                   radius_m=radius_m, role=role, rule=rule, expectation=expectation,
                   registered_at=registered_at or date.today().isoformat(),
                   point_hash=point_hash(lon, lat, radius_m, kind), source=source, note=note)
    problems = p.validate()
    if problems:
        raise ValueError("точка не защитима: " + "; ".join(problems))
    return p


@dataclass
class AppearanceResult:
    """Итог проверки одного набора точек за период. Числа — доли, а не «выросло»."""

    kind: str
    date_before: str
    date_after: str
    named_total: int = 0
    named_appeared: int = 0
    control_total: int = 0
    control_appeared: int = 0
    detail: list[dict] = field(default_factory=list)
    # the city's own register (scripts/registry/object_registers.py): points taken out because an object already stood
    # within their radius, and how many of each group had a map gap within 500 m (None where it was not counted)
    excluded: list[str] = field(default_factory=list)
    gap_named: int | None = None
    gap_control: int | None = None

    @property
    def named_rate(self) -> float | None:
        return self.named_appeared / self.named_total if self.named_total else None

    @property
    def control_rate(self) -> float | None:
        return self.control_appeared / self.control_total if self.control_total else None

    @property
    def lift(self) -> float | None:
        """Разность долей: сколько появлений сверх дрейфа карты."""
        if self.named_rate is None or self.control_rate is None:
            return None
        return self.named_rate - self.control_rate

    def verdict(self, min_points: int = 20) -> str:
        """Вердикт по тем же принципам, что у линии эффекта: мало данных — отказ."""
        if self.named_total < min_points or self.control_total < min_points:
            return (f"отказ: точек мало ({self.named_total} названных, {self.control_total} контрольных, "
                    f"нужно по {min_points}) — доля считается, вердикт нет")
        if self.lift is None:
            return "отказ: доли не посчитаны"
        if self.named_appeared == 0 and self.control_appeared == 0:
            # Вырожденный случай первого прогона: точки отбирались как пустые
            # на дату регистрации, поэтому нулевые доли подтверждают отбор,
            # а не говорят что-либо о выполнении. Называть это «неотличимо
            # от дрейфа» было бы подменой: сравнивать пока нечего.
            return ("база: ни одного появления ни в названных, ни в контрольных точках — "
                    "отбор подтверждён, проверка выполнения возможна только в следующие сезоны")
        v = "выполнение не отличается от дрейфа карты" if self.lift <= 0 else f"появлений сверх дрейфа: {self.lift:+.0%}"
        return v + self.gap_caution()

    def gap_caution(self) -> str:
        """Правило, записанное 27.09.2026 до первой проверки: если у названных и контрольных точек доля «пробела
        карты» в 500 м (объект по реестру города, которого OSM планировщика не знал) различается на 20 пунктов и
        больше, картографы будут догонять город у одной группы чаще — вердикт получает оговорку, а не молчит."""
        if self.gap_named is None or self.gap_control is None or not self.named_total or not self.control_total:
            return ""
        d = self.gap_named / self.named_total - self.gap_control / self.control_total
        if abs(d) < 0.20:
            return ""
        return (f" — оговорка: пробел карты у названных {self.gap_named}/{self.named_total}, у контрольных "
                f"{self.gap_control}/{self.control_total}; появление у группы с бóльшим пробелом может быть картографией")


def load(path: Path = REGISTRY) -> list[NamedPoint]:
    if not path.exists():
        return []
    return [NamedPoint(**r) for r in json.loads(path.read_text())]


def save(points: list[NamedPoint], path: Path = REGISTRY) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(p) for p in points], ensure_ascii=False, indent=1))


def append(point: NamedPoint, path: Path = REGISTRY) -> list[NamedPoint]:
    pts = load(path)
    if any(p.id == point.id for p in pts):
        raise ValueError(f"точка {point.id} уже зарегистрирована: правка — это новая запись")
    pts.append(point)
    save(pts, path)
    return pts
