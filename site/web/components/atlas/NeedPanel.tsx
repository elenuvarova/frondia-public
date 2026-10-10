'use client'
import { useMemo } from 'react'
import { sectorName, sectorPlace } from '@/lib/names'
import { LACK, MIN_RESIDENTS, NEED_LENSES, SCENARIOS, SHOP_TYPES, fewResidents, measuredIn, needStep, worst } from '@/lib/lenses'
import type { AtlasCity } from '@/lib/atlas/types'
import { heatLede, needLabel } from '@/lib/atlas/words'
import type { Sector } from '@/lib/types'
import { useT } from '@/lib/t-client'
import { Chips, Choice, PanelKicker } from './bits'
import { Equity } from './Equity'
import { useMoreBelow } from './useMoreBelow'
import { tie, plain } from '@/lib/typography'

export interface NeedOpt { scenario: string; shop: string }

interface NeedPanelProps {
  city: AtlasCity
  lens: string
  setLens: (lens: string) => void
  opt: NeedOpt
  setOpt: (opt: NeedOpt) => void
  onPick: (s: Sector) => void
  otherCity: () => void
}

// What's missing: one need lens over the city, its legend, who is short, and the sectors lacking most
// (Atlas.jsx 375–427)
export function NeedPanel({ city, lens, setLens, opt, setOpt, onPick, otherCity }: NeedPanelProps) {
  const more = useMoreBelow<HTMLElement>()
  const { t, raw, loc } = useT('atlas')
  const { t: tc } = useT('common')
  const name = tc(`cities.${city.city}`)
  const measured = measuredIn(city, lens)
  const list = useMemo(() => (measured ? worst(city, lens, opt) : []), [city, lens, opt, measured])
  // a legend has gaps (3-30-300 names only two of the five steps): the catalogue keeps them as nulls
  const legend = raw<(string | null)[]>(`need.lenses.${lens}.legend`).map((label, i) => (label ? t(`need.lenses.${lens}.legend.${i}`) : null))
  const lede = lens === 'heat' ? heatLede(t, name, city.heat_canopy_r, loc) : t(`need.lenses.${lens}.lede`)
  return (
    <section className="panel" ref={more} aria-label={plain(t('need.aria'))}>
      <PanelKicker>{t('q.need.long')}</PanelKicker>
      <div>
        <h1 className="display-s">{t('need.title', { title: t(`need.lenses.${lens}.title`), city: name })}</h1>
      </div>
      <Chips label={t('need.lens')} value={lens} onChange={setLens} options={NEED_LENSES.map((k) => [k, t(`need.lenses.${k}.chip`)] as const)} />
      {lens === 'services' && measured && (
        <Choice label={t('need.weighted')} value={opt.scenario} onChange={(v) => setOpt({ ...opt, scenario: v })}
                options={SCENARIOS.map((k) => [k, t(`need.scenario.${k}`)] as const)} />
      )}
      {lens === 'shops' && measured && (
        <Choice label={t('need.nearest')} value={opt.shop} onChange={(v) => setOpt({ ...opt, shop: v })}
                options={SHOP_TYPES.map((k) => [k, t(`need.shop.${k}`)] as const)} />
      )}
      {measured ? (
        <>
          <p className="small">{lede}</p>
          {/* phone: the list legend is hidden, a one-line ramp carries the ends */}
          <div className="ramp" aria-hidden="true">
            <span className="ramp-bar">{LACK.map((c, i) => legend[i] && <i key={i} style={{ background: c }} />)}</span>
            <span className="ramp-ends"><span>{legend.find(Boolean)}</span><span>{[...legend].reverse().find(Boolean)}</span></span>
          </div>
          <ul className="legend">
            {legend.map((label, i) => label && <li key={i}><i className="sw" style={{ background: LACK[i] }} />{label}</li>)}
            {lens !== 'services' && <li><i className="sw sw-blank" />{t(`need.blank.${lens === 'heat' ? 'heat' : lens === 'shops' ? 'shops' : 'r3'}`)}</li>}
            <li><i className="sw sw-few" />{t('need.few', { min: String(MIN_RESIDENTS), n: String(fewResidents(city)) })}</li>
          </ul>
          <p className="small panel-source">{t(`need.lenses.${lens}.source`)} {t(`need.lenses.${lens}.limit`)}</p>
          <Equity city={city} lens={lens} opt={opt} />
          <p className="label panel-sub">{t('need.lacking')}</p>
          <ol className="toplist">
            {list.map((s) => (
              <li key={s.id}>
                <button type="button" onClick={() => onPick(s)}>
                  <i className="dot" style={{ background: LACK[(needStep(s, lens, opt) ?? 1) - 1] }} />
                  <span>{tie(sectorName(s, loc), loc)}<small>{tie(sectorPlace(s, loc), loc)}</small></span><span className="mono">{needLabel(t, s, lens, opt, loc)}</span>
                </button>
              </li>
            ))}
          </ol>
        </>
      ) : (
        <p className="small">{t('need.notMeasured', { city: name })} <button type="button" className="link" onClick={otherCity}>{t('need.seeIn', { city: tc(`cities.${city.city === 'brussels' ? 'antwerp' : 'brussels'}`) })}</button></p>
      )}
    </section>
  )
}
