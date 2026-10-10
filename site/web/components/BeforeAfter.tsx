'use client'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useT } from '@/lib/t-client'
import { plain } from '@/lib/typography'

type GsapCore = typeof import('gsap')['gsap']
type DraggableInstance = InstanceType<typeof import('gsap/Draggable')['Draggable']>

interface BeforeAfterProps {
  before: string
  after: string
  altBefore: string
  altAfter: string
  tagBefore: ReactNode
  tagAfter: ReactNode
  label: string
  initial?: number
}

/* Before/After Split Slider — adapted from Osmo Supply (osmo.supply/resource/before-after-split-slider).
   Kept: data-splitter="wrap | after | handle", data-splitter-initial, a clip-path mask on the
   "after" layer, GSAP Draggable on the handle bounded by the wrap, re-measure on resize.
   Added on the way in: the handle is a slider for keyboards and screen readers (role="slider",
   arrows ±5, Page ±20, Home / End), the two halves carry their windows as tags, and the listeners
   and the Draggable are torn down on unmount. GSAP loads only when a slider is on the page.
   After review (26 Sep): the whole picture is the drag surface, and a tap moves the split to the
   finger — a 2-px line was a hard target on a phone. The jump happens on a tap (onClick) or once a
   horizontal drag has started (onDragStart), never on touchstart, so a vertical swipe that begins on
   the picture scrolls the page and leaves the split alone. Each tag rides in its own layer next to
   the split, so "Before" never sits on the after picture. zIndexBoost is off: Draggable's default
   lifts the handle to z-index 1000+ on every press, above the fixed nav. */
export function BeforeAfter({ before, after, altBefore, altAfter, tagBefore, tagAfter, initial = 50, label }: BeforeAfterProps) {
  const { t } = useT('common')
  const wrap = useRef<HTMLDivElement>(null), handle = useRef<HTMLDivElement>(null), afterEl = useRef<HTMLDivElement>(null)
  const [pct, setPct] = useState(initial)
  const pctRef = useRef(initial)
  const gs = useRef<GsapCore | null>(null), dragRef = useRef<DraggableInstance | null>(null)

  // a tag shows only where its half has room for all of it: measured in pixels, the tag's own width plus its 10-px gap and
  // 4 px from the frame. The old share of the width (27 % / 73 %) cut «Before» at the frame's edge where the frame is
  // narrow (288 px at 320 and at 1024, 325 at 360: design wave, 5 Oct)
  const tagB = useRef<HTMLSpanElement>(null), tagA = useRef<HTMLSpanElement>(null)
  const [show, setShow] = useState({ before: initial > 27, after: initial < 73 })

  // one mover for drag, keys and resize: GSAP owns the handle's x once it has loaded
  const place = (p: number) => {
    const w = wrap.current, h = handle.current, a = afterEl.current
    if (!w || !h || !a) return
    const q = Math.min(100, Math.max(0, p))
    const width = w.getBoundingClientRect().width, x = (q / 100) * width
    pctRef.current = q
    const before = x - 14 >= (tagB.current?.offsetWidth ?? 0), after = width - x - 14 >= (tagA.current?.offsetWidth ?? 0)
    setShow((o) => (o.before === before && o.after === after ? o : { before, after }))
    if (gs.current) { gs.current.set(h, { x }); dragRef.current?.update() }
    else h.style.transform = `translateX(${x}px)`
    a.style.clipPath = `inset(0 0 0 ${q}%)`
    setPct(Math.round(q))
  }

  useEffect(() => {
    place(initial)
    let drag: DraggableInstance | undefined, killed = false
    const onResize = () => place(pctRef.current)
    window.addEventListener('resize', onResize)
    Promise.all([import('gsap'), import('gsap/Draggable')]).then(([{ gsap }, { Draggable }]) => {
      if (killed || !handle.current) return
      gsap.registerPlugin(Draggable)
      gs.current = gsap
      handle.current.style.transform = ''
      // put the split under the pointer: on a tap, or once a horizontal drag has begun
      function jump(this: DraggableInstance) {
        const r = wrap.current!.getBoundingClientRect()
        const q = Math.min(100, Math.max(0, ((this.pointerX - r.left - window.scrollX) / r.width) * 100))   // pointerX is page x
        gsap.set(handle.current, { x: (q / 100) * r.width })
        this.update()
        pctRef.current = q
        afterEl.current!.style.clipPath = `inset(0 0 0 ${q}%)`
        setPct(Math.round(q))
      }
      ;[drag] = Draggable.create(handle.current, {
        type: 'x', trigger: wrap.current, bounds: wrap.current, cursor: 'ew-resize', activeCursor: 'grabbing',
        allowNativeTouchScrolling: true, zIndexBoost: false,
        onClick: jump,
        onDragStart: jump,
        onDrag() {
          const w = wrap.current!.getBoundingClientRect().width
          const q = (this.x / w) * 100
          pctRef.current = q
          afterEl.current!.style.clipPath = `inset(0 0 0 ${q}%)`
          setPct(Math.round(q))
        },
      })
      dragRef.current = drag ?? null
      place(pctRef.current)
    })
    return () => { killed = true; window.removeEventListener('resize', onResize); drag?.kill(); dragRef.current = null; gs.current = null }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const onKey = (e: React.KeyboardEvent) => {
    const step = ({ ArrowLeft: -5, ArrowDown: -5, ArrowRight: 5, ArrowUp: 5, PageDown: -20, PageUp: 20 } as Record<string, number>)[e.key]
    if (step != null) { e.preventDefault(); place(pctRef.current + step) }
    else if (e.key === 'Home') { e.preventDefault(); place(0) }
    else if (e.key === 'End') { e.preventDefault(); place(100) }
  }

  return (
    <div ref={wrap} data-splitter="wrap" data-splitter-initial={initial} className="splitter">
      <div className="splitter-content">
        <img src={before} alt={plain(altBefore)} loading="lazy" />
        <span ref={tagB} className={`splitter-tag splitter-tag--before${show.before ? '' : ' is-hidden'}`} style={{ right: `calc(${100 - pct}% + 10px)` }}>{tagBefore}</span>
      </div>
      <div ref={afterEl} data-splitter="after" className="splitter-content is--after">
        <img src={after} alt={plain(altAfter)} loading="lazy" />
        <span ref={tagA} className={`splitter-tag splitter-tag--after${show.after ? '' : ' is-hidden'}`} style={{ left: `calc(${pct}% + 10px)` }}>{tagAfter}</span>
      </div>
      <div ref={handle} data-splitter="handle" className="splitter-handle" role="slider" tabIndex={0}
           aria-label={plain(label)} aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct}
           aria-valuetext={plain(t('charts.beforeAfter', { before: String(pct), after: String(100 - pct) }))} onKeyDown={onKey}>
        <span className="splitter-handle__center" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
            <path d="M20.7931 11.5L15.2931 5.99995L16.0002 5.29285L22.3537 11.6464V12.3535L16.0002 18.7071L15.2931 18L20.793 12.5L3.20719 12.5L8.70714 18L8.00004 18.7071L1.64648 12.3535L1.64648 11.6464L8.00004 5.29285L8.70714 5.99995L3.2071 11.5L20.7931 11.5Z" fill="currentColor" />
          </svg>
        </span>
      </div>
    </div>
  )
}
