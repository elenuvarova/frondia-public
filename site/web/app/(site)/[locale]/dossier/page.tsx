import type { Metadata } from 'next'
import { hasLocale } from 'next-intl'
import { getTranslations, setRequestLocale } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { Callout } from '@/components/doc/Callout'
import { DocShell } from '@/components/doc/DocShell'
import { Scale } from '@/components/doc/Scale'
import { Section } from '@/components/doc/Section'
import { PrintButton } from '@/components/PrintButton'
import { Link } from '@/i18n/navigation'
import { routing } from '@/i18n/routing'
import { EV } from '@/lib/analytics'
import type { CityKey } from '@/lib/cities'
import { getCases, getPoints } from '@/lib/data'
import { dossierAddress, dossierQuery, indexable, resolveDossier, type Search as DossierSearch } from '@/lib/dossier'
import { dec, fixed, int, longDate, pct, shortWindow, signed, type Locale } from '@/lib/format'
import { placeName, sectorLabel, sectorPlace } from '@/lib/names'
import { atlasHref } from '@/lib/links'
import { docMetadata } from '@/lib/seo'
import { siteUrl } from '@/lib/site'
import { getT } from '@/lib/t'
import { tie, plain } from '@/lib/typography'
import type { City, Sector } from '@/lib/types'

/* The sector dossier (phase 2b, docs/07-unified-frondia.md): one sector, why money for greening
   should come to it, and how the result will be checked afterwards. Word for word the Vite page
   (site/apps/landing/src/pages/Dossier.jsx), every number from the site's data (city.dossier and
   the sector itself), read on the server; it prints on A4 from the browser (styles/dossier.css).
   Without ?sector= it opens the sector the open rule picks. A wrong address is not an error page:
   an unknown sector or a missing city file answers 200 with the old explanation and noindex, and a
   city where the rule picks nothing (Liège, Charleroi: exempt under Article 8(1)) says so. */

const CASE_ORDER = ['ninove', 'droogdokkenpark', 'spoor-noord'] as const
// the cases table's columns, by name: the reading (k of n seasons) is wide screens only — on a phone
// it moves under the intervention's name (doc-phone)
const CASES_HEAD = [
  ['intervention', ''], ['effect', 'num'], ['threshold', 'num'], ['times', 'num'], ['reading', 'doc-wide-only'],
] as const
const PATH = '/dossier'

type Search = Promise<DossierSearch>
type Params = Promise<{ locale: string }>

export async function generateMetadata({ params, searchParams }: { params: Params; searchParams: Search }): Promise<Metadata> {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  const [t, tc, landingTitle, r] = await Promise.all([
    getTranslations({ locale, namespace: 'dossier' }),
    getTranslations({ locale, namespace: 'common' }),
    getTranslations({ locale, namespace: 'landing.meta' }).then((lt) => lt('title')),
    searchParams.then(resolveDossier),
  ])
  const title = r.state === 'ok' ? t('meta.title', { name: sectorLabel(r.s, locale, (id) => tc('sectorFallback', { id })) }) : t('meta.titleNone')
  return docMetadata({ locale, path: PATH, query: dossierQuery(r), title, description: t('standfirst'), indexable: indexable(r), ogAlt: landingTitle })
}

export default async function Dossier({ params, searchParams }: { params: Params; searchParams: Search }) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  setRequestLocale(locale)
  const [{ t }, { t: tc }] = await Promise.all([getT('dossier'), getT('common')])
  const r = await resolveDossier(await searchParams)
  const toAtlas = (rest: string) => (
    <a href={atlasHref(locale, rest)} data-ev={EV.atlas} data-ev-from="dossier">{tie(`${t('inAtlas')} →`, locale)}</a>
  )

  if (r.state === 'error') return <DocShell><h1 className="doc-missing">{t('missing')}</h1></DocShell>
  if (r.state === 'noPick') {
    const lau = r.city.communes?.list.find((c) => c.green != null)
    return (
      <DocShell>
        <h1 className="doc-missing">{t('noPick', { city: tc(`cities.${r.cityKey}`), green: pct(lau?.green, 1, locale) })} {toAtlas(`?city=${r.cityKey}`)}</h1>
      </DocShell>
    )
  }
  if (r.state === 'missing') {
    return <DocShell><h1 className="doc-missing">{t('missing')} {toAtlas(`?city=${r.cityKey}`)}</h1></DocShell>
  }
  const [cases, points] = await Promise.all([getCases(), getPoints(r.cityKey)])
  return <DocShell><Body loc={locale} cityKey={r.cityKey} city={r.city} s={r.s} cases={cases} points={points} /></DocShell>
}

