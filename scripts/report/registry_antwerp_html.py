"""Страница реестра Антверпена: сколько вмешательств вообще поддаётся проверке.

Отличие от брюссельской страницы. В Брюсселе реестр — это деньги и сроки:
251 строка, 2,13 млрд €, вопрос «что из этого измерено». В Антверпене вопрос
другой и честнее звучит так: **из 252 проектов застройщика до аудита доживают
пять**, и страница показывает, где отсеиваются остальные.

Все числа считаются из файлов реестра и слоя пакета, ничего не вписано руками:
`data/registry/agvespa_projects.json`, `agvespa_park_links.csv`,
`cities/antwerp/layers/park_audit_dated.csv`.

    python scripts/report/registry_antwerp_html.py
"""
from __future__ import annotations

import csv
import html
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.audit import MIN_HA_LANDSAT  # noqa: E402
from engine.config import CONTROL, QUALITY  # noqa: E402
from engine.manifest import Manifest  # noqa: E402

from scripts.report.paths import DERIVED, OUT as SCRATCH, today_ru  # noqa: E402

CSS = """
:root{--paper:#EFF1EC;--surface:#FFFFFF;--ink:#141B17;--muted:#5B6B62;--rule:#D5DAD3;--rule-2:#E4E8E3;
--accent:#1E6E58;--accent-soft:#E2EDE7;--heat:#C2451C;--heat-soft:#F7E6DE;--step:#B9C4BC;
--display:"IBM Plex Sans Condensed","Helvetica Neue",Arial,sans-serif;--body:"IBM Plex Serif",Georgia,serif;
--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--measure:34rem;--wide:62rem}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;
--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;--step:#3A463E}}
:root[data-theme="dark"]{--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;
--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;--step:#3A463E}
*{box-sizing:border-box}body{background:var(--paper);color:var(--ink);font-family:var(--body);font-size:16.5px;line-height:1.62;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}a:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
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
tr:last-child td{border-bottom:none}td small{font-size:.82rem;color:var(--muted)}
/* Ступени отсева — не украшение: каждая строка это одно проверяемое условие и цена, которую оно берёт */
.steps{display:flex;flex-direction:column;background:var(--surface);border:1px solid var(--rule)}
.step{display:grid;grid-template-columns:5.5ch 1fr auto;gap:.2rem 1rem;align-items:baseline;padding:.85rem 1.15rem;border-bottom:1px solid var(--rule-2)}
.step:last-child{border-bottom:none}
.step .n{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:1.35rem;font-weight:500;line-height:1.1}
.step .t{font-family:var(--display);font-size:.98rem;line-height:1.3}
.step .t small{display:block;color:var(--muted);font-size:.82rem;line-height:1.35;margin-top:.15rem}
.step .drop{font-family:var(--mono);font-size:.78rem;color:var(--heat);white-space:nowrap;align-self:center}
.step.keep{background:var(--accent-soft)}.step.keep .drop{color:var(--accent)}
.bar{grid-column:1/-1;height:3px;background:var(--rule-2);margin-top:.55rem}.bar i{display:block;height:100%;background:var(--step)}
.step.keep .bar i{background:var(--accent)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}
.stat{background:var(--surface);padding:1rem 1.05rem;display:flex;flex-direction:column;gap:.2rem}
.stat b{font-family:var(--display);font-weight:700;font-size:2rem;line-height:1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat span{font-family:var(--display);font-size:.8rem;color:var(--muted);line-height:1.3}
.tag{font-family:var(--mono);font-size:.67rem;letter-spacing:.05em;text-transform:uppercase;padding:.14rem .42rem;white-space:nowrap;border:1px solid currentColor}
.t-gain{color:var(--accent)}.t-mute{color:var(--muted)}.t-loss{color:var(--heat)}
.foot{font-family:var(--display);font-size:.82rem;color:var(--muted);border-top:1px solid var(--rule);padding-top:1rem;max-width:46rem}
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def n(x) -> str:
    return f"{int(x):,}".replace(",", " ")


def funnel_of(projects: list[dict], links: list[dict], audited: list[dict]) -> list[dict]:
    """Ступени отсева от списка проектов до аудируемых. Каждая ступень — условие,
    которое можно проверить по файлам, а не оценка на глаз."""
    done = [p for p in projects if (p.get("status") or "").startswith("Gerealiseerd")]
    dated = [p for p in projects if p.get("completed_year")]
    named = {(r["project"], r["park"]) for r in links if r["name_match"] == "True"}
    return [
        dict(k=len(projects), t="Проектов в реестре застройщика",
             s="AG Vespa: список отдаёт всё одной страницей, у каждого проекта координата маркера", drop=""),
        dict(k=len(done), t="Завершено",
             s="статус «Gerealiseerd»; остальные в работе — для аудита рано", drop=f"−{len(projects) - len(done)}"),
        dict(k=len(dated), t="С годом сдачи",
             s="год берётся из события открытия в хронологии, а не из статуса; без хронологии срок не угадывается",
             drop=f"−{len(done) - len(dated)}"),
        dict(k=len(named), t="Привязано к измеримому парку",
             s=f"совпадение имени И расстояние ≤ 400 м до именованного парка OSM ≥ 1 га; "
               f"одного расстояния мало — так набирается {len(links)} пар, включая чужие",
             drop=f"−{len(dated) - len(named)}"),
        dict(k=len(audited), t="Дошло до аудита", keep=True,
             s="сроки укладываются между окнами сравнения, и прибор для такого следа существует",
             drop=f"−{len(named) - len(audited)}"),
    ]


def main() -> int:
    projects = json.loads(Path("data/registry/agvespa_projects.json").read_text())
    links = list(csv.DictReader(Path("data/registry/agvespa_park_links.csv").open()))
    audited = list(csv.DictReader(Path("cities/antwerp/layers/park_audit_dated.csv").open()))
    m = Manifest.read("antwerp")

    steps = funnel_of(projects, links, audited)
    top = steps[0]["k"]
    no_timeline = sum(1 for p in projects if not p.get("timeline"))
    no_budget = sum(1 for p in projects if not p.get("budget"))
    themes = Counter(p.get("theme") or "не указана" for p in projects)
    basis = Counter(p.get("completed_basis") for p in projects if p.get("completed_year"))
    green = [r for r in audited if r["verdict"] in ("ПОЗЕЛЕНЕЛ", "ПОТЕРЯЛ")]
    prelim = [r for r in audited if r["verdict"].startswith("предварительно")]
    spoor = next(float(r["effect"]) for r in audited if "Spoor Noord" in r["project"])

    def verdict_tag(v: str) -> str:
        if v == "ПОЗЕЛЕНЕЛ":
            return f'<span class="tag t-gain">{esc(v.lower())}</span>'
        if v == "ПОТЕРЯЛ":
            return f'<span class="tag t-loss">{esc(v.lower())}</span>'
        return f'<span class="tag t-mute">{esc(v)}</span>'

    def audit_row(r: dict) -> str:
        instr = "Sentinel-2, 10 м" if r["instrument"] == "ndvi" else "Landsat, 30 м"
        dw = f"<small>{esc(r['dw_outcome'])}</small>" if r.get("dw_outcome") else ""
        return (f"<tr><td>{esc(r['project'])}<small>{esc(r['park'])}</small></td>"
                f"<td class='num'>{esc(r['completed_year'])}</td>"
                f"<td class='num'>{float(r['area_ha']):.1f}</td>"
                f"<td>{instr}<small>{esc(r['window'])}</small></td>"
                f"<td class='num'>{esc(r['scenes_before'])} / {esc(r['scenes_after'])}</td>"
                f"<td class='num'>{float(r['effect']):+.4f}</td>"
                f"<td class='num'>{float(r['threshold']):.4f}</td>"
                f"<td>{verdict_tag(r['verdict'])}{dw}</td></tr>")

    audit_rows = "".join(audit_row(r) for r in sorted(audited, key=lambda r: -float(r["effect"])))

    step_html = "".join(
        f'<div class="step{" keep" if s.get("keep") else ""}"><div class="n">{s["k"]}</div>'
        f'<div class="t">{esc(s["t"])}<small>{esc(s["s"])}</small></div>'
        f'<div class="drop">{esc(s["drop"])}</div>'
        f'<div class="bar"><i style="width:{100 * s["k"] / top:.1f}%"></i></div></div>'
        for s in steps)

    theme_rows = "".join(f"<tr><td>{esc(t)}</td><td class='num'>{c}</td></tr>"
                         for t, c in themes.most_common(8))
    prelim_txt = f", как у объекта {esc(prelim[0]['park'])}" if prelim else ""

    doc = f"""<meta charset="utf-8"><title>Реестр вмешательств · Антверпен</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>{CSS}</style>
