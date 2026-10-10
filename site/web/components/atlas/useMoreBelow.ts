'use client'
import { useEffect, useRef, type RefObject } from 'react'

// A floating card scrolls inside itself. While more of it waits below the fold, the card carries
// data-more-below and its lower edge fades; once it is scrolled, data-more-above fades the upper edge
// (atlas.css). Osmo's "Hide Scrollbar" names the fade as the cue a scrolling area needs; the card keeps
// its thin bar as well. Content changes (a new lens, a longer list) move the fold without a scroll
// event, so size and content changes are watched too. Ported from site/apps/atlas/src/lib/moreBelow.js.
export function useMoreBelow<T extends HTMLElement>(): RefObject<T | null> {
  const ref = useRef<T | null>(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return undefined
    let frame = 0
    const flag = (name: string, on: boolean) => { if (on !== el.hasAttribute(name)) el.toggleAttribute(name, on) }
    const update = () => {
      frame = 0
      flag('data-more-below', el.scrollTop + el.clientHeight < el.scrollHeight - 4)
      flag('data-more-above', el.scrollTop > 4)
    }
    const later = () => { if (!frame) frame = requestAnimationFrame(update) }
    update()
    el.addEventListener('scroll', later, { passive: true })
    // the card and each block in it: text can grow without a DOM change (a web font arriving)
    const ro = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(later)
    const watch = () => { if (!ro) return; ro.disconnect(); ro.observe(el); for (const k of Array.from(el.children)) ro.observe(k) }
    watch()
    const mo = new MutationObserver(() => { watch(); later() })
    mo.observe(el, { childList: true, subtree: true })
    return () => {
      el.removeEventListener('scroll', later)
      ro?.disconnect()
      mo.disconnect()
      if (frame) cancelAnimationFrame(frame)
    }
  }, [])
  return ref
}
