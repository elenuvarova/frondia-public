import createMiddleware from 'next-intl/middleware'
import { NextRequest, NextResponse } from 'next/server'
import { routing } from './i18n/routing'
import { SHARED_UMAMI, umamiConfig } from './lib/analytics'
import { buildCsp } from './lib/csp'
import { legacyRedirect } from './lib/legacy'

const intl = createMiddleware(routing)
const SITE_URL = process.env.SITE_URL || 'https://frondia.eu'
// the counter's own origin (null without UMAMI_WEBSITE_ID: no counter, nothing added to the CSP); the shared
// dashboard's counter rides with it
const UMAMI_ORIGIN = umamiConfig()?.hostUrl

export default function proxy(request: NextRequest) {
  const moved = legacyRedirect(request.nextUrl, request.headers.get('host') || '', SITE_URL)
  if (moved) return NextResponse.redirect(moved, 301)

  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')
  const csp = buildCsp(nonce, process.env.NODE_ENV === 'development', UMAMI_ORIGIN, UMAMI_ORIGIN && SHARED_UMAMI.hostUrl)
  const headers = new Headers(request.headers)
  headers.set('x-nonce', nonce)
  headers.set('Content-Security-Policy', csp)
  const response = intl(new NextRequest(request, { headers }))
  response.headers.set('Content-Security-Policy', csp)
  return response
}

export const config: { matcher: (string | { source: string; has: { type: 'host'; value: string }[] })[] } = {
  matcher: [
    // the site: everything except Next's own files, the exact /health, files with an extension (data, photos,
    // fonts, and /u/script.js and /u/shared.js — the Umami trackers, rewritten by next.config), and the site-wide
    // icon/manifest routes (app/icon.tsx, app/apple-icon.tsx, app/manifest.ts live outside [locale]: /icon/0 and /apple-icon have no dot either, and without
    // this exclusion next-intl would rewrite them onto a [locale] segment that doesn't have them,
    // 404ing every icon); /healthz or /health-check go through it and get the styled 404.
    '/((?!_next|health$|icon/|apple-icon$|.*\\..*).*)',
    // a dotted path under a language's prefix (/nl/foo.php, /fr/x.json) is no file of the site: it gets its language, so the
    // 404 answers in it and its switch offers /fr/foo.php, not /fr/nl/foo.php (re-check 5 after plan 5, #4; design wave)
    '/(nl|fr|xx)/(.*\\..*)',
    // the old hosts and www (lib/legacy.ts): every path, files and Next's own included, so an old link to a data file,
    // a download, the favicon or robots.txt moves too (plan 6). A literal, because Next reads the matcher at build time;
    // the container's healthcheck asks 127.0.0.1, which is none of these, so it still gets /health itself.
    { source: '/:path*', has: [{ type: 'host', value: '(?:frondia\\.ontwrpn\\.com|facta\\.ontwrpn\\.com|www\\.frondia\\.eu)' }] },
  ],
}
