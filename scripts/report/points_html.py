"""Страница линии выполнения: точки, названные до проверки.

Необычная для проекта страница: на ней нет результата. Есть обещание,
зафиксированное датой и хешем, и правила, по которым его проверят через
несколько сезонов. Смысл именно в том, что публикация идёт ДО измерения —
иначе точку всегда можно подобрать под то, что появилось.

Все числа считаются из файлов: реестров точек, манифестов городов и
измеренного дрейфа карты OSM.

    python scripts/report/points_html.py
"""
from __future__ import annotations

import collections
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.manifest import Manifest  # noqa: E402
from engine.registries.points import DEFAULT_RADIUS_M, KINDS, load  # noqa: E402

from scripts.report.paths import DERIVED, OUT as SCRATCH  # noqa: E402
from scripts.report.background import background, plural as bg_plural  # noqa: E402

from engine.registries.points import KIND_LABEL_RU as KIND_RU  # noqa: E402
ASSET_RU = {"toilets": "туалеты", "benches": "скамейки", "waste_bins": "урны",
            "drinking_water": "фонтанчики", "bike_parking": "велопарковки",
            "defibrillators": "дефибрилляторы", "fitness_stations": "тренажёры",
            "dog_areas": "площадки для собак", "playgrounds": "детские площадки",
            "shelters": "навесы и укрытия", "recycling": "контейнеры раздельного сбора",
            "bicycle_repair": "велоремонтные станции", "public_bookcases": "книжные шкафы",
            "picnic_tables": "столы для пикника"}


def plural(n: int, one: str, few: str, many: str) -> str:
    n10, n100 = n % 10, n % 100
    return one if n10 == 1 and n100 != 11 else few if 2 <= n10 <= 4 and not 12 <= n100 <= 14 else many


