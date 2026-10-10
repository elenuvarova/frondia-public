"""
Предрегистрация следа вмешательства — контракт, к которому подключится tender-radar.

Зачем
─────
Главное возражение к любому аудиту: «вы обвели полигон там, где позеленело».
Оно снимается только одним способом: полигон зафиксирован и датирован ДО начала
работ, а число посчитано после. Это дисциплина углеродного MRV (TREEO, veritree),
перенесённая к муниципалитетам. В США USDA требует того же от грантополучателей:
инвентаризация до возмещения.

Откуда приходит сигнал «работы начнутся»
────────────────────────────────────────
`uk-eu-tender-radar` ингестит EU TED / OCDS — объявления о закупках. Тендер на
переустройство площади выходит за месяцы до работ. Это и есть момент фиксации.

⚠️ На 2026-09-02 tender-radar в Phase 0: каркас и модель данных есть, ингест
не написан. Поэтому здесь определён КОНТРАКТ записи, а не подключение. Правило
проекта: сначала формат, потом код. Запись можно создавать и вручную — из
страницы Beliris, из контракта, из письма коммуны — лишь бы дата фиксации
предшествовала дате начала работ.

Что делает запись защитимой
───────────────────────────
  · геометрия ЧУЖАЯ или зафиксированная: OSM id, полигон коммуны, либо обводка
    с хешем и датой;
  · `registered_at` строго раньше `works_start` — проверяется кодом;
  · источник сигнала назван: номер тендера, URL проекта, документ;
  · после регистрации геометрия НЕ меняется — любое изменение = новая запись.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path

REGISTRY = Path("data/registry/preregistered.json")


def geometry_hash(geom: dict) -> str:
    """Отпечаток геометрии: доказательство, что полигон не менялся после фиксации."""
    canon = json.dumps(geom, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class Preregistration:
    """Одна зафиксированная запись. Неизменяема по построению."""

    id: str
    name: str
    city: str
    geometry: dict
    geometry_hash: str
    geometry_source: str          # "osm:way/123", "commune:pdf", "manual"
    registered_at: str            # ISO-дата фиксации
    works_start: str | None       # ожидаемое начало работ, ISO
    signal_source: str            # "ted:2026/S 123-456789", "beliris:url", "contract:90"
    intervention_type: str        # "park_creation", "square_depaving", "restoration", ...
    expected_checks: tuple[str, ...] = ("coverage",)   # + "appearance" для мебели
    note: str = ""

    def validate(self) -> list[str]:
        """Что нарушено. Пустой список — запись защитима."""
        problems = []
        if geometry_hash(self.geometry) != self.geometry_hash:
            problems.append("геометрия изменена после фиксации")
        if self.works_start and self.registered_at >= self.works_start:
            problems.append(
                f"фиксация {self.registered_at} не раньше начала работ {self.works_start}: "
                "предрегистрация не состоялась")
        if not self.signal_source:
            problems.append("не назван источник сигнала о вмешательстве")
        if self.geometry_source == "manual" and not self.note:
            problems.append("ручная обводка без пояснения, кто и почему")
        return problems

    @property
    def defensible(self) -> bool:
        return not self.validate()


def register(name: str, city: str, geometry: dict, geometry_source: str,
             signal_source: str, intervention_type: str,
             works_start: str | None = None,
             expected_checks: tuple[str, ...] = ("coverage",),
             note: str = "", registered_at: str | None = None) -> Preregistration:
    """Создать запись. Дата фиксации — сегодня, если не передана явно."""
    today = registered_at or date.today().isoformat()
    h = geometry_hash(geometry)
    rec = Preregistration(
        id=f"pre_{today}_{h}",
        name=name, city=city, geometry=geometry, geometry_hash=h,
        geometry_source=geometry_source, registered_at=today,
        works_start=works_start, signal_source=signal_source,
        intervention_type=intervention_type, expected_checks=expected_checks,
        note=note,
    )
    problems = rec.validate()
    if problems:
        raise ValueError("запись не защитима: " + "; ".join(problems))
    return rec


def load(path: Path = REGISTRY) -> list[Preregistration]:
    if not path.exists():
        return []
    return [Preregistration(**r) for r in json.loads(path.read_text())]


def save(records: list[Preregistration], path: Path = REGISTRY) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(r) for r in records],
                               ensure_ascii=False, indent=1))
    return path


def append(rec: Preregistration, path: Path = REGISTRY) -> Path:
    """Только добавление. Правка существующей записи запрещена по смыслу."""
    records = load(path)
    if any(r.id == rec.id for r in records):
        raise ValueError(f"запись {rec.id} уже есть: изменение = новая запись")
    records.append(rec)
    return save(records, path)


# ── досье записи: запись + база «до» + контроль, всё привязано к хешу ─────────

BASELINE_CSV = Path("data/registry/preregistered_baseline.csv")
CONTROLS_JSON = Path("data/registry/preregistered_controls.json")


@dataclass(frozen=True)
class Dossier:
    """Всё, что было зафиксировано до работ. Будущий аудит читает отсюда и ничего
    не пересчитывает по окну, которое можно подобрать под результат."""

    record: Preregistration
    baseline: dict            # прибор → {"value", "scenes", "window"}
    control: dict | None      # {"comparable", "gap", "control_ids", "control_names", "window"}

    def validate(self) -> list[str]:
        problems = self.record.validate()
        for name, b in self.baseline.items():
            if b.get("geometry_hash") not in (None, self.record.geometry_hash):
                problems.append(f"база «до» по {name} снята с другой геометрии")
        if self.control and self.control.get("geometry_hash") not in (None, self.record.geometry_hash):
            problems.append("контроль назван для другой геометрии")
        return problems


def load_dossier(rec_id: str, registry: Path = REGISTRY,
                 baseline_csv: Path = BASELINE_CSV,
                 controls_json: Path = CONTROLS_JSON) -> Dossier:
    import csv
    rec = next((r for r in load(registry) if r.id == rec_id), None)
    if rec is None:
        raise KeyError(f"записи {rec_id} нет в реестре")
    baseline = {}
    if baseline_csv.exists():
        for row in csv.DictReader(baseline_csv.open()):
            if row["id"] == rec_id:
                baseline[row["instrument"]] = {
                    "value": float(row["value"]) if row["value"] not in ("", "None") else None,
                    "scenes": int(row["scenes"]) if row.get("scenes") not in ("", "None", None) else None,
                    "window": row["window"], "geometry_hash": row["geometry_hash"]}
    control = None
    if controls_json.exists():
        control = next((c for c in json.loads(controls_json.read_text()) if c["id"] == rec_id), None)
    return Dossier(rec, baseline, control)
