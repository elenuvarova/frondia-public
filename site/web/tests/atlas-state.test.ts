import { expect, test } from 'vitest'
import en from '@/messages/en.json'
import { OBJECT_KEYS, atlasPath, atlasQuery, firstMeasured, parseAtlas, toParams, type AtlasState } from '@/lib/atlas/state'
import type { City } from '@/lib/types'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const P = (s: string) => parseAtlas(new URLSearchParams(s))
const DEFAULT: AtlasState = { city: 'brussels', q: 'change', lens: null, scenario: 'family', shop: 'bakery', obj: 'toilets', n: 10, view: 'change', m: 'green', caseSlug: null, sector: null }

test('a bare address is Brussels, what changed, sectors', () => {
  expect(P('')).toEqual(DEFAULT)
})

test('every parameter the old atlas read, read the same way', () => {
  expect(P('city=ghent&q=need&lens=shops&shop=cafe&for=senior')).toEqual({ ...DEFAULT, city: 'ghent', q: 'need', lens: 'shops', shop: 'cafe', scenario: 'senior' })
  expect(P('city=antwerp&q=place&obj=benches&n=25')).toEqual({ ...DEFAULT, city: 'antwerp', q: 'place', obj: 'benches', n: 25 })
  expect(P('view=communes')).toMatchObject({ view: 'communes' })
  expect(P('view=photos&m=built')).toMatchObject({ view: 'photos', m: 'built' })
  expect(P('city=antwerp&case=droogdokkenpark')).toMatchObject({ city: 'antwerp', caseSlug: 'droogdokkenpark' })
  expect(P('city=brussels&sector=21004E72-')).toMatchObject({ sector: '21004E72-' })
})

// Intended difference (F16): the old atlas looked names up in plain objects (CITY_NAMES[city], OBJECTS[obj]), so
// `city=constructor` or `obj=toString` passed as known values (and fetched data/constructor.json). Here they fall back.
test('odd values fall back as before, except prototype names (which now fall back too)', () => {
  expect(P('city=paris').city).toBe('brussels')
  expect(P('city=constructor').city).toBe('brussels')
  expect(P('q=maybe').q).toBe('change')
  expect(P('q=need&lens=junk')).toMatchObject({ q: 'need', lens: null })
  expect(P('for=kids&shop=butcher')).toMatchObject({ scenario: 'family', shop: 'bakery' })
  expect(P('obj=toString').obj).toBe('toilets')
  expect(P('n=').n).toBe(0)            // Number('') is 0 and the parameter is present: the old atlas took 0
  expect(P('n=41').n).toBe(10)
  expect(P('n=2.5').n).toBe(10)
  expect(P('n=-1').n).toBe(10)
  expect(P('view=change').view).toBe('change')
  expect(P('view=nope').view).toBe('change')
  expect(P('m=green').m).toBe('green')
  expect(P('case=&sector=')).toMatchObject({ caseSlug: null, sector: null })
  expect(P('city=antwerp&city=ghent').city).toBe('antwerp')   // the first value, as URLSearchParams.get
})

