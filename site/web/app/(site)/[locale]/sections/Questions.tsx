import { Rule } from '@/components/Rule'
import { tagOf } from '@/i18n/locales'
import { fixed, int } from '@/lib/format'
import { atlasHref } from '@/lib/links'
import { EV } from '@/lib/analytics'
import { getT } from '@/lib/t'
import type { Facts } from '@/lib/types'
import { inWords } from './words'

interface Faq { id: string }

/* (7) Questions: objections from the brief, answered with the numbers from /data. Every question is
   a closed <details>; FaqAnchors opens the one a link or the address asks for. "How often is the
   detector wrong?" appears only when the Groenkaart check is in the data. */
export async function Questions({ facts }: { facts: Facts }) {
  const [{ t, rich, raw, loc }, { t: tc }] = await Promise.all([getT('landing'), getT('common')])
  const list = (xs: string[]) => new Intl.ListFormat(tagOf(loc), { type: 'conjunction' }).format(xs)
  const rs = Object.values(facts.cities).flatMap((c) => c.art8.canopy_r)
  // each city named from the catalogue (common.cities), not from the data's English name
  const cs = Object.entries(facts.cities).map(([key, c]) => ({ ...c, key, city: tc(`cities.${key}`) }))
  const b0 = cs.find((c) => c.key === 'brussels')!
  const wider = cs.filter((c) => c !== b0).map((c, i) => {
    const p = Math.round((c.threshold_ndvi / b0.threshold_ndvi - 1) * 100)
    const key = `${p >= 0 ? 'wider' : 'narrower'}${i === 0 ? 'First' : ''}`
    return t(`questions.${key}`, { name: c.city, p: String(Math.abs(p)) })
  })
  // pooled over Antwerp and Ghent: canopy, the pair where both instruments read trees
  const check = facts.check?.pooled.canopy
  const values = {
    canopyR: t('questions.canopyR', { lo: fixed(Math.min(...rs), 2, loc), hi: fixed(Math.max(...rs), 2, loc) }),
    cities: list(cs.map((c, i) => t(i === 0 ? 'questions.cityFirst' : 'questions.city', { name: c.city, n: int(c.comparable, loc) }))),
    wider: list(wider),
    seasons: inWords(raw<string[]>('words'), new Set(facts.monitoring.map((m) => m.season)).size).toLowerCase(),
    spec: check ? t('of', { k: String(check.specificity.k), n: String(check.specificity.n) }) : '',
    agree: check ? t('of', { k: String(check.agreement_when_ours_changed.k), n: String(check.agreement_when_ours_changed.n) }) : '',
  }
  const faq = raw<Faq[]>('faq').map((f, i) => ({ ...f, i })).filter((f) => f.id !== 'wrong' || check)
  return (
    <section id="faq" className="section">
      <div className="wrap">
        <Rule n={8} right={t('questions.ruleRight')}>{t('questions.rule')}</Rule>
        <div className="faq-grid">
          <h2 className="display-l reveal">{rich('questions.title', { em: (c) => <em>{c}</em> })}</h2>
          <div className="faq">
            {faq.map((f) => (
              <details key={f.id} id={`q-${f.id}`} className="faq-item reveal">
                <summary><h3 className="display-s">{t(`faq.${f.i}.q`)}</h3><span className="faq-mark mono" aria-hidden="true">+</span></summary>
                <p className="body">{t(`faq.${f.i}.a`, values)}</p>
              </details>
            ))}
            <div className="hero-cta hero-cta--left faq-next">
              <a href={atlasHref(loc)} className="pill pill--ink" data-ev={EV.atlas} data-ev-from="faq">{t('cta.atlas')} <span className="arr">→</span></a>
              <a href="#threshold" className="pill pill--ghost">{t('cta.method')}</a>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
