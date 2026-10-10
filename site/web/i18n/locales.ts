// The languages of the site. A language is added here, with its catalogue (messages/<code>.json) and its data texts
// (scripts/site/i18n/<code>.json); routes, the switcher, hreflang, number formats and the typography's short words all
// read this list. A language is published (routed, in the sitemap and hreflang) only with published: true; before that a
// local build can route it for review with NEXT_PUBLIC_PREVIEW_LOCALES=nl,fr,xx (never set in the Dockerfile: test).
import SHORT from './short-words.json'

export const CODES = ['en', 'nl', 'fr', 'xx'] as const
export type Locale = (typeof CODES)[number]
const NNBSP = ' '

export interface LocaleInfo {
  code: Locale; tag: string; label: string; name: string; published: boolean
  dev?: true                       // the pseudo-language: preview builds only, never in the switcher
  quotes: [string, string]
  percentSpace: string             // between a number and "%": French puts a narrow no-break space
  short: string                    // the words a line never ends on (lib/typography.ts, scripts/typo-audit.mjs)
}

export const LOCALES: LocaleInfo[] = [
  { code: 'en', tag: 'en-GB', label: 'EN', name: 'English', published: true, quotes: ['“', '”'], percentSpace: '', short: SHORT.en },
  // nl and fr: published after their catalogues and data texts passed review (plan 5, task 15); the reviews are in i18n/reviews/
  { code: 'nl', tag: 'nl-BE', label: 'NL', name: 'Nederlands', published: true, quotes: ['‘', '’'], percentSpace: '', short: SHORT.nl },
  { code: 'fr', tag: 'fr-BE', label: 'FR', name: 'Français', published: true, quotes: ['« ', ' »'], percentSpace: NNBSP, short: SHORT.fr },
  // English with accents and 35 % more length (lib/pseudo.ts): the layout's check before any translation
  { code: 'xx', tag: 'en-XA', label: 'XX', name: 'Pseudo', published: false, dev: true, quotes: ['“', '”'], percentSpace: '', short: SHORT.en },
]
export const DEFAULT: Locale = 'en'
export const PUBLISHED: Locale[] = LOCALES.filter((l) => l.published).map((l) => l.code)
const isCode = (c: string): c is Locale => (CODES as readonly string[]).includes(c)

export function routedLocales(env: Record<string, string | undefined> = process.env): Locale[] {
  const extra = (env.NEXT_PUBLIC_PREVIEW_LOCALES ?? '').split(',').map((s) => s.trim())
    .filter((c): c is Locale => isCode(c) && !PUBLISHED.includes(c))
  return [...PUBLISHED, ...new Set(extra)]
}
// read once: NEXT_PUBLIC_ variables are inlined at build, so the server and the browser's router agree
export const ROUTED: Locale[] = routedLocales({ NEXT_PUBLIC_PREVIEW_LOCALES: process.env.NEXT_PUBLIC_PREVIEW_LOCALES })
export const isPublished = (code: string): code is Locale => (PUBLISHED as string[]).includes(code)
export const isRouted = (code: string): code is Locale => (ROUTED as string[]).includes(code)
export const infoOf = (code: Locale): LocaleInfo => LOCALES.find((l) => l.code === code)!
export const tagOf = (code: Locale) => infoOf(code).tag
// the lang of a passage kept in English on another language's page, such as the rights holders' credits (same.json):
// a screen reader then reads it with an English voice (WCAG 3.1.2; re-check 2 after plan 5). Undefined on English pages,
// where the html's own lang already says it
export const keptEnglish = (loc: Locale): string | undefined => (loc === DEFAULT ? undefined : tagOf(DEFAULT))

export function localePath(loc: Locale, p: string): string {
  const clean = p === '/' ? '' : p
  return loc === DEFAULT ? (clean || '/') : `/${loc}${clean}`
}

export function alternates(p: string, siteUrl: string): Record<string, string> {
  const out: Record<string, string> = {}
  for (const code of PUBLISHED) out[tagOf(code)] = siteUrl + localePath(code, p)
  out['x-default'] = siteUrl + localePath(DEFAULT, p)
  return out
}