test('the address the view writes: only what differs from the defaults, case before sector', () => {
  expect(atlasQuery({ ...DEFAULT, lens: 'heat' })).toBe('?city=brussels')
  expect(atlasQuery({ ...DEFAULT, q: 'need', lens: 'services' })).toBe('?city=brussels&q=need&lens=services')
  expect(atlasQuery({ ...DEFAULT, q: 'need', lens: 'services', scenario: 'senior' })).toBe('?city=brussels&q=need&lens=services&for=senior')
  expect(atlasQuery({ ...DEFAULT, q: 'need', lens: 'shops', shop: 'cafe', scenario: 'senior' })).toBe('?city=brussels&q=need&lens=shops&shop=cafe')
  expect(atlasQuery({ ...DEFAULT, q: 'place', lens: 'heat' })).toBe('?city=brussels&q=place&obj=toilets')
  expect(atlasQuery({ ...DEFAULT, q: 'place', lens: 'heat', n: 0 })).toBe('?city=brussels&q=place&obj=toilets&n=0')
  expect(atlasQuery({ ...DEFAULT, lens: 'heat', view: 'field', m: 'built' })).toBe('?city=brussels&view=field')
  expect(atlasQuery({ ...DEFAULT, lens: 'heat', m: 'built' })).toBe('?city=brussels&m=built')
  expect(atlasQuery({ ...DEFAULT, lens: 'heat', caseSlug: 'ninove', sector: 'X' })).toBe('?city=brussels&case=ninove')
  expect(atlasQuery({ ...DEFAULT, lens: 'heat', sector: '21004E72-' })).toBe('?city=brussels&sector=21004E72-')
  expect(atlasPath('en', { ...DEFAULT, lens: 'heat', city: 'ghent' })).toBe('/atlas?city=ghent')
})

test('a parsed canonical address written back is the same address', () => {
  for (const q of ['?city=brussels&q=need&lens=services', '?city=brussels&q=place&obj=toilets', '?city=brussels&case=ninove', '?city=antwerp&case=droogdokkenpark',
    '?city=brussels&view=communes', '?city=brussels&m=built&sector=21004E72-']) {
    const s = parseAtlas(new URLSearchParams(q))
    expect(atlasQuery({ ...s, lens: s.lens ?? 'heat' })).toBe(q)
  }
})

test('the server query object reads like URLSearchParams', () => {
  expect(toParams({ city: ['antwerp', 'ghent'], n: '' }).get('city')).toBe('antwerp')
  expect(toParams({ city: ['antwerp', 'ghent'], n: '' }).get('n')).toBe('')
  expect(toParams({ x: undefined }).has('x')).toBe(false)
})

test('the object keys are the catalogue’s objects', () => {
  expect([...OBJECT_KEYS].sort()).toEqual(Object.keys(en.common.objects.many).sort())
})

test('a non-canonical address is written back in its canonical form', () => {
  const back = (q: string) => { const s = P(q); return atlasQuery({ ...s, lens: s.lens ?? 'heat' }) }
  expect(back('?q=change')).toBe('?city=brussels')
  expect(back('?city=brussels&sector=')).toBe('?city=brussels')
  expect(back('?case=ninove')).toBe('?city=brussels&case=ninove')
})

test('every branch of the old reader and writer (golden values from Atlas.jsx)', () => {
  expect(P('n=40').n).toBe(40)
  expect(P('n=0').n).toBe(0)
  expect(P('view=field').view).toBe('field')
  expect(atlasQuery({ ...DEFAULT, q: 'need', lens: 'shops', shop: 'bakery' })).toBe('?city=brussels&q=need&lens=shops')
  expect(atlasQuery({ ...DEFAULT, q: 'place', lens: 'heat', view: 'field' })).toBe('?city=brussels&q=place&obj=toilets')
  expect(atlasQuery({ ...DEFAULT, q: 'place', lens: 'heat', m: 'built' })).toBe('?city=brussels&q=place&obj=toilets')
  expect(atlasQuery({ ...DEFAULT, lens: 'heat', view: 'communes', m: 'built' })).toBe('?city=brussels&view=communes')
  expect(atlasQuery({ ...DEFAULT, q: 'need', lens: 'heat', scenario: 'senior', shop: 'cafe' })).toBe('?city=brussels&q=need&lens=heat')
  expect(atlasQuery({ ...DEFAULT, q: 'need', lens: 'services', shop: 'cafe' })).toBe('?city=brussels&q=need&lens=services')
})

test('the first measured need lens, and heat when nothing is measured', () => {
  const bxl = JSON.parse(readFileSync(path.join(__dirname, '../public/data/brussels.json'), 'utf8')) as City
  expect(firstMeasured(bxl)).toBe('services')
  expect(firstMeasured({ ...bxl, sectors: [] })).toBe('heat')
})
