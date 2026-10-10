// The response headers next.config sets on every answer (re-check 4). The page CSP is not here: it needs a fresh nonce
// per request, so proxy.ts writes it (lib/csp.ts buildCsp).
import { STATIC_CSP } from './csp'

// Browser features the site never uses, switched off for it and for anything it might ever embed
export const PERMISSIONS_POLICY = [
  'camera=()', 'microphone=()', 'geolocation=()', 'payment=()', 'usb=()', 'serial=()', 'bluetooth=()', 'hid=()',
  'midi=()', 'magnetometer=()', 'gyroscope=()', 'accelerometer=()', 'display-capture=()', 'browsing-topics=()',
].join(', ')

// HSTS: browsers honour it only over HTTPS, so on frondia.eu (TLS at the proxy) it takes effect and on a local http
// run it is ignored. A year, this host only: includeSubDomains and preload are a domain-wide decision (Elena's,
// at the proxy), not this app's.
export const HSTS = 'max-age=31536000'

export type HeaderRule = { source: string; headers: { key: string; value: string }[] }

export function securityHeaders(): HeaderRule[] {
  return [
    {
      source: '/:path*',
      headers: [
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'Permissions-Policy', value: PERMISSIONS_POLICY },
        { key: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
        { key: 'Strict-Transport-Security', value: HSTS },
      ],
    },
    // A path with an extension skips proxy.ts (its matcher), so nothing gave it a CSP: data files, photos, the og card,
    // the SVG favicon (an SVG opened on its own is a document that could run script) and — the one HTML page — the 404
    // for an address such as /wp-login.php. A static policy, with no nonce: such a 404 renders but does not hydrate.
    // Paths without a dot never match here, so a page never carries two policies.
    { source: '/:path(.*\\..*)', headers: [{ key: 'Content-Security-Policy', value: STATIC_CSP }] },
  ]
}
