'use client'
import { useEffect, useRef } from 'react'
import { CONSENT_EVENT, onStorageChoice, safeStorage, readChoice, type Choice } from '@/lib/consent'

// Microsoft Clarity, project ypa2k9inj5 — loaded only after "Accept", never before. Reproduces the
// snippet Elena got from Microsoft (queue function + async tag) instead of an inline <script> string,
// so the CSP nonce can sit on the element the way the rest of the site's scripts get it.
type ClarityFn = { (...args: unknown[]): void; q?: unknown[] }
declare global {
  interface Window { clarity?: ClarityFn }
}

// Clarity's own first-party cookies (_clck: an anonymous id kept across sessions; _clsk: the current
// session). Cleared on withdrawal so a "Decline" genuinely leaves nothing behind while the reload
// that follows is still in flight.
const CLARITY_COOKIES = ['_clck', '_clsk']

function expireCookie(name: string, domain?: string): void {
  const base = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`
  document.cookie = domain ? `${base}; domain=${domain}` : base
}

// Where Clarity may have set them: host-only, on the host itself, and on its parent domain (the last
// two labels — frondia.eu for www.frondia.eu, and the host itself when it has only two). Derived from
// the address, so a preview host or a new domain is cleaned the same way. Not for an IP or localhost.
export function cookieDomains(hostname: string): string[] {
  const labels = hostname.split('.')
  if (labels.length < 2 || /^[\d.]+$/.test(hostname) || hostname.includes(':')) return []
  return [...new Set([hostname, labels.slice(-2).join('.')])].map((d) => `.${d}`)
}

function clearClarityCookies(): void {
  const domains = cookieDomains(window.location.hostname)
  for (const name of CLARITY_COOKIES) {
    expireCookie(name)
    for (const d of domains) expireCookie(name, d)
  }
}

export function Clarity({ id, nonce }: { id: string; nonce?: string }) {
  const loaded = useRef(false)

  useEffect(() => {
    function load() {
      if (loaded.current) return
      loaded.current = true
      if (!window.clarity) {
        const fn: ClarityFn = (...args: unknown[]) => {
          fn.q = fn.q || []
          fn.q.push(args)
        }
        window.clarity = fn
      }
      const script = document.createElement('script')
      script.async = true
      script.src = `https://www.clarity.ms/tag/${id}`
      if (nonce) script.setAttribute('nonce', nonce)
      const first = document.getElementsByTagName('script')[0]
      first?.parentNode?.insertBefore(script, first)
      window.clarity!('consentv2', { ad_Storage: 'denied', analytics_Storage: 'granted' })
    }

    function withdraw() {
      // Clarity cannot be unloaded once its tag has run: tell it consent is gone, drop its
      // cookies, then reload to start clean.
      window.clarity?.('consentv2', { ad_Storage: 'denied', analytics_Storage: 'denied' })
      clearClarityCookies()
      window.location.reload()
    }

    function handle(choice: Choice | null) {
      if (choice === 'granted') load()
      else if (loaded.current) withdraw()
    }

    if (readChoice(safeStorage()) === 'granted') load()

    function onConsent(e: Event) {
      handle((e as CustomEvent<Choice | null>).detail)
    }
    window.addEventListener(CONSENT_EVENT, onConsent)
    // Cross-tab: a Decline/withdrawal (or a fresh Accept) in another tab reaches this one too, so
    // Clarity never keeps running here after consent was pulled somewhere else.
    const offStorage = onStorageChoice(handle)
    // Back/forward cache: a page restored from it kept its old state (Clarity running) while the
    // choice may have been withdrawn on another page meanwhile — check again on every restore.
    function onPageShow(e: PageTransitionEvent) {
      if (e.persisted) handle(readChoice(safeStorage()))
    }
    window.addEventListener('pageshow', onPageShow)
    return () => {
      window.removeEventListener(CONSENT_EVENT, onConsent)
      window.removeEventListener('pageshow', onPageShow)
      offStorage()
    }
  }, [id, nonce])

  return null
}
