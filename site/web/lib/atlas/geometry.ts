// The atlas map's geometry, ported from site/apps/atlas/src/pages/Atlas.jsx without changing the arithmetic. Pure.
import type { Locale } from '@/lib/format'
import { placeName } from '@/lib/names'

export interface Box { x0: number; y0: number; x1: number; y1: number }
export interface ViewBox { x: number; y: number; w: number; h: number }
export interface Size { w: number; h: number }
export interface Free { l: number; t: number; w: number; h: number }

const PHONE = 860   // the CSS's phone is max-width: 860px

// every coordinate pair of an SVG path (Atlas.jsx:130–138); null for a path with no coordinates, so a caller skips it
// (the old code threw on one)
export function bbox(d: string): Box | null {
  const m = d.match(/-?\d+(\.\d+)?/g)
  if (!m) return null
  const nums = m.map(Number)
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity
  for (let i = 0; i < nums.length; i += 2) {
    x0 = Math.min(x0, nums[i]!); x1 = Math.max(x1, nums[i]!)
    y0 = Math.min(y0, nums[i + 1]!); y1 = Math.max(y1, nums[i + 1]!)
  }
  return { x0, y0, x1, y1 }
}

// the part of the stage the panels leave free (Atlas.jsx:40–45)
export function freeArea(size: Size): Free {
  const mobile = size.w <= PHONE
  const l = mobile ? 12 : 376, r = mobile ? 12 : 72, t = mobile ? 56 : 24, b = mobile ? size.h * 0.46 : 24
  return { l, t, w: Math.max(80, size.w - l - r), h: Math.max(80, size.h - t - b) }
}

// `drawer`: a card is open on the right, keep the target out from under it (Atlas.jsx:48–55)
export function fitBox(size: Size, b: Box, pad = 1, drawer = false): ViewBox {
  const free = freeArea(size)
  const fw = drawer && size.w > PHONE ? Math.max(80, free.w - 332) : free.w
  const bw = Math.max(24, (b.x1 - b.x0) * pad), bh = Math.max(24, (b.y1 - b.y0) * pad)
  const s = Math.min(fw / bw, free.h / bh)
  const cx = (b.x0 + b.x1) / 2, cy = (b.y0 + b.y1) / 2
  return { x: cx - (free.l + fw / 2) / s, y: cy - (free.t + free.h / 2) / s, w: size.w / s, h: size.h / s }
}

// zoom between 1/28 and 1.25 of home (Atlas.jsx:61–67), and the middle of the free area kept on the map. Home puts the
// map's centre in the middle of the part of the stage the panels leave free, so that point's place in the view (fx, fy)
// is read from home; a pan, a drag or a zoom about the pointer stops when a corner of the map reaches it, and the city
// always fills at least a quarter of the free area or half its own size there. Before the round-2 re-check (6 Oct 2026)
// the view's corner could go a whole view past the map, and 30 presses of a pan key took the city off the screen.
// `from`, the view a move starts from: a flight to a place on the map's edge beside an open card can end with that point
// a little past the map; a move from there is never pushed back across it (a press of «right» would jump the map left)
export function clampView(v: ViewBox, home: ViewBox, W: number, H: number, from?: ViewBox): ViewBox {
  const w = Math.min(home.w * 1.25, Math.max(home.w / 28, v.w)), k = w / v.w
  const h = v.h * k
  const cx = v.x + v.w / 2, cy = v.y + v.h / 2
  const fx = (W / 2 - home.x) / home.w, fy = (H / 2 - home.y) / home.h
  const fa = from ? [from.x + fx * from.w, from.y + fy * from.h] : [W / 2, H / 2]
  const ax = Math.min(Math.max(W, fa[0]!), Math.max(Math.min(0, fa[0]!), cx - w / 2 + fx * w))
  const ay = Math.min(Math.max(H, fa[1]!), Math.max(Math.min(0, fa[1]!), cy - h / 2 + fy * h))
  return { w, h, x: ax - fx * w, y: ay - fy * h }
}

// commune names: the larger commune is placed first; a name that would touch a placed name or a registered pin
// moves up or down by a line, and one with no free place is left out (Atlas.jsx:534–546). The width is the name's in the
// page's language (a Dutch name is often longer: Sint-Agatha-Berchem)
export function placeLabels<T extends { x: number; y: number; name: string; name_nl?: string; name_fr?: string; area?: number }>(
  list: T[], pins: { x: number; y: number }[], fs: number, pinR: number, loc: Locale,
): T[] {
  const placed: T[] = []
  const boxes: Box[] = pins.map((p) => ({ x0: p.x - pinR, x1: p.x + pinR, y0: p.y - pinR, y1: p.y + pinR }))
  const hit = (b: Box) => boxes.some((o) => b.x0 < o.x1 && b.x1 > o.x0 && b.y0 < o.y1 && b.y1 > o.y0)
  for (const c of [...list].sort((a, b) => (b.area || 0) - (a.area || 0))) {
    const w = placeName(c, loc).length * fs * 0.56, h = fs * 1.2
    for (const dy of [0, 1.15, -1.15, 2.3, -2.3]) {
      const y = c.y + dy * h
      const b = { x0: c.x - w / 2, x1: c.x + w / 2, y0: y - h / 2, y1: y + h / 2 }
      if (!hit(b)) { boxes.push(b); placed.push({ ...c, y }); break }
    }
  }
  return placed
}

// the green share's class in the five ColorBrewer greens (Atlas.jsx:529)
export const greenStep = (g: number | null | undefined): number | null =>
  g == null ? null : g < 0.15 ? 0 : g < 0.3 ? 1 : g < 0.45 ? 2 : g < 0.6 ? 3 : 4

// a list bar: heat diverges from the city median, the rest grow from the left (Atlas.jsx:305–313)
export function barStyle(lens: string, v: number, vals: number[]): { left: string | number; width: string } {
  if (lens === 'heat') {
    const m = Math.max(1, ...vals.map(Math.abs))
    const w = (50 * Math.abs(v)) / m
    return { left: `${v >= 0 ? 50 : 50 - w}%`, width: `${w}%` }
  }
  const top = lens === 'services' ? 100 : lens === 'shops' ? Math.max(...vals) : 1
  return { left: 0, width: `${(100 * v) / top}%` }
}

// an audit's label runs right of its pin, unless another pin sits on that line of text; the sizes follow the
// zoom (Atlas.jsx:947–954). `place` gives the label's text for a slug
export function leftLabels(cases: { slug: string; x: number; y: number }[], place: (slug: string) => string | undefined, vbw: number): Set<string> {
  const fs = vbw / 58, out = new Set<string>()
  for (const a of cases) {
    const reach = vbw / 70 + 0.5 * fs * (place(a.slug)?.length || 0)
    if (cases.some((b) => b !== a && b.x > a.x && b.x - a.x < reach && Math.abs(b.y - a.y) < 1.4 * fs)) out.add(a.slug)
  }
  return out
}
