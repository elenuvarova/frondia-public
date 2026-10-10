'use client'
import { int, longDate, pct } from '@/lib/format'
import { sectorName, sectorPlace } from '@/lib/names'
import type { AtlasCity, AtlasPoints } from '@/lib/atlas/types'
import { placeRegister } from '@/lib/atlas/words'
import type { Point, Sector } from '@/lib/types'
import { useT } from '@/lib/t-client'
import { Choice, PanelKicker } from './bits'
import { MoreN } from './MoreN'
import { useMoreBelow } from './useMoreBelow'
import { tie, plain } from '@/lib/typography'

// the legend's rows, in the catalogue's order: named, comparison, further candidates
const ROLES = ['named', 'control', 'more']

interface PlacePanelProps {
  city: AtlasCity
  points: AtlasPoints | null
  pointsError?: boolean   // the named points file could not be read (A8, as for the city's own file)
  obj: string
  setObj: (obj: string) => void
  onPick: (p: Point, s: Sector | undefined) => void
  n: number
  setN: (n: number) => void
}

// What to place: one kind of object, its coverage today and with N more, and the ten named first
// (Atlas.jsx 476–521). A date is read at noon, as the old atlas did, so no time zone moves the day.
export function PlacePanel({ city, points, pointsError, obj, setObj, onPick, n, setN }: PlacePanelProps) {
  const more = useMoreBelow<HTMLElement>()
  const { t, raw, loc } = useT('atlas')
  const { t: tc } = useT('common')
  if (!points) {
    return (
      <section className="panel" ref={more} aria-label={plain(t('place.aria'))}>
        {pointsError
          ? <><p className="small">{tc('unavailable')}</p><button type="button" className="link" onClick={() => location.reload()}>{t('reload')}</button></>
          : <p className="small">{t('place.loading')}</p>}
      </section>
    )
  }
  const name = tc(`cities.${city.city}`)
  const type = points.types.find((x) => x.key === obj) || points.types[0]!
  const named = points.points.filter((p) => p.t === type.key && p.role === 'named').sort((a, b) => a.r - b.r)
  const byId = new Map(city.sectors.map((s) => [s.id, s]))
  const objects = (k: string) => tc(`objects.many.${k}`)
  const day = (iso: string) => longDate(`${iso}T12:00:00`, loc)
  const legend = raw<string[]>('place.legend')
  return (
    <section className="panel" ref={more} aria-label={plain(t('place.aria'))}>
      <PanelKicker>{t('q.place.long')}</PanelKicker>
      <div>
        <h1 className="display-s">{t('place.title', { objects: objects(type.key), city: name })}</h1>
        <p className="mono panel-window">{t('place.window', { n: String(type.n), pool: int(type.pool, loc) })}</p>
      </div>
      <Choice label={t('place.object')} value={type.key} onChange={setObj}
              options={points.types.map((x) => [x.key, objects(x.key)] as const)} />
      {type.before != null && (
        <div className="counts">
          <div><span className="num-l">{pct(type.before, 0, loc)}</span><span className="label">{t('place.today')}</span></div>
          <div><span className="num-l">{pct(type.after, 0, loc)}</span><span className="label">{t('place.allPlaced', { n: String(type.n) })}</span></div>
        </div>
      )}
      <MoreN city={city} points={points} t={type} n={n} setN={setN} />
      <ul className="legend legend--points">
        {legend.map((_, i) => <li key={i}><i className={`pt pt-${ROLES[i]}`} />{t(`place.legend.${i}`)}</li>)}
      </ul>
      <p className="small">{t('place.lede')} {t('place.named', { date: day(points.registered_at) })}</p>
      <p className="small panel-source">{t('place.source')} {t('place.limit')} {t('place.mapped')}</p>
      {type.official && <p className="small panel-source">{placeRegister(t, type.official, tc(`objects.a.${type.key}`), tc(`objects.no.${type.key}`))} {t('place.snap', { date: day(type.official.date) })}</p>}
      <p className="label panel-sub">{t('place.namedFirst')}</p>
      <ol className="toplist">
        {named.map((p) => {
          const s = p.s ? byId.get(p.s) : undefined
          return (
            <li key={p.r}>
              <button type="button" onClick={() => onPick(p, s)}>
                <i className="pt pt-named" /><span>{s ? tie(sectorName(s, loc), loc) : t('place.outside')}<small>{s ? tie(sectorPlace(s, loc), loc) : name}</small></span><span className="mono">{tc('sep.rank', { n: String(p.r) })}</span>
              </button>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
