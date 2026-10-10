import { unstable_doesMiddlewareMatch as matches } from 'next/experimental/testing/server'
import { expect, test } from 'vitest'
import { config } from '@/proxy'
import { routing } from '@/i18n/routing'
import { LEGACY_HOSTS, legacyRedirect } from '@/lib/legacy'
import { buildCsp } from '@/lib/csp'

const SITE = 'https://frondia.eu'

test('old hosts move to the site with path and query', () => {
  expect(legacyRedirect(new URL('https://frondia.ontwrpn.com/atlas?city=ghent&sector=X#y'), 'frondia.ontwrpn.com', SITE))
    .toBe('https://frondia.eu/atlas?city=ghent&sector=X')
  expect(legacyRedirect(new URL('https://facta.ontwrpn.com/'), 'facta.ontwrpn.com', SITE)).toBe('https://frondia.eu/')
  expect(legacyRedirect(new URL('https://www.frondia.eu/data'), 'www.frondia.eu', SITE)).toBe('https://frondia.eu/data')
})

test('the site itself and local hosts are left alone', () => {
  expect(legacyRedirect(new URL('https://frondia.eu/data'), 'frondia.eu', SITE)).toBeNull()
  expect(legacyRedirect(new URL('http://localhost:5180/'), 'localhost:5180', SITE)).toBeNull()
})

test('the CSP keeps the old rules and adds the nonce', () => {
  const csp = buildCsp('abc', false)
  expect(csp).toContain("script-src 'self' 'nonce-abc' 'strict-dynamic'")
  expect(csp).toContain("style-src 'self' 'unsafe-inline'")
  expect(csp).toContain("frame-ancestors 'none'")
  expect(csp).not.toContain('unsafe-eval')
  expect(buildCsp('abc', true)).toContain("'unsafe-eval'")
})

test('the proxy skips only the exact /health, Next files and files with an extension', () => {
  const m = (url: string) => matches({ config, url })
  expect(m('/')).toBe(true)
  expect(m('/foo')).toBe(true)
  expect(m('/nl')).toBe(true)
  expect(m('/healthz')).toBe(true)
  expect(m('/health')).toBe(false)
  expect(m('/_next/static/x.js')).toBe(false)
  expect(m('/favicon.ico')).toBe(false)
  // /u/script.js (Umami's tracker, rewritten by next.config) is skipped as a file with an extension;
  // the counts go straight to UMAMI_HOST, so /u/ is not reserved: any other /u/… path is a page path
  expect(m('/u/script.js')).toBe(false)
  expect(m('/u/api/send')).toBe(true)
})

test('a dotted path under a language prefix goes through the proxy (its 404 gets the language); files and the root do not', () => {
  const m = (url: string) => matches({ config, url })
  expect(m('/nl/foo.php')).toBe(true)
  expect(m('/fr/x.json')).toBe(true)
  expect(m('/fr/a/b.env')).toBe(true)
  expect(m('/foo.php')).toBe(false)
  expect(m('/data/brussels.json')).toBe(false)
  expect(m('/nlx/foo.php')).toBe(false)
  expect(m('/_next/static/nl/x.js')).toBe(false)
})

test('the icon, manifest and og routes (outside [locale]) are never locale-prefixed', () => {
  const m = (url: string) => matches({ config, url })
  // app/icon.tsx, app/apple-icon.tsx, app/manifest.ts have no [locale] segment above them: a
  // rewrite onto /en/icon/0 would 404 (no such route), so the matcher must skip them outright
  expect(m('/icon/0')).toBe(false)
  expect(m('/icon/1')).toBe(false)
  expect(m('/apple-icon')).toBe(false)
  expect(m('/manifest.webmanifest')).toBe(false)
  // app/og/[file]/route.ts: the og card per language, a file name with an extension
  expect(m('/og/en.jpg')).toBe(false)
})

test('next-intl sets no locale cookie: the footer promises none', () => {
  expect(routing.localeCookie).toBe(false)
})

