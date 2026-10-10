import { signed, type Locale } from '@/lib/format'
import type { getT } from '@/lib/t'
import { plain } from '@/lib/typography'

// the shape a case's series actually carries (site_data.py / scripts/report); lib/types.ts'
// Case.series leaves season items typed as `{ effect: number; [k: string]: unknown }` — the season
// number and the optional scene count are typed here, since only this chart reads them
export interface SeriesSeason { season: number; effect: number; scenes?: number }
export interface SeriesData { threshold: number; seasons: SeriesSeason[] }

export interface SeriesProps {
  series: SeriesData
  // a server component, so not under the provider: the server parent passes getT('common') (its t and
  // rich already tie the words), and the chart reads common.charts.series.*
  i18n: Pick<Awaited<ReturnType<typeof getT>>, 't' | 'rich'>
  height?: number
  night?: boolean
  completed?: string | number
  loc: Locale
}

/** Effect of one intervention, summer by summer, against the same named controls.
 *  The grey band is the noise (± audit threshold). Filled dot = beyond it. */
export function Series({ series, i18n, height = 120, night = false, completed, loc }: SeriesProps) {
  if (!series.seasons?.length) return null
  const pts = [...series.seasons].sort((a, b) => a.season - b.season)
  const thr = series.threshold
  const W = 420, H = height, padL = 4, padR = 4, padT = 10, padB = 20
  const ys = pts.map((p) => p.effect)
  const lo = Math.min(-thr * 1.4, ...ys), hi = Math.max(thr * 2, ...ys) * 1.08
  const s0 = Math.min(...pts.map((p) => p.season)), s1 = Math.max(...pts.map((p) => p.season))
  const x = (s: number) => padL + ((s - s0) / Math.max(1, s1 - s0)) * (W - padL - padR)
  const y = (v: number) => padT + (1 - (v - lo) / (hi - lo)) * (H - padT - padB)
  // a missing summer breaks the line: joining across it would draw a value for a year with no data
  const line = pts.map((p, k) => `${k && p.season - pts[k - 1]!.season === 1 ? 'L' : 'M'}${x(p.season).toFixed(1)},${y(p.effect).toFixed(1)}`).join(' ')
  const missing: number[] = []
  for (let k = 1; k < pts.length; k++) for (let s = pts[k - 1]!.season + 1; s < pts[k]!.season; s++) missing.push(s)
  const above = pts.filter((p) => p.effect > thr).length

  return (
    <figure className={`series ${night ? 'series--night' : ''}`}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img"
           aria-label={plain(i18n.t('charts.series.aria', { from: String(s0), to: String(s1), above: String(above), n: String(pts.length) }))}>
        <rect x="0" y={y(thr)} width={W} height={y(-thr) - y(thr)} className="series-band" />
        <line x1="0" x2={W} y1={y(0)} y2={y(0)} className="series-zero" />
        <path d={line} className="series-line" />
        {pts.map((p) => (
          <circle key={p.season} cx={x(p.season)} cy={y(p.effect)} r="3.6"
                  className={p.effect > thr ? 'series-dot on' : 'series-dot'}>
            <title>{i18n.t('charts.series.point', { season: String(p.season), effect: signed(p.effect, 3, loc), scenes: p.scenes ? String(p.scenes) : 'none' })}</title>
          </circle>
        ))}
        {/* the summers the text talks about are the ones in the noise and the missing ones: they carry
            their year on the chart (a noise year under its dot, a missing year on the axis row where
            the line breaks), so a touch or keyboard reader does not need the hover title */}
        {pts.filter((p) => p.effect <= thr && p.season !== s0 && p.season !== s1).map((p) => (
          <text key={`y${p.season}`} x={x(p.season)} y={Math.min(H - padB + 2, y(p.effect) + 15)} className="series-year" textAnchor="middle">{p.season}</text>
        ))}
        {missing.filter((m) => m !== s0 && m !== s1).map((m) => (
          <text key={`m${m}`} x={x(m)} y={H - 4} className="series-year series-year--gap" textAnchor="middle">{m}</text>
        ))}
        <text x={x(s0)} y={H - 4} className="series-axis">{s0}</text>
        <text x={x(s1)} y={H - 4} className="series-axis" textAnchor="end">{s1}</text>
      </svg>
      <figcaption className="mono">
        {/* 'none' is the catalogue's "no such part" (a select, not an empty string) */}
        {i18n.rich('charts.series.caption', {
          above: String(above), n: String(pts.length), from: String(s0), to: String(s1), opened: completed ? String(completed) : 'none',
          gap: missing.length > 0 ? missing.join(i18n.t('sep.list')) : 'none', b: (c) => <b>{c}</b>,
        })}
      </figcaption>
    </figure>
  )
}
