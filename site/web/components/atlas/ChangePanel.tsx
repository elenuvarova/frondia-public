'use client'
import { NullHistogram } from '@/components/NullHistogram'
import { fixed, int, pct, shortWindow, signed } from '@/lib/format'
import { sectorName, sectorPlace } from '@/lib/names'
import type { AtlasCity, AtlasRegistered, Hist } from '@/lib/atlas/types'
import type { Sector } from '@/lib/types'
import { useT } from '@/lib/t-client'
import { Chips, Choice, Seq, Toggle, PanelKicker } from './bits'
import { BuiltBody } from './BuiltBody'
import { CommuneBody } from './CommuneBody'
import { useMoreBelow } from './useMoreBelow'
import { tie, plain } from '@/lib/typography'

interface ChangePanelProps {
  city: AtlasCity
  lens: string
  setLens: (lens: string) => void
  measure: string
  setMeasure: (m: string) => void
  control: boolean
  setControl: (on: boolean) => void
  counts: { up: number; down: number }
  top: Sector[]
  onPick: (s: Sector) => void
  onPickRegistered: (r: AtlasRegistered) => void
}

// What changed: sectors against their matched places, the communes the law counts, the field, the two
// summers side by side (Atlas.jsx 647–712)
export function ChangePanel({ city, lens, setLens, measure, setMeasure, control, setControl, counts, top, onPick, onPickRegistered }: ChangePanelProps) {
  const more = useMoreBelow<HTMLElement>()
  const { t, loc } = useT('atlas')
  const { t: tc } = useT('common')
  const name = tc(`cities.${city.city}`)
  const thr = city.thresholds.ndvi
  const photos = lens === 'photos' ? city.photos : null
  const builtOn = lens === 'change' && measure === 'built' && !!city.built
  const years = city.photos ? { a: String(city.photos.years[0]), b: String(city.photos.years[1]) } : null
  const windowText = lens === 'communes' ? t('communes.window')
    : lens === 'field' && city.field ? t('change.fieldWindow', { year: String(city.field.year) })
    : photos && years ? t('photos.window', years)
    : t('change.window', { window: shortWindow(city.window) })
  const views = [['change', t('change.views.change')], ['communes', t('change.views.communes')], ['field', t('change.views.field')],
    ...(city.photos ? [['photos', t('change.views.photos')]] : [])] as [string, string][]
  const bg = city.background
  const check = city.check?.green
  return (
    <section className="panel" ref={more} aria-label={plain(t('change.aria'))}>
      <PanelKicker>{t('q.change.long')}</PanelKicker>
      <div>
        <h1 className="display-s">{lens === 'communes' ? t('communes.title', { city: name }) : t('change.title', { city: name })}</h1>
        <Seq className="mono panel-window" text={windowText} />
      </div>
      <Chips label={t('change.view')} value={lens} onChange={setLens} options={views} />
      {lens === 'change' && city.built && <Choice label={t('built.measure')} value={measure} onChange={setMeasure}
                                                  options={[['green', t('built.options.green')], ['built', t('built.options.built')]]} />}
      {lens === 'communes' ? <CommuneBody city={city} onPickRegistered={onPickRegistered} /> : builtOn ? <BuiltBody city={city} top={top} onPick={onPick} /> : <>
      <Toggle on={control} onChange={setControl}>{t('change.subtract')}</Toggle>
      {/* the counts change with the switch and the city: said when they do (WCAG 4.1.3, re-check 2) */}
      <div className="counts" aria-live="polite">
        <div><span className="num-l tone-up">{int(counts.up, loc)}</span><span className="label">{t(control ? 'change.counts.upEffect' : 'change.counts.upRaw')}</span></div>
        <div><span className="num-l tone-down">{int(counts.down, loc)}</span><span className="label">{t(control ? 'change.counts.downEffect' : 'change.counts.downRaw')}</span></div>
      </div>
      {photos && years ? (
        <>
          <p className="small photo-lede">{t('photos.lede', years)}</p>
          {/* the outlines have no other key, on a phone too: the compact legend stays */}
          <ul className="legend legend--compact legend--outline">
            <li><i className="sw sw-line-up" />{t(control ? 'photos.legend.up' : 'photos.legend.rawUp')}</li>
            <li><i className="sw sw-line-down" />{t(control ? 'photos.legend.down' : 'photos.legend.rawDown')}</li>
          </ul>
        </>
      ) : (
        <>
          <NullHistogram hist={city.hist as Hist} thr={thr} mode={control ? 'effect' : 'raw'} height={170} compact loc={loc} />
          <ul className="legend">
            <li><i className="sw sw-up" />{t('change.legend.up')}</li>
            <li><i className="sw sw-down" />{t('change.legend.down')}</li>
            <li><i className="sw sw-noise" />{t('change.legend.noise')}</li>
            {control && <li><i className="sw sw-refused" />{t('change.legend.refused', { n: String(city.counts.refused) })}</li>}
          </ul>
        </>
      )}
      <p className="small">
        {control
          ? t('change.threshold', { thr: fixed(thr, 3, loc), n: int(city.units.comparable, loc), city: name })
          : t('change.background', { shift: signed(bg.raw_median, 3, loc), k: String(bg.k_raw), n: String(bg.n), city: name, share: pct(bg.share_raw, 0, loc), eff: String(bg.k_eff) })}
      </p>
      {photos && <p className="small panel-source">{t('photos.note', { window: shortWindow(city.window) })}</p>}
      {control && lens === 'change' && check && (
        <p className="small panel-source">{t('change.check', { sk: String(check.specificity.k), sn: String(check.specificity.n), ck: String(check.agreement_when_ours_changed.k), cn: String(check.agreement_when_ours_changed.n) })}</p>
      )}
      {control && (
        <>
          <p className="label panel-sub">{t('change.top')}</p>
          <ol className="toplist">
            {top.map((s) => (
              <li key={s.id}>
                <button type="button" onClick={() => onPick(s)}>
                  <i className={`dot dot-${s.nv}`} /><span>{tie(sectorName(s, loc), loc)}<small>{tie(sectorPlace(s, loc), loc)}</small></span><span className="mono">{signed(s.ne, 3, loc)}</span>
                </button>
              </li>
            ))}
          </ol>
        </>
      )}
      </>}
    </section>
  )
}
