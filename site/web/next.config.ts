import path from 'node:path'
import type { NextConfig } from 'next'
import createNextIntlPlugin from 'next-intl/plugin'
import { umamiRewrites } from './lib/analytics'
import { securityHeaders } from './lib/headers'

const withNextIntl = createNextIntlPlugin('./i18n/request.ts')

const config: NextConfig = {
  // one standalone server in the Docker image; the workspace root is one level up (site/)
  output: 'standalone',
  outputFileTracingRoot: path.join(__dirname, '..'),
  poweredByHeader: false,
  // app/global-not-found.tsx: the 404 for every address no page answers, rendered on the server (M7)
  experimental: { globalNotFound: true },
  // the preview languages (i18n/locales.ts) are fixed when the site is built: Next inlines a NEXT_PUBLIC_ variable only
  // when it is defined at build time, and otherwise the server would read it at run time, so a production image started
  // with NEXT_PUBLIC_PREVIEW_LOCALES set would route languages its build never had. An unset variable is baked in empty
  env: { NEXT_PUBLIC_PREVIEW_LOCALES: process.env.NEXT_PUBLIC_PREVIEW_LOCALES ?? '' },
  // browsers and crawlers still ask for /favicon.ico; the page itself links /favicon.svg;
  // /u/script.js serves Umami's tracker from this site (script-src stays 'self'); the counts
  // themselves go straight to UMAMI_HOST (lib/analytics.ts)
  async rewrites() {
    return [{ source: '/favicon.ico', destination: '/favicon.svg' }, ...umamiRewrites()]
  },
  // the CSP itself comes from proxy.ts (it needs a fresh nonce per request); the rest, and a static CSP for the
  // paths proxy.ts skips, from lib/headers.ts
  async headers() {
    return securityHeaders()
  },
}

export default withNextIntl(config)
