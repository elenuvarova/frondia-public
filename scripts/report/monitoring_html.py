"""Страница мониторинга: бюллетень сезона для одного города.

Что это: годовой отчёт «в этом сезоне N секторов потеряли зелень сверх порога»
в публичной форме — воронка кандидаты → стройка → не подтверждено →
подтверждённая потеря кроны, именованные подтверждённые секторы с документами,
сравнение с прошлым сезоном, паспорт порогов из манифеста.

Правило страницы: поимённо публикуются только потери, подтверждённые вторым
прибором (Dynamic World, пороги из манифеста), и стройки — как честная потеря,
не деградация. «Не подтверждено» идёт числом, без имён: односезонный NDVI без
второго прибора слишком шумен, чтобы называть сектор.

Вход: `cities/<city>/layers/monitoring_<season>.csv` (слой пакета, не сырой файл),
`cities/<city>/manifest.json` (пороги сезона и DW). Вердикт берётся из слоя
(`dw_label`), не пересчитывается по округлённому порогу.

    python scripts/report/monitoring_html.py --city brussels --season 2025
"""
from __future__ import annotations

import argparse
import csv
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.config import CITIES, CONTROL, QUALITY  # noqa: E402
from engine.manifest import Manifest  # noqa: E402

from scripts.report.paths import DERIVED, OUT as SCRATCH, today_ru  # noqa: E402

# ── человеческий слой: документы к подтверждённым потерям. Числа — из слоя. ──
NOTES = {
    ("brussels", 2025, "21016A193"): dict(
        short="буря 9 июля 2024",
        what="Parc de Wolvendael, Uccle, ~18 га, около 10 000 деревьев.",
        cause="Буря 9 июля 2024 года: погиб ребёнок, инспекция признала аварийными более 150 деревьев, "
              "около сотни спилено (53 на липовой аллее), 59 пней удалено; часть парка закрыта до 2025-го. "
              "Восстановление 270 000 €, коммуна и регион; посажено около ста новых деревьев.",
        sources=[
            ("RTBF, 2025", "https://www.rtbf.be/article/uccle-la-renaissance-du-parc-de-wolvendael-apres-la-tempete-meurtriere-de-juillet-2024-11662757"),
            ("DH, 14.11.2024", "https://www.dhnet.be/regions/bruxelles/2024/11/14/quatre-mois-apres-la-tempete-une-partie-du-parc-de-wolvendael-est-toujours-fermee-3H75267ERNHETAXM5NNPZVZM3I/"),
            ("BX1", "https://bx1.be/categories/news/uccle-le-parc-de-wolvendael-devrait-rouvrir-ses-portes-prochainement/"),
            ("uccle.be", "https://www.uccle.be/fr/actualites/reouverture-complete-du-parc-de-wolvendael"),
        ],
        verdict="Потеря кроны настоящая и не связана с политикой города: причина — буря и санитарная рубка. "
                "Так и печатается. Молодые посадки на месте спиленных дадут NDVI ниже прежней кроны ещё несколько сезонов.",
    ),
    ("brussels", 2026, "21016A193"): dict(
        short="та же буря 2024-го",
        what="Parc de Wolvendael, Uccle — второй сезон подряд.",
        cause="Та же потеря, что в 2025-м, а не новое событие: база сезона 2026 — лета 2023–2025, и два из них "
              "ещё до бури 9 июля 2024 года. Крона −0,051 в 2025-м и −0,059 в 2026-м: спиленные деревья не "
              "вернулись, а около ста новых посадок пока не дают кроны.",
        sources=[
            ("RTBF, 2025", "https://www.rtbf.be/article/uccle-la-renaissance-du-parc-de-wolvendael-apres-la-tempete-meurtriere-de-juillet-2024-11662757"),
            ("uccle.be", "https://www.uccle.be/fr/actualites/reouverture-complete-du-parc-de-wolvendael"),
        ],
        verdict="Повторная регистрация одной потери. Уйдёт из бюллетеня, когда база целиком окажется после бури — "
                "с сезона 2028-го, если посадки не наберут крону раньше.",
    ),
    ("brussels", 2026, "21001A982"): dict(
        short="причина не установлена",
        what="Parc Forestier, Anderlecht: около 5 га, бывшее кладбище, почти 300 деревьев, с 2018 года в ведении "
             "Bruxelles Environnement.",
        cause="Документ нашёлся один: разрешение 2025 года на обрезку четырёх деревьев и рубку трёх. На пять "
              "гектаров трёх деревьев мало, чтобы объяснить сигнал. Оба прибора превышают свои пороги лишь в 1,3 "
              "раза, а сезон 2026 спокойный — порог самый низкий за три года.",
        sources=[
            ("OpenPermits 2025", "https://openpermits.brussels/fr/theme/tree_cutting/2025"),
            ("gardens.brussels", "https://gardens.brussels/fr/espaces-verts/parc-forestier"),
        ],
        verdict="Причина не установлена. Публикуется как измерение на грани порога, не как претензия; "
                "проверка — следующим сезоном.",
    ),
    ("brussels", 2026, "21001A83-"): dict(
        reclass="СТРОЙКА",
        what="Peterbos, Anderlecht: социальный жилой массив в парке, 17 га.",
        cause="В апреле 2026 начались крупные работы: спортивный и общественный комплекс 2 400 м² на месте "
              "парковки в центре парка и полная реконструкция корпусов. В 2025-м сектор был в шуме (−0,017), "
              "в 2026-м −0,044 — скачок совпадает с началом работ. Застройка ещё не выросла выше порога, потому "
              "что расчистка идёт раньше строительства.",
        sources=[
            ("VRT NWS, 06.04.2026", "https://www.vrt.be/vrtnws/fr/2026/04/06/lancement-de-grands-travaux-au-peterbos-a-anderlecht-nouveau-c/"),
            ("anderlecht.be, CQD Peterbos", "https://anderlecht.be/index.php/fr/peterbos"),
            ("SLRB", "https://slrb-bghm.brussels/fr/chantiers/peterbos-1-et-5-eveloppe"),
        ],
        verdict="Приборы видят потерю кроны, документы — стройплощадку. Сектор перенесён в стройки: потеря "
                "честная, но это застройка, а не деградация зелени.",
    ),
}


