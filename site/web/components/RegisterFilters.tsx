'use client'
import { useCallback, useEffect, useState, useTransition, type ReactNode } from 'react'
import { useRouter } from '@/i18n/navigation'
import { viewQuery, type Show } from '@/lib/register-view'
import { plain } from '@/lib/typography'

/* The register's filter (Maze's result tabs with their counts) and the jump to one contract, 1:1 with
   site/apps/landing/src/pages/Register.jsx. A tab or the checkbox replaces the address
   (/register?show=…&checked=1, through next-intl's router, so the language prefix stays) without
   moving the page, and the server sends that view's rows; the pressed tab and the box show the choice
   at once, not only when the rows arrive. Until they do, the list is aria-busy and the list and the tab
   counts fade (register.css), so the new choice never reads as the old view's numbers; focus stays on
   the control that was used. The words and the rows come from the server, already set: the rows are
   this component's children, and the list around them is rendered here only to carry aria-busy. */

export interface Tab { k: Show; name: string; n: string; count: number }

// a contract's row: into view, and focus on it for the keyboard, as the old page did
function land(id: number): boolean {
  const el = document.getElementById(`c${id}`)
  if (!el) return false
  el.scrollIntoView({ block: 'start' })
  el.focus({ preventScroll: true })
  return true
}

// Go to a contract (#c<id>). The row may be filtered out: the filter is cleared first, and the page
// waits for the row to arrive with the server's answer — no reload either way.
function useGoTo() {
  const router = useRouter()
  return useCallback((id: number) => {
    if (document.getElementById(`c${id}`)) {
      requestAnimationFrame(() => requestAnimationFrame(() => land(id)))
      return
    }
    const obs = new MutationObserver(() => { if (land(id)) { obs.disconnect(); clearTimeout(timer) } })
    const timer = setTimeout(() => obs.disconnect(), 10000)
    obs.observe(document.body, { childList: true, subtree: true })
    router.replace('/register', { scroll: false })
  }, [router])
}

export function RegisterFilters({ show, checked, tabs, label, only, live, children }: {
  show: Show; checked: boolean; tabs: Tab[]; label: string; only: ReactNode; live: string; children: ReactNode
}) {
  const router = useRouter()
  const goTo = useGoTo()
  const [pending, startTransition] = useTransition()
  const [view, setViewState] = useState({ show, checked })
  useEffect(() => { setViewState({ show, checked }) }, [show, checked])

  const setView = (s: Show, ch: boolean) => {
    setViewState({ show: s, checked: ch })
    startTransition(() => { router.replace(`/register${viewQuery(s, ch)}`, { scroll: false }) })
  }

  // a shared link to one contract (#c87) lands on it, and so does a later change of the hash
  useEffect(() => {
    const go = () => {
      const m = /^#c(\d+)$/.exec(location.hash)
      if (m) goTo(Number(m[1]))
    }
    go()
    window.addEventListener('hashchange', go)
    return () => window.removeEventListener('hashchange', go)
  }, [goTo])

  return (
    <>
      <div className="reg-filter reg-wide" data-pending={pending ? '' : undefined}>
        <div className="reg-tabs" role="group" aria-label={plain(label)}>
          {tabs.map(({ k, name, n, count }) => (
            <button key={k} type="button" aria-pressed={view.show === k} disabled={k !== 'all' && !count} onClick={() => setView(k, view.checked)}>
              {name} <span className="reg-tab-n">{n}</span>
            </button>
          ))}
        </div>
        <label className="reg-only">
          <input type="checkbox" id="reg-checked" checked={view.checked} onChange={(e) => setView(view.show, e.target.checked)} />
          {only}
        </label>
      </div>
      <p className="sr-only" aria-live="polite">{live}</p>
      <div className="reg-list reg-wide" aria-busy={pending ? 'true' : undefined}>{children}</div>
    </>
  )
}

// a disagreement's "its quotes": to its contract's row, in place
export function RecordLink({ id, children }: { id: number; children: ReactNode }) {
  const goTo = useGoTo()
  return (
    <a className="reg-miss-link" href={`#c${id}`} onClick={(e) => { e.preventDefault(); goTo(id) }}>{children}</a>
  )
}
