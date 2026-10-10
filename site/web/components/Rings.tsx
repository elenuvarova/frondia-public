'use client'
import { useEffect, useMemo, useRef, useState } from 'react'
import { fixed, signed } from '@/lib/format'
import { count } from '@/lib/icu'
import { sectorName } from '@/lib/names'
import { simplex3 } from '@/lib/noise'
import { useT } from '@/lib/t-client'
import { plain } from '@/lib/typography'

/** One audit as a cross-section of a trunk.
 *
 *  The pith is the place when the works were done; every ring after it is one summer.
 *  A ring's width is that summer's effect against the same twelve matched places, at one
 *  scale for every case (`unit`, px per unit of vegetation index) — so a bigger disc means a
 *  bigger or longer effect, not a bigger picture. Solid ring: beyond the audit threshold.
 *  Dashed: inside the noise. Two marks come from dendrochronology itself (A. E. Douglass's
 *  skeleton plots): a summer missing from the series is an absent ring — dotted, with two
 *  offset dots — and a documented disturbance (works on the site) is a scar, a ring broken
 *  where it was cut. The twelve dots on the pith are the matched places: the reference
 *  chronology every ring is cross-dated against.
 *
 *  Motion follows the method: rings inside the noise keep moving, rings beyond it stay still.
 *  Reduced motion: one still frame. */

// the shape a case actually carries (site_data.py); lib/types.ts' Case leaves season items and
// controls typed loosely (`{ effect: number; [k: string]: unknown }`, `unknown[]`) — the fields
// this chart reads are typed here, since only Rings reads them
export interface RingNote { kind?: string; text: string }
interface RingSeason { season: number; effect: number; scenes?: number }
interface RingControl { id?: string; name: string; name_nl?: string; name_fr?: string; dist_km?: number }
export interface RingsCase {
  completed: string | number
  series: { threshold: number; seasons: RingSeason[] }
  controls?: RingControl[]
}
type RingKind = 'up' | 'down' | 'noise' | 'scar'
type RingGroup =
  | { year: number; kind: 'absent'; note?: RingNote }
  | { year: number; kind: RingKind; effect: number; k: number; scenes?: number; note?: RingNote }

const STEPS = 200
// split a tag into short lines for the narrow tag column
const wrap = (s: string, n: number): string[] => s.split(' ').reduce<string[]>((ls, w) => {
  const last = ls[ls.length - 1]
  if (last && (last + ' ' + w).length <= n) ls[ls.length - 1] = last + ' ' + w
  else ls.push(w)
  return ls
}, [])
const TAU = Math.PI * 2

export function ringsOf(c: RingsCase, notes: Record<number, RingNote> = {}): RingGroup[] {
  const thr = c.series.threshold
  const by = new Map(c.series.seasons.map((p) => [p.season, p]))
  const ys = c.series.seasons.map((p) => p.season)
  const out: RingGroup[] = []
  for (let y = Math.min(...ys); y <= Math.max(...ys); y++) {
    const p = by.get(y), note = notes[y]
    if (!p) { out.push({ year: y, kind: 'absent', note }); continue }
    const kind: RingKind = note?.kind === 'scar' ? 'scar' : p.effect > thr ? 'up' : p.effect < -thr ? 'down' : 'noise'
    out.push({ year: y, kind, effect: p.effect, k: p.effect / thr, scenes: p.scenes, note })
  }
  return out
}

/** Total effect a disc has to hold — used by a plate to pick one `unit` for all its discs. */
export const ringsSpan = (c: RingsCase): number => c.series.seasons.reduce((a, p) => a + Math.max(0, p.effect), 0)

function useInView(ref: React.RefObject<Element | null>): boolean {
  const [on, setOn] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el || typeof IntersectionObserver === 'undefined') { setOn(true); return }
    const io = new IntersectionObserver(([e]) => setOn(!!e?.isIntersecting), { rootMargin: '80px' })
    io.observe(el)
    return () => io.disconnect()
  }, [ref])
  return on
}

interface RingsProps {
  c: RingsCase
  place: string
  notes?: Record<number, RingNote>
  unit?: number
  pith?: number
  minW?: number
  aspect?: number
  size?: number
  night?: boolean
  animate?: boolean
  seed?: number
  tags?: boolean
  wood?: boolean
  label?: string
  mono?: boolean
  ruler?: boolean
}

