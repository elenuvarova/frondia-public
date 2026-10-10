#!/usr/bin/env python3
"""
Публичная страница аудита одного вмешательства — экран 2 из вайрфреймов.

Что это
───────
Страница-доказательство, которой делятся. Одна колонка, читается сверху вниз,
без входа. Порядок намеренный: паспорт → снимки до/после → эффект с порогом →
второй прибор → контроль поимённо → проверка на устойчивость → метод → границы.
Призыв — один, внизу: сначала доказать, потом предложить.

Что фиксировано, что настраивается
──────────────────────────────────
Всё дело лежит в JSON: числа, пороги, контроль, снимки. Генератор его не меняет.
Настраивается только подача. Ни одна цифра на странице не появляется мимо дела.

Запуск:
    .venv/bin/python scripts/report/audit_html.py --case data/registry/cases/ninove.json
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.report.paths import DERIVED, OUT as SCRATCH  # noqa: E402
from scripts.report.background import sentence as bg_sentence  # noqa: E402

CSS = """
:root{--paper:#EFF1EC;--surface:#FFFFFF;--ink:#141B17;--muted:#5B6B62;--rule:#D5DAD3;--rule-2:#E4E8E3;
--accent:#1E6E58;--accent-soft:#E2EDE7;--heat:#C2451C;--heat-soft:#F7E6DE;
--display:"IBM Plex Sans Condensed","Helvetica Neue",Arial,sans-serif;--body:"IBM Plex Serif",Georgia,serif;
--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--measure:34rem;--wide:56rem}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;
--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14}}
:root[data-theme="dark"]{--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;
--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14}
*{box-sizing:border-box}body{background:var(--paper);color:var(--ink);font-family:var(--body);font-size:16.5px;line-height:1.62;-webkit-font-smoothing:antialiased}
.page{max-width:var(--wide);margin:0 auto;padding:3.5rem 1.5rem 6rem;display:flex;flex-direction:column;gap:2.75rem}
.col{max-width:var(--measure)}.masthead{display:flex;flex-direction:column;gap:.9rem;padding-bottom:1.75rem;border-bottom:2px solid var(--ink)}
.eyebrow{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
h1{font-family:var(--display);font-weight:700;font-size:clamp(2.3rem,7vw,3.8rem);line-height:.98;letter-spacing:-.02em;margin:0;text-wrap:balance}
.passport{display:flex;flex-wrap:wrap;gap:.45rem}.chip{font-family:var(--mono);font-size:.72rem;border:1px solid var(--rule);padding:.25rem .55rem;white-space:nowrap}
.chip a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}
section{display:flex;flex-direction:column;gap:1rem}.sec-head{display:flex;flex-direction:column;gap:.3rem;border-top:1px solid var(--rule);padding-top:.85rem}
.sec-head .eyebrow{color:var(--accent)}h2{font-family:var(--display);font-weight:600;font-size:clamp(1.35rem,3.2vw,1.8rem);line-height:1.12;margin:0;text-wrap:balance}
p{margin:0}strong{font-weight:600}code{font-family:var(--mono);font-size:.86em}
ul{margin:0;padding-left:1.15rem;display:flex;flex-direction:column;gap:.45rem}li::marker{color:var(--muted)}
.callout{background:var(--accent-soft);border-left:3px solid var(--accent);padding:1rem 1.2rem;max-width:var(--measure)}
.warn{background:var(--heat-soft);border-left:3px solid var(--heat);padding:1rem 1.2rem;max-width:var(--measure)}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:.6rem}@media(max-width:40rem){.pair{grid-template-columns:1fr}}
.frame{position:relative;background:var(--surface);border:1px solid var(--rule)}.frame img{display:block;width:100%;height:auto}
.frame .corner{position:absolute;top:.5rem;left:.5rem;font-family:var(--mono);font-size:.68rem;letter-spacing:.06em;background:var(--surface);color:var(--ink);border:1px solid var(--rule);padding:.15rem .45rem}
figcaption{font-family:var(--display);font-size:.84rem;color:var(--muted);line-height:1.45;max-width:40rem}
figure{margin:0;display:flex;flex-direction:column;gap:.6rem}
.verdict{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1px;background:var(--rule);border:1px solid var(--rule)}
@media(max-width:40rem){.verdict{grid-template-columns:1fr}}
.verdict>div{background:var(--surface);padding:1rem 1.05rem;display:flex;flex-direction:column;gap:.2rem}
.verdict b{font-family:var(--display);font-weight:700;font-size:2.1rem;line-height:1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.verdict span{font-family:var(--display);font-size:.8rem;color:var(--muted);line-height:1.3}
.tag{font-family:var(--mono);font-size:.67rem;letter-spacing:.05em;text-transform:uppercase;padding:.14rem .42rem;white-space:nowrap;border:1px solid currentColor}
.t-sig{color:var(--accent)}.t-no{color:var(--muted)}
.scroll{overflow-x:auto;max-width:100%}table{border-collapse:collapse;width:100%;min-width:30rem;font-size:.9rem;font-family:var(--display);font-weight:500}
th{text-align:left;font-family:var(--mono);font-weight:500;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--ink);padding:0 .85rem .5rem 0;vertical-align:bottom}
td{border-bottom:1px solid var(--rule);padding:.55rem .85rem .55rem 0;vertical-align:top;line-height:1.4}td.num{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
tr:last-child td{border-bottom:none}
.cta{display:flex;flex-wrap:wrap;gap:1rem;align-items:center;justify-content:space-between;border-top:2px solid var(--ink);padding-top:1.5rem}
.cta p{max-width:30rem}.btn{font-family:var(--display);font-weight:600;background:var(--ink);color:var(--paper);padding:.7rem 1.2rem;text-decoration:none;white-space:nowrap}
.foot{font-family:var(--display);font-size:.82rem;color:var(--muted)}
"""


def esc(x) -> str:
    return html.escape(str(x))


def plural(n: int, one: str, few: str, many: str) -> str:
    n10, n100 = n % 10, n % 100
    return one if n10 == 1 and n100 != 11 else few if 2 <= n10 <= 4 and not 12 <= n100 <= 14 else many



def series_phrase(seasons: list[dict], thr: float) -> str:
    """Фраза о том, держится ли эффект, для трёх форм ряда.

    Раньше фраза знала одну форму — провал в конце — и у Park Spoor Noord напечатала
    «держится до 2026-го и в 2018 уходит в шум»: засуха 2018 года посреди ряда, после
    которой эффект вернулся. Формы: без провалов; провал только в конце; провалы
    посреди ряда, после которых эффект возвращается; и то и другое."""
    first = next((o["season"] for o in seasons if o["effect"] > thr), None)
    after = [o for o in seasons if o["season"] >= (first or 9999)]
    below = [o["season"] for o in after if o["effect"] <= thr]
    tail = []
    for o in reversed(after):
        if o["effect"] > thr:
            break
        tail.insert(0, o["season"])
    dips = [y for y in below if y not in tail]
    n = len(after)
    yrs = lambda ys: ", ".join(map(str, ys))
    if not below:
        return f"и держится все {n} {plural(n, 'сезон', 'сезона', 'сезонов')}"
    if not dips:
        last_up = max(o["season"] for o in after if o["effect"] > thr)
        return f"держится до {last_up}-го и в {yrs(tail)} уходит в шум"
    if not tail:
        k = n - len(dips)
        return (f"и держится {k} {plural(k, 'сезон', 'сезона', 'сезонов')} из {n}: "
                f"в шуме только {yrs(dips)}, после чего эффект возвращается")
    return f"держится {n - len(below)} из {n} сезонов: в шуме {yrs(dips)} посреди ряда и {yrs(tail)} в конце"


def img_uri(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    args = ap.parse_args()
    C = json.loads(Path(args.case).read_text())

    inst_rows = "\n".join(
        f"<tr><td>{esc(i['label'])}</td><td class='num'>{i['before']:.3f} → {i['after']:.3f}</td>"
        f"<td class='num'>{i['effect']:+.3f}</td><td class='num'>{i['threshold']:.4f}</td>"
        f"<td><span class='tag {'t-sig' if i['significant'] else 't-no'}'>{'значимо' if i['significant'] else 'в пределах шума'}</span></td>"
        f"<td>{esc(i.get('reading',''))}</td></tr>"
        for i in C["instruments"])

    ctrl_rows = "\n".join(
        f"<tr><td><code>{esc(c['id'])}</code></td><td>{esc(c['name']) if c['name'] != c['id'] else '<span class=\'t-no\'>без названия</span>'}</td><td class='num'>{c['ndvi_before']:.3f}</td>"
        f"<td class='num'>{c['d_ndvi_raw']:+.4f}</td><td class='num'>{c['dist_km']}</td></tr>"
        for c in C["controls"])

    doc_rows = "\n".join(
        f"<tr><td>{esc(d['what'])}</td><td>{esc(d['source'])}</td><td>{esc(d['detail'])}</td></tr>"
        for d in C["documents"])

    # Блок кластера печатается, только если кластер есть. Пустая таблица под
    # заголовком «эффект нельзя приписать одному проекту» утверждала бы то,
    # чего мы не проверяли для этого дела.
    cluster_rows = "\n".join(
        f"<tr><td>{esc(p['name'])}</td><td>{esc(p['domain'])}</td><td class='num'>{p['dist_m']} м</td></tr>"
        for p in C.get("cluster", []))

    tc = C["timing_check"]
    tc_rows = "\n".join(
        f"<tr><td>{esc(r['window'])}</td><td class='num'>{r['scenes']}</td><td class='num'>{r['ndvi_before']:.3f}</td>"
        f"<td class='num'>{r['effect']:+.4f}</td><td class='num'>{r['gap']:+.4f}</td></tr>"
        for r in tc["rows"])

    im = C["images"]
    main_i = C["instruments"][0]

    # Снимков может не быть, и это не повод рисовать пустые рамки: у дел на Landsat
    # участок в 20 га — примерно 15 на 15 пикселей, композит в человеческом виде
    # не строится. Причина печатается на месте картинки.
    b_uri, a_uri = img_uri(im.get("before", "")), img_uri(im.get("after", ""))
    if b_uri and a_uri:
        frames_html = (
            '<figure><div class="pair">'
            f'<div class="frame"><span class="corner">ДО · {esc(C["window_before"])}</span>'
            f'<img alt="композит до вмешательства" src="{b_uri}"></div>'
            f'<div class="frame"><span class="corner">ПОСЛЕ · {esc(C["window_after"])}</span>'
            f'<img alt="композит после вмешательства" src="{a_uri}"></div></div>'
            '<figcaption>Летние медианные композиты Sentinel-2, 10 м на пиксель. Жёлтый контур — полигон парка '
            'из OpenStreetMap: геометрия чужая, названная и версионированная, а не обведённая нами. '
            f'{esc(C["image_note"])}</figcaption></figure>')
    else:
        frames_html = (
            '<div class="warn col"><p><strong>Снимков «до/после» здесь нет, и это не упущение.</strong> '
            f'{esc(C.get("instrument_note", ""))} На тридцати метрах след площадью '
            f'{C.get("area_ha", 0):.0f} га — около пятнадцати пикселей в поперечнике: картинка получилась бы '
            'убедительной по форме и бессмысленной по содержанию. Доказательство здесь — числа с порогом '
            f'и поимённый контроль. {esc(C["image_note"])}</p></div>')

    cluster_html = ("" if not C.get("cluster") else
        '<div class="warn col"><p><strong>Кластер: этот эффект нельзя приписать одному проекту.</strong> '
        'В радиусе 500 м в тот же период шли ещё проекты. Узел перестраивался целиком, и измеренное изменение — '
        'их совокупный результат. Единица цены эффекта — узел и сумма бюджетов, а не отдельная строка.</p></div>'
        '<div class="scroll"><table><thead><tr><th>проект в кластере</th><th>домен</th><th>от парка</th></tr></thead>'
        f'<tbody>{cluster_rows}</tbody></table></div>')

    second_txt = esc(C["second_instrument"]) if C.get("second_instrument") else (
        "NDVI меряет зелёность и не отличает молодое дерево от травы. Классы покрытия Dynamic World "
        "по тем же снимкам говорят, что сменилось: застройка, трава, крона, голая поверхность. "
        "Два независимых прибора, сказавших одно, — довод тяжелее одного числа.")

    ot = C.get("over_time")
    ot_html = ""
    if ot:
        thr_a = ot["threshold_audit"]
        rows = "\n".join(
            f"<tr><td class='num'>{o['season']}</td><td class='num'>{o['scenes']}</td><td class='num'>{o['site']:.3f}</td>"
            f"<td class='num'>{o['control']:.3f}</td><td class='num'>{o['effect']:+.3f}</td>"
            f"<td><span class='tag {'t-sig' if o['effect'] > thr_a else 't-no'}'>{'сверх порога' if o['effect'] > thr_a else 'в шуме'}</span></td></tr>"
            for o in ot["seasons"])
        seasons = ot["seasons"]
        first = next((o["season"] for o in seasons if o["effect"] > thr_a), None)
        lo_s = min(seasons, key=lambda o: o["effect"]); hi_s = max(seasons, key=lambda o: o["effect"])
        # Три формы ряда, и у каждой своя честная фраза. Раньше фраза знала только одну —
        # провал в конце — и у Park Spoor Noord напечатала «держится до 2026-го и в 2018
        # уходит в шум»: засуха 2018 года посреди ряда, после которой эффект вернулся.
        held_txt = series_phrase(seasons, thr_a)
        b = ot["base"]
        base_txt = ((b[0][:4] if b[0][:4] == b[1][:4] else f"{b[0][:4]}–{b[1][:4]}")
                    if isinstance(b, (list, tuple)) else str(b))
        when = (f"с первого измеренного лета, {first} года," if first == seasons[0]["season"]
                else f"с {first} года")
        # сезонный порог — свой у каждого города и прибора, а не брюссельские «около 0,031»
        if C["instruments"][0]["key"] == "ndvi_landsat":
            season_txt = ("Отдельного сезонного порога для Landsat нет, поэтому каждое лето сравнивается с порогом "
                          "окна — это строже, чем нужно для одного сезона, и лето ниже него ещё не значит, что "
                          "эффекта нет.")
        else:
            city_key = "antwerp" if "нтвер" in C["city"] or "ntwerp" in C["city"] else "brussels"
            from engine.manifest import Manifest
            mon = [v.threshold for k, v in Manifest.read(city_key).layers.items() if k.startswith("monitoring_")]
            season_txt = (f"Посезонные значения шумнее четырёхлетнего среднего, и сравнивать их с аудитным порогом "
                          f"можно только как ориентир: сезонный порог мониторинга этого города — "
                          f"{min(mon):.3f}–{max(mon):.3f}." if mon else
                          "Посезонные значения шумнее четырёхлетнего среднего: аудитный порог для них — ориентир.")
        note_txt = f" {esc(ot['note'])}" if ot.get("note") else ""
        ot_html = f"""
<section>
  <div class="sec-head"><span class="eyebrow">Во времени</span><h2>Когда эффект появился и держится ли</h2></div>
  <div class="col"><p>Аудит выше — среднее за четыре лета. Здесь каждое лето отдельно против тех же двенадцати контрольных секторов, база — {base_txt}, до начала работ. Это отвечает на вопрос, которого не задаёт ни один соседний инструмент: через сколько лет после сдачи результат виден и не уходит ли он.</p></div>
  <div class="scroll"><table><thead><tr><th>лето</th><th>сцен</th><th>объект</th><th>контроль</th><th>эффект</th><th>к порогу {thr_a:.4f}</th></tr></thead><tbody>{rows}</tbody></table></div>
  <div class="callout col"><p><strong>Эффект виден {when} {held_txt}.</strong>{note_txt} Амплитуда от {lo_s['effect']:+.2f} ({lo_s['season']}) до {hi_s['effect']:+.2f} ({hi_s['season']}). {season_txt}</p></div>
</section>"""

    # превышение порога — с согласованием: «в 3 раза», «в 5 раз»
    k = round(abs(main_i["effect"]) / main_i["threshold"]) if main_i["threshold"] else 0
    ratio_txt = (f"превышение порога в {k} {plural(k, 'раз', 'раза', 'раз')}" if k >= 2 else
                 "превышение порога" if main_i["significant"] else "в пределах порога")
    # подвал называет приборы, которыми дело действительно измерено
    keys = {i["key"] for i in C["instruments"]}
    sources_txt = ("Landsat Collection 2 Level 2, 30 м" if keys == {"ndvi_landsat"} else
                   "Copernicus Sentinel-2 и Dynamic World")
    doc = f"""<meta charset="utf-8"><title>{esc(C['title'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>{CSS}</style>
<div class="page">
<header class="masthead">
  <div class="eyebrow">Аудит вмешательства · {esc(C['city'])} · {esc(C['type'])}</div>
  <h1>{esc(C['name'])}</h1>
  <div class="passport">
    <span class="chip">{esc(C['commune'])}</span><span class="chip">{esc(C['area_ha'])} га</span>
    <span class="chip">сдача: {esc(C['completed'])}</span><span class="chip">бюджет: {esc(C['budget'])}</span>
    <span class="chip">OSM <code>{esc(C['osm'])}</code></span>
    <span class="chip">документ-основание: <a href="{esc(C['source_url'])}">{esc(C['source_label'])}</a></span>
  </div>
</header>

<section>
  {frames_html}
</section>

<section>
  <div class="verdict">
    <div><b>{main_i['effect']:+.3f}</b><span>эффект против контроля · {esc(main_i['label'])}</span></div>
    <div><b>{main_i['threshold']:.4f}</b><span>порог значимости — 95-й процентиль шума по {esc(C['calibration_n'])} секторам</span></div>
    <div><b class="{'t-sig' if main_i['significant'] else 't-no'}">{esc(C['verdict'])}</b><span>{ratio_txt} · {esc(C['population_note'])}</span></div>
  </div>
  <div class="callout col"><p><strong>{esc(C['one_line'])}</strong></p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">{"Второй прибор" if len(C["instruments"]) > 1 else "Второго прибора нет"}</span><h2>{"Что именно произошло — словами, не одной цифрой" if len(C["instruments"]) > 1 else "Чем это НЕ подтверждено"}</h2></div>
  <div class="col"><p>{second_txt}</p></div>
  <div class="scroll"><table><thead><tr><th>прибор</th><th>до → после</th><th>эффект</th><th>порог</th><th>вердикт</th><th>чтение</th></tr></thead><tbody>{inst_rows}</tbody></table></div>
  <div class="col"><p>{esc(C['reading'])}</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Контроль</span><h2>Двенадцать секторов, где не вмешивались</h2></div>
  <div class="col"><p>{esc(bg_sentence('antwerp' if 'нтвер' in C['city'] or 'ntwerp' in C['city'] else 'brussels', with_threshold=False))} Контроль подобран по состоянию <em>до</em> вмешательства, не ближе 1,5 км, чтобы не попасть в ту же стройку. Каждый назван — любой может пересчитать.</p></div>
  <div class="scroll"><table><thead><tr><th>сектор</th><th>название</th><th>NDVI до</th><th>сырое Δ</th><th>км</th></tr></thead><tbody>{ctrl_rows}</tbody></table></div>
  <div class="col"><p>Разрыв подбора — {C['control_gap']:+.4f} при пределе 0,04: контроль сопоставим. Если бы разрыв был больше, вердикт не выносился бы вовсе.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Устойчивость</span><h2>Проверка сдвигом окна: не поймали ли мы стройку</h2></div>
  <div class="col"><p>{esc(tc['why'])}</p></div>
  <div class="scroll"><table><thead><tr><th>окно «до»</th><th>сцен</th><th>NDVI до</th><th>эффект</th><th>разрыв</th></tr></thead><tbody>{tc_rows}</tbody></table></div>
  <div class="callout col"><p>{esc(tc['conclusion'])}</p></div>
</section>

{ot_html}

<section>
  <div class="sec-head"><span class="eyebrow">Документы</span><h2>Что об этом месте говорят те, кто его делал</h2></div>
  <div class="scroll"><table><thead><tr><th>что</th><th>источник</th><th>детали</th></tr></thead><tbody>{doc_rows}</tbody></table></div>
  {cluster_html}
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Границы</span><h2>Чего этот аудит не утверждает</h2></div>
  <div class="col"><ul>{"".join(f"<li>{esc(l)}</li>" for l in C['limits'])}</ul></div>
</section>

<div class="cta">
  <p>Хотите такой же аудит для своего вмешательства? Нужны полигон работ, зафиксированный до начала, и год сдачи. Всё остальное — со спутника и из документов.</p>
  <a class="btn" href="#">Проверить своё вмешательство</a>
</div>
<p class="foot">Числа — из движка, пороги — из калибровки на секторах этого города, снимки — {esc(sources_txt)}. Текст шаблонный. Доказательство фиксировано, подача настраивается.</p>
</div>
"""
    out = SCRATCH / f"audit-{C['slug']}.html"
    out.write_text(doc, encoding="utf-8")
    print(f"→ {out}  ({len(doc) // 1024} КБ)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
