import { BeforeAfter } from '@/components/BeforeAfter'
import { Rule } from '@/components/Rule'
import { Series, type SeriesData } from '@/components/Series'
import { fixed, int, signed, times } from '@/lib/format'
import { caseHref } from '@/lib/links'
import { EV } from '@/lib/analytics'
import { getT } from '@/lib/t'
import type { Case } from '@/lib/types'

type T = Awaited<ReturnType<typeof getT>>

function CaseCard({ c, T, common }: { c: Case; T: T; common: T }) {
  const { t, rich, raw, loc } = T
  const k = `cases.${c.slug}`
  const place = t(`${k}.place`)
  const imageNote = raw<Record<string, string>>(k).imageNote != null ? t(`${k}.imageNote`) : null
  const ndvi = c.instruments[0]!
  const main = c.defensible_effect ?? ndvi.effect
  const above = c.series.seasons.filter((p) => p.effect > c.series.threshold).length
  const b = (x: React.ReactNode) => <b>{x}</b>
  return (
    <article className="case reveal">
      <div className="case-media">
        {c.images.before && c.images.after ? (
          <BeforeAfter before={'/' + c.images.before} after={'/' + c.images.after}
                       altBefore={t('audits.altBefore', { place, window: c.window_before })}
                       altAfter={t('audits.altAfter', { place, window: c.window_after })}
                       tagBefore={rich('audits.tagBefore', { b, window: c.window_before })}
                       tagAfter={rich('audits.tagAfter', { b, window: c.window_after })}
                       label={t('audits.compare', { place })} initial={30} />
        ) : (
          <div className="case-img case-img--none">
            <p className="small">{t('audits.noImage', { ha: int(c.area_ha, loc) })}</p>
          </div>
        )}
      </div>
      <p className="mono case-meta">{t('audits.meta', { city: t(`${k}.city`), ha: fixed(c.area_ha, 1, loc), completed: String(c.completed) })}</p>
      <h3 className="display-m case-title">{rich(`${k}.title`, { em: (x) => <em>{x}</em> })}</h3>
      <p className="case-num">
        <span className="num-l">{signed(main, 3, loc)}</span>
        <span className="label">{t('audits.overThreshold', { times: times(main, ndvi.threshold, 1, loc) })}</span>
      </p>
      <dl className="readout">
        {c.defensible_effect != null && <div><dt className="label">{t('audits.standard')}</dt><dd className="mono">{signed(ndvi.effect, 3, loc)}</dd></div>}
        <div><dt className="label">{t('audits.threshold')}</dt><dd className="mono">{fixed(ndvi.threshold, 3, loc)}</dd></div>
        <div><dt className="label">{t('audits.above')}</dt><dd className="mono">{t('of', { k: String(above), n: String(c.series.seasons.length) })}</dd></div>
        <div><dt className="label">{t('audits.controls')}</dt><dd className="mono">{t('audits.named', { n: String(c.controls.length) })}</dd></div>
      </dl>
      <Series series={c.series as unknown as SeriesData} completed={c.completed} loc={loc} i18n={common} />
      <p className="small case-reading">{t(`${k}.reading`)}{imageNote && <> {imageNote}</>}</p>
      <a className="case-link" href={caseHref(loc, c)} data-ev={EV.audit} data-ev-case={c.slug}>
        <span className="case-link-t">{t('audits.open')}<span className="sr-only">{t('srSuffix', { name: place })}</span></span> <span className="arr">→</span>
      </a>
    </article>
  )
}

// (5) Three places, measured: each audit with its before/after, its numbers, its series and its caveat
export async function Cases({ cases }: { cases: Case[] }) {
  const [T, common] = await Promise.all([getT('landing'), getT('common')])
  const { t, rich } = T
  return (
    <section id="cases" className="section">
      <div className="wrap">
        <Rule n={6} right={t('audits.ruleRight')}>{t('audits.rule')}</Rule>
        <div className="split reveal">
          <h2 className="display-l">{rich('audits.title', { em: (x) => <em>{x}</em> })}</h2>
          <div className="body">
            <p>{t('audits.p1')}</p>
            <p>{t('audits.p2')}</p>
          </div>
        </div>
        <div className="cases">{cases.map((c) => <CaseCard key={c.slug} c={c} T={T} common={common} />)}</div>
      </div>
    </section>
  )
}
