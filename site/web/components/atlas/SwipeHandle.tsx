'use client'
import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent, type RefObject } from 'react'
import { useT } from '@/lib/t-client'
import { plain } from '@/lib/typography'

/* The whole city before and after: the handle of the swipe (Atlas.jsx 783–861). It writes --split (0…1 of the stage's
   width) on the stage, and the upper photo under the map reads it, so a drag re-renders the handle and nothing else.
   It stays on the free map: right of the panel and left of an open drawer, on a wide screen. The look is the landing's
   split slider (Osmo); the knob is a slider for keyboards and screen readers: arrows ±2 %, Page ±10 %, Home / End to
   the ends. */
const KNOB_ROOM = 120   // px a year tag needs beside the knob

export function SwipeHandle({ stageRef, years }: { stageRef: RefObject<HTMLElement | null>; years: [number, number] }) {
  const { t } = useT('atlas')
  const a = String(years[0]), b = String(years[1])
  const [split, setSplit] = useState(0.5)
  const [room, setRoom] = useState({ before: true, after: true })
  const [knobY, setKnobY] = useState<number | null>(null)
  const at = useRef(0.5), drag = useRef(false)
  // the free map: on a wide screen right of the panel and left of an open drawer, the knob in the lower quarter (a
  // picked place lands mid-map); on a phone the cards sit at the bottom, so the knob sits just above the higher of
  // them and below the zoom buttons
  const bounds = (): [number, number, number, number | null] => {
    const st = stageRef.current
    if (!st) return [0, 1, 1, null]
    const r = st.getBoundingClientRect()
    const panel = st.querySelector(':scope > .panel'), drawer = st.querySelector(':scope > .drawer')
    let lo = 16, hi = r.width - 16, y = r.height * 0.76
    if (window.matchMedia('(min-width: 861px)').matches) {
      if (panel) lo = Math.max(lo, panel.getBoundingClientRect().right - r.left + 24)
      if (drawer) hi = Math.min(hi, drawer.getBoundingClientRect().left - r.left - 24)
    } else {
      const zoom = st.querySelector(':scope > .zoom')
      const top = (zoom ? zoom.getBoundingClientRect().bottom - r.top : 0) + 30
      const cards = [panel, drawer].filter((x): x is Element => !!x).map((el) => el.getBoundingClientRect().top - r.top)
      y = Math.max(top, Math.min(r.height, ...cards) - 40)
    }
    return [lo / r.width, hi / r.width, r.width, Math.round(y)]
  }
  const apply = (v: number) => {
    const [lo, hi, w, y] = bounds()
    setKnobY(y)
    const q = Math.min(hi, Math.max(lo, v))
    at.current = q
    stageRef.current?.style.setProperty('--split', String(q))
    setSplit(q)
    const before = (q - lo) * w > KNOB_ROOM, after = (hi - q) * w > KNOB_ROOM
    setRoom((p) => (p.before === before && p.after === after ? p : { before, after }))
  }
  // after every render: a drawer that opened or the panel's width may have moved the bounds
  useEffect(() => { apply(at.current) })
  useEffect(() => {
    const st = stageRef.current
    const on = () => apply(at.current)
    window.addEventListener('resize', on)
    st?.addEventListener('animationend', on)   // a drawer slides in: measure where it came to rest
    return () => { window.removeEventListener('resize', on); st?.removeEventListener('animationend', on); st?.style.removeProperty('--split') }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const toPointer = (e: PointerEvent) => { const r = stageRef.current!.getBoundingClientRect(); apply((e.clientX - r.left) / r.width) }
  const onDown = (e: PointerEvent<HTMLDivElement>) => {
    if (e.button) return
    e.preventDefault()
    // a tap on a year moves the split a tenth toward it: the split moves without a drag (WCAG 2.5.7; re-check 2, 3 Oct;
    // design wave, 5 Oct). The knob stays the keyboard's and the screen reader's (a slider), so the tags stay hidden to them
    const tag = (e.target as Element).closest('.swipe-tag')
    if (tag) { apply(at.current + (tag.classList.contains('is-before') ? -0.1 : 0.1)); return }
    e.currentTarget.setPointerCapture(e.pointerId)
    drag.current = true
    toPointer(e)
  }
  const onKey = (e: KeyboardEvent) => {
    const [lo, hi] = bounds()
    const step = ({ ArrowLeft: -0.02, ArrowDown: -0.02, ArrowRight: 0.02, ArrowUp: 0.02, PageDown: -0.1, PageUp: 0.1 } as Record<string, number>)[e.key]
    if (step != null) { e.preventDefault(); apply(at.current + step) }
    else if (e.key === 'Home') { e.preventDefault(); apply(lo) }
    else if (e.key === 'End') { e.preventDefault(); apply(hi) }
  }
  const p = Math.round(split * 100)
  const style = { left: `${split * 100}%`, '--knob-y': knobY == null ? undefined : `${knobY}px` } as CSSProperties
  return (
    <div className="swipe" style={style} onPointerDown={onDown}
         onPointerMove={(e) => { if (drag.current) toPointer(e) }}
         onPointerUp={() => { drag.current = false }} onPointerCancel={() => { drag.current = false }}>
      <span className="swipe-line" aria-hidden="true" />
      <span className={`swipe-tag is-before${room.before ? '' : ' is-hidden'}`} aria-hidden="true">{t('photos.tag', { y: a })}</span>
      <div className="swipe-knob" role="slider" tabIndex={0} aria-label={plain(t('photos.handle', { a, b }))}
           aria-valuemin={0} aria-valuemax={100} aria-valuenow={p} aria-valuetext={plain(t('photos.valueText', { p: String(p), a, b }))} onKeyDown={onKey}>
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" aria-hidden="true">
          <path d="M20.7931 11.5L15.2931 5.99995L16.0002 5.29285L22.3537 11.6464V12.3535L16.0002 18.7071L15.2931 18L20.793 12.5L3.20719 12.5L8.70714 18L8.00004 18.7071L1.64648 12.3535L1.64648 11.6464L8.00004 5.29285L8.70714 5.99995L3.2071 11.5L20.7931 11.5Z" fill="currentColor" />
        </svg>
      </div>
      <span className={`swipe-tag is-after${room.after ? '' : ' is-hidden'}`} aria-hidden="true">{t('photos.tag', { y: b })}</span>
    </div>
  )
}
