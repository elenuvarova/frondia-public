#!/usr/bin/env python3
"""
Индекс скриптов — строится из докстрингов, а не пишется руками.

Первая строка докстринга каждого скрипта — его назначение. Скрипты без
докстринга помечаются. Прототипы (Брюссель-only, до движка) — отдельной группой.

Запуск:  python3 scripts/index_scripts.py  →  scripts/README.md
"""
from __future__ import annotations
import ast, re
from pathlib import Path

PROTOTYPES = {"retro_audit.py", "retro_audit_matched.py", "placebo_band.py", "audit_parks_batch.py",
              "audit_one_park.py", "dynamic_world_check.py", "diagnose_green_decline.py",
              "equity_of_greening.py", "calibrate_dynamic_world.py"}
GROUPS = {"gee": "Прогоны Earth Engine", "official": "Официальные слои ЕС: расчёт по методике Комиссии",
          "registry": "Реестры: сбор и связи", "report": "Генераторы страниц и дел",
          "site": "Английский сайт (site/): поле и данные",
          "design": "Дизайн: замеры референсов для досок Figma"}


def purpose(p: Path) -> str:
    try:
        doc = ast.get_docstring(ast.parse(p.read_text(encoding="utf-8"))) or ""
    except SyntaxError:
        return "(не разбирается)"
    first = next((l.strip() for l in doc.splitlines() if l.strip()), "")
    return first.rstrip(".") or "(без докстринга)"


def main() -> int:
    root = Path("scripts"); out = ["# Скрипты\n", "Индекс собран из докстрингов (`python3 scripts/index_scripts.py`). "
           "Живые скрипты работают через `engine/` и параметризованы по городу; прототипы — "
           "Брюссель-only, оставлены как история метода и для регрессий.\n"]
    for g, title in GROUPS.items():
        live, proto = [], []
        for p in sorted((root / g).glob("*.py")):
            (proto if p.name in PROTOTYPES else live).append(p)
        out.append(f"\n## {title}\n")
        for p in live:
            out.append(f"- `{g}/{p.name}` — {purpose(p)}")
        if proto:
            out.append("\n<details><summary>прототипы (до движка, только Брюссель)</summary>\n")
            for p in proto:
                out.append(f"- `{g}/{p.name}` — {purpose(p)}")
            out.append("\n</details>")
    out.append("\n## Прочее\n- `index_scripts.py` — этот индекс\n")
    (root / "README.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    n = sum(1 for g in GROUPS for _ in (root / g).glob("*.py"))
    print(f"→ scripts/README.md · скриптов: {n}, из них прототипов: {sum(1 for g in GROUPS for p in (root/g).glob('*.py') if p.name in PROTOTYPES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
