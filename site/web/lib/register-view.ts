import type { Register, RegisterContract } from './types'
import { firstParam } from './site'

// The register's views, without the server (lib/register.ts reads the file; components/RegisterFilters
// writes the address): the Vite page (site/apps/landing/src/pages/Register.jsx) read `show` and
// `checked` with URLSearchParams.get — the first value of a repeated parameter — and anything but the
// four label filters shows all, anything but checked=1 the whole list.
export type Search = Record<string, string | string[] | undefined>
export const FILTERS = ['yes', 'weak', 'no', 'blank'] as const
export type Kind = (typeof FILTERS)[number]
export type Show = Kind | 'all'

export const kindOf = (c: Pick<RegisterContract, 'described' | 'label'>): Kind => (c.described ? c.label : 'blank')

export function readView(q: Search): { show: Show; checked: boolean } {
  const s = firstParam(q.show)
  return { show: (FILTERS as readonly string[]).includes(s) ? (s as Kind) : 'all', checked: firstParam(q.checked) === '1' }
}

// the pool the tabs count (the checked ones only, or all), and the rows the list shows
export function counts(cs: RegisterContract[], checked: boolean): Record<Show, number> {
  const n: Record<Show, number> = { all: 0, yes: 0, weak: 0, no: 0, blank: 0 }
  for (const c of cs) if (!checked || c.test) { n.all++; n[kindOf(c)]++ }
  return n
}
export const shownOf = (cs: RegisterContract[], show: Show, checked: boolean): RegisterContract[] =>
  cs.filter((c) => (!checked || c.test) && (show === 'all' || kindOf(c) === show))

// a view's own address, as the old page wrote it (the filter, then checked; nothing for the whole list)
export function viewQuery(show: Show, checked: boolean): string {
  const q = new URLSearchParams()
  if (show !== 'all') q.set('show', show)
  if (checked) q.set('checked', '1')
  const s = q.toString()
  return s ? `?${s}` : ''
}

// who gave the reference labels decides the check's words (en.js REGISTER.ref)
export const refOf = (d: Pick<Register, 'eval'> | null | undefined): 'model' | 'person' => (d?.eval?.kind === 'model' ? 'model' : 'person')
