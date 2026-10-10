// Visit counts: Umami on our own server (stats.frondia.eu). The tracker script is served through this
// site (/u/script.js, a rewrite — script-src stays 'self'), but the counts go straight to Umami's own
// origin, so Umami sees the visitor's address rather than this server's (it uses it for the country
// and the anonymous visitor hash, and does not store it). The CSP names that one origin in connect-src.
// No cookies; Do Not Track is honoured; only frondia.eu is counted, so local runs and previews never
// reach the numbers. No website id — no counter at all.
export const EV = { atlas: 'atlas-open', audit: 'audit-open', faq: 'faq-open', lang: 'lang-switch', consent: 'consent', download: 'download' } as const

const DEFAULT_HOST = 'https://stats.frondia.eu'

type Env = Record<string, string | undefined>

// The origin of UMAMI_HOST (scheme + host + port, no path); a malformed value falls back to ours.
export function umamiOrigin(env: Env = process.env): string {
  try {
    return new URL(env.UMAMI_HOST || DEFAULT_HOST).origin
  } catch {
    return DEFAULT_HOST
  }
}

export function umamiConfig(env: Env = process.env) {
  const websiteId = env.UMAMI_WEBSITE_ID
  if (!websiteId) return null
  return { src: '/u/script.js', websiteId, hostUrl: umamiOrigin(env), domains: 'frondia.eu', beforeSend: BEFORE_SEND }
}

// The tracker calls window[BEFORE_SEND](type, payload) before every send (data-before-send); a null
// return drops the send. components/Events.tsx installs it.
export const BEFORE_SEND = 'frondiaBeforeSend'
const REPLACED = /^\/(?:[a-z]{2}\/)?(?:atlas|data|register)\/?$/
// Umami counts a page view on every History API change, and three pages rewrite their own address in place: the atlas
// on every click (replaceState, A3), the data page on a change of city and the register on a change of filter
// (router.replace, L10). One visit would read as dozens. A view whose path is one of those three and whose referrer is
// the same path on this site (language prefix included) is that rewrite, not a visit; Umami's referrer for a history
// change is the previous address (for the first view it is the outside referrer or empty). A language switch changes
// the path, and the dossier and the commune move by links: those count as before
export function isReplaceRepeat(url: string, referrer: string, origin: string): boolean {
  if (!referrer) return false
  try {
    const u = new URL(url, origin), r = new URL(referrer, origin)
    return u.origin === origin && r.origin === origin && REPLACED.test(u.pathname) && u.pathname === r.pathname
  } catch {
    return false
  }
}

// The filter's whole decision, for components/Events.tsx: drop a page view (Umami's type "event" with no name) that
// is the atlas, the data page or the register rewriting its own address; every named event, every identify and every
// other view passes
export function dropView(type: string, payload: { name?: unknown; url?: unknown; referrer?: unknown }, origin: string): boolean {
  return type === 'event' && !payload.name && isReplaceRepeat(String(payload.url ?? ''), String(payload.referrer ?? ''), origin)
}

// A second counter: the shared dashboard for all of Elena's sites (stats.ontwrpn.com), page views only. Loaded the same
// way as ours — its script through this site (/u/shared.js), its counts straight to its own origin, which goes in
// connect-src — with the same options. It rides with ours (no UMAMI_WEBSITE_ID, neither), and data-domains keeps previews out. It loads
// after ours (components/Umami.tsx), and the tracker only claims window.umami when it is still free, so the click
// events (components/Events.tsx) keep going to stats.frondia.eu alone.
export const SHARED_UMAMI = {
  src: '/u/shared.js',
  websiteId: '2454bbce-1112-4e69-9899-6d4fe32ebd27',
  hostUrl: 'https://stats.ontwrpn.com',
  domains: 'frondia.eu',
  beforeSend: BEFORE_SEND,
} as const

// Only the scripts are proxied; each tracker posts to its own `${hostUrl}/api/send` directly.
export function umamiRewrites(env: Env = process.env) {
  return [
    { source: '/u/script.js', destination: `${umamiOrigin(env)}/script.js` },
    { source: SHARED_UMAMI.src, destination: `${SHARED_UMAMI.hostUrl}/script.js` },
  ]
}
