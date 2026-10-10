import { createTranslator } from 'next-intl'
import { expect, test } from 'vitest'
import { communeQuery, finderItems, indexable, resolveCommune } from '@/lib/commune'
import { fold, matches } from '@/lib/finder'
import { fixed, int } from '@/lib/format'
import en from '@/messages/en.json'

// the commune page's known answers (plan 3, task 3): what an address opens, what the finder finds,
// and the catalogue's own lines — checked against the production page 28 Sep 2026

test('an address opens the index, a commune, or the old message — never an error', async () => {
  const index = await resolveCommune({})
  expect(index.state).toBe('index')
  expect(indexable(index)).toBe(true)
  expect(communeQuery(index)).toBe('')
  if (index.state !== 'index') return
  expect(index.communes).toHaveLength(23)

  const anderlecht = await resolveCommune({ code: '21001' })
  expect(anderlecht.state === 'ok' && anderlecht.c.name).toBe('Anderlecht')
  expect(indexable(anderlecht)).toBe(true)
  expect(communeQuery(anderlecht)).toBe('?code=21001')

  const nope = await resolveCommune({ code: '00000' })
  expect(nope.state).toBe('missing')
  expect(indexable(nope)).toBe(false)
  expect(communeQuery(nope)).toBe('?code=00000')
  expect(communeQuery(await resolveCommune({ code: 'a&b' }))).toBe('?code=a%26b')

  // the old router read the query with URLSearchParams.get: an empty code is no code (the index),
  // a repeated one reads its first value
  expect((await resolveCommune({ code: '' })).state).toBe('index')
  const rep = await resolveCommune({ code: ['44021', '00000'] })
  expect(rep.state === 'ok' && rep.c.name).toBe('Ghent')
  expect((await resolveCommune({ code: ['00000', '21001'] })).state).toBe('missing')
})

test('one commune of each city resolves', async () => {
  for (const [code, city] of [['21004', 'brussels'], ['11002', 'antwerp'], ['44021', 'ghent'], ['62063', 'liege'], ['52011', 'charleroi']]) {
    const r = await resolveCommune({ code })
    expect(r.state === 'ok' && r.c.city, code).toBe(city)
  }
})

test('the finder folds accents and case, matches the code and the city, and lists all when empty', async () => {
  const r = await resolveCommune({})
  if (r.state !== 'index') throw new Error(r.state)
  const items = finderItems(r.communes, 'en', (code) => `NIS ${code}`, (city) => en.common.cities[city as keyof typeof en.common.cities])
  expect(Object.keys(items[0]!).sort()).toEqual(['city', 'code', 'find', 'name', 'nis'])
  expect(items.find((c) => c.code === '21001')!.nis).toBe('NIS 21001')
  expect(fold('Liège')).toBe('liege')
  expect(matches(items, 'LIEGE').map((c) => c.code)).toEqual(['62063'])
  expect(matches(items, ' 21001 ').map((c) => c.name)).toEqual(['Anderlecht'])
  expect(matches(items, 'brussels')).toHaveLength(19)
  // the official name counts too: Bruxelles is officially Bruxelles / Brussel
  expect(matches(items, 'brussel').length).toBeGreaterThanOrEqual(19)
  expect(matches(items, '')).toHaveLength(23)
  expect(matches(items, 'zzz')).toEqual([])
})