export function Rings({
  c, place, notes = {}, unit = 90, pith = 24, minW = 2.6, aspect = 1, size = 360,
  night = false, animate = true, seed = 7, tags = true, wood = true, label,
  mono = false, ruler = false,
}: RingsProps) {
  const { t: tr, loc } = useT('common')
  const rings = useMemo(() => ringsOf(c, notes), [c, notes])
  const N = useMemo(() => simplex3(seed), [seed])
  const thr = c.series.threshold
  // reduced motion and a Figma capture (#figmacapture) freeze the rings at their final state; both
  // read the browser, so the server (and the client's first paint) always assume neither — the
  // effect below corrects it once mounted, the same timing PhotoRustle uses for its phone frame
  const [envStill, setEnvStill] = useState(false)
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches || location.hash.includes('figmacapture')) setEnvStill(true)
  }, [])
  const still = !animate || envStill

  // radii: cumulative widths out from the pith
  const radii = useMemo(() => {
    let r = pith
    return rings.map((g) => {
      const w = g.kind === 'absent' ? 0 : Math.max(minW, Math.max(0, g.effect) * unit)
      r += w
      return r
    })
  }, [rings, unit, pith, minW])
  const R = radii.length ? radii[radii.length - 1]! : pith

  const tagged = tags ? rings.map((g, i) => ({ g, i })).filter(({ g }) => g.note) : []
  // the tag column is reserved whether or not this case has notes: discs on one plate keep one scale
  const tagW = tags ? 150 : 0
  const pad = 14
  const W = size + tagW, H = Math.round(size * Math.max(1, aspect))
  const cx = size / 2, cy = H / 2

  // grow in once, when first seen; then let the noise rings move while visible
  const ref = useRef<HTMLElement>(null)
  const inView = useInView(ref)
  const [shown, setShown] = useState(still ? rings.length : 0)
  useEffect(() => {
    if (still || !inView || shown >= rings.length) return
    const t = setTimeout(() => setShown((n) => n + 1), 90)
    return () => clearTimeout(t)
  }, [still, inView, shown, rings.length])
  // once the environment turns out to prefer reduced motion (known only after mount), jump
  // straight to the final state instead of playing out the reveal that had already started
  useEffect(() => { if (still) setShown(rings.length) }, [still, rings.length])
  const [t, setT] = useState(0)
  const moving = !still && inView && rings.some((g) => g.kind === 'noise')
  useEffect(() => {
    if (!moving) return
    let raf = 0, last = 0
    const tick = (now: number) => {
      if (now - last > 42) { setT(now / 1000); last = now }   // ~24 fps is plenty for a wobble
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [moving])

  // the trunk's own shape, shared by every ring (rings in wood run roughly parallel)
  const trunk = (co: number, si: number): number => 1 + 0.055 * N(co * 0.8 + 11, si * 0.8 + 11, 3.1) + 0.02 * N(co * 2.1, si * 2.1, 8.7)
  const point = (r: number, th: number, i: number, amp: number, z: number): [number, number] => {
    const co = Math.cos(th), si = Math.sin(th)
    const wob = amp * (0.7 * N(co * 2 + 3, si * 2 + 3, i * 0.37 + z) + 0.3 * N(co * 6, si * 6, i * 0.91 + z * 1.7))
    const rr = r * trunk(co, si) + wob
    return [cx + rr * co, cy + rr * si * aspect]
  }
  const pathOf = (r: number, i: number, amp: number, z: number, from = 0, to = TAU): string => {
    const n = Math.max(8, Math.round((STEPS * (to - from)) / TAU))
    let d = ''
    for (let s = 0; s <= n; s++) {
      const [x, y] = point(r, from + ((to - from) * s) / n, i, amp, z)
      d += `${s ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`
    }
    return to - from >= TAU - 1e-6 ? d + 'Z' : d
  }

  const AMP: Record<'up' | 'noise' | 'absent' | 'scar' | 'down', number> = { up: 0.55, noise: 2.4, absent: 0, scar: 0.55, down: 0.55 }
  const SCAR: [number, number] = [-0.95, -0.35]        // where a scar cuts the ring (upper right), radians
  const TAG_AT = -0.6                         // where tag leaders touch their ring

  const els = rings.slice(0, shown).map((g, i) => {
    const r = radii[i]!, z = g.kind === 'noise' ? t * 0.35 : 0
    // 'none' is the catalogue's "no such part" (a select, not an empty string)
    const note = g.note ? g.note.text : 'none'
    const tip = g.kind === 'absent'
      ? tr('charts.rings.absent', { year: String(g.year), note })
      : tr('charts.rings.ring', {
        year: String(g.year), effect: signed(g.effect, 3, loc), beyond: g.k >= 1 ? 'yes' : 'no', k: fixed(g.k, 1, loc),
        scenes: g.scenes ? String(g.scenes) : 'none', note,
      })
    const weight = g.kind === 'up' ? (g.k >= 3 ? 2.3 : g.k >= 2 ? 1.7 : 1.2) : 1
    const annulus = wood && g.kind === 'up' && i > -1
      ? pathOf(r, i, AMP.up, 0) + (i ? pathOf(radii[i - 1]!, i - 1, AMP[rings[i - 1]!.kind] ?? 0.55, 0) : pathOf(pith, -1, 0, 0))
      : null
    if (g.kind === 'absent') {
      const [x1, y1] = point(r, TAG_AT + 0.25, i, 0, 0), [x2, y2] = point(r + 4, TAG_AT + 0.33, i, 0, 0)
      return (
        <g key={g.year} className="ring ring--absent">
          <title>{tip}</title>
          <path d={pathOf(r, i, 0, 0)} />
          <circle cx={x1} cy={y1} r="1.6" /><circle cx={x2} cy={y2} r="1.6" />
        </g>
      )
    }
    if (g.kind === 'scar') {
      const [a, b] = SCAR
      return (
        <g key={g.year} className="ring ring--scar">
          <title>{tip}</title>
          <path d={pathOf(r, i, AMP.scar, 0, b, a + TAU)} style={{ strokeWidth: 1.4 }} />
          {/* callus: the ends of a cut ring curl inward */}
          <path d={pathOf(r - 3, i, 0, 0, b - 0.02, b + 0.07)} /><path d={pathOf(r - 3, i, 0, 0, a - 0.07, a + 0.02)} />
        </g>
      )
    }
    return (
      <g key={g.year} className={`ring ring--${g.kind}`}>
        <title>{tip}</title>
        {annulus && <path d={annulus} className={`ring-wood k${g.k >= 3 ? 3 : g.k >= 2 ? 2 : 1}`} fillRule="evenodd" />}
        <path d={pathOf(r, i, AMP[g.kind], z)} style={{ strokeWidth: weight }} />
      </g>
    )
  })

  // twelve matched places as dots on the pith: the reference chronology
  const ctrl = (c.controls || []).slice(0, 12)
  const dots = ctrl.map((x, k) => {
    const th = (k / Math.max(1, ctrl.length)) * TAU - Math.PI / 2
    const [px, py] = point(pith, th, -1, 0, 0)
    return <circle key={x.id || k} cx={px} cy={py} r="2" className="ring-ctrl"><title>{tr('charts.rings.control', { k: String(k + 1), name: sectorName({ n: x.name, n_nl: x.name_nl, n_fr: x.name_fr }, loc), km: x.dist_km == null ? 'none' : fixed(x.dist_km, 1, loc) })}</title></circle>
  })

  const above = rings.filter((g) => g.kind === 'up').length
  const summers = rings.filter((g) => g.kind !== 'absent').length
  const aria = label || tr('charts.rings.aria', { place, summers: count(summers), completed: String(c.completed), above: String(above), n: String(ctrl.length), thr: fixed(thr, 3, loc) })

  return (
    <figure ref={ref} className={`rings ${night ? 'rings--night' : ''} ${mono ? 'rings--mono' : ''}`}>
      <svg viewBox={`${-pad} ${-pad} ${W + 2 * pad} ${H + 2 * pad}`} role="img" aria-label={plain(aria)}>
        <path d={pathOf(pith, -1, 0, 0)} className="ring-pith" />
        {dots}
        {els}
        <text x={cx} y={cy + 4} textAnchor="middle" className="ring-year ring-year--pith">{c.completed}</text>
        {shown >= rings.length && rings.length > 0 && (() => {
          const [lx, ly] = point(R + 6, Math.PI / 2, rings.length - 1, 0, 0)
          return <text x={lx} y={ly + 12} textAnchor="middle" className="ring-year">{rings[rings.length - 1]!.year}</text>
        })()}
        {ruler && shown >= rings.length && (() => {
          const TH = 0.42
          const [x0, y0] = point(pith, TH, -1, 0, 0), [x1, y1] = point(R + 26, TH, rings.length - 1, 0, 0)
          return (
            <g className="ring-ruler">
              <path d={`M${x0.toFixed(1)},${y0.toFixed(1)} L${x1.toFixed(1)},${y1.toFixed(1)}`} />
              {rings.map((g, i) => {
                if (g.kind === 'absent' || i % 2) return null
                const [px, py] = point(radii[i]!, TH, i, 0, 0)
                return <text key={g.year} x={px + 6} y={py + 3}>{fixed(g.effect, 3, loc)}</text>
              })}
            </g>
          )
        })()}
        {shown >= rings.length && tagged.map(({ g, i }, n) => {
          const [ax, ay] = point(radii[i]!, TAG_AT + n * 0.22, i, 0, 0)
          const ty = pad + 8 + n * 52, tx = size + 12
          return (
            <g key={g.year} className="ring-tag">
              <path d={`M${ax.toFixed(1)},${ay.toFixed(1)} L${(tx - 8).toFixed(1)},${ty.toFixed(1)} L${tx - 2},${ty}`} />
              <circle cx={ax} cy={ay} r="2.2" />
              <text x={tx} y={ty + 4}>
                <tspan className="ring-tag-year">{g.year}</tspan>
                {wrap(g.note!.text, 22).map((ln, k) => <tspan key={k} x={tx} dy={k ? 14 : 15}>{ln}</tspan>)}
              </text>
            </g>
          )
        })}
      </svg>
    </figure>
  )
}
