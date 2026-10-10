import type { CSSProperties } from 'react'
import { Rule } from '@/components/Rule'
import { localePath } from '@/i18n/locales'
import { fixed, pct } from '@/lib/format'
import { atlasHref } from '@/lib/links'
import { EV } from '@/lib/analytics'
import { getT } from '@/lib/t'
import type { Facts } from '@/lib/types'
import { inWords } from './words'

interface Audience { key: 'regions' | 'municipalities' | 'funders' }

// (2) The law and who it is for. The funders' link opens its question below (FaqAnchors).
export async function Law({ facts }: { facts: Facts }) {
  const [{ t, rich, raw, loc }, { t: tc }] = await Promise.all([getT('landing'), getT('common')])
  const b = facts.cities.brussels!.art8
  const others = Object.entries(facts.cities).filter(([k]) => k !== 'brussels')
  const rs = Object.values(facts.cities).flatMap((c) => c.art8.canopy_r)
  const nStats = 2 + others.length
  const href: Record<Audience['key'], string> = {
    regions: atlasHref(loc),
    municipalities: atlasHref(loc, '?case=ninove'),
    funders: '#q-outline',
  }
  const em = (c: React.ReactNode) => <em>{c}</em>
  return (
    <section id="law" className="section">
      <div className="wrap">
        <Rule n={3} right={t('law.ruleRight')}>{t('law.rule')}</Rule>
        <div className="split reveal">
          <h2 className="display-l">{rich('law.title', { em })}</h2>
          <div className="body">
            <p>{t('law.p1')}</p>
            <p>{t('law.p2')}</p>
          </div>
        </div>
        <div className="stats stats--law reveal" style={{ '--n': nStats <= 4 ? nStats : 3 } as CSSProperties}>
          <div><span className="num-l">{t('of', { k: String(b.exempt.length), n: String(b.laus) })}</span><span className="label">{t('law.stats.exempt')}</span></div>
          <div><span className="num-l">{pct(b.green_ucuc, 1, loc)}</span><span className="label">{t('law.stats.region')}</span></div>
          {others.map(([k, c]) => {
            const a = c.art8, exempt = a.exempt.length > 0, city = tc(`cities.${k}`)
            const label = exempt
              ? (!a.stable && a.green_nw_ucuc <= 0.45
                ? t('law.stats.cityExemptWater', { city, v: pct(a.green_nw_ucuc, 1, loc) })
                : t('law.stats.cityExempt', { city }))
              : (!a.stable && a.green7_ucuc > 0.45
                ? t('law.stats.cityBelowFarmland', { city, v: pct(a.green7_ucuc, 1, loc) })
                : t('law.stats.cityBelow', { city }))
            return (
              <div key={k}>
                <span className="num-l">{pct(a.green_ucuc, 1, loc)}</span>
                <span className="label">{label}</span>
              </div>
            )
          })}
        </div>
        <a className="case-link law-communes reveal" href={localePath(loc, '/commune')}><span className="case-link-t">{t('law.communes')}</span> <span className="arr">→</span></a>
        <ul className="audiences">
          {raw<Audience[]>('audiences').map((x, i) => (
            <li key={x.key} className="reveal">
              <h3 className="display-s">{t(`audiences.${i}.who`)}</h3>
              <p className="body">{t(`audiences.${i}.text`)}</p>
              <a className="case-link" href={href[x.key]}
                 {...(x.key !== 'funders' && { 'data-ev': EV.atlas, 'data-ev-from': `audience-${x.key}` })}>
                <span className="case-link-t">{t(`audiences.${i}.cta`)}</span> <span className="arr">{x.key === 'funders' ? '↓' : '→'}</span>
              </a>
            </li>
          ))}
        </ul>
        <p className="body law-close reveal">
          {rich('law.close', {
            em, lo: fixed(Math.min(...rs), 2, loc), hi: fixed(Math.max(...rs), 2, loc),
            count: inWords(raw<string[]>('words'), Object.keys(facts.cities).length).toLowerCase(),
          })}
        </p>
      </div>
    </section>
  )
}
