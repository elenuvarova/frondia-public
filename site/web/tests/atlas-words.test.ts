import fs from 'node:fs'
import path from 'node:path'
import { createTranslator } from 'next-intl'
import { expect, test } from 'vitest'
import en from '@/messages/en.json'
import { CITIES } from '@/lib/cities'
import { getCity, getPoints } from '@/lib/data'
import { fixed, pct, signed } from '@/lib/format'
import type { AtlasCity, AtlasPoints, EquityRow } from '@/lib/atlas/types'
import { changeTip, equityCut, equityReading, glue, haValue, heatLede, km, moreWho, needLabel, placeRegister, pts, registeredNone, unstableLine } from '@/lib/atlas/words'
// @ts-expect-error — the old site's words (plain JS, kept from tag vite-apps-final): the oracle these messages must reproduce
import { COMMUNES, EQUITY, MORE, NEED, NOT_MEASURED, OBJECT_ONE, PLACE, QUESTIONS, REGISTERED, BALANCE, CHECK, PHOTOS, BUILT, SCENARIO_LABEL, SERVICE_LABEL, SHOP_LABEL } from './oracle/old-en.js'

const t = createTranslator({ locale: 'en', messages: en, namespace: 'atlas', onError: (e) => { throw e } })
const tr = (k: string, v?: Record<string, string | number>) => t(k as never, v as never)
const kmOld = (m: number | null | undefined) => (m == null ? '—' : m < 1000 ? `${m} m` : `${(m / 1000).toFixed(1)} km`)

// Atlas.jsx's own composition (lines 298–331), the oracle for equityReading
const EQUITY_FMT: Record<string, (v: number) => string> = {
  services: (v) => `${Math.round(v)}/100`, shops: (v) => kmOld(Math.round(v / 10) * 10),
  heat: (v) => `${signed(v, 1, 'en')} °C`, r3: (v) => pct(v, 0, 'en'),
}
const MORE_IS_WORSE: Record<string, boolean> = { services: false, shops: true, heat: true, r3: true }
function oldReading(lens: string, o: string, e: { thirds: number[]; all: number; kid: number; old: number }): string {
  const f = EQUITY_FMT[lens]!
  const [p, , r] = e.thirds as [number, number, number]
  const worse = MORE_IS_WORSE[lens] ? p > r : p < r
  const income = EQUITY.reading[lens](worse, f(p), f(r), o)
  const g = EQUITY.group[lens]
  const d: Record<string, number> = { kid: e.kid - e.all, old: e.old - e.all }
  const named = ['kid', 'old'].filter((k) => Math.abs(d[k]!) * 100 >= 2)
  const noun: Record<string, string> = { kid: EQUITY.kidNoun, old: EQUITY.oldNoun }
  let ages: string
  if (!named.length) ages = EQUITY.ages.none(g)
  else if (named.length === 1) ages = EQUITY.ages.one(noun[named[0]!], d[named[0]!]! > 0, g, pct((e as never)[named[0]!], 0, 'en'), pct(e.all, 0, 'en'))
  else if ((d.kid! > 0) !== (d.old! > 0)) {
    const [m, l] = d.kid! > 0 ? ['kid', 'old'] : ['old', 'kid']
    ages = EQUITY.ages.split(noun[m!], noun[l!], g, pct((e as never)[m!], 0, 'en'), pct((e as never)[l!], 0, 'en'), pct(e.all, 0, 'en'))
  } else ages = EQUITY.ages.both(d.kid! > 0, g, pct(e.kid, 0, 'en'), pct(e.old, 0, 'en'), pct(e.all, 0, 'en'))
  return `${income} ${ages}`
}

test.each(CITIES)('%s: every "who is short" reading equals the old site’s', async (key) => {
  const c = (await getCity(key)) as AtlasCity
  const cases: [string, string][] = [
    ...['family', 'remote', 'senior'].map((o) => ['services', o] as [string, string]),
    ...['bakery', 'cafe', 'confectionery'].map((o) => ['shops', o] as [string, string]),
    ['heat', '_'], ['r3', '_'],
  ]
  let n = 0
  for (const [lens, o] of cases) {
    const e = (c.equity as unknown as Record<string, Record<string, EquityRow> | undefined>)[lens]?.[o]
    if (!e) continue
    n++
    expect(equityReading(tr, lens, o, e, 'en')).toBe(oldReading(lens, o, e))
    const cut = e.cut == null ? null : EQUITY.cut[lens](lens === 'heat' ? `${signed(e.cut, 1, 'en')} °C` : lens === 'shops' ? kmOld(Math.round(e.cut / 10) * 10) : e.cut)
    expect(equityCut(tr, lens, e, 'en')).toBe(cut)
  }
  expect(n).toBeGreaterThan(0)
})

