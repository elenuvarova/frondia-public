import type { Locale } from '@/i18n/locales'
import { CITIES, cityOf, type CityKey } from './cities'
import { DataError, getCity, getDownloads } from './data'
import { temporalCoverage } from './downloads'
import type { DownloadsCity } from './types'
import { firstParam } from './site'

// Which data page an address asks for (/data?city=…). The Vite page (site/apps/landing/src/pages/
// Data.jsx) read the city with URLSearchParams.get and cityOf: the first value of a repeated
// parameter, and anything that is not one of the five keys — absent, empty, misspelled — opens
// Brussels. So does this, and never an error page: downloads.json missing is the old page's one line
// (its "Loading…" that never ended), still 200 and not indexed. The address a page is known by always
// names its city (?city=brussels for a bare /data). A city the address names but the site doesn't have
// is Brussels's page under Brussels's canonical, indexable like the dossier's stray ?city= (ruling Q16:
// noindex with a canonical elsewhere is a mixed signal) — but it carries no Dataset of its own.
export type Search = Record<string, string | string[] | undefined>
export type Resolved =
  | { state: 'ok'; city: CityKey; given: string; d: DownloadsCity; temporal: string | null }
  | { state: 'error'; city: CityKey; given: string }

export async function resolveData(q: Search, loc: Locale): Promise<Resolved> {
  const given = firstParam(q.city)
  const city = cityOf(given)
  let d: DownloadsCity | undefined
  try {
    d = (await getDownloads(loc))[city]
  } catch (e) {
    if (e instanceof DataError) return { state: 'error', city, given }
    throw e
  }
  if (!d) return { state: 'error', city, given }
  // the dataset's time span, from the city's own data: the trend's windows and the latest season
  // measured since the 2024 base. Without the city file the span is simply left out.
  const c = await getCity(city).catch(() => null)
  // city.json writes the season as a string ("2026")
  const latest = c?.balance?.latest
  const season = latest && /^\d{4}$/.test(latest) ? Number(latest) : null
  return { state: 'ok', city, given, d, temporal: temporalCoverage(c?.window, season) }
}

export const dataQuery = (r: Resolved): string => `?city=${r.city}`

// the page is there to be found when its data is; a stray ?city= too, under Brussels's canonical
export const indexable = (r: Resolved): boolean => r.state === 'ok'

// the schema.org Dataset only on a real city's view (or the bare address, which is Brussels's under
// its own canonical), not on a stray ?city= shown as the default: one Dataset per city, not a duplicate
export const hasDataset = (r: Resolved): r is Extract<Resolved, { state: 'ok' }> =>
  r.state === 'ok' && (r.given === '' || (CITIES as readonly string[]).includes(r.given))
