'use client'
import { useEffect, useRef, useState } from 'react'
import { fixed, signed, type Locale } from '@/lib/format'
import { useT } from '@/lib/t-client'
import { plain } from '@/lib/typography'

// the shape city.hist actually carries (site_data.py); lib/types.ts leaves City.hist as unknown
// since only this chart reads it
export interface Hist { raw: number[]; effect: number[]; n: number; hi: number; lo: number }

// Bars carry real geometry (y/height), tweened in JS — not CSS transforms — so any
// renderer that reads the DOM (print, Figma capture) sees the true distribution.
function useTween(target: number[], ms = 700): number[] {
  const [v, setV] = useState(target)
  const cur = useRef(target)
  useEffect(() => {
    const from = cur.current
    if (from === target || matchMedia('(prefers-reduced-motion: reduce)').matches) { cur.current = target; setV(target); return }
    const t0 = performance.now()
    let raf: number
    const step = (now: number) => {
      const t = Math.min(1, (now - t0) / ms), k = 1 - Math.pow(1 - t, 3)
      const next = target.map((x, i) => (from[i] ?? 0) + (x - (from[i] ?? 0)) * k)
      cur.current = t < 1 ? next : target
      setV(cur.current)
      if (t < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [target, ms])
  return v
}

interface NullHistogramProps {
  hist: Hist
  thr: number
  mode?: 'raw' | 'effect'
  height?: number
  marker?: { value: number; label: string }
  compact?: boolean
  night?: boolean
  showAxis?: boolean
  label?: string     // the page's own name for the chart; without it, common.charts.hist
  width?: number
  invert?: boolean   // a measure where growth is the loss (built-up ground): the ramps swap sides
  loc: Locale        // the page's language: decimal separators of the axis and the marker
}

/** The legend is the noise itself: the distribution of effects the method finds
 *  where nothing happened, with the threshold marked. In `raw` mode the same bins
 *  hold before/after change without a control — the whole city slides right. */
export function NullHistogram({
  hist, thr, mode = 'effect', height = 150, marker, compact = false, night = false,
  showAxis = true, label, width = 600,
  invert = false, loc,
}: NullHistogramProps) {
  const { t } = useT('common')
  const target = mode === 'raw' ? hist.raw : hist.effect
  const counts = useTween(target)
  const max = Math.max(...hist.effect, ...hist.raw)
  const W = width
  // compact charts render at ~40% scale: larger axis type in user units, so it reads at 12 px
  const padB = showAxis ? (compact ? 40 : 26) : 4
  const H = height
  const plotH = H - padB - 6
  const bw = W / hist.n
  const w = (hist.hi - hist.lo) / hist.n
  const x = (v: number) => ((v - hist.lo) / (hist.hi - hist.lo)) * W
  const ramp = (c: number) => {
    const k = Math.abs(c) / thr
    if (k < 1) return night ? 'var(--night-ink-3)' : 'var(--noise-bar)'
    const i = k >= 3 ? 2 : k >= 2 ? 1 : 0
    return (invert ? c < 0 : c > 0) ? ['var(--gain-1)', 'var(--gain-2)', 'var(--gain-3)'][i] : ['var(--loss-1)', 'var(--loss-2)', 'var(--loss-3)'][i]
  }
  const total = target.reduce((a, b) => a + b, 0)
  // a narrow chart has no room beside the arrow: the label moves above the plot, clear of the
  // dashed threshold line it used to sit on (review, 26 Sep, a 390-px phone)
  const labelAbove = W < 600
  const showLabel = marker && marker.value > hist.hi && !compact

  return (
    <figure className={`hist ${compact ? 'hist--compact' : ''} ${night ? 'hist--night' : ''} ${showLabel && labelAbove ? 'hist--label-above' : ''}`}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img"
           aria-label={plain(label || t('charts.hist', { n: String(total), thr: fixed(thr, 3, loc) }))}>
        {/* noise band */}
        <rect x={x(-thr)} y="0" width={x(thr) - x(-thr)} height={plotH + 6} className="hist-band" />
        {counts.map((c, i) => {
          const centre = hist.lo + (i + 0.5) * w
          // a bin that is non-empty in the target never shrinks below 2 units: the tails beyond the
          // threshold are the point. Keyed on the target, not the tweened value, so a bin on its way
          // to zero does not leave a 2-unit stub for the whole tween.
          const h = max && (target[i] ?? 0) > 0 ? Math.max(2, (c / max) * plotH) : (max ? (c / max) * plotH : 0)
          return (
            <rect key={i} className="hist-bar" x={i * bw + 0.8} width={Math.max(0.5, bw - 1.6)}
                  y={6 + plotH - h} height={h} fill={ramp(centre)} />
          )
        })}
        {[-thr, thr].map((t, i) => (
          <line key={i} x1={x(t)} x2={x(t)} y1="0" y2={plotH + 6} className="hist-thr" />
        ))}
        <line x1={x(0)} x2={x(0)} y1={plotH + 6} y2={plotH + 11} className="hist-tick" />
        {showAxis && (
          <g className="hist-axis">
            <text x={x(-thr)} y={H - 6} textAnchor="middle">{signed(-thr, 3, loc)}</text>
            <text x={x(0)} y={H - 6} textAnchor="middle" className="zero">0</text>
            <text x={x(thr)} y={H - 6} textAnchor="middle">{signed(thr, 3, loc)}</text>
          </g>
        )}
        {marker && marker.value > hist.hi && (
          <g className="hist-marker">
            <line x1={W - 70} x2={W - 4} y1="42" y2="42" />
            <path d={`M${W - 10},37 L${W - 3},42 L${W - 10},47`} />
          </g>
        )}
      </svg>
      {showLabel && (
        <figcaption className="hist-marker-label mono"
                    style={labelAbove ? { top: 0, transform: 'translateY(calc(-100% - 6px))' } : { top: `${(34 / H) * 100}%` }}>
          {marker.label} <b>{signed(marker.value, 3, loc)}</b> →
        </figcaption>
      )}
    </figure>
  )
}