// Every branch of the reading, whatever today's data happens to reach: both directions of the income gap for each
// lens and option, and every age branch (none, one for each group either way, split both ways, both either way), with
// differences on both sides of the 2-point boundary
test('every branch of the "who is short" reading equals the old site’s, on synthetic rows', () => {
  const BASE: Record<string, [number, number, number]> = {
    services: [55, 62, 71], shops: [420, 610, 1530], heat: [-0.4, 0.6, 1.8], r3: [0.12, 0.2, 0.31],
  }
  const cases: [string, string][] = [
    ...['family', 'remote', 'senior'].map((o) => ['services', o] as [string, string]),
    ...['bakery', 'cafe', 'confectionery'].map((o) => ['shops', o] as [string, string]),
    ['heat', '_'], ['r3', '_'],
  ]
  const D = [0, 0.019, 0.02, 0.05, -0.019, -0.02, -0.05]
  const all = 0.2
  const seen = new Set<string>()
  for (const [lens, o] of cases) {
    for (const thirds of [BASE[lens]!, [...BASE[lens]!].reverse() as [number, number, number]]) {
      for (const dk of D) for (const dold of D) {
        const e: EquityRow = { thirds, all, kid: all + dk, old: all + dold, cut: null }
        const got = equityReading(tr, lens, o, e, 'en')
        expect(got, `${lens} ${o} ${thirds} ${dk} ${dold}`).toBe(oldReading(lens, o, e))
        seen.add(got.split(':')[0]!)
        seen.add(got.split('. ')[1]!.split(':')[0]!.replace(/ in .*? (more|less|about)/, ' in G $1'))
      }
    }
  }
  // the reading's own words, each reached: both directions of every lens, and every shape of the ages sentence
  for (const s of [
    'The poorest third is less well served than the richest', 'The poorest third is better served than the richest',
    'The poorest third lives farther from a bakery than the richest', 'The poorest third lives closer to a café than the richest',
    'The poorest third is hotter than the richest', 'The poorest third is cooler than the richest',
    'The poorest third misses both parts more often than the richest', 'The poorest third misses both parts less often than the richest',
    'Children live in G more often than residents overall', 'Children live in G less often than residents overall',
    'People aged 65 and over live in G more often than residents overall', 'People aged 65 and over live in G less often than residents overall',
    'Children live in G more often than residents overall, people aged 65 and over less often',
    'People aged 65 and over live in G more often than residents overall, children less often',
    'Children and people aged 65 and over both live in G more often than residents overall',
    'Children and people aged 65 and over both live in G less often than residents overall',
  ]) expect(seen, s).toContain(s)
  expect([...seen].some((s) => s.startsWith('Children and people aged 65 and over live in G about'))).toBe(true)
})

test.each(CITIES)('%s: the commune lines, the registered lines, the heat lede and the register sentences equal the old site’s', async (key) => {
  const c = (await getCity(key)) as AtlasCity
  for (const x of c.communes.list.filter((y) => y.stable === false)) {
    expect(unstableLine(tr, x, x.name, 'en')).toBe(COMMUNES.unstable(x, fixed(100 * Math.abs(0.45 - (x.green as number)), 1, 'en'), pct(x.green7, 1, 'en'), pct(x.green_nw, 1, 'en')))
  }
  if (!c.registered.length) expect(registeredNone(tr, key, c.name)).toBe(REGISTERED.none(key, c.name))
  // one difference from the old site, on purpose (re-check 3): r keeps two decimals, as the dossier prints it (Liège −0.8 → −0.80)
  const lede = heatLede(tr, en.common.cities[key], c.heat_canopy_r, 'en')
  expect(lede).toBe(NEED.heat.lede({ ...c, heat_canopy_r: fixed(c.heat_canopy_r, 2, 'en').replace('−', '-') }))
  expect(lede).toMatch(/r = −0\.\d\d\.$/)
  const p = (await getPoints(key)) as AtlasPoints
  for (const ty of p.types.filter((x) => x.official)) {
    const kind = OBJECT_ONE[ty.key].toLowerCase()
    const k = ty.key as keyof typeof en.common.objects.a
    expect(placeRegister(tr, ty.official!, en.common.objects.a[k], en.common.objects.no[k])).toBe(PLACE.register(ty.official, kind))
  }
})

