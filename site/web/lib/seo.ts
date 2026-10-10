// The site's own structured data: WebSite on the landing, a Dataset per city on /data — functions,
// not components, so it stays a pure value a test can check without rendering anything.
import type { Metadata } from 'next'
import { alternates, localePath, tagOf } from '@/i18n/locales'
import type { AtlasResolved } from './atlas/resolve'
import { atlasPath } from './atlas/state'
import type { CityKey } from './cities'
import { downloadPath, formatOf } from './downloads'
import type { Locale } from './format'
import { siteUrl } from './site'
import type { DownloadsCity } from './types'

export function websiteLd(loc: Locale, siteUrl: string, description?: string): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'Frondia',
    url: siteUrl + localePath(loc, '/'),
    inLanguage: tagOf(loc),
    ...(description ? { description } : {}),
    author: { '@type': 'Person', name: 'Elena Uvarova' },
  }
}

// The og card's own address: a prerendered JPEG per language (app/og/[file]/route.ts), set as
// openGraph.images on every page (and on the [locale] layout, for the 404) so og:image is always this
// exact absolute address. Twitter's card follows without its own `images` field: Next fills
// twitter:image from openGraph.images when `twitter` isn't set.
export const OG_SIZE = { width: 1200, height: 630 } as const

export function ogImageUrl(loc: Locale, siteUrl: string): string {
  return `${siteUrl}/og/${loc}.jpg`
}

export function ogImageMeta(loc: Locale, siteUrl: string, alt: string): Array<{ url: string; width: number; height: number; type: string; alt: string }> {
  return [{ url: ogImageUrl(loc, siteUrl), ...OG_SIZE, type: 'image/jpeg', alt }]
}

// ── a document page's head (dossier, commune, data, register) ─────────────────────────────────
// Every URL on SITE_URL: the canonical keeps the page's own query (its city, sector or code), and so
// does each language's alternate; og:url is the canonical; robots only when the page is not to be
// found (a wrong address, missing data). The og card's alt is the landing's title, as on every page.
export interface DocHead {
  locale: Locale
  path: string // '/dossier'
  query: string // '?city=brussels&sector=…', '' for none
  title: string
  description: string
  indexable: boolean
  ogAlt: string
}

export function docMetadata({ locale, path, query, title, description, indexable, ogAlt }: DocHead): Metadata {
  const site = siteUrl()
  const url = site + localePath(locale, path) + query
  const languages = Object.fromEntries(Object.entries(alternates(path, site)).map(([k, v]) => [k, v + query]))
  return {
    metadataBase: new URL(site),
    title,
    description,
    alternates: { canonical: url, languages },
    ...(indexable ? {} : { robots: { index: false } }),
    openGraph: {
      title, description, url, locale: tagOf(locale).replace('-', '_'), type: 'website',
      images: ogImageMeta(locale, site, ogAlt),
    },
  }
}

// ── the atlas's head (one per view) ─────────────────────────────────────────────────────────
// Every view of a city (a lens, an object, a sector, an audit) is a view of one page (A4 of plan 4): the
// canonical is /atlas?city=<city>, each language's alternate is the canonical's, and it is indexed. og:url is
// the view itself, normalised as the client normalises it (a sector of another city dropped), so a shared link
// previews what it opens; an audit this city does not have is dropped too (Q12), and one it has opens on "what
// changed" (resolveAtlas, Q15) — the raw audit is kept only when the city's file could not be read, so nothing is
// known to drop. noindex only when the server could not read the city's file. Every URL on SITE_URL.
// The words of a view's head live in lib/atlas/head.ts: the atlas's client sets document.title with them too (re-check 2)
export { atlasHeadWords } from './atlas/head'

export interface AtlasHead {
  locale: Locale
  r: AtlasResolved
  title: string
  description: string
  ogAlt: string
}

