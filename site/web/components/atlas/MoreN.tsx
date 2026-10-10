'use client'
import type { CSSProperties } from 'react'
import { int, pct } from '@/lib/format'
import type { AtlasCity, AtlasPoints, PointType } from '@/lib/atlas/types'
import { moreWho } from '@/lib/atlas/words'
import { useT } from '@/lib/t-client'
import { plain } from '@/lib/typography'

/* ── what if N more? (phase 2): the planner's coverage after each rank ─────────────────────────
   The value above the slider and the result under it, as Dub's calculator sets them; the curve is the
   context of the choice, as Mixpanel draws the volume you pick: the area up to N is filled, a marker
   stands at N, and a dashed line marks the ten named on 5 September (Mixpanel's "Recommended").
   (Atlas.jsx 433–474) */

// path coordinates to a tenth of a unit (geometry, not a number anyone reads)
const c1 = (v: number) => Math.round(v * 10) / 10

export function CoverageCurve({ steps, k, named = 10 }: { steps: number[]; k: number; named?: number }) {
  const W = 235, H = 64, lo = steps[0]!, hi = steps[steps.length - 1] || lo + 0.01
  const x = (i: number) => (i / (steps.length - 1)) * W
  const y = (v: number) => H - 4 - ((v - lo) / (hi - lo || 1)) * (H - 10)
  const line = steps.map((v, i) => `${i ? 'L' : 'M'}${c1(x(i))},${c1(y(v))}`).join('')
  const area = `M0,${H}` + steps.slice(0, k + 1).map((v, i) => `L${c1(x(i))},${c1(y(v))}`).join('') + `L${c1(x(k))},${H}Z`
  return (
    <svg className="more-curve" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
      {k > 0 && <path d={area} className="more-curve-area" />}
      <path d={line} className="more-curve-line" vectorEffect="non-scaling-stroke" />
      <line x1={x(named)} x2={x(named)} y1="0" y2={H} className="more-curve-named" vectorEffect="non-scaling-stroke" />
      <line x1={x(k)} x2={x(k)} y1="0" y2={H} className="more-curve-mark" vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

export function MoreN({ city, points, t: type, n, setN }: { city: AtlasCity; points: AtlasPoints; t: PointType; n: number; setN: (n: number) => void }) {
  const { t, loc } = useT('atlas')
  const steps = type.steps
  if (!steps) return null
  const k = Math.max(0, Math.min(n, steps.length - 1))
  const byId = new Map(city.sectors.map((s) => [s.id, s]))
  const cut = city.equity?.income_cuts?.[0]
  const first = points.points.filter((p) => p.t === type.key && p.r <= k && p.s && byId.get(p.s)?.inc != null)
  const poor = first.filter((p) => (byId.get(p.s)!.inc as number) <= (cut as number)).length
  const euro = t('equity.money', { v: int(cut, loc) })
  return (
    <div className="more-n">
      <p className="label more-title">{t('more.title', { k: String(k) })}</p>
      <input type="range" className="more-range" min="0" max={steps.length - 1} step="1" value={k}
             onChange={(e) => setN(Number(e.target.value))} aria-label={plain(t('more.slider'))}
             aria-valuetext={plain(t('more.valueText', { k: String(k), p: pct(steps[k], 0, loc) }))} />
      <p className="more-read"><b className="num-m">{pct(steps[0], 0, loc)} → {pct(steps[k], 0, loc)}</b><span>{t('more.read')}</span></p>
      <div className="more-chart">
        <CoverageCurve steps={steps} k={k} />
        {/* the tag sits on the side of the dashed line away from the marker, so the two never cross */}
        <span className={`more-named-tag mono${k > 10 ? ' is-left' : ''}`} style={{ '--at': `${(100 * 10) / (steps.length - 1)}%` } as CSSProperties} aria-hidden="true">{t('more.named')}</span>
      </div>
      <p className="more-ends mono" aria-hidden="true"><span>{t('more.today')}</span><span>{t('more.all', { n: String(steps.length - 1) })}</span></p>
      <p className="small">{moreWho(t, k, poor, euro)}</p>
    </div>
  )
}
