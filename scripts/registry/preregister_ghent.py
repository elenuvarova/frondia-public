"""Первые записи предрегистрации Гента — из собственного реестра проектов города.

Источник — снимок `fetch_ghent_projects.py` (data.stad.gent: `stadsvernieuwing-projecten-gent` и
`parken-gent`). След — полигон города (ступень 2 правила следа): у парка — полигон парковой службы,
у зелёной зоны — полигон проекта. Статус «In voorbereiding» сверен со страницей проекта или с
документом (разрешение Omgevingsloket), и перед записью ещё раз проверяется, что городские службы
не работают внутри следа (GIPOD). Каждая запись несёт ОЖИДАЕМЫЙ исход, записанный до измерения.

Кого не записали 27.09.2026 и почему (запись нельзя править, поэтому сомнительное не пишется):
  · Witte Kaproenenpark (3,4 га, работы в 2027) — весной 2024 внутри следа снесены два здания,
    база 2023–25 захватывает снос; с 07.09.2026 там же идут работы FARYS.
  · Gentbrugse Meersen, северная часть (71 га, с 2028) — в следе с ноября 2022 сажают лес: база сама
    движется; полигон — зона, а не северная часть.
  · Groengebied Oude Bareel (9,7 га) — часть засажена в декабре 2023; сроков нет.
  · Citadelpark, «ondergrondse spons» (26 га) — внутри идёт «herwaardering Citadelpark» (22 га).
  · Groengebied Slotendries (15 га) — страница говорит «In uitvoering», реестр отстал.
  · Noendries (1,4 га) — дорожная служба города работает в следе с 31.05.2026 (GIPOD); страница — «In uitvoering».
  · Henri Storyplein (5,6 га) — перенос поля долгосрочный, место не выбрано, денег нет.
  · Marseillestraat (8,7 га) — зона включает жильё; контур парка покажут 07.10.2026 — записать тогда.

Запуск (после fetch_ghent_projects.py в тот же день):
    .venv/bin/python scripts/registry/preregister_ghent.py  → data/registry/preregistered.json
"""
from __future__ import annotations

import gzip
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine.registries.preregistration import register, load, append
from fetch_ghent_projects import SNAPS, city_works, hectares, works_inside

PAGE = "https://stad.gent/nl/plannen-en-projecten/"

# Что записываем. Слова статуса и сроков — цитаты со страниц и из документов, не выводы.
RECORDS = [
    {
        "name": "Papiermolenpark",
        "layer": "ghent_parks", "match": ("naam", "Papiermolenpark"), "status": ("status", "gepland"),
        "signal_source": (f"stad.gent:{PAGE}project-inrichting-nieuw-wijkpark-papiermolenpark "
                          "(страница закрыта 403; копия Wayback 14.11.2025: «In voorbereiding», "
                          "«2025-2030 Ontwerp en uitvoering», «Een concrete timing … kunnen we momenteel niet geven»)"),
        "intervention_type": "park_creation",
        "note": ("ожидание: trees вверх по мере роста посадок («meer natuur, bos en groen»); NDVI в шуме или сначала "
                 "вниз — молодая посадка на лугу может мериться как потеря (Geboortebos); built чуть вверх (дорожки, "
                 "площадки). След — полигон парковой службы со статусом «gepland»; зона проекта шире (10,3 га). "
                 "Велодорожка через участок уже построена («intussen afgewerkt», дата не названа) — база 2023–25 "
                 "могла её захватить. Сроков работ город не называет."),
    },
    {
        "name": "Groenrealisatie Rosdambeekvallei",
        "layer": "ghent_projects", "match": ("projectnaam", "Project Groenrealisatie Rosdambeekvallei"),
        "status": ("status", "In voorbereiding"),
        "signal_source": ("stad.gent:data.stad.gent stadsvernieuwing-projecten-gent «Project Groenrealisatie "
                          "Rosdambeekvallei», In voorbereiding; omgevingsvergunning 2026058579 (Stad Gent, «Verwijderen "
                          "van vrijstaande gebouwen», ingediend 15.06.2026, vergund 20.08.2026)"),
        "intervention_type": "green_realisation",
        "note": ("ожидание: built вниз на участках сноса, остальная долина — в шуме по NDVI. След — зона проекта "
                 "(20 га), снос занимает её малую часть, поэтому эффект на всём следе может утонуть: это граница "
                 "применимости, печатать «в шуме», не провал. Страницы проекта нет, сроков нет. GIPOD видит только "
                 "общественное пространство — снос на участках туда не попадёт; начало работ ловить по снимкам "
                 "реестра и по разрешениям."),
    },
]


def latest(layer: str) -> tuple[dict, str]:
    snaps = sorted(SNAPS.glob(f"{layer}_*.geojson.gz"))
    if not snaps:
        raise SystemExit(f"нет снимка {layer}: сначала fetch_ghent_projects.py")
    return json.load(gzip.open(snaps[-1], "rt")), snaps[-1].name.split("_")[-1][:10]


def main() -> int:
    today = date.today().isoformat()
    have = {(r.city, r.geometry_hash) for r in load()}
    for spec in RECORDS:
        data, snap_day = latest(spec["layer"])
        if snap_day != today:
            print(f"снимок {spec['layer']} от {snap_day}, не сегодняшний: статус мог уйти — сначала fetch_ghent_projects.py")
            return 1
        key, value = spec["match"]
        f = next((f for f in data["features"] if f["properties"].get(key) == value), None)
        if f is None:
            print(f"  ✗ {spec['name']}: нет в снимке {spec['layer']}")
            continue
        p = f["properties"]
        skey, sval = spec["status"]
        if p.get(skey) != sval:
            print(f"  ✗ {spec['name']}: статус «{p.get(skey)}», а записывать можно только «{sval}» — отказ")
            continue
        busy = [w for w in works_inside(f["geometry"]) if city_works(w["owner"])]
        if busy:
            print(f"  ✗ {spec['name']}: город уже работает в следе — {busy[0]['owner']}, {busy[0]['what']} — отказ")
            continue
        layer = "parken-gent" if spec["layer"] == "ghent_parks" else "stadsvernieuwing-projecten-gent"
        rec = register(name=spec["name"], city="ghent", geometry=f["geometry"],
                       geometry_source=f"stad.gent:{layer}/{p['urid']}", signal_source=spec["signal_source"],
                       intervention_type=spec["intervention_type"], note=spec["note"], registered_at=today)
        if ("ghent", rec.geometry_hash) in have:
            print(f"  · {spec['name']}: уже записан с этой геометрией")
            continue
        append(rec)
        print(f"  ✓ {spec['name']}: {hectares(f['geometry']):.2f} га, {rec.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
