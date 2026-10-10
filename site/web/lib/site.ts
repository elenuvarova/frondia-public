// The site's own address and the query's reading, in one place for every page, the sitemap and robots.

// SITE_URL, read per request from the running container (never frozen at build time, never taken
// from the request's Host header)
export const siteUrl = (): string => process.env.SITE_URL || 'https://frondia.eu'

// URLSearchParams.get semantics, as the old pages read their address: the first value of a
// repeated parameter, '' when absent
export const firstParam = (v: string | string[] | undefined): string => (Array.isArray(v) ? v[0] : v) ?? ''