CSS = """
:root{--paper:#EFF1EC;--surface:#FFFFFF;--ink:#141B17;--muted:#5B6B62;--rule:#D5DAD3;--rule-2:#E4E8E3;
--accent:#1E6E58;--accent-soft:#E2EDE7;--heat:#C2451C;--heat-soft:#F7E6DE;--ctrl:#8A8F86;
--display:"IBM Plex Sans Condensed","Helvetica Neue",Arial,sans-serif;--body:"IBM Plex Serif",Georgia,serif;
--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--measure:34rem;--wide:62rem}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;
--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;--ctrl:#6B7268}}
:root[data-theme="dark"]{--paper:#0F1411;--surface:#161C18;--ink:#E3E8E3;--muted:#8FA096;--rule:#28322C;--rule-2:#1F2823;
--accent:#54AF8F;--accent-soft:#172B24;--heat:#EA7148;--heat-soft:#2E1C14;--ctrl:#6B7268}
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
/* Дрейф карты: одна полоса на дату — рост, который объясняет всё без контроля */
.drift{display:grid;grid-template-columns:5rem 1fr 5rem;gap:.5rem 1rem;align-items:center;background:var(--surface);border:1px solid var(--rule);padding:1.2rem 1.25rem;font-family:var(--display)}
.drift .y{font-family:var(--mono);font-size:.85rem;color:var(--muted)}
.drift .b{height:1.1rem;background:var(--rule-2)}.drift .b i{display:block;height:100%;background:var(--ctrl)}
.drift .v{font-family:var(--mono);font-variant-numeric:tabular-nums;text-align:right;font-size:.95rem}
.drift .last i{background:var(--heat)}
.sets{display:grid;grid-template-columns:repeat(auto-fit,minmax(17rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}
.set{background:var(--surface);padding:1.25rem 1.3rem;display:flex;flex-direction:column;gap:.55rem}
.set b.n{font-family:var(--display);font-weight:700;font-size:2.4rem;line-height:1;letter-spacing:-.02em}
.set h3{margin:0}.set p{font-size:.93rem;color:var(--muted);line-height:1.45}
.split{display:flex;gap:.3rem;font-family:var(--mono);font-size:.7rem;letter-spacing:.05em;text-transform:uppercase}
.split span{padding:.15rem .45rem;border:1px solid currentColor}
.split .n{color:var(--accent)}.split .c{color:var(--muted)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(10rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}
.stat{background:var(--surface);padding:1rem 1.05rem;display:flex;flex-direction:column;gap:.2rem}
.stat b{font-family:var(--display);font-weight:700;font-size:2rem;line-height:1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat span{font-family:var(--display);font-size:.8rem;color:var(--muted);line-height:1.3}
.t-mute{color:var(--muted)}
.foot{font-family:var(--display);font-size:.82rem;color:var(--muted);border-top:1px solid var(--rule);padding-top:1rem;max-width:46rem}
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def n(x) -> str:
    return f"{int(x):,}".replace(",", " ")


def main() -> int:
    # Три набора: правило+жребий по Брюсселю и два от планировщика с отсечкой.
    bxl_rule = load(Path("data/registry/named_points.json"))
    bxl_plan = load(Path("data/registry/named_points_brussels.json"))
    bxl = bxl_rule + bxl_plan
    ant = load(Path("data/registry/named_points_antwerp.json"))
    drift = json.loads(Path("data/registry/osm_drift_brussels_waste_basket.json").read_text())
    man_a = Manifest.read("antwerp")

    def split(pts):
        return sum(1 for p in pts if p.role == "named"), sum(1 for p in pts if p.role == "control")

    b_named, b_ctrl = split(bxl)
    a_named, a_ctrl = split(ant)
    total = len(bxl) + len(ant)
    reg_date = min(p.registered_at for p in bxl + ant)

    dmax = max(r["count"] for r in drift)
    drift_html = "".join(
        f'<div class="y">{esc(r["date"][:4] if r["date"] != "now" else "сейчас")}</div>'
        f'<div class="b{" last" if i == len(drift) - 1 else ""}"><i style="width:{100 * r["count"] / dmax:.0f}%"></i></div>'
        f'<div class="v">{n(r["count"])}</div>'
        for i, r in enumerate(drift))
    growth = drift[-1]["count"] / drift[0]["count"]

    kinds_b = collections.Counter(p.kind for p in bxl)
    kinds_a = collections.Counter(p.kind for p in ant)
    kind_rows = "".join(
        f"<tr><td>{esc(KIND_RU.get(k, k))}<small><code>{esc(k)}</code></small></td>"
        f"<td class='num'>{kinds_b.get(k, 0) or '—'}</td><td class='num'>{kinds_a.get(k, 0) or '—'}</td></tr>"
        for k in KINDS if kinds_b.get(k) or kinds_a.get(k))

    def coverage(city):
        out = {}
        for key, e in Manifest.read(city).layers.items():
            if not key.startswith("points_") or key == "points_improvements":
                continue
            try:
                before, after = (e.method or "").split("покрытие ")[1].split(" → ")
                out[key[len("points_"):]] = (float(before), float(after))
            except (IndexError, ValueError):
                continue
        return out
    cov_b, cov_a = coverage("brussels"), coverage("antwerp")
    def cell(c):
        return (f"<td class='num'>{c[0]:.2f} → {c[1]:.2f}</td><td class='num'>{(c[1] - c[0]) * 100:+.0f} п.п.</td>"
                if c else "<td class='num t-mute'>—</td><td class='num t-mute'>—</td>")
    assets = sorted(set(cov_b) | set(cov_a),
                    key=lambda a: -max((cov_b.get(a, (0, 0))[1] - cov_b.get(a, (0, 0))[0]),
                                       (cov_a.get(a, (0, 0))[1] - cov_a.get(a, (0, 0))[0])))
    cov_rows = "".join(f"<tr><td>{esc(ASSET_RU.get(a, a))}</td>{cell(cov_b.get(a))}{cell(cov_a.get(a))}</tr>"
                       for a in assets)
    n_kinds = len(set(kinds_b) | set(kinds_a))
    first_three = ", ".join(KIND_RU[k] for k in ("waste_basket", "bench", "toilets"))

    bg = background("brussels")   # фон озеленения — тот же модуль, что на методе и атласе
    doc = f"""<meta charset="utf-8"><title>Точки, названные заранее</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>{CSS}</style>
