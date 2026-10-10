import type { Metadata } from 'next'
import { hasLocale } from 'next-intl'
import { getTranslations, setRequestLocale } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { DocShell } from '@/components/doc/DocShell'
import { Section } from '@/components/doc/Section'
import { CommuneFinder } from '@/components/CommuneFinder'
import { Link } from '@/i18n/navigation'
import { routing } from '@/i18n/routing'
import { EV } from '@/lib/analytics'
import { communeQuery, finderItems, indexable, resolveCommune, type Search as CommuneSearch } from '@/lib/commune'
import { fixed, int, longDate, pct, signed, type Locale } from '@/lib/format'
import { placeName, sectorName } from '@/lib/names'
import { atlasHref } from '@/lib/links'
import { docMetadata } from '@/lib/seo'
import { count } from '@/lib/icu'
import { getT } from '@/lib/t'
import { spokenPoints, tie, plain } from '@/lib/typography'
import type { Commune as CommuneRow } from '@/lib/types'

/* The commune page (phase 2c, item 3; docs/07-unified-frondia.md): what Article 8 counts in one
   commune and what changed there, every number from communes.json, read on the server. Word for word
   the Vite page (site/apps/landing/src/pages/Commune.jsx), on the dossier's measured layout. Without
   ?code= it is the index: the finder and every commune by city. An unknown code is not an error page:
   it answers 200 with the old message, the finder and noindex. */

const PATH = '/commune'
const ROWS = ['green', 'trees', 'built'] as const
const WHERE = ['least_canopy', 'poorest', 'hottest'] as const

type Search = Promise<CommuneSearch>
type Params = Promise<{ locale: string }>

export async function generateMetadata({ params, searchParams }: { params: Params; searchParams: Search }): Promise<Metadata> {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  const [t, landingTitle, r] = await Promise.all([
    getTranslations({ locale, namespace: 'commune' }),
    getTranslations({ locale, namespace: 'landing.meta' }).then((lt) => lt('title')),
    searchParams.then(resolveCommune),
  ])
  const title = r.state === 'ok' ? t('meta.title', { name: placeName(r.c, locale) }) : t('meta.titleIndex')
  const description = r.state === 'ok' ? t('standfirst') : t('index.lede')
  return docMetadata({ locale, path: PATH, query: communeQuery(r), title, description, indexable: indexable(r), ogAlt: landingTitle })
}

// the finder, its words written here: the browser is not sent the commune catalogue
async function Finder({ communes, current }: { communes: CommuneRow[]; current?: string }) {
  const [{ t, loc }, { t: tc }] = await Promise.all([getT('commune'), getT('common')])
  return (
    <CommuneFinder communes={finderItems(communes, loc, (code) => t('find.nis', { code }), (city) => tc(`cities.${city}`))} current={current}
      labels={{ label: t('find.label'), placeholder: t('find.placeholder'), none: t('find.none') }} />
  )
}

export default async function CommunePage({ params, searchParams }: { params: Params; searchParams: Search }) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  setRequestLocale(locale)
  const { t } = await getT('commune')
  const r = await resolveCommune(await searchParams)

  if (r.state === 'error') return <DocShell><h1 className="doc-missing">{t('missing')}</h1></DocShell>
  if (r.state === 'index') return <DocShell><Index loc={locale} communes={r.communes} /></DocShell>
  if (r.state === 'missing') {
    return <DocShell><h1 className="doc-missing">{t('missing')}</h1><Finder communes={r.communes} /></DocShell>
  }
  return <DocShell><Body loc={locale} c={r.c} communes={r.communes} /></DocShell>
}

