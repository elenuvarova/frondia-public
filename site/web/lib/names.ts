import { titleCase, type Locale } from '@/lib/format'

// Place names in the page's language: the one way a page prints the name of a sector, a sector's commune, or a commune
// (tests/names.test.ts scans the source for any other). site_data.py writes the official Dutch and French names from
// Statbel's 2024 register next to the English site's own (`n_nl`/`n_fr`, `c_nl`/`c_fr` on a sector; `name_nl`/`name_fr`
// on a commune, an event, a matched place), and only where they differ, so a missing or empty variant means "as in
// English". English and the pseudo-language read the English field. A city is common.cities.<key>, a region
// common.regions.<region_key> — catalogue words, not data.

// a name that is no name: empty, blank, or the source's own "None" (Liège 62063L0AP) — such a sector is nameless, and
// every place shows what it shows for the five nameless Brussels sectors
const real = (v: string | undefined): v is string => v != null && v.trim() !== '' && v.trim() !== 'None'

export function inLang<K extends string>(
  rec: { [P in K]: string } & Partial<Record<`${K}_nl` | `${K}_fr`, string>>, key: K, loc: Locale,
): string {
  const own = loc === 'nl' || loc === 'fr' ? (rec as Partial<Record<string, string>>)[`${key}_${loc}`] : undefined
  if (real(own)) return own
  const en = (rec as Record<K, string>)[key]
  return real(en) ? en : ''
}

// a sector's name, set in title case from the register's capitals ("RESISTANCE" → "Resistance"); '' when it has none
export const sectorName = (s: { n: string; n_nl?: string; n_fr?: string }, loc: Locale): string => titleCase(inLang(s, 'n', loc))

// a sector's name where it is a label or a heading of its own (the dossier, the atlas card, the hover tip): a nameless
// sector is called by its code, `fallback` writing common.sectorFallback ("Sector 21004A19-"). Lists and the page title
// keep sectorName: there a nameless sector keeps what it had (the title falls through to the view, lib/atlas/head.ts)
export const sectorLabel = (s: { id: string; n: string; n_nl?: string; n_fr?: string }, loc: Locale, fallback: (id: string) => string): string =>
  sectorName(s, loc) || fallback(s.id)

// the commune or district a sector lies in, as the site writes it ("Molenbeek" → "Sint-Jans-Molenbeek" in Dutch)
export const sectorPlace = (s: { c: string; c_nl?: string; c_fr?: string }, loc: Locale): string => inLang(s, 'c', loc)

// a commune's name ("Ixelles" → "Elsene" in Dutch)
export const placeName = (r: { name: string; name_nl?: string; name_fr?: string }, loc: Locale): string => inLang(r, 'name', loc)
