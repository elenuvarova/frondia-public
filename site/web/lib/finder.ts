import type { Commune } from './types'

// The commune finder's match (the client component and its tests share it; no server imports here).
// Accents folded, case ignored, over the commune's names in every language, the official name, the city's name in every
// language and the NIS code; an empty query lists every commune — as the Vite page's CommuneFinder did.
// `name` and `city` are what the list shows, in the page's language; `nis` is the code as the list writes it
// ("NIS 21001"); `find` is everything a query may match — all put into words on the server (lib/commune.ts)
export interface FinderItem { code: Commune['code']; name: string; city: string; nis: string; find: string }

// a hyphen, a dash, an apostrophe or a run of spaces is one gap: «sint joost» finds Sint-Joost-ten-Node (re-check 5)
export const fold = (t: string): string =>
  t.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[\s\-\u2010-\u2015'\u2019\u02BC]+/g, ' ').toLowerCase()

export function matches(communes: FinderItem[], q: string): FinderItem[] {
  const f = fold(q.trim())
  return f ? communes.filter((c) => fold(c.find).includes(f)) : communes
}
