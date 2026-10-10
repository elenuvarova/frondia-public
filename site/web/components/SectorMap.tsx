'use client'
import { memo, useEffect, useId, useMemo, useRef, useState, type CSSProperties, type ReactNode, type Ref, type SVGProps } from 'react'
import type { City, Sector } from '@/lib/types'
import { FIELD_UNDER_DATA, fillFor, type MapMode } from '@/lib/verdict'
import { plain } from '@/lib/typography'

// the colours live in lib/verdict (server code counts with them); client code may import them here too
export { FIELD_UNDER_DATA, GAIN, LOSS, builtFill, countFor, fillFor } from '@/lib/verdict'

// showCases draws the audited cases' own outlines: not in lib/types.ts (only SectorMap reads it)
type MapCity = City & { cases?: { slug: string; d: string }[] }

interface SectorMapProps {
  city: MapCity
  mode?: MapMode
  field?: boolean
  fieldOpacity?: number
  outside?: number
  view?: { x: number; y: number; w: number; h: number }
  selected?: Sector | null
  hovered?: Sector | null
  onSelect?: (s: Sector) => void
  onHover?: (s: Sector | null) => void
  showCases?: boolean
  stroke?: string
  strokeWidth?: number
  className?: string
  label: string     // the page names the map (no English default: the words live in the catalogue)
  children?: ReactNode
  svgRef?: Ref<SVGSVGElement>
  activeCase?: string
  fieldSrc?: string
  outsideFill?: string
  blend?: CSSProperties['mixBlendMode']
  fill?: ((s: Sector) => string | null) | null
  photos?: [string, string] | null
  // the atlas makes its map a keyboard stop (tabIndex, aria-describedby, focus handlers: re-check 2)
  svgProps?: SVGProps<SVGSVGElement>
}

/* The satellite field is an ordinary <img> under the vectors, placed by the same
   viewBox arithmetic as the SVG (meet). Outside the region it is dimmed by ONE
   even-odd path: the field's rectangle minus every sector ring. Plain image + plain
   vector — nothing that a print, a screenshot or a Figma capture would drop. */