test('the CSP lets the counter send to its own origin, in connect-src only', () => {
  const csp = buildCsp('abc', false, 'https://stats.frondia.eu')
  expect(csp).toContain("connect-src 'self' https://stats.frondia.eu https://*.clarity.ms https://c.bing.com")
  expect(csp).toContain("script-src 'self' 'nonce-abc' 'strict-dynamic';")
  expect(csp.match(/stats\.frondia\.eu/g)).toHaveLength(1)
  // no counter configured: nothing added
  expect(buildCsp('abc', false)).not.toContain('stats.frondia.eu')
})

test('the CSP lets Clarity send, and nothing else new', () => {
  const csp = buildCsp('abc', false)
  expect(csp).toContain("connect-src 'self' https://*.clarity.ms https://c.bing.com")
  expect(csp).toContain("img-src 'self' data: blob: https://*.clarity.ms https://c.bing.com")
  expect(csp).toContain("script-src 'self' 'nonce-abc' 'strict-dynamic'")
})

// plan 6: after the switch the old hosts are domains of this app; every path there must move, not only page paths —
// an old link to a data file, a download, the favicon or robots.txt would otherwise answer 200 from the old host
const FILES = ['/data/brussels.json', '/downloads/brussels/art8_balance_2025.csv', '/favicon.svg', '/favicon.ico',
  '/robots.txt', '/sitemap.xml', '/og/en.jpg', '/manifest.webmanifest', '/icon/0', '/apple-icon', '/health',
  '/_next/static/chunks/a.js', '/atlas/assets/index-abc.js', '/u/script.js']

test('on the old hosts and www every path goes through the proxy: files, downloads, Next’s own and /health too', () => {
  const m = (origin: string, p: string) => matches({ config, url: `${origin}${p}` })
  for (const host of [...LEGACY_HOSTS, 'www.frondia.eu'])
    for (const p of FILES) expect(m(`https://${host}`, p), `${host}${p}`).toBe(true)
  // a port in the Host header does not hide the old host
  expect(m('https://frondia.ontwrpn.com:8443', '/data/brussels.json')).toBe(true)
})

test('the site itself and look-alike hosts keep the old matcher: files skip the proxy', () => {
  const m = (origin: string, p: string) => matches({ config, url: `${origin}${p}` })
  for (const p of FILES) expect(m('https://frondia.eu', p), `frondia.eu${p}`).toBe(false)
  for (const host of ['stats.frondia.eu', 'notfrondia.ontwrpn.com', 'frondia.ontwrpn.com.example.org', 'localhost:5191'])
    expect(m(`http://${host}`, '/data/brussels.json'), host).toBe(false)
})

test('a file on an old host moves like a page, path and query kept', () => {
  expect(legacyRedirect(new URL('https://frondia.ontwrpn.com/downloads/ghent/art8_balance_2025.csv?v=2'), 'frondia.ontwrpn.com', SITE))
    .toBe('https://frondia.eu/downloads/ghent/art8_balance_2025.csv?v=2')
  expect(legacyRedirect(new URL('https://facta.ontwrpn.com/data/brussels.json'), 'FACTA.ontwrpn.com:443', SITE))
    .toBe('https://frondia.eu/data/brussels.json')
  expect(LEGACY_HOSTS.has('frondia.ontwrpn.com') && LEGACY_HOSTS.has('facta.ontwrpn.com')).toBe(true)
})

test('the shared dashboard counter sends to its own origin too, connect-src only', () => {
  const csp = buildCsp('abc', false, 'https://stats.frondia.eu', 'https://stats.ontwrpn.com')
  expect(csp).toContain("connect-src 'self' https://stats.frondia.eu https://stats.ontwrpn.com https://*.clarity.ms https://c.bing.com")
  expect(csp).toContain("script-src 'self' 'nonce-abc' 'strict-dynamic';")
  expect(csp.match(/stats\.ontwrpn\.com/g)).toHaveLength(1)
  expect(buildCsp('abc', false, 'https://stats.frondia.eu')).not.toContain('stats.ontwrpn.com')
})
