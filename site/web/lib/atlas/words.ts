// The atlas's sentences that are built from parts: which message, which branch, which numbers. Each is a pure
// function of a translator for the `atlas` section (no tie — the component ties what it renders) and the data,
// ported from site/apps/atlas/src/pages/Atlas.jsx (km, needLabel, EQUITY_FMT, equityReading, Equity's cut and
// pts) and from the functions of site/packages/shared/content/en.js (COMMUNES.unstable, PLACE.register,
// MORE.who/whoOne, REGISTERED.none, NEED.heat.lede). tests/atlas-words.test.ts checks every one against the old
// functions on the data of all five cities. Every other atlas word is read from the catalogue by key.
import { dec, fixed, pct, signed, type Locale } from '@/lib/format'
import { NB } from '@/lib/typography'
import { count, type TValues } from '@/lib/icu'
import type { AtlasCommune, EquityRow, PointOfficial } from './types'

export type Tr = (key: string, values?: TValues) => string

// a unit keeps to its number: the first "value + space" in the formatted text gets a no-break space, wherever the
// language puts the unit ("+1,2 °C", "environ 3 ha"); it works on the value that was put in, never on a
// translated unit, so no language's spelling of "°C" or "ha" is assumed. The value must stand on its own: not the
// tail of a longer number ("15 and 5 ha" glues the 5, not the end of 15)
const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
export function glue(text: string, v: string): string {
  return text.replace(new RegExp(`(^|[^0-9.,])${escape(v)} `), (_, before: string) => `${before}${v}${NB}`)
}

// metres as the data has them (the old code printed the raw number), kilometres with one decimal
export const km = (tr: Tr, m: number | null | undefined, loc: Locale): string =>
  m == null ? '—' : m < 1000 ? tr('units.m', { v: dec(m, loc, 3) }) : tr('units.km', { v: fixed(m / 1000, 1, loc) })

// what a list row shows for a need lens (Atlas.jsx needLabel)
export interface NeedSector { fit?: Record<string, number | null> | null; shop?: Record<string, number | null> | null; hot?: number | null; cs?: number | null }
export interface NeedOpt { scenario: string; shop: string }
export function needLabel(tr: Tr, s: NeedSector, lens: string, opt: NeedOpt, loc: Locale): string {
  if (lens === 'services') { const v = s.fit?.[opt.scenario]; return tr('units.score', { v: v == null ? '—' : dec(v, loc, 3) }) }
  if (lens === 'shops') return km(tr, s.shop?.[opt.shop], loc)
  if (lens === 'heat') return tr('units.c', { v: signed(s.hot, 1, loc) })
  if (lens === 'r3') return tr('need.canopy', { v: pct(s.cs, 0, loc) })
  return ''
}

const MORE_IS_WORSE: Record<string, boolean> = { services: false, shops: true, heat: true, r3: true }
export const GAP_PTS = 2   // a group is named in the reading from 2 points of difference with all residents

// the bars keep the degree with its number (Atlas.jsx's EQUITY_FMT used a no-break space here, and only here)
const heatValue = (tr: Tr, v: number, loc: Locale) => { const s = signed(v, 1, loc); return glue(tr('units.c', { v: s }), s) }

function fmt(tr: Tr, lens: string, v: number, loc: Locale): string {
  if (lens === 'services') return tr('units.score', { v: String(Math.round(v)) })
  if (lens === 'shops') return km(tr, Math.round(v / 10) * 10, loc)
  if (lens === 'heat') return heatValue(tr, v, loc)
  return pct(v, 0, loc)
}
export const equityFormat = fmt

// hectares as Atlas.jsx's HA() and BALANCE.split arguments set them: one decimal, the sign from the value itself (so
// +0.04 reads "+0.0 ha"), a real minus, and a no-break space before "ha"; `sign: false` for the lost/gained split
export function haValue(tr: Tr, v: number, loc: Locale, sign = true): string {
  const s = (sign ? (v > 0 ? '+' : v < 0 ? '−' : '') : '') + fixed(Math.abs(v), 1, loc)
  return glue(tr('units.ha', { v: s }), s)
}

// the poorest third against the richest, then who lives in the worst-off group against all residents
export function equityReading(tr: Tr, lens: string, o: string, e: EquityRow, loc: Locale): string {
  const [p, , r] = e.thirds
  const worse = MORE_IS_WORSE[lens] ? p > r : p < r
  const income = tr(`equity.reading.${lens}`, { worse: worse ? 'yes' : 'no', p: fmt(tr, lens, p, loc), r: fmt(tr, lens, r, loc), o })
  const group = tr(`equity.group.${lens}`)
  const d = { kid: e.kid - e.all, old: e.old - e.all }
  const named = (['kid', 'old'] as const).filter((k) => Math.abs(d[k]) * 100 >= GAP_PTS)
  let ages: string
  if (!named.length) ages = tr('equity.ages.none', { group })
  else if (named.length === 1) {
    const k = named[0]!
    ages = tr('equity.ages.one', { who: k, more: d[k] > 0 ? 'yes' : 'no', group, x: pct(e[k], 0, loc), all: pct(e.all, 0, loc) })
  } else if ((d.kid > 0) !== (d.old > 0)) {
    const [m, l] = d.kid > 0 ? (['kid', 'old'] as const) : (['old', 'kid'] as const)
    ages = tr('equity.ages.split', { more: m, group, x: pct(e[m], 0, loc), y: pct(e[l], 0, loc), all: pct(e.all, 0, loc) })
  } else ages = tr('equity.ages.both', { more: d.kid > 0 ? 'yes' : 'no', group, x: pct(e.kid, 0, loc), y: pct(e.old, 0, loc), all: pct(e.all, 0, loc) })
  return `${income} ${ages}`
}

