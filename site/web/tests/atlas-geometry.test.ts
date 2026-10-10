import { expect, test } from 'vitest'
import { barStyle, bbox, clampView, fitBox, freeArea, greenStep, leftLabels, placeLabels, type ViewBox } from '@/lib/atlas/geometry'

test('bbox reads every coordinate pair of a path', () => {
  expect(bbox('M0,0L10,5L-2,3Z')).toEqual({ x0: -2, y0: 0, x1: 10, y1: 5 })
  expect(bbox('')).toBeNull()
  expect(bbox('MZ')).toBeNull()
})

test('fitBox places a box in the map area the panels leave free (desktop and phone)', () => {
  const d = fitBox({ w: 1000, h: 800 }, { x0: 0, y0: 0, x1: 100, y1: 100 })
  expect(d.x).toBeCloseTo(-68.1159, 3); expect(d.y).toBeCloseTo(-22.4638, 3)
  expect(d.w).toBeCloseTo(181.1594, 3); expect(d.h).toBeCloseTo(144.9275, 3)
  const p = fitBox({ w: 390, h: 800 }, { x0: 0, y0: 0, x1: 100, y1: 100 })
  expect(p.x).toBeCloseTo(-3.2787, 3); expect(p.y).toBeCloseTo(-16.6667, 3)
  expect(p.w).toBeCloseTo(106.5574, 3); expect(p.h).toBeCloseTo(218.5792, 3)
  // a drawer on the right (desktop only) narrows the free width by 332
  const r = fitBox({ w: 1000, h: 800 }, { x0: 0, y0: 0, x1: 100, y1: 100 }, 1, true)
  expect(r.w).toBeCloseTo(1000 / 2.2, 3)
})

test('the free area: panels on desktop, a sheet on the phone (860 is still a phone)', () => {
  expect(freeArea({ w: 1000, h: 800 })).toEqual({ l: 376, t: 24, w: 552, h: 752 })
  expect(freeArea({ w: 860, h: 1000 })).toEqual({ l: 12, t: 56, w: 836, h: 484 })
  expect(freeArea({ w: 1000, h: 100 })).toEqual({ l: 376, t: 24, w: 552, h: 80 })   // never under 80
})

test('clampView keeps the zoom between 1/28 and 1.25 of home', () => {
  const home = { x: 0, y: 0, w: 1000, h: 800 }
  expect(clampView({ x: 0, y: 0, w: 5000, h: 4000 }, home, 1000, 800).w).toBe(1250)
  expect(clampView({ x: 0, y: 0, w: 1, h: 0.8 }, home, 1000, 800).w).toBeCloseTo(1000 / 28, 6)
})

test('commune names move a line rather than touch, larger communes first', () => {
  const out = placeLabels([{ name: 'Bb', x: 0, y: 0, area: 1 }, { name: 'Aa', x: 0, y: 0, area: 2 }], [], 10, 4, 'en')
  expect(out.map((c) => c.name)).toEqual(['Aa', 'Bb'])
  expect(out[0]!.y).toBe(0)
  expect(out[1]!.y).toBeCloseTo(13.8, 6)
})

test('the green classes and the bars', () => {
  expect([null, 0.1, 0.15, 0.449, 0.45, 0.6].map(greenStep)).toEqual([null, 0, 1, 2, 3, 4])
  expect(barStyle('services', 50, [50, 60, 70])).toEqual({ left: 0, width: '50%' })
  // heat leaves the centre line: the widest |value| (2) is half the track, so −1 is a quarter, left of centre
  expect(barStyle('heat', -1, [-1, 0, 2])).toEqual({ left: '25%', width: '25%' })
})

test('an audit label runs left when another pin sits on its line to the right', () => {
  const place = (slug: string) => ({ a: 'Droogdokkenpark', b: 'Park Spoor Noord' })[slug] ?? ''
  // vbw 580: fs 10, reach of a = 580/70 + 0.5 * 10 * 15 ≈ 83.3
  expect([...leftLabels([{ slug: 'a', x: 0, y: 0 }, { slug: 'b', x: 75, y: 0 }], place, 580)]).toEqual(['a'])
  expect([...leftLabels([{ slug: 'a', x: 0, y: 0 }, { slug: 'b', x: 75, y: 20 }], place, 580)]).toEqual([])
})

// golden values below are computed by running the old Atlas.jsx code
const close = (a: ViewBox, b: ViewBox) => { for (const k of ['x', 'y', 'w', 'h'] as const) expect(a[k]).toBeCloseTo(b[k], 6) }

test('861 wide is a desktop', () => {
  expect(freeArea({ w: 861, h: 1000 })).toEqual({ l: 376, t: 24, w: 413, h: 952 })
})

test('fitBox: no drawer on the phone, the padding, and the 24-unit floor', () => {
  const box = { x0: 0, y0: 0, x1: 100, y1: 100 }
  expect(fitBox({ w: 390, h: 800 }, box, 1, true)).toEqual(fitBox({ w: 390, h: 800 }, box))
  close(fitBox({ w: 1000, h: 800 }, box, 2), { x: -186.231884, y: -94.927536, w: 362.318841, h: 289.855072 })
  close(fitBox({ w: 1000, h: 800 }, { x0: 10, y0: 20, x1: 15, y1: 22 }), { x: -15.847826, y: 3.608696, w: 43.478261, h: 34.782609 })
})