async function Body({ loc, cityKey, city, s, cases, points }: {
  loc: Locale; cityKey: CityKey; city: City; s: Sector
  cases: Awaited<ReturnType<typeof getCases>>; points: Awaited<ReturnType<typeof getPoints>>
}) {
  // common.raw('sep.dot') in the place list: the bare " · " there was never tied, and t would tie its first space
  const [{ t, raw }, landing, common] = await Promise.all([getT('dossier'), getT('landing'), getT('common')])
  // the catalogue's lists decide how many rows there are; each row is still read through t (tied)
  const rows = (key: string) => raw<unknown[]>(key).map((_, i) => i)
  const money = (v: number | null | undefined) => (v != null ? t('money', { v: int(v, loc) }) : '—')

  const dz = city.dossier, med = dz.medians
  const t24 = s.t24!
  // a nameless sector is called by its code: the title, the heading and the table's row read "Sector 21004A19-"
  const name = sectorLabel(s, loc, (id) => common.t('sectorFallback', { id }))
  const measured = (k: 't24' | 'n24') => city.sectors.filter((x) => x[k] != null)
  // at least 1: «the lowest 0 %» reads as nonsense for the city's least green sector (re-check 3)
  const lower = (k: 't24' | 'n24') => Math.max(1, Math.round((100 * measured(k).filter((x) => x[k]! < s[k]!).length) / measured(k).length))
  const [cutLow] = dz.cuts
  const lowIncome = s.inc != null && s.inc <= cutLow
  const inThird = !!s.lt3
  const [lo, hi] = dz.thirds
  const ratio = lo.t24 / hi.t24
  const thr = city.thresholds
  const bg = city.background
  const law = city.communes?.list.find((c) => c.code === s.id.slice(0, 5) && c.green != null)
  // the printed sheet and the colophon carry the page's own address — the site's, not the request's host
  const url = dossierAddress(siteUrl(), loc, cityKey, s.id)
  const picked = dz.pick.ids[0] === s.id

  // the reading of a share of the city's median, in words (gap in the title, the fairness heading)
  const share = t24 / med.t24
  const gap = share <= 0.55 ? { gap: 'half', p: '' }
    : share < 0.95 ? { gap: 'below', p: int(Math.round(100 * (1 - share)), loc) }
      : share <= 1.05 ? { gap: 'at', p: '' }
        : { gap: 'above', p: int(Math.round(100 * (share - 1)), loc) }
  const fairKind = ratio < 0.4 ? 'less' : ratio <= 0.6 ? 'half' : ratio < 0.95 ? 'share' : 'even'

  // after the baseline: the bulletin's seasons, read into words, joined as the old page joined them
  const span = dz.seasons.length > 1 ? `${dz.seasons[0]}–${dz.seasons[dz.seasons.length - 1]}` : String(dz.seasons[0] ?? '')
  const after = dz.seasons.length
    ? (s.after?.length
      ? t('trend.after', { span, items: s.after.map(([yr, kind, eff]) => t('trend.afterItem', { year: String(yr), kind: t(`trend.kinds.${kind}`), effect: signed(eff, 3, loc) })).join(common.t('sep.semi')) })
      : t('trend.afterNone', { span }))
    : null

  // 3-30-300 and heat, when both layers exist here
  let rule: { lead: string; body: string } | null = null
  if (s.cs != null && s.hot != null && s.p30 != null) {
    const fails: string[] = []
    if (!s.p30) fails.push(t('fair.rule.canopyFail', { c: pct(s.cs, 1, loc) }))
    if (!s.p300) fails.push(t('fair.rule.parkFail', { p: pct(s.np, 0, loc) }))
    const both = s.hot >= 1 && inThird
    const rr = city.heat_canopy_r
    rule = {
      lead: t(both ? 'fair.rule.leadBoth' : 'fair.rule.lead'),
      body: t('fair.rule.body', {
        verdict: fails.length === 2 ? 'none' : fails.length === 1 ? 'one' : 'both', fails: fails.join(common.t('sep.semi')),
        lst: fixed(s.lst, 1, loc), exc: fixed(Math.abs(s.hot), 1, loc), side: s.hot >= 0 ? 'above' : 'below',
        strength: rr <= -0.8 ? 'deterministic' : rr <= -0.5 ? 'strong' : 'noticeable', r: fixed(rr, 2, loc), both: both ? 'yes' : 'no',
      }),
    }
  }

  const here = points ? points.points.filter((p) => p.s === s.id && p.r <= 20).sort((a, b) => a.t.localeCompare(b.t) || a.r - b.r) : []
  const regDate = points && longDate(points.registered_at, loc)
  const caseRows = CASE_ORDER.map((slug) => cases.find((c) => c.slug === slug)).filter((c) => c != null)
  const income = lowIncome && inThird ? t('income.both', { cut: int(cutLow, loc) })
    : s.inc != null ? t('income.one', { inc: int(s.inc, loc), cut: int(cutLow, loc) }) : t('income.none')
  const rules = dz.rules

  return (
    <>
      {/* the printed sheet carries its own address (komoot's print view) */}
      <p className="doc-print-head" aria-hidden="true"><span>frondia</span><span>{url}</span></p>
      <header className="doc-head">
        <p className="label">{t('kicker', { commune: sectorPlace(s, loc), id: s.id })}</p>
        <h1 className="display-l">{t('title', { name, ...gap, pop: int(s.pop, loc) })}</h1>
        <p className="lede doc-standfirst">{t('standfirst')}</p>
        <dl className="doc-meta">
          {rows('facts').map((i) => (
            <div key={i}><dt className="label">{t(`facts.${i}.k`)}</dt><dd className="mono">{t(`facts.${i}.v`, { last: String(dz.seasons[dz.seasons.length - 1] ?? 2024) })}</dd></div>
          ))}
        </dl>
        <div className="doc-actions">
          <PrintButton label={t('print')} />
          <a className="pill pill--ghost pill--sm" href={atlasHref(loc, `?city=${cityKey}&sector=${s.id}`)} data-ev={EV.atlas} data-ev-from="dossier">{t('inAtlas')} <span className="arr">→</span></a>
        </div>
      </header>

      <Section id="passport" eyebrow={t('passport.eyebrow')} title={t('passport.title')} wide>
        <dl className="doc-figures">
          <div><dt>{t('passport.residents')}</dt><dd>{int(s.pop, loc)}</dd></div>
          {s.k15 != null && <div><dt>{t('passport.children')}</dt><dd>{int(s.k15, loc)}<small>{pct(s.kid, 0, loc)}</small></dd></div>}
          {s.o65 != null && <div><dt>{t('passport.seniors')}</dt><dd>{int(s.o65, loc)}<small>{pct(s.old, 0, loc)}</small></dd></div>}
          <div><dt>{t('passport.income')}</dt><dd>{money(s.inc)}</dd></div>
          <div><dt>{t('passport.canopy')}</dt><dd>{fixed(s.t24, 3, loc)}</dd></div>
          <div><dt>{t('passport.built')}</dt><dd>{fixed(s.b24, 3, loc)}</dd></div>
        </dl>
        <div className="doc-col">
          <p>{t('standing', { tp: int(lower('t24'), loc), np: int(lower('n24'), loc) })} {income}</p>
          {picked && <p className="doc-small">{t('picked', { minHeat: dec(dz.pick.min_heat, loc), minRes: int(dz.pick.min_residents, loc), n: int(dz.pick.n, loc) })}</p>}
        </div>
      </Section>

      <Section id="state" eyebrow={t('scale.eyebrow')} title={t('scale.title')} wide>
        <Scale s={s} city={city} />
        <div className="doc-col"><p>{t('scale.note')}</p></div>
      </Section>

      <Section id="trend" eyebrow={t('trend.eyebrow')} title={t('trend.title')}>
        <p>{t('trend.body', { w: shortWindow(city.window), ne: signed(s.ne, 4, loc), nt: fixed(thr.ndvi, 4, loc), te: signed(s.te, 4, loc), tt: fixed(thr.trees, 4, loc) })} {s.nv ? t(`trend.means.${s.nv}`) : ''}</p>
        <p>{t('trend.background', { shift: signed(bg.raw_median, 3, loc), kRaw: int(bg.k_raw, loc), n: int(bg.n, loc), share: pct(bg.share_raw, 0, loc), kEff: int(bg.k_eff, loc) })}</p>
        {after && <p>{after}</p>}
        <Callout lead={t('trend.notProof.lead')}>{t('trend.notProof.body')}</Callout>
        {law && (() => {
          const k = law.exempt ? 'exempt' : 'counted'
          return <Callout lead={t(`trend.law.${k}.lead`)}>{t(`trend.law.${k}.body`, { commune: placeName(law, loc), green: pct(law.green, 1, loc) })}</Callout>
        })()}
      </Section>

      <Section id="fairness" eyebrow={t('fair.eyebrow')} title={t('fair.title', { kind: fairKind, p: int(Math.round(100 * (1 - ratio)), loc) })} wide>
        <div className="doc-table-wrap" tabIndex={0} role="region" aria-label={plain(t('fair.eyebrow'))}>
          <table className="doc-table">
            <thead><tr>{rows('fair.head').map((i) => <th key={i} scope="col" className={i ? 'num' : ''}>{t(`fair.head.${i}`)}</th>)}</tr></thead>
            <tbody>
              <tr><th scope="row">{t('fair.rows.lowest')}</th><td className="num">{money(lo.income)}</td><td className="num">{fixed(lo.t24, 3, loc)}</td><td className="num">{fixed(lo.n24, 3, loc)}</td></tr>
              <tr><th scope="row">{t('fair.rows.highest')}</th><td className="num">{money(hi.income)}</td><td className="num">{fixed(hi.t24, 3, loc)}</td><td className="num">{fixed(hi.n24, 3, loc)}</td></tr>
              <tr className="is-here"><th scope="row">{name}</th><td className="num">{money(s.inc)}</td><td className="num">{fixed(s.t24, 3, loc)}</td><td className="num">{fixed(s.n24, 3, loc)}</td></tr>
            </tbody>
          </table>
          <p className="doc-asof">{t('fair.asOf')}</p>
        </div>
        <div className="doc-col">
          <p>{t('fair.note', { ratio: fixed(ratio, 2, loc) })} {t(lowIncome ? (t24 < lo.t24 ? 'fair.group.below' : 'fair.group.level') : 'fair.group.out')}</p>
          {s.k15 != null && (
            <Callout lead={t('fair.kids.lead')}>
              {t('fair.kids.body', {
                k: int(s.k15, loc), kp: pct(s.kid, 0, loc), o: int(s.o65, loc), op: pct(s.old, 0, loc), o80: int(s.o80, loc),
                third: pct(dz.kids_third, 0, loc), hardest: dz.kids_third > 0.38 ? 'yes' : 'no',
              }) + (inThird ? ` ${t('fair.kids.inThird')}` : '')}
            </Callout>
          )}
          {rule && <Callout lead={rule.lead} tone="warn">{rule.body}</Callout>}
        </div>
      </Section>

      <Section id="place" eyebrow={t('place.eyebrow')} title={t('place.title')}>
        {here.length ? (
          <>
            <p>{t('place.lede', { n: int(here.length, loc), date: regDate || '' })}</p>
            <ul className="doc-points">
              {here.map((p) => (
                <li key={`${p.t}-${p.r}`}><span>{common.t(`objects.one.${p.t}`)}</span><span className="mono">{common.t('sep.rank', { n: String(p.r) })}{common.raw<string>('sep.dot')}{p.role ? t(`place.role.${p.role}`) : ''}</span></li>
              ))}
            </ul>
          </>
        ) : <p>{t('place.none')}</p>}
        {/* trees are ranked by sector, not by point: one sentence when this sector is among the twenty (tree_priority.py) */}
        {s.tr != null && s.trl && city.tree_named_at && (
          <p>{t('place.tree', { rank: String(s.tr), role: s.trl, date: longDate(city.tree_named_at, loc), target: pct(city.tree_target ?? 0.3, 0, loc), reg: city.tree_register_copy ? 'yes' : 'no', copy: city.tree_register_copy ? longDate(city.tree_register_copy, loc) : '' })}</p>
        )}
      </Section>

      <Section id="cases" eyebrow={t('cases.eyebrow')} title={t('cases.title')} wide>
        {/* the scroller's own name: the section is already a region named by its heading (re-check 2, landmark-unique) */}
        <div className="doc-table-wrap" tabIndex={0} role="region" aria-label={plain(t('cases.eyebrow'))}>
          <table className="doc-table">
            <thead><tr>{CASES_HEAD.map(([k, cls]) => <th key={k} scope="col" className={cls}>{t(`cases.head.${k}`)}</th>)}</tr></thead>
            <tbody>
              {caseRows.map((c) => {
                const nd = c.instruments[0]!, eff = c.defensible_effect ?? nd.effect
                const k = c.series.seasons.filter((x) => x.effect > c.series.threshold).length
                const series = t('cases.series', { k: int(k, loc), n: int(c.series.seasons.length, loc) })
                return (
                  <tr key={c.slug}>
                    <th scope="row">{landing.t(`cases.${c.slug}.place`)}<small>{landing.t(`cases.${c.slug}.city`)}: {t(`cases.what.${c.slug}`, { ha: fixed(c.area_ha, 1, loc) })}</small>
                      <small className="doc-phone">{series}</small></th>
                    <td className="num">{signed(eff, 3, loc)}</td>
                    <td className="num">{fixed(nd.threshold, 3, loc)}</td>
                    <td className="num">{fixed(eff / nd.threshold, 1, loc)}×</td>
                    <td className="doc-wide-only">{series}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <div className="doc-col">
          <p>{t('cases.note')}</p>
          <Callout lead={t('cases.left.lead')}>{t('cases.left.body')}</Callout>
        </div>
      </Section>

      <Section id="commitment" eyebrow={t('commitment.eyebrow')} title={t('commitment.title')}>
        <ol className="doc-pledges">
          {rows('commitment.items').map((i) => (
            <li key={i}><strong>{t(`commitment.items.${i}.lead`)}</strong> {t(`commitment.items.${i}.body`, {
              controls: int(rules.controls, loc), km: dec(rules.exclusion_m / 1000, loc), minScenes: int(rules.min_scenes, loc), maxGap: dec(rules.max_gap, loc),
            })}</li>
          ))}
        </ol>
      </Section>

      <Section id="limits" eyebrow={t('limits.eyebrow')} title={t('limits.title')}>
        <ul className="doc-limits">{rows('limits.items').map((i) => <li key={i}>{t(`limits.items.${i}`)}</li>)}</ul>
      </Section>

      <footer className="doc-foot">
        <dl className="doc-colophon">
          {rows('colophon').map((i) => <div key={i}><dt>{t(`colophon.${i}.k`)}</dt><dd>{t(`colophon.${i}.v`)}</dd></div>)}
          <div><dt>{t('online')}</dt><dd className="mono">{url}</dd></div>
          <div><dt>{t('data.label')}</dt><dd><Link href={`/data?city=${cityKey}`}>{t('data.link')}</Link></dd></div>
        </dl>
      </footer>
    </>
  )
}
