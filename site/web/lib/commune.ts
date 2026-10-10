import en from '@/messages/en.json'
import fr from '@/messages/fr.json'
import nl from '@/messages/nl.json'
import { DataError, getCommunes } from './data'
import type { Locale } from './format'
import { placeName } from './names'
import type { FinderItem } from './finder'
import type { Commune } from './types'
import { firstParam } from './site'

// Which commune page an address asks for (/commune?code=…). The same outcomes as the Vite page
// (site/apps/landing/src/pages/Commune.jsx), in its order: communes.json cannot be read → `error` (the
// missing message alone); no code → `index` (the finder and every commune by city); a code no commune
// of the five cities has → `missing` (the message and the finder); otherwise `ok`.
export type Search = Record<string, string | string[] | undefined>
export type Resolved =
  | { state: 'ok'; communes: Commune[]; c: Commune; code: string }
  | { state: 'index'; communes: Commune[]; code: '' }
  | { state: 'missing'; communes: Commune[]; code: string }
  | { state: 'error'; code: string }

export async function resolveCommune(q: Search): Promise<Resolved> {
  const code = firstParam(q.code) // and an empty code is no code: it opens the index
  let communes: Commune[]
  try {
    communes = await getCommunes()
  } catch (e) {
    if (e instanceof DataError) return { state: 'error', code }
    throw e
  }
  if (!code) return { state: 'index', communes, code: '' }
  const c = communes.find((x) => x.code === code)
  return c ? { state: 'ok', communes, c, code } : { state: 'missing', communes, code }
}

// the address a commune page is known by
export const communeQuery = (r: Resolved): string => (r.code ? `?code=${encodeURIComponent(r.code)}` : '')

// an unknown code, or the data not there, is a page that explains, not one to be found
export const indexable = (r: Resolved): boolean => r.state === 'ok' || r.state === 'index'

// what the finder needs of each commune, and no more (it travels to the browser): its name and its city in the page's
// language (`city` writes common.cities.<key>), `nis` the code in the page's words (commune.find.nis), since the
// catalogue itself stays on the server; and what a query matches — the commune's English, Dutch and French names, the
// official one, the city's name in every language that has a catalogue, and the code
const CITY_NAMES: Record<string, string[]> = (() => {
  const out: Record<string, string[]> = {}
  for (const m of [en, nl, fr] as { common?: { cities?: Record<string, string> } }[]) {
    for (const [k, v] of Object.entries(m.common?.cities ?? {})) out[k] = [...new Set([...(out[k] ?? []), v])]
  }
  return out
})()
export const finderItems = (cs: Commune[], loc: Locale, nis: (code: string) => string, city: (key: string) => string): FinderItem[] =>
  cs.map((row) => ({
    code: row.code, name: placeName(row, loc), city: city(row.city), nis: nis(row.code),
    find: [...new Set([row.name, row.name_nl, row.name_fr, row.official, ...(CITY_NAMES[row.city] ?? []), row.code])].filter(Boolean).join(' '),
  }))
