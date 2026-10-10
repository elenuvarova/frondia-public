'use client'
import { useEffect, useRef } from 'react'

/* A sector's card or an audit's drawer and the keyboard (re-check 2; WCAG 2.1.1, 2.4.3): opened from a control (a list
   row, a pin, the map, the card's "Audit: …"), focus moves to the card's heading, so the next Tab is inside it; Escape
   closes it; closed while focus was in it, focus goes back to what opened it, or to the map when that is gone. Opened by
   a link from outside (focus still on the page's body) it leaves focus where it is. `key` is what the card shows: a new
   sector in the same card counts as opening it again. Returns the ref for the heading (tabIndex -1). */
export function useDrawerFocus<T extends HTMLElement>(onClose: () => void, key: string) {
  const head = useRef<T>(null)
  const close = useRef(onClose)
  close.current = onClose
  useEffect(() => {
    const from = document.activeElement instanceof HTMLElement || document.activeElement instanceof SVGElement
      ? document.activeElement as HTMLElement | SVGElement : null
    const byControl = !!from && from !== document.body && !!from.closest('.atlas')
    if (byControl && !head.current?.closest('.drawer')?.contains(from)) head.current?.focus({ preventScroll: true })
    return () => {
      // only when focus was in the card (it went with it, to the body): a click on a question or a lens keeps its focus
      const now = document.activeElement
      if (now && now !== document.body && now.isConnected) return
      const back = byControl && from!.isConnected && !from!.closest('.drawer') ? from : document.querySelector<SVGSVGElement>('.atlas-svg > svg')
      back?.focus({ preventScroll: true })
    }
  }, [key])
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && !e.defaultPrevented) { e.preventDefault(); close.current() } }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])
  return head
}
