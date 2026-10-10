import { HistogramBlock } from '@/components/HistogramBlock'
import type { Hist } from '@/components/NullHistogram'
import { Rule } from '@/components/Rule'
import { fixed, int } from '@/lib/format'
import { getT } from '@/lib/t'
import type { Case, City } from '@/lib/types'

// (3) How it decides: the placebo calibration in three steps, and the noise it measures
export async function Threshold({ city, ninove }: { city: City; ninove?: Case }) {
  const [{ t, rich, raw, loc }, { t: tc }] = await Promise.all([getT('landing'), getT('common')])
  const name = tc(`cities.${city.city}`)
  const thr = city.thresholds.ndvi
  const nv = ninove?.instruments.find((i) => i.key === 'ndvi')
  const steps = raw<string[]>('threshold.steps')
  return (
    <section id="threshold" className="section night grain section--method">
      <div className="wrap">
        <Rule n={4} right={t('threshold.ruleRight')}>{t('threshold.rule')}</Rule>
        <div className="split reveal">
          <h2 className="display-l">{rich('threshold.title', { em: (c) => <em>{c}</em> })}</h2>
          <ol className="steps">
            {steps.map((_, i) => (
              <li key={i}>
                <span className="mono">0{i + 1}</span>
                <p>{t(`threshold.steps.${i}`, { n: int(city.units.comparable, loc), thr: fixed(thr, 3, loc), city: name })}</p>
              </li>
            ))}
          </ol>
        </div>
        <HistogramBlock hist={city.hist as Hist} thr={thr} city={name} comparable={city.units.comparable}
                        mean={city.null_mean.ndvi} marker={nv?.effect} />
      </div>
    </section>
  )
}
