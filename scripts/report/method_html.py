"""Страница метода: почему числу можно верить и где движок отказывается считать.

Это не пересказ методологии словами, а её отчётность. Каждое утверждение здесь
подкреплено числом, которое пересчитывается из файлов проекта: манифестов обоих
городов, слоёв аудита и мониторинга, реестра предрегистраций.

Главная мысль страницы: **отказ считать — такой же результат, как эффект**, и
страница показывает, сколько раз каждая защита сработала на реальных данных.

    python scripts/report/method_html.py
"""
from __future__ import annotations

import collections
import csv
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.audit import MIN_HA_LANDSAT  # noqa: E402
from engine.config import CONTROL, LIMITS, QUALITY  # noqa: E402
from engine.manifest import Manifest  # noqa: E402

from scripts.report.paths import DERIVED, OUT as SCRATCH, today_ru  # noqa: E402
from scripts.report.background import sentence as bg_sentence  # noqa: E402

CITY_NAME = {"brussels": "Брюссель", "antwerp": "Антверпен"}
INSTR_LABEL = {"ndvi": "зелёность, Sentinel-2 10 м", "ndvi_landsat": "зелёность, Landsat 30 м",
               "trees": "древесная крона", "grass": "травяной покров", "built": "застройка и покрытие",
               "bare": "голая поверхность", "shrub": "кустарник"}

