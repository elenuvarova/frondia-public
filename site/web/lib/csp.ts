// The same policy the nginx landing sent, with a per-request nonce for Next's inline scripts.
// Styles keep 'unsafe-inline': the charts set positions in style attributes.
// Clarity needs connect-src and img-src for its own domain and Microsoft's consent-check pixel
// (c.bing.com); its script-src needs nothing — strict-dynamic already trusts a script our nonced
// script creates, which is how Clarity is loaded (components/Clarity.tsx).
// Umami's tracker is served from this site (/u/script.js), but it posts the counts to Umami's own
// origin (so Umami sees the visitor's address, not this server's): that origin goes in connect-src
// only, and only when the counter is on. The shared dashboard's counter (lib/analytics SHARED_UMAMI) is loaded the same
// way: its origin is the fourth argument, connect-src only.
export function buildCsp(nonce: string, isDev: boolean, umamiOrigin?: string, sharedOrigin?: string): string {
  return [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ''}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob: https://*.clarity.ms https://c.bing.com",
    "font-src 'self' data:",
    `connect-src 'self'${umamiOrigin ? ` ${umamiOrigin}` : ''}${sharedOrigin ? ` ${sharedOrigin}` : ''} https://*.clarity.ms https://c.bing.com`,
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
  ].join('; ')
}

// For the responses proxy.ts never sees (a path with an extension: data, photos, the og card, the favicon, and the 404
// such an address gets): no inline script at all, everything else as the page policy without Clarity or Umami
// (lib/headers.ts).
export const STATIC_CSP = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self' data:",
  "connect-src 'self'",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
].join('; ')
