#!/usr/bin/env python3
"""
Извлечение ПЛАНИРУЕМЫХ мер по озеленению из описаний квартальных контрактов.

Задача, которую это решает
──────────────────────────
Голый поиск по ключевым словам не отличает состояние от действия. Peterbos попал
в выборку «озеленение» по фразе «dégagements … verdurisés», которая описывает,
что участок УЖЕ зелёный, а не что его озеленят. Для реестра это разные вещи.

Как отличаем
────────────
Работаем по предложениям. Мера засчитывается, только если в одном предложении
есть И термин озеленения, И проспективный маркер французского языка — будущее
время либо оборот намерения («prévoit», «sera», «vise à», «création de»).
Прошедшее время и описательные обороты («est verdurisé», «constitué de») —
признак состояния, а не плана.

Каждая найденная мера сохраняется ВМЕСТЕ С ЦИТАТОЙ, из которой извлечена, —
это требование прослеживаемости: любое утверждение в досье должно вести к
источнику.

Это детерминированная базовая линия. Её результат вычитывается вручную, разница
даёт измеренную точность — тот же принцип eval-набора, что и для LLM.

Запуск:
    .venv/bin/python scripts/registry/extract_greening.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

IN_RAW = Path("data/registry/contracts_raw.json")
OUT = Path("data/registry/greening_baseline.json")

# Термины озеленения. Ловим корни, чтобы покрыть словоформы.
GREEN_TERMS = [
    "verdurisation", "verduris", "végétalis", "vegetalis", "verdiss",
    "déminéralis", "demineralis",
    "plantation", "planter", "arbre", "arbust",
    "espace vert", "espaces verts", "maillage vert",
    "parc", "jardin", "potager", "agroécolog", "agroecolog",
    "noue", "perméabilis", "permeabilis",
]

# Проспективные маркеры: намерение или будущее.
PROSPECTIVE = [
    r"\bprévoi\w*", r"\bprévu\w*", r"\bvise\w*\s+à", r"\bvisera\w*",
    r"\bsera\b", r"\bseront\b", r"\bpermettra\b", r"\bpermettront\b",
    r"\bcréation\b", r"\bcréer\b", r"\bcréé\w*\b",
    r"\baménagement\b", r"\bréaménag\w*", r"\baménager\b",
    r"\bprogramme\s+(?:vise|prévoit|comprend)", r"\bobjectif\b",
    r"\bprojet\s+de\b", r"\bdévelopper\b", r"\bdéveloppera\b",
    r"\brenforcer\b", r"\baugmenter\b", r"\bimplant\w*",
    r"\bfutur\w*", r"\bnouveau\b", r"\bnouvelle\b",
    r"\btransform\w*", r"\brequalif\w*", r"\brénov\w*",
]

# Маркеры описания состояния — если есть они и нет проспективных, это не мера.
STATIVE = [
    r"\best\s+\w*verduris", r"\bsont\s+\w*verduris",
    r"\bconstitué\w*\b", r"\bcaractéris\w*", r"\bse\s+trouve\b",
    r"\bon\s+retrouve\b", r"\bon\s+trouve\b", r"\bcomporte\b",
    r"\bexistant\w*\b", r"\bactuel\w*\b",
]

PROSPECTIVE_RE = re.compile("|".join(PROSPECTIVE), re.I)
STATIVE_RE = re.compile("|".join(STATIVE), re.I)


def sentences(text: str) -> list[str]:
    """Грубое деление на предложения — достаточное для этой задачи."""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Þ])", text)
    return [p.strip() for p in parts if len(p.strip()) > 25]


# Поиск по границе слова: без этого «plantation» находится внутри «implantation»,
# а «parc» — внутри «parcelle» и в названиях улиц вроде «avenue du Parc».
_TERM_RES = [(t, re.compile(r"(?<![a-zà-ÿ])" + re.escape(t), re.I)) for t in GREEN_TERMS]


def green_terms_in(sent: str) -> list[str]:
    return sorted({t for t, rx in _TERM_RES if rx.search(sent)})


def classify(sent: str) -> tuple[str, list[str]]:
    """→ ('measure' | 'state' | 'none', найденные термины)"""
    terms = green_terms_in(sent)
    if not terms:
        return "none", []
    has_pro = bool(PROSPECTIVE_RE.search(sent))
    has_sta = bool(STATIVE_RE.search(sent))
    if has_pro and not has_sta:
        return "measure", terms
    if has_pro and has_sta:
        return "measure", terms          # смешанное — склоняемся к мере, пометим на вычитку
    return "state", terms


def main() -> int:
    contracts = json.loads(IN_RAW.read_text())
    out = []

    for c in contracts:
        measures, states, mixed = [], [], []
        for sent in sentences(c["description"]):
            kind, terms = classify(sent)
            if kind == "none":
                continue
            item = {"quote": sent[:400], "terms": terms}
            if kind == "measure":
                if STATIVE_RE.search(sent):
                    item["needs_review"] = "смешанные маркеры"
                    mixed.append(item)
                measures.append(item)
            else:
                states.append(item)

        out.append({
            "id": c["id"],
            "name": c["name"],
            "commune": c["commune"],
            "years": [c["year_start"], c["year_end"]],
            "has_greening_measure": bool(measures),
            "measures": measures,
            "state_only": states,
            "needs_review": bool(mixed),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))

    with_m = [r for r in out if r["has_greening_measure"]]
    state_only = [r for r in out if not r["has_greening_measure"] and r["state_only"]]
    review = [r for r in out if r["needs_review"]]

    print(f"контрактов:                      {len(out)}")
    print(f"с планируемой мерой озеленения:  {len(with_m)}")
    print(f"только описание состояния:       {len(state_only)}  ← их наивный поиск считал бы мерами")
    print(f"требуют вычитки:                 {len(review)}")
    print(f"→ {OUT}\n")

    print("=== только состояние (ложные срабатывания наивного поиска) ===")
    for r in state_only[:12]:
        q = r["state_only"][0]["quote"]
        print(f"  [{r['id']:>3}] {r['name'][:24]:<24} «{q[:90]}…»")

    print("\n=== контракты с мерами, окна 2019–2020 ===")
    for r in with_m:
        if 2019 <= r["years"][0] <= 2020:
            print(f"  [{r['id']:>3}] {r['name'][:26]:<26} {r['years'][0]}–{r['years'][1]}  "
                  f"мер: {len(r['measures'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
