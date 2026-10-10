'use client'
import { useEffect } from 'react'
import { BEFORE_SEND, EV, dropView } from '@/lib/analytics'

// The site's own click events, sent through Umami's tracker (window.umami, from components/Umami.tsx).
// Umami's built-in data-umami-event handling is NOT used: on a link it cancels the navigation and
// only follows the link once the send has come back (a slow Umami holds up every way into the atlas),
// and on a <summary> it only sees clicks on the summary itself, never on the question text inside it.
// Instead: an element with `data-ev="<name>"` sends that event on click, with every
// `data-ev-<key>="<value>"` as its data — nothing is prevented, and Umami's send uses fetch keepalive,
// so it outlives the navigation. A FAQ question (<details class="faq-item" id="q-<id>">) sends
// faq-open when it opens, however it was opened. No Umami (no website id, Do Not Track, another
// domain) — window.umami is missing or does nothing, and so does this.
// Elements that are not HTML (the atlas's SVG audit pins) call `track` themselves.
// It also installs the tracker's data-before-send filter (lib/analytics BEFORE_SEND): a page view the
// atlas, the data page or the register causes by rewriting its own address (replaceState,
// router.replace) is dropped; the first view of each, views of every other page and every named
// event pass unchanged.
type Umami = { track: (name: string, data?: Record<string, string>) => unknown }
type Payload = { name?: string; url?: unknown; referrer?: unknown }
declare global {
  interface Window {
    umami?: Umami
    [BEFORE_SEND]?: (type: string, payload: Payload) => Payload | null
  }
}

export function track(name: string, data?: Record<string, string>): void {
  try {
    window.umami?.track(name, data)
  } catch {
    // counting never breaks the page
  }
}

// data-ev-from="hero" → { from: 'hero' }; data-ev-some-key → { someKey }
function dataOf(el: HTMLElement): Record<string, string> | undefined {
  const data: Record<string, string> = {}
  for (const [k, v] of Object.entries(el.dataset)) {
    if (k.length > 2 && k.startsWith('ev') && v !== undefined) data[k[2]!.toLowerCase() + k.slice(3)] = v
  }
  return Object.keys(data).length ? data : undefined
}

export function Events() {
  useEffect(() => {
    window[BEFORE_SEND] = (type, payload) => (dropView(type, payload, location.origin) ? null : payload)
    // capture phase on window: runs before any other click handler (a Next <Link> that navigates
    // client-side, a React onClick that unmounts the button) and never waits on anything
    function onClick(e: MouseEvent) {
      const el = (e.target as Element | null)?.closest?.('[data-ev]')
      if (!(el instanceof HTMLElement)) return
      const name = el.dataset.ev
      if (name) track(name, dataOf(el))
    }
    // `toggle` does not bubble, but a capturing listener still sees it for every <details> below
    function onToggle(e: Event) {
      const d = e.target
      if (!(d instanceof HTMLDetailsElement) || !d.open || !d.classList.contains('faq-item')) return
      const m = d.id.match(/^q-(.+)$/)
      if (m) track(EV.faq, { id: m[1]! })
    }
    window.addEventListener('click', onClick, true)
    document.addEventListener('toggle', onToggle, true)
    return () => {
      window.removeEventListener('click', onClick, true)
      document.removeEventListener('toggle', onToggle, true)
      delete window[BEFORE_SEND]
    }
  }, [])
  return null
}