test('the small sentences: what-if, km, the plain messages that took arguments', () => {
  expect(moreWho(tr, 0, 0, '€20,000')).toBe(MORE.zero)
  expect(moreWho(tr, 1, 1, '€20,000')).toBe(MORE.whoOne(true, '€20,000'))
  expect(moreWho(tr, 1, 0, '€20,000')).toBe(MORE.whoOne(false, '€20,000'))
  expect(moreWho(tr, 12, 5, '€20,000')).toBe(MORE.who(12, 5, '€20,000'))
  // the old site's one slip, fixed (re-check 3): "Of these 10, 1 stand where…" (Ghent's benches)
  expect(moreWho(tr, 10, 1, '€27,536')).toBe('Of these 10, 1 stands where the poorest third of residents live (sector median income below €27,536).')
  expect(moreWho(tr, 10, 0, '€27,536')).toContain('Of these 10, 0 stand where')
  for (const m of [null, 120, 999, 1000, 1549, 23456]) expect(km(tr, m, 'en')).toBe(kmOld(m))
  expect(tr('communes.region', { n: 19, g: '39.3%' })).toBe(COMMUNES.region(19, '39.3%'))
  expect(tr('balance.raw', { city: 'Brussels', s: '2026', g: '+1.2 ha', b: '−3.4 ha' })).toBe(BALANCE.raw('Brussels', '2026', '+1.2 ha', '−3.4 ha'))
  // re-check 1 (9 Oct 2026): the old site's sentence (oracle CHECK) put the first rate's condition the wrong way round —
  // 98 of 100 is the satellite agreeing where the aerial map sees no change, not the other way — so it departs here
  {
    // the order of the conditions, not a copy of the catalogue: the first rate is the satellite agreeing where the aerial
    // map sees no change (specificity), the second the aerial map agreeing where the satellite says it changed
    const s = tr('change.check', { sk: 98, sn: 100, ck: 32, cn: 100 })
    expect(s.indexOf('the aerial map sees no change')).toBeGreaterThan(-1)
    expect(s.indexOf('the aerial map sees no change')).toBeLessThan(s.indexOf('98 of 100'))
    expect(s.indexOf('this map says a sector changed')).toBeLessThan(s.indexOf('32 of 100'))
    expect(s.indexOf('98 of 100')).toBeLessThan(s.indexOf('this map says a sector changed'))
  }
  expect(tr('photos.valueText', { p: 40, a: 2017, b: 2024 })).toBe(PHOTOS.valueText(40, 2017, 2024))
  expect(tr('built.threshold', { thr: '0.025', n: '686', city: 'Brussels' })).toBe(BUILT.threshold('0.025', '686', 'Brussels'))
  expect(tr('registered.lede', { n: 2, city: 'ghent', date: '27 September 2026' })).toBe(REGISTERED.lede(2, '27 September 2026', REGISTERED.source.ghent))
})

