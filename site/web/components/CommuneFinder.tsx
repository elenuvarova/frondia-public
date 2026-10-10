'use client'
import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import { useRouter } from '@/i18n/navigation'
import { matches, type FinderItem } from '@/lib/finder'
import { plain } from '@/lib/typography'

export interface FinderLabels { label: string; placeholder: string; none: string }

/* "Find a commune" (the commune page, plan 3 task 3): 1:1 with CommuneFinder in
   site/apps/landing/src/pages/Commune.jsx. An ARIA 1.2 combobox with a listbox popup (the APG's
   pattern): type to filter, arrows to move, Enter to go, Escape to close (a second Escape clears the
   field); the list shows every commune while the field is empty. Going to a commune is a client-side
   navigation through next-intl's router, so the address keeps its language prefix. Its words come
   from the server as props, each commune's name and city in the page's language and its "NIS …"
   already written (lib/commune.ts finderItems): the browser is sent only the few words the layout picks (lib/client-messages.ts). The list closes when focus leaves the
   field (a Tab past it left the open list over the next controls, WCAG 2.4.11; a click on an option keeps the focus,
   its pointerdown is prevented), and the active option carries the focus ring (re-check 2). */
export function CommuneFinder({ communes, labels, current }: { communes: FinderItem[]; labels: FinderLabels; current?: string }) {
  const router = useRouter()
  const id = useId()
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const box = useRef<HTMLDivElement>(null)
  const hits = useMemo(() => matches(communes, q), [q, communes])
  useEffect(() => { setActive(0) }, [q])
  useEffect(() => {
    const off = (e: PointerEvent) => { if (!box.current?.contains(e.target as Node)) setOpen(false) }
    document.addEventListener('pointerdown', off)
    return () => document.removeEventListener('pointerdown', off)
  }, [])
  const go = (c: FinderItem) => { setOpen(false); setQ(''); router.push(`/commune?code=${c.code}`) }
  const onKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); setActive((i) => Math.min(hits.length - 1, i + (open ? 1 : 0))) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((i) => Math.max(0, i - 1)) }
    else if (e.key === 'Enter' && open && hits[active]) { e.preventDefault(); go(hits[active]!) }
    else if (e.key === 'Escape') { if (open) setOpen(false); else setQ('') }
  }
  const optId = (i: number) => `${id}-opt-${i}`
  return (
    <div className="finder" ref={box}>
      <label className="sr-only" htmlFor={`${id}-in`}>{labels.label}</label>
      <div className="finder-field">
        <svg className="finder-mag" viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="4.75" /><path d="M10.5 10.5 14 14" /></svg>
        <input id={`${id}-in`} type="text" role="combobox" autoComplete="off" spellCheck="false"
               aria-expanded={open} aria-controls={`${id}-list`} aria-autocomplete="list"
               aria-activedescendant={open && hits[active] ? optId(active) : undefined}
               placeholder={plain(labels.placeholder)} value={q}
               onChange={(e) => { setQ(e.target.value); setOpen(true) }} onFocus={() => setOpen(true)} onKeyDown={onKey}
               onBlur={() => setOpen(false)} />
      </div>
      {open && (
        <ul className="finder-list" role="listbox" id={`${id}-list`} aria-label={plain(labels.label)} onPointerDown={(e) => e.preventDefault()}>
          {hits.length ? hits.map((o, i) => (
            <li key={o.code} id={optId(i)} role="option" aria-selected={i === active} className={o.code === current ? 'is-current' : ''}
                onPointerDown={(e) => e.preventDefault()} onClick={() => go(o)} onPointerMove={() => setActive(i)}>
              <span className="finder-name">{o.name}<small>{o.nis}</small></span>
              <span className="finder-tag">{o.city}</span>
            </li>
          )) : <li className="finder-none" role="option" aria-disabled="true" aria-selected="false">{labels.none}</li>}
        </ul>
      )}
    </div>
  )
}