export function atlasMetadata({ locale, r, title, description, ogAlt }: AtlasHead): Metadata {
  const site = siteUrl()
  const query = `?city=${r.state.city}`
  const canonical = site + localePath(locale, '/atlas') + query
  const languages = Object.fromEntries(Object.entries(alternates('/atlas', site)).map(([k, v]) => [k, v + query]))
  const url = site + atlasPath(locale, { ...r.state, lens: r.lens, sector: r.sector?.id ?? null })
  return {
    metadataBase: new URL(site),
    title,
    description,
    alternates: { canonical, languages },
    ...(r.ok ? {} : { robots: { index: false } }),
    openGraph: {
      title, description, url, locale: tagOf(locale).replace('-', '_'), type: 'website',
      images: ogImageMeta(locale, site, ogAlt),
    },
  }
}

// ── the data page's Dataset (Google Dataset Search) ────────────────────────────────────────────
// One Dataset per city, every value from downloads.json or the city's own data: no licence, format
// or date is assumed. The licence is each file's own (a city mixes CC BY 4.0 with ODbL layers built
// on OpenStreetMap); only when every layer carries the same licence does the dataset get it too.
// A licence the data names is also given its official address, so a crawler can recognise it — the
// name stays the data's own. Every contentUrl is absolute on SITE_URL, never on the request's host.
const MEDIA: Record<string, string> = { CSV: 'text/csv', GeoPackage: 'application/geopackage+sqlite3', JSON: 'application/json' }
const LICENCE_URL: [RegExp, string][] = [
  [/^CC BY 4\.0\b/, 'https://creativecommons.org/licenses/by/4.0/'],
  [/^ODbL 1\.0\b/, 'https://opendatacommons.org/licenses/odbl/1-0/'],
]

export function licenceLd(name: string): Record<string, unknown> {
  const url = LICENCE_URL.find(([re]) => re.test(name))?.[1]
  return { '@type': 'CreativeWork', name, ...(url ? { url } : {}) }
}

export interface DatasetText {
  loc: Locale
  name: string // "Frondia — Brussels: …", from the catalogue
  place: string // the city, common.cities.<key> in the page's language (not the data's English name)
  description: string
  country: string
  temporalCoverage?: string | null
}

export function datasetLd(city: CityKey, d: DownloadsCity, siteUrl: string, x: DatasetText): Record<string, unknown> {
  const fileUrl = (file: string) => siteUrl + downloadPath(city, file)
  const licences = [...new Set(d.layers.map((l) => l.licence))]
  const one = licences.length === 1 ? licences[0]! : null
  const dates = d.layers.map((l) => l.computed).filter((v): v is string => !!v).sort()
  const layers = d.layers.map((l) => {
    const media = MEDIA[formatOf(l)]
    return {
      '@type': 'DataDownload',
      name: l.title,
      description: l.measures,
      contentUrl: fileUrl(l.file),
      ...(media ? { encodingFormat: media } : {}),
      license: licenceLd(l.licence),
      ...(l.computed ? { dateModified: l.computed } : {}),
    }
  })
  const manifest = {
    '@type': 'DataDownload',
    name: 'manifest.json',
    contentUrl: fileUrl('manifest.json'),
    encodingFormat: MEDIA.JSON,
    ...(one ? { license: licenceLd(one) } : {}),
  }
  return {
    '@context': 'https://schema.org',
    '@type': 'Dataset',
    name: x.name,
    description: x.description,
    url: siteUrl + localePath(x.loc, '/data') + `?city=${city}`,
    // name, description and the layers' titles are in the page's language (the files themselves stay English)
    inLanguage: tagOf(x.loc),
    creator: { '@type': 'Person', name: 'Elena Uvarova' },
    ...(one ? { license: licenceLd(one) } : {}),
    spatialCoverage: { '@type': 'Place', name: x.place, containedInPlace: { '@type': 'Country', name: x.country } },
    ...(x.temporalCoverage ? { temporalCoverage: x.temporalCoverage } : {}),
    ...(dates.length ? { dateModified: dates[dates.length - 1] } : {}),
    distribution: [...layers, manifest],
  }
}
