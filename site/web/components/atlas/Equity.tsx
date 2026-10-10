'use client'
import { int, pct } from '@/lib/format'
import { barStyle } from '@/lib/atlas/geometry'
import type { AtlasCity, EquityRow } from '@/lib/atlas/types'
import { equityCut, equityFormat, equityReading, pts } from '@/lib/atlas/words'
import { useT } from '@/lib/t-client'
import { spokenPoints, plain } from '@/lib/typography'
import { count } from '@/lib/icu'
import type { NeedOpt } from './NeedPanel'

/* ── who is short (phase 2): the lens by income third, and who lives in the worst-off group ──
   Rows as in Deel's side panel (label and value on one line, a thin bar on a hairline track); the age
   rows are set against all residents in points, as Steep's breakdown sets segments against the total.
   Bars are ink, not the lack ramp: the ramp means a class on the map. Heat is a difference from the
   city's median sector, so its bars leave the centre line to either side. (Atlas.jsx 334–373) */
export function Equity({ city, lens, opt }: { city: AtlasCity; lens: string; opt: NeedOpt }) {
  const { t, loc } = useT('atlas')
  const { t: tc } = useT('common')
  const o = lens === 'services' ? opt.scenario : lens === 'shops' ? opt.shop : '_'
  const block = city.equity?.[lens] as Record<string, EquityRow> | undefined
  const e = block?.[o]
  if (!e) return null
  const f = (v: number) => equityFormat(t, lens, v, loc)
  const cut = equityCut(t, lens, e, loc)
  const euro = (v: number) => t('equity.money', { v: int(v, loc) })
  return (
    <section className="equity" aria-label={plain(t('equity.title'))}>
      <p className="label">{t('equity.title')}</p>
      {/* a signed value keeps its plus sign on the line before it ("richest: +1.6 °C" broke at 360 px; the old atlas did too) */}
      <p className="small equity-read">{equityReading(t, lens, o, e, loc).replace(/ (?=\+\d)/g, '\u00A0')}</p>
      <p className="small equity-head">{t(`equity.byIncome.${lens}`, { o })}</p>
      <ul className={`bars${lens === 'heat' ? ' bars--diverging' : ''}`}>
        {e.thirds.map((v, i) => (
          <li key={i}>
            <span>{t(`equity.thirds.${i}`)}</span><span className="v">{f(v)}</span>
            <span className="track" aria-hidden="true"><i style={barStyle(lens, v, e.thirds)} /></span>
          </li>
        ))}
      </ul>
      <p className="small equity-head">{t('equity.livesIn', { group: t(`equity.group.${lens}`), cut: cut ?? 'none' })}</p>
      <ul className="bars">
        <li className="ref">
          <span>{t('equity.all')}</span><span className="v">{pct(e.all, 0, loc)}</span>
          <span className="track" aria-hidden="true"><i style={{ left: 0, width: `${100 * e.all}%` }} /></span>
        </li>
        {(['kid', 'old'] as const).map((k) => (
          <li key={k} className="vs-row">
            <span>{t(`equity.${k}`)}</span>
            <span className="vs">{spokenPoints(pts(t, e[k], e.all, loc), loc, (n) => tc('pointsSpoken', { n: count(n) }))}<span className="sr-only"> {t('equity.vs')}</span></span>
            <span className="v">{pct(e[k], 0, loc)}</span>
            <span className="track" aria-hidden="true"><i style={{ left: 0, width: `${100 * e[k]}%` }} /></span>
          </li>
        ))}
      </ul>
      <p className="small panel-source">{t('equity.source', { lo: euro(city.equity.income_cuts[0]), hi: euro(city.equity.income_cuts[1]) })}</p>
    </section>
  )
}