def apply_documents(rows: list[dict], city: str, season: int) -> list[dict]:
    """Третий фильтр после двух приборов — документы. Если документ показывает, что
    «потеря кроны» — это расчистка стройплощадки, сектор переносится в стройки.
    Прибор ошибается здесь закономерно: расчистка идёт раньше застройки, и в сезон
    начала работ крона уже упала, а класс built ещё не вырос выше порога."""
    for r in rows:
        n = NOTES.get((city, season, r["id"]))
        if n and n.get("reclass") and r["dw_label"]:
            r["instrument_label"], r["dw_label"] = r["dw_label"], n["reclass"]
    return rows

CSS = """
:root{--paper:#EFF1EC;--surface:#FFFFFF;--ink:#141B17;--muted:#5B6B62;--rule:#D5DAD3;--rule-2:#E4E8E3;
--accent:#1E6E58;--accent-soft:#E2EDE7;--heat:#C2451C;--heat-soft:#F7E6DE;
--l1:#EB7F7F;--l2:#e05f5f;--l3:#c9302f;--n:#D9DCD6;
--display:"IBM Plex Sans Condensed","Helvetica Neue",Arial,sans-serif;--body:"IBM Plex Serif",Georgia,serif;
--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--measure:34rem;--wide:60rem}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;
--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;
--l1:#DF5E5E;--l2:#C94848;--l3:#AD2E2E;--n:#2F353A}}
:root[data-theme="dark"]{--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;
--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;--l1:#DF5E5E;--l2:#C94848;--l3:#AD2E2E;--n:#2F353A}
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
tr:last-child td{border-bottom:none}
.tag{font-family:var(--mono);font-size:.67rem;letter-spacing:.05em;text-transform:uppercase;padding:.14rem .42rem;white-space:nowrap;border:1px solid currentColor}
.t-loss{color:var(--heat)}.t-gain{color:var(--accent)}.t-mute{color:var(--muted)}
/* воронка — один объект: подпись · полоса · число */
.funnel{display:grid;grid-template-columns:minmax(11rem,14rem) 1fr auto;gap:.55rem 1rem;align-items:center;background:var(--surface);border:1px solid var(--rule);padding:1.2rem 1.25rem;font-family:var(--display)}
.funnel .lab{font-size:.92rem;line-height:1.25}.funnel .lab small{display:block;font-family:var(--mono);font-size:.68rem;color:var(--muted);letter-spacing:.04em}
.funnel .bar{height:1.35rem;background:var(--rule-2);position:relative}.funnel .bar i{position:absolute;inset:0 auto 0 0;display:block}
.funnel .val{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:1.05rem;text-align:right;min-width:3ch}
.funnel .val small{display:block;font-size:.68rem;color:var(--muted)}
.funnel .rule{grid-column:1/-1;border-top:1px dashed var(--rule);margin:.25rem 0}
.c-cand{background:var(--l1)}.c-build{background:var(--muted)}.c-unc{background:var(--n)}.c-conf{background:var(--l3)}.c-gain{background:var(--accent)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}
.stat{background:var(--surface);padding:1rem 1.05rem;display:flex;flex-direction:column;gap:.2rem}
.stat b{font-family:var(--display);font-weight:700;font-size:2rem;line-height:1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat span{font-family:var(--display);font-size:.8rem;color:var(--muted);line-height:1.3}
.doc{border:1px solid var(--rule);background:var(--surface);padding:1.1rem 1.25rem;display:flex;flex-direction:column;gap:.55rem;max-width:46rem}
.doc .src{font-family:var(--mono);font-size:.74rem;color:var(--muted);display:flex;flex-wrap:wrap;gap:.3rem 1.1rem}
.foot{font-family:var(--display);font-size:.82rem;color:var(--muted);border-top:1px solid var(--rule);padding-top:1rem;max-width:46rem}
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def fmt_int(n) -> str:
    return f"{int(round(float(n))):,}".replace(",", " ")


def _f(v):
    try:
        return None if v in ("", None, "None") else float(v)
    except (TypeError, ValueError):
        return None


def load_layer(city: str, season: int) -> list[dict]:
    p = Path(f"cities/{city}/layers/monitoring_{season}.csv")
    rows = []
    for r in csv.DictReader(p.open()):
        rows.append({
            "id": r["id"], "name": r.get("name") or r["id"],
            "area_ha": _f(r.get("area_ha")) or 0.0, "population": int(float(r.get("population") or 0)),
            "effect": _f(r.get("effect")), "comparable": str(r.get("comparable")).lower() == "true",
            "dw_label": r.get("dw_label") or "", "dw_trees": _f(r.get("dw_trees")), "dw_built": _f(r.get("dw_built")),
        })
    return rows


def funnel(rows: list[dict], thr: float) -> dict:
    """Воронка сезона. Кандидат — сектор с эффектом ниже −порога ИЛИ с вердиктом
    второго прибора в слое: слой округлён до 4 знаков, и сектор ровно на пороге
    не должен выпадать при пересчёте. Вердикт — из слоя, не отсюда."""
    ok = [r for r in rows if r["effect"] is not None and r["comparable"]]
    refused = sum(1 for r in rows if r["effect"] is not None and not r["comparable"])
    lost = sorted([r for r in ok if r["effect"] < -thr or r["dw_label"]], key=lambda r: r["effect"])
    gained = sorted([r for r in ok if r["effect"] > thr], key=lambda r: -r["effect"])
    return dict(
        measured=len(ok) + refused, refused=refused, lost=lost, gained=gained,
        lost_pop=sum(r["population"] for r in lost), gained_pop=sum(r["population"] for r in gained),
        confirmed=[r for r in lost if r["dw_label"] == "ПОТЕРЯ КРОНЫ"],
        construction=[r for r in lost if r["dw_label"] == "СТРОЙКА"],
        unconfirmed=[r for r in lost if r["dw_label"] == "не подтверждено"],
        unchecked=[r for r in lost if not r["dw_label"]],
    )


def communes(city: str) -> dict[str, str]:
    try:
        from engine.adapters import ADAPTERS
        return {u.id: u.commune for u in ADAPTERS[city]().units() if u.commune and u.commune != "?"}
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", choices=list(CITIES), required=True)
    ap.add_argument("--season", type=int, required=True)
    args = ap.parse_args()
    city, season = args.city, args.season
    cfg = CITIES[city]
    m = Manifest.read(city)
    layer = m.layers.get(f"monitoring_{season}")
    if layer is None:
        print(f"слой monitoring_{season} не зарегистрирован в манифесте {city}: страница не собирается", file=sys.stderr)
        return 1
    thr = layer.threshold
    thr_trees, thr_built = m.layers["trees"].threshold, m.layers["built"].threshold
    rows = apply_documents(load_layer(city, season), city, season)
    F = funnel(rows, thr)
    com = communes(city)
    prev_layer = m.layers.get(f"monitoring_{season - 1}")
    P = (funnel(apply_documents(load_layer(city, season - 1), city, season - 1), prev_layer.threshold)
         if prev_layer else None)
    base = f"{season - 3}–{season - 1}"
    name = cfg["display_name"]

    n_c, n_b, n_u, n_k = len(F["confirmed"]), len(F["construction"]), len(F["unconfirmed"]), len(F["unchecked"])
    cand = len(F["lost"])
    if n_c == 0:
        headline = f"{name}, лето {season}: {cand} кандидатов, подтверждённых потерь кроны нет"
    elif n_c == 1:
        headline = f"{name}, лето {season}: {cand} кандидатов, одна потеря кроны"
    else:
        headline = f"{name}, лето {season}: {cand} кандидатов, потерь кроны {n_c}"

    def w(n):  # ширина полосы от числа кандидатов
        return f"{(100 * n / cand) if cand else 0:.1f}%"

    def row(r, with_dw=True):
        cm = com.get(r["id"], "")
        t = f"{r['dw_trees']:+.3f}" if r["dw_trees"] is not None else "—"
        b = f"{r['dw_built']:+.3f}" if r["dw_built"] is not None else "—"
        dw = f"<td class='num'>{t}</td><td class='num'>{b}</td>" if with_dw else ""
        moved = (" <span class='tag t-mute'>перенесён по документам</span>" if r.get("instrument_label") else "")
        name = esc(r["name"]) if r["name"] and r["name"] != r["id"] else "<span class='t-mute'>без названия</span>"
        return (f"<tr><td><code>{esc(r['id'])}</code></td><td>{name}{(' · ' + esc(cm)) if cm and cm != r['name'] else ''}{moved}</td>"
                f"<td class='num t-loss'>{r['effect']:+.4f}</td>{dw}"
                f"<td class='num'>{fmt_int(r['population'])}</td><td class='num'>{r['area_ha']:.0f}</td></tr>")

    dw_head = f"<th>Δ trees<br><small>порог {thr_trees:.3f}</small></th><th>Δ built<br><small>порог {thr_built:.3f}</small></th>"

    # подтверждённые — поимённо, с документами
    if F["confirmed"]:
        conf_tbl = ("<div class='scroll'><table><thead><tr><th>сектор</th><th>название</th><th>эффект NDVI</th>"
                    f"{dw_head}<th>жителей</th><th>га</th></tr></thead><tbody>"
                    + "".join(row(r) for r in F["confirmed"]) + "</tbody></table></div>")
        docs = []
        for r in F["confirmed"]:
            n = NOTES.get((city, season, r["id"]))
            if n:
                srcs = " ".join(f"<a href='{esc(u)}'>{esc(t)}</a>" for t, u in n["sources"])
                docs.append(f"<div class='doc'><h3>{esc(r['name'])}: что говорят документы</h3><p>{esc(n['what'])}</p>"
                            f"<p>{esc(n['cause'])}</p><p><strong>{esc(n['verdict'])}</strong></p><div class='src'>{srcs}</div></div>")
            else:
                docs.append(f"<div class='warn col'><p><strong>{esc(r['name'])}: причина не установлена.</strong> Два прибора сошлись на потере кроны, "
                            "но документа, объясняющего её, в реестре нет. Публикуется как измерение без причины — не как претензия к городу.</p></div>")
        conf_html = conf_tbl + "".join(docs)
    else:
        conf_html = (f"<div class='callout col'><p><strong>Ни одна из {cand} потерь NDVI не подтверждена вторым прибором.</strong> "
                     f"Класс trees ни в одном секторе не упал больше порога {thr_trees:.3f}. Односезонная просадка зелёности "
                     "без движения кроны — погода или шум, и ни один сектор не называется.</p></div>")

    build_html = ("<div class='scroll'><table><thead><tr><th>сектор</th><th>название</th><th>эффект NDVI</th>"
                  f"{dw_head}<th>жителей</th><th>га</th></tr></thead><tbody>"
                  + "".join(row(r) for r in F["construction"]) + "</tbody></table></div>") if F["construction"] else \
        "<p class='col'>Строек среди кандидатов этого сезона нет.</p>"
    for r in (x for x in F["construction"] if x.get("instrument_label")):
        n = NOTES[(city, season, r["id"])]
        srcs = " ".join(f"<a href='{esc(u)}'>{esc(t)}</a>" for t, u in n["sources"])
        build_html += (f"<div class='doc'><h3>{esc(r['name'])}: приборы видят потерю кроны, документы — стройку</h3>"
                       f"<p>{esc(n['what'])}</p><p>{esc(n['cause'])}</p><p><strong>{esc(n['verdict'])}</strong></p>"
                       f"<div class='src'>{srcs}</div></div>")

    unchecked_html = ""
    if n_k:
        unchecked_html = (f"<div class='warn col'><p><strong>{n_k} кандидатов не проверены вторым прибором.</strong> "
                          "Слой собран прогоном, который проверял только сильнейшие потери; эти секторы не публикуются "
                          "ни как потеря, ни как шум — до пересчёта.</p></div>")

    if P:
        prev_html = f"""<div class="scroll"><table><thead><tr><th></th><th>сезон {season - 1}</th><th>сезон {season}</th></tr></thead><tbody>