test('clampView keeps the centre on a map that is not square', () => {
  // home's free middle is where the map's centre sits (here 0.6 of the view across and down): a pan keeps that point on
  // the map, so a corner of the map is the farthest it goes (round-2 re-check, 6 Oct 2026: it let the city leave the screen)
  const home = { x: 0, y: 0, w: 1000, h: 500 }
  expect(clampView({ x: -5000, y: -5000, w: 1000, h: 500 }, home, 1200, 600)).toEqual({ w: 1000, h: 500, x: -600, y: -300 })
  expect(clampView({ x: 5000, y: 5000, w: 1000, h: 500 }, home, 1200, 600)).toEqual({ w: 1000, h: 500, x: 600, y: 300 })
  expect(clampView({ x: 100, y: 50, w: 500, h: 250 }, home, 1200, 600)).toEqual({ w: 500, h: 250, x: 100, y: 50 })
})

test('a pan never takes the city out of the free part of the stage, at any zoom, on a laptop and a phone', () => {
  // the farthest pan in each direction still leaves at least half the free area's width and height (or half the map's,
  // when the map is smaller on screen) of city in the part of the stage the panels leave free
  const W = 1000, H = 700
  for (const size of [{ w: 1440, h: 900 }, { w: 390, h: 700 }, { w: 320, h: 216 }]) {
    const home = fitBox(size, { x0: 0, y0: 0, x1: W, y1: H }), free = freeArea(size)
    for (const zoom of [1.25, 1, 1 / 4, 1 / 28]) for (const [dx, dy] of [[-1, 0], [1, 0], [0, -1], [0, 1], [1, 1], [-1, -1]] as const) {
      const w = home.w * zoom, h = home.h * zoom
      const v = clampView({ x: dx * 1e6, y: dy * 1e6, w, h }, home, W, H)
      const s = size.w / v.w
      const mx0 = (0 - v.x) * s, mx1 = (W - v.x) * s, my0 = (0 - v.y) * s, my1 = (H - v.y) * s   // the map on screen
      const ox = Math.min(mx1, free.l + free.w) - Math.max(mx0, free.l), oy = Math.min(my1, free.t + free.h) - Math.max(my0, free.t)
      expect(ox, `${size.w}×${size.h} zoom ${zoom} pan ${dx},${dy}`).toBeGreaterThanOrEqual(Math.min(free.w, mx1 - mx0) / 2 - 1e-6)
      expect(oy, `${size.w}×${size.h} zoom ${zoom} pan ${dx},${dy}`).toBeGreaterThanOrEqual(Math.min(free.h, my1 - my0) / 2 - 1e-6)
    }
  }
})

test('a move that starts a little past the map is never pushed back across it, and goes no farther out', () => {
  const home = { x: 0, y: 0, w: 1000, h: 500 }   // the free middle at 0.6 across: x 600 puts it on the right edge (1200)
  const past = { x: 700, y: 0, w: 1000, h: 500 }  // a flight left it 100 past
  expect(clampView({ ...past, x: 900 }, home, 1200, 600, past).x).toBe(700)   // «right»: stays, no jump back
  expect(clampView({ ...past, x: 500 }, home, 1200, 600, past).x).toBe(500)   // «left»: moves
  expect(clampView({ ...past, x: 900 }, home, 1200, 600).x).toBe(600)         // with no start, the plain bound
})

test('placeLabels: a pin moves a name a line down; with no free line the name is left out; the width is 0.56 em a letter', () => {
  expect(placeLabels([{ name: 'Ab', x: 0, y: 0 }], [{ x: 0, y: 0 }], 10, 4, 'en')[0]!.y).toBeCloseTo(13.8, 6)
  expect(placeLabels([{ name: 'Ab', x: 0, y: 0 }], [0, 13.8, -13.8, 27.6, -27.6].map((y) => ({ x: 0, y })), 10, 4, 'en')).toEqual([])
  // 'Ab' at fs 10 is 11.2 wide: a pin of radius 4 at x 9.5 touches it, at 9.7 it does not
  expect(placeLabels([{ name: 'Ab', x: 0, y: 0 }], [{ x: 9.5, y: 0 }], 10, 4, 'en')[0]!.y).toBeCloseTo(13.8, 6)
  expect(placeLabels([{ name: 'Ab', x: 0, y: 0 }], [{ x: 9.7, y: 0 }], 10, 4, 'en')[0]!.y).toBe(0)
})

test('greenStep and barStyle at their edges', () => {
  expect(greenStep(0.3)).toBe(2)
  expect(greenStep(0.299)).toBe(1)
  expect(barStyle('heat', 0, [-1, 0, 2])).toEqual({ left: '50%', width: '0%' })
  expect(barStyle('heat', 1, [-1, 0, 2])).toEqual({ left: '50%', width: '25%' })
  expect(barStyle('heat', 0.5, [0.5, -0.25])).toEqual({ left: '50%', width: '25%' })   // the widest |value| is at least 1
  expect(barStyle('shops', 300, [300, 600])).toEqual({ left: 0, width: '50%' })
  expect(barStyle('r3', 0.4, [0.4, 0.9])).toEqual({ left: 0, width: '40%' })
})

test('leftLabels: a pin 1.2 lines off still shares the line (the limit is 1.4)', () => {
  const place = (slug: string) => ({ a: 'Droogdokkenpark', b: 'Park Spoor Noord' } as Record<string, string>)[slug]
  // vbw 580: fs 10, so 12 is 1.2 lines
  expect([...leftLabels([{ slug: 'a', x: 0, y: 0 }, { slug: 'b', x: 75, y: 12 }], place, 580)]).toEqual(['a'])
  expect([...leftLabels([{ slug: 'x', x: 0, y: 0 }, { slug: 'y', x: 8, y: 0 }], place, 580)]).toEqual(['x'])   // no place: the reach is vbw/70 = 8.29
})
