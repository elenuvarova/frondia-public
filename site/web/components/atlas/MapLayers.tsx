'use client'
import { placeLabels } from '@/lib/atlas/geometry'
import type { AtlasCity } from '@/lib/atlas/types'
import type { Point } from '@/lib/types'
import { placeName } from '@/lib/names'
import { useT } from '@/lib/t-client'
import { plain } from '@/lib/typography'

/* What the atlas draws over the sectors (Atlas.jsx 1054–1091): the communes and the registered places on the
   communes view, the audits' pins on "what changed", the named points on "what to place". Sizes are in map units,
   computed by the atlas from the zoom. */
interface MapLayersProps {
  city: AtlasCity
  q: string
  communesOn: boolean
  caseSlug: string | null
  vbw: number
  unitPx: number
  labelFs: number
  pinR: number
  pinFs: number
  leftLabel: Set<string>
  onCase: (slug: string) => void       // a click (the atlas ignores one that ends a drag)
  onCaseKey: (slug: string) => void    // Enter: never the end of a drag; a held key opens (and counts) once
  onCaseFocus: (slug: string) => void  // reached by Tab: the atlas flies it out from under a card
  shown: Point[]
  moreN: number
  onHoverPoint: (p: Point | null) => void
  onPickPoint: (p: Point) => void
}

export function MapLayers({ city, q, communesOn, caseSlug, vbw, unitPx, labelFs, pinR, pinFs, leftLabel, onCase, onCaseKey, onCaseFocus, shown, moreN, onHoverPoint, onPickPoint }: MapLayersProps) {
  const { t, loc } = useT('atlas')
  const { t: tl, raw: rl } = useT('landing')
  const known = rl<Record<string, { place?: string }>>('cases')
  const placeOf = (slug: string) => (known[slug]?.place ? tl(`cases.${slug}.place`) : undefined)
  const registered = city.registered || []
  return (
    <>
      {communesOn && (
        <g className="communes" aria-hidden="true">
          {city.communes.list.map((c) => <path key={c.code} d={c.d} className={`commune${c.exempt ? ' is-exempt' : ''}`} />)}
          {registered.map((r) => <path key={r.id} d={r.d} className={`reg${r.comparable ? '' : ' is-refused'}`} />)}
          {/* a boulevard's footprint is a hairline at city scale: a numbered pin makes it findable, the same number as in the list */}
          {registered.map((r, i) => (
            <g key={r.id} className={`reg-pin${r.comparable ? '' : ' is-refused'}`} transform={`translate(${r.x} ${r.y})`}>
              <circle r={pinR} strokeWidth={1 / unitPx} />
              <text style={{ fontSize: pinFs }} dy="0.36em">{i + 1}</text>
            </g>
          ))}
          {placeLabels(city.communes.list, registered, labelFs, pinR, loc).map((c) => (
            <text key={c.code} x={c.x} y={c.y} className={`commune-label${c.exempt ? ' is-exempt' : ''}`}
                  style={{ fontSize: labelFs }} strokeWidth={labelFs / 4}>{placeName(c, loc)}</text>
          ))}
        </g>
      )}
      {q === 'change' && !communesOn && city.cases.map((c) => {
        const place = placeOf(c.slug)
        return (
          <g key={c.slug} className={`case-pin${leftLabel.has(c.slug) ? ' is-left' : ''}`} transform={`translate(${c.x} ${c.y})`}
             onClick={() => onCase(c.slug)}
             role="link" tabIndex={0} aria-label={plain(t('passport.audit', { place: place ?? '' }))}
             onKeyDown={(e) => { if (e.key === 'Enter' && !e.repeat) onCaseKey(c.slug) }}
             onFocus={() => onCaseFocus(c.slug)}>
            <circle r={12 / unitPx} className="case-pin-hit" />
            {/* the open case shows its footprint, not a dot on top of it */}
            {c.slug !== caseSlug && <circle r={vbw / 110} className="case-pin-dot" />}
            <text x={(leftLabel.has(c.slug) ? -1 : 1) * (c.slug === caseSlug ? vbw / 40 : vbw / 70)} y={vbw / 260} style={{ fontSize: vbw / 58 }} strokeWidth={vbw / 280}>{place}</text>
          </g>
        )
      })}
      {shown.length > 0 && (
        <g className="pts" aria-hidden="true">
          {shown.map((p) => (
            <circle key={p.r} cx={p.x} cy={p.y}
                    r={p.role === 'named' ? vbw / 150 : p.role === 'control' ? vbw / 170 : vbw / 330}
                    className={`pt-dot pt-dot-${p.role || 'more'}${p.r > moreN ? ' is-beyond' : ''}`}
                    onMouseEnter={() => onHoverPoint(p)} onMouseLeave={() => onHoverPoint(null)}
                    onClick={() => onPickPoint(p)} />
          ))}
        </g>
      )}
    </>
  )
}