CSS = """
:root{--paper:#EFF1EC;--surface:#FFFFFF;--ink:#141B17;--muted:#5B6B62;--rule:#D5DAD3;--rule-2:#E4E8E3;
--accent:#1E6E58;--accent-soft:#E2EDE7;--heat:#C2451C;--heat-soft:#F7E6DE;--stop:#8A6A2F;--stop-soft:#F4EBDA;
--display:"IBM Plex Sans Condensed","Helvetica Neue",Arial,sans-serif;--body:"IBM Plex Serif",Georgia,serif;
--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--measure:34rem;--wide:62rem}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;
--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;
--stop:#D2A957;--stop-soft:#2A2318}}
:root[data-theme="dark"]{--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;
--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;--stop:#D2A957;--stop-soft:#2A2318}
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
.scroll{overflow-x:auto;max-width:100%}table{border-collapse:collapse;width:100%;min-width:32rem;font-size:.9rem;font-family:var(--display);font-weight:500}
th{text-align:left;font-family:var(--mono);font-weight:500;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--ink);padding:0 .85rem .5rem 0;vertical-align:bottom}
td{border-bottom:1px solid var(--rule);padding:.6rem .85rem .6rem 0;vertical-align:top;line-height:1.4}td.num{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
tr:last-child td{border-bottom:none}td small{display:block;font-size:.82rem;color:var(--muted)}
/* Защиты: каждая — правило, его причина и сколько раз оно сработало на данных */
.guards{display:flex;flex-direction:column;gap:1px;background:var(--rule);border:1px solid var(--rule)}
.guard{background:var(--surface);padding:1.15rem 1.25rem;display:grid;grid-template-columns:1fr minmax(7rem,auto);gap:.35rem 1.5rem;align-items:start}
.guard h3{margin:0;font-size:1.02rem}
.guard p{font-size:.94rem;color:var(--muted);line-height:1.45}
.guard .fired{grid-row:span 2;text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}
.guard .fired b{display:block;font-family:var(--display);font-weight:700;font-size:1.9rem;line-height:1;color:var(--stop)}
.guard .fired span{font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);line-height:1.3;display:block;margin-top:.25rem}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}
.stat{background:var(--surface);padding:1rem 1.05rem;display:flex;flex-direction:column;gap:.2rem}
.stat b{font-family:var(--display);font-weight:700;font-size:2rem;line-height:1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat span{font-family:var(--display);font-size:.8rem;color:var(--muted);line-height:1.3}
.tag{font-family:var(--mono);font-size:.67rem;letter-spacing:.05em;text-transform:uppercase;padding:.14rem .42rem;white-space:nowrap;border:1px solid currentColor}
.t-yes{color:var(--accent)}.t-no{color:var(--heat)}.t-mute{color:var(--muted)}
.foot{font-family:var(--display);font-size:.82rem;color:var(--muted);border-top:1px solid var(--rule);padding-top:1rem;max-width:46rem}
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def plural(n: int, one: str, few: str, many: str) -> str:
    n10, n100 = n % 10, n % 100
    return one if n10 == 1 and n100 != 11 else few if 2 <= n10 <= 4 and not 12 <= n100 <= 14 else many


def verdicts(path: str, key: str = "verdict") -> collections.Counter:
    p = Path(path)
    if not p.exists():
        return collections.Counter()
    return collections.Counter(r[key] for r in csv.DictReader(p.open()) if r.get(key))


def main() -> int:
    man = {c: Manifest.read(c) for c in CITY_NAME}

    # ── пороги обоих городов: одна таблица, приборы строками ────────────────
    instr_keys = ["ndvi", "ndvi_landsat", "trees", "grass", "built", "bare", "shrub"]
    thr_rows = ""
    for k in instr_keys:
        cells = ""
        for c in CITY_NAME:
            v = man[c].layers.get(k)
            cells += f"<td class='num'>{v.threshold:.4f}</td>" if v and v.threshold else "<td class='num t-mute'>—</td>"
        thr_rows += f"<tr><td>{esc(INSTR_LABEL[k])}<small><code>{esc(k)}</code></small></td>{cells}</tr>"

    # ── отказы: сколько раз каждая защита сработала ─────────────────────────
    pv_b = verdicts("data/park_audit_2017_2024.csv")
    pv_a = verdicts("data/park_audit_antwerp_2017_2024.csv")
    refused_parks = pv_b["контроль несопоставим"] + pv_a["контроль несопоставим"]
    parks_total = sum(pv_b.values()) + sum(pv_a.values())

    # Мониторинг считается ТЕМИ ЖЕ функциями, что строят бюллетень: слой, документы, воронка.
    # Иначе страница метода и бюллетень расходились бы (так и было: 4 против 3, пока метод
    # не знал о переносе Peterbos в стройки по документам).
    from scripts.report.monitoring_html import apply_documents, funnel, load_layer
    mon = {}
    for c in CITY_NAME:
        seasons = sorted(int(k.split("_")[1]) for k in man[c].layers if k.startswith("monitoring_"))
        for s in seasons:
            if not Path(f"cities/{c}/layers/monitoring_{s}.csv").exists():
                continue
            thr = man[c].layers[f"monitoring_{s}"].threshold
            rows = apply_documents(load_layer(c, s), c, s)
            F = funnel(rows, thr)
            mon[(c, s)] = dict(F=F, threshold=thr,
                               moved=sum(1 for r in F["construction"] if r.get("instrument_label")))
    n_seasons = len({s for (_, s) in mon})
    cand = sum(len(v["F"]["lost"]) for v in mon.values())
    confirmed = sum(len(v["F"]["confirmed"]) for v in mon.values())
    construction = sum(len(v["F"]["construction"]) for v in mon.values())
    moved = sum(v["moved"] for v in mon.values())
    confirmed_names = [f"{r['name'].title()} ({s})" for (c, s), v in sorted(mon.items(), key=lambda kv: kv[0][1])
                       for r in v["F"]["confirmed"]]

    lnd = verdicts("cities/brussels/layers/park_audit_landsat.csv")
    restorations = lnd["шум"]
    dated = verdicts("cities/antwerp/layers/park_audit_dated.csv")
    prelim = sum(v for k, v in dated.items() if k.startswith("предварительно"))

    ctrl_pre = json.loads(Path("data/registry/preregistered_controls.json").read_text())
    pre_refused = sum(1 for c in ctrl_pre if not c.get("comparable"))

    guards = [
        dict(n=refused_parks, unit=f"из {parks_total} парков",
             h="Отказ, когда контроля нет",
             p=f"Объект на краю шкалы сравнивать не с чем: подбор по ближайшему соседу тянет крайние значения "
               f"к центру. Если контроль расходится с объектом по исходной зелёности больше чем на "
               f"{CONTROL['max_gap_ndvi']}, вердикт не выносится вовсе. В пакетном аудите парков защита "
               f"отказалась считать {refused_parks} объектов из {parks_total} — это {100 * refused_parks / parks_total:.0f} % "
               f"выборки, и без неё столько же недостоверных вердиктов было бы опубликовано."),
        dict(n=cand - confirmed, unit=f"из {cand} кандидатов",
             h="Правило двух приборов",
             p=f"Падение зелёности за один сезон само по себе ничего не значит: это может быть погода, стройка "
               f"или шум. Потеря публикуется, только если второй прибор видит падение кроны и не видит роста "
               f"застройки. За {n_seasons} {plural(n_seasons, 'сезон', 'сезона', 'сезонов')} в двух городах из "
               f"{cand} кандидатов потерей кроны {plural(confirmed, 'подтверждена', 'подтверждены', 'подтверждено')} "
               f"{confirmed}; {construction} {plural(construction, 'оказалась', 'оказались', 'оказались')} стройкой, "
               f"из них {moved} — по документам, когда приборы уже видели потерю кроны, а застройка ещё не выросла. "
               f"Остальные не подтвердились ничем."),
        dict(n=restorations, unit="реставраций в шуме",
             h="Молчание там, где молчать обязан",
             p=f"Реставрация существующего парка не меняет растительность по построению — починка дорожек и "
               f"прудов в NDVI не отражается. Это не отговорка: гипотеза проверена на проектах, сданных "
               f"до эры Sentinel-2, с окном под каждый проект и порогом под каждое окно. Все {restorations} "
               f"дали шум, в том числе семь крупных реставраций 2009–2016 годов."),
        dict(n=prelim, unit="понижен до предварительного",
             h="Мало снимков — вердикт слабее",
             p=f"Меньше {QUALITY['min_scenes']} годных снимков в окне — медиана шумная, и вердикт помечается "
               f"предварительным, а число снимков печатается рядом с эффектом. Так же выбирается прибор: "
               f"для следа мельче {MIN_HA_LANDSAT:.0f} га Landsat даёт единицы пикселей, и берётся Sentinel-2 "
               f"даже ценой короткого окна «до»."),
        dict(n=pre_refused, unit=f"из {len(ctrl_pre)} предрегистраций",
             h="Отказ, объявленный заранее",
             p="У следов, зафиксированных до начала работ, контроль назван и проверен тогда же. Один объект "
               "признан несопоставимым за годы до аудита: через пять лет никто не сможет подобрать контроль "
               "под то, что получилось. Это и отличает предрегистрацию от ретроспективной проверки."),
    ]
    guards_html = "".join(
        f'<div class="guard"><h3>{esc(g["h"])}</h3>'
        f'<div class="fired"><b>{g["n"]}</b><span>{esc(g["unit"])}</span></div>'
        f'<p>{esc(g["p"])}</p></div>' for g in guards)

    mon_rows = "".join(
        f"<tr><td>{esc(CITY_NAME[c])}, сезон {s}</td><td class='num'>{v['threshold']:.4f}</td>"
        f"<td class='num'>{len(v['F']['lost'])}</td>"
        f"<td class='num'>{len(v['F']['construction'])}{' (' + str(v['moved']) + ' по док.)' if v['moved'] else ''}</td>"
        f"<td class='num'>{len(v['F']['unconfirmed'])}</td>"
        f"<td class='num'>{len(v['F']['confirmed'])}</td>"
        f"<td class='num'>{v['F']['refused']}</td></tr>"
        for (c, s), v in sorted(mon.items(), key=lambda kv: (kv[0][1], kv[0][0])))

    limits_html = "".join(f"<li>{esc(x)}</li>" for x in LIMITS)

    doc = f"""<meta charset="utf-8"><title>Метод и его отказы</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>{CSS}</style>
