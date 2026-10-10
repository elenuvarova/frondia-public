// Old addresses of the site answer with a permanent redirect to it, path and query kept:
// facta.ontwrpn.com (renamed 27 Sep 2026), frondia.ontwrpn.com (until frondia.eu), www.
// The old hosts (proxy.ts's second matcher lists them, with www.<site>, as a literal; tests/proxy.test.ts keeps the two in step)
export const LEGACY_HOSTS: ReadonlySet<string> = new Set(['facta.ontwrpn.com', 'frondia.ontwrpn.com'])

export function legacyRedirect(url: URL, host: string, siteUrl: string): string | null {
  const h = host.toLowerCase().split(':')[0]!
  const site = new URL(siteUrl).hostname
  if (!LEGACY_HOSTS.has(h) && h !== `www.${site}`) return null
  return siteUrl.replace(/\/+$/, '') + url.pathname + url.search
}
