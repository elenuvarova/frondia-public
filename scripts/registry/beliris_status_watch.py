#!/usr/bin/env python3
"""Сверка статусов Beliris: что сдвинулось с прошлого снимка.

Зачем. Предрегистрация следа имеет смысл, только если мы узнаём о начале работ.
Beliris публикует статус проекта (`en_projet` → `en_execution` → `termine`), и
переход — ровно то событие, которое делает запись проверяемой:

  · предрегистрированный проект перешёл в `en_execution` — запись опередила
    работы, это надо зафиксировать датой обнаружения (дату начала работ Beliris
    не публикует; дата снимка — верхняя граница);
  · любой проект перешёл в `termine` — новый кандидат в аудит с окнами под проект.

Каждый прогон сохраняет снимок в `data/registry/snapshots/` и сравнивает с
предыдущим. Ничего не перезаписывает: основной реестр `beliris_projects.json`
остаётся тем, на чём посчитаны опубликованные страницы.

Первая сверка, 24.09.2026, через три недели после регистрации: переходов два,
оба не о зелени (пожарная часть, велоулица). Ни один из шести
предрегистрированных проектов не начался — записи ждут.

    .venv/bin/python scripts/registry/beliris_status_watch.py
"""
from __future__ import annotations

import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

AJAX = ("https://www.beliris.be/beliris/ajax/projects.php?language=FR"
        "&filterStatus%5B%5D=en_projet&filterStatus%5B%5D=en_execution"
        "&filterStatus%5B%5D=termine&filterCommune=&page_alias=")
SNAPS = Path("data/registry/snapshots")
BASE = Path("data/registry/beliris_projects.json")          # снимок, на котором посчитан реестр
PREREG = Path("data/registry/preregistered.json")


def fetch() -> list[dict]:
    req = urllib.request.Request(AJAX, headers={"User-Agent": "map-project-research/0.1"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())["projects"]


def previous_snapshot(today: str) -> Path:
    older = sorted(p for p in SNAPS.glob("beliris_projects_*.json") if p.stem.split("_")[-1] < today)
    return older[-1] if older else BASE


def main() -> int:
    today = date.today().isoformat()
    now = fetch()
    SNAPS.mkdir(parents=True, exist_ok=True)
    snap = SNAPS / f"beliris_projects_{today}.json"
    prev_path = previous_snapshot(today)
    old = json.loads(prev_path.read_text())
    snap.write_text(json.dumps(now, ensure_ascii=False, indent=1))

    O = {p["url"]: p for p in old}
    N = {p["url"]: p for p in now}
    print(f"сравнение {prev_path.name} → {snap.name}: было {len(O)}, стало {len(N)}")

    moves = [(O[u], N[u]) for u in N if u in O and O[u]["project_status"] != N[u]["project_status"]]
    print(f"переходов статуса: {len(moves)}")
    for a, b in moves:
        print(f"  {a['project_status']} → {b['project_status']} · {b['domaine']:<10} · {b['cleanTitle'] or b['title']}")
    for u in N.keys() - O.keys():
        print(f"  новый · {N[u]['project_status']} · {N[u]['cleanTitle'] or N[u]['title']}")
    for u in O.keys() - N.keys():
        print(f"  исчез · {O[u]['project_status']} · {O[u]['cleanTitle'] or O[u]['title']}")

    # предрегистрированные — отдельно, потому что ради них сверка и существует
    started, waiting = [], []
    for rec in json.loads(PREREG.read_text()) if PREREG.exists() else []:
        url = rec.get("signal_source", "").removeprefix("beliris:")
        p = N.get(url)
        status = p["project_status"] if p else "нет в списке"
        (started if status in ("en_execution", "termine") else waiting).append((rec, status))
    print(f"\nпредрегистрированных: {len(started) + len(waiting)} · начались {len(started)} · ждут {len(waiting)}")
    for rec, status in started:
        print(f"  ⚑ {rec['name'][:60]} — {status}, обнаружено {today}: запись от {rec['registered_at']} "
              f"опередила работы, дату начала взять из документов")
    for rec, status in waiting:
        print(f"  · {rec['name'][:60]} — {status}")

    done = [b for a, b in moves if b["project_status"] == "termine"]
    if done:
        print(f"\nновые завершённые — кандидаты в аудит с окнами под проект: {len(done)}")
        for b in done:
            print(f"  {b['domaine']:<10} {b['cleanTitle'] or b['title']}")
    print(f"→ {snap}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
