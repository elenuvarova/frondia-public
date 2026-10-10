import type { MetadataRoute } from 'next'
import { alternates, localePath, PUBLISHED } from '@/i18n/locales'
import { DataError, getCommunes } from '@/lib/data'
import { CITIES } from '@/lib/cities'
import { dossierQuery, resolveDossier } from '@/lib/dossier'
import { siteUrl } from '@/lib/site'

// rendered per request: SITE_URL is read from the running container, not frozen at build time
export const dynamic = 'force-dynamic'

// pages with no address parameters
const PAGES = ['/', '/privacy', '/register']

// /dossier?city=<city>&sector=<picked id>, the canonical long form (Q3), for every city whose open
// rule picks a sector. Liège and Charleroi's rule picks nothing (noPick, Article 8(1)): ?city=liege
// is a one-sentence page, self-canonical and noindex (Q17), so it is not listed; bare /dossier shares
// Brussels's canonical.
async function dossierPaths(): Promise<string[]> {
  const rs = await Promise.all(CITIES.map((city) => resolveDossier({ city })))
  return rs.filter((r) => r.state === 'ok').map((r) => `/dossier${dossierQuery(r)}`)
}

// /commune plus /commune?code=<code> for every commune the data has (23 on 28 Sep 2026). Without
// communes.json the sitemap still answers, as /commune does: the index alone
async function communePaths(): Promise<string[]> {
  try {
    const communes = await getCommunes()
    return ['/commune', ...communes.map((c) => `/commune?code=${c.code}`)]
  } catch (e) {
    if (e instanceof DataError) return ['/commune']
    throw e
  }
}

// /data?city=<city> for the five cities; bare /data (and a stray ?city=) shares Brussels's canonical
// (Q10, Q16), so it is not listed a second time
const dataPaths = CITIES.map((city) => `/data?city=${city}`)

// /atlas?city=<city> for the five cities: every view inside a city (a lens, an object, a sector, an audit)
// canonicalises to its city (A4 of plan 4), so the views are not listed (A5); bare /atlas shares Brussels's canonical
const atlasPaths = CITIES.map((city) => `/atlas?city=${city}`)

// Next's own sitemap XML writer (resolve-route-data.js) drops <loc> and the hreflang href straight
// into the markup with no escaping, so a '&' between query parameters must be escaped here or the
// feed is not well-formed XML. '<' and '>' cannot occur in the addresses this file builds, but they
// are escaped too, on the same principle as JsonLd.tsx: escape what could break the markup, not just
// what happens to be present today.
const xmlEscape = (s: string): string => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const site = siteUrl()
  const paths = [...PAGES, ...atlasPaths, ...(await dossierPaths()), ...(await communePaths()), ...dataPaths]
  return paths.flatMap((p) => PUBLISHED.map((loc) => ({
    url: xmlEscape(site + localePath(loc, p)),
    alternates: { languages: Object.fromEntries(Object.entries(alternates(p, site)).map(([k, v]) => [k, xmlEscape(v)])) },
  })))
}
