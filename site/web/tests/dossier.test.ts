import { createTranslator } from 'next-intl'
import { expect, test } from 'vitest'
import { dossierQuery, indexable, resolveDossier } from '@/lib/dossier'
import { fixed, int, pct } from '@/lib/format'
import { getCases } from '@/lib/data'
import { placeName, sectorLabel, sectorName, sectorPlace } from '@/lib/names'
import en from '@/messages/en.json'

// the dossier's known answers (plan 3, task 2): which sector the open rule picks in each city, what a
// wrong address shows, and the catalogue's own lines — checked against the production page 28 Sep 2026

test('without ?sector= each city opens the rule’s first pick, or says the rule picks nothing', async () => {
  const bxl = await resolveDossier({})
  expect(bxl.state).toBe('ok')
  if (bxl.state !== 'ok') return
  expect(bxl.cityKey).toBe('brussels')
  expect(bxl.s.id).toBe('21004E72-')
  expect(bxl.city.dossier.pick.n).toBe(110)
  for (const [city, n] of [['antwerp', 77], ['ghent', 34]] as const) {
    const r = await resolveDossier({ city })
    expect(r.state, city).toBe('ok')
    if (r.state === 'ok') expect(r.city.dossier.pick.n, city).toBe(n)
  }
  for (const city of ['liege', 'charleroi']) {
    const r = await resolveDossier({ city })
    expect(r.state, city).toBe('noPick')
    // one sentence, no dossier: not to be found (ruling Q17)
    expect(indexable(r), city).toBe(false)
  }
})

test('a wrong address resolves to the old messages, never an error', async () => {
  const nope = await resolveDossier({ sector: 'nope' })
  expect(nope.state).toBe('missing')
  expect(nope.cityKey).toBe('brussels')
  expect(indexable(nope)).toBe(false)
  expect(dossierQuery(nope)).toBe('?city=brussels&sector=nope')
  // a named sector in a city without a pick is looked up, not answered with noPick
  expect((await resolveDossier({ city: 'liege', sector: 'nope' })).state).toBe('missing')
  // an unknown city is Brussels, a repeated parameter reads its first value, an empty sector is none
  expect((await resolveDossier({ city: 'paris' })).cityKey).toBe('brussels')
  expect((await resolveDossier({ city: ['antwerp', 'ghent'] })).cityKey).toBe('antwerp')
  const empty = await resolveDossier({ city: 'brussels', sector: '' })
  expect(empty.state === 'ok' && empty.s.id).toBe('21004E72-')
  expect(dossierQuery(empty)).toBe('?city=brussels&sector=21004E72-')
  expect(dossierQuery(await resolveDossier({ city: 'liege' }))).toBe('?city=liege')
  expect(dossierQuery(await resolveDossier({ sector: 'a&b' }))).toBe('?city=brussels&sector=a%26b')
})

// strict: a message that fails to parse or format throws here, instead of printing its key
const t = createTranslator({ locale: 'en', messages: en, namespace: 'dossier', onError: (e) => { throw e } })

test('the catalogue keeps the dossier’s known lines', () => {
  expect(en.dossier.standfirst).toBe('Why money for greening should come to this sector, and how the result will be checked with the same method that measured its state.')
  expect(t('meta.title', { name: 'Maison Rouge (Place)-Sud' })).toBe('Dossier · Maison Rouge (Place)-Sud · Frondia')
  expect(t('title', { name: 'Maison Rouge (Place)-Sud', gap: 'below', p: '26', pop: int(7180, 'en') }))
    .toBe('Maison Rouge (Place)-Sud: canopy 26% below the city’s median, 7,180 residents')
  expect(t('title', { name: 'X', gap: 'half', p: '', pop: '1' })).toBe('X: half the city’s median canopy, 1 residents')
  expect(t('fair.title', { kind: 'half', p: '' })).toBe('The poorest third of the city lives with half the canopy')
  expect(t('scale.reading', { side: 'at', p: '' })).toBe('at the city’s median')
  expect(t('scale.reading', { side: 'below', p: '36' })).toBe('36% below the city’s median')
  // named, not positional: a translation may reorder them (plan 3 fix wave, M8)
  expect(t('fair.rows.lowest')).toBe('Lowest third by income')
  expect(t('fair.rows.highest')).toBe('Highest third')
  expect(Object.keys(en.dossier.cases.head)).toEqual(['intervention', 'effect', 'threshold', 'times', 'reading'])
  expect(t('cases.head.reading')).toBe('Reading')
})

test('a city the rule skips says why, with its own Article 8(1) figure', async () => {
  const r = await resolveDossier({ city: 'liege' })
  if (r.state !== 'noPick') throw new Error(r.state)
  const lau = r.city.communes.list.find((c) => c.green != null)
  expect(t('noPick', { city: r.city.name, green: pct(lau?.green, 1, 'en') })).toMatch(
    /^The open rule picks no sector in Liège\. It asks for a commune the law counts, and Liège is exempt under Article 8\(1\): \d+\.\d% green/)
})

