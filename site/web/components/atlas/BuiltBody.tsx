'use client'
import { NullHistogram } from '@/components/NullHistogram'
import { fixed, int, signed } from '@/lib/format'
import { sectorName, sectorPlace } from '@/lib/names'
import type { AtlasCity } from '@/lib/atlas/types'
import type { Sector } from '@/lib/types'
import { useT } from '@/lib/t-client'
import { tie } from '@/lib/typography'

// sealed ground: the built-up class against the same matched places. There is no raw view, since the
// run kept each sector's effect and not its own before and after, so the toggle gives way to a line saying so
// (Atlas.jsx 716–747)
type BuiltSector = Sector & { bv?: string | null; be?: number | null }

export function BuiltBody({ city, top, onPick }: { city: AtlasCity; top: Sector[]; onPick: (s: Sector) => void }) {
  const { t, loc } = useT('atlas')
  const { t: tc } = useT('common')
  const b = city.built
  if (!b) return null
  const thr = fixed(b.threshold, 3, loc)
  return (
    <>
      <p className="small">{t('built.lede')}</p>
      <div className="counts">
        <div><span className="num-l tone-down">{int(b.counts.up, loc)}</span><span className="label">{t('built.counts.up')}</span></div>
        <div><span className="num-l tone-up">{int(b.counts.down, loc)}</span><span className="label">{t('built.counts.down')}</span></div>
      </div>
      <NullHistogram hist={b.hist} thr={b.threshold} mode="effect" height={170} compact invert loc={loc}
                     label={t('built.histAria', { n: String(b.counts.up + b.counts.down + b.counts.noise), thr })} />
      <ul className="legend">
        <li><i className="sw sw-down" />{t('built.legend.up')}</li>
        <li><i className="sw sw-up" />{t('built.legend.down')}</li>
        <li><i className="sw sw-noise" />{t('built.legend.noise')}</li>
        <li><i className="sw sw-refused" />{t('change.legend.refused', { n: String(b.counts.refused) })}</li>
      </ul>
      <p className="small">{t('built.threshold', { thr, n: int(city.units.comparable, loc), city: tc(`cities.${city.city}`) })} {t('built.limit')}</p>
      <p className="small panel-source">{t('built.rawOff')}</p>
      <p className="label panel-sub">{t('built.top')}</p>
      <ol className="toplist">
        {(top as BuiltSector[]).map((s) => (
          <li key={s.id}>
            <button type="button" onClick={() => onPick(s)}>
              <i className={`dot dot-${s.bv === 'up' ? 'down' : 'up'}`} /><span>{tie(sectorName(s, loc), loc)}<small>{tie(sectorPlace(s, loc), loc)}</small></span><span className="mono">{signed(s.be, 3, loc)}</span>
            </button>
          </li>
        ))}
      </ol>
    </>
  )
}
