#!/usr/bin/env python3
"""Досье под заявку на финансирование: обоснование по одному сектору.

Четвёртый экран из вайрфреймов и единственная форма продукта, за которую
предполагалось брать деньги. Отличие от отчёта: отчёт говорит, что произошло
в городе, досье — почему деньги должны прийти именно сюда и чем потом будет
доказано, что они сработали.

Устройство: **доказательство фиксировано, подача настраивается.** Все числа
берутся из слоёв городского пакета и дел аудита; меняется только текст вокруг
них. Обещание проверки — не обещание результата: досье прямо перечисляет, что
метод измерит, чего не измерит и в каком случае откажется выносить вердикт.

    .venv/bin/python scripts/report/dossier_html.py --city brussels --sector 21012A152
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.config import CITIES, CONTROL, QUALITY  # noqa: E402
from engine.manifest import Manifest  # noqa: E402
from engine.registries.points import load as load_points  # noqa: E402

from scripts.report.paths import DERIVED, OUT as SCRATCH, today_ru  # noqa: E402
from scripts.report.background import sentence as bg_sentence  # noqa: E402

# Падежи и определение дохода по городу. С 25.09.2026 доход в обоих пакетах — медиана
# Statbel 2023 (`scripts/registry/statbel_income.py`); до того у Антверпена было среднее.
# Подпись всё равно берётся по городу: она обязана говорить, что стоит в строке.
CITY_GEN = {"brussels": "Брюсселя", "antwerp": "Антверпена"}
CITY_DAT = {"brussels": "Брюсселю", "antwerp": "Антверпену"}
INCOME_LABEL = {"brussels": "медианный облагаемый доход, Statbel 2023",
                "antwerp": "медианный облагаемый доход, Statbel 2023"}

# Правило выбора сектора для --sector auto: открытое, чтобы досье нельзя было
# упрекнуть в подборе адреса под вывод.
PICK_RULE = ("нижний терциль по доходу, нижняя треть по кроне, летом поверхность жарче медианы "
             "города не меньше чем на 1 °C, коммуна не проходит исключение ст. 8(1), не меньше "
             "500 жителей; из подходящих — сектор, где больше всего детей до 15 лет")

# Дела аудита — доказательная база «что даёт вмешательство такого типа».
CASES = [("ninove", "Parc de la Porte de Ninove", "Брюссель", "пустырь у канала → парк 2,2 га"),
         ("droogdokkenpark", "Droogdokkenpark", "Антверпен", "старые доки → парк на набережной"),
         ("spoor-noord", "Park Spoor Noord", "Антверпен", "сортировочная станция → парк 19,5 га")]

CSS = """
:root{--paper:#EFF1EC;--surface:#FFFFFF;--ink:#141B17;--muted:#5B6B62;--rule:#D5DAD3;--rule-2:#E4E8E3;
--accent:#1E6E58;--accent-soft:#E2EDE7;--heat:#C2451C;--heat-soft:#F7E6DE;--bar:#C6CFC7;
--display:"IBM Plex Sans Condensed","Helvetica Neue",Arial,sans-serif;--body:"IBM Plex Serif",Georgia,serif;
--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--measure:34rem;--wide:60rem}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;
--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;--bar:#39433B}}
:root[data-theme="dark"]{--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;
--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;--bar:#39433B}
*{box-sizing:border-box}body{background:var(--paper);color:var(--ink);font-family:var(--body);font-size:16.5px;line-height:1.62;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}a:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.page{max-width:var(--wide);margin:0 auto;padding:4rem 1.5rem 7rem;display:flex;flex-direction:column;gap:3rem}
.col{max-width:var(--measure)}.masthead{display:flex;flex-direction:column;gap:1rem;padding-bottom:2rem;border-bottom:2px solid var(--ink)}
.eyebrow{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
h1{font-family:var(--display);font-weight:700;font-size:clamp(2.2rem,6vw,3.4rem);line-height:1;letter-spacing:-.02em;margin:0;text-wrap:balance}
.standfirst{font-size:1.12rem;line-height:1.5;max-width:38rem;margin:0}
.dateline{font-family:var(--mono);font-size:.76rem;color:var(--muted);display:flex;flex-wrap:wrap;gap:.4rem 1.4rem}
section{display:flex;flex-direction:column;gap:1.1rem}.sec-head{display:flex;flex-direction:column;gap:.3rem;border-top:1px solid var(--rule);padding-top:.9rem}
.sec-head .eyebrow{color:var(--accent)}h2{font-family:var(--display);font-weight:600;font-size:clamp(1.35rem,3.2vw,1.8rem);line-height:1.12;margin:0;text-wrap:balance}
h3{font-family:var(--display);font-weight:600;font-size:1.02rem;margin:.4rem 0 0}p{margin:0}strong{font-weight:600}code{font-family:var(--mono);font-size:.86em}
ul,ol{margin:0;padding-left:1.15rem;display:flex;flex-direction:column;gap:.45rem}li::marker{color:var(--muted)}
.callout{background:var(--accent-soft);border-left:3px solid var(--accent);padding:1rem 1.2rem;max-width:var(--measure)}
.warn{background:var(--heat-soft);border-left:3px solid var(--heat);padding:1rem 1.2rem;max-width:var(--measure)}
.scroll{overflow-x:auto;max-width:100%}table{border-collapse:collapse;width:100%;min-width:30rem;font-size:.9rem;font-family:var(--display);font-weight:500}
th{text-align:left;font-family:var(--mono);font-weight:500;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--ink);padding:0 .85rem .5rem 0;vertical-align:bottom}
td{border-bottom:1px solid var(--rule);padding:.6rem .85rem .6rem 0;vertical-align:top;line-height:1.4}td.num{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
tr:last-child td{border-bottom:none}td small{display:block;font-size:.82rem;color:var(--muted)}
.passport{display:grid;grid-template-columns:repeat(auto-fit,minmax(9rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}
.passport div{background:var(--surface);padding:.9rem 1rem;display:flex;flex-direction:column;gap:.15rem}
.passport b{font-family:var(--display);font-weight:700;font-size:1.6rem;line-height:1;font-variant-numeric:tabular-nums}
.passport span{font-family:var(--display);font-size:.78rem;color:var(--muted);line-height:1.3}
/* Сравнение с городом: полоса показывает, где сектор стоит на шкале */
.bars{display:grid;grid-template-columns:minmax(8rem,10rem) 1fr auto;gap:.55rem 1rem;align-items:center;
background:var(--surface);border:1px solid var(--rule);padding:1.2rem 1.25rem;font-family:var(--display)}
.bars .l{font-size:.92rem}.bars .l small{display:block;font-family:var(--mono);font-size:.68rem;color:var(--muted)}
.bars .t{height:1.1rem;background:var(--rule-2);position:relative}
.bars .t i{position:absolute;inset:0 auto 0 0;background:var(--bar)}
.bars .t u{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--ink);text-decoration:none}
.bars .v{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:.92rem;text-align:right}
.bars .here i{background:var(--heat)}
.foot{font-family:var(--display);font-size:.82rem;color:var(--muted);border-top:1px solid var(--rule);padding-top:1rem;max-width:46rem}
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def n(x) -> str:
    return f"{int(round(float(x))):,}".replace(",", " ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="brussels", choices=list(CITIES))
    ap.add_argument("--sector", required=True, help="код сектора или auto — выбор по правилу PICK_RULE")
    args = ap.parse_args()
    city = args.city

    rows = list(csv.DictReader(Path(f"cities/{city}/layers/article8_2024.csv").open()))
    num = ("area_ha", "population", "density", "income", "ndvi_2024", "trees_2024",
           "grass_2024", "built_2024", "ndvi_eff", "trees_eff", "gap")
    for r in rows:
        for k in num:
            r[k] = float(r[k]) if r.get(k) not in ("", None) else None
    with_income = [r for r in rows if r["income"]]
    inc_sorted = sorted(r["income"] for r in with_income)
    cut_low = inc_sorted[len(inc_sorted) // 3]
    cut_high = inc_sorted[2 * len(inc_sorted) // 3]
    low = [r for r in with_income if r["income"] <= cut_low]
    high = [r for r in with_income if r["income"] >= cut_high]

    def wmean(items, key):
        pop = sum(r["population"] for r in items if r[key] is not None)
        return sum(r[key] * r["population"] for r in items if r[key] is not None) / pop if pop else None

    med = {k: statistics.median(r[k] for r in rows if r[k] is not None)
           for k in ("ndvi_2024", "trees_2024", "built_2024")}
    # Возрастная структура: кому именно достаётся или не достаётся крона.
    age = {r["id"]: r for r in csv.DictReader(Path(f"cities/{city}/layers/population_age.csv").open())}
    by_trees = sorted((r for r in rows if r["trees_2024"] is not None), key=lambda r: r["trees_2024"])
    third_ids = {r["id"] for r in by_trees[:len(by_trees) // 3]}

    def layer_rows(name):
        pth = Path(f"cities/{city}/layers/{name}.csv")
        return list(csv.DictReader(pth.open())) if pth.exists() else []

    heat_by = {r["id"]: float(r["excess_over_city_c"]) for r in layer_rows("heat_2022_2025")}
    lau = {r["lau_id"]: r for r in layer_rows("art8_official_lau_2021")}

    # Сектор: указанный или выбранный правилом. Кандидаты печатаются, чтобы выбор был проверяем.
    if args.sector == "auto":
        def fits(r):
            code = f"BE_{r['id'][:5]}"
            return (r["income"] is not None and r["income"] <= cut_low and r["id"] in third_ids
                    and heat_by.get(r["id"], -99) >= 1.0 and r["population"] >= 500
                    and code in lau and lau[code]["exempt"] != "True")
        cands = sorted((r for r in rows if fits(r)),
                       key=lambda r: (-int(age.get(r["id"], {}).get("children_0_14") or 0), -r["population"]))
        if not cands:
            raise SystemExit("по правилу не подходит ни один сектор")
        print(f"правило выбора: {PICK_RULE}\nподходят {len(cands)}:")
        for r in cands[:6]:
            print(f"  {r['id']} {r['name'][:34]:<34} {r['commune']:<12} детей "
                  f"{age.get(r['id'], {}).get('children_0_14', '—'):>5} · жителей {n(r['population'])} · "
                  f"крона {r['trees_2024']:.3f} · жарче на {heat_by[r['id']]:+.1f} °C")
        sector, n_fit = cands[0]["id"], len(cands)
    else:
        sector, n_fit = args.sector, None
    s = next(r for r in rows if r["id"] == sector)

    pct = {k: 100 * sum(1 for r in rows if r[k] is not None and r[k] < s[k]) / len(rows)
           for k in ("ndvi_2024", "trees_2024")}
    a = age.get(sector)
    kids_third = sum(int(age[i]["children_0_14"]) for i in third_ids if i in age)
    kids_all = sum(int(v["children_0_14"]) for v in age.values())
    in_third = sector in third_ids

    # Норма 3-30-300 и тепловая нагрузка по этому сектору, если слои посчитаны.
    def layer_row(name):
        pth = Path(f"cities/{city}/layers/{name}.csv")
        if not pth.exists():
            return None
        return next((r for r in csv.DictReader(pth.open()) if r["id"] == sector), None)

    rule = layer_row("rule_3_30_300")
    heat = layer_row("heat_2022_2025")

    man = Manifest.read(city)
    # пороги приборов — для обязательства будущего аудита; пороги тренда — слоя ст. 8,
    # посчитанные тем же прогоном, что и эффекты, которые здесь печатаются
    thr_ndvi = man.layers["ndvi"].threshold
    thr_trees = man.layers["trees"].threshold
    s8thr = json.loads(Path(f"cities/{city}/layers/article8_2024_summary.json").read_text())["thresholds"]
    trend_thr_ndvi, trend_thr_trees = s8thr["ndvi"], s8thr.get("trees", thr_trees)

    # где сектор стоит на шкале города — три полосы
    def bar(label, sub, key, val, unit=""):
        mx = max(r[key] for r in rows if r[key] is not None)
        return (f'<div class="l">{esc(label)}<small>{esc(sub)}</small></div>'
                f'<div class="t here"><i style="width:{100 * val / mx:.1f}%"></i>'
                f'<u style="left:{100 * med[key] / mx:.1f}%" title="медиана города"></u></div>'
                f'<div class="v">{val:.3f}{unit}</div>')

    bars = (bar("Древесная крона", f"медиана города {med['trees_2024']:.3f}", "trees_2024", s["trees_2024"])
            + bar("Зелёность", f"медиана города {med['ndvi_2024']:.3f}", "ndvi_2024", s["ndvi_2024"])
            + bar("Застройка", f"медиана города {med['built_2024']:.3f}", "built_2024", s["built_2024"]))

    # дела аудита как доказательная база; итог ряда считается из дела, а не вписан
    def series_note(c):
        ot = c.get("over_time")
        if not ot:
            return ""
        thr = ot["threshold_audit"]
        k = sum(1 for o in ot["seasons"] if o["effect"] > thr); n = len(ot["seasons"])
        return f" Сверх порога {k} из {n} сезонов после сдачи."
    case_rows = ""
    for slug, title, ccity, what in CASES:
        p = Path(f"data/registry/cases/{slug}.json")
        if not p.exists():
            continue
        c = json.loads(p.read_text())
        i = c["instruments"][0]
        # защитимое число важнее стандартного окна: у Droogdokkenpark половина стандартного
        # эффекта — стройплощадка в базе, и лендинг печатает +0,15, а не +0,29
        eff = c.get("defensible_effect", i["effect"])
        eff_note = f"<small>{esc(c['defensible_note'])}</small>" if c.get("defensible_note") else ""
        case_rows += (f"<tr><td>{esc(title)}<small>{esc(ccity)} · {esc(what)}</small></td>"
                      f"<td class='num'>{eff:+.3f}{eff_note}</td><td class='num'>{i['threshold']:.4f}</td>"
                      f"<td class='num'>{eff / i['threshold']:.1f}×</td>"
                      f"<td>{esc(c.get('verdict_line') or '')}{series_note(c)}</td></tr>")

    # точки линии выполнения в этом секторе
    from engine.registries.points import KIND_LABEL_RU
    pts = [p for f in ("named_points.json", f"named_points_{args.city}.json")
           if Path(f"data/registry/{f}").exists()
           for p in load_points(Path(f"data/registry/{f}")) if p.unit_id == sector]
    pts_txt = ""
    if pts:
        roles = ", ".join(f"{KIND_LABEL_RU.get(p.kind, p.kind)} ({'названа' if p.role == 'named' else 'контроль'})"
                          for p in pts)
        pts_txt = (f'<div class="callout col"><p><strong>В этом секторе уже есть точка второй линии.</strong> '
                   f'{esc(roles)}: место зафиксировано {esc(pts[0].registered_at)} с хешем, и появление объекта '
                   f'будет проверено по истории карты. Досье и проверка выполнения смотрят на один и тот же адрес.</p></div>')

    low_trees, high_trees = wmean(low, "trees_2024"), wmean(high, "trees_2024")
    ratio = low_trees / high_trees if high_trees else None
    verdict_ndvi = s["ndvi_verdict"]
    trend_txt = {
        "шум": "изменение зелёности за 2017–2024 годы не вышло за порог значимости: сектор стоит на месте",
        "значимо вниз": "зелёность значимо упала относительно сопоставимых секторов",
        "значимо вверх": "зелёность значимо выросла относительно сопоставимых секторов",
    }.get(verdict_ndvi, f"вердикт тренда: {verdict_ndvi}")

    # Заголовок считается, а не пишется: «вдвое ниже» при отношении 0,6 было бы
    # преувеличением того же рода, против которого построен весь метод.
    share = s["trees_2024"] / med["trees_2024"]
    if share <= 0.55:
        headline_gap = f"кроны вдвое меньше городской медианы"
    elif share < 0.95:
        headline_gap = f"кроны на {100 * (1 - share):.0f} % меньше городской медианы"
    elif share <= 1.05:
        headline_gap = "крона на уровне городской медианы"
    else:
        headline_gap = f"кроны на {100 * (share - 1):.0f} % больше городской медианы"

    age_html = ""
    if a:
        kids, old_, oldest = int(a["children_0_14"]), int(a["seniors_65_plus"]), int(a["seniors_80_plus"])
        tot = int(a["population_census"])
        age_html = (
            f'<div class="callout col"><p><strong>Кому здесь не хватает тени.</strong> В секторе живёт '
            f'{n(kids)} детей до 15 лет ({100 * kids / tot:.0f} % населения) и {n(old_)} человек старше 65 '
            f'({100 * old_ / tot:.0f} %), из них {n(oldest)} старше 80 — группы, для которых жара опаснее всего. '
            f'По городу в трети секторов с наименьшей кроной живёт {100 * kids_third / kids_all:.0f} % всех детей: '
            f'нехватка тени распределена не поровну, и сильнее всего она задевает именно их.'
            + (" Этот сектор входит в ту треть." if in_third else "")
            + '</p></div>')

    rule_html = ""
    if rule and heat:
        can = float(rule["canopy_share"]); near = float(rule["near_park_share"])
        exc = float(heat["excess_over_city_c"]); lst = float(heat["lst_summer_c"])
        fails = []
        if rule["passes_30"] != "1":
            fails.append(f"кроны {100 * can:.1f} % при норме 30 %")
        if rule["passes_300"] != "1":
            fails.append(f"в 300 м от парка лежит {100 * near:.0f} % площади сектора при норме половины")
        verdict = ("оба измеримых пункта нормы не выполняются: " + "; ".join(fails)) if len(fails) == 2 else \
                  ("один пункт нормы не выполняется: " + "; ".join(fails)) if fails else \
                  "оба измеримых пункта нормы выполняются"
        # Сила связи тепла и кроны — посчитана по городу, а не перенесена из Брюсселя:
        # там r = −0,89, в Антверпене −0,66, и «почти детерминированная» была бы неправдой.
        wc = {r["id"]: float(r["wc_trees"]) for r in layer_rows("worldcover_2021")}
        ids_hc = sorted(set(wc) & set(heat_by))
        r_hc = statistics.correlation([heat_by[i] for i in ids_hc], [wc[i] for i in ids_hc]) if len(ids_hc) > 30 else None
        strength = ("почти детерминированная" if r_hc is not None and r_hc <= -0.8 else
                    "сильная" if r_hc is not None and r_hc <= -0.5 else "заметная")
        both_bad = exc >= 1.0 and in_third
        rule_html = (
            f'<div class="warn col"><p><strong>{"Норма и жара сходятся в одной точке." if both_bad else "Норма 3-30-300 и жара."}</strong> '
            f'По правилу 3-30-300, принятому в городском лесоводстве, {esc(verdict)}. '
            f'Летняя температура поверхности здесь <strong>{lst:.1f} °C</strong> — на '
            f'<strong>{abs(exc):.1f} °C</strong> {"выше" if exc >= 0 else "ниже"} медианы города. Чем меньше кроны, '
            f'тем жарче: связь по городу {strength}'
            + (f" (r = {r_hc:.2f})".replace("-", "−") if r_hc is not None else "")
            + (", и этот сектор стоит на плохом конце обеих шкал сразу. " if both_bad else ". ")
            + 'Температура здесь описывает состояние: охлаждение от вмешательства проект не измеряет, '
            'потому что порог значимости для неё больше реалистичного эффекта парка.</p></div>')

    # Тексты, которые раньше были брюссельскими константами, — из данных города
    cfg_name = CITIES[city]["display_name"]
    low_income = s["income"] is not None and s["income"] <= cut_low
    if low_income and in_third:
        income_txt = (f"Доход ниже порога нижнего терциля ({n(cut_low)} €), то есть перед нами совпадение "
                      "двух дефицитов: мало зелени и мало денег.")
    elif s["income"] is not None:
        income_txt = f"Доход сектора — {n(s['income'])} € при пороге нижнего терциля {n(cut_low)} €."
    else:
        income_txt = "Дохода по этому сектору в данных нет."
    # фон города — общая функция, та же, что на методе, атласе и аудите
    background_txt = "Важно, что сравнение идёт с контролем, а не с собственным прошлым. " + bg_sentence(city)
    if ratio is None:
        equity_head = "Кому досталась крона"
    elif ratio < 0.4:
        equity_head = "Беднейшая треть города живёт меньше чем при половине кроны"
    elif ratio <= 0.6:
        equity_head = "Беднейшая треть города живёт при половине кроны"
    elif ratio < 0.95:
        equity_head = f"У беднейшей трети города кроны на {100 * (1 - ratio):.0f} % меньше, чем у богатейшей"
    else:
        equity_head = "Крона распределена между доходными группами почти поровну"
    if low_income:
        group_txt = ("Этот сектор лежит ниже среднего даже для своей группы." if s["trees_2024"] < low_trees else
                     "Для своей группы сектор не хуже среднего: дефицит здесь общий для всей нижней трети.")
    else:
        group_txt = "Сектор не входит в нижний терциль по доходу."

    # Статья 8: входит ли коммуна сектора в национальный итог (методика Комиссии)
    law_html = ""
    lr = lau.get(f"BE_{sector[:5]}")
    if lr:
        g = float(lr["green_ucuc"])
        cname = s["commune"] if city == "brussels" else lr["name"].split(" / ")[0]
        law_html = (
            f'<div class="callout col"><p><strong>{"Закон этот сектор считает." if lr["exempt"] != "True" else "Коммуна может выйти из-под закона."}</strong> '
            + (f"Коммуна {esc(cname)} исключение ст. 8(1) не проходит: зелени в её городских центрах и кластерах "
               f"{100 * g:.1f} % при пороге 45 % (методика Комиссии, CLCplus 2021). Всё, что здесь посажено или "
               "потеряно, входит в национальный итог нулевой чистой потери."
               if lr["exempt"] != "True" else
               f"Коммуна {esc(cname)} проходит исключение ст. 8(1): зелени в городских центрах и кластерах "
               f"{100 * g:.1f} % при пороге 45 %. Если государство её исключит, изменения здесь в национальный итог "
               "не войдут, и обоснование держится на справедливости и жаре, а не на законе.")
            + '</p></div>')
    # После базы: сезоны мониторинга позже 2024-го, теми же функциями, что бюллетень
    from scripts.report.monitoring_html import apply_documents, funnel, load_layer
    events = []
    after_years = sorted(int(k.split("_")[1]) for k in man.layers
                         if k.startswith("monitoring_") and int(k.split("_")[1]) > 2024)
    for yr in after_years:
        F = funnel(apply_documents(load_layer(city, yr), city, yr), man.layers[f"monitoring_{yr}"].threshold)
        for key, kind in (("construction", "стройка по второму прибору"), ("confirmed", "потеря кроны по двум приборам"),
                          ("unconfirmed", "потеря зелёности, второй прибор не подтвердил"),
                          ("gained", "прибавил зелёности сверх порога")):
            events += [(yr, kind, r["effect"]) for r in F[key] if r["id"] == sector]
    if after_years:
        span = f"{after_years[0]}–{after_years[-1]}" if len(after_years) > 1 else str(after_years[0])
        after_txt = ("После базы, в сезонах " + span + ": " +
                     "; ".join(f"{yr} — {kind} ({eff:+.3f} NDVI)".replace("-", "−") for yr, kind, eff in events) + "."
                     if events else f"После базы, в сезонах {span}, значимых изменений в секторе нет.")
    else:
        after_txt = ""
    pick_txt = (f'<div class="col"><p><strong>Как выбран сектор.</strong> Правилом, а не вручную: {esc(PICK_RULE)}. '
                f'Подходят {n_fit}; досье — о первом из них.</p></div>' if n_fit else "")

    doc = f"""<meta charset="utf-8"><title>Досье · {esc(s['name'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>{CSS}</style>
<div class="page">
<header class="masthead">
  <div class="eyebrow">Досье под заявку · {esc(s['commune'])} · сектор {esc(s['id'])}</div>
  <h1>{esc(s['name'])}: {esc(headline_gap)} при {n(s['population'])} жителях</h1>
  <p class="standfirst">Обоснование, почему средства на озеленение должны прийти в этот сектор, и обязательство проверить результат тем же методом, которым измерено состояние. Каждое число ведёт к слою городского пакета; границы применимости напечатаны рядом с числами, а не в примечании.</p>
  <div class="dateline"><span>единица: статистический сектор Statbel</span><span>база 2024 года</span><span>снимки: Sentinel-2, Dynamic World</span><span>собрано {today_ru()}</span></div>
</header>

<section>
  <div class="sec-head"><span class="eyebrow">Паспорт</span><h2>Кто здесь живёт и что вокруг</h2></div>
  <div class="passport">
    <div><b>{n(s['population'])}</b><span>жителей</span></div>
    <div><b>{s['area_ha']:.1f}</b><span>гектаров</span></div>
    <div><b>{n(s['density'])}</b><span>человек на гектар</span></div>
    <div><b>{n(s['income'])} €</b><span>{esc(INCOME_LABEL.get(city, 'облагаемый доход'))}</span></div>
    <div><b>{s['trees_2024']:.3f}</b><span>крона, вероятность класса</span></div>
    <div><b>{s['built_2024']:.3f}</b><span>застройка и покрытие</span></div>
  </div>
  <div class="col"><p>По кроне сектор стоит в нижних <strong>{pct['trees_2024']:.0f} %</strong> города, по зелёности — в нижних <strong>{pct['ndvi_2024']:.0f} %</strong>. {esc(income_txt)}</p></div>
  {pick_txt}
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Состояние</span><h2>Где сектор стоит на шкале города</h2></div>
  <div class="bars">{bars}</div>
  <div class="col"><p>Чёрная риска — медиана города, полоса — значение сектора. Крона здесь <strong>{s['trees_2024']:.3f}</strong> против медианы {med['trees_2024']:.3f}, застройка <strong>{s['built_2024']:.3f}</strong> против {med['built_2024']:.3f}. Значения классов — вероятности, а не доли площади: сравнивать их между секторами можно, читать как проценты территории нельзя.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Тренд</span><h2>Само не улучшится</h2></div>
  <div class="col"><p>За 2017–2024 годы изменение против двенадцати подобранных контрольных секторов составило <strong>{s['ndvi_eff']:+.4f}</strong> по зелёности при пороге значимости {trend_thr_ndvi:.4f} и <strong>{s['trees_eff']:+.4f}</strong> по кроне при пороге {trend_thr_trees:.4f}. Это значит: {trend_txt}.</p>
  <p>{esc(background_txt)}</p></div>
  {'<div class="col"><p>' + esc(after_txt) + '</p></div>' if after_txt else ''}
  <div class="warn col"><p><strong>Что это не доказывает.</strong> Отсутствие роста — не доказательство бездействия города: в секторе могли идти работы, которых метод не видит. Реставрация существующей зелени не отражается в этих числах по построению, а рассеянные уличные посадки тонут в площади сектора.</p></div>
  {law_html}
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Справедливость</span><h2>{esc(equity_head)}</h2></div>
  <div class="scroll"><table><thead><tr><th>группа</th><th>доход, медиана по группе</th><th>крона 2024</th><th>зелёность 2024</th></tr></thead><tbody>
    <tr><td>нижний терциль по доходу</td><td class='num'>{n(statistics.median(r['income'] for r in low))} €</td><td class='num'>{low_trees:.3f}</td><td class='num'>{wmean(low, 'ndvi_2024'):.3f}</td></tr>
    <tr><td>верхний терциль</td><td class='num'>{n(statistics.median(r['income'] for r in high))} €</td><td class='num'>{high_trees:.3f}</td><td class='num'>{wmean(high, 'ndvi_2024'):.3f}</td></tr>
    <tr><td><strong>{esc(s['name'])}</strong></td><td class='num'>{n(s['income'])} €</td><td class='num'>{s['trees_2024']:.3f}</td><td class='num'>{s['ndvi_2024']:.3f}</td></tr>
  </tbody></table></div>
  <div class="col"><p>Взвешено по населению. Отношение кроны нижнего терциля к верхнему — <strong>{ratio:.2f}</strong>. Регламент (EU) 2024/1991 требует нулевой чистой потери зелени и кроны к 2030 году, но о распределении между районами молчит; показатель ООН 11.7 и Tree Equity Score — нет. {esc(group_txt)}</p></div>
  {age_html}
  {rule_html}
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Чего ожидать от вмешательства</span><h2>Три измеренных случая вместо обещаний</h2></div>
  <div class="scroll"><table><thead><tr><th>вмешательство</th><th>эффект</th><th>порог</th><th>превышение</th><th>чтение</th></tr></thead><tbody>{case_rows}</tbody></table></div>
  <div class="col"><p>Это не прогноз для данного сектора, а диапазон измеренного по сопоставимым работам: смена покрытия на большей части участка даёт эффект в три и более раз выше порога и держится годами. Величина зависит от того, что было до работ: пустырь даёт больше, чем уже озеленённая набережная.</p></div>
  <div class="warn col"><p><strong>Чего в этой таблице нет намеренно.</strong> Охлаждения: порог значимости для температуры поверхности вышел 1,32 °C, что больше реалистичного эффекта городских парков, поэтому утверждений о градусах здесь не будет. Стоимости эффекта: сравнивать цену можно только внутри одного типа работ, а бюджеты сопоставимых проектов опубликованы лишь частично.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Обязательство</span><h2>Что именно мы проверим и когда откажемся</h2></div>
  <div class="col"><ol>
    <li><strong>След работ фиксируется до начала.</strong> Полигон, его хеш и дата записываются в реестр раньше первого дня работ. Обвести задним числом там, где позеленело, будет невозможно.</li>
    <li><strong>Контроль называется тогда же.</strong> {CONTROL['n_controls']} секторов, похожих на объект по состоянию до работ, не ближе {CONTROL['exclusion_m']} м. Список публикуется до измерения; если сопоставимого контроля нет, это фиксируется как отказ, а не подгоняется.</li>
    <li><strong>Порог берётся из калибровки города,</strong> а не назначается под результат: нулевое распределение считается той же схемой подбора и теми же снимками, что и сам аудит, — так, как посчитан порог тренда выше.</li>
    <li><strong>Окно сравнения строится от даты сдачи:</strong> база до начала работ, оценка через два года после. Если работы попадают внутрь окна, аудит отказывается считать.</li>
    <li><strong>Вердикт выносится двумя приборами.</strong> Зелёность и классы покрытия по одним снимкам: первый говорит, что изменилось, второй — что именно, вплоть до «раскрыли, но не засадили».</li>
    <li><strong>Отказ — публикуемый исход.</strong> Меньше {QUALITY['min_scenes']} снимков в окне, разрыв с контролем больше {CONTROL['max_gap_ndvi']}, работы вне окна — вердикт не выносится, и это печатается наравне с результатом.</li>
  </ol></div>
  {pts_txt}
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Границы</span><h2>Что метод не измерит даже при идеальном исполнении</h2></div>
  <div class="col"><ul>
    <li>Охлаждение воздуха и поверхности: шум канала больше реалистичного эффекта.</li>
    <li>Реставрацию существующей зелени: починка дорожек и прудов растительность не меняет.</li>
    <li>Рассеянные уличные посадки, измеряемые на уровне сектора: полгектара новой кроны на девятнадцати гектарах тонут.</li>
    <li>Причину изменения: спутник называет место, документы называют причину. Без документа изменение публикуется как измерение, а не как заслуга.</li>
    <li>Молодые посадки первых лет: саженцы на лугу дают зелёность ниже травы, которую заменили, и честное озеленение может измеряться как потеря.</li>
  </ul></div>
</section>

<div class="foot">Источники: слой <code>cities/{esc(city)}/layers/article8_2024.csv</code> (уровни 2024 года и тренд против контроля), манифест города (пороги и их происхождение), дела аудита <code>data/registry/cases/*.json</code>, реестр точек второй линии. Снимки: Copernicus Sentinel-2 SR Harmonized с маской Cloud Score+, Google Dynamic World V1. Секторы, население и доход: Statbel. Доказательство фиксировано и не меняется от редакции текста: числа, пороги и контроль пересчитываются из этих файлов.</div>
</div>
"""
    out = SCRATCH / f"dossier-{sector}.html"
    out.write_text(doc, encoding="utf-8")
    print(f"→ {out}  ({len(doc.encode()) // 1024} КБ) · {s['name']} · {n(s['population'])} чел · "
          f"крона {s['trees_2024']:.3f} (медиана {med['trees_2024']:.3f}) · доход {n(s['income'])} € · "
          f"точек второй линии {len(pts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
