import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { expect, test } from 'vitest'
import { SectorMap } from '@/components/SectorMap'
import type { City, Sector } from '@/lib/types'

// The lightest classes' edge (WCAG 1.4.11, design wave 5 Oct) is a stroke on the sector's own path, not a second copy of
// its geometry: the copy added 136 KB raw / 36 KB gzip to the landing's HTML (round-3 re-check, 6 Oct). Fails on bd8848d.
const sq = (x: number) => `M${x},0h10v10h-10Z`
const sectors = [
  { id: 'a', d: sq(0), f: 'var(--lack-1)' },   // light: lack-4 edge
  { id: 'b', d: sq(10), f: 'var(--lack-4)' },  // dark: paper outline
  { id: 'c', d: sq(20), f: 'var(--green-2)' }, // light: green-5 edge
  { id: 'd', d: sq(30), f: null },             // blank
  { id: 'e', d: sq(40), f: 'var(--loss-1)' },  // light: loss-3 edge
  { id: 'f', d: sq(50), f: 'var(--gain-3)' },  // dark
]
const city = { svg: { W: 60, H: 10 }, thresholds: { ndvi: 0.04 }, sectors, field: null } as unknown as City
const fill = (s: Sector) => (s as unknown as { f: string | null }).f
const html = renderToStaticMarkup(createElement(SectorMap, { city, fill, field: false, label: 'map' }))
const paths = [...html.matchAll(/<path ([^>]*)>/g)].map((m) => m[1]!).filter((a) => /\bd="M\d+,0h10/.test(a))
const attr = (a: string, k: string) => a.match(new RegExp(`\\b${k}="([^"]*)"`))?.[1]

test('every sector’s geometry is in the markup once', () => {
  for (const s of sectors) expect(html.split(`d="${s.d}"`).length - 1, s.id).toBe(1)
  expect(html).not.toContain('light-edges')
})

test('the lightest classes carry their ramp’s dark step as a 0.8 stroke; the others the paper outline', () => {
  const by = Object.fromEntries(paths.map((a) => [sectors.find((s) => attr(a, 'd') === s.d)!.id, a]))
  expect([attr(by.a!, 'stroke'), attr(by.c!, 'stroke'), attr(by.e!, 'stroke')]).toEqual(['var(--lack-4)', 'var(--green-5)', 'var(--loss-3)'])
  for (const k of ['a', 'c', 'e']) expect(attr(by[k]!, 'stroke-width'), k).toBe('0.8')
  for (const k of ['b', 'd', 'f']) expect([attr(by[k]!, 'stroke'), attr(by[k]!, 'stroke-width')], k).toEqual(['var(--paper)', '0.6'])
})

test('the light sectors are painted last, so a neighbour’s paper outline never covers their edge', () => {
  const ids = paths.map((a) => sectors.find((s) => attr(a, 'd') === s.d)!.id)
  expect(ids).toEqual(['b', 'd', 'f', 'a', 'c', 'e'])   // the rest in the data's order, then the light ones in theirs
})

// The landing's maps get a slim city (lib/map-city.ts): the same pictures from a fraction of the data, since a client
// component's props are sent to the browser again inside the page (round-3 re-check, 6 Oct)
import fs from 'node:fs'
import path from 'node:path'
import { ThreeMap } from '@/components/ThreeMap'
import { mapCity } from '@/lib/map-city'

const bxl = JSON.parse(fs.readFileSync(path.join(__dirname, '../public/data/brussels.json'), 'utf8')) as City
const draw = (c: City, el: 'raw' | 'effect' | 'need' | 'place' | 'change') => renderToStaticMarkup(
  el === 'raw' || el === 'effect' ? createElement(SectorMap, { city: c, mode: el, label: 'map' }) : createElement(ThreeMap, { city: c, kind: el, label: 'map' }))

test('the landing’s five maps draw the same from the slim city as from the whole one', () => {
  const slim = mapCity(bxl)
  for (const k of ['raw', 'effect', 'need', 'place', 'change'] as const) expect(draw(slim, k) === draw(bxl, k), k).toBe(true)
  expect(draw(bxl, 'need')).toContain('is-light')   // the case the edge is for is in the comparison
})

test('the slim city is one object per city and a fraction of the package', () => {
  expect(mapCity(bxl)).toBe(mapCity(bxl))
  const full = JSON.stringify(bxl).length, slim = JSON.stringify(mapCity(bxl)).length
  expect(slim).toBeLessThan(260_000)   // 210 KB on 6 Oct; the package is 680 KB
  expect(slim / full).toBeLessThan(0.4)
})
