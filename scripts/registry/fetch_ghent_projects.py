#!/usr/bin/env python3
"""
Реестр проектов Гента: снимок, кандидаты в предрегистрацию, сигнал «работы начались».

Источник
────────
Город публикует собственный реестр пространственных проектов — `stadsvernieuwing-projecten-gent`
на data.stad.gent (тот же слой — `SG-E-Infrastructuur:Stadsvernieuwing_projecten` на geo.gent.be):
359 записей, у каждой полигон, нарисованный городом, и статус («In voorbereiding», «In uitvoering»,
«Recent uitgevoerd», «Gearchiveerd»). Это ступень 2 правила следа — геометрия заказчика, как `mapShapes`
у Beliris. Рядом — `parken-gent` парковой службы (186 парков, статус «gepland» / «in uitvoering» /
«uitgevoerd»). Лицензия обоих — Modellicentie Gratis Hergebruik.

Чего в реестре нет: дат у зелёных проектов парковой службы (`koppelid` 13xx) — их даёт страница проекта
на stad.gent, и дату оттуда цитируют, а не выводят. `datumstart` бывает устаревшей (Tolhuispark), статус
бывает старше страницы (Slotendries); полигон — зона проекта, не всегда след (Marseillestraat включает
жильё). Истории версий Opendatasoft не хранит: снимок, который копим сами, и есть момент фиксации.

Сигнал «работы начались» — GIPOD, фламандский реестр занятий общественного пространства (открытый WFS,
без ключа). Озеленения там не найти (нет такого типа, горизонт — полгода вперёд), но любая работа
(не событие) со статусом «In uitvoering» или «Lopende», пересекающая след, значит, что на месте уже копают.
Такой кандидат печатается с этой работой; решает человек, чья это работа и трогает ли она покрытие.

Выход
─────
  data/registry/snapshots/ghent_projects_<дата>.geojson.gz, ghent_parks_<дата>.geojson.gz — снимки;
  data/registry/ghent_candidates.json — зелёные проекты «In voorbereiding» от 1 га, с площадью, датами
  реестра, статусом парка и работами GIPOD внутри следа. Это кандидаты, не записи: запись делает
  `preregister_ghent.py` после сверки со страницей проекта.

Запуск:
    .venv/bin/python scripts/registry/fetch_ghent_projects.py
"""
from __future__ import annotations

import collections
import gzip
import json
import math
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
SNAPS = ROOT / "data/registry/snapshots"
OUT = ROOT / "data/registry/ghent_candidates.json"
ODS = "https://data.stad.gent/api/explore/v2.1/catalog/datasets/{}/exports/geojson"
GIPOD = "https://geo.api.vlaanderen.be/GIPOD/wfs"
UA = {"User-Agent": "frondia-registry/0.1 (research; open data)"}
MIN_HA = 1.0                                   # меньше гектара не мерим (CLAUDE.md, граница применимости)
# «park» — только словом (wijkpark, Papiermolenpark — да; Technologiepark — нет); plein — площадь под озеленение
GREEN_WORDS = re.compile(r"\b(wijk|buurt|stads)?park\b|groen|meersen|vallei|dries\b|\bbos\b|plein|onthard|spons", re.I)
WORKS_ON = {"In uitvoering", "Lopende"}


