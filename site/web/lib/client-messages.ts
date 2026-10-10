// The words the browser is sent (the layout's NextIntlClientProvider): only what the client
// components read with useT — the rest of the catalogue stays on the server, where getT reads it.
// Without a `messages` prop next-intl 4 hands the provider the whole catalogue, and every page would
// carry every other page's text in its flight payload (55 KB of en.json on 28 Sep 2026).
//   common.nav              Nav and LanguageSwitcher
//   common.consent          ConsentBanner
//   common.charts           NullHistogram, BeforeAfter and Rings, which render under both layouts
//   landing.loadError       app/(site)/[locale]/error.tsx
//   landing.threshold.hist  HistogramBlock
// The rest of common stays on the server for the site: Footer and NotFound are server components, and
// no site client component reads the city or object names or the separators (plan 5 fix wave: P5-2 and
// the footer item; 5 072 characters with all of common, under 3 000 now).
// A client component that needs a word from elsewhere either gets it as a prop from its server
// parent (CitySelect, CommuneFinder, PrintButton, RegisterFilters) or has its path added here;
// tests/client-messages.test.ts fails when a client component reads a key this list does not ship.
// SITE_CLIENT_PATHS is the site's root layout's subset; ATLAS_CLIENT_PATHS the atlas's layout's: common,
// its own section, and landing.cases (an audit's place name and story in the atlas's drawer and title).
export const SITE_CLIENT_PATHS = ['common.nav', 'common.consent', 'common.charts', 'landing.loadError', 'landing.threshold.hist'] as const
export const ATLAS_CLIENT_PATHS = ['common', 'atlas', 'landing.cases'] as const

type Tree = { [k: string]: unknown }

export function clientMessages(all: Tree, paths: readonly string[] = SITE_CLIENT_PATHS): Tree {
  const out: Tree = {}
  for (const p of paths) {
    const parts = p.split('.')
    let from: unknown = all
    for (const k of parts) from = from && typeof from === 'object' ? (from as Tree)[k] : undefined
    if (from === undefined) continue
    let to = out
    for (const k of parts.slice(0, -1)) to = (to[k] ??= {}) as Tree
    to[parts[parts.length - 1]!] = from
  }
  return out
}
