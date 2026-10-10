import type { Metadata } from 'next'
import { hasLocale } from 'next-intl'
import { getTranslations, setRequestLocale } from 'next-intl/server'
import { headers } from 'next/headers'
import { notFound } from 'next/navigation'
import { CitySelect } from '@/components/CitySelect'
import { DocShell } from '@/components/doc/DocShell'
import { Section } from '@/components/doc/Section'
import { JsonLd } from '@/components/JsonLd'
import { keptEnglish, localePath } from '@/i18n/locales'
import { routing } from '@/i18n/routing'
import { EV } from '@/lib/analytics'
import { CITIES, type CityKey } from '@/lib/cities'
import { dataQuery, hasDataset, indexable, resolveData, type Search as DataSearch } from '@/lib/data-page'
import { downloadName, downloadPath, formatOf, groupId, GROUPS, kb } from '@/lib/downloads'
import { fixed, int, type Locale } from '@/lib/format'
import { atlasHref } from '@/lib/links'
import { datasetLd, docMetadata } from '@/lib/seo'
import { siteUrl } from '@/lib/site'
import { count } from '@/lib/icu'
import { getT } from '@/lib/t'
import { tie, plain } from '@/lib/typography'
import type { DownloadLayer } from '@/lib/types'

/* The data download (phase 2b, docs/07-unified-frondia.md): every layer behind the atlas as a CSV with
   its manifest — what it measures, how, from what source, with what threshold, its limits, every
   column, and the terms of reuse — written by scripts/site/downloads.py and read here on the server.
   Word for word the Vite page (site/apps/landing/src/pages/Data.jsx), on the dossier's measured
   layout. A file per card, as Optimal Workshop lists its downloads (a format tag, one line on what is
   inside, the download); the columns as Snowflake's data dictionary. Each city's view also carries
   its layers as a schema.org Dataset, for Google Dataset Search. A download is counted (Umami, the
   `download` event) and stays a plain download: the browser saves the file under its frondia- name. */

const PATH = '/data'

type Search = Promise<DataSearch>
type Params = Promise<{ locale: string }>

export async function generateMetadata({ params, searchParams }: { params: Params; searchParams: Search }): Promise<Metadata> {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  const [t, common, landingTitle, r] = await Promise.all([
    getTranslations({ locale, namespace: 'data' }),
    getTranslations({ locale, namespace: 'common' }),
    getTranslations({ locale, namespace: 'landing.meta' }).then((lt) => lt('title')),
    searchParams.then((q) => resolveData(q, locale)),
  ])
  const title = r.state === 'ok' ? t('meta.title', { city: common(`cities.${r.city}`) }) : t('meta.titleNone')
  return docMetadata({ locale, path: PATH, query: dataQuery(r), title, description: t('lede'), indexable: indexable(r), ogAlt: landingTitle })
}

export default async function DataPage({ params, searchParams }: { params: Params; searchParams: Search }) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  setRequestLocale(locale)
  // the Dataset's words go to crawlers as plain text: without the no-break spaces tie() puts in the page
  const [{ t, raw }, common, plain, plainCommon, r] = await Promise.all([
    getT('data'), getT('common'), getTranslations({ locale, namespace: 'data' }), getTranslations({ locale, namespace: 'common' }),
    searchParams.then((q) => resolveData(q, locale)),
  ])
  // downloads.json unreadable: the one line the old page showed then (its "Loading…" never ended),
  // in the terse shape of the dossier's and the commune's own error — still 200, not indexed
  if (r.state === 'error') return <DocShell><p className="doc-missing">{common.t('unavailable')}</p></DocShell>
  const loc: Locale = locale
  const city = r.city
  const c = r.d
  const site = siteUrl()
  const rows = (key: string) => raw<unknown[]>(key).map((_, i) => i)
  const nonce = (await headers()).get('x-nonce') ?? undefined

  return (
    <DocShell>
      {hasDataset(r) && (
        <JsonLd nonce={nonce} data={datasetLd(city, r.d, site, {
          loc, name: plain('ld.name', { city: plainCommon(`cities.${city}`) }), place: plainCommon(`cities.${city}`), description: plain('lede'), country: plain('ld.country'), temporalCoverage: r.temporal,
        })} />
      )}
      <header className="doc-head">
        <p className="label">{t('kicker')}</p>
        <h1 className="display-l">{t('title')}</h1>
        <p className="lede doc-standfirst">{t('lede')}</p>
        <dl className="doc-meta">
          {rows('facts').map((i) => (
            <div key={i}><dt className="label">{t(`facts.${i}.k`)}</dt><dd className="mono">{t(`facts.${i}.v`, {
              name: common.t(`cities.${city}`), n: int(c.layers.length, loc), formats: [...new Set(c.layers.map(formatOf))].join(common.t('sep.list')),
            })}</dd></div>
          ))}
        </dl>
        <div className="doc-actions">
          <CitySelect city={city} label={t('city')} options={CITIES.map((k) => ({ key: k, name: common.t(`cities.${k}`) }))} />
          <a className="pill pill--ghost pill--sm" href={downloadPath(city, 'manifest.json')} download={downloadName(city, 'manifest.json')}
             data-ev={EV.download} data-ev-file="manifest.json" data-ev-city={city}>{t('manifest')} <span className="arr">↓</span></a>
          <a className="pill pill--ghost pill--sm" href={atlasHref(loc, `?city=${city}`)} data-ev={EV.atlas} data-ev-from="data">{t('inAtlas')} <span className="arr">→</span></a>
        </div>
      </header>

      {GROUPS.map(({ group, key }) => {
        const ls = c.layers.filter((l) => l.group === group)
        if (!ls.length) return null
        const id = groupId(group)
        return (
          <Section key={group} id={id} eyebrow={t(`groups.${key}.label`)} title={t(`groups.${key}.title`)} wide>
            <div className="data-list">{ls.map((l) => <Layer key={l.key} l={l} city={city} loc={loc} />)}</div>
          </Section>
        )
      })}

      <footer className="doc-foot">
        <dl className="doc-colophon">
          {rows('colophon').map((i) => (
            <div key={i}><dt>{t(`colophon.${i}.k`)}</dt><dd>{t(`colophon.${i}.v`, { site: new URL(site).host + localePath(loc, PATH) })}</dd></div>
          ))}
        </dl>
        {/* L6: the downloads and their manifest stay English; a page in another language says so once */}
        {loc !== 'en' && <p className="doc-small">{t('filesInEnglish')}</p>}
      </footer>
    </DocShell>
  )
}

