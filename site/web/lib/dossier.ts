import { cityOf, type CityKey } from './cities'
import { localePath } from '@/i18n/locales'
import { DataError, getCity } from './data'
import type { Locale } from './format'
import type { City, Sector } from './types'
import { firstParam } from './site'

// Which dossier an address asks for (/dossier?city=…&sector=…). The same four outcomes as the Vite
// page (site/apps/landing/src/pages/Dossier.jsx), in its order: no city file → `error` (the missing
// message, no link); a city where the open rule picks nothing and the address names no sector →
// `noPick` (Liège, Charleroi: exempt under Article 8(1)); a sector outside the measured part →
// `missing` (with a link to the atlas); otherwise `ok`. Without ?sector= the rule's first pick opens.
export type Search = Record<string, string | string[] | undefined>
export type Resolved =
  | { state: 'ok'; cityKey: CityKey; city: City; s: Sector }
  | { state: 'noPick'; cityKey: CityKey; city: City; sector: string }
  | { state: 'missing'; cityKey: CityKey; city: City; sector: string }
  | { state: 'error'; cityKey: CityKey; sector: string }

export async function resolveDossier(q: Search): Promise<Resolved> {
  const cityKey = cityOf(firstParam(q.city))
  const sector = firstParam(q.sector)
  let city: City
  try {
    city = await getCity(cityKey)
  } catch (e) {
    if (e instanceof DataError) return { state: 'error', cityKey, sector }
    throw e
  }
  const id = sector || city.dossier.pick.ids[0]
  const s = city.sectors.find((x) => x.id === id)
  if (s && s.t24 != null) return { state: 'ok', cityKey, city, s }
  return !sector && !city.dossier.pick.n ? { state: 'noPick', cityKey, city, sector } : { state: 'missing', cityKey, city, sector }
}

// the address a dossier is known by: its city and, once there is one, its sector
export function dossierQuery(r: Resolved): string {
  const sector = r.state === 'ok' ? r.s.id : r.sector
  return `?city=${r.cityKey}${sector ? `&sector=${encodeURIComponent(sector)}` : ''}`
}

// the address the printed sheet and the colophon carry: the site's host (SITE_URL, never the
// request's), the page in its language, the city and the sector — as text, not a link
export const dossierAddress = (site: string, loc: Locale, city: CityKey, id: string): string =>
  `${new URL(site).host}${localePath(loc, '/dossier')}?city=${city}&sector=${id}`

// a wrong sector or a city without its data is a page that explains, not one to be found; so is a
// city whose rule picks nothing (Liège, Charleroi): one sentence and a link, no dossier (ruling Q17 —
// noindex, its links still followed)
export const indexable = (r: Resolved): boolean => r.state === 'ok'
