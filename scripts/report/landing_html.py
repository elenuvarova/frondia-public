#!/usr/bin/env python3
"""
Лендинг Frondia — экран 1. Герой — живой атлас города, не иллюстрация.

Собирается из уже сгенерированных страниц и сводок: SVG героя берётся из
`atlas-<city>.html` (без интерактива и подписей), числа — из
`cities/<city>/layers/article8_2024_summary.json`, ссылки — из LINKS ниже.
Пересборка детерминирована: тот же вход — тот же файл.

Запуск:
    .venv/bin/python scripts/report/landing_html.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.report.paths import DERIVED, OUT as SCRATCH  # noqa: E402
from scripts.report.background import background  # noqa: E402

LINKS = {
    "ninove": "https://claude.ai/code/artifact/a9e35a12-4c1b-4c64-848a-14c0ebc1db43",
    "droogdok": "https://claude.ai/code/artifact/a47736d3-f30e-4335-b8af-24e32da0648b",
    "a8b": "https://claude.ai/code/artifact/717101e7-1a3c-41d1-9299-cc1cde23fc5e",
    "a8a": "https://claude.ai/code/artifact/6ac3d09b-018b-42bd-a273-bafa7d037ebb",
    "atlasb": "https://claude.ai/code/artifact/ae0da47e-1db6-488b-b213-09e3f2282d4c",
    "atlasa": "https://claude.ai/code/artifact/b8c951fd-a398-4fcf-be50-7398262752e2",
    "reg": "https://claude.ai/code/artifact/2c4e2d71-5f2c-404c-b822-4cf4c18dc9f0",
    "law": "https://claude.ai/code/artifact/f190ca3b-0b87-4dba-af6e-5fdd5cf13a25",
    "monb": "https://claude.ai/artifact/GF5rb1hGewm5nieQxVpeco",      # бюллетень Брюсселя, сезон 2026
    "rega": "https://claude.ai/code/artifact/384e3689-532b-45ad-8a47-04b0c867e800",
    "spoor": "https://claude.ai/code/artifact/eb9b95e5-7d00-49cc-99e0-cc03fcb986e5",
    "methodpage": "https://claude.ai/code/artifact/f64f4628-9f22-4c33-ac7c-f4606a49a84f",
    "points": "https://claude.ai/code/artifact/a65bca81-6e1f-44c2-b4f9-4afdc74644ca",
    "mona": "https://claude.ai/artifact/Subw7ZKd2iJAWg1kYvcYan",      # бюллетень Антверпена, сезон 2026
}


def plural(n: int, one: str, few: str, many: str) -> str:
    n10, n100 = n % 10, n % 100
    return one if n10 == 1 and n100 != 11 else few if 2 <= n10 <= 4 and not 12 <= n100 <= 14 else many


def monitoring_cards() -> dict:
    """Карточки мониторинга — из последнего сезона в пакетах, теми же функциями, что бюллетень:
    слой, перенос по документам, воронка. Раньше числа были вписаны руками и устаревали каждый год."""
    from engine.manifest import Manifest
    from scripts.report.monitoring_html import apply_documents, funnel, load_layer
    out = {}
    per_city = {}
    for city in ("brussels", "antwerp"):
        m = Manifest.read(city)
        season = max(int(k.split("_")[1]) for k in m.layers if k.startswith("monitoring_"))
        F = funnel(apply_documents(load_layer(city, season), city, season), m.layers[f"monitoring_{season}"].threshold)
        per_city[city] = (season, F)
    season = per_city["brussels"][0]
    Fb, Fa = per_city["brussels"][1], per_city["antwerp"][1]
    cand = len(Fb["lost"]) + len(Fa["lost"])
    conf = Fb["confirmed"] + Fa["confirmed"]
    constr = len(Fb["construction"]) + len(Fa["construction"])
    unconf = len(Fb["unconfirmed"]) + len(Fa["unconfirmed"])
    moved = [r["name"].title() for r in Fb["construction"] + Fa["construction"] if r.get("instrument_label")]
    word = {0: "Ни одной потери кроны", 1: "Одна потеря кроны", 2: "Две потери кроны", 3: "Три потери кроны"}
    out["mon_season"] = season
    out["mon_cand"] = cand
    out["mon_conf"] = len(conf)
    out["mon_h3"] = f"{word.get(len(conf), f'{len(conf)} потерь кроны')} из {cand} кандидатов"
    moved_txt = (f"; {', '.join(moved)} приборы приняли за потерю кроны, а документы показали стройплощадку"
                 if moved else "")
    from scripts.report.monitoring_html import NOTES
    def named(r, city):
        n = NOTES.get((city, per_city[city][0], r["id"]), {})
        return r["name"].title() + (f" ({n['short']})" if n.get("short") else " (причина не установлена)")
    names = [named(r, "brussels") for r in Fb["confirmed"]] + [named(r, "antwerp") for r in Fa["confirmed"]]
    names_txt = (", ".join(names[:-1]) + " и " + names[-1]) if len(names) > 1 else "".join(names)
    out["mon_p"] = (f"Второй прибор не подтвердил {unconf}, {constr} "
                    f"{plural(constr, 'оказался стройкой', 'оказались стройками', 'оказались стройками')}{moved_txt}. "
                    + (f"Подтверждены {names_txt}." if names else "Ни один сектор не назван поимённо."))
    out["mona_h3"] = (f"{len(Fa['lost'])} {plural(len(Fa['lost']), 'кандидат', 'кандидата', 'кандидатов')}, "
                      f"{len(Fa['confirmed'])} {plural(len(Fa['confirmed']), 'потеря', 'потери', 'потерь')} кроны")
    out["mona_p"] = (f"{len(Fa['construction'])} {plural(len(Fa['construction']), 'стройка', 'стройки', 'строек')}, "
                     f"{len(Fa['unconfirmed'])} не подтверждено вторым прибором.")
    return out


def case_series(slug: str) -> tuple[int, int, list[int]]:
    """Сколько сезонов ряда дела сверх аудитного порога, из скольких, и какие в шуме —
    из самого дела, чтобы карточка не отставала от ряда на странице аудита."""
    C = json.loads(Path(f"data/registry/cases/{slug}.json").read_text())
    ot = C["over_time"]; thr = ot["threshold_audit"]
    below = [o["season"] for o in ot["seasons"] if o["effect"] <= thr]
    return len(ot["seasons"]) - len(below), len(ot["seasons"]), below


def series_cards() -> dict:
    k, n, below = case_series("droogdokkenpark")
    last = json.loads(Path("data/registry/cases/droogdokkenpark.json").read_text())["over_time"]["seasons"][-1]
    back = below and last["season"] not in below
    dd = (f"Сверх порога {k} {plural(k, 'сезон', 'сезона', 'сезонов')} из {n}"
          + (f"; провал {', '.join(map(str, below))}-го — стройка на доках, после него эффект вернулся." if back else
             f"; в шуме {', '.join(map(str, below))}." if below else "."))
    k2, n2, below2 = case_series("spoor-noord")
    sp = (f"ряд из {n2} {plural(n2, 'сезона', 'сезонов', 'сезонов')}, сверх порога {k2}"
          + ("; в засуху 2018-го преимущество исчезает." if 2018 in below2 else "."))
    dd_eff = json.loads(Path("data/registry/cases/droogdokkenpark.json").read_text()).get("defensible_effect")
    ru = lambda x, f: format(x, f).replace(".", ",")
    ni, sp_i = (next(i for i in json.loads(Path(f"data/registry/cases/{s}.json").read_text())["instruments"]
                     if i["key"].startswith("ndvi")) for s in ("ninove", "spoor-noord"))
    return {"dd_series": dd, "sp_series": sp,
            "dd_effect": f"{dd_eff:+.2f}".replace(".", ",") if dd_eff is not None else "—",
            # эффект и порог — из дела, чтобы карточка не расходилась со страницей аудита
            "ni_effect": ru(ni["effect"], "+.3f"), "ni_thr": ru(ni["threshold"], ".3f"),
            "sp_effect": ru(sp_i["effect"], "+.3f"), "sp_thr": ru(sp_i["threshold"], ".3f")}


def hero_svg(city: str) -> str:
    atlas = (DERIVED / f"atlas-{city}-map.svg").read_text(encoding="utf-8")
    svg = re.search(r'<svg class="map"[\s\S]*?</svg>', atlas).group(0)
    svg = re.sub(r'\s(?:tabindex|role|aria-label)="[^"]*"', "", svg)
    svg = re.sub(r"<title>[^<]*</title>", "", svg)
    svg = svg.replace('class="map" id="map"', 'class="hero-map" aria-hidden="true"')
    return re.sub(r'<g aria-hidden="true">[\s\S]*?</g>\s*</svg>', "</svg>", svg)


def main() -> int:
    svg = hero_svg("brussels")
    S8b = json.loads(Path("cities/brussels/layers/article8_2024_summary.json").read_text())
    S8a = json.loads(Path("cities/antwerp/layers/article8_2024_summary.json").read_text())
    lo, hi = S8b["equity_income_terciles"][0], S8b["equity_income_terciles"][-1]
    ratio = 100 * lo["trees_2024_wmean"] / hi["trees_2024_wmean"]
    L = LINKS
    ta = S8a["trend"]
    mon = monitoring_cards()
    from engine.registries.points import load as load_points
    n_points = sum(len(load_points(Path(f))) for f in
                   ("data/registry/named_points.json", "data/registry/named_points_brussels.json",
                    "data/registry/named_points_antwerp.json") if Path(f).exists())
    doc = TEMPLATE.format(svg=svg, ratio=ratio, measured=S8b["units_measured"] + S8a["units_measured"],
                          n_points=n_points, **mon, **series_cards(),
                          ant_trees=f"−{ta['trees_loss_sectors']} / +{ta['trees_gain_sectors']}", **L,
                          bg_raw=background('brussels')['k_raw'], bg_n=background('brussels')['n'],
                          bg_eff=background('brussels')['k_eff'])
    out = SCRATCH / "frondia-landing.html"
    out.write_text(doc, encoding="utf-8")
    print(f"→ {out}  ({len(doc)//1024} КБ)")
    return 0


TEMPLATE = r"""<title>Frondia</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>
:root{{--paper:#EFF1EC;--surface:#FFFFFF;--ink:#141B17;--muted:#5B6B62;--rule:#D5DAD3;--rule-2:#E4E8E3;--accent:#1E6E58;--accent-soft:#E2EDE7;--heat:#C2451C;
--g1:#3EB0A0;--g2:#22998d;--g3:#0f6b63;--l1:#EB7F7F;--l2:#e05f5f;--l3:#c9302f;--n:#D9DCD6;--u:#E6E9E3;--gap:#EFF1EC;
--display:"IBM Plex Sans Condensed","Helvetica Neue",Arial,sans-serif;--body:"IBM Plex Serif",Georgia,serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--paper:#12151A;--surface:#181D22;--ink:#E3E8E3;--muted:#8FA096;--rule:#2A3138;--rule-2:#21272D;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;
--g1:#3AA898;--g2:#1F8F82;--g3:#0F6B60;--l1:#DF5E5E;--l2:#C94848;--l3:#AD2E2E;--n:#2F353A;--u:#1C2126;--gap:#12151A}}}}
:root[data-theme="dark"]{{--paper:#12151A;--surface:#181D22;--ink:#E3E8E3;--muted:#8FA096;--rule:#2A3138;--rule-2:#21272D;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;
--g1:#3AA898;--g2:#1F8F82;--g3:#0F6B60;--l1:#DF5E5E;--l2:#C94848;--l3:#AD2E2E;--n:#2F353A;--u:#1C2126;--gap:#12151A}}
*{{box-sizing:border-box}}body{{background:var(--paper);color:var(--ink);font-family:var(--body);font-size:17px;line-height:1.6;-webkit-font-smoothing:antialiased}}
a{{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}}a:focus-visible{{outline:2px solid var(--accent);outline-offset:3px}}
.nav{{max-width:72rem;margin:0 auto;padding:1.2rem 1.5rem;display:flex;align-items:center;gap:1.6rem;font-family:var(--display);font-weight:600;font-size:.95rem}}
.nav .mark{{font-weight:700;font-size:1.15rem;letter-spacing:-.01em;margin-right:auto;text-decoration:none;color:var(--ink)}}.nav a{{text-decoration:none;color:var(--ink)}}
.nav .cta{{background:var(--ink);color:var(--paper);padding:.5rem 1rem;border-radius:999px}}
.hero{{position:relative;overflow:hidden;background:var(--surface);border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}}
.hero-map{{display:block;width:100%;max-height:78vh;height:auto;opacity:.92}}
.hero-map .sec{{stroke:var(--gap);stroke-width:1.2;stroke-linejoin:round}}
.hero-map .sec.g1{{fill:var(--g1)}}.hero-map .sec.g2{{fill:var(--g2)}}.hero-map .sec.g3{{fill:var(--g3)}}.hero-map .sec.l1{{fill:var(--l1)}}.hero-map .sec.l2{{fill:var(--l2)}}.hero-map .sec.l3{{fill:var(--l3)}}.hero-map .sec.n{{fill:var(--n)}}.hero-map .sec.u{{fill:var(--u)}}
.hero-copy{{position:absolute;left:0;right:0;bottom:0;padding:2.2rem 1.5rem 2.4rem;background:linear-gradient(to top,var(--surface) 55%,transparent);display:flex;flex-direction:column;gap:1rem;align-items:flex-start}}
.hero-copy .inner{{max-width:72rem;margin:0 auto;width:100%;display:flex;flex-direction:column;gap:1rem}}
h1{{font-family:var(--display);font-weight:700;font-size:clamp(2.4rem,6.5vw,4.6rem);line-height:.96;letter-spacing:-.025em;margin:0;max-width:16ch;text-wrap:balance}}
.lead{{font-size:1.15rem;max-width:36rem;margin:0}}
.btn{{display:inline-flex;align-items:center;gap:.5rem;font-family:var(--display);font-weight:600;background:var(--ink);color:var(--paper);padding:.8rem 1.3rem;border-radius:999px;text-decoration:none}}
.btn:after{{content:"›";font-size:1.2em;line-height:1}}
.caption{{font-family:var(--mono);font-size:.72rem;color:var(--muted)}}
.page{{max-width:72rem;margin:0 auto;padding:3rem 1.5rem 6rem;display:flex;flex-direction:column;gap:3rem}}
.eyebrow{{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}}
h2{{font-family:var(--display);font-weight:600;font-size:clamp(1.5rem,3.4vw,2.1rem);line-height:1.1;margin:0;text-wrap:balance}}
section{{display:flex;flex-direction:column;gap:1.1rem}}p{{margin:0}}.col{{max-width:36rem}}strong{{font-weight:600}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1rem}}
.card{{background:var(--surface);border:1px solid var(--rule);padding:1.2rem 1.25rem;display:flex;flex-direction:column;gap:.5rem;text-decoration:none;color:var(--ink)}}
.card:hover{{border-color:var(--ink)}}.card .k{{font-family:var(--mono);font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}}
.card b{{font-family:var(--display);font-weight:700;font-size:2.2rem;line-height:1;letter-spacing:-.02em}}.card h3{{font-family:var(--display);font-weight:600;font-size:1.05rem;margin:0}}
.card p{{font-size:.92rem;color:var(--muted);font-family:var(--display)}}
.strip{{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}}
.strip div{{background:var(--surface);padding:1rem 1.05rem;display:flex;flex-direction:column;gap:.15rem}}.strip b{{font-family:var(--display);font-weight:700;font-size:1.8rem;line-height:1}}.strip span{{font-family:var(--display);font-size:.78rem;color:var(--muted)}}
.how{{display:grid;grid-template-columns:repeat(auto-fit,minmax(15rem,1fr));gap:1.2rem}}.how div{{border-top:2px solid var(--ink);padding-top:.6rem;display:flex;flex-direction:column;gap:.3rem}}
.how h3{{font-family:var(--display);font-weight:600;font-size:1rem;margin:0}}.how p{{font-family:var(--display);font-size:.92rem;color:var(--muted)}}
.foot{{font-family:var(--display);font-size:.82rem;color:var(--muted);border-top:1px solid var(--rule);padding-top:1rem;display:flex;flex-wrap:wrap;gap:.4rem 1.4rem}}
@media (prefers-reduced-motion:reduce){{*{{transition:none}}}}
</style>
<nav class="nav"><a class="mark" href="#">Frondia</a><a href="{ninove}">Аудит</a><a href="{reg}">Реестр</a><a href="{atlasb}">Атлас</a><a href="#method">Методология</a><a class="cta" href="{ninove}">Смотреть аудит</a></nav>

<div class="hero">
  {svg}
  <div class="hero-copy"><div class="inner">
    <span class="caption">Брюссель · 686 секторов · изменение зелени 2017–2019 → 2021–2024 против контроля · это настоящие данные, не иллюстрация</span>
    <h1>Мы измеряем, что реально изменилось в городе</h1>
    <p class="lead">И отличаем изменение от шума — с порогом, измеренным на самом городе, а не назначенным. Города тратят деньги на зелень и не знают, что дало результат. Теперь знают.</p>
    <a class="btn" href="{ninove}">Смотреть аудит</a>
  </div></div>
</div>

<div class="page">
<section>
  <span class="eyebrow">Последние</span>
  <div class="cards">
    <a class="card" href="{ninove}"><span class="k">аудит вмешательства</span><b>{ni_effect}</b><h3>Parc de la Porte de Ninove</h3><p>Пустырь у канала стал парком. Порог {ni_thr}, два прибора сошлись, контроль поимённо, проверка сдвигом окна устояла.</p></a>
    <a class="card" href="{droogdok}"><span class="k">аудит вмешательства · Антверпен</span><b>{dd_effect}</b><h3>Droogdokkenpark</h3><p>Стандартное окно даёт +0,29, но половина — стройплощадка в базе. С базой до работ +0,15, втрое выше порога. {dd_series}</p></a>
    <a class="card" href="{monb}"><span class="k">мониторинг · сезон {mon_season}</span><b>{mon_cand} → {mon_conf}</b><h3>{mon_h3}</h3><p>{mon_p}</p></a>
    <a class="card" href="{spoor}"><span class="k">аудит вмешательства · Антверпен</span><b>{sp_effect}</b><h3>Park Spoor Noord</h3><p>Сортировочная станция стала парком. Порог своего окна {sp_thr}, {sp_series} Второго прибора у этих лет нет, и это сказано.</p></a>
    <a class="card" href="{a8a}"><span class="k">статья 8 · Антверпен</span><b>{ant_trees}</b><h3>Крона идёт в минус</h3><p>Секторы со значимой потерей и приростом кроны к базе 2024. Закон требует нулевой чистой потери к 2030-му.</p></a>
    <a class="card" href="{a8b}"><span class="k">статья 8 · Брюссель</span><b>{ratio:.0f} %</b><h3>Кроны у беднейшей трети</h3><p>От кроны богатейшей трети по доходу. Закон об этом молчит; мы печатаем.</p></a>
  </div>
</section>

<section>
  <div class="strip">
    <div><b>{measured}</b><span>секторов измерено в двух городах</span></div>
    <div><b>7 + 6</b><span>приборов откалибровано: Брюссель и Антверпен, каждый со своим порогом</span></div>
    <div><b>251</b><span>вмешательств в реестре с бюджетами и сроками</span></div>
    <div><b>2,13 млрд €</b><span>сведено с тем, что измерил спутник</span></div>
  </div>
</section>

<section id="method">
  <span class="eyebrow">Как считается</span>
  <h2>Четыре правила, из-за которых числу можно верить</h2>
  <div class="how">
    <div><h3>Против контроля, не «до/после»</h3><p>За период позеленел весь город. Эффект — изменение объекта минус изменение двенадцати похожих секторов, где ничего не делали. Без контроля за порог вышли бы {bg_raw} из {bg_n} секторов Брюсселя, с контролем — {bg_eff}.</p></div>
    <div><h3>Порог измерен</h3><p>Каждый сектор по очереди играет «вмешательство»; распределение эффектов — шум метода; порог — его 95-й процентиль. Отдельно для каждого города.</p></div>
    <div><h3>Два прибора</h3><p>Зелёность и классы покрытия по одним снимкам. Один говорит «изменилось», второй — что именно: раскрыли и засадили, стройка, рекультивация.</p></div>
    <div><h3>Отказ — результат</h3><p>Нет сопоставимого контроля, объект меньше гектара, работы внутри окна, мало снимков — вердикт не выносится. Это честнее числа.</p></div>
  </div>
  <p class="col">Чего не измеряем и не притворяемся: охлаждение, реставрации существующих парков, рассеянные уличные посадки, причину изменения без документа. Всё это установлено измерением, а не осторожностью.</p>
  <p class="col"><a href="{methodpage}"><strong>Полная методология с числом отказов</strong></a> — сколько раз каждая защита отказалась считать: 68 парков из 250 без сопоставимого контроля, 43 кандидата мониторинга из 44 отсеяны правилом двух приборов, 25 реставраций в шуме.</p>
</section>

<section>
  <span class="eyebrow">Страницы</span>
  <div class="cards">
    <a class="card" href="{atlasb}"><span class="k">атлас</span><h3>Брюссель</h3><p>686 секторов, легенда — нулевое распределение метода, зелень по доходу.</p></a>
    <a class="card" href="{atlasa}"><span class="k">атлас</span><h3>Антверпен</h3><p>457 секторов, свой порог 0,046, потерь больше, чем приростов.</p></a>
    <a class="card" href="{mona}"><span class="k">мониторинг · Антверпен {mon_season}</span><h3>{mona_h3}</h3><p>{mona_p} Бюллетень сезона — то, что закон просит раз в шесть лет.</p></a>
    <a class="card" href="{reg}"><span class="k">реестр</span><h3>251 вмешательство</h3><p>Контракты и Beliris с бюджетами, сроками, статусом разметки и измерением.</p></a>
    <a class="card" href="{rega}"><span class="k">реестр · Антверпен</span><h3>252 проекта, 5 проверяемых</h3><p>Воронка данных города с обязанностью по закону: где теряется возможность что-либо доказать — на сроках, границах и размере следа.</p></a>
    <a class="card" href="{points}"><span class="k">вторая линия · выполнение</span><b>{n_points}</b><h3>Точки, названные заранее</h3><p>Урна и скамейка не меняют зелёность — эффект от них не измерить. Проверяется другое: появился объект там, где его назвали. Точки зафиксированы датой и хешем до проверки.</p></a>
    <a class="card" href="{methodpage}"><span class="k">как это устроено</span><h3>Метод и его отказы</h3><p>Три решения, пять защит и число срабатываний каждой на настоящих данных двух городов.</p></a>
    <a class="card" href="{law}"><span class="k">почему сейчас</span><h3>Покупатель по закону</h3><p>Регламент 2024/1991, ст. 8: нулевая потеря зелени и кроны к 2030-му. Бельгия сорвала срок плана.</p></a>
  </div>
</section>

<p class="foot"><span>Copernicus Sentinel-2 · Dynamic World · Landsat</span><span>Statbel · OpenStreetMap · quartiers.brussels · beliris.be</span><span>доказательство фиксировано, подача настраивается</span><span>2 сентября 2026</span></p>
</div>
"""


if __name__ == "__main__":
    raise SystemExit(main())