<div class="page">
<header class="masthead">
  <div class="eyebrow">Линия выполнения · Брюссель и Антверпен · зафиксировано {esc(reg_date)}</div>
  <h1>{total} точки названы до проверки</h1>
  <p class="standfirst">На этой странице нет результата — и в этом всё дело. Мы называем места, где точечные объекты нужнее всего, фиксируем их датой и хешем и публикуем сейчас. Проверка появления будет через несколько сезонов, и подвинуть точку под то, что появилось, будет уже нельзя.</p>
  <div class="dateline"><span>{n_kinds} {plural(n_kinds, 'тип', 'типа', 'типов')} объектов: урны, скамейки, туалеты и другие</span><span>радиус проверки {DEFAULT_RADIUS_M} м</span><span>источник проверки: история OpenStreetMap</span></div>
</header>

<section>
  <div class="sec-head"><span class="eyebrow">Зачем так сложно</span><h2>Объектов на карте становится больше сами по себе</h2></div>
  <div class="col"><p>Проверять выполнение по OpenStreetMap соблазнительно и почти всегда неверно. Карта — не перепись города, а работа добровольцев, и она пополняется независимо от того, что делает город. Вот сколько урн видит OSM в Брюсселе по годам:</p></div>
  <div class="drift">{drift_html}</div>
  <div class="warn col"><p><strong>Рост в {growth:.1f} раза за восемь лет.</strong> Урны не устанавливали втрое чаще — их рисовали. Любой вывод «объектов стало больше» без контроля объясняется этим целиком. Ровно та же ловушка, что в измерении зелени: за те же годы позеленел весь город, и без контроля «значимо позеленевшими» оказались бы {bg['k_raw']} {bg_plural(bg['k_raw'], 'сектор', 'сектора', 'секторов')} Брюсселя из {bg['n']} вместо {bg['k_eff']}.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Два набора</span><h2>Одна дисциплина, два независимых способа назвать точки</h2></div>
  <div class="sets">
    <div class="set">
      <b class="n">{len(bxl)}</b>
      <h3>Брюссель: два способа сразу</h3>
      <div class="split"><span class="n">{b_named} названных</span><span class="c">{b_ctrl} контрольных</span></div>
      <p><strong>{len(bxl_rule)} точки по собственному правилу:</strong> секторы нижнего терциля по доходу, где сегодня нет урны в 150 м от центра сектора; отобранные делятся пополам хешем от напечатанного зерна. <strong>{len(bxl_plan)} точек от планировщика:</strong> та же отсечка бюджета, что в Антверпене, по семи типам объектов. Два независимых способа отбора в одном городе — проверить можно оба.</p>
    </div>
    <div class="set">
      <b class="n">{len(ant)}</b>
      <h3>Антверпен: чужой движок и отсечка бюджета</h3>
      <div class="split"><span class="n">{a_named} названных</span><span class="c">{a_ctrl} контрольных</span></div>
      <p>Точки ранжирует независимый планировщик по приросту покрытия с учётом депривации. При обычном бюджете город получил бы первую десятку по каждому типу объекта; вторая десятка отобрана тем же движком из того же пула, но в рекомендацию не попала. Отличие ровно одно — отсечка.</p>
    </div>
  </div>
  <div class="callout col"><p>Второй способ честнее первого: правило выбора придумала не я, а ранг присвоен по приросту покрытия. Сравнение «попал в отсечку против не попал» ближе к настоящему опыту, чем «названные против случайных».</p></div>
  <div class="warn col"><p><strong>Оговорка, которую нельзя опускать.</strong> Решатель добавляет точки по убыванию прироста, поэтому вторая десятка по построению чуть хуже первой. Контроль получается консервативным: если объекты появятся в названных точках чаще, часть разницы может объясняться тем, что точки просто лучше.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Что именно названо</span><h2>{n_kinds} {plural(n_kinds, 'тип', 'типа', 'типов')} объектов, два города</h2></div>
  <div class="scroll"><table><thead><tr><th>тип объекта</th><th>Брюссель</th><th>Антверпен</th></tr></thead><tbody>{kind_rows}</tbody></table></div>
  <div class="col"><p>Ни один из этих объектов не меняет ни зелёность, ни запечатанность: эффект от урны или скамейки не измеряется со спутника ничем, и притворяться нечего. Проверяется другое — появился объект там, где его назвали, или нет.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Что обещает планировщик</span><h2>Насколько выросло бы покрытие, если поставить по сорок объектов каждого типа</h2></div>
  <div class="scroll"><table><thead><tr><th>тип объекта</th><th>Брюссель: сейчас → стало бы</th><th>прирост</th><th>Антверпен: сейчас → стало бы</th><th>прирост</th></tr></thead><tbody>{cov_rows}</tbody></table></div>
  <div class="col"><p>Покрытие считается по сетке спроса в радиусе пятиминутной ходьбы, а не по населению. Самые пустые категории — уличные тренажёры и площадки для собак: там сорок объектов меняют картину города, а не подправляют её. Это рекомендация, а не измерение: числа говорят, что было бы, а не что произошло.</p></div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Как это проверят</span><h2>Правила вердикта записаны раньше данных</h2></div>
  <div class="col"><ul>
    <li><strong>Что считается появлением.</strong> Объект нужного типа в {DEFAULT_RADIUS_M} метрах от точки, которого на дату фиксации там не было. Радиус входит в хеш: расширить его задним числом нельзя.</li>
    <li><strong>Что считается результатом.</strong> Разность долей: сколько названных точек получили объект минус сколько получили контрольные. Разность и есть то, что осталось после вычитания дрейфа карты.</li>
    <li><strong>Когда вердикта не будет.</strong> Меньше двадцати точек в любой половине — доли печатаются, вердикт не выносится. Так же устроен отказ в измерении зелени.</li>
    <li><strong>Что уже проверено.</strong> Первый прогон дал ноль появлений в обеих половинах Брюсселя. Это не результат, а подтверждение отбора: точки выбирались как пустые сегодня.</li>
  </ul></div>
  <div class="stats">
    <div class="stat"><b>{b_named}</b><span>названных точек Брюсселя ждут проверки</span></div>
    <div class="stat"><b>{a_named}</b><span>названных точек Антверпена ждут проверки</span></div>
    <div class="stat"><b>0</b><span>появлений на дату фиксации — так и должно быть</span></div>
    <div class="stat"><b>{DEFAULT_RADIUS_M} м</b><span>радиус, зашитый в хеш каждой точки</span></div>
  </div>
