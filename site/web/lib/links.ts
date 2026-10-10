// lib/links.ts — the atlas is a route of this site since the move to Next (was a separate app)
import type { Locale } from './format'
import { DEFAULT, ROUTED, localePath } from '@/i18n/locales'
import type { Case } from './types'

export const atlasHref = (loc: Locale, rest = '') => localePath(loc, '/atlas') + rest
export const caseHref = (loc: Locale, c: Pick<Case, 'city' | 'slug'>) => atlasHref(loc, `?city=${c.city}&case=${c.slug}`)

// The language switch's target: the same page and the same parameters (in the atlas, the view its address holds). The
// path comes without a language prefix (next-intl's usePathname); `loc` puts the target language's prefix on it, none for
// English (a next-intl Link with locale="en" would write /en/…, which only answers with a redirect); `hash` keeps the place
// on the page (#c87 in the register)
// on the page (#c87 in the register). A path that still carries a routed language's prefix is taken without it, so the
// switch never doubles one: the proxy skips a dotted path (/nl/foo.php), its 404 got no language, and next-intl's
// pathname kept the /nl, so the switch offered /nl/nl/foo.php and /fr/nl/foo.php (re-check 5 after plan 5, #4)
const PREFIX = new RegExp(`^/(?:${ROUTED.filter((l) => l !== DEFAULT).join('|') || '(?!)'})(?=/|$)`)
export const switchHref = (pathname: string, search: string, loc: Locale = DEFAULT, hash = '') =>
  localePath(loc, pathname.replace(PREFIX, '') || '/') + (search ? `?${search}` : '') + hash
