// The atlas's address, resolved on the server for the page's head and its preloads: the view the address asks for,
// the lens the "what's missing" question opens on, and only a sector or an audit that this city has. The browser
// reads the city's file itself (A2), so nothing here goes into the client tree but the state — normalised as the
// client would normalise it once the city is in (Q15): an audit of this city opens on "what changed", an unknown one
// or another city's is dropped, so the head, the preloads and the first render describe the same view.
import 'server-only'
import { DataError, getCity } from '@/lib/data'
import { firstMeasured, parseAtlas, toParams, type AtlasState, type RawQuery } from './state'
import type { AtlasCity } from './types'
import type { Sector } from '@/lib/types'

export interface AtlasResolved {
  state: AtlasState
  lens: string
  ok: boolean
  fieldSrc: string | null
  sector: Pick<Sector, 'id' | 'n' | 'c' | 'n_nl' | 'n_fr' | 'c_nl' | 'c_fr'> | null
  caseSlug: string | null
}

export async function resolveAtlas(query: RawQuery): Promise<AtlasResolved> {
  const state = parseAtlas(toParams(query))
  let city: AtlasCity
  try {
    city = (await getCity(state.city)) as AtlasCity
  } catch (e) {
    if (e instanceof DataError) return { state, lens: state.lens ?? 'heat', ok: false, fieldSrc: null, sector: null, caseSlug: null }
    throw e
  }
  const s = state.sector ? city.sectors.find((x) => x.id === state.sector) : undefined
  const caseSlug = state.caseSlug && (city.cases || []).some((c) => c.slug === state.caseSlug) ? state.caseSlug : null
  return {
    state: caseSlug ? { ...state, q: 'change', caseSlug } : { ...state, caseSlug: null },
    lens: state.lens ?? firstMeasured(city),
    ok: true,
    fieldSrc: city.field?.src ? '/' + city.field.src : null,
    sector: s ? { id: s.id, n: s.n, c: s.c, n_nl: s.n_nl, n_fr: s.n_fr, c_nl: s.c_nl, c_fr: s.c_fr } : null,
    caseSlug,
  }
}

// The field photo is the wide screen's largest paint, so it is preloaded with the HTML whenever the view shows it (not
// on "what's missing", nor on the communes or photos views). On a phone (≤ 860 px, the atlas's own breakpoint) the
// panel's words matter more: the preload is limited to wide screens, and a phone fetches the photo when the map mounts,
// after the city's file, as the old atlas did (Q14).
export const FIELD_MEDIA = '(min-width: 861px)'
export function fieldPreload(state: AtlasState, fieldSrc: string | null): { href: string; media: string } | null {
  const shown = state.q !== 'need' && !(state.q === 'change' && (state.view === 'communes' || state.view === 'photos'))
  return fieldSrc && shown ? { href: fieldSrc, media: FIELD_MEDIA } : null
}