test('a commune is named in the page’s language; the finder finds it by any of its names, and its city by any language', async () => {
  const r = await resolveCommune({})
  if (r.state !== 'index') throw new Error(r.state)
  const city = (k: string) => en.common.cities[k as keyof typeof en.common.cities]
  const nl = finderItems(r.communes, 'nl', (code) => code, city)
  const fr = finderItems(r.communes, 'fr', (code) => code, city)
  expect(nl.find((c) => c.code === '21002')!.name).toBe('Oudergem')
  expect(fr.find((c) => c.code === '21002')!.name).toBe('Auderghem')
  expect(fr.find((c) => c.code === '44021')!.name).toBe('Gand')
  expect(nl.find((c) => c.code === '11002')!.name).toBe('Antwerpen')
  expect(fr.find((c) => c.code === '11002')!.name).toBe('Anvers')
  // the English page finds Elsene, and the French page Ixelles: the query matches every name, whatever the page shows
  const enItems = finderItems(r.communes, 'en', (code) => code, city)
  expect(matches(enItems, 'elsene').map((c) => c.code)).toEqual(['21009'])
  expect(matches(nl, 'ixelles').map((c) => c.code)).toEqual(['21009'])
  expect(matches(fr, 'anvers').map((c) => c.code)).toEqual(['11002'])
  // a hyphen, a space or an apostrophe is the same gap (re-check 5 after plan 5: «sint joost» and «saint josse» found
  // nothing, though the names are Sint-Joost-ten-Node and Saint-Josse-ten-Noode)
  for (const q of ['sint joost', 'saint josse', 'Saint–Josse ten', 'sint-joost  ten node'])
    expect(matches(fr, q).map((c) => c.code), q).toEqual(['21014'])
  expect(matches(nl, 'berchem sainte agathe').map((c) => c.code)).toEqual(['21003'])
  expect(fold('Sint-Joost-ten-Node')).toBe('sint joost ten node')
  // the region is the catalogue's, by the row's key
  const oud = await resolveCommune({ code: '21002' })
  if (oud.state !== 'ok') throw new Error(oud.state)
  expect(oud.c.region_key).toBe('brussels')
  expect(en.common.regions[oud.c.region_key]).toBe('Brussels-Capital Region')
  expect(r.communes.map((c) => c.region_key).every((k) => k in en.common.regions)).toBe(true)
})

// strict: a message that fails to parse or format throws here, instead of printing its key
const t = createTranslator({ locale: 'en', messages: en, namespace: 'commune', onError: (e) => { throw e } })

test('the catalogue keeps the commune page’s known lines', () => {
  expect(t('meta.title', { name: 'Anderlecht' })).toBe('Anderlecht · Commune · Frondia')
  expect(t('meta.titleIndex')).toBe('Communes · Frondia')
  // the noun is part of the sentence, so a translation can decline it (plan 3 fix wave, M8)
  expect(t('balance.title', { v: '+1.2 ha', s: '2026' })).toBe('Tree canopy +1.2 ha beyond noise by summer 2026')
  expect(t('find.hint', { n: int(23, 'en') })).toBe('23 communes in Brussels, Antwerp, Ghent, Liège and Charleroi')
  expect(t('title', { name: 'Anderlecht', exempt: 'no' })).toBe('Anderlecht: counted in Article 8’s total')
  expect(t('title', { name: 'Uccle', exempt: 'yes' })).toBe('Uccle: left out of Article 8’s count')
  expect(t('law.title', { kind: 'green', p: fixed(100 * (0.45 - 0.380321), 1, 'en') })).toBe('7.0 points under the green line: counted')
  expect(t('law.title', { kind: 'exempt', p: '' })).toBe('Over both lines: left out of the count')
  expect(t('law.vsLine', { p: '5.0', side: 'below', line: '45' })).toBe('5.0 points below the 45% line')
  expect(t('change.title', { up: '1', n: 1, down: '0', m: '10' })).toBe('1 sector greener and 0 lost beyond noise, of 10 measured')
  expect(t('change.title', { up: '3', n: 3, down: '3', m: '77' })).toBe('3 sectors greener and 3 lost beyond noise, of 77 measured')
  expect(t('change.title', { up: '0', n: 0, down: '2', m: '77' })).toBe('0 sectors greener and 2 lost beyond noise, of 77 measured')
  expect(t('facts.1.v' as never, { area: '17.9' } as never)).toBe('17.9 km²')
  expect(t('ndvi', { v: '−0.035' })).toBe('−0.035 NDVI')
  expect(t('missing')).toBe('No commune of the five cities has this code.')
})

test('every commune message parses', () => {
  const leaves = (o: unknown, p: string): string[] =>
    o && typeof o === 'object' ? Object.entries(o).flatMap(([k, v]) => leaves(v, p ? `${p}.${k}` : k)) : [p]
  for (const key of leaves(en.commune, '')) {
    expect(() => t(key as never, { name: 'n', n: 1, code: 'c', region: 'r', exempt: 'no', stable: 'yes', pop: '1', area: '1',
      measured: '1', sectors: '1', lau: 'l', v: '1', kind: 'both', p: '1', side: 'above', line: '45', green: '1', canopy: '1',
      base: '2024', k: 'k', s: '2026', a: 'a', b: 'b', w: 'w', up: '1', down: '1', m: '1', d: 'd', l: 'l',
      resIn: '1', resOut: '1', haIn: '1', haOut: '1' } as never), key).not.toThrow()
  }
})