async function Layer({ l, city, loc }: { l: DownloadLayer; city: CityKey; loc: Locale }) {
  const { t, raw } = await getT('data')
  const fmt = formatOf(l)
  const n = int(l.rows, loc)   // '—' when a layer has no row count, as on the old page
  const tag = [
    fmt,
    t(fmt === 'GeoPackage' ? 'file.polygons' : 'file.rows', { count: count(l.rows ?? 0), n }),
    t('file.kb', { kb: int(kb(l.bytes), loc) }),
    ...(l.computed ? [t('computed', { d: l.computed })] : []),
  ]
  const x = (s: string) => tie(s, loc)
  return (
    <article className="data-card" id={l.key}>
      <div className="data-card-head">
        <h3 className="data-card-title">{x(l.title)}</h3>
        <p className="mono data-tag seq-wrap"><span className="seq">
          {tag.map((s) => <span key={s}>{s}</span>)}
        </span></p>
      </div>
      <p className="data-card-what">{x(l.measures)}</p>
      <p className="data-card-meta">
        <span>{l.threshold != null ? t('threshold', { v: fixed(l.threshold, 4, loc) }) : t('noThreshold')}</span>
        {/* a licence's name stays as its rights holder writes it (L6), so in English words it is marked English, as the credits */}
        <span lang={keptEnglish(loc)}>{x(l.licence)}</span>
      </p>
      <a className="pill pill--ink pill--sm data-dl" href={downloadPath(city, l.file)} download={downloadName(city, l.file)}
         data-ev={EV.download} data-ev-file={l.file} data-ev-city={city}>{t('download', { fmt })} <span className="arr">↓</span></a>
      <details className="data-more">
        <summary><span>{t('details')}</span><span className="data-more-mark" aria-hidden="true">+</span></summary>
        <dl className="data-facts">
          <div><dt>{t('rows.method')}</dt><dd>{x(l.method)}</dd></div>
          <div><dt>{t('rows.source')}</dt><dd>{x(l.source)}</dd></div>
          <div><dt>{t('rows.threshold')}</dt><dd>{x(l.threshold_from)}</dd></div>
          <div><dt>{t('rows.limits')}</dt><dd><ul>{l.limits.map((s) => <li key={s}>{x(s)}</li>)}</ul></dd></div>
          <div><dt>{t('rows.licence')}</dt><dd lang={keptEnglish(loc)}>{x(l.licence)}</dd></div>
          <div><dt>{t('rows.credit')}</dt><dd><ul lang={keptEnglish(loc)}>{l.credit.map((s) => <li key={s}>{x(s)}</li>)}</ul></dd></div>
        </dl>
        <div className="data-cols-wrap" tabIndex={0} role="region" aria-label={plain(t('columnsLabel', { title: l.title }))}>
          <table className="data-cols">
            <thead><tr>{raw<unknown[]>('columns').map((_, i) => <th key={i} scope="col">{t(`columns.${i}`)}</th>)}</tr></thead>
            <tbody>{l.columns.map((col) => <tr key={col.name}><th scope="row" className="mono">{col.name}</th><td>{x(col.description)}</td></tr>)}</tbody>
          </table>
        </div>
      </details>
    </article>
  )
}
