'use client'
import { useEffect, useRef, useState } from 'react'
import { localePath } from '@/i18n/locales'
import { EV } from '@/lib/analytics'
import { onOpenConsent, onStorageChoice, readChoice, safeStorage, saveChoice, type Choice } from '@/lib/consent'
import { useT } from '@/lib/t-client'
import { plain } from '@/lib/typography'

// A no-op fallback so a choice still gets dispatched (and this tab's own banner still hides) even if
// localStorage itself is unreachable (sandboxed iframe, storage disabled by policy) — saveChoice
// dispatches `frondia:consent` regardless of whether the write actually landed.
const NOOP_STORAGE: Pick<Storage, 'setItem'> = { setItem() {} }

// Shown once, after hydration (so the server-rendered page and the first client render match — no
// flash of a banner the crawler or a no-JS visitor never sees). Reopened from /privacy via openConsent().
// back to where focus stood before, if that control is still there and shown; otherwise to the page's <main>, without
// scrolling (never to the page's top)
function giveFocusBack(el: HTMLElement | null) {
  if (el && el.isConnected && el.getClientRects().length && !el.closest('[inert], [hidden]') && !(el as HTMLButtonElement).disabled) {
    el.focus()
    if (document.activeElement === el) return
  }
  const main = document.getElementById('main')
  if (!main) return
  if (!main.hasAttribute('tabindex')) main.tabIndex = -1
  main.focus({ preventScroll: true })
}

export function ConsentBanner() {
  const { t, loc } = useT('common')
  const [visible, setVisible] = useState(false)
  const card = useRef<HTMLDivElement>(null)
  // the last place focus stood outside the card: a choice gives it back there (WCAG 2.4.3; round-2 re-check, 6 Oct 2026 —
  // the button pressed went with the card and focus fell to <body>, so the next Tab started again from the page's top)
  const before = useRef<HTMLElement | null>(null)

  useEffect(() => {
    setVisible(readChoice(safeStorage()) === null)
    const offOpen = onOpenConsent(() => setVisible(true))
    // Cross-tab: a choice made (or withdrawn) in another tab updates this tab's banner too.
    const offStorage = onStorageChoice((choice) => setVisible(choice === null))
    return () => { offOpen(); offStorage() }
  }, [])

  // the card's height as --consent-h on the root while it is up: the atlas, which does not scroll, makes that much room
  // above it (atlas.css; WCAG 2.4.11, Elena, 5 Oct 2026). It changes with the language and the width, so it is measured
  useEffect(() => {
    const el = card.current, root = document.documentElement
    if (!visible || !el) return
    const set = () => root.style.setProperty('--consent-h', `${Math.ceil(el.getBoundingClientRect().height)}px`)
    set()
    const ro = new ResizeObserver(set)
    ro.observe(el)
    return () => { ro.disconnect(); root.style.removeProperty('--consent-h') }
  }, [visible])

  useEffect(() => {
    if (!visible) return
    const keep = (e: Element | null) => {
      if (e instanceof HTMLElement && e !== document.body && !card.current?.contains(e)) before.current = e
    }
    keep(document.activeElement)
    const onFocus = (e: FocusEvent) => keep(e.target as Element | null)
    document.addEventListener('focusin', onFocus)
    return () => document.removeEventListener('focusin', onFocus)
  }, [visible])

  function choose(choice: Choice) {
    saveChoice(safeStorage() ?? NOOP_STORAGE, choice)
    // only when focus would be lost with the card (a mouse click in Safari leaves it where it was: then it stays)
    const a = document.activeElement
    if (!a || a === document.body || card.current?.contains(a)) giveFocusBack(before.current)
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div className="consent-banner" ref={card} role="region" aria-label={plain(t('consent.label'))}>
      {/* on a short screen (≤ 400 px tall: a phone on its side, 400 % zoom) the card shows the short line instead, and
          the Privacy link below carries the rest (consent.css); the same two buttons either way */}
      <p className="consent-text consent-text--full">{t('consent.text')}</p>
      <p className="consent-text consent-text--short">{t('consent.short')}</p>
      <div className="consent-actions">
        <button
          type="button"
          className="pill pill--ghost"
          data-ev={EV.consent}
          data-ev-choice="granted"
          onClick={() => choose('granted')}
        >
          {t('consent.accept')}
        </button>
        <button
          type="button"
          className="pill pill--ghost"
          data-ev={EV.consent}
          data-ev-choice="denied"
          onClick={() => choose('denied')}
        >
          {t('consent.decline')}
        </button>
        <a className="consent-privacy" href={localePath(loc, '/privacy')}>{t('consent.privacy')}</a>
      </div>
    </div>
  )
}
