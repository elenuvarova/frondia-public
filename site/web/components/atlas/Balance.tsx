'use client'
import type { AtlasCity } from '@/lib/atlas/types'
import { haValue } from '@/lib/atlas/words'
import { useT } from '@/lib/t-client'

// the balance after the 2024 base: lost and gained beyond noise, and the net, in hectares — the three bars of
// France's Mon Diagnostic Artificialisation (Figma 125:2, row 49) set as rows on a hairline track (Deel), one
// scale for all three. Left is less, right is more; the colour says what the change means: more built-up is loss
// (Atlas.jsx 551–578)
const ROWS = ['green', 'trees', 'built'] as const

export function Balance({ city }: { city: AtlasCity }) {
  const { t, loc } = useT('atlas')
  const { t: tc } = useT('common')
  const b = city.balance
  if (!b) return null
  const s = b.latest, d = b.seasons[s]!
  const top = Math.max(1, ...ROWS.flatMap((k) => [Math.abs(d[k].lost_ha), d[k].gained_ha]))
  const w = (v: number) => `${(50 * Math.abs(v)) / top}%`
  const ha = (v: number) => haValue(t, v, loc)
  return (
    <div className="balance">
      <p className="label panel-sub">{t('balance.title', { base: String(b.base) })}</p>
      <p className="small">{t('balance.lede', { base: String(b.base), s })}</p>
      <ul className="bars bars--diverging bars--balance">
        {ROWS.map((k) => (
          <li key={k}>
            <span>{t(`balance.rows.${k}`)}<small>{t('balance.split', { lost: haValue(t, d[k].lost_ha, loc, false), gained: haValue(t, d[k].gained_ha, loc, false) })}</small></span>
            <span className="v">{t('balance.net', { v: ha(d[k].net_ha) })}</span>
            <span className="track" aria-hidden="true">
              <i className={k === 'built' ? 'is-gain' : 'is-loss'} style={{ left: `calc(50% - ${w(d[k].lost_ha)})`, width: w(d[k].lost_ha) }} />
              <i className={k === 'built' ? 'is-loss' : 'is-gain'} style={{ left: '50%', width: w(d[k].gained_ha) }} />
            </span>
          </li>
        ))}
      </ul>
      <p className="small">{t('balance.raw', { city: tc(`cities.${city.city}`), s, g: ha(d.green.raw_net_ha), b: ha(d.built.raw_net_ha) })}</p>
      {[String(b.base), s].filter((y) => b.preliminary[y]).map((y) => <p key={y} className="small">{t('balance.preliminary', { y })}</p>)}
      <p className="small panel-source">{t('balance.limit')}</p>
    </div>
  )
}
