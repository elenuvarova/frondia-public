#!/usr/bin/env python3
"""
Реестр вмешательств — экран 6 в публичной форме.

Что это
───────
Единственный слой, которого нет ни у кого: что город делал, когда, за сколько —
сведённый с тем, что спутник измерил. 98 квартальных контрактов quartiers.brussels
(бюджеты из описаний) + 153 завершённых проекта Beliris (бюджеты и даты со
страниц) + связи с измеренными парками.

Честность в структуре
─────────────────────
· Статус разметки виден: «извлечено правилом», «проверено человеком», «не
  сопоставлено». Реестр без статуса — это красивая таблица, не источник.
· Сроки печатаются как статус по окнам, не как вердикт: «сдан в окне после —
  стандартное окно ловит стройку» честнее, чем число.
· Бюджет — на весь проект; парк — часть. «N млн купили +X» здесь не пишется.

Запуск:
    .venv/bin/python scripts/report/registry_html.py
"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.audit import windows_for_completion

from scripts.report.paths import DERIVED, OUT as SCRATCH  # noqa: E402

DOMAIN_RU = {"vert": "зелень", "public": "общественное пространство", "mobilite": "мобильность",
             "batiment": "здания", "culture": "культура", "loisir": "досуг"}


def esc(x) -> str:
    return html.escape(str(x))


def eur(v) -> str:
    try:
        return f"{int(float(v)):,}".replace(",", " ") + " €"
    except (TypeError, ValueError):
        return "—"


def timing(year_end: int | None) -> tuple[str, str]:
    """→ (класс, текст) по стандартному окну 2017–2019 → 2021–2024."""
    if not year_end:
        return "t-unk", "срок неизвестен"
    if year_end <= 2019:
        return "t-old", "сдан до окна «до»" if year_end < 2017 else "сдан в окне «до»"
    if year_end >= 2021:
        return "t-new", "сдан в окне «после» — стройка в кадре"
    return "t-ok", "укладывается в окно"


def main() -> int:
    contracts = json.loads(Path("data/registry/contracts_raw.json").read_text())
    c_budgets = json.loads(Path("data/registry/contracts_budgets.json").read_text())
    c_links = list(csv.DictReader(Path("data/registry/contract_park_links.csv").open()))
    baseline = {r["id"]: r for r in json.loads(Path("data/registry/greening_baseline.json").read_text())}
    # эталон вычитки: форма файла могла меняться — читаем любую из трёх
    gold = {}
    gp = Path("data/registry/greening_gold.json")
    if gp.exists():
        raw = json.loads(gp.read_text())
        # метки лежат под содержательным ключом рядом со служебными «_», «_labels»
        if isinstance(raw, dict):
            inner = [v for k, v in raw.items() if not str(k).startswith("_")]
            raw = inner[0] if len(inner) == 1 and isinstance(inner[0], (dict, list)) else raw
        items = raw.items() if isinstance(raw, dict) else ((g.get("id"), g) for g in raw if isinstance(g, dict))
        for k, v in items:
            try:
                key = int(k)
            except (TypeError, ValueError):
                continue
            gold[key] = v.get("label", "") if isinstance(v, dict) else str(v)
    beliris = json.loads(Path("data/registry/beliris_dated.json").read_text())
    b_measured = list(csv.DictReader(Path("data/registry/beliris_measured.csv").open()))
    b_link = {}
    for r in b_measured:
        b_link.setdefault(r["project"], r)
    # Landsat-аудит старых проектов (≤ 2016): окна под проект, порог под окно, 30 м.
    # Отдельный прибор — отдельная пометка; с сентинелевскими вердиктами не смешивается.
    b_landsat = {}
    # читаем слой из пакета — там он зарегистрирован в манифесте; сырой файл только запасной
    lp = Path("cities/brussels/layers/park_audit_landsat.csv")
    if not lp.exists():
        lp = Path("data/registry/beliris_landsat_audit.csv")
    if lp.exists():
        for r in csv.DictReader(lp.open()):
            b_landsat.setdefault(r["project"], r)
    links_by_contract = {}
    for r in c_links:
        links_by_contract.setdefault(r["contract_id"], []).append(r)

    rows = []
    # ── квартальные контракты ─────────────────────────────────────────────────
    for c in contracts:
        cid = str(c["id"])
        bl = baseline.get(c["id"], {})
        if c["id"] in gold:
            status = ("проверено человеком", "s-gold")
        elif bl.get("has_greening_measure"):
            status = ("мера озеленения — извлечено правилом", "s-rule")
        elif bl.get("state_only"):
            status = ("только описание состояния", "s-state")
        else:
            status = ("озеленение не упомянуто", "s-none")
        lk = links_by_contract.get(cid, [])
        park = "; ".join(f"{l['park']} ({l['verdict']}{', ' + ('%+.3f' % float(l['ndvi_effect'])) if l['ndvi_effect'] else ''})" for l in lk) or "—"
        tcls, ttxt = timing(c["year_end"])
        rows.append({
            "src": "contrat", "src_label": "Квартальный контракт", "name": c["name"], "commune": c["commune"] or "—",
            "domain": "квартал", "years": f"{c['year_start']}–{c['year_end']}", "year_end": c["year_end"],
            "budget": c_budgets.get(cid, {}).get("total_eur"), "park": park, "status": status[0], "scls": status[1],
            "tcls": tcls, "ttxt": ttxt, "url": c["url"],
            "measured": bool(lk), "verdict": (lk[0]["verdict"] if lk else ""),
        })
    # ── Beliris ──────────────────────────────────────────────────────────────
    for p in beliris:
        m = b_link.get(p["title"]); L = b_landsat.get(p["title"])
        if L and (not m or m["verdict"] in ("контроль несопоставим", "шум")) and p.get("end_year") and p["end_year"] <= 2016:
            small = float(L["area_ha"]) < 3
            lv = "мелкий для 30 м" if small else L["verdict"]
            park = f"{L['park'].split(' - ')[0]} ({lv}, {float(L['effect']):+.3f} · Landsat, окно {L['window']})"
            verdict_src = lv; measured = True
        elif m:
            park = f"{m['park']} ({m['verdict']}, {float(m['ndvi_effect']):+.3f})"; verdict_src = m["verdict"]; measured = True
        else:
            park = "—"; verdict_src = ""; measured = False
        tcls, ttxt = timing(p.get("end_year"))
        if L and p.get("end_year") and p["end_year"] <= 2016:
            tcls, ttxt = "t-ok", f"окно под проект (Landsat): {L['window']}"
        rows.append({
            "src": "beliris", "src_label": "Beliris", "name": p["title"], "commune": "—",
            "domain": DOMAIN_RU.get(p.get("domaine", ""), p.get("domaine", "")),
            "years": p.get("end") or "—", "year_end": p.get("end_year"),
            "budget": p.get("budget_eur"), "park": park, "status": "сопоставлен по координате" if (m or L) else "не сопоставлен",
            "scls": "s-coord" if (m or L) else "s-none", "tcls": tcls, "ttxt": ttxt, "url": p.get("url", ""),
            "measured": measured, "verdict": verdict_src,
        })

    n = len(rows); total_budget = sum(r["budget"] for r in rows if r["budget"])
    with_budget = sum(1 for r in rows if r["budget"])
    measured = [r for r in rows if r["measured"]]
    sig = [r for r in measured if r["verdict"] in ("ПОЗЕЛЕНЕЛ", "ПОТЕРЯЛ")]
    auditable = sum(1 for r in rows if r["year_end"] and windows_for_completion(r["year_end"] + (1 if r["src"] == "contrat" else 0), data_from=2000))
    landsat_n = sum(1 for r in rows if "Landsat" in r["park"])
    # Предрегистрация: записи + снятая база «до»
    pre_rows = ""
    pre_path = Path("data/registry/preregistered.json"); base_path = Path("data/registry/preregistered_baseline.csv")
    if pre_path.exists():
        base = {}
        if base_path.exists():
            for b in csv.DictReader(base_path.open()):
                base.setdefault(b["id"], {})[b["instrument"]] = (b["value"], b["area_ha"])
        ctrl_path = Path("data/registry/preregistered_controls.json")
        ctrl = {c["id"]: c for c in json.loads(ctrl_path.read_text())} if ctrl_path.exists() else {}
        for rec in json.loads(pre_path.read_text()):
            bb = base.get(rec["id"], {}); cc = ctrl.get(rec["id"])
            ctrl_txt = "—" if not cc else (f"12 секторов, разрыв {cc['gap']:+.3f}" if cc["comparable"] else f"несопоставим ({cc['gap']:+.3f})")
            ndvi = bb.get("ndvi", ("—", "—")); built = bb.get("built", ("—", ""))
            src = rec["geometry_source"]
            src_txt = "полигон Beliris" if src.startswith("beliris") else f"OSM {src.split(':', 1)[1]}"
            expect = rec["note"].split(";")[0].replace("ожидание: ", "")
            pre_rows += (f'<tr><td>{esc(rec["name"])}</td><td class="mono">{src_txt}</td><td class="mono">{ndvi[1]}</td>'
                         f'<td class="mono">{rec["registered_at"]}</td><td class="mono">{rec["geometry_hash"]}</td>'
                         f'<td class="mono">{ndvi[0]}</td><td class="mono">{built[0]}</td><td class="mono">{ctrl_txt}</td><td>{esc(expect)}</td></tr>')
    communes = sorted({r["commune"] for r in rows if r["commune"] != "—"})
    st = Counter(r["ttxt"] for r in rows)

    def tr(r):
        return (f"<tr data-src='{r['src']}' data-com='{esc(r['commune'])}' data-v='{esc(r['verdict'] or 'none')}' data-t='{r['tcls']}'>"
                f"<td><span class='tag'>{esc(r['src_label'])}</span></td>"
                f"<td><a href='{esc(r['url'])}'>{esc(r['name'])}</a></td><td>{esc(r['commune'])}</td><td>{esc(r['domain'])}</td>"
                f"<td class='num'>{esc(r['years'])}</td><td class='num'>{eur(r['budget'])}</td>"
                f"<td>{esc(r['park'])}</td><td><span class='st {r['scls']}'>{esc(r['status'])}</span></td>"
                f"<td><span class='st {r['tcls']}'>{esc(r['ttxt'])}</span></td></tr>")
    rows.sort(key=lambda r: (-(r["year_end"] or 0), r["name"]))
    body = "\n".join(tr(r) for r in rows)

    doc = f"""<title>Реестр вмешательств · Брюссель</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>
