import { Odometer, OdometerGroup } from '@/components/Odometer'
import { PhotoRustle } from '@/components/PhotoRustle'
import { Rule } from '@/components/Rule'
import { SectorMap } from '@/components/SectorMap'
import { fixed, int, pct, times } from '@/lib/format'
import { mapCity } from '@/lib/map-city'
import { getT } from '@/lib/t'
import type { Case, City } from '@/lib/types'
import { countFor } from '@/lib/verdict'
import { LILAC_BAND, inWords } from './words'

// (1) The rustle and the growth on two maps, the band of four numbers on the photograph between them
export async function Anyway({ city, other, ninove }: { city: City; other: City; ninove?: Case }) {
  const [{ t, rich, raw, loc }, { t: tc }] = await Promise.all([getT('landing'), getT('common')])
  const name = tc(`cities.${city.city}`)
  const bg = city.background, thr = city.thresholds.ndvi
  const eff = countFor(city.sectors, 'effect', thr)
  const nv = ninove?.instruments.find((i) => i.key === 'ndvi')
  const [before = city.window, after = ''] = city.window.split(' → ')
  const em = (c: React.ReactNode) => <em>{c}</em>
  return (
    <section id="anyway" className="section section--band">
      <div className="wrap">
        <Rule n={1} right={t('anyway.ruleRight', { city: name, before, after })}>{t('anyway.rule')}</Rule>
        <div className="split reveal">
          <h2 className="display-l">{rich('anyway.title', { words: inWords(raw<string[]>('words'), bg.k_eff), em })}</h2>
          <p className="body">{t('anyway.body', { share: pct(bg.share_raw, 0, loc), k: int(bg.k_eff, loc) })}</p>
        </div>
      </div>
      {/* the band's photograph never moved on the old page either: it is always still */}
      <PhotoRustle photo={LILAC_BAND} still className="rustle-band">
        <OdometerGroup className="wrap rustle-tiles">
          <div><Odometer value={bg.k_raw} className="num-xl" /><span className="label">{t('anyway.tiles.raw')}</span></div>
          <div><Odometer value={bg.k_eff} className="num-xl" /><span className="label">{t('anyway.tiles.effect')}</span></div>
          <div>
            <Odometer value={`±${fixed(thr, 3, loc)}`} className="num-xl" />
            <span className="label">{t('anyway.tiles.threshold', { city: name, other: tc(`cities.${other.city}`), p: String(Math.round((other.thresholds.ndvi / thr - 1) * 100)) })}</span>
          </div>
          {nv && <div><Odometer value={times(nv.effect, nv.threshold, 1, loc)} className="num-xl" /><span className="label">{t('anyway.tiles.ninove')}</span></div>}
        </OdometerGroup>
      </PhotoRustle>
      <div className="wrap">
        <div className="twin">
          <figure className="twin-map reveal">
            <SectorMap city={mapCity(city)} mode="raw" label={t('anyway.rawMap', { n: String(bg.k_raw) })} />
            <figcaption>
              <span className="num-xl">{bg.k_raw}</span>
              <span className="twin-cap"><span className="label">{t('anyway.rawLabel')}</span>{t('anyway.rawCap')}</span>
            </figcaption>
          </figure>
          <figure className="twin-map reveal">
            <SectorMap city={mapCity(city)} mode="effect" label={t('anyway.effectMap', { up: String(eff.up), down: String(eff.down) })} />
            <figcaption>
              <span className="num-xl">{bg.k_eff}</span>
              <span className="twin-cap">
                <span className="label">{t('anyway.effectLabel')}</span>
                {t('anyway.effectCap', { down: String(eff.down), refused: String(city.counts.refused) })}
              </span>
            </figcaption>
          </figure>
        </div>
        <p className="body twin-close reveal">{t('anyway.close')}</p>
      </div>
    </section>
  )
}