def get(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return json.load(r)


def hectares(geom: dict) -> float:
    """Площадь в гектарах в локальной равнопромежуточной проекции: на 5 км Гента ошибка < 0,1 %."""
    lat0 = shape(geom).centroid.y
    k, r = math.cos(math.radians(lat0)), 6371008.8
    return transform(lambda x, y, z=None: (math.radians(x) * r * k, math.radians(y) * r), shape(geom)).area / 1e4


def is_green(p: dict) -> bool:
    """Зелёный проект: тема «Openbaar groen», проект парковой службы (koppelid 13xx) или слово в названии."""
    return ("Openbaar groen" in (p.get("thema") or "")
            or (p.get("koppelbron") == "ProjectenDWBW" and str(p.get("koppelid") or "").startswith("13"))
            or bool(GREEN_WORDS.search(p.get("projectnaam") or "")))


def snapshot(name: str, data: dict, today: str) -> Path:
    SNAPS.mkdir(parents=True, exist_ok=True)
    path = SNAPS / f"{name}_{today}.geojson.gz"
    with gzip.open(path, "wt") as f:
        json.dump(data, f, ensure_ascii=False)
    return path


def previous(name: str, today: str) -> dict | None:
    snaps = sorted(p for p in SNAPS.glob(f"{name}_*.geojson.gz") if p.name.split("_")[-1][:10] < today)
    return json.load(gzip.open(snaps[-1], "rt")) if snaps else None


def city_works(owner: str | None) -> bool:
    """Работа самого города (дороги, парки), а не разрешение на занятие тротуара и не сети."""
    return bool(owner) and owner.startswith("Stad Gent") and "Innames" not in owner


def works_inside(geom: dict) -> list[dict]:
    """Работы GIPOD, которые идут внутри следа сейчас. События (рынки, террасы) не считаются."""
    g = shape(geom)
    x0, y0, x1, y1 = g.bounds
    q = urllib.parse.urlencode({"service": "WFS", "version": "2.0.0", "request": "GetFeature",
                                "typeNames": "GIPOD:INNAME", "outputFormat": "application/json",
                                # долгота, широта: в порядке широта-долгота сервер молча отдаёт чужие записи
                                "srsName": "EPSG:4326", "bbox": f"{x0},{y0},{x1},{y1},EPSG:4326"})
    hits = []
    for f in get(f"{GIPOD}?{q}")["features"]:
        p = f["properties"]
        if p.get("Type") == "Evenement" or p.get("Status") not in WORKS_ON or not f.get("geometry"):
            continue
        if not shape(f["geometry"]).intersects(g):
            continue
        hits.append({"gipod": p["GipodId"], "status": p["Status"], "owner": p.get("Owner"),
                     "what": (p.get("Reference") or p.get("Description") or "").strip().splitlines()[0][:120],
                     "start": (p.get("Start") or "")[:10], "end": (p.get("End") or "")[:10]})
    return hits


def main() -> int:
    today = date.today().isoformat()
    projects = get(ODS.format("stadsvernieuwing-projecten-gent"))
    parks = get(ODS.format("parken-gent"))
    if len(projects["features"]) < 100 or len(parks["features"]) < 100:
        print(f"брак выгрузки: проектов {len(projects['features'])}, парков {len(parks['features'])}")
        return 1
    before = previous("ghent_projects", today)
    print("снимки:", snapshot("ghent_projects", projects, today).name, snapshot("ghent_parks", parks, today).name)

    # переходы статусов с прошлого снимка — событие, которое делает запись проверяемой
    if before:
        was = {f["properties"]["urid"]: f["properties"]["status"] for f in before["features"]}
        for f in projects["features"]:
            p = f["properties"]
            if p["urid"] in was and was[p["urid"]] != p["status"] and is_green(p):
                print(f"  переход: {p['projectnaam']}: {was[p['urid']]} → {p['status']}")

    park_shapes = [(shape(f["geometry"]), f["properties"]) for f in parks["features"] if f.get("geometry")]
    out = []
    for f in projects["features"]:
        p = f["properties"]
        if p.get("status") != "In voorbereiding" or not is_green(p) or not f.get("geometry"):
            continue
        ha = hectares(f["geometry"])
        if ha < MIN_HA:
            continue
        g = shape(f["geometry"])
        # парк парковой службы, который покрывает больше половины своей площади внутри зоны проекта
        park = next((pp for s, pp in park_shapes if s.intersects(g) and s.intersection(g).area > 0.5 * s.area), None)
        out.append({"urid": p["urid"], "name": p["projectnaam"], "hectares": round(ha, 2),
                    "status": p["status"], "thema": p.get("thema"), "koppel": f"{p.get('koppelbron')}:{p.get('koppelid')}",
                    "register_start": (p.get("datumstart") or "")[:10] or None,
                    "register_end": (p.get("datumeinde") or "")[:10] or None,
                    "edited": (p.get("last_edited_date") or "")[:10] or None,
                    "park": {"name": park["naam"], "status": park["status"]} if park else None,
                    "works_now": works_inside(f["geometry"]), "geometry": f["geometry"]})
    out.sort(key=lambda c: -c["hectares"])
    OUT.write_text(json.dumps({"fetched": today, "source": "data.stad.gent stadsvernieuwing-projecten-gent, parken-gent; "
                                                           "GIPOD WFS INNAME", "candidates": out},
                              ensure_ascii=False, indent=1))
    print(f"кандидатов (зелёные, In voorbereiding, ≥ {MIN_HA:g} га): {len(out)} → {OUT.relative_to(ROOT)}")
    for c in out:
        park = f" · парк «{c['park']['name']}» {c['park']['status']}" if c["park"] else ""
        dates = f" · реестр {c['register_start']}→{c['register_end']}" if c["register_start"] else ""
        print(f"  {c['hectares']:7.2f} га  {c['name']}{dates}{park}")
        # работы городских служб печатаются поимённо; разрешения на занятие (контейнеры, леса) и сети — счётом
        city = [w for w in c["works_now"] if city_works(w["owner"])]
        rest = collections.Counter(w["owner"] for w in c["works_now"] if not city_works(w["owner"]))
        for w in city:
            print(f"           ⚠ город уже работает: {w['owner']} — {w['what']} ({w['start']}→{w['end']})")
        if rest:
            print("           прочие занятия: " + ", ".join(f"{o} ×{n}" for o, n in rest.most_common()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
