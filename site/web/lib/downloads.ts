import type { CityKey } from './cities'
import type { DownloadLayer } from './types'

// The data page's plain helpers, apart from its resolver (lib/data-page.ts reads the files, and is
// server-only through lib/data): the Dataset builder in lib/seo.ts and the tests use these too.

// the old page's default: a layer without a format is a CSV
export const formatOf = (l: Pick<DownloadLayer, 'format'>): string => l.format || 'CSV'

// kilobytes as the old page printed them: rounded, never below 1
export const kb = (bytes: number): number => Math.max(1, Math.round(bytes / 1024))

// the sections, in the old page's order: the data's group name (also the section's anchor, as the
// old page built it — /commune links to #the-law) and the catalogue key its words live under
export const GROUPS = [
  { group: 'What changed', key: 'changed' },
  { group: 'The law', key: 'law' },
  { group: 'What’s missing', key: 'missing' },
  { group: 'What to place', key: 'place' },
  { group: 'Cross-checks', key: 'checks' },
  { group: 'Sectors', key: 'sectors' },
] as const
export const groupId = (g: string): string => g.toLowerCase().replace(/[^a-z]+/g, '-')

export const downloadPath = (city: CityKey, file: string): string => `/downloads/${city}/${file}`
export const downloadName = (city: CityKey, file: string): string => `frondia-${city}-${file}`

// "2017–2019 → 2021–2024" and 2026 → "2017/2026" (ISO 8601 interval of years); null when the data
// names no year at all
export function temporalCoverage(window: string | undefined, latest: number | null): string | null {
  const years = [...(window ?? '').matchAll(/\d{4}/g)].map((m) => Number(m[0]))
  if (latest != null) years.push(latest)
  if (!years.length) return null
  return `${Math.min(...years)}/${Math.max(...years)}`
}
