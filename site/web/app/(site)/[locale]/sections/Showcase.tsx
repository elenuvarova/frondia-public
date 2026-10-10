import { Rule } from '@/components/Rule'
import { ThreeMap } from '@/components/ThreeMap'
import { signed } from '@/lib/format'
import { LACK } from '@/lib/lenses'
import { mapCity } from '@/lib/map-city'
import { atlasHref } from '@/lib/links'
import { EV } from '@/lib/analytics'
import { getT } from '@/lib/t'
import type { Case, City, Points } from '@/lib/types'
import { countFor } from '@/lib/verdict'
import { plain } from '@/lib/typography'

type Q = 'need' | 'place' | 'change'
// the query each card opens the atlas with, on that lens
const QUERY: Record<Q, string> = { need: '?q=need&lens=services', place: '?q=place&obj=toilets', change: '?q=change' }

/* (4) One map, three questions: live mini-maps from the atlas's own component and data — the
   product shown as itself, not as a picture of itself (the course's showcase rule) — then a
   screenshot of an audit inside the atlas, with three numbered notes. */
export async function Showcase({ city, ninove, points }: { city: City; ninove: Case; points: Points | null }) {
  const { t, rich, raw, loc } = await getT('landing')
  const nv = ninove.instruments.find((i) => i.key === 'ndvi')!
  const W = city.svg.W
  const pts = (points?.points || []).filter((p) => p.t === 'toilets').sort((a, b) => b.r - a.r)
  const eff = countFor(city.sectors, 'effect', city.thresholds.ndvi)
  const effect = signed(nv.effect, 3, loc)
  const legend: Record<Q, React.ReactNode> = {
    need: <span className="three-ramp" aria-hidden="true">{LACK.map((c) => <i key={c} style={{ background: c }} />)}</span>,
    place: <span className="three-pts" aria-hidden="true"><i className="pt-named" /><i className="pt-control" /><i className="pt-more" /></span>,
    change: <span className="three-ramp" aria-hidden="true"><i style={{ background: 'var(--gain-2)' }} /><i style={{ background: 'var(--noise)' }} /><i style={{ background: 'var(--loss-2)' }} /></span>,
  }
  const b = (c: React.ReactNode) => <b>{c}</b>
  return (
    <section id="atlas" className="section">
      <div className="wrap">
        <Rule n={5} right={t('showcase.ruleRight')}>{t('showcase.rule')}</Rule>
        <div className="split reveal">
          <h2 className="display-l">{rich('showcase.title', { em: (c) => <em>{c}</em> })}</h2>
          <div className="body">
            <p>{t('showcase.body')}</p>
            <a href={atlasHref(loc)} className="pill pill--ink" data-ev={EV.atlas} data-ev-from="showcase">{t('cta.atlas')} <span className="arr">→</span></a>
          </div>
        </div>
        <div className="three reveal">
          {raw<{ key: Q }[]>('three').map((q, i) => {
            const title = t(`three.${i}.title`), cta = t(`three.${i}.cta`)
            return (
              <article key={q.key} className="three-card">
                <a className="three-map" href={atlasHref(loc, QUERY[q.key])} aria-label={plain(t('showcase.threeAria', { title, cta: cta.toLocaleLowerCase(loc) }))}
                   data-ev={EV.atlas} data-ev-from={`three-${q.key}`}>
                  <ThreeMap city={mapCity(city)} kind={q.key} label={t(`showcase.maps.${q.key}`)}>
                    {q.key === 'place' && pts.map((p) => (
                      <circle key={p.r} cx={p.x} cy={p.y} r={p.role === 'named' ? W / 90 : p.role === 'control' ? W / 100 : W / 200}
                              className={`three-pt three-pt--${p.role || 'more'}`} />
                    ))}
                  </ThreeMap>
                </a>
                <p className="mono three-n">0{i + 1} {legend[q.key]}</p>
                <h3 className="display-s">{title}</h3>
                <p className="small">{t(`three.${i}.text`)}</p>
                <a className="case-link" href={atlasHref(loc, QUERY[q.key])} data-ev={EV.atlas} data-ev-from={`three-${q.key}`}>
                  <span className="case-link-t">{cta}<span className="sr-only">{t('srSuffix', { name: title })}</span></span> <span className="arr">→</span>
                </a>
              </article>
            )
          })}
        </div>
        <p className="label three-audit-rule reveal">{t('showcase.auditRule')}</p>
        <figure className="showcase reveal">
          <a className="browser" href={atlasHref(loc, '?case=ninove')} aria-label={plain(t('showcase.browserAria'))}
             data-ev={EV.audit} data-ev-case={ninove.slug}>
            <span className="browser-bar" aria-hidden="true"><i /><i /><i /><span className="mono">{t('showcase.browserBar')}</span></span>
            <span className="browser-shot">
              {/* a phone gets the audit card alone: the whole atlas at 358 px is unreadable */}
              <picture>
                <source media="(max-width: 720px)" type="image/webp" srcSet="/showcase/atlas-ninove-audit.webp" width="588" height="1182" />
                <source media="(max-width: 720px)" srcSet="/showcase/atlas-ninove-audit.jpg" width="588" height="1182" />
                <source type="image/webp" srcSet="/showcase/atlas-ninove.webp" width="2160" height="1350" />
                <img src="/showcase/atlas-ninove.jpg" width="2160" height="1350" loading="lazy" decoding="async"
                     alt={plain(t('showcase.alt', { up: String(eff.up), down: String(eff.down), effect }))} />
              </picture>
              <span className="shot-mark" style={{ left: '16.5%', top: '29%' }} aria-hidden="true">1</span>
              <span className="shot-mark" style={{ left: '72%', top: '84%' }} aria-hidden="true">2</span>
              <span className="shot-mark" style={{ left: '78%', top: '25.5%' }} aria-hidden="true">3</span>
            </span>
          </a>
          <figcaption className="showcase-notes">
            <ol>
              {raw<string[]>('showcase.notes').map((_, i) => (
                <li key={i}><span className="mono">0{i + 1}</span><p>{rich(`showcase.notes.${i}`, { b, effect })}</p></li>
              ))}
            </ol>
          </figcaption>
        </figure>
      </div>
    </section>
  )
}