function SectorMapImpl({
  city, mode = 'effect', field = true, fieldOpacity = FIELD_UNDER_DATA, outside = 0.32, view,
  selected, hovered, onSelect, onHover, showCases = false, stroke = 'var(--paper)',
  strokeWidth = 0.6, className = '', label, children, svgRef, activeCase,
  fieldSrc: fieldOverride, outsideFill = 'var(--paper)', blend = 'multiply',
  fill: fillFn = null,   // (sector) → colour | null: a lens with its own ramp (the "need" lenses); memoise it
  photos = null,         // [before, after] true-colour summers in the field's frame: the atlas swipe
  svgProps,
}: SectorMapProps) {
  const { W, H } = city.svg
  const thr = city.thresholds.ndvi
  const vbv = view || { x: 0, y: 0, w: W, h: H }
  const vb = `${vbv.x} ${vbv.y} ${vbv.w} ${vbv.h}`
  const fieldSrc = field && city.field ? (fieldOverride || '/' + city.field.src) : null
  const fb = city.field?.box
  const uid = useId().replace(/:/g, '')
  const interactive = Boolean(onSelect || onHover)
  const hasPhotos = Boolean(photos)   // a dependency by value: the photos' pair may be a new array on every render

  const wrap = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState<{ w: number; h: number } | null>(null)
  useEffect(() => {
    const el = wrap.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => e && setSize({ w: e.contentRect.width, h: e.contentRect.height }))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // latest handlers without changing element identity: panning re-renders the
  // viewBox only, React skips the 724 unchanged sector elements
  const h = useRef<{ onSelect?: (s: Sector) => void; onHover?: (s: Sector | null) => void }>({})
  h.current = { onSelect, onHover }

  // the lightest classes of each ramp are under 3 : 1 against the map's ground (lack-1 1.37, lack-2 1.84, green-1 1.14,
  // green-2 1.40, gain-1 2.28, loss-1 2.30; WCAG 1.4.11, re-check 2, 3 Oct): such a sector's own path is stroked in its
  // ramp's dark step (≥ 3.8 : 1, 0.8 instead of the paper's 0.6), so its shape reads against the ground. Fills and hues
  // stay as they are (design wave, 5 Oct; the alternative, darker ramps, would darken every step). The light sectors are
  // painted after the rest, so a neighbour's paper outline never covers their edge; the edge is the path's own stroke,
  // not a second copy of its geometry (the copy added 136 KB raw / 36 KB gzip to the landing; round-3 re-check, 6 Oct)
  const sectorEls = useMemo(() => {
    const rest: ReactNode[] = [], light: ReactNode[] = []
    for (const s of city.sectors) {
      const raw = fillFn ? fillFn(s) : fillFor(s, mode, thr)
      const fill = raw === 'url(#hatch)' ? `url(#hatch-${uid})` : raw
      const edge = hasPhotos ? undefined : LIGHT_EDGE[raw ?? '']
      ;(edge ? light : rest).push(
        <path key={s.id} d={s.d} fill={fill || 'transparent'}
              stroke={edge ?? stroke} strokeWidth={edge ? 0.8 : strokeWidth} vectorEffect="non-scaling-stroke"
              className={edge ? 'is-filled is-light' : fill ? 'is-filled' : ''}
              onClick={interactive ? () => h.current.onSelect?.(s) : undefined}
              onMouseEnter={interactive ? () => h.current.onHover?.(s) : undefined}
              onMouseLeave={interactive ? () => h.current.onHover?.(null) : undefined} />,
      )
    }
    return [...rest, ...light]
  }, [city, mode, thr, stroke, strokeWidth, interactive, uid, fillFn, hasPhotos])

  const outsideD = useMemo(() => {
    if (!fb) return null
    return `M${fb[0]},${fb[1]}h${fb[2]}v${fb[3]}h${-fb[2]}Z` + city.sectors.map((s) => s.d).join('')
  }, [city, fb])

  // the "no fair comparison" hatch is sized on screen, not in map units: a 4-unit period was
  // 2.5 px on a desktop map and 1.3 px on a phone, where it averaged out to a flat pale fill
  // and the refusal read as empty ground. 5-px period, 1.2-px line at any width or zoom.
  const px = size ? Math.min(size.w / vbv.w, size.h / vbv.h) : null
  const hp = px ? 5 / px : 4, hs = px ? 1.2 / px : 1.2

  // the field's frame on screen, by the viewBox arithmetic (meet); the photos share it
  // The offset is a transform, not left/top: a pan or a flight moves the picture every frame, and a moved left/top is a
  // layout shift — a link to a sector or an audit scored a CLS of 1.2–2.4 in Chrome; a transform scores none (re-check 1)
  let frame: { left: number; top: number; width: number; height: number; transform: string } | null = null
  let frameLeft = 0
  if ((fieldSrc || photos) && size && fb) {
    const s = Math.min(size.w / vbv.w, size.h / vbv.h)
    const ox = (size.w - vbv.w * s) / 2, oy = (size.h - vbv.h * s) / 2
    frameLeft = ox + (fb[0] - vbv.x) * s
    frame = { left: 0, top: 0, width: fb[2] * s, height: fb[3] * s, transform: `translate(${frameLeft}px, ${oy + (fb[1] - vbv.y) * s}px)` }
  }
  const imgStyle = fieldSrc && frame ? { ...frame, opacity: fieldOpacity } : null

  // photos: the verdicts become outlines, so the ground stays visible; the direction is the verdict's
  // (effect) or the raw change's sign (raw), exactly as the fills would have had it
  const outlined = useMemo(() => {
    if (!photos) return []
    return city.sectors.filter((s) => { const f = fillFor(s, mode, thr); return f && !f.startsWith('url') })
      .map((s) => ({ s, up: mode === 'effect' ? s.nv === 'up' : (s.raw ?? 0) > 0 }))
  }, [photos, city, mode, thr])

  return (
    <div ref={wrap} className={`sector-map ${className}`}>
      {imgStyle && <img className="sector-field" src={fieldSrc ?? undefined} alt="" aria-hidden="true" style={{ ...imgStyle, mixBlendMode: blend }} draggable="false" />}
      {/* the after summer lies on the before one and is cut at the split: --split (0…1 of the map's
          width) is set by the swipe handle on an ancestor, so dragging never re-renders the map */}
      {photos && frame && (
        <>
          <img className="sector-photo" src={photos[0]} alt="" aria-hidden="true" style={frame} draggable="false" decoding="async" />
          <img className="sector-photo is-after" src={photos[1]} alt="" aria-hidden="true" draggable="false" decoding="async"
               style={{ ...frame, '--img-left': `${frameLeft}px`, '--map-w': `${size!.w}px` } as CSSProperties} />
        </>
      )}
      {/* a map you can click holds focusable pins (the audits): a picture may not contain controls, so
          it is a labelled group; a map you only look at stays a picture */}
      <svg ref={svgRef} viewBox={vb} preserveAspectRatio="xMidYMid meet"
           role={interactive ? 'group' : 'img'} aria-label={plain(label)} {...svgProps}>
        <defs>
          <pattern id={`hatch-${uid}`} width={hp} height={hp} patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <rect width={hp} height={hp} fill="var(--hatch-ground, var(--paper-2))" />
            {/* in the middle of the tile: at x = 0 the tile clipped half the stroke away */}
            <line x1={hp / 2} y1="0" x2={hp / 2} y2={hp} stroke="var(--hatch, var(--ink-4))" strokeWidth={hs} />
          </pattern>
        </defs>
        {(fieldSrc || photos) && outsideD && (
          <path d={outsideD} fill={outsideFill} fillOpacity={1 - outside} fillRule="evenodd" pointerEvents="none" />
        )}
        <g className="sectors" strokeLinejoin="round">{sectorEls}</g>
        {outlined.length > 0 && (
          <g className="photo-verdicts" fill="none" strokeLinejoin="round" pointerEvents="none">
            {/* a paper casing under the colour: the outline reads on dark forest and on white roofs */}
            {outlined.map(({ s }) => <path key={s.id} d={s.d} className="pv-case" vectorEffect="non-scaling-stroke" />)}
            {outlined.map(({ s, up }) => <path key={s.id} d={s.d} className={up ? 'pv-up' : 'pv-down'} vectorEffect="non-scaling-stroke" />)}
          </g>
        )}
        {/* on a photograph an ink line alone vanishes into a dark forest: it gets a paper casing */}
        {hovered && hovered.id !== selected?.id && photos && (
          <path d={hovered.d} fill="none" stroke="var(--paper)" strokeWidth="3.2" vectorEffect="non-scaling-stroke" pointerEvents="none" />
        )}
        {hovered && hovered.id !== selected?.id && (
          <path d={hovered.d} fill="none" stroke="var(--ink)" strokeWidth="1.2" vectorEffect="non-scaling-stroke" pointerEvents="none" />
        )}
        {selected && photos && (
          <path d={selected.d} fill="none" stroke="var(--paper)" strokeWidth="4.6" vectorEffect="non-scaling-stroke" pointerEvents="none" />
        )}
        {selected && (
          <path d={selected.d} fill="none" stroke="var(--ink)" strokeWidth="2.2" vectorEffect="non-scaling-stroke" pointerEvents="none" />
        )}
        {showCases && city.cases?.map((c) => (
          photos
            ? <path key={c.slug} d={c.d} fill="none" stroke="var(--paper)" strokeWidth={c.slug === activeCase ? 2.6 : 1.6}
                    vectorEffect="non-scaling-stroke" pointerEvents="none" />
            : c.slug === activeCase
            ? <path key={c.slug} d={c.d} fill="var(--gain-2)" stroke="var(--ink)" strokeWidth="1.8"
                    vectorEffect="non-scaling-stroke" pointerEvents="none" />
            : <path key={c.slug} d={c.d} fill="var(--ink)" fillOpacity={.85} stroke="var(--paper)" strokeWidth="1"
                    vectorEffect="non-scaling-stroke" pointerEvents="none" />
        ))}
        {children}
      </svg>
    </div>
  )
}

const LIGHT_EDGE: Record<string, string> = {
  'var(--lack-1)': 'var(--lack-4)', 'var(--lack-2)': 'var(--lack-4)',
  'var(--green-1)': 'var(--green-5)', 'var(--green-2)': 'var(--green-5)',
  'var(--gain-1)': 'var(--gain-3)', 'var(--loss-1)': 'var(--loss-3)',
}

export const SectorMap = memo(SectorMapImpl)