<tr><td>база</td><td class="num">{season - 4}–{season - 2}</td><td class="num">{base}</td></tr>
<tr><td>порог сезона, NDVI</td><td class="num">{prev_layer.threshold:.4f}</td><td class="num">{thr:.4f}</td></tr>
<tr><td>кандидатов: потеря сверх порога</td><td class="num">{len(P['lost'])}</td><td class="num">{cand}</td></tr>
<tr><td>жителей в кандидатах</td><td class="num">{fmt_int(P['lost_pop'])}</td><td class="num">{fmt_int(F['lost_pop'])}</td></tr>
<tr><td>из них стройка</td><td class="num">{len(P['construction'])}</td><td class="num">{n_b}</td></tr>
<tr><td>не подтверждено</td><td class="num">{len(P['unconfirmed'])}</td><td class="num">{n_u}</td></tr>
<tr><td><strong>подтверждённая потеря кроны</strong></td><td class="num"><strong>{len(P['confirmed'])}</strong></td><td class="num"><strong>{n_c}</strong></td></tr>
<tr><td>прибавили сверх порога</td><td class="num">{len(P['gained'])}</td><td class="num">{len(F['gained'])}</td></tr>
<tr><td>отказ: контроль несопоставим</td><td class="num">{P['refused']}</td><td class="num">{F['refused']}</td></tr>
</tbody></table></div>"""
        ratio = (cand / len(P["lost"])) if P["lost"] else None
        prev_note = ""
        if ratio and ratio >= 1.6:
            prev_note = (f"<div class='callout col'><p><strong>Кандидатов в {ratio:.1f} раза больше, чем сезоном раньше, подтверждённых — {n_c}.</strong> "
                         "Число кандидатов зависит от погоды сезона; число подтверждённых — от кроны. Публикуемая строка — вторая.</p></div>")
    else:
        prev_html, prev_note = "<p class='col'>Предыдущего сезона в пакете нет.</p>", ""

    doc = f"""<meta charset="utf-8"><title>Мониторинг · {esc(name)} {season}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>{CSS}</style>