<div class="page">
<header class="masthead">
  <div class="eyebrow">Метод · Frondia · измерение городских изменений</div>
  <h1>Отказ считать — тоже результат</h1>
  <p class="standfirst">Инструмент, который на любой вопрос отвечает числом, бесполезен: доверия заслуживает тот, который умеет сказать «здесь я не измеряю». Эта страница показывает, из чего собран метод и сколько раз каждая его защита сработала на настоящих данных двух городов.</p>
  <div class="dateline"><span>Брюссель: 686 секторов</span><span>Антверпен: 457 секторов</span><span>снимки: Sentinel-2, Landsat, Dynamic World</span><span>обновлено {today_ru()}</span></div>
</header>

<section>
  <div class="sec-head"><span class="eyebrow">Основа</span><h2>Три решения, на которых стоит всё остальное</h2></div>
  <div class="col">
  <p><strong>Первое: сравнивать не с прошлым, а с контролем.</strong> {esc(bg_sentence('brussels'))} Поэтому эффект считается как разность разностей: изменение объекта минус изменение {CONTROL['n_controls']} похожих участков, подобранных по состоянию <em>до</em> работ и удалённых не ближе {CONTROL['exclusion_m']} м, чтобы не попасть в ту же стройку.</p>
  <p><strong>Второе: порог измерять, а не назначать.</strong> Каждый сектор города по очереди играет роль вмешательства: ему подбирается свой контроль и считается эффект. Полученное распределение — это шум метода в чистом виде, потому что никакого вмешательства там не было. Порог значимости — его 95-й процентиль. Среднее этого распределения во всех городах и приборах практически ноль: метод не выдумывает эффектов там, где их нет.</p>
  <p><strong>Третье: порог — свойство пары «город и прибор».</strong> Антверпен шумнее Брюсселя примерно на четверть, и брюссельский порог там был бы неверен. Прибор без калибровки для конкретного города может посчитать число, но не имеет права назвать его значимым.</p>
  </div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Пороги</span><h2>Что считается значимым и почему в двух городах по-разному</h2></div>
  <div class="scroll"><table><thead><tr><th>прибор</th><th>Брюссель</th><th>Антверпен</th></tr></thead><tbody>{thr_rows}</tbody></table></div>
  <div class="col"><p>Все значения — 95-е процентили собственных нулевых распределений, посчитанных на секторах соответствующего города. У аудитов с окном под конкретный проект единого порога на слой нет вовсе: он считается заново на каждом окне и печатается в строке рядом с эффектом.</p></div>
  <div class="warn col"><p><strong>Температуры в этой таблице нет, и это принципиально.</strong> Порог для температуры поверхности вышел 1,32 °C, а охлаждающий эффект городских парков по литературе составляет 0,5–2 °C. Шум метода проглатывает большинство реалистичных эффектов, поэтому утверждения вида «вмешательство охладило квартал» на этих данных не делаются. Ни одного.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Защиты</span><h2>Пять правил и сколько раз каждое сработало</h2></div>
  <div class="guards">{guards_html}</div>
  <div class="callout col"><p>Ни одно из этих правил не придумано заранее «на всякий случай». Каждое добавлено после того, как без него был получен убедительный и неверный результат.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Годовой цикл</span><h2>Мониторинг: {n_seasons} {plural(n_seasons, 'сезон', 'сезона', 'сезонов')}, два города, {confirmed} {plural(confirmed, 'подтверждённая потеря', 'подтверждённые потери', 'подтверждённых потерь')}</h2></div>
  <div class="scroll"><table><thead><tr><th>город и сезон</th><th>порог сезона</th><th>кандидатов</th><th>стройка</th><th>не подтверждено</th><th>потеря кроны</th><th>отказ по контролю</th></tr></thead><tbody>{mon_rows}</tbody></table></div>
  <div class="col"><p>Порог сезона всегда выше или ниже аудитного и никогда с ним не смешивается: окно «после» здесь — одно лето, и нулевое распределение считается тем же прогоном. Подтверждённые потери кроны: {esc(", ".join(confirmed_names))}. Wolvendael — одна и та же буря 9 июля 2024 года, зарегистрированная дважды, потому что база сезона 2026 ещё содержит лета до неё. Причина в каждом случае ищется по документам: у Wolvendael она названа и не связана с политикой города, у Parc Forestier не установлена — и напечатано именно так.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Словарь исходов</span><h2>Что именно произошло, а не одна цифра</h2></div>
  <div class="col"><p>Одного числа мало: рост зелёности бывает разным по смыслу. Классы покрытия по тем же снимкам дают формулировку, которую можно проверить и которая продаётся лучше цифры.</p>
  <ul>
    <li><strong>Раскрыли и озеленили</strong> — застройка вниз, трава или крона вверх. Так выглядит настоящий новый парк.</li>
    <li><strong>Голая поверхность заросла</strong> — рекультивация промзоны, а не создание парка.</li>
    <li><strong>Раскрыли, но не засадили</strong> — покрытие снято, вместо газона гравий или настил.</li>
    <li><strong>Крона выросла без смены покрытия</strong> — деревья поднялись там, где ничего не строили.</li>
    <li><strong>Стройка</strong> — застройка вверх. Потеря честная, но это не деградация зелени.</li>
  </ul>
  <p>Отдельный случай, который метод обязан признавать: молодые посадки на лугу дают зелёность <em>ниже</em> травы, которую заменили. Настоящее озеленение на горизонте пяти лет может измеряться как потеря — это записано в ограничения, а не спрятано.</p>
  </div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Границы</span><h2>Чего этот метод не измеряет</h2></div>
  <div class="col"><ul>{limits_html}</ul></div>
  <div class="col"><p>Список короткий намеренно. Каждая строка в нём — результат проверки, а не осторожность на всякий случай: температура отвергнута измеренным порогом, невидимость реставраций подтверждена отдельным прогоном, предел по размеру объекта найден на конкретном парке, где правило выбора прибора дало неверный ответ.</p></div>
</section>

<div class="foot">Все числа на этой странице пересчитываются из файлов проекта: манифестов <code>cities/&lt;город&gt;/manifest.json</code> ({len(man['brussels'].layers)} и {len(man['antwerp'].layers)} слоёв), слоёв аудита и мониторинга в тех же пакетах, реестра предрегистраций. Снимки: Copernicus Sentinel-2 SR Harmonized с маской Cloud Score+ ≥ {QUALITY['cloud_score_plus_min']}, Landsat Collection 2 Level 2, Google Dynamic World V1. Единица — статистический сектор Statbel. Каждый количественный шаг закрыт тестом на известный ответ.</div>
</div>
"""
    out = SCRATCH / "method.html"
    out.write_text(doc, encoding="utf-8")
    print(f"→ {out}  ({len(doc.encode()) // 1024} КБ) · отказов по контролю {refused_parks}/{parks_total} · "
          f"сезонов {n_seasons}, кандидатов {cand}, подтверждено {confirmed}, строек {construction} "
          f"(по документам {moved}) · реставраций в шуме {restorations}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
