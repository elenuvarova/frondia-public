import { expect, test } from 'vitest'
import en from '@/messages/en.json'

const leaves = (o: unknown, p = ''): [string, unknown][] =>
  o && typeof o === 'object' ? Object.entries(o).flatMap(([k, v]) => leaves(v, p ? `${p}.${k}` : k)) : [[p, o]]

test('no empty strings in the English catalogue', () => {
  for (const [k, v] of leaves(en)) if (typeof v === 'string') expect(v.trim(), k).not.toBe('')
})

test('common has the words of the bar and the footer', () => {
  expect(en.common.nav.atlas).toBe('Open the atlas')
  expect(en.common.footer.motto).toBe(', the growth, not the rustle.')
  // /data and /register when their file can't be read: said plainly, as the landing's load error
  // does (the old pages showed a "Loading…" that never ended)
  expect(en.common.unavailable).toBe('The measurements behind this page did not load.')
})

test('the landing keeps its known lines', () => {
  expect(en.landing.hero.title).toBe('What actually <em>changed.</em>')
  expect(en.landing.hero.caption).toBe('An illustration, not a measurement.')
  expect(en.landing.words).toHaveLength(21)
  expect(en.landing.faq.map((f: { id: string }) => f.id)).toEqual(['scope', 'trees', 'outline', 'wrong', 'official', 'small', 'cities', 'current'])
})

test('the privacy page says the basis, where the choice is kept, and uses curly apostrophes', () => {
  const p = en.privacy as Record<string, unknown>
  expect(p.basis).toMatch(/consent/)
  expect(p.basis).toMatch(/legitimate interest/)
  expect(p.counts).toMatch(/your cookie choice/)
  expect(p.counts).toMatch(/as long as the site runs/)
  expect(p.clarity).toMatch(/local storage, not in a cookie/)
  expect(p.none).toMatch(/other sites using Clarity/)
  expect(p.who).toContain('<mail>{email}</mail>')
  for (const [k, v] of leaves(p)) if (typeof v === 'string') expect(v, k).not.toContain("'")
})

test('common carries the city and object names and the charts’ words (plan 4, task 3)', () => {
  const c = en.common as Record<string, unknown>
  expect(c.cities).toEqual({ brussels: 'Brussels', antwerp: 'Antwerp', ghent: 'Ghent', liege: 'Liège', charleroi: 'Charleroi' })
  const o = c.objects as { one: Record<string, string>; many: Record<string, string> }
  expect(o.one.toilets).toBe('public toilet')
  expect(o.many.fitness_stations).toBe('Outdoor fitness')
  expect(Object.keys(o.one)).toHaveLength(14)
  expect(Object.keys(o.many).sort()).toEqual(Object.keys(o.one).sort())
  // moved, not copied
  expect((en.data as Record<string, unknown>).cities).toBeUndefined()
  expect((en.dossier.place as Record<string, unknown>).objects).toBeUndefined()
})

test('the separators, and each object with its article and its negation (plan 5, task 3)', () => {
  const c = en.common as Record<string, unknown>
  expect(c.sep).toEqual({ dot: ' · ', list: ', ', semi: '; ', rank: '#{n}' })
  const o = c.objects as Record<'one' | 'a' | 'no', Record<string, string>>
  const keys = Object.keys(o.one).sort()
  expect(Object.keys(o.a).sort()).toEqual(keys)
  expect(Object.keys(o.no).sort()).toEqual(keys)
  expect(o.a.fitness_stations).toBe('an outdoor fitness station')
  // the old code chose "an" before a vowel and "no" for none, on the singular: the phrases say the same
  for (const k of keys) {
    expect(o.a[k], k).toBe(`${/^[aeiou]/i.test(o.one[k]!) ? 'an' : 'a'} ${o.one[k]}`)
    expect(o.no[k], k).toBe(`no ${o.one[k]}`)
  }
})

// L7: the nearest-shop label and the shops reading keep their own choice by shop (an adjective agrees with
// the noun in French), so their variants are checked against need.shop: the same shops, "other" standing for
// confectionery
test('the shop choices cover need.shop: bakery, café, and other for confectionery', () => {
  const variants = (m: string) => {
    const x = /\{(?:shop|o), select, ((?:\w+ \{[^{}]*\} ?)+)\}/.exec(m)
    expect(x, m).not.toBeNull()
    return [...x![1]!.matchAll(/(\w+) \{/g)].map((y) => y[1]).join('|')
  }
  expect(variants(en.atlas.passport.nearest)).toBe('bakery|cafe|other')
  expect(variants(en.atlas.equity.reading.shops)).toBe('bakery|cafe|other')
  expect(Object.keys(en.atlas.need.shop)).toEqual(['bakery', 'cafe', 'confectionery'])
})