async function Index({ loc, communes }: { loc: Locale; communes: CommuneRow[] }) {
  const [{ t }, { t: tc }] = await Promise.all([getT('commune'), getT('common')])
  const byCity = new Map<string, CommuneRow[]>()
  for (const c of communes) byCity.set(c.city, [...(byCity.get(c.city) ?? []), c])
  return (
    <>
      <header className="doc-head">
        <p className="label">{t('index.kicker')}</p>
        <h1 className="display-l">{t('index.title')}</h1>
        <p className="lede doc-standfirst">{t('index.lede')}</p>
        <Finder communes={communes} />
        <p className="doc-small finder-hint">{t('find.hint', { n: int(communes.length, loc) })}</p>
      </header>
      <section className="doc-sec doc-sec--wide commune-index" aria-label={plain(t('index.kicker'))}>
        {[...byCity].map(([city, cs]) => (
          <div key={city} className="commune-index-city">
            <p className="label">{tc(`cities.${city}`)}</p>
            <ul>{cs.map((c) => <li key={c.code}><Link href={`${PATH}?code=${c.code}`} prefetch={false}>{placeName(c, loc)}</Link>
              <span className={`chip${c.art8.exempt ? ' chip--up' : ''}`}><i />{c.art8.exempt ? t('law.exempt') : t('law.counted')}</span></li>)}</ul>
          </div>
        ))}
      </section>
    </>
  )
}

