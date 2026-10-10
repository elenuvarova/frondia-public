import type { Locale } from '@/i18n/locales'
import { DataError, getRegister } from './data'
import { downloadName } from './downloads'
import { readView, type Search, type Show } from './register-view'
import type { Register } from './types'

// Which view of the register an address asks for (/register?show=…&checked=1), read as the old page
// read it (lib/register-view.ts). Never an error page: register.json missing is the head alone (the
// old page's "Loading…" that never ended), still 200 and not indexed. The filters are views of one
// page, so every view is known by the bare /register.
export type Resolved =
  | { state: 'ok'; show: Show; checked: boolean; d: Register }
  | { state: 'error'; show: Show; checked: boolean }

export async function resolveRegister(q: Search, loc: Locale): Promise<Resolved> {
  const view = readView(q)
  try {
    return { state: 'ok', ...view, d: await getRegister(loc) }
  } catch (e) {
    if (e instanceof DataError) return { state: 'error', ...view }
    throw e
  }
}

// the address every view is known by (canonical, hreflang, og:url): no show, no checked
export const registerQuery = (): string => ''

// the page is there to be found when its data is; a filtered view too, under the bare canonical
export const indexable = (r: Resolved): boolean => r.state === 'ok'

// the two files live with Brussels's layers (scripts/site/downloads.py) and are saved under the name every
// layer on /data gets: frondia-<city>-<file> (re-check 3: the check saved as "register-check.json" while the
// colophon and the server call it register_check.json)
export const REGISTER_CITY = 'brussels' as const
export const REGISTER_FILES = [
  { file: 'register.csv', name: downloadName(REGISTER_CITY, 'register.csv'), key: 'csv' },
  { file: 'register_check.json', name: downloadName(REGISTER_CITY, 'register_check.json'), key: 'checkFile' },
] as const
