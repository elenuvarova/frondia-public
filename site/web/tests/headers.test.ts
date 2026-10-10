import { unstable_getResponseFromNextConfig as respond } from 'next/experimental/testing/server'
import { expect, test } from 'vitest'
import { STATIC_CSP } from '@/lib/csp'
import { HSTS, PERMISSIONS_POLICY, securityHeaders } from '@/lib/headers'

// re-check 4: the headers next.config sets, run through Next's own header matching (not a regex of our own)
const at = (path: string) => respond({ url: `https://frondia.eu${path}`, nextConfig: { headers: async () => securityHeaders() } })

test('every answer carries the hardening headers, with Permissions-Policy, COOP and HSTS', async () => {
  for (const p of ['/', '/atlas', '/data/brussels.json', '/og/en.jpg', '/health', '/icon/0', '/_next/static/chunks/a.js']) {
    const h = (await at(p)).headers
    expect(h.get('x-content-type-options'), p).toBe('nosniff')
    expect(h.get('x-frame-options'), p).toBe('DENY')
    expect(h.get('referrer-policy'), p).toBe('strict-origin-when-cross-origin')
    expect(h.get('permissions-policy'), p).toBe(PERMISSIONS_POLICY)
    expect(h.get('cross-origin-opener-policy'), p).toBe('same-origin')
    expect(h.get('strict-transport-security'), p).toBe(HSTS)
  }
  expect(PERMISSIONS_POLICY).toContain('geolocation=()')
  expect(PERMISSIONS_POLICY).toContain('camera=()')
  expect(HSTS).toMatch(/^max-age=\d{8,}/)
})

test('a path with an extension (skipped by proxy.ts) gets the static CSP; a page path never gets a second policy', async () => {
  for (const p of ['/wp-login.php', '/foo.php', '/data/brussels.json', '/favicon.svg', '/og/en.jpg', '/u/script.js']) {
    expect((await at(p)).headers.get('content-security-policy'), p).toBe(STATIC_CSP)
  }
  for (const p of ['/', '/atlas', '/dossier', '/en/privacy', '/health', '/icon/0', '/apple-icon']) {
    expect((await at(p)).headers.get('content-security-policy'), p).toBeNull()
  }
  expect(STATIC_CSP).toContain("script-src 'self';")
  expect(STATIC_CSP).not.toMatch(/script-src[^;]*unsafe-inline/)
  expect(STATIC_CSP).toContain("frame-ancestors 'none'")
})