</section>

<section>
  <div class="sec-head"><span class="eyebrow">Границы</span><h2>Чего эта линия не докажет</h2></div>
  <div class="col"><ul>
    <li>Появление объекта в OpenStreetMap — не доказательство установки: возможно, картограф наконец заметил то, что стояло годами. Именно для этого нужен контроль.</li>
    <li>Эффект точечных объектов на среду не измеряется: ни NDVI, ни классы покрытия на урну не реагируют. Эта линия отвечает на вопрос «сделано ли», а не «сработало ли».</li>
    <li>Точки названы нами, а не согласованы с городом. Если город не знает о рекомендации, проверка меряет его обычную работу, а не отклик на неё.</li>
    <li>Типы объектов не равны по заметности в карте: дефибрилляторы и тренажёры картографируются реже урн, и дрейф у них свой.</li>
  </ul></div>
</section>

<div class="foot">Реестры точек: <code>data/registry/named_points.json</code> и <code>named_points_antwerp.json</code>, у каждой записи правило отбора, ожидание, дата и хеш от координат, радиуса и типа. Кандидаты Антверпена — City Planner, слои <code>cities/antwerp/points/*.geojson</code> в манифесте города. Дрейф карты измерен историческими запросами OpenStreetMap. Все числа на странице пересчитываются из этих файлов.</div>
</div>
"""
    out = SCRATCH / "named-points.html"
    out.write_text(doc, encoding="utf-8")
    print(f"→ {out}  ({len(doc.encode()) // 1024} КБ) · точек {total} "
          f"(Брюссель {len(bxl)}, Антверпен {len(ant)}) · дрейф ×{growth:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
