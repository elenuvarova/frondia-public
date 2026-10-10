// The atlas's address, read and written as the old atlas did (site/apps/atlas/src/pages/Atlas.jsx:869–887 reads it,
// 960–976 writes it). Pure: the server reads it for the header, the client for the first view.
// One intended difference: the old atlas looked city and object up in plain objects, so a prototype name
// (`city=constructor`, `obj=toString`) passed as known; here only the real keys do (F16).
import { cityOf, type CityKey } from '@/lib/cities'
import type { Locale } from '@/lib/format'
import { NEED_LENSES, SCENARIOS, SHOP_TYPES, measuredIn } from '@/lib/lenses'
import type { City } from '@/lib/types'
import { localePath } from '@/i18n/locales'

export const QUESTIONS = ['need', 'place', 'change'] as const
export type Question = (typeof QUESTIONS)[number]
export const VIEWS = ['change', 'communes', 'field', 'photos'] as const
export type View = (typeof VIEWS)[number]
export const OBJECT_KEYS = ['benches', 'bicycle_repair', 'bike_parking', 'defibrillators', 'dog_areas', 'drinking_water',
  'fitness_stations', 'picnic_tables', 'playgrounds', 'public_bookcases', 'recycling', 'shelters', 'toilets', 'waste_bins'] as const

export interface AtlasState {
  city: CityKey; q: Question; lens: string | null; scenario: string; shop: string; obj: string; n: number
  view: View; m: 'green' | 'built'; caseSlug: string | null; sector: string | null
}
export type RawQuery = Record<string, string | string[] | undefined>

// Next's searchParams object → URLSearchParams: every value of a key, in order, so get() is the first, as in the browser
export function toParams(q: RawQuery): URLSearchParams {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(q)) {
    if (v === undefined) continue
    for (const x of Array.isArray(v) ? v : [v]) p.append(k, x)
  }
  return p
}

const among = (list: readonly string[], v: string | null): v is string => v !== null && list.includes(v)

export function parseAtlas(p: URLSearchParams): AtlasState {
  const get = (k: string) => p.get(k)
  const raw = get('n'), v = Number(raw)
  const q = get('q'), lens = get('lens'), scenario = get('for'), shop = get('shop'), obj = get('obj'), view = get('view')
  return {
    city: cityOf(get('city')),
    q: among(QUESTIONS, q) ? (q as Question) : 'change',
    lens: among(NEED_LENSES, lens) ? lens : null,
    scenario: among(SCENARIOS, scenario) ? scenario : 'family',
    shop: among(SHOP_TYPES, shop) ? shop : 'bakery',
    obj: among(OBJECT_KEYS, obj) ? obj : 'toilets',
    // Number('') is 0: an empty n= is 0, as before; a missing one is the default ten
    n: raw !== null && Number.isInteger(v) && v >= 0 && v <= 40 ? v : 10,
    view: among(['communes', 'field', 'photos'], view) ? (view as View) : 'change',
    m: get('m') === 'built' ? 'built' : 'green',
    caseSlug: get('case') || null,
    sector: get('sector') || null,
  }
}

// only what differs from the defaults; an open audit wins over an open sector
export function atlasQuery(v: AtlasState & { lens: string }): string {
  const p = new URLSearchParams({ city: v.city })
  if (v.q !== 'change') p.set('q', v.q)
  if (v.q === 'need') {
    p.set('lens', v.lens)
    if (v.lens === 'services' && v.scenario !== 'family') p.set('for', v.scenario)
    if (v.lens === 'shops' && v.shop !== 'bakery') p.set('shop', v.shop)
  }
  if (v.q === 'place') { p.set('obj', v.obj); if (v.n !== 10) p.set('n', String(v.n)) }
  if (v.q === 'change' && v.view !== 'change') p.set('view', v.view)
  if (v.q === 'change' && v.view === 'change' && v.m === 'built') p.set('m', 'built')
  if (v.caseSlug) p.set('case', v.caseSlug)
  else if (v.sector) p.set('sector', v.sector)
  return `?${p}`
}

export const atlasPath = (loc: Locale, v: AtlasState & { lens: string }): string => localePath(loc, '/atlas') + atlasQuery(v)

// until one is chosen, the first need lens this city measures
export const firstMeasured = (city: City): string => NEED_LENSES.find((k) => measuredIn(city, k)) || 'heat'
