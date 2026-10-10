#!/usr/bin/env python3
"""
Отчёт по статье 8 регламента (EU) 2024/1991 — HTML из данных города.

Правило, которое этот генератор воплощает
─────────────────────────────────────────
Доказательство фиксировано, подача настраивается. Все числа берутся из
`cities/<city>/layers/article8_2024_summary.json` и манифеста; порог, контроль,
логика вердикта — не параметры. Настраивается язык, глубина, адресат.

Текст пока шаблонный: ключа API нет, ИИ-редакция под критерии программы —
когда появится. Числа при этом не меняются ни при какой редакции.

Запуск:
    .venv/bin/python scripts/report/article8_html.py --city brussels
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.config import CITIES, CONTROL, LIMITS, QUALITY
from engine.manifest import Manifest
from engine.instruments import REGISTRY

from scripts.report.paths import DERIVED, OUT as SCRATCH, today_ru  # noqa: E402
from scripts.report.background import sentence as bg_sentence  # noqa: E402

CSS = """
:root{--paper:#EFF1EC;--surface:#FFFFFF;--ink:#141B17;--muted:#5B6B62;--rule:#D5DAD3;--rule-2:#E4E8E3;
--accent:#1E6E58;--accent-soft:#E2EDE7;--heat:#C2451C;--heat-soft:#F7E6DE;
--display:"IBM Plex Sans Condensed","Helvetica Neue",Arial,sans-serif;--body:"IBM Plex Serif",Georgia,serif;
--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--measure:34rem;--wide:60rem}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;
--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14}}
:root[data-theme="dark"]{--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;
--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14}
*{box-sizing:border-box}body{background:var(--paper);color:var(--ink);font-family:var(--body);font-size:16.5px;line-height:1.62;-webkit-font-smoothing:antialiased}
.page{max-width:var(--wide);margin:0 auto;padding:4rem 1.5rem 7rem;display:flex;flex-direction:column;gap:3rem}
.col{max-width:var(--measure)}.masthead{display:flex;flex-direction:column;gap:1rem;padding-bottom:2rem;border-bottom:2px solid var(--ink)}
.eyebrow{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
h1{font-family:var(--display);font-weight:700;font-size:clamp(2.4rem,7vw,4rem);line-height:.98;letter-spacing:-.02em;margin:0;text-wrap:balance}
.standfirst{font-size:1.15rem;line-height:1.5;max-width:38rem;margin:0}
.dateline{font-family:var(--mono);font-size:.76rem;color:var(--muted);display:flex;flex-wrap:wrap;gap:.4rem 1.4rem}
section{display:flex;flex-direction:column;gap:1.1rem}.sec-head{display:flex;flex-direction:column;gap:.3rem;border-top:1px solid var(--rule);padding-top:.9rem}
.sec-head .eyebrow{color:var(--accent)}h2{font-family:var(--display);font-weight:600;font-size:clamp(1.4rem,3.4vw,1.9rem);line-height:1.12;margin:0;text-wrap:balance}
h3{font-family:var(--display);font-weight:600;font-size:1.05rem;margin:.4rem 0 0}p{margin:0}strong{font-weight:600}code{font-family:var(--mono);font-size:.86em}
ul{margin:0;padding-left:1.15rem;display:flex;flex-direction:column;gap:.45rem}li::marker{color:var(--muted)}
.callout{background:var(--accent-soft);border-left:3px solid var(--accent);padding:1rem 1.2rem;max-width:var(--measure)}
.warn{background:var(--heat-soft);border-left:3px solid var(--heat);padding:1rem 1.2rem;max-width:var(--measure)}
.scroll{overflow-x:auto;max-width:100%}table{border-collapse:collapse;width:100%;min-width:34rem;font-size:.9rem;font-family:var(--display);font-weight:500}
th{text-align:left;font-family:var(--mono);font-weight:500;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--ink);padding:0 .85rem .5rem 0;vertical-align:bottom}
td{border-bottom:1px solid var(--rule);padding:.6rem .85rem .6rem 0;vertical-align:top;line-height:1.4}td.num{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
tr:last-child td{border-bottom:none}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}
.stat{background:var(--surface);padding:1rem 1.05rem;display:flex;flex-direction:column;gap:.2rem}
.stat b{font-family:var(--display);font-weight:700;font-size:2rem;line-height:1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat span{font-family:var(--display);font-size:.8rem;color:var(--muted);line-height:1.3}
.tag{font-family:var(--mono);font-size:.67rem;letter-spacing:.05em;text-transform:uppercase;padding:.14rem .42rem;white-space:nowrap;border:1px solid currentColor}
.t-loss{color:var(--heat)}.t-gain{color:var(--accent)}.t-mute{color:var(--muted)}
.foot{font-family:var(--display);font-size:.82rem;color:var(--muted);border-top:1px solid var(--rule);padding-top:1rem;max-width:46rem}
"""


def esc(x) -> str:
    return html.escape(str(x))


def fmt_int(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", choices=list(CITIES), required=True)
    args = ap.parse_args()

    cfg = CITIES[args.city]
    root = Path(f"cities/{args.city}/layers")
    S = json.loads((root / "article8_2024_summary.json").read_text())
    m = Manifest.read(args.city)
    rows = list(csv.DictReader((root / "article8_2024.csv").open()))
    b, tr, thr = S["baseline"], S["trend"], S["thresholds"]
    has_trees = "trees" in thr

    def layer_rows():
        out = []
        for k, v in m.layers.items():
            if k not in REGISTRY:   # производные слои пакета — не приборы, в таблицу порогов не идут
                continue
            out.append(f"<tr><td><code>{esc(k)}</code></td><td>{esc(v.measures)}</td>"
                       f"<td class='num'>{v.threshold:.4f}</td><td>{esc(v.threshold_source or '')}</td></tr>")
        return "\n".join(out)

    def loss_rows(items, key="eff"):
        if not items:
            return "<tr><td colspan='5'>значимых потерь нет</td></tr>"
        out = []
        for t in items:
            tre = t.get("trees_eff")
            tre_s = f"{tre:+.3f}" if tre is not None else "—"
            out.append(f"<tr><td>{esc(t['name'])}</td><td>{esc(t['commune'])}</td>"
                       f"<td class='num'>{t[key]:+.4f}</td><td class='num'>{fmt_int(t['population'])}</td>"
                       f"<td class='num'>{tre_s}</td></tr>")
        return "\n".join(out)

    def tercile_rows():
        out = []
        for t in S["equity_income_terciles"]:
            out.append(f"<tr><td>{esc(t['label'])}</td><td class='num'>{fmt_int(t['income_median'])} €</td>"
                       f"<td class='num'>{t['ndvi_2024_wmean']:.3f}</td><td class='num'>{t['trees_2024_wmean']:.3f}</td>"
                       f"<td class='num'>{t['ndvi_eff_mean']:+.4f}</td><td class='num'>{t['loss_sectors']}</td>"
                       f"<td class='num'>{t['gain_sectors']}</td></tr>")
        return "\n".join(out)

    terc = S["equity_income_terciles"]
    equity_line = ""
    if len(terc) == 3:
        lo, hi = terc[0], terc[2]
        equity_line = (f"Нижний терциль по доходу (медиана {fmt_int(lo['income_median'])} €) в 2024 году имеет "
                       f"зелёность {lo['ndvi_2024_wmean']:.3f} и крону {lo['trees_2024_wmean']:.3f}; верхний "
                       f"({fmt_int(hi['income_median'])} €) — {hi['ndvi_2024_wmean']:.3f} и {hi['trees_2024_wmean']:.3f}. "
                       f"Тренд к базе: {lo['ndvi_eff_mean']:+.4f} против {hi['ndvi_eff_mean']:+.4f}.")

    refused = S["units_measured"] - S["units_comparable"]
    not_measured = S["units_total"] - S["units_measured"]

    # Слои, добавленные позже: возраст, официальная крона, норма 3-30-300, жара.
    # Каждый читается, только если посчитан — отчёт не должен падать на неполном пакете.
    def read_layer(name):
        pth = root / (name + ".csv")
        return list(csv.DictReader(pth.open())) if pth.exists() else []

    age_rows = read_layer("population_age")
    wc_rows = read_layer("worldcover_2021")
    rule_rows = read_layer("rule_3_30_300")
    heat_rows = read_layer("heat_2022_2025")

    age_html = ""
    if age_rows:
        by_trees = sorted((r for r in rows if r.get("trees_2024")), key=lambda r: float(r["trees_2024"]))
        third = set(r["id"] for r in by_trees[:len(by_trees) // 3])
        age_by_id = {r["id"]: r for r in age_rows}
        kids_all = sum(int(r["children_0_14"]) for r in age_rows)
        old_all = sum(int(r["seniors_80_plus"]) for r in age_rows)
        kids_third = sum(int(age_by_id[i]["children_0_14"]) for i in third if i in age_by_id)
        old_third = sum(int(age_by_id[i]["seniors_80_plus"]) for i in third if i in age_by_id)
        if kids_all and old_all:
            age_html = ('<div class="col"><p><strong>Возраст говорит резче дохода.</strong> В трети секторов с '
                        "наименьшей кроной живёт <strong>%.0f %%</strong> всех детей города до 15 лет, но только "
                        "<strong>%.0f %%</strong> людей старше 80. Литература о городской жаре говорит прежде всего "
                        "о пожилых; распределение кроны здесь сильнее всего задевает детей. Источник: перепись "
                        "Statbel 2021 года.</p></div>" % (100 * kids_third / kids_all, 100 * old_third / old_all))

    parts = []
    if wc_rows:
        pop_wc = sum(float(r["population"] or 0) for r in wc_rows)
        wc_mean = sum(float(r["wc_trees"]) * float(r["population"] or 0) for r in wc_rows) / pop_wc if pop_wc else 0
        parts.append('<div class="col"><p><strong>Официальная сверка.</strong> По ESA WorldCover (жёсткая '
                     "классификация 10 м, доля площади) деревья занимают <strong>%.1f %%</strong> территории у "
                     "среднего жителя. Наш прибор даёт среднюю вероятность класса, а не долю площади, и величины "
                     "расходятся втрое при высоком согласии рангов. Для процентов и площадей нужен продукт с "
                     "жёсткой классификацией, для изменения против контроля — наш прибор с калиброванным "
                     "порогом.</p></div>" % (100 * wc_mean))
        # Третий прибор: другой производитель и другой сенсор. Два первых оба сидят на
        # Sentinel-2, поэтому их согласие — слабое свидетельство; этот — независимый.
        pv_rows = read_layer("canopy_probav_2019")
        if pv_rows:
            import statistics
            pv = {r["id"]: float(r["canopy_share"]) for r in pv_rows}
            wc_by = {r["id"]: float(r["wc_trees"]) for r in wc_rows}
            dw_by = {r["id"]: float(r["trees_2024"]) for r in rows if r.get("trees_2024")}
            def r_with(other):
                ids = sorted(set(pv) & set(other))
                return statistics.correlation([pv[i] for i in ids], [other[i] for i in ids]), len(ids)
            r_wc, n_wc = r_with(wc_by)
            r_dw, n_dw = r_with(dw_by)
            parts.append('<div class="callout col"><p><strong>Третий прибор, независимый от первых двух.</strong> '
                         "Dynamic World и WorldCover оба построены на снимках Sentinel-2, поэтому их согласие — "
                         "слабое свидетельство. Доля кроны Copernicus Global Land Service (производитель VITO, "
                         "сенсор PROBA-V, 100 м, 2019) не зависит от них ни по сенсору, ни по производителю — и "
                         "ранжирует секторы так же: <strong>r = %.2f</strong> с WorldCover и <strong>r = %.2f</strong> "
                         "с нашим классом trees (%d секторов). Величины трёх приборов при этом расходятся, и так "
                         "должно быть: определения кроны и разрешение у них разные. Сверка по рангу, не по "
                         "процентам; базой 2024 года продукт 2019 года быть не может.</p></div>"
                         % (r_wc, r_dw, min(n_wc, n_dw)))
    if rule_rows:
        popr = sum(float(r["population"] or 0) for r in rule_rows)
        def sh(pred):
            return sum(float(r["population"] or 0) for r in rule_rows if pred(r)) / popr if popr else 0
        s30 = sh(lambda r: r["passes_30"] == "1"); s300 = sh(lambda r: r["passes_300"] == "1")
        both = sh(lambda r: r["passes_both"] == "1")
        none_ = sh(lambda r: r["passes_30"] != "1" and r["passes_300"] != "1")
        parts.append('<div class="scroll"><table><thead><tr><th>правило 3-30-300</th><th>доля населения</th></tr>'
                     "</thead><tbody>"
                     "<tr><td>живёт при кроне не ниже 30 %%</td><td class='num'>%.1f %%</td></tr>"
                     "<tr><td>живёт в 300 м от парка от 1 га</td><td class='num'>%.1f %%</td></tr>"
                     "<tr><td><strong>выполняются оба измеримых пункта</strong></td><td class='num'>"
                     "<strong>%.1f %%</strong></td></tr>"
                     "<tr><td>не выполняется ни один</td><td class='num'>%.1f %%</td></tr></tbody></table></div>"
                     '<div class="col"><p>Норма Конейнендейка, принятая в городском лесоводстве: три дерева из окна, '
                     "30 %% кроны в районе, 300 м до парка. Третий пункт здесь не измерен и не имитирован — для "
                     "него нужен обзор от каждого здания.</p></div>"
                     % (100 * s30, 100 * s300, 100 * both, 100 * none_))
    if heat_rows:
        heat_by_id = {r["id"]: float(r["excess_over_city_c"]) for r in heat_rows}
        wc_by_id = {r["id"]: float(r["wc_trees"]) for r in wc_rows} if wc_rows else {}
        both_bad = [r for r in heat_rows
                    if heat_by_id.get(r["id"], 0) >= 1 and wc_by_id.get(r["id"], 1) < 0.10]
        pop_bad = sum(float(r["population"] or 0) for r in both_bad)
        parts.append('<div class="warn col"><p><strong>Жара и отсутствие тени совпадают.</strong> Летняя '
                     "температура поверхности сектора тем выше, чем меньше в нём кроны. Секторов, где одновременно "
                     "на градус жарче медианы города и кроны меньше десятой части, — <strong>%d</strong>, в них "
                     "живёт <strong>%s</strong> человек. Это состояние, а не эффект: охлаждение от вмешательств "
                     "проект не измеряет, потому что порог значимости для температуры больше реалистичного эффекта "
                     "парка.</p></div>" % (len(both_bad), fmt_int(pop_bad)))
    extra_html = "\n  ".join(parts) if parts else '<div class="col"><p>Дополнительные слои ещё не посчитаны.</p></div>'

    # ── После базы: сезоны мониторинга позже 2024 года ──────────────────────
    # Для статьи 8 стройка на зелени — тоже потеря: закон считает площадь зелени и кроны,
    # а не её состояние. Поэтому здесь поимённо и стройки, и подтверждённые потери кроны.
    # Считается теми же функциями, что бюллетень мониторинга: слой, документы, воронка.
    from scripts.report.monitoring_html import NOTES, apply_documents, funnel, load_layer
    after_seasons = sorted(int(k.split("_")[1]) for k in m.layers
                           if k.startswith("monitoring_") and int(k.split("_")[1]) > 2024)
    after_rows, named_rows = "", ""
    uniq_conf, uniq_constr = {}, {}          # сектор считается один раз, даже если повторяется в соседних сезонах
    after_names = {}
    for yr in after_seasons:
        F = funnel(apply_documents(load_layer(args.city, yr), args.city, yr), m.layers[f"monitoring_{yr}"].threshold)
        uniq_conf.update({r["id"]: r["population"] for r in F["confirmed"]})
        uniq_constr.update({r["id"]: r["population"] for r in F["construction"]})
        after_rows += (f"<tr><td>лето {yr}</td><td class='num'>{len(F['lost'])}</td>"
                       f"<td class='num'>{len(F['construction'])}</td><td class='num'>{len(F['confirmed'])}</td>"
                       f"<td class='num'>{len(F['unconfirmed'])}</td><td class='num'>{len(F['gained'])}</td></tr>")
        for kind, rows_k in (("потеря кроны", F["confirmed"]), ("стройка", F["construction"])):
            for r in rows_k:
                note = NOTES.get((args.city, yr, r["id"]), {})
                why = note.get("short") or ("по документам — стройплощадка" if r.get("instrument_label") else
                                            "застройка выросла по второму прибору" if kind == "стройка" else
                                            "причина не установлена")
                nm = r["name"] if r["name"] and r["name"] != r["id"] else "без названия"
                after_names[r["id"]] = nm
                named_rows += (f"<tr><td>{yr}</td><td>{esc(kind)}</td><td><code>{esc(r['id'])}</code> {esc(nm)}</td>"
                               f"<td class='num'>{r['effect']:+.3f}</td><td class='num'>{fmt_int(r['population'])}</td>"
                               f"<td>{esc(why)}</td></tr>")
    def people(ids_pop):
        pop = sum(ids_pop.values())
        return "в парковых секторах без жителей" if pop == 0 else f"{fmt_int(pop)} жителей"
    def sectors(n):
        return f"{n} {'сектор' if n % 10 == 1 and n % 100 != 11 else 'сектора' if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else 'секторов'}"
    after_summary = (f"За {len(after_seasons)} {'сезон' if len(after_seasons) == 1 else 'сезона'} после базы: "
                     f"{sectors(len(uniq_constr))} со стройкой ({people(uniq_constr)}) и "
                     + (f"{sectors(len(uniq_conf))} с подтверждённой потерей кроны ({people(uniq_conf)})."
                        if uniq_conf else "ни одной подтверждённой потери кроны."))
    if after_seasons:
        after_html = f"""
<section>
  <div class="sec-head"><span class="eyebrow">После базы</span><h2>Что случилось с зеленью после 2024 года</h2></div>
  <div class="col"><p>Каждое лето после базы сравнивается с тремя предыдущими против подобранного контроля, со своим порогом сезона. Потеря кроны называется, только если её видят два прибора; причина ищется по документам. Для статьи 8 стройка на зелени — тоже потеря: закон считает площадь зелени и кроны, а не её состояние.</p></div>
  <div class="scroll"><table><thead><tr><th>сезон</th><th>кандидатов</th><th>стройка</th><th>потеря кроны</th><th>не подтверждено</th><th>прибавили</th></tr></thead><tbody>{after_rows}</tbody></table></div>
  {'<div class="scroll"><table><thead><tr><th>сезон</th><th>что</th><th>сектор</th><th>эффект NDVI</th><th>жителей</th><th>причина</th></tr></thead><tbody>' + named_rows + '</tbody></table></div>' if named_rows else ''}
  <div class="callout col"><p><strong>{after_summary}</strong> Сектор считается один раз, даже если повторяется в соседних сезонах: база каждого сезона — три предыдущих лета, и событие остаётся в ней, пока не выйдет из окна.</p></div>
  <div class="warn col"><p><strong>Это годовой сигнал, а не чистая потеря в гектарах.</strong> Закон меряет площадь зелени раз в шесть лет; здесь — где и когда искать изменения, чтобы к 2030 году не узнать о них из итоговой цифры. Прирост зелени вторым прибором не проверяется и поимённо не публикуется.</p></div>
</section>"""
    else:
        after_html = ""

    # ── Исключение ст. 8(1) по методике Комиссии ──────────────────────────────
    # Слой считает scripts/official/art8_official.py: наборы данных из FAQ регламента,
    # расчёт как в скрипте EEA/JRC NRR_Art8. Здесь только чтение и подача.
    off_path = root / "art8_official_2021_summary.json"
    excl_html, excl_sources = "", ""
    law_warn = ("Освобождён ли город по порогу «45 % зелени и 10 % кроны», решает делинеация городских "
                "экосистем государством — её пока нет.")
    if off_path.exists():
        O = json.loads(off_path.read_text())
        laus = sorted(O["laus"], key=lambda r: -(r["green_ucuc"] or 0))
        ex = [r for r in laus if r["exempt"]]
        unstable = [r for r in laus if not r["stable"]]

        def pc(v):
            return "—" if v is None else f"{100 * v:.1f} %"

        from engine.adapters.brussels import REFNIS
        lau_short = {"BE_11002": "Antwerpen", **{f"BE_{k}": v for k, v in REFNIS.items()}}

        def short(r):
            # В GISCO порядок языков в названии не единый (Forest идёт вторым), поэтому
            # имена — из того же справочника, что на остальных страницах.
            return lau_short.get(r["lau_id"]) or r["name"].split(" / ")[0]

        excl_rows = ""
        for r in laus:
            verdict = ("<span class='tag t-gain'>проходит</span>" if r["exempt"]
                       else "<span class='tag t-loss'>не проходит</span>")
            if not r["stable"]:
                verdict += " <span class='tag t-mute'>зависит от прочтения</span>"
            excl_rows += (f"<tr><td>{esc(short(r))}</td><td class='num'>{r['area_km2_ucuc']:.1f}</td>"
                          f"<td class='num'><strong>{pc(r['green_ucuc'])}</strong></td>"
                          f"<td class='num'>{pc(r['green_with7_ucuc'])}</td><td class='num'>{pc(r['green_no_water_ucuc'])}</td>"
                          f"<td class='num'>{pc(r['green_ucuc_statbel'])}</td>"
                          f"<td class='num'>{pc(r['canopy_wvl_ucuc'])}</td><td>{verdict}</td></tr>")
        reg = O["region"]["parts"]["ucuc"]
        if len(laus) > 1:
            excl_rows += (f"<tr><td><strong>все {len(laus)} как одна экосистема</strong></td>"
                          f"<td class='num'>{reg['area_km2']:.1f}</td><td class='num'><strong>{pc(reg['green'])}</strong></td>"
                          f"<td class='num'>{pc(reg['green_with7'])}</td><td class='num'>{pc(reg['green_no_water'])}</td>"
                          f"<td class='num'>—</td><td class='num'>{pc(reg['canopy_wvl'])}</td>"
                          f"<td>{'<span class=\"tag t-gain\">проходит</span>' if O['region']['exempt'] else '<span class=\"tag t-loss\">не проходит</span>'}</td></tr>")

        if len(laus) == 1:
            r = laus[0]
            head = (f"{esc(short(r))} исключение {'проходит' if r['exempt'] else 'не проходит'}: "
                    f"зелени в городских клетках {pc(r['green_ucuc'])} при пороге 45 %")
        else:
            head = (f"Исключение проходят {len(ex)} коммуны из {len(laus)}, "
                    f"{'регион целиком — тоже' if O['region']['exempt'] else 'регион целиком — нет'}")

        # Последствие: что уходит из итога, если государство исключит всё, что может.
        consequence = ""
        if ex and len(laus) > 1:
            area_all = sum(r["area_km2_all"] for r in laus)
            area_ex = sum(r["area_km2_all"] for r in ex)
            pop_all = sum(r["population"] or 0 for r in laus)
            pop_ex = sum(r["population"] or 0 for r in ex)
            rest = [r for r in laus if not r["exempt"]]
            w = sum(r["area_km2_ucuc"] for r in rest)
            rest_green = sum(r["green_ucuc"] * r["area_km2_ucuc"] for r in rest) / w if w else None
            woody_all = sum(r["canopy_wvl_all"] * r["area_km2_all"] for r in laus)
            woody_ex = sum(r["canopy_wvl_all"] * r["area_km2_all"] for r in ex)
            ex_codes = {r["lau_id"][3:] for r in ex}
            in_ex = [i for i in list(uniq_constr) + list(uniq_conf) if i[:5] in ex_codes]
            events = ""
            if uniq_constr or uniq_conf:
                n_ev = len(uniq_constr) + len(uniq_conf)
                who = ", ".join(f"{after_names.get(i, i)} ({REFNIS.get(i[:5], i[:5])})" for i in in_ex)
                events = (f" Из {n_ev} секторов со стройкой или потерей кроны после базы (раздел ниже) "
                          + (f"{len(in_ex)} {'лежит' if len(in_ex) % 10 == 1 and len(in_ex) % 100 != 11 else 'лежат'} "
                             f"в коммунах, которые можно исключить, — {esc(who)}: такие потери выпадут из "
                             "национального итога вместе с коммуной." if in_ex else
                             "ни один не лежит в коммунах, которые можно исключить."))
            consequence = (
                f'<div class="callout col"><p><strong>Если исключить всё, что можно, из итога уйдёт '
                f'{100 * area_ex / area_all:.0f} % площади и {100 * pop_ex / pop_all:.0f} % жителей</strong> — '
                f"{', '.join(esc(short(r)) for r in ex)}: самые зелёные коммуны, в них {100 * woody_ex / woody_all:.0f} % "
                f"древесной растительности региона. Обязательство нулевой чистой потери останется на {len(rest)} плотных коммунах, где зелени "
                f"в городских клетках в среднем {pc(rest_green)}.{events}</p></div>")

        corr = O.get("correlations_canopy", {})
        corr_txt = ""
        if corr:
            names = {"worldcover_2021": "WorldCover", "article8_2024": "нашим классом trees",
                     "canopy_probav_2019": "Proba-V"}
            corr_txt = (" По секторам официальная крона ранжирует так же, как наши приборы: "
                        + ", ".join(f"r = {v['r']:.2f} с {names.get(k, k)}" for k, v in corr.items()) + ".")
        chk = O.get("checks", {})
        tcd_txt = ""
        if "tcd_2018_published" in chk:
            tcd_txt = (f"<li>Регион публикует крону «{100 * chk['tcd_2018_published']:.0f} % по Copernicus, 2018». "
                       f"По слою Tree Cover Density 2018 внутри 19 коммун доля пикселей с любой кроной — "
                       f"{100 * chk['tcd_2018_region_share_any']:.1f} %, средняя плотность — "
                       f"{100 * chk['tcd_2018_region_mean_density']:.1f} %. Точно не сходится; как считал регион, "
                       "не опубликовано.</li>")
        law_warn = ("Исключать ли коммуны и объединять ли их в одну экосистему, решает государство; ниже — только "
                    "расчёт по методике Комиссии.")
        no_exact = [r for r in laus if r["green_ucuc_statbel"] is None]
        if len(laus) == 1:
            robust_txt = ("Две проверки устойчивости: пашня засчитана как зелень, вода не засчитана. "
                          + ("Вердикт не меняется. " if not unstable else "Вердикт зависит от прочтения. ")
                          + ("Проверка на точных границах Statbel не сделана: в пакете нет секторов порта."
                             if no_exact else ""))
        else:
            robust_txt = ("Три проверки устойчивости: пашня засчитана как зелень; вода не засчитана; коммуна собрана "
                          "из секторов Statbel вместо обобщённых границ 1:1M"
                          + (" (где пакет покрывает коммуну целиком)" if no_exact else "") + ". "
                          + ("Вердикт не меняется ни в одной коммуне." if not unstable else
                             f"Вердикт зависит от прочтения в {len(unstable)} коммунах — они помечены."))
        excl_html = f"""
<section>
  <div class="sec-head"><span class="eyebrow">Исключение ст. 8(1) · методика Комиссии</span><h2>{head}</h2></div>
  <div class="col"><p>Городскую экосистему можно не включать в национальный итог, если в её <strong>городских центрах и кластерах</strong> зелень больше 45 % и крона больше 10 %. Считали теми наборами данных, которые назвала Комиссия: зелень — CLCplus Backbone, крона — Woody Vegetation Layer, клетки центров и кластеров — сетка Евростата 1 км² 2021 года, единица — LAU 2024. Расчёт повторяет официальный скрипт EEA и JRC. В Бельгии LAU — это коммуна; {'у всех ' + str(len(laus)) + ' класс урбанизации' if len(laus) > 1 else 'класс урбанизации'} — «город».</p></div>
  <div class="scroll"><table><thead><tr><th>коммуна</th><th>в центрах и кластерах, км²</th><th>зелень</th><th>с пашней</th><th>без воды</th><th>точные границы</th><th>крона</th><th>исключение</th></tr></thead>
  <tbody>{excl_rows}</tbody></table></div>
  <div class="col"><p>{robust_txt}{corr_txt}</p></div>
  {consequence}
  <div class="warn col"><ul>
    <li>Зелень — по CLCplus 2021, регламент называет 2023 год; на открытом сервере EEA есть только 2021. Крона — по WVL 2021: FAQ разрешает его для черновиков планов, для окончательных нужен WVL 2024, его раздают только представителям стран.</li>
    <li>Какие классы CLCplus считать зеленью по ст. 3(20), — наше прочтение: деревья, кусты, постоянные травы, мхи, вода. Официальная таблица соответствия закрыта логином, поэтому вердикт перепроверен при двух соседних прочтениях.</li>
    {tcd_txt}
    <li>Это уровень одного года, а не изменение: порог исключения — правило закона, не порог шума.</li>
  </ul></div>
</section>"""
        excl_sources = (
            "<tr><td>исключение ст. 8(1): зелень</td><td>Copernicus CLCplus Backbone, 10 м</td><td>2021</td></tr>"
            "<tr><td>исключение ст. 8(1): крона</td><td>Copernicus HRL Woody Vegetation Layer, 5 м; сверка — Tree Cover Density, 10 м</td><td>2021; 2018</td></tr>"
            "<tr><td>городские центры и кластеры, LAU</td><td>Евростат: сетка 1 км², LAU 2024 (GISCO 1:1M), DEGURBA 2024</td><td>2021; 2024</td></tr>")

    doc = f"""<title>Статья 8 · {esc(cfg['display_name'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>{CSS}</style>
<div class="page">
<header class="masthead">
  <div class="eyebrow">Регламент (EU) 2024/1991 · статья 8 · городские экосистемы</div>
  <h1>База 2024: {esc(cfg['display_name'])}</h1>
  <p class="standfirst">Уровень городской зелени и древесной кроны на базовый 2024 год по {fmt_int(S['units_measured'])} статистическим секторам, тренд, с которым город к базе подошёл, и где потери сидят по доходу. Каждое число ведёт к источнику; границы применимости напечатаны рядом с числами.</p>
  <div class="dateline"><span>снимки: Sentinel-2, Dynamic World</span><span>единица: сектор Statbel</span><span>окно тренда: {esc(S['window'])}</span><span>сформировано {today_ru()}</span></div>
</header>

<section>
  <div class="sec-head"><span class="eyebrow">Что требует закон</span><h2>Нулевая чистая потеря к 2030 году относительно 2024-го</h2></div>
  <div class="col"><p>Статья 8 обязывает государство обеспечить, чтобы общая площадь городской зелени и древесной кроны в городских экосистемах к 31 декабря 2030 года не опустилась ниже уровня <strong>2024 года</strong>, а с 2031-го росла, с замером раз в шесть лет. Данные предписаны: Copernicus, покрытие земли. Этот документ фиксирует уровень 2024 года по секторам и показывает, откуда город к нему пришёл.</p></div>
  <div class="warn col"><p><strong>Что здесь не утверждается.</strong> {esc(law_warn)} Значения классов Dynamic World — средние вероятности, а не доли площади. Уровень сектора — не уровень отдельного вмешательства.</p></div>
</section>
{excl_html}

<section>
  <div class="sec-head"><span class="eyebrow">База 2024</span><h2>Уровни на летний сезон 2024, взвешено по населению</h2></div>
  <div class="stats">
    <div class="stat"><b>{b['ndvi_wmean']:.3f}</b><span>зелёность, NDVI · то, ниже чего нельзя опуститься</span></div>
    <div class="stat"><b>{b['trees_wmean']:.3f}</b><span>крона, вероятность класса trees · учитывается законом отдельно</span></div>
    <div class="stat"><b>{b['grass_wmean']:.3f}</b><span>травяной покров, класс grass</span></div>
    <div class="stat"><b>{b['built_wmean']:.3f}</b><span>застройка, класс built</span></div>
  </div>
  <div class="col"><p>Население в измеренных секторах — {fmt_int(S['population'])} человек. Уровни по каждому сектору — в приложенном слое <code>article8_2024.csv</code>; это и есть база, против которой считается чистая потеря.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Тренд к базе</span><h2>С какой динамикой город пришёл к 2024 году</h2></div>
  <div class="col"><p>Изменение {esc(S['window'])} по каждому сектору против двенадцати подобранных контрольных секторов — разность разностей. Значимым считается эффект за порогом, измеренным на нулевом распределении этого города: зелень <strong>{thr.get('ndvi', 0):.4f}</strong>{f", крона <strong>{thr['trees']:.4f}</strong>" if has_trees else ""}.</p></div>
  <div class="stats">
    <div class="stat"><b class="t-loss">{tr['ndvi_loss_sectors']}</b><span>секторов значимо потеряли зелень · {fmt_int(tr['ndvi_loss_pop'])} жителей</span></div>
    <div class="stat"><b class="t-gain">{tr['ndvi_gain_sectors']}</b><span>секторов значимо прибавили · {fmt_int(tr['ndvi_gain_pop'])} жителей</span></div>
    <div class="stat"><b class="t-loss">{tr['trees_loss_sectors'] if has_trees else '—'}</b><span>секторов значимо потеряли крону · {fmt_int(tr['trees_loss_pop']) if has_trees else '—'} жителей</span></div>
    <div class="stat"><b class="t-gain">{tr['trees_gain_sectors'] if has_trees else '—'}</b><span>секторов значимо прибавили крону · {fmt_int(tr['trees_gain_pop']) if has_trees else '—'} жителей</span></div>
  </div>
  <div class="col"><p>Медиана эффекта по сопоставимым секторам — {tr['ndvi_eff_median']:+.4f}: город в целом к базе {'зеленел' if tr['ndvi_eff_median'] > 0 else 'терял зелень'} относительно собственного контроля.</p></div>

  <h3>Где зелень ушла сильнее всего</h3>
  <div class="scroll"><table><thead><tr><th>сектор</th><th>коммуна</th><th>эффект NDVI</th><th>жителей</th><th>эффект кроны</th></tr></thead>
  <tbody>{loss_rows(S['top_ndvi_loss'])}</tbody></table></div>
  <div class="col"><p>Потеря зелени при неизменной кроне — трава или кустарник; потеря кроны — деревья. Стройка даёт рост класса built и вычитается из «потерь кроны» при проверке вторым прибором.</p></div>
</section>

{after_html}

<section>
  <div class="sec-head"><span class="eyebrow">Справедливость</span><h2>Кому досталась зелень и у кого она уходит</h2></div>
  <div class="col"><p>Закон молчит о распределении. Индикатор SDG 11.7 и Tree Equity Score — нет. Секторы разбиты на терцили по медианному облагаемому доходу сектора (Statbel, 2023).</p></div>
  <div class="scroll"><table><thead><tr><th>терциль дохода</th><th>медиана дохода</th><th>NDVI 2024</th><th>крона 2024</th><th>тренд NDVI</th><th>потерь</th><th>приростов</th></tr></thead>
  <tbody>{tercile_rows()}</tbody></table></div>
  <div class="callout col"><p>{esc(equity_line)}</p></div>
  {age_html}
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Норма и жара</span><h2>Три независимые проверки состояния</h2></div>
  {extra_html}
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Метод</span><h2>Как это посчитано и почему числу можно верить</h2></div>
  <div class="col"><ul>
    <li><strong>Разность разностей.</strong> Эффект = (объект после − до) − (контроль после − до). {esc(bg_sentence(args.city))}</li>
    <li><strong>Контроль подобранный, не соседний.</strong> {CONTROL['n_controls']} секторов, похожих на объект по состоянию до периода, не ближе {CONTROL['exclusion_m']} м — соседство не гарантирует сопоставимости.</li>
    <li><strong>Порог измерен, не назначен.</strong> Каждый сектор по очереди играет «вмешательство»; распределение эффектов — нулевое; порог — его 95-й процентиль. Считается тем же прогоном, что и эффекты этого отчёта — тот же подбор, те же снимки: зелень <strong>{thr.get('ndvi', 0):.4f}</strong>{f", крона <strong>{thr['trees']:.4f}</strong>" if has_trees else ''}. {'Среднее нулевого распределения около нуля: метод не смещён.' if all((S.get('thresholds_unbiased') or {}).values()) else 'Нулевое распределение смещено — вердикты тренда недействительны.'} В таблице ниже — пороги приборов: ими меряются аудиты отдельных вмешательств.</li>
    <li><strong>Отказ — результат.</strong> Если контроль отличается от объекта по исходной зелёности больше {CONTROL['max_gap_ndvi']}, вердикт не выносится. Меньше {QUALITY['min_scenes']} сцен в окне — результат предварительный.</li>
  </ul></div>
  <div class="scroll"><table><thead><tr><th>слой</th><th>что меряет</th><th>порог</th><th>происхождение порога</th></tr></thead>
  <tbody>{layer_rows()}</tbody></table></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Границы применимости</span><h2>Чего этот отчёт не измеряет</h2></div>
  <div class="col"><ul>{"".join(f"<li>{esc(l)}</li>" for l in LIMITS)}
    <li>значения классов Dynamic World — вероятности, не доли площади: абсолютные величины не интерпретировать, только изменение</li>
    <li>уровень сектора не равен уровню вмешательства: рассеянные посадки тонут в площади сектора</li>
  </ul></div>
  <div class="stats">
    <div class="stat"><b>{S['units_measured']}</b><span>секторов измерено из {S['units_total']}</span></div>
    <div class="stat"><b>{refused}</b><span>отказ: контроль несопоставим</span></div>
    <div class="stat"><b>{not_measured}</b><span>не измерено: мельче {CONTROL['min_area_ha']:.0f} га или нет данных</span></div>
  </div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Источники</span><h2>Откуда каждое число</h2></div>
  <div class="scroll"><table><thead><tr><th>что</th><th>источник</th><th>период</th></tr></thead><tbody>
    <tr><td>зелёность (NDVI)</td><td>Copernicus Sentinel-2 SR Harmonized, летние медианы, маска Cloud Score+</td><td>2017–2024</td></tr>
    <tr><td>крона, трава, застройка</td><td>Google Dynamic World V1 по Sentinel-2, 10 м, летние средние</td><td>2017–2024</td></tr>
    <tr><td>секторы, население</td><td>Statbel, статистические секторы</td><td>2024</td></tr>
    <tr><td>доход</td><td>Statbel TF_PSNL_INC_TAX_SECTOR, медианный облагаемый доход</td><td>2023</td></tr>
    <tr><td>пороги</td><td>нулевое распределение метода по секторам этого города, <code>cities/{esc(args.city)}/manifest.json</code></td><td>2026-09</td></tr>
    {excl_sources}
  </tbody></table></div>
  <p class="foot">Доказательство фиксировано, подача настраивается: числа, пороги и контроль не меняются ни при какой редакции текста. Текст этой версии шаблонный; редакция под критерии конкретной программы и на FR/NL — при подключении языковой модели, которая числа не считает.</p>
</section>
</div>
"""
    out = SCRATCH / f"article8-{args.city}.html"
    out.write_text(doc, encoding="utf-8")
    print(f"→ {out}  ({len(doc) // 1024} КБ)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
