#!/usr/bin/env python3
"""
Публичный атлас изменений — хороплет по секторам города, экран 3 в публичной форме.

Модель — ParkScore от Trust for Public Land: бесплатная публичная карта, которая
создаёт давление и приводит покупателя. Только у нас на карте не состояние, а
ИЗМЕНЕНИЕ против контроля с измеренным порогом — того, что не печатает никто.

Что фиксировано
───────────────
Цвет — эффект против контроля, бины от порога значимости из манифеста.
Ноль шкалы — среднее изменение контроля, иначе весь город бирюзовый (без
контроля за порог вышла бы треть секторов Брюсселя, `background.py`). Легенда — само нулевое распределение метода
с отметками порога: «значимо» видно, а не сказано.

Палитра — расходящаяся, провалидирована `dataviz/scripts/validate_palette.js`:
плечи как ordinal-рампы (монотонность, шаг ΔL ≥ 0,06, светлый конец ≥ 2:1),
полюса по всем парам (тёмная: ΔE 8,6 дейтан / 26,0 норма; светлая: протан 7,8 —
полоса 6–8, законна при вторичном кодировании: обводка-зазор, подписи, таблица).
Тёмная тема — отдельно подобранные ступени под #12151A, не переворот.

Запуск:
    .venv/bin/python scripts/report/atlas_html.py --city brussels
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.config import CITIES, LIMITS
from engine.manifest import Manifest

from scripts.report.paths import DERIVED, MONTHS_RU, OUT as SCRATCH  # noqa: E402
from scripts.report.background import sentence as bg_sentence  # noqa: E402


def esc(x) -> str:
    return html.escape(str(x))


def fmt(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def cls(eff, thr):
    """Бин по эффекту: −2 сильная потеря … +2 сильный прирост; None — не измерен."""
    if eff is None:
        return "u"
    # три бина на плечо — ровно столько ступеней провалидировано в рампе
    if eff > 3 * thr: return "g3"
    if eff > 2 * thr: return "g2"
    if eff > thr: return "g1"
    if eff < -3 * thr: return "l3"
    if eff < -2 * thr: return "l2"
    if eff < -thr: return "l1"
    return "n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", choices=list(CITIES), default="brussels")
    args = ap.parse_args()
    cfg = CITIES[args.city]

    A = json.loads((DERIVED / f"atlas-{args.city}.json").read_text())
    H = json.loads((DERIVED / f"atlas-hist-{args.city}.json").read_text())
    S = json.loads(Path(f"cities/{args.city}/layers/article8_2024_summary.json").read_text())
    m = Manifest.read(args.city)
    # пороги — те, по которым слой ст. 8 вынес вердикты (посчитаны тем же прогоном)
    thr_n = S["thresholds"]["ndvi"]
    thr_t = S["thresholds"].get("trees")
    null_mean = (S.get("thresholds_mean") or {}).get("ndvi")
    unbiased = (S.get("thresholds_unbiased") or {}).get("ndvi", True)
    comp = m.layers["article8_2024"].computed if "article8_2024" in m.layers else ""
    computed_ru = (f"{int(comp[8:10])} {MONTHS_RU[int(comp[5:7]) - 1]} {comp[:4]}" if len(comp) == 10 else comp)
    W, Hh = A["meta"]["W"], A["meta"]["H"]

    secs = A["sectors"]

    META = A["meta"]   # «измерено»/«отказ» — из данных, не пересчёт
    measured = [s for s in secs if s["ne"] is not None]
    for s in secs:
        s["cn"] = cls(s["ne"], thr_n)
        s["ct"] = cls(s["te"], thr_t) if thr_t else "u"
    up = sorted([s for s in measured if s["nv"] == "рост"], key=lambda s: -s["ne"])
    down = sorted([s for s in measured if s["nv"] == "потеря"], key=lambda s: s["ne"])
    top, bot = up[0], down[0]

    # ── SVG-пути ─────────────────────────────────────────────────────────────
    paths = []
    for s in secs:
        title = f"{s['n']} · {s['c']}"
        paths.append(
            f'<path d="{s["d"]}" class="sec {s["cn"]}" data-cn="{s["cn"]}" data-ct="{s["ct"]}" '
            f'data-id="{esc(s["id"])}" data-n="{esc(s["n"])}" data-c="{esc(s["c"])}" '
            f'data-ne="{"" if s["ne"] is None else s["ne"]}" data-te="{"" if s["te"] is None else s["te"]}" '
            f'data-nv="{esc(s["nv"])}" data-tv="{esc(s["tv"])}" data-pop="{s["pop"]}" '
            f'data-inc="{"" if s["inc"] is None else int(s["inc"])}" data-n24="{"" if s["n24"] is None else s["n24"]}" '
            f'tabindex="0" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title></path>')

    # центроиды двух крайних для прямых подписей — только они, не каждая точка
    def centroid_of(d):
        pts = [tuple(map(float, p.split(","))) for seg in d.split("M")[1:] for p in seg.rstrip("Z").split()]
        return sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)
    tx, ty = centroid_of(top["d"]); bx, by = centroid_of(bot["d"])

    # ── гистограмма-легенда ──────────────────────────────────────────────────
    lo, hi, n, counts = H["lo"], H["hi"], H["n"], H["counts"]
    mx = max(counts) or 1
    bw = 100.0 / n
    bars = []
    for i, c in enumerate(counts):
        e = lo + (i + 0.5) * (hi - lo) / n
        k = cls(e, thr_n)
        h = 100.0 * c / mx
        bars.append(f'<rect x="{i*bw:.2f}" y="{100-h:.2f}" width="{bw-0.25:.2f}" height="{h:.2f}" class="{k}"/>')
    x_thr_pos = 100 * (thr_n - lo) / (hi - lo); x_thr_neg = 100 * (-thr_n - lo) / (hi - lo)
    x_zero = 100 * (0 - lo) / (hi - lo)

    # ── таблица значимых ─────────────────────────────────────────────────────
    def row(s):
        te = f"{s['te']:+.3f}" if s["te"] is not None else "—"
        inc = fmt(s["inc"]) + " €" if s["inc"] else "—"
        return (f"<tr><td>{esc(s['n'])}</td><td>{esc(s['c'])}</td><td class='num'>{s['ne']:+.4f}</td>"
                f"<td class='num'>{te}</td><td>{esc(s['nv'])}</td><td class='num'>{fmt(s['pop'])}</td><td class='num'>{inc}</td></tr>")
    sig_rows = "\n".join(row(s) for s in up + down)
    all_rows = "\n".join(row(s) for s in sorted(measured, key=lambda s: -s["ne"]))

    terc = S["equity_income_terciles"]
    lo_t, hi_t = terc[0], terc[-1]
    not_measured = len(secs) - META["measured"]
    incomparable = META["refused"]

    # Коммуна в подписи обязательна: имена секторов Statbel повторяются — CHEMIN DE FER
    # есть в Моленбеке (сильнейшая потеря) и в Одергеме (рост), и без коммуны их не различить.
    doc = f"""<meta charset="utf-8"><title>Атлас изменений · {esc(cfg['display_name'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>
:root{{--paper:#EFF1EC;--surface:#FFFFFF;--ink:#141B17;--muted:#5B6B62;--rule:#D5DAD3;--rule-2:#E4E8E3;--accent:#1E6E58;--accent-soft:#E2EDE7;--heat:#C2451C;--heat-soft:#F7E6DE;
--g1:#3EB0A0;--g2:#22998d;--g3:#0f6b63;--l1:#EB7F7F;--l2:#e05f5f;--l3:#c9302f;--n:#D9DCD6;--u:#E6E9E3;--gap:#EFF1EC;
--display:"IBM Plex Sans Condensed","Helvetica Neue",Arial,sans-serif;--body:"IBM Plex Serif",Georgia,serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--measure:34rem;--wide:64rem}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--paper:#12151A;--surface:#181D22;--ink:#E3E8E3;--muted:#8FA096;--rule:#2A3138;--rule-2:#21272D;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;
--g1:#3AA898;--g2:#1F8F82;--g3:#0F6B60;--l1:#DF5E5E;--l2:#C94848;--l3:#AD2E2E;--n:#2F353A;--u:#1C2126;--gap:#12151A}}}}
:root[data-theme="dark"]{{--paper:#12151A;--surface:#181D22;--ink:#E3E8E3;--muted:#8FA096;--rule:#2A3138;--rule-2:#21272D;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;
--g1:#3AA898;--g2:#1F8F82;--g3:#0F6B60;--l1:#DF5E5E;--l2:#C94848;--l3:#AD2E2E;--n:#2F353A;--u:#1C2126;--gap:#12151A}}
*{{box-sizing:border-box}}body{{background:var(--paper);color:var(--ink);font-family:var(--body);font-size:16.5px;line-height:1.62;-webkit-font-smoothing:antialiased}}
.page{{max-width:var(--wide);margin:0 auto;padding:3.5rem 1.5rem 6rem;display:flex;flex-direction:column;gap:2.5rem}}
.col{{max-width:var(--measure)}}.masthead{{display:flex;flex-direction:column;gap:.9rem;padding-bottom:1.75rem;border-bottom:2px solid var(--ink)}}
.eyebrow{{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
h1{{font-family:var(--display);font-weight:700;font-size:clamp(2.3rem,7vw,3.8rem);line-height:.98;letter-spacing:-.02em;margin:0;text-wrap:balance}}
.standfirst{{font-size:1.12rem;line-height:1.5;max-width:40rem;margin:0}}.dateline{{font-family:var(--mono);font-size:.76rem;color:var(--muted);display:flex;flex-wrap:wrap;gap:.4rem 1.4rem}}
section{{display:flex;flex-direction:column;gap:1rem}}.sec-head{{display:flex;flex-direction:column;gap:.3rem;border-top:1px solid var(--rule);padding-top:.85rem}}.sec-head .eyebrow{{color:var(--accent)}}
h2{{font-family:var(--display);font-weight:600;font-size:clamp(1.35rem,3.2vw,1.8rem);line-height:1.12;margin:0;text-wrap:balance}}h3{{font-family:var(--display);font-weight:600;font-size:1.02rem;margin:.3rem 0 0}}
p{{margin:0}}strong{{font-weight:600}}code{{font-family:var(--mono);font-size:.86em}}ul{{margin:0;padding-left:1.15rem;display:flex;flex-direction:column;gap:.4rem}}
.callout{{background:var(--accent-soft);border-left:3px solid var(--accent);padding:1rem 1.2rem;max-width:var(--measure)}}.warn{{background:var(--heat-soft);border-left:3px solid var(--heat);padding:1rem 1.2rem;max-width:var(--measure)}}
/* ── фильтры: один ряд над всем, что они меняют ── */
.filters{{display:flex;flex-wrap:wrap;gap:.6rem 1.4rem;align-items:center;font-family:var(--display);font-size:.9rem}}
.seg{{display:inline-flex;border:1px solid var(--rule);background:var(--surface)}}.seg button{{font:inherit;font-weight:600;background:none;border:0;padding:.45rem .9rem;color:var(--muted);cursor:pointer}}
.seg button[aria-pressed="true"]{{background:var(--ink);color:var(--paper)}}.seg button:focus-visible{{outline:2px solid var(--accent);outline-offset:-2px}}
label.chk{{display:inline-flex;gap:.45rem;align-items:center;cursor:pointer}}
/* ── карта ── */
.mapwrap{{position:relative;background:var(--surface);border:1px solid var(--rule);padding:.6rem}}
svg.map{{display:block;width:100%;height:auto}}
.sec{{stroke:var(--gap);stroke-width:1.3;stroke-linejoin:round;cursor:pointer;transition:opacity .12s}}
.sec.g1{{fill:var(--g1)}}.sec.g2{{fill:var(--g2)}}.sec.g3{{fill:var(--g3)}}.sec.l1{{fill:var(--l1)}}.sec.l2{{fill:var(--l2)}}.sec.l3{{fill:var(--l3)}}.sec.n{{fill:var(--n)}}.sec.u{{fill:var(--u)}}
.map.only-sig .sec.n,.map.only-sig .sec.u{{opacity:.35}}
.sec:hover,.sec:focus-visible{{stroke:var(--ink);stroke-width:2;outline:none}}
.lbl{{font-family:var(--display);font-weight:600;font-size:15px;fill:var(--ink);paint-order:stroke;stroke:var(--surface);stroke-width:4px;stroke-linejoin:round;pointer-events:none}}
.lbl.sub{{font-weight:500;font-size:12px;fill:var(--muted)}}
.tip{{position:absolute;pointer-events:none;background:var(--ink);color:var(--paper);font-family:var(--display);font-size:.84rem;line-height:1.35;padding:.55rem .7rem;max-width:18rem;display:none;z-index:5}}
.tip b{{font-size:.95rem;display:block;margin-bottom:.15rem}}.tip .m{{font-family:var(--mono);font-size:.78rem}}
/* ── легенда = распределение ── */
.legend{{display:grid;grid-template-columns:1fr;gap:.5rem;background:var(--surface);border:1px solid var(--rule);padding:.9rem 1rem}}
svg.hist{{display:block;width:100%;height:110px}}svg.hist rect.g1{{fill:var(--g1)}}svg.hist rect.g2{{fill:var(--g2)}}svg.hist rect.g3{{fill:var(--g3)}}svg.hist rect.l1{{fill:var(--l1)}}svg.hist rect.l2{{fill:var(--l2)}}svg.hist rect.l3{{fill:var(--l3)}}svg.hist rect.n{{fill:var(--n)}}
svg.hist line{{stroke:var(--ink);stroke-width:.5}}svg.hist line.zero{{stroke:var(--muted);stroke-dasharray:none;stroke-width:.4}}
.bins{{display:grid;grid-template-columns:repeat(auto-fit,minmax(6.5rem,1fr));gap:.35rem;font-family:var(--mono);font-size:.68rem;color:var(--muted)}}
.bins div{{display:flex;flex-direction:column;gap:.25rem}}.bins i{{display:block;height:.6rem}}.bins .g3 i{{background:var(--g3)}}.bins .g2 i{{background:var(--g2)}}.bins .g1 i{{background:var(--g1)}}.bins .n i{{background:var(--n)}}.bins .l1 i{{background:var(--l1)}}.bins .l2 i{{background:var(--l2)}}.bins .l3 i{{background:var(--l3)}}.bins .u i{{background:var(--u);border:1px solid var(--rule)}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(9.5rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}}
.stat{{background:var(--surface);padding:.9rem 1rem;display:flex;flex-direction:column;gap:.15rem}}.stat b{{font-family:var(--display);font-weight:700;font-size:1.9rem;line-height:1;letter-spacing:-.02em}}.stat span{{font-family:var(--display);font-size:.78rem;color:var(--muted);line-height:1.3}}
.scroll{{overflow-x:auto;max-width:100%}}table{{border-collapse:collapse;width:100%;min-width:38rem;font-size:.88rem;font-family:var(--display);font-weight:500}}
th{{text-align:left;font-family:var(--mono);font-weight:500;font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--ink);padding:0 .8rem .45rem 0;vertical-align:bottom}}
td{{border-bottom:1px solid var(--rule-2);padding:.5rem .8rem .5rem 0;vertical-align:top;line-height:1.35}}td.num{{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}}tr:last-child td{{border-bottom:none}}
details summary{{cursor:pointer;font-family:var(--display);font-weight:600;color:var(--accent)}}
.foot{{font-family:var(--display);font-size:.82rem;color:var(--muted);border-top:1px solid var(--rule);padding-top:1rem;max-width:46rem}}
@media (prefers-reduced-motion:reduce){{.sec{{transition:none}}}}
@media (forced-colors:active){{.sec{{stroke:CanvasText;stroke-width:1}}}}
</style>
<div class="page">
<header class="masthead">
  <div class="eyebrow">Атлас изменений · {esc(cfg['display_name'])} · 2017–2019 → 2021–2024</div>
  <h1>Что реально изменилось в зелени города</h1>
  <p class="standfirst">Каждый из {META["measured"]} статистических секторов измерен со спутника и сравнён с двенадцатью похожими секторами, где ничего не делали. Цвет — не «стало зеленее», а «изменилось <em>сильнее или слабее сопоставимых мест</em>». Порог значимости измерен на самом городе, а не назначен.</p>
  <div class="dateline"><span>Sentinel-2 · Dynamic World</span><span>единица: сектор Statbel</span><span>порог зелени {thr_n:.4f}{f' · кроны {thr_t:.4f}' if thr_t else ''}</span><span>расчёт {computed_ru}</span></div>
</header>

<section>
  <div class="stats">
    <div class="stat"><b class="up">{len(up)}</b><span>секторов значимо зеленее контроля · {fmt(sum(s['pop'] for s in up))} жителей</span></div>
    <div class="stat"><b>{len(down)}</b><span>секторов значимо бледнее · {fmt(sum(s['pop'] for s in down))} жителей</span></div>
    <div class="stat"><b>{len(measured) - len(up) - len(down)}</b><span>в пределах шума метода</span></div>
    <div class="stat"><b>{not_measured + incomparable}</b><span>не измерено или контроль несопоставим — честный отказ</span></div>
  </div>
</section>

<section>
  <div class="filters" role="group" aria-label="Что показывать">
    <span class="seg" role="group" aria-label="Метрика">
      <button type="button" data-metric="cn" aria-pressed="true">Зелень (NDVI)</button>
      <button type="button" data-metric="ct" aria-pressed="false"{'' if thr_t else ' disabled'}>Крона</button>
    </span>
    <label class="chk"><input type="checkbox" id="onlysig"> приглушить незначимое</label>
  </div>
  <div class="mapwrap">
    <svg class="map" id="map" viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg" aria-label="Карта секторов, цвет — эффект против контроля">
      <g id="secs">{"".join(paths)}</g>
      <g aria-hidden="true">
        <text class="lbl" x="{tx:.0f}" y="{ty:.0f}" text-anchor="middle">{esc(top['n'])}</text>
        <text class="lbl sub" x="{tx:.0f}" y="{ty+16:.0f}" text-anchor="middle">{esc(top['c'])} · {top['ne']:+.3f} · сильнейший прирост</text>
        <text class="lbl" x="{bx:.0f}" y="{by:.0f}" text-anchor="middle">{esc(bot['n'])}</text>
        <text class="lbl sub" x="{bx:.0f}" y="{by+16:.0f}" text-anchor="middle">{esc(bot['c'])} · {bot['ne']:+.3f} · сильнейшая потеря</text>
      </g>
    </svg>
    <div class="tip" id="tip" role="status" aria-live="polite"></div>
  </div>
  <p class="col" style="font-family:var(--display);font-size:.88rem;color:var(--muted)">Наведите или перейдите клавишей Tab на сектор. Подписаны только два крайних; всё остальное — в таблице ниже.</p>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Легенда</span><h2>Это нулевое распределение метода, а не шкала</h2></div>
  <div class="col"><p>Каждый сектор по очереди «притворялся» вмешательством, ему подбирался контроль, считался эффект. Так выглядит шум по {H['total']} секторам. Порог значимости — его 95-й процентиль: <strong>{thr_n:.4f}</strong>. Цвет на карте — тот же, что у столбца, в который попал сектор.</p></div>
  <div class="legend">
    <svg class="hist" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="Гистограмма нулевого распределения эффектов">
      {"".join(bars)}
      <line class="zero" x1="{x_zero:.2f}" y1="0" x2="{x_zero:.2f}" y2="100"/>
      <line x1="{x_thr_neg:.2f}" y1="0" x2="{x_thr_neg:.2f}" y2="100"/>
      <line x1="{x_thr_pos:.2f}" y1="0" x2="{x_thr_pos:.2f}" y2="100"/>
    </svg>
    <div class="bins" aria-hidden="true">
      <div class="l3"><i></i>&lt; −{3*thr_n:.3f}</div><div class="l2"><i></i>−{3*thr_n:.3f} … −{2*thr_n:.3f}</div><div class="l1"><i></i>−{2*thr_n:.3f} … −{thr_n:.3f}</div><div class="n"><i></i>шум ±{thr_n:.3f}</div><div class="g1"><i></i>+{thr_n:.3f} … +{2*thr_n:.3f}</div><div class="g2"><i></i>+{2*thr_n:.3f} … +{3*thr_n:.3f}</div><div class="g3"><i></i>&gt; +{3*thr_n:.3f}</div><div class="u"><i></i>не измерен</div>
    </div>
    <p style="font-family:var(--display);font-size:.84rem;color:var(--muted)">Вертикали — порог ±{thr_n:.4f}. Слева от левой — {H['below']} секторов, справа от правой — {H['above']}. {('Среднее распределения ' + format(null_mean, '+.4f').replace('-', '−') + ': метод ' + ('не смещён.' if unbiased else 'СМЕЩЁН, порог недействителен.')) if null_mean is not None else ''}</p>
  </div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Кому досталось</span><h2>Зелень по доходу</h2></div>
  <div class="stats">
    <div class="stat"><b>{lo_t['ndvi_2024_wmean']:.3f}</b><span>зелёность 2024, нижний терциль по доходу · медиана {fmt(lo_t['income_median'])} €</span></div>
    <div class="stat"><b>{hi_t['ndvi_2024_wmean']:.3f}</b><span>верхний терциль · медиана {fmt(hi_t['income_median'])} €</span></div>
    <div class="stat"><b>{lo_t['trees_2024_wmean']:.3f}</b><span>крона 2024, нижний терциль</span></div>
    <div class="stat"><b>{hi_t['trees_2024_wmean']:.3f}</b><span>крона 2024, верхний терциль</span></div>
  </div>
  <div class="callout col"><p>Беднейшая треть секторов живёт при <strong>{100*lo_t['trees_2024_wmean']/hi_t['trees_2024_wmean']:.0f} %</strong> кроны богатейшей. Закон об этом молчит; индикатор SDG 11.7 — нет.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Таблица</span><h2>Значимые секторы — всё, что есть на карте, словами</h2></div>
  <div class="scroll"><table><thead><tr><th>сектор</th><th>коммуна</th><th>эффект NDVI</th><th>эффект кроны</th><th>вердикт</th><th>жителей</th><th>доход</th></tr></thead><tbody>{sig_rows}</tbody></table></div>
  <details><summary>Показать все {len(measured)} сопоставимых секторов (ещё {META["refused"]} — отказ: контроль несопоставим)</summary>
    <div class="scroll" style="margin-top:.75rem"><table><thead><tr><th>сектор</th><th>коммуна</th><th>эффект NDVI</th><th>эффект кроны</th><th>вердикт</th><th>жителей</th><th>доход</th></tr></thead><tbody>{all_rows}</tbody></table></div>
  </details>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Метод и границы</span><h2>Почему числу можно верить и чего оно не говорит</h2></div>
  <div class="col"><ul>
    <li><strong>Разность разностей.</strong> Эффект = (сектор после − до) − (контроль после − до). {esc(bg_sentence(args.city))}</li>
    <li><strong>Контроль подобранный.</strong> 12 секторов, похожих по состоянию до периода, не ближе 1,5 км. Если сопоставимого нет — отказ, не число.</li>
    <li><strong>Порог измерен.</strong> 95-й процентиль нулевого распределения — та гистограмма выше.</li>
  </ul></div>
  <div class="warn col"><p><strong>Чего атлас не утверждает.</strong> Причину изменения: сильнейший прирост города — Zavelenberg — это не политика, а прекращение выпаса после смерти фермера. Спутник видит изменение; причину даёт документ. Каждый цвет здесь — кандидат для проверки, не вердикт о вмешательстве.</p></div>
  <div class="col"><ul>{"".join(f"<li>{esc(l)}</li>" for l in LIMITS)}</ul></div>
</section>

<p class="foot">Снимки: Copernicus Sentinel-2 SR Harmonized и Google Dynamic World, летние медианы 2017–2024, 10 м. Секторы, население: Statbel 2024; доход: Statbel 2023. Пороги — из <code>cities/{esc(args.city)}/manifest.json</code>. Палитра провалидирована на цветовую слепоту в обеих темах. Доказательство фиксировано, подача настраивается.</p>
</div>
<script>
(function(){{
  const map=document.getElementById('map'),tip=document.getElementById('tip'),wrap=map.parentElement;
  const secs=map.querySelectorAll('.sec');let metric='cn';
  function paint(){{secs.forEach(p=>{{p.setAttribute('class','sec '+p.dataset[metric]);}});}}
  document.querySelectorAll('[data-metric]').forEach(b=>b.addEventListener('click',()=>{{
    document.querySelectorAll('[data-metric]').forEach(x=>x.setAttribute('aria-pressed','false'));
    b.setAttribute('aria-pressed','true');metric=b.dataset.metric;paint();}}));
  document.getElementById('onlysig').addEventListener('change',e=>map.classList.toggle('only-sig',e.target.checked));
  function show(p,x,y){{
    const ne=p.dataset.ne?(+p.dataset.ne).toFixed(4):'—',te=p.dataset.te?(+p.dataset.te).toFixed(4):'—';
    const inc=p.dataset.inc?Number(p.dataset.inc).toLocaleString('ru-RU')+' €':'—';
    tip.innerHTML='<b>'+p.dataset.n+'</b>'+p.dataset.c+'<br><span class="m">NDVI '+(ne[0]=='-'?ne:'+'+ne)+' · крона '+(te=='—'?'—':(te[0]=='-'?te:'+'+te))+'</span><br>'+(p.dataset.nv||'не измерен')+' · '+Number(p.dataset.pop).toLocaleString('ru-RU')+' жит. · '+inc;
    tip.style.display='block';const r=wrap.getBoundingClientRect();
    tip.style.left=Math.min(x-r.left+14,r.width-tip.offsetWidth-8)+'px';tip.style.top=(y-r.top+14)+'px';}}
  secs.forEach(p=>{{
    p.addEventListener('mousemove',e=>show(p,e.clientX,e.clientY));
    p.addEventListener('mouseleave',()=>tip.style.display='none');
    p.addEventListener('focus',()=>{{const b=p.getBoundingClientRect();show(p,b.left+b.width/2,b.top+b.height/2);}});
    p.addEventListener('blur',()=>tip.style.display='none');}});
}})();
</script>
"""
    out = SCRATCH / f"atlas-{args.city}.html"
    out.write_text(doc, encoding="utf-8")
    # карта отдельно, в проект: лендинг берёт её для героя и не должен зависеть от временной папки
    import re as _re
    (DERIVED / f"atlas-{args.city}-map.svg").write_text(
        _re.search(r'<svg class="map"[\s\S]*?</svg>', doc).group(0), encoding="utf-8")
    print(f"→ {out}  ({len(doc)//1024} КБ) · измерено {META['measured']} · отказ {META['refused']} · значимо +{len(up)} / −{len(down)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
