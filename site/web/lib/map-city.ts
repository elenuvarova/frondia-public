import type { City, Sector } from './types'

/* The landing's maps (SectorMap, ThreeMap) are client components, so the city they are given travels to the browser a
   second time, in the page's RSC payload, beside the SVG already rendered from it. They read only the frame, the
   threshold, the field and, per sector, its outline and the fields their fills read (fillFor: nv, ne, raw, cmp;
   needFill for services: pop, fitq). The whole package (every lens, the communes' outlines, the seasons, the register)
   was 680 KB raw / 150 KB gzip of Brussels in every landing (round-3 re-check, 6 Oct); this is 210 / 52.
   One object per city (WeakMap): React sends an object once however many maps share it. Server code keeps the full city. */
const KEEP = ['id', 'd', 'nv', 'ne', 'raw', 'cmp', 'pop', 'fitq'] as const
const cache = new WeakMap<City, City>()

export function mapCity(city: City): City {
  let m = cache.get(city)
  if (!m) {
    const sectors = city.sectors.map((s) => {
      const o: Record<string, unknown> = {}
      for (const k of KEEP) if (s[k] !== undefined) o[k] = s[k]
      return o as unknown as Sector   // a map's sector: the name and commune stay on the server
    })
    m = { svg: city.svg, thresholds: city.thresholds, field: city.field, sectors } as unknown as City
    cache.set(city, m)
  }
  return m
}