:root{{--paper:#EFF1EC;--surface:#FFFFFF;--ink:#141B17;--muted:#5B6B62;--rule:#D5DAD3;--rule-2:#E4E8E3;--accent:#1E6E58;--accent-soft:#E2EDE7;--heat:#C2451C;--heat-soft:#F7E6DE;
--display:"IBM Plex Sans Condensed","Helvetica Neue",Arial,sans-serif;--body:"IBM Plex Serif",Georgia,serif;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--measure:34rem;--wide:72rem}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--paper:#12151A;--surface:#181D22;--ink:#E3E8E3;--muted:#8FA096;--rule:#2A3138;--rule-2:#21272D;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14}}}}
:root[data-theme="dark"]{{--paper:#12151A;--surface:#181D22;--ink:#E3E8E3;--muted:#8FA096;--rule:#2A3138;--rule-2:#21272D;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14}}
*{{box-sizing:border-box}}body{{background:var(--paper);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}}
.page{{max-width:var(--wide);margin:0 auto;padding:3.5rem 1.5rem 6rem;display:flex;flex-direction:column;gap:2.25rem}}
.col{{max-width:var(--measure)}}.masthead{{display:flex;flex-direction:column;gap:.9rem;padding-bottom:1.75rem;border-bottom:2px solid var(--ink)}}
.eyebrow{{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
h1{{font-family:var(--display);font-weight:700;font-size:clamp(2.2rem,6vw,3.6rem);line-height:.98;letter-spacing:-.02em;margin:0;text-wrap:balance}}
.standfirst{{font-size:1.1rem;line-height:1.5;max-width:40rem;margin:0}}.dateline{{font-family:var(--mono);font-size:.76rem;color:var(--muted);display:flex;flex-wrap:wrap;gap:.4rem 1.4rem}}
p{{margin:0}}strong{{font-weight:600}}a{{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}}
.stat{{background:var(--surface);padding:.9rem 1rem;display:flex;flex-direction:column;gap:.15rem}}.stat b{{font-family:var(--display);font-weight:700;font-size:1.9rem;line-height:1;letter-spacing:-.02em}}.stat span{{font-family:var(--display);font-size:.78rem;color:var(--muted);line-height:1.3}}
.filters{{display:flex;flex-wrap:wrap;gap:.6rem 1.2rem;align-items:center;font-family:var(--display);font-size:.9rem}}
.filters select,.filters input[type=search]{{font:inherit;padding:.4rem .6rem;border:1px solid var(--rule);background:var(--surface);color:var(--ink)}}
.filters label{{display:inline-flex;gap:.4rem;align-items:center}}
.scroll{{overflow-x:auto;max-width:100%;background:var(--surface);border:1px solid var(--rule)}}
table{{border-collapse:collapse;width:100%;min-width:64rem;font-size:.85rem;font-family:var(--display);font-weight:500}}
th{{text-align:left;font-family:var(--mono);font-weight:500;font-size:.64rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--ink);padding:.7rem .7rem .5rem;vertical-align:bottom;position:sticky;top:0;background:var(--surface)}}
td{{border-bottom:1px solid var(--rule-2);padding:.5rem .7rem;vertical-align:top;line-height:1.35}}td.num{{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}}
tr[hidden]{{display:none}}
.tag{{font-family:var(--mono);font-size:.62rem;letter-spacing:.05em;text-transform:uppercase;padding:.1rem .35rem;border:1px solid var(--rule);white-space:nowrap}}
.st{{font-family:var(--mono);font-size:.66rem;letter-spacing:.03em;padding:.12rem .4rem;border:1px solid currentColor;white-space:nowrap}}
.s-gold{{color:var(--accent)}}.s-rule{{color:var(--ink)}}.s-state,.s-none{{color:var(--muted)}}.s-coord{{color:var(--ink)}}
.t-ok{{color:var(--accent)}}.t-new{{color:var(--heat)}}.t-old,.t-unk{{color:var(--muted)}}
.callout{{background:var(--accent-soft);border-left:3px solid var(--accent);padding:1rem 1.2rem;max-width:var(--measure)}}
.warn{{background:var(--heat-soft);border-left:3px solid var(--heat);padding:1rem 1.2rem;max-width:var(--measure)}}
.count{{font-family:var(--mono);font-size:.78rem;color:var(--muted)}}
.foot{{font-family:var(--display);font-size:.82rem;color:var(--muted);border-top:1px solid var(--rule);padding-top:1rem;max-width:46rem}}
.pre h2{{font-family:var(--display);font-size:1.5rem;margin:0 0 .5rem}}.pre{{display:flex;flex-direction:column;gap:.75rem}}
</style>
<div class="page">
<header class="masthead">
  <div class="eyebrow">Реестр вмешательств · Брюссельский регион · 1994–2027</div>
  <h1>Что город делал и сколько платил</h1>
  <p class="standfirst">{n} вмешательств из двух источников — квартальные контракты quartiers.brussels и проекты Beliris — с бюджетами, сроками и статусом разметки. Там, где документ называет парк, а спутник его измерил, стоит эффект. Единственный слой, которого нет ни у кого, и он дорожает с каждой строкой.</p>
  <div class="dateline"><span>{with_budget} с бюджетом · {eur(total_budget)}</span><span>сопоставлено с измерением: {len(measured)}</span><span>2 сентября 2026</span></div>
</header>

<section class="stats">
  <div class="stat"><b>{n}</b><span>вмешательств в реестре</span></div>
  <div class="stat"><b>{eur(total_budget).replace(' €','')}</b><span>€ суммарно, у {with_budget} с известным бюджетом</span></div>
  <div class="stat"><b>{len(measured)}</b><span>сопоставлено с измеренным объектом</span></div>
  <div class="stat"><b>{len(sig)}</b><span>из них с эффектом сверх порога</span></div>
  <div class="stat"><b>{auditable}</b><span>пригодны к аудиту по срокам при окнах под проект и Landsat</span></div>
</section>

<div class="warn col"><p><strong>Сроки — главный ограничитель.</strong> {st.get('сдан в окне «после» — стройка в кадре', 0)} вмешательств сданы внутри окна «после» — стандартное измерение поймает стройку, а не результат. {st.get('сдан до окна «до»', 0) + st.get('сдан в окне «до»', 0)} сданы до 2020-го. Реестр печатает это статусом, а не числом.</p></div>

<div class="filters" role="group" aria-label="Фильтры">
  <label>источник <select id="f-src"><option value="">все</option><option value="contrat">Квартальные контракты</option><option value="beliris">Beliris</option></select></label>
  <label>коммуна <select id="f-com"><option value="">все</option>{"".join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in communes)}</select></label>
  <label>измерение <select id="f-v"><option value="">все</option><option value="ПОЗЕЛЕНЕЛ">позеленел</option><option value="ПОТЕРЯЛ">потерял</option><option value="шум">шум</option><option value="контроль несопоставим">контроль несопоставим</option><option value="none">не сопоставлено</option></select></label>
  <label>сроки <select id="f-t"><option value="">все</option><option value="t-ok">укладывается</option><option value="t-new">в окне «после»</option><option value="t-old">до 2020</option><option value="t-unk">неизвестно</option></select></label>
  <input type="search" id="f-q" placeholder="поиск по названию" aria-label="Поиск по названию">
  <span class="count" id="count"></span>
</div>

<div class="scroll"><table id="reg"><thead><tr><th>источник</th><th>вмешательство</th><th>коммуна</th><th>домен</th><th>сроки</th><th>бюджет</th><th>измеренный объект</th><th>разметка</th><th>сроки vs окна</th></tr></thead>
<tbody>{body}</tbody></table></div>

<div class="callout col"><p><strong>Два прибора, две пометки.</strong> Проекты, сданные до 2017-го, Sentinel-2 измерить не может — окно «до» упирается в начало ряда. Для них стоит вердикт по <strong>Landsat, 30 м</strong>, с окном под проект и порогом под окно ({landsat_n} строк). Объекты меньше 3 га на 30 м — 11–30 пикселей, помечены «мелкий для 30 м» и как измерение не считаются. Семь крупных реставраций 2009–2016 — все в шуме: реставрация не меняет растительность по построению.</p></div>
<section class="pre">
<h2>Зафиксировано до работ</h2>
<p class="col">Проекты Beliris в статусе «в проекте»: след, хеш геометрии и ожидаемый исход записаны <strong>раньше</strong> начала работ, база «до» снята и контроль подобран сейчас (лето 2023–2025) — включая отказ «контроль несопоставим», записанный до результата. Будущий аудит не сможет обвести контур там, где позеленело, и не сможет подобрать окно «до» под результат. Проект, где работы уже идут (Canal-Midi), контракт записи отверг.</p>
<div class="tablewrap"><table><thead><tr><th>Проект</th><th>След</th><th>га</th><th>Фиксация</th><th>Хеш</th><th>NDVI до</th><th>built до</th><th>Контроль</th><th>Ожидание</th></tr></thead>
<tbody>{pre_rows}</tbody></table></div>
</section>
<div class="callout col"><p><strong>Как читать «разметку».</strong> «Проверено человеком» — вычитанный эталон. «Извлечено правилом» — детерминированное сито: точность 33 %, полнота 100 %, поэтому мусор возможен, пропуск — нет. «Только описание состояния» — контракт говорит «уже зелено», а не «озеленим»; в меры не идёт. Beliris сопоставлен по координате в радиусе 500 м — это близость, не тождество.</p></div>

<p class="foot">Источники: quartiers.brussels (98 контрактов, бюджеты из описаний), beliris.be (153 завершённых проекта, бюджеты и даты со страниц), OSM (парки ≥ 1 га), измерение — Sentinel-2 / Dynamic World против подобранного контроля. Ярлык домена — как администрация подшила проект, не что произошло: сильнейший зелёный эффект города числится как «общественное пространство».</p>
</div>
<script>
(function(){{
  const rows=[...document.querySelectorAll('#reg tbody tr')],cnt=document.getElementById('count');
  const f={{src:document.getElementById('f-src'),com:document.getElementById('f-com'),v:document.getElementById('f-v'),t:document.getElementById('f-t'),q:document.getElementById('f-q')}};
  function apply(){{
    const q=f.q.value.trim().toLowerCase();let shown=0;
    rows.forEach(r=>{{
      const ok=(!f.src.value||r.dataset.src===f.src.value)&&(!f.com.value||r.dataset.com===f.com.value)&&(!f.v.value||r.dataset.v===f.v.value)&&(!f.t.value||r.dataset.t===f.t.value)&&(!q||r.children[1].textContent.toLowerCase().includes(q));
      r.hidden=!ok;if(ok)shown++;}});
    cnt.textContent=shown+' из '+rows.length;}}
  Object.values(f).forEach(el=>el.addEventListener('input',apply));apply();
}})();
</script>
"""
    out = SCRATCH / "registry-brussels.html"
    out.write_text(doc, encoding="utf-8")
    print(f"→ {out}  ({len(doc)//1024} КБ) · {n} строк · бюджет {eur(total_budget)} · измерено {len(measured)} · значимо {len(sig)} · аудируемо {auditable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