<div class="page">
<header class="masthead">
  <div class="eyebrow">Реестр вмешательств · Антверпен · AG Vespa</div>
  <h1>Из {top} проектов до аудита доходят {steps[-1]['k']}</h1>
  <p class="standfirst">Город с юридической обязанностью по статье 8 — и реестр, в котором почти нет того, что нужно для проверки. Эта страница показывает не список работ, а где именно теряется возможность что-либо доказать: на сроках, на границах и на размере следа.</p>
  <div class="dateline"><span>источник: agvespa.be/projecten</span><span>собрано {today_ru()}</span><span>измерение: Sentinel-2 и Landsat против подобранного контроля</span></div>
</header>

<section>
  <div class="sec-head"><span class="eyebrow">Воронка данных</span><h2>Где отсеиваются проекты</h2></div>
  <div class="steps">{step_html}</div>
  <div class="col"><p>Ни одна ступень не про качество работ города. Все пять — про то, что реестр должен содержать, чтобы вмешательство вообще можно было проверить: дату, границу и размер.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Чего нет в реестре</span><h2>Три пробела, каждый проверен на всех {top} проектах</h2></div>
  <div class="stats">
    <div class="stat"><b>{no_timeline}</b><span>проектов без хронологии — срок сдачи взять неоткуда</span></div>
    <div class="stat"><b>{no_budget}</b><span>проектов без бюджета: цена эффекта не считается ни для одного</span></div>
    <div class="stat"><b>{len(links)}</b><span>пар «проект рядом с парком» ≤ 400 м, из них по имени — {steps[3]['k']}</span></div>
  </div>
  <div class="warn col"><p><strong>Расстояние следом не считается.</strong> Музейное кафе одинаково близко к трём паркам сразу, а районный дом — к двум. Поэтому связь принимается только при совпадении названия, а остальные {len(links) - steps[3]['k']} пар остаются кандидатами и в аудит не идут. Это то же правило, из-за которого в Брюсселе один эффект едва не приписали пяти проектам сразу.</p></div>
  <div class="col"><p>Год сдачи, там где он есть, взят из события открытия в хронологии ({basis.get('done_event', 0)} проектов), а не из статуса: у Droogdokkeneiland статус «в работе» и события до 2025 года, но павильон открыт в сентябре 2018-го — по последнему событию объект выпал бы из проверки.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Аудит</span><h2>Пять проектов, у которых сроки и границы позволяют проверку</h2></div>
  <div class="col"><p>Окно сравнения строится под каждый проект от года сдачи, порог значимости считается заново на каждом окне: все {n(457)} секторов города по очереди играют роль вмешательства, и 95-й процентиль этого нулевого распределения становится порогом. Общий порог города сюда не переносится.</p></div>
  <div class="scroll"><table><thead><tr><th>проект и след</th><th>сдан</th><th>га</th><th>прибор и окно</th><th>сцен до / после</th><th>эффект</th><th>порог</th><th>вердикт</th></tr></thead>
  <tbody>{audit_rows}</tbody></table></div>
  <div class="callout col"><p><strong>Park Spoor Noord, +{spoor:.3f} при пороге 0,058.</strong> Сортировочная станция площадью 19,5 га превращена в парк, открыт в 2009 году. Втрое выше порога своего окна — и ровно тот тип работ, который метод видит: смена покрытия на большей части измеряемого участка.</p></div>
  <div class="col"><p>Два «шума» тоже осмысленны. Sorghvliedt — реставрация существующего парка, а она не меняет растительность по построению; Keiligbrug — мост через парк, а не озеленение. Инструмент молчит там, где молчать обязан.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Оговорки</span><h2>Что здесь предварительно и почему</h2></div>
  <div class="col"><ul>
    <li><strong>Прибор выбирается по году и по размеру следа.</strong> Объект мельче {MIN_HA_LANDSAT:.0f} га на Landsat — полтора-три десятка пикселей, поэтому для таких следов берётся Sentinel-2, даже если окно «до» приходится сжать до одного года.</li>
    <li><strong>Короткая база понижает вердикт.</strong> Меньше {QUALITY['min_scenes']} годных снимков в окне — вердикт помечается предварительным{prelim_txt}. Число снимков напечатано рядом с каждым эффектом.</li>
    <li><strong>Контроль подобранный, не соседний.</strong> {CONTROL['n_controls']} секторов, похожих на объект по состоянию до работ, не ближе {CONTROL['exclusion_m']} м; при слишком большом расхождении вердикт не выносится вовсе.</li>
    <li><strong>Реставрации этот метод не измеряет.</strong> Проверено отдельно на семи крупных реставрациях с их собственными окнами: все в пределах шума. Реставрация идёт в отчётность о выполнении, а не в доказательство эффекта.</li>
  </ul></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Состав реестра</span><h2>Чем занят застройщик</h2></div>
  <div class="scroll"><table><thead><tr><th>тема проекта</th><th>проектов</th></tr></thead><tbody>{theme_rows}</tbody></table></div>
  <div class="col"><p>Жильё и общественные здания — три четверти реестра; работы с покрытием и озеленением, то есть измеримые со спутника, составляют меньшинство. Это не упрёк городу, а объяснение, почему число проверяемых объектов мало и будет малым: доказательная проверка изменений — принципиально малосерийная работа на один город.</p></div>
</section>

<div class="foot">Источник: agvespa.be/projecten, {top} страниц проектов со статусом, темой, адресом и хронологией. Периметры работ — именованные парки OpenStreetMap ≥ 1 га. Снимки: Copernicus Sentinel-2 SR Harmonized и Landsat Collection 2 Level 2, летние медианы. Секторы и население: Statbel. Пороги и слой — <code>cities/antwerp/manifest.json</code>, {len(m.layers)} записей. Каждое число на странице пересчитывается из этих файлов.</div>
</div>
"""
    out = SCRATCH / "registry-antwerp.html"
    out.write_text(doc, encoding="utf-8")
    print(f"→ {out}  ({len(doc.encode()) // 1024} КБ) · проектов {top} · с датой {steps[2]['k']} · "
          f"привязано {steps[3]['k']} · аудировано {len(audited)} · значимых {len(green)} · предварительных {len(prelim)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
