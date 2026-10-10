'use client'
import { localePath } from '@/i18n/locales'
import { int, longDate, pct } from '@/lib/format'
import { greenStep } from '@/lib/atlas/geometry'
import type { AtlasCity, AtlasRegistered } from '@/lib/atlas/types'
import { registeredNone, unstableLine } from '@/lib/atlas/words'
import { placeName } from '@/lib/names'
import { useT } from '@/lib/t-client'
import { Balance } from './Balance'
import { spokenPoints, tie } from '@/lib/typography'
import { count } from '@/lib/icu'

/* ── communes (phase 2): Article 8(1) by commune, and what was registered before the works ────
   The list follows Grain's scale: the threshold labelled once above the rows, a dashed line through
   them (elements board, 44). A registered footprint is an outline with no fill, as Zillow draws a
   boundary someone set. The fill is the green share itself, in ColorBrewer Greens (brand.css), and a
   bar in the list takes its commune's class, so list and map read the same. (Atlas.jsx 580–640) */
export const GREENS = ['var(--green-1)', 'var(--green-2)', 'var(--green-3)', 'var(--green-4)', 'var(--green-5)']

export function CommuneBody({ city, onPickRegistered }: { city: AtlasCity; onPickRegistered: (r: AtlasRegistered) => void }) {
  const { t, raw, loc } = useT('atlas')
  // rc('sep.dot') where a bare " · " sat between two values: t would tie its first space, which the English never had
  const { t: tc, raw: rc } = useT('common')
  const name = tc(`cities.${city.city}`)
  const co = city.communes
  const tested = co.list.filter((c) => c.green != null).sort((a, b) => (b.green as number) - (a.green as number))
  const lo = co.leave_out
  const reg = city.registered || []
  const untested = co.tested < co.list.length
  const legend = raw<string[]>('communes.legend')
  return (
    <>
      <p className="small">{t('communes.lede')}</p>
      <div className="counts">
        <div><span className="num-l">{int(co.exempt, loc)}</span><span className="label">{t('communes.exempt')}</span></div>
        <div><span className="num-l">{int(co.tested - co.exempt, loc)}</span><span className="label">{t('communes.counted')}</span></div>
      </div>
      {co.region && <p className="small">{t('communes.region', { n: String(co.tested), g: pct(co.region.green, 1, loc) })}</p>}
      {lo && <p className="small">{t('communes.leaveOut', { n: String(co.exempt), area: pct(lo.area, 0, loc), res: pct(lo.residents, 0, loc), woody: pct(lo.woody, 0, loc), rest: String(lo.rest), restGreen: pct(lo.rest_green, 0, loc) })}</p>}
      <div className="threshold-list">
        <p className="small equity-head">{t('communes.listTitle')}</p>
        <div className="tl-scale" aria-hidden="true">
          <span>{t('communes.scale.lo')}</span><span className="tl-mark">{t('communes.scale.mark')}</span><span>{t('communes.scale.hi')}</span>
        </div>
        <ul className="bars tl-rows">
          {tested.map((c) => (
            <li key={c.code} className={c.exempt ? 'is-exempt' : ''}>
              <span><a href={`${localePath(loc, '/commune')}?code=${c.code}`}>{tie(placeName(c, loc), loc)}</a>{c.exempt && <small>{t('communes.exempt')}</small>}{c.canopy != null && c.canopy < 0.1 && <small>{t('communes.canopyToo', { c: pct(c.canopy, 0, loc) })}</small>}</span>
              <span className="v">{pct(c.green, 1, loc)}</span>
              <span className="track" aria-hidden="true"><i style={{ left: 0, width: `${100 * (c.green as number)}%`, background: GREENS[greenStep(c.green)!] }} /></span>
            </li>
          ))}
        </ul>
      </div>
      {tested.filter((c) => c.stable === false).map((c) => (
        <p key={c.code} className="small">{spokenPoints(unstableLine(t, c, placeName(c, loc), loc), loc, (n) => tc('pointsSpoken', { n: count(n) }))}</p>
      ))}
      {untested && <p className="small">{t('communes.untested')}</p>}
      <ul className="legend legend--compact">
        {legend.map((_, i) => <li key={i}><i className="sw" style={{ background: GREENS[i] }} />{t(`communes.legend.${i}`)}</li>)}
        <li><i className="sw sw-exempt" />{t('communes.legendExempt')}</li>
        {untested && <li><i className="sw sw-few" />{t('communes.legendUntested')}</li>}
        {reg.length > 0 && <li><i className="sw sw-registered" />{t('communes.legendRegistered')}</li>}
      </ul>
      <p className="small panel-source">{t('communes.source')}</p>
      {city.balance && <Balance city={city} />}
      <p className="label panel-sub">{t('registered.title')}</p>
      {reg.length ? (
        <>
          <p className="small reg-lede">{t('registered.lede', { n: String(reg.length), date: longDate(`${reg[0]!.registered}T12:00:00`, loc), city: city.city })}</p>
          <ol className="toplist toplist--reg">
            {reg.map((r, i) => (
              <li key={r.id}>
                <button type="button" onClick={() => onPickRegistered(r)}>
                  <i className={`reg-num${r.comparable ? '' : ' is-refused'}`}>{i + 1}</i>
                  <span>{tie(r.name, loc)}<small>{r.comparable ? tie(`${t(`registered.expects.${r.type}`)}${rc<string>('sep.dot')}${t('registered.named')}`, loc) : t('registered.refused')}</small></span>
                </button>
              </li>
            ))}
          </ol>
        </>
      ) : <p className="small reg-lede">{registeredNone(t, city.city, name)}</p>}
    </>
  )
}
