/* The lenses of the unified Frondia (docs/07-unified-frondia.md): one map, three questions.
     need   — what a sector lacks: everyday services, shops within reach, summer heat, 3-30-300
     place  — what to place where: City Planner's ranked points, named before anyone placed anything
     change — what actually changed: greenness against twelve matched places
   Numbers come from the city JSON (scripts/site/site_data.py); words from content/en.js.
   A "need" lens maps a sector to a step of the lack ramp: 1…5 (5 = most lacking), 0 (not lacking),
   or null (not measured in this city). */
import type { City, Sector } from './types'

// fields the need lenses read that lib/types.ts leaves in Sector's catch-all: fitq/fit (fit-score
// per scenario), shop (metres to the nearest shop per type), hot (°C above the city median), r3, cs
// (3-30-300 pieces) — typed here, not in lib/types.ts, since only this file reads them
type NeedSector = Sector & {
  fitq?: Record<string, number> | null
  fit?: Record<string, number> | null
  shop?: Record<string, number> | null
  hot?: number | null
  r3?: number | null
  cs?: number | null
}
export interface NeedOpt {
  scenario?: string
  shop?: string
}

export const LACK = ['var(--lack-1)', 'var(--lack-2)', 'var(--lack-3)', 'var(--lack-4)', 'var(--lack-5)']
export const NEED_LENSES = ['services', 'shops', 'heat', 'r3']
export const SCENARIOS = ['family', 'remote', 'senior']
export const SHOP_TYPES = ['bakery', 'cafe', 'confectionery']

// a forest, a port or a rail yard lacks nothing a resident would miss: below this many residents a
// sector is not shaded on a need lens (and says so in the legend)
export const MIN_RESIDENTS = 200

export function needStep(s: NeedSector, lens: string, opt: NeedOpt = {}): number | null {
  if ((s.pop || 0) < MIN_RESIDENTS) return null
  // fifths of the lived-in sectors, not of all (site_data.services_fifths): 1 best served … 5 worst
  if (lens === 'services') return s.fitq?.[opt.scenario || 'family'] ?? null
  if (lens === 'shops') {
    const m = s.shop?.[opt.shop || 'bakery']
    if (m == null) return null
    return m <= 300 ? 0 : m <= 600 ? 1 : m <= 1000 ? 2 : m <= 1500 ? 3 : m <= 2500 ? 4 : 5
  }
  if (lens === 'heat') {
    const h = s.hot
    return h == null ? null : h <= 0 ? 0 : Math.min(5, Math.ceil(h))   // °C above the city median
  }
  if (lens === 'r3') return s.r3 == null ? null : s.r3 === 2 ? 0 : s.r3 === 1 ? 2 : 4
  return null
}

// the value a list sorts by (higher = more lacking) and shows
export function needValue(s: NeedSector, lens: string, opt: NeedOpt = {}): number | null {
  if (lens === 'services') { const v = s.fit?.[opt.scenario || 'family']; return v == null ? null : 100 - v }
  if (lens === 'shops') return s.shop?.[opt.shop || 'bakery'] ?? null
  if (lens === 'heat') return s.hot ?? null
  if (lens === 'r3') return s.r3 == null ? null : 2 - s.r3 + (s.cs != null ? 1 - s.cs : 0)
  return null
}

// few residents: a quiet grey, so it never reads as "lacks nothing" (blank) or as a lack (ramp)
export const needFill = (s: NeedSector, lens: string, opt?: NeedOpt): string | null => {
  if ((s.pop || 0) < MIN_RESIDENTS) return 'var(--noise)'
  const k = needStep(s, lens, opt)
  return k ? LACK[k - 1]! : null
}

export const measuredIn = (city: City, lens: string): boolean =>
  (city.sectors as NeedSector[]).some((s) => needStep(s, lens, {}) != null)
export const fewResidents = (city: City): number =>
  city.sectors.filter((s) => (s.pop || 0) < MIN_RESIDENTS).length

// the sectors that lack most, with at least some residents (a park or a port sector lacks nothing)
export function worst(city: City, lens: string, opt: NeedOpt, n = 8): NeedSector[] {
  return (city.sectors as NeedSector[])
    .filter((s) => needStep(s, lens, opt))
    .sort((a, b) => needValue(b, lens, opt)! - needValue(a, lens, opt)!)
    .slice(0, n)
}