async function Body({ loc, c, communes }: { loc: Locale; c: CommuneRow; communes: CommuneRow[] }) {
  const [{ t, raw }, landing, { t: tc }] = await Promise.all([getT('commune'), getT('landing'), getT('common')])
  // the catalogue's lists decide how many rows there are; each row is still read through t (tied)
  const rows = (key: string) => raw<unknown[]>(key).map((_, i) => i)
  const pc = (v: string) => t('pc', { v })
  // hectares with their sign, as the old page's HA(): a real minus, an explicit plus, nothing on zero
  const HA = (v: number) => t('ha', { v: `${v > 0 ? '+' : v < 0 ? '−' : ''}${fixed(Math.abs(v), 1, loc)}` })
  const side = (v: number) => (v >= 0 ? 'above' : 'below')
  // French «1,2 pt» is read as its full phrase (lib/typography.ts spokenPoints); other languages unchanged
  const spoken = (text: string) => spokenPoints(text, loc, (n) => tc('pointsSpoken', { n: count(n) }))
  const vsLine = (v: number, line: number) =>
    spoken(t('law.vsLine', { p: fixed(Math.abs(100 * (v - line)), 1, loc), side: side(100 * (v - line)), line: int(Math.round(100 * line), loc) }))
  const vsRegion = (v: number, rv: number) =>
    spoken(t('law.vsRegion', { p: fixed(Math.abs(100 * (v - rv)), 1, loc), side: side(100 * (v - rv)) }))
  // a sector's name (a change, an event, the dossier's pick) in the page's language, set as a title
  const name = (s: { n: string; n_nl?: string; n_fr?: string }) => tie(sectorName(s, loc), loc)
  const commune = placeName(c, loc)
  // ' · a · b' after a link or a figure: the middle dot never starts a line (tie glues it to the left)
  const dot = (...parts: string[]) => tie(parts.map((x) => tc('sep.dot') + x).join(''), loc)
  const toAtlas = (extra: string) => ({ href: atlasHref(loc, `?city=${c.city}${extra}`), 'data-ev': EV.atlas, 'data-ev-from': 'commune' })
  const cases = landing.raw<Record<string, { place?: string }>>('cases')

  const a = c.art8, r = a.region
  const b = c.balance, latest = b?.latest
  const bl = b && latest ? b.seasons[latest] : undefined
  const seasons = b ? Object.keys(b.seasons).sort() : []
  const canopyNet = bl ? bl.trees.net : 0
  const lawKind = a.exempt ? 'exempt' : a.green <= 0.45 && a.canopy <= 0.1 ? 'both' : a.green <= 0.45 ? 'green' : 'canopy'
  const kindKey = (k: string) => (k === 'canopy loss' ? 'canopyLoss' : k)

  return (
    <>
      <header className="doc-head">
        <p className="label">{t('kicker', { region: tc(`regions.${c.region_key}`), code: c.code })}</p>
        <h1 className="display-l">{t('title', { name: commune, exempt: a.exempt ? 'yes' : 'no' })}</h1>
        {c.official !== commune && <p className="mono commune-official">{c.official}</p>}
        <p className="lede doc-standfirst">{t('standfirst')}</p>
        <dl className="doc-meta">
          {rows('facts').map((i) => (
            <div key={i}><dt className="label">{t(`facts.${i}.k`)}</dt><dd className="mono">{t(`facts.${i}.v`, {
              pop: int(c.pop, loc), area: fixed(c.area_km2, 1, loc), measured: int(c.measured, loc), sectors: int(c.sectors, loc), lau: c.lau_id,
            })}</dd></div>
          ))}
        </dl>
        <div className="doc-actions">
          <Finder communes={communes} current={c.code} />
        </div>
        <div className="doc-actions">
          <a className="pill pill--ink pill--sm" {...toAtlas('&view=communes')}>{t('inAtlas')} <span className="arr">→</span></a>
          <Link className="pill pill--ghost pill--sm" href={`/data?city=${c.city}#the-law`}>{t('data')} <span className="arr">→</span></Link>
        </div>
      </header>

      <Section id="law" eyebrow={t('law.eyebrow')} title={spoken(t('law.title', { kind: lawKind, p: fixed(100 * (0.45 - a.green), 1, loc) }))} wide>
        <dl className="doc-figures commune-figures">
          <div><dt>{t('law.green')}</dt><dd>{pct(a.green, 1, loc)}<small>{r ? vsRegion(a.green, r.green) : vsLine(a.green, 0.45)}</small></dd></div>
          <div><dt>{t('law.canopy')}</dt><dd>{pct(a.canopy, 1, loc)}<small>{r ? vsRegion(a.canopy, r.canopy) : vsLine(a.canopy, 0.1)}</small></dd></div>
          <div><dt>{t('law.perResident')}</dt><dd>{a.canopy_m2_per_resident != null ? fixed(a.canopy_m2_per_resident, 0, loc) : '—'}<small>{t('law.m2')}</small></dd></div>
        </dl>
        <div className="doc-col">
          <p>{t('law.reading', {
            green: fixed(100 * a.green, 1, loc), canopy: fixed(100 * a.canopy, 1, loc), name: commune,
            exempt: a.exempt ? 'yes' : 'no', stable: a.stable ? 'yes' : 'no',
          })}</p>
          {r && <p className="doc-small">{t('law.region', {
            n: int(r.n, loc), green: fixed(100 * r.green, 1, loc), canopy: fixed(100 * r.canopy, 1, loc), exempt: r.exempt ? 'yes' : 'no',
          })}</p>}
        </div>
        <div className="doc-table-wrap" tabIndex={0} role="region" aria-label={plain(t('law.eyebrow'))}>
          <table className="doc-table">
            <thead><tr>{rows('law.cols').map((i) => <th key={i} scope="col" className={i ? 'num' : ''}>{t(`law.cols.${i}`)}</th>)}</tr></thead>
            <tbody>
              {a.readings.map((x) => (
                <tr key={x.reading}>
                  <th scope="row">{t(`law.readings.${x.reading}`)}</th>
                  <td className="num mono">{x.green != null ? pc(fixed(x.green, 1, loc)) : '—'}</td>
                  <td className="num mono">{x.canopy != null ? pc(fixed(x.canopy, 1, loc)) : '—'}</td>
                  <td className="num">{x.exempt == null ? t('law.notComputed') : x.exempt ? t('law.exempt') : t('law.counted')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>

      {c.baseline && (() => {
        const bs = c.baseline
        return (
          <Section id="baseline" eyebrow={t('base.eyebrow')} title={t('base.title')} wide>
            <div className="doc-table-wrap" tabIndex={0} role="region" aria-label={plain(t('base.eyebrow'))}>
              <table className="doc-table">
                <thead><tr>{rows('base.cols').map((i) => <th key={i} scope="col" className={i ? 'num' : ''}>{t(`base.cols.${i}`)}</th>)}</tr></thead>
                <tbody>
                  {(['ucuc', 'lau'] as const).map((k) => (
                    <tr key={k}>
                      <th scope="row">{t(`base.${k}`)}</th>
                      <td className="num mono">{t('ha', { v: int(bs[`uea_${k}_ha`], loc) })}</td>
                      <td className="num mono">{t('ha', { v: int(bs[`green_${k}_ha`], loc) })}<small>{dot(pc(fixed(bs[`green_${k}_pct`], 1, loc)))}</small></td>
                      <td className="num mono">{t('ha', { v: int(bs[`canopy_${k}_ha`], loc) })}<small>{dot(pc(fixed(bs[`canopy_${k}_pct`], 1, loc)))}</small></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="doc-col"><p className="doc-small">{t('base.note')}</p></div>
          </Section>
        )
      })()}

      {b && (
        <Section id="balance" eyebrow={t('balance.eyebrow', { base: String(b.base) })}
                 title={t('balance.title', { v: HA(canopyNet), s: String(latest) })} wide>
          <div className="doc-table-wrap" tabIndex={0} role="region" aria-label={plain(t('balance.eyebrow', { base: String(b.base) }))}>
            <table className="doc-table">
              {seasons.map((s) => (
                <tbody key={s}>
                  <tr className="doc-table-group">{rows('balance.cols').map((i) => <th key={i} scope="col" className={i ? 'num' : ''}>{t(`balance.cols.${i}`, { s })}</th>)}</tr>
                  {ROWS.map((k) => {
                    const v = b.seasons[s]![k]
                    return (
                      <tr key={k}>
                        <th scope="row">{t(`balance.rows.${k}`)}</th>
                        <td className="num mono">{HA(v.lost)}</td>
                        <td className="num mono">{HA(v.gained)}</td>
                        <td className="num mono"><strong>{HA(v.net)}</strong></td>
                      </tr>
                    )
                  })}
                </tbody>
              ))}
            </table>
          </div>
          <div className="doc-col">
            <p className="doc-small">{t('balance.note')}</p>
            <p className="doc-subhead">{t('balance.events')}</p>
            {c.events.length ? (
              <ul className="doc-points">
                {c.events.map((e) => (
                  <li key={`${e.season}-${e.id}`}>
                    <span><a {...toAtlas(`&sector=${e.id}`)}>{name({ n: e.name, n_nl: e.name_nl, n_fr: e.name_fr })}</a>{dot(String(e.season), t(`balance.kinds.${kindKey(e.kind)}`))}</span>
                    <span className="mono">{e.effect != null ? t('ndvi', { v: signed(e.effect, 3, loc) }) : ''}</span>
                  </li>
                ))}
              </ul>
            ) : <p>{t('balance.none', { a: seasons[0] ?? '', b: seasons[seasons.length - 1] ?? '' })}</p>}
          </div>
        </Section>
      )}

      <Section id="change" eyebrow={t('change.eyebrow', { w: c.change.window.replace(/ /g, '') })}
               title={t('change.title', { up: int(c.change.counts.up, loc), n: count(c.change.counts.up), down: int(c.change.counts.down, loc), m: int(c.measured, loc) })}>
        <p className="doc-subhead">{t('change.green')}</p>
        {c.change.top.length ? (
          <ul className="doc-points">
            {c.change.top.map((x) => <li key={x.id}><span><a {...toAtlas(`&sector=${x.id}`)}>{name(x)}</a>{dot(t(`change.words.${x.v}`))}</span><span className="mono">{signed(x.e, 3, loc)}</span></li>)}
          </ul>
        ) : <p>{t('change.noneGreen')}</p>}
        <p className="doc-subhead">{t('change.built')}</p>
        <p>{t('change.counts', { up: int(c.change.built.up, loc), down: int(c.change.built.down, loc) })}</p>
        {c.change.top_built.length > 0 && (
          <ul className="doc-points">
            {c.change.top_built.map((x) => <li key={x.id}><span><a {...toAtlas(`&m=built&sector=${x.id}`)}>{name(x)}</a>{dot(x.v === 'up' ? t('change.words.sealed') : t('change.words.unsealed'))}</span><span className="mono">{signed(x.e, 3, loc)}</span></li>)}
          </ul>
        )}
      </Section>

      {c.trees && (() => {
        const tr = c.trees
        const planted = tr.planted
        const ys = planted ? Object.keys(planted).sort() : []
        const total = planted ? ys.reduce((s, y) => s + planted[y]!, 0) : 0
        const w = tr.where
        return (
          <Section id="trees" eyebrow={t('trees.eyebrow')} title={t('trees.title', { n: int(tr.trees, loc) })} wide>
            {planted && (
              <>
                <dl className="doc-figures commune-figures commune-years">
                  {ys.map((y) => <div key={y}><dt>{y}</dt><dd>{int(planted[y], loc)}</dd></div>)}
                </dl>
                <div className="doc-col"><p className="doc-small">{t('trees.total', { n: int(total, loc), a: ys[0] ?? '', b: ys[ys.length - 1] ?? '' })}</p></div>
              </>
            )}
            {w && (
              <>
                <div className="doc-col"><p className="doc-subhead">{t('trees.whereTitle')}</p></div>
                <div className="doc-table-wrap" tabIndex={0} role="region" aria-label={plain(t('trees.whereTitle'))}>
                  <table className="doc-table">
                    <thead><tr>{rows('trees.cols').map((i) => <th key={i} scope="col" className={i ? 'num' : ''}>{t(`trees.cols.${i}`)}</th>)}</tr></thead>
                    <tbody>
                      {WHERE.map((k) => {
                        const x = w[k]
                        return (
                          <tr key={k}>
                            <th scope="row">{t(`trees.rows.${k}`)}</th>
                            <td className="num mono">{pc(int(Math.round(100 * x.planted_share), loc))}</td>
                            <td className="num mono">{pc(int(Math.round(100 * x.residents_share), loc))}</td>
                            <td className="num mono">{t('trees.vs', { a: fixed(x.per_1000_in_third, 1, loc), b: fixed(x.per_1000_elsewhere, 1, loc) })}</td>
                            <td className="num mono">{t('trees.vs', { a: fixed(x.per_10ha_in_third, 1, loc), b: fixed(x.per_10ha_elsewhere, 1, loc) })}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
                <div className="doc-col"><p>{t('trees.reading', {
                  resIn: fixed(w.least_canopy.per_1000_in_third, 1, loc), resOut: fixed(w.least_canopy.per_1000_elsewhere, 1, loc),
                  haIn: fixed(w.least_canopy.per_10ha_in_third, 1, loc), haOut: fixed(w.least_canopy.per_10ha_elsewhere, 1, loc),
                })}</p></div>
              </>
            )}
            <div className="doc-col">
              <p className="doc-small">{t('trees.snapshot', { d: longDate(tr.date, loc) })}</p>
              <p className="doc-small">{t('trees.source', { l: tr.licence })}</p>
            </div>
          </Section>
        )
      })()}

      {(c.registered.length > 0 || c.cases.length > 0 || c.dossier) && (
        <Section id="record" eyebrow={t('record.eyebrow')} title={t('record.title')}>
          {c.registered.length > 0 && <>
            <p className="doc-subhead">{t('record.registered')}</p>
            <ul className="doc-points">{c.registered.map((x) => <li key={x.id}>{x.comparable ? tie(x.name, loc) : tie(`${x.name}${tc('sep.dot')}${t('record.refused')}`, loc)}</li>)}</ul>
          </>}
          {c.cases.length > 0 && <>
            <p className="doc-subhead">{t('record.cases')}</p>
            <ul className="doc-points">{c.cases.map((s) => (
              <li key={s}><a {...toAtlas(`&case=${s}`)}>{cases[s]?.place ? landing.t(`cases.${s}.place`) : s}</a></li>
            ))}</ul>
          </>}
          {c.dossier && <>
            <p className="doc-subhead">{t('record.dossier')}</p>
            <ul className="doc-points"><li><Link href={`/dossier?city=${c.city}&sector=${c.dossier.id}`}>{name(c.dossier)}</Link><span className="mono">{c.dossier.id}</span></li></ul>
          </>}
        </Section>
      )}

      <footer className="doc-foot">
        <ul className="doc-limits">{rows('limits').map((i) => <li key={i}>{t(`limits.${i}`)}</li>)}</ul>
      </footer>
    </>
  )
}