test('every atlas message formats with every argument it names (no ICU error)', () => {
  const leaves = (o: unknown, p = ''): [string, unknown][] =>
    o && typeof o === 'object' && !Array.isArray(o) ? Object.entries(o).flatMap(([k, v]) => leaves(v, p ? `${p}.${k}` : k)) : [[p, o]]
  for (const [k, v] of leaves(en.atlas)) {
    if (typeof v !== 'string') continue
    // every {name} and {name, plural|select, …} the message mentions, nested branches too: plural gets a number,
    // select any string (its `other` branch), tags a pass-through
    const vals: Record<string, unknown> = { b: (c: string) => c, em: (c: string) => c }
    for (const m of v.matchAll(/\{\s*(\w+)\s*(?:,\s*(\w+))?/g)) vals[m[1]!] = m[2] === 'plural' ? 2 : 'x'
    expect(() => t.markup(k as never, vals as never), k).not.toThrow()
  }
})

// Atlas.jsx's needLabel (lines 154–160) and Equity's pts (line 330), the oracles for the list rows and the age rows
function oldNeedLabel(s: Record<string, any>, lens: string, opt: { scenario: string; shop: string }): string {
  if (lens === 'services') return `${s.fit?.[opt.scenario]}/100`
  if (lens === 'shops') return kmOld(s.shop?.[opt.shop])
  if (lens === 'heat') return `${signed(s.hot, 1, 'en')} °C`
  if (lens === 'r3') return `${pct(s.cs, 0, 'en')} canopy`
  return ''
}
const oldPts = (v: number, all: number) => { const n = Math.round((v - all) * 100); return `${signed(n, 0, 'en')} ${Math.abs(n) === 1 ? 'pt' : 'pts'}` }

test.each(CITIES)('%s: every sector’s list label and every age row equal the old site’s', async (key) => {
  const c = (await getCity(key)) as AtlasCity
  let n = 0
  for (const s of c.sectors as unknown as Record<string, any>[]) {
    for (const scenario of ['family', 'remote', 'senior']) {
      if (s.fit?.[scenario] == null) continue
      n++
      expect(needLabel(tr, s, 'services', { scenario, shop: 'bakery' }, 'en')).toBe(oldNeedLabel(s, 'services', { scenario, shop: 'bakery' }))
    }
    for (const shop of ['bakery', 'cafe', 'confectionery']) {
      expect(needLabel(tr, s, 'shops', { scenario: 'family', shop }, 'en')).toBe(oldNeedLabel(s, 'shops', { scenario: 'family', shop }))
    }
    if (s.hot != null) expect(needLabel(tr, s, 'heat', { scenario: 'family', shop: 'bakery' }, 'en')).toBe(oldNeedLabel(s, 'heat', { scenario: 'family', shop: 'bakery' }))
    if (s.cs != null) expect(needLabel(tr, s, 'r3', { scenario: 'family', shop: 'bakery' }, 'en')).toBe(oldNeedLabel(s, 'r3', { scenario: 'family', shop: 'bakery' }))
    expect(needLabel(tr, s, 'junk', { scenario: 'family', shop: 'bakery' }, 'en')).toBe('')
  }
  expect(n).toBeGreaterThan(0)
  for (const lens of ['services', 'shops', 'heat', 'r3']) {
    for (const e of Object.values((c.equity as unknown as Record<string, Record<string, EquityRow> | undefined>)[lens] ?? {})) {
      for (const v of [...e.thirds, e.kid, e.old, e.all]) expect(pts(tr, v, e.all, 'en')).toBe(oldPts(v, e.all))
    }
  }
  for (const [v, all] of [[0.31, 0.3], [0.29, 0.3], [0.3, 0.3], [0.35, 0.3]] as const) expect(pts(tr, v, all, 'en')).toBe(oldPts(v, all))
})

test('the branches no city’s data reaches today equal the old site’s too', () => {
  // a commune whose verdict turns some other way; a city without a dictionary line for its missing records
  const odd = { code: 'x', name: 'Ghent', d: '', x: 0, y: 0, green: 0.5, exempt: true, green7: 0.52, green_nw: 0.47, stable: false }
  expect(unstableLine(tr, odd, odd.name, 'en')).toBe(COMMUNES.unstable(odd, fixed(100 * Math.abs(0.45 - odd.green), 1, 'en'), pct(odd.green7, 1, 'en'), pct(odd.green_nw, 1, 'en')))
  for (const k of ['brussels', 'ghent']) expect(registeredNone(tr, k, k === 'ghent' ? 'Ghent' : 'Brussels')).toBe(REGISTERED.none(k, k === 'ghent' ? 'Ghent' : 'Brussels'))
  // a register with nothing standing, no gap, and a gap the named points lead by exactly the rule's 20 points
  const o = (na: number, ca: number, ng: number | null, cg: number | null) => ({ date: '2026-09-27', named: { at: na, gap: ng, n: 10 }, control: { at: ca, gap: cg, n: 10 } })
  for (const x of [o(0, 0, null, null), o(0, 2, null, null), o(1, 0, 3, 1), o(0, 0, 1, 5), o(0, 0, 2, 2)]) {
    for (const [k, kind] of [['fitness_stations', 'outdoor fitness station'], ['benches', 'bench']] as const) {
      expect(placeRegister(tr, x, en.common.objects.a[k], en.common.objects.no[k])).toBe(PLACE.register(x, kind))
    }
  }
  // the lede for every city's source, and a city that has none
  expect(tr('registered.lede', { n: 6, city: 'brussels', date: '5 September 2026' })).toBe(REGISTERED.lede(6, '5 September 2026', REGISTERED.source.brussels))
  expect(tr('registered.lede', { n: 1, city: 'liege', date: '5 September 2026' })).toBe(REGISTERED.lede(1, '5 September 2026', 'projects'))
})

// Every word the catalogue copied rather than wrote: the keys taken from en.js equal en.js (objects and arrays whole),
// the messages that were en.js functions give the same sentence, and every other fixed label is a literal of
// Atlas.jsx, so a changed word fails here rather than on the page
test('the copied labels equal en.js, and every other fixed label is the old atlas’s own literal', () => {
  const a = en.atlas as unknown as Record<string, any>
  const at = (k: string) => k.split('.').reduce<any>((n, x) => n?.[x], a)
  const { lede: _l, ...heatRest } = NEED.heat
  const FROM_EN: [string, unknown][] = [
    ['q', QUESTIONS],
    ['need.lenses.services', NEED.services], ['need.lenses.shops', NEED.shops], ['need.lenses.r3', NEED.r3],
    ['need.scenario', SCENARIO_LABEL], ['need.shop', SHOP_LABEL], ['need.service', SERVICE_LABEL],
    ['equity.title', EQUITY.title], ['equity.thirds', EQUITY.thirds], ['equity.all', EQUITY.all], ['equity.kid', EQUITY.kid],
    ['equity.old', EQUITY.old], ['equity.vs', EQUITY.vs], ['equity.byIncome.heat', EQUITY.byIncome.heat()],
    ['equity.byIncome.r3', EQUITY.byIncome.r3()], ['equity.group', EQUITY.group],
    ['place.legend', PLACE.legend], ['place.lede', PLACE.lede], ['place.source', PLACE.source], ['place.limit', PLACE.limit],
    ['place.mapped', PLACE.mapped],
    ['more.slider', MORE.slider], ['more.read', MORE.read], ['more.today', MORE.today], ['more.named', MORE.named], ['more.zero', MORE.zero],
    ['photos.legend', PHOTOS.legend], ['change.views.photos', PHOTOS.chip], ['change.views.communes', COMMUNES.chip],
    ['built.lede', BUILT.lede], ['built.counts', BUILT.counts], ['built.legend', BUILT.legend], ['built.limit', BUILT.limit],
    ['built.rawOff', BUILT.rawOff], ['built.top', BUILT.top], ['built.passport', BUILT.passport],
    ['built.measure', BUILT.measure], ['built.word', { ...BUILT.word, none: 'not measured' }], ['built.options', Object.fromEntries(BUILT.options)],
    ...['window', 'lede', 'exempt', 'counted', 'scale', 'listTitle', 'untested', 'legend', 'legendExempt', 'legendUntested',
      'legendRegistered', 'source'].map((k) => [`communes.${k}`, COMMUNES[k]] as [string, unknown]),
    ['balance.rows', BALANCE.rows], ['balance.limit', BALANCE.limit],
    ['registered.title', REGISTERED.title], ['registered.expects', REGISTERED.expects], ['registered.refused', REGISTERED.refused],
    ['registered.named', REGISTERED.named],
    ...['antwerp', 'liege', 'charleroi'].map((k) => [`registered.none.${k}`, REGISTERED.none(k, '')] as [string, unknown]),
  ]
  for (const [k, v] of FROM_EN) expect(at(k), k).toEqual(v)
  const { lede: _h, ...heatNew } = a.need.lenses.heat
  expect(heatNew).toEqual(heatRest)

  // the en.js functions, now messages: the same sentence for the same arguments
  const same: [string, Record<string, string | number>, string][] = [
    ['need.notMeasured', { city: 'Liège' }, NOT_MEASURED('Liège')],
    ['more.title', { k: 7 }, MORE.title(7)], ['more.all', { n: 40 }, MORE.all(40)],
    ['communes.title', { city: 'Ghent' }, COMMUNES.title('Ghent')], ['communes.canopyToo', { c: '8%' }, COMMUNES.canopyToo('8%')],
    ['communes.leaveOut', { n: 4, area: '31%', res: '12%', woody: '40%', rest: 15, restGreen: '33.1%' },
      COMMUNES.leaveOut(4, '31%', '12%', '40%', 15, '33.1%')],
    ['photos.window', { a: 2017, b: 2025 }, PHOTOS.window(2017, 2025)], ['photos.tag', { y: 2025 }, PHOTOS.tag(2025)],
    ['photos.handle', { a: 2017, b: 2025 }, PHOTOS.handle(2017, 2025)], ['photos.lede', { a: 2017, b: 2025 }, PHOTOS.lede(2017, 2025)],
    ['photos.note', { window: '2017–19 → 2021–24' }, PHOTOS.note('2017–19 → 2021–24')],
    ['balance.title', { base: 2024 }, BALANCE.title(2024)], ['balance.lede', { base: 2024, s: '2026' }, BALANCE.lede(2024, '2026')],
    ['balance.net', { v: '+1.2 ha' }, BALANCE.net('+1.2 ha')], ['balance.split', { lost: '3.1 ha', gained: '0.4 ha' }, BALANCE.split('3.1 ha', '0.4 ha')],
    ['balance.preliminary', { y: 2026 }, BALANCE.preliminary(2026)],
    ['equity.byIncome.services', { o: 'family' }, EQUITY.byIncome.services('family')],
    ['equity.byIncome.services', { o: 'remote' }, EQUITY.byIncome.services('remote')],
    ['equity.byIncome.services', { o: 'senior' }, EQUITY.byIncome.services('senior')],
    ...['bakery', 'cafe', 'confectionery'].map((o) => ['equity.byIncome.shops', { o }, EQUITY.byIncome.shops(o)] as [string, Record<string, string>, string]),
    ['equity.livesIn', { group: 'the hottest third', cut: '+1.5 °C or more' }, EQUITY.livesIn('the hottest third', '+1.5 °C or more')],
    ['equity.livesIn', { group: 'the sectors that meet neither part', cut: 'none' }, EQUITY.livesIn('the sectors that meet neither part', null)],
    ['equity.source', { lo: '€18,000', hi: '€24,000' }, EQUITY.source('€18,000', '€24,000')],
    ['place.named', { date: '4 September 2026' }, PLACE.named('4 September 2026')],
    ['place.snap', { date: '27 September 2026' }, PLACE.registerSnap('27 September 2026')],
  ]
  for (const [k, v, want] of same) expect(tr(k, v), k).toBe(want)

  // every other placeholder-free label is a literal of the old atlas; the few it never had are pinned here
  const jsx = fs.readFileSync(path.resolve(__dirname, 'oracle/old-Atlas.jsx.txt'), 'utf8')
  const copied = FROM_EN.map(([k]) => k).concat('need.lenses.heat')
  const NEW: Record<string, string> = {
    'meta.description': 'Every sector of Brussels, Antwerp, Ghent, Liège and Charleroi, three questions: what it lacks, what to place there, and what actually changed in its green, beyond the city’s own noise.',
    reload: 'Reload',
    // re-check 2: the map's keyboard, read as its description (WCAG 2.1.1); the old atlas had no keyboard map
    mapKeys: 'Arrow keys move the map, plus and minus zoom, Enter opens the sector in the middle.',
    // design wave (5 Oct): the pan buttons, a single pointer's way to move the map (WCAG 2.5.7)
    'pan.group': 'Move the map', 'pan.up': 'Up', 'pan.left': 'Left', 'pan.right': 'Right', 'pan.down': 'Down',
  }
  const leaves = (o: unknown, p = ''): [string, unknown][] =>
    o && typeof o === 'object' && !Array.isArray(o) ? Object.entries(o).flatMap(([k, v]) => leaves(v, p ? `${p}.${k}` : k)) : [[p, o]]
  let n = 0
  const missing: string[] = []
  for (const [k, v] of leaves(a)) {
    if (copied.some((c) => k === c || k.startsWith(`${c}.`))) continue
    if (typeof v !== 'string' || /[{}]/.test(v)) continue
    if (k in NEW) { expect(v, k).toBe(NEW[k]); continue }
    n++
    // as a JS string or as JSX text: 'Zoom in', "Zoom in", `…`, or >Zoom in< (whitespace around JSX text allowed)
    const lit = v.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    if (!new RegExp(`['"\`]${lit}['"\`]|>\\s*${lit}\\s*<`).test(jsx)) missing.push(`${k}: ${v}`)
  }
  expect(missing).toEqual([])
  expect(n).toBeGreaterThan(50)
  // the 3-30-300 words of the sector card: Atlas.jsx's R3
  expect(jsx).toContain(`const R3 = ${JSON.stringify(a.passport.r3Value).replace(/"/g, '\'').replace(/,/g, ', ')}`)
})

// Atlas.jsx's HA() (line 551) and the BALANCE.split arguments (line 564): one decimal and a no-break space before ha
const NBSP = String.fromCharCode(160)
const HAold = (v: number) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${fixed(Math.abs(v), 1, 'en')}${NBSP}ha`
test.each(CITIES)('%s: every hectare figure of the balance equals the old site’s, no-break space included', async (key) => {
  const c = (await getCity(key)) as AtlasCity
  let n = 0
  for (const d of Object.values(c.balance?.seasons ?? {})) {
    for (const k of ['green', 'trees', 'built'] as const) {
      n++
      expect(haValue(tr, d[k].net_ha, 'en')).toBe(HAold(d[k].net_ha))
      expect(haValue(tr, d[k].lost_ha, 'en', false)).toBe(`${fixed(Math.abs(d[k].lost_ha), 1, 'en')}${NBSP}ha`)
      expect(haValue(tr, d[k].gained_ha, 'en', false)).toBe(`${fixed(d[k].gained_ha, 1, 'en')}${NBSP}ha`)
    }
  }
  for (const v of [0, 0.04, -0.04, 12.25, -3.96]) expect(haValue(tr, v, 'en')).toBe(HAold(v))
  expect(n).toBeGreaterThan(0)
})

test('the map tip on what changed: a value, or “not measured” where the sector has none, never “effect —” (re-check 3)', async () => {
  expect(changeTip(tr, 'effect', 0.0132, 'en')).toBe('effect +0.013')
  expect(changeTip(tr, 'raw', -0.0376, 'en')).toBe('raw −0.038')
  expect(changeTip(tr, 'built', 0, 'en')).toBe('built-up 0.000')
  const c = (await getCity('brussels')) as AtlasCity
  const none = c.sectors.filter((s) => s.ne == null)
  expect(none.length).toBe(38)
  for (const s of none) {
    expect(changeTip(tr, 'effect', s.ne, 'en')).toBe('not measured')
    expect(changeTip(tr, 'raw', s.raw, 'en')).toBe('not measured')
  }
})


const fr = (key: string, v?: Record<string, string | number>) => key === 'units.c' ? `${v!.v} °C` : key === 'units.ha' ? `${v!.v} ha` : key
test('the unit keeps to its number whatever the language writes around it', () => {
  expect(glue(fr('units.c', { v: '+1,2' }), '+1,2')).toBe('+1,2\u00A0°C')
  expect(glue('environ 3 ha', '3')).toBe('environ 3\u00A0ha')
  expect(glue('no number here', '7')).toBe('no number here')
  expect(glue('15 and 5 ha', '5')).toBe('15 and 5\u00A0ha')
  expect(glue('1.5 ha', '5')).toBe('1.5 ha')
})
test('the register sentence takes the object with its own article, in any language', () => {
  const tr = (k: string, v?: Record<string, string | number>) => `${k}|${JSON.stringify(v)}`
  const o = { date: '2026-09-26', named: { at: 2, gap: null, n: 10 }, control: { at: 1, gap: null, n: 10 } }
  expect(placeRegister(tr, o, 'een bank', 'geen bank')).toContain('"a":"een bank"')
  expect(placeRegister(tr, { ...o, named: { ...o.named, at: 0 }, control: { ...o.control, at: 0 } }, 'un banc', 'aucun banc')).toContain('"no":"aucun banc"')
})
test('the heat lede names the city in the page language', () => {
  expect(heatLede((k, v) => `${v!.city} ${v!.r}`, 'Luik', -0.8, 'nl')).toBe('Luik −0,80')
})