<div class="page">
<header class="masthead">
  <div class="eyebrow">Мониторинг · сезон {season} · база {esc(base)} · {esc(name)}</div>
  <h1>{esc(headline)}</h1>
  <p class="standfirst">Годовой замер по {fmt_int(F['measured'])} статистическим секторам: где зелёность за лето {season} упала сильнее, чем у сопоставимых секторов, и что из этого — настоящая потеря кроны. Поимённо публикуются только потери, подтверждённые вторым прибором, и стройки. Остальное — числом.</p>
  <div class="dateline"><span>снимки: Sentinel-2, Dynamic World</span><span>единица: сектор Statbel</span><span>порог сезона: {thr:.4f}</span><span>сформировано {today_ru()}</span></div>
</header>

<section>
  <div class="sec-head"><span class="eyebrow">Воронка сезона</span><h2>От {cand} кандидатов до {n_c if n_c else 'нуля'} {'подтверждённой потери' if n_c == 1 else 'подтверждённых потерь'}</h2></div>
  <div class="funnel" role="table" aria-label="Воронка сезона">
    <div class="lab">Потеря NDVI сверх порога<small>кандидаты · {fmt_int(F['lost_pop'])} жителей</small></div><div class="bar"><i class="c-cand" style="width:{w(cand)}"></i></div><div class="val">{cand}</div>
    <div class="lab">Стройка<small>built вверх сверх {thr_built:.3f} · честная потеря, не деградация</small></div><div class="bar"><i class="c-build" style="width:{w(n_b)}"></i></div><div class="val">{n_b}</div>
    <div class="lab">Не подтверждено<small>ни trees вниз, ни built вверх · не публикуется поимённо</small></div><div class="bar"><i class="c-unc" style="width:{w(n_u)}"></i></div><div class="val">{n_u}</div>
    <div class="lab"><strong>Потеря кроны</strong><small>trees вниз сверх {thr_trees:.3f}, застройки нет · в отчёт</small></div><div class="bar"><i class="c-conf" style="width:{w(n_c)}"></i></div><div class="val">{n_c}</div>
    <div class="rule"></div>
    <div class="lab">Прибавили сверх порога<small>{fmt_int(F['gained_pop'])} жителей · вторым прибором не проверялись</small></div><div class="bar"><i class="c-gain" style="width:{w(len(F['gained']))}"></i></div><div class="val">{len(F['gained'])}</div>
  </div>
  <div class="col"><p>Правило двух приборов: потеря за один сезон публикуется, только если Dynamic World видит падение класса <code>trees</code> сверх собственного порога и не видит роста <code>built</code>. Первый прогон в 2024-м показал, зачем оно: из трёх сильнейших NDVI-потерь одна была стройкой, одна противоречила второму прибору, одна не подтвердилась ничем.</p></div>
  {unchecked_html}
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Подтверждённые потери кроны</span><h2>{'Что потеряно и почему' if n_c else 'Ни одной'}</h2></div>
  {conf_html}
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Стройка</span><h2>Потеря честная, но это застройка, не деградация</h2></div>
  <div class="col"><p>Секторы, где зелёность упала, а класс <code>built</code> вырос сверх порога. Это тоже потеря зелени в смысле статьи 8 — но её причина видна прибору, и она называется своим именем.</p></div>
  {build_html}
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Сезон к сезону</span><h2>Сравнение с {season - 1}-м</h2></div>
  {prev_html}
  {prev_note}
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Паспорт измерения</span><h2>Откуда пороги и что здесь не утверждается</h2></div>
  <div class="stats">
    <div class="stat"><b>{thr:.4f}</b><span>порог сезона, NDVI · {esc(layer.threshold_source or '')}</span></div>
    <div class="stat"><b>{thr_trees:.4f}</b><span>порог класса trees · {esc(m.layers['trees'].threshold_source or '')}</span></div>
    <div class="stat"><b>{thr_built:.4f}</b><span>порог класса built · {esc(m.layers['built'].threshold_source or '')}</span></div>
    <div class="stat"><b>{F['refused']}</b><span>отказ: контроль несопоставим (разрыв > {CONTROL['max_gap_ndvi']})</span></div>
  </div>
  <ul class="col">
    <li><strong>База скользящая.</strong> Лето {season} сравнивается с летними медианами {esc(base)}; эффект — против {CONTROL['n_controls']} подобранных секторов по состоянию «до», не ближе {CONTROL['exclusion_m']} м. Без контроля погода сезона красила бы весь город в один цвет.</li>
    <li><strong>Порог сезона — свой.</strong> Аудитный порог четырёхлетнего окна сюда не переносится: окно «после» здесь — один сезон, и нулевое распределение считается заново тем же прогоном.</li>
    <li><strong>Один сезон — не тренд.</strong> Подтверждённая потеря говорит, что крона упала; вернётся ли она, покажут следующие сезоны. Закон меряет раз в шесть лет; этот бюллетень — ежегодно.</li>
    <li><strong>Причина — из документов, не из прибора.</strong> Спутник называет сектор, документы называют причину. Потеря без документа публикуется как измерение, не как претензия.</li>
    <li>Значения классов Dynamic World — вероятности, не доли площади: интерпретируется только изменение.</li>
  </ul>
</section>

<div class="foot">Слой <code>cities/{esc(city)}/layers/monitoring_{season}.csv</code>, пороги — <code>cities/{esc(city)}/manifest.json</code>. Снимки: Copernicus Sentinel-2 SR Harmonized (маска Cloud Score+ ≥ {QUALITY['cloud_score_plus_min']}), Google Dynamic World V1. Секторы и население: Statbel. Вердикт каждого сектора берётся из слоя, не пересчитывается по округлённому порогу.</div>
</div>
"""
    out = SCRATCH / f"monitoring-{city}-{season}.html"
    out.write_text(doc, encoding="utf-8")
    print(f"→ {out}  ({len(doc.encode()) // 1024} КБ) · кандидатов {cand} · стройка {n_b} · не подтверждено {n_u} · "
          f"подтверждено {n_c} · не проверено {n_k} · прибавили {len(F['gained'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