// the income cut that bounds the worst-off group, in the lens's terms; none for 3-30-300
export function equityCut(tr: Tr, lens: string, e: EquityRow, loc: Locale): string | null {
  if (e.cut == null || lens === 'r3') return null
  const v = lens === 'heat' ? heatValue(tr, e.cut, loc) : lens === 'shops' ? km(tr, Math.round(e.cut / 10) * 10, loc) : dec(e.cut, loc, 3)
  return tr(`equity.cut.${lens}`, { v })
}

// an age row against all residents, in points: "+3 pts", "−1 pt"
export function pts(tr: Tr, v: number, all: number, loc: Locale): string {
  const n = Math.round((v - all) * 100)
  return tr('equity.pts', { n: signed(n, 0, loc), abs: count(Math.abs(n)) })
}

// a commune whose verdict turns over under another reading of Article 3(20)
// `name` is the commune's, in the page's language (lib/names.ts placeName)
export function unstableLine(tr: Tr, c: AtlasCommune, name: string, loc: Locale): string {
  const values = {
    name,
    pts: fixed(100 * Math.abs(0.45 - (c.green as number)), 1, loc),
    g7: pct(c.green7, 1, loc),
    gnw: pct(c.green_nw, 1, loc),
  }
  if (!c.exempt && (c.green7 as number) > 0.45) return tr('communes.unstable.farmland', values)
  if (c.exempt && (c.green_nw as number) <= 0.45) return tr('communes.unstable.water', values)
  return tr('communes.unstable.other', { name })
}

// the city's own register at the named points: what already stands there, what the map lacked, and a caution
// when one group sits in such gaps 20 points more often (the rule written into the check on 27 Sep 2026). The
// object comes with its own article (`a`, common.objects.a: "an outdoor fitness station") and its own negation
// (`no`, common.objects.no: "no bench"), since an article agrees with its noun in Dutch and French
export function placeRegister(tr: Tr, o: PointOfficial, a: string, no: string): string {
  const parts: string[] = [
    o.named.at || o.control.at
      ? tr('place.register.at', { a, named: String(o.named.at), control: String(o.control.at) })
      : tr('place.register.none', { no }),
  ]
  if (o.named.gap != null) {
    const cg = o.control.gap as number
    parts.push(tr('place.register.gap', { named: String(o.named.gap), namedN: String(o.named.n), control: String(cg), controlN: String(o.control.n) }))
    const namedShare = o.named.gap / o.named.n, controlShare = cg / o.control.n
    if (Math.abs(namedShare - controlShare) >= 0.2) parts.push(tr('place.register.caution', { group: namedShare > controlShare ? 'named' : 'control' }))
  }
  return parts.filter(Boolean).join(' ')
}

// under "What if N more?": how many of the first k stand where the poorest third lives
export function moreWho(tr: Tr, k: number, poor: number, cut: string): string {
  if (k === 0) return tr('more.zero')
  if (k === 1) return tr('more.whoOne', { poor: poor > 0 ? 'yes' : 'no', cut })
  return tr('more.who', { k: String(k), poor: count(poor), cut })
}

// why a city has no record registered before the works
const NONE_KEYS = new Set(['antwerp', 'liege', 'charleroi'])
export function registeredNone(tr: Tr, city: string, name: string): string {
  return NONE_KEYS.has(city) ? tr(`registered.none.${city}`) : tr('registered.none.other', { city: name })
}

// the heat lens's lede: the city's own correlation of heat and canopy, with a real minus and two decimals,
// as the dossier prints it (re-check 3: Liège's read "r = −0.8" here and "r = −0.80" in its dossier); the city's
// name is the page language's (common.cities), not the data's
export function heatLede(tr: Tr, cityName: string, r: number, loc: Locale): string {
  return tr('need.lenses.heat.lede', { city: cityName, r: fixed(r, 2, loc) })
}

// the map tip on "what changed": the sector's value, or, where it has none, the words the need lenses' tip
// uses, never "effect —" (re-check 3: 38 Brussels sectors outside the measured part read "effect —")
export function changeTip(tr: Tr, kind: 'effect' | 'raw' | 'built', v: number | null | undefined, loc: Locale): string {
  return v == null ? tr('tip.notMeasured') : tr(`tip.${kind}`, { v: signed(v, 3, loc) })
}
