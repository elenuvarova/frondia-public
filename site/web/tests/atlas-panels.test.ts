import { NextIntlClientProvider } from 'next-intl'
import { createElement, type ReactElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { expect, test } from 'vitest'
import en from '@/messages/en.json'
import { ATLAS_CLIENT_PATHS, clientMessages } from '@/lib/client-messages'
import { getCases, getCity, getPoints } from '@/lib/data'
import { countFor } from '@/lib/verdict'
import { fixed, int } from '@/lib/format'
import type { AtlasCity, AtlasPoints } from '@/lib/atlas/types'
import { ChangePanel } from '@/components/atlas/ChangePanel'
import { NeedPanel } from '@/components/atlas/NeedPanel'
import { PlacePanel } from '@/components/atlas/PlacePanel'
import { Passport } from '@/components/atlas/Passport'
import { CaseDrawer } from '@/components/atlas/CaseDrawer'

// the atlas's panels render under the atlas layout's provider, with only the atlas's subset of the catalogue:
// rendering them here proves the subset is enough: a missing key throws (onError), and none prints as `atlas.…`, `common.…` or `landing.…`
const messages = clientMessages(en as never, ATLAS_CLIENT_PATHS)
const html = (el: ReactElement) => renderToStaticMarkup(createElement(NextIntlClientProvider, { locale: 'en', timeZone: 'Europe/Brussels', messages, onError: (e: Error) => { throw e }, children: el }))
  .replace(/ |⁠/g, (c) => (c === ' ' ? ' ' : ''))
const noop = () => {}
const CITIES = ['brussels', 'antwerp', 'ghent', 'liege', 'charleroi'] as const

test('what changed, Brussels: the title, the counts and the threshold sentence from the data', async () => {
  const city = (await getCity('brussels')) as AtlasCity
  const counts = countFor(city.sectors, 'effect', city.thresholds.ndvi)!
  const out = html(createElement(ChangePanel, { city, lens: 'change', setLens: noop, measure: 'green', setMeasure: noop, control: true, setControl: noop, counts, top: [], onPick: noop, onPickRegistered: noop }))
  expect(out).toContain('What changed in Brussels')
  expect(out).toContain(`>${counts.up}<`)
  expect(out).toContain(`Threshold ±${fixed(city.thresholds.ndvi, 3, 'en')} — measured on ${int(city.units.comparable, 'en')} sectors of Brussels playing “intervention” once each.`)
  expect(out).not.toMatch(/(atlas|common|landing)\./)   // no key printed instead of a word
})

test('communes, Ghent: the registered records and the commune links lead to this site', async () => {
  const city = (await getCity('ghent')) as AtlasCity
  const out = html(createElement(ChangePanel, { city, lens: 'communes', setLens: noop, measure: 'green', setMeasure: noop, control: true, setControl: noop, counts: { up: 0, down: 0 }, top: [], onPick: noop, onPickRegistered: noop }))
  expect(out).toContain('Communes the law counts in Ghent')
  expect(out).toContain('projects from the City of Ghent’s own register')
  expect(out).toMatch(/href="\/commune\?code=44021"/)
})

test.each(['services', 'shops', 'heat', 'r3'])('need lens %s renders in every city without a printed key', async (lens) => {
  for (const key of CITIES) {
    const city = (await getCity(key)) as AtlasCity
    const out = html(createElement(NeedPanel, { city, lens, setLens: noop, opt: { scenario: 'family', shop: 'bakery' }, setOpt: noop, onPick: noop, otherCity: noop }))
    expect(out, `${key}/${lens}`).not.toMatch(/(atlas|common|landing)\./)
    expect(out).toContain(' in ' + (en.common.cities as Record<string, string>)[key])
  }
})

test('what to place, Brussels: toilets, the slider and the named list', async () => {
  const city = (await getCity('brussels')) as AtlasCity
  const points = (await getPoints('brussels')) as AtlasPoints
  const out = html(createElement(PlacePanel, { city, points, obj: 'toilets', setObj: noop, onPick: noop, n: 10, setN: noop }))
  expect(out).toContain('Public toilets in Brussels')
  expect(out).toContain('What if 10 more?')
  expect(out).toContain('aria-valuetext="10: ')
  expect(out).toContain('Named first')
})

test('a sector page and an audit drawer', async () => {
  const city = (await getCity('brussels')) as AtlasCity
  const points = (await getPoints('brussels')) as AtlasPoints
  const s = city.sectors.find((x) => x.id === '21004E72-')!
  const out = html(createElement(Passport, { s, city, cases: city.cases, points, opt: { scenario: 'family', shop: 'bakery' }, onClose: noop, onOpenCase: noop }))
  // Seq sets " · "-joined parts as separate spans (the dots are CSS), so each part is its own text node
  expect(out).toContain('<span>Sector</span><span>21004E72-</span>')
  expect(out).toMatch(/href="\/dossier\?city=brussels&amp;sector=21004E72-"/)
  const c = (await getCases()).find((x) => x.slug === 'ninove')!
  const d = html(createElement(CaseDrawer, { c: c as never, onClose: noop }))
  expect(d).toContain('Porte de Ninove')
  expect(d).toContain('<span>Audit</span><span>Brussels</span><span>opened ')
})

test('an audit card gives every matched place’s distance with one decimal, as the list reads (re-check 3)', async () => {
  for (const c of await getCases()) {
    const d = html(createElement(CaseDrawer, { c: c as never, onClose: noop }))
    for (const x of c.controls as { name: string; dist_km: number }[]) expect(d, `${c.slug} ${x.name}`).toContain(`>${fixed(x.dist_km, 1, 'en')} km<`)
  }
  // Droogdokkenpark's list had "3 km" between "3.1 km" and "2.9 km"
  const dd = html(createElement(CaseDrawer, { c: (await getCases()).find((x) => x.slug === 'droogdokkenpark') as never, onClose: noop }))
  expect(dd).toContain('>3.0 km<')
  expect(dd).not.toContain('>3 km<')
})

