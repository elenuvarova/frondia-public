import type { Sector } from './types'

/* The verdict colours of a sector and their counts. Plain functions, no React: the server sections of
   the landing count with them (a 'use client' module cannot be called from the server), and
   SectorMap draws with them. */
export const GAIN = ['var(--gain-1)', 'var(--gain-2)', 'var(--gain-3)']
// Field under verdict fills. Checked, not eyeballed (25.09.2026): at 0.30 (multiply on paper) the
// field's darkest green stays lighter than the lightest fill (L* 79.7 vs 65.4), and the minimum
// CIEDE2000 between field and either ramp is 10.8 under normal, deutan, protan and tritan vision.
// Full strength (0.95) only where no verdict is drawn: the atlas field lens.
export const FIELD_UNDER_DATA = 0.3
export const LOSS = ['var(--loss-1)', 'var(--loss-2)', 'var(--loss-3)']

export type MapMode = 'raw' | 'effect' | 'field'
// the "sealed ground" lens reads bv/be, which lib/types.ts leaves in Sector's catch-all
type SealSector = Sector & { bv?: 'up' | 'down' | 'refused' | null; be?: number | null }

// Bins of the validated ramps: threshold, 2×, 3×.
function step(k: number): number { return k >= 3 ? 2 : k >= 2 ? 1 : 0 }

/** Colour of one sector.
 *  effect — the verdict of the layer (against 12 matched sectors);
 *  raw    — the same threshold applied to before/after change alone;
 *  field  — no fill, the satellite field shows through. */
export function fillFor(s: Sector, mode: MapMode, thr: number): string | null {
  if (mode === 'effect') {
    if (s.nv === 'refused') return 'url(#hatch)'
    if (s.nv !== 'up' && s.nv !== 'down') return null
    return (s.nv === 'up' ? GAIN : LOSS)[step(Math.abs(s.ne ?? 0) / thr)]!
  }
  if (mode === 'raw') {
    if (!s.cmp || s.raw == null) return null
    const k = Math.abs(s.raw) / thr
    if (k < 1) return null
    return (s.raw > 0 ? GAIN : LOSS)[step(k)]!
  }
  return null
}

/** Sealed ground (built-up class against the same matched places): more built-up beyond noise takes
 *  the loss ramp, less (unsealed) the gain ramp, as France's artificialisation maps colour them. */
export function builtFill(s: SealSector, thr: number): string | null {
  if (s.bv === 'refused') return 'url(#hatch)'
  if (s.bv !== 'up' && s.bv !== 'down') return null
  return (s.bv === 'up' ? LOSS : GAIN)[step(Math.abs(s.be ?? 0) / thr)]!
}

export function countFor(sectors: Sector[], mode: 'effect', thr: number): { up: number; down: number } {
  let up = 0, down = 0
  for (const s of sectors) {
    const f = fillFor(s, mode, thr)
    if (!f || f.startsWith('url')) continue
    if (mode === 'effect' ? s.nv === 'up' : (s.raw ?? 0) > 0) up++
    else down++
  }
  return { up, down }
}