test('the 3-30-300 paragraph reads each branch whole', () => {
  const base = { fails: 'a; b', lst: '37.1', exc: '1.5', side: 'above', r: '−0.89' }
  const both = t('fair.rule.body', { ...base, verdict: 'none', strength: 'deterministic', both: 'yes' })
  expect(both).toContain('neither measurable part of the rule is met: a; b.')
  expect(both).toContain('the link is almost deterministic (r = −0.89), and this sector sits at the bad end of both scales at once.')
  const one = t('fair.rule.body', { ...base, fails: 'a', verdict: 'one', strength: 'other', side: 'below', both: 'no' })
  expect(one).toContain('one part of the rule is not met: a.')
  expect(one).toContain('1.5 °C below the city’s median')
  expect(one).toContain('the link is noticeable (r = −0.89). Temperature')
  expect(t('fair.rule.body', { ...base, verdict: 'both', strength: 'strong', both: 'no' })).toContain('both measurable parts of the rule are met.')
})

test('every dossier message parses', () => {
  const leaves = (o: unknown, p: string): string[] =>
    o && typeof o === 'object' ? Object.entries(o).flatMap(([k, v]) => leaves(v, p ? `${p}.${k}` : k)) : [p]
  for (const key of leaves(en.dossier, '')) {
    // every argument any message names, so each branch has what it needs
    expect(() => t(key as never, { name: 'n', gap: 'at', p: '1', pop: '1', commune: 'c', id: 'i', last: '2026', city: 'c', green: 'g',
      minHeat: '1', minRes: '1', n: '1', v: '1', tp: '1', np: '1', cut: '1', inc: '1', side: 'at', w: 'w', ne: '1', nt: '1', te: '1', tt: '1',
      shift: '1', kRaw: '1', share: '1', kEff: '1', span: 's', items: 'i', year: '1', kind: 'k', effect: '1', ratio: '1',
      k: '1', kp: '1', o: '1', op: '1', o80: '1', third: '1', hardest: 'no', c: '1', verdict: 'both', fails: '', lst: '1', exc: '1',
      strength: 'strong', r: '1', both: 'no', date: 'd', controls: '1', km: '1', minScenes: '1', maxGap: '1', ha: '1', rank: '1', role: 'named', target: '30%', reg: 'yes', copy: 'c' } as never), key).not.toThrow()
  }
})

test('the cases table gives each footprint from the data, rounded as the landing rounds it (re-check 3)', async () => {
  const cases = await getCases()
  const ha = (slug: string) => fixed(cases.find((c) => c.slug === slug)!.area_ha, 1, 'en')
  // Porte de Ninove is 2.25 ha: the landing printed 2.3 and this table a typed-in 2.2
  expect(t('cases.what.ninove', { ha: ha('ninove') })).toBe('wasteland by the canal → park, 2.3 ha')
  expect(t('cases.what.spoor-noord', { ha: ha('spoor-noord') })).toBe('rail yard → park, 19.5 ha')
  expect(t('cases.what.droogdokkenpark', { ha: ha('droogdokkenpark') })).toBe('old docks → a quayside park')
  for (const v of Object.values(en.dossier.cases.what)) expect(v).not.toMatch(/\d ha/)   // no area typed into the catalogue
})


test('the dossier’s sector, its commune and its Article 8 commune in the page’s language; “None” is no name', async () => {
  const r = await resolveDossier({ city: 'brussels', sector: '21004E72-' })
  if (r.state !== 'ok') throw new Error(r.state)
  expect(sectorName(r.s, 'en')).toBe('Maison Rouge (Place)-Sud')
  expect(sectorName(r.s, 'nl')).toBe('Roodhuisplein-Zuid')
  expect(sectorName(r.s, 'fr')).toBe('Maison Rouge (Place)-Sud')
  expect([sectorPlace(r.s, 'en'), sectorPlace(r.s, 'nl'), sectorPlace(r.s, 'fr')]).toEqual(['Bruxelles', 'Brussel', 'Bruxelles'])
  const law = r.city.communes.list.find((c) => c.code === '21009')!
  expect([placeName(law, 'en'), placeName(law, 'nl'), placeName(law, 'fr')]).toEqual(['Ixelles', 'Elsene', 'Ixelles'])
  // Liège 62063L0AP is "None" in the source: its dossier prints what a nameless sector's prints, in every language
  const none = await resolveDossier({ city: 'liege', sector: '62063L0AP' })
  if (none.state !== 'ok') throw new Error(none.state)
  for (const loc of ['en', 'nl', 'fr'] as const) expect(sectorName(none.s, loc)).toBe('')
  expect(sectorPlace(none.s, 'en')).toBe('Rocourt')
  // and the dossier calls it by its code (fix round 1): "Dossier · Sector 62063L0AP · Frondia", not "Dossier ·  · Frondia"
  const tc = createTranslator({ locale: 'en', messages: en, namespace: 'common', onError: (e) => { throw e } })
  const label = sectorLabel(none.s, 'en', (id) => tc('sectorFallback', { id }))
  expect(t('meta.title', { name: label })).toBe('Dossier · Sector 62063L0AP · Frondia')
  expect(t('title', { name: label, gap: 'above', p: '21', pop: '759' })).toBe('Sector 62063L0AP: canopy 21% above the city’s median, 759 residents')
})
