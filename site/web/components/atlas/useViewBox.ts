'use client'
import { useCallback, useEffect, useMemo, useRef, useState, type PointerEvent, type RefObject } from 'react'
import { clampView, fitBox as fitArea, type Box, type Size, type ViewBox } from '@/lib/atlas/geometry'

/* ── pan & zoom on the SVG viewBox (Atlas.jsx 24–128) ──────────────────────────────────────────────
   The viewBox always has the container's aspect, so screen ↔ map is one scale `s`. "Fit" places a box in the part
   of the stage that the floating panels leave free (lib/atlas/geometry.ts holds the arithmetic). */
export function useViewBox(svgRef: RefObject<SVGSVGElement | null>, W: number, H: number) {
  const [el, setEl] = useState<HTMLElement | null>(null)
  const [size, setSize] = useState<Size | null>(null)
  const [vb, setVb] = useState<ViewBox>({ x: 0, y: 0, w: W, h: H })
  // the view as last set, for a flight's start: read here, never inside a setVb updater (updaters must stay pure —
  // development's StrictMode runs them twice, which would start two animation loops)
  const vbRef = useRef(vb)
  vbRef.current = vb
  const put = useCallback((v: ViewBox) => { vbRef.current = v; setVb(v) }, [])
  const drag = useRef<{ x: number; y: number; vb: ViewBox } | null>(null)
  const moved = useRef(false)
  // the fingers on the map, and a pinch's last span and midpoint: two fingers zoom about their midpoint and pan with it
  // (the map is touch-action: none, so the browser's own pinch never reaches the page; before re-check 1 the second
  // finger restarted the drag from where it landed and the map jumped)
  const fingers = useRef(new Map<number, { x: number; y: number }>())
  const pinch = useRef<{ d: number; x: number; y: number } | null>(null)
  const anim = useRef(0)
  // the latest home and map size for the stable handlers below (zoomAt never changes: the wheel listener is bound once)
  const S = useRef<{ home: ViewBox; W: number; H: number }>({ home: { x: 0, y: 0, w: W, h: H }, W, H })

  useEffect(() => {
    if (!el) return
    const ro = new ResizeObserver(([e]) => { if (e) setSize({ w: e.contentRect.width, h: e.contentRect.height }) })
    ro.observe(el)
    return () => ro.disconnect()
  }, [el])

  // `drawer`: a card is open on the right, keep the target out from under it. No stage measured yet: no fit
  const fitBox = useCallback((b: Box | null, pad = 1, drawer = false): ViewBox | null => {
    if (!size || !b) return null
    return fitArea(size, b, pad, drawer)
  }, [size])

  const home = useMemo(() => fitBox({ x0: 0, y0: 0, x1: W, y1: H }) || { x: 0, y: 0, w: W, h: H }, [fitBox, W, H])
  useEffect(() => { put(home) }, [home, put])
  // a flight still running when the atlas leaves the page stops with it
  useEffect(() => () => cancelAnimationFrame(anim.current), [])
  S.current = { home, W, H }

  const clamp = (v: ViewBox, from?: ViewBox) => clampView(v, S.current.home, S.current.W, S.current.H, from)
  const toSvg = (cx: number, cy: number) => {
    const svg = svgRef.current!
    const p = svg.createSVGPoint(); p.x = cx; p.y = cy
    return p.matrixTransform(svg.getScreenCTM()!.inverse())
  }
  const zoomAt = useCallback((cx: number, cy: number, f: number) => {
    if (!svgRef.current?.getScreenCTM()) return
    const p = toSvg(cx, cy)
    setVb((v) => {
      const n = clamp({ x: p.x - (p.x - v.x) * f, y: p.y - (p.y - v.y) * f, w: v.w * f, h: v.h * f })
      const k = n.w / v.w
      // about the pointer, then within the pan's bounds: a wheel over the empty edge of the stage zoomed the city away
      return clamp({ ...n, x: p.x - (p.x - v.x) * k, y: p.y - (p.y - v.y) * k }, v)
    })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const flyTo = useCallback((target: ViewBox | null, ms = 800) => {
    if (!target) return
    cancelAnimationFrame(anim.current)
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { put(target); return }
    const from = vbRef.current
    const t0 = performance.now()
    const ease = (t: number) => 1 - Math.pow(1 - t, 3)
    const step = (now: number) => {
      const t = Math.min(1, (now - t0) / ms), k = ease(t)
      put({ x: from.x + (target.x - from.x) * k, y: from.y + (target.y - from.y) * k,
            w: from.w + (target.w - from.w) * k, h: from.h + (target.h - from.h) * k })
      if (t < 1) anim.current = requestAnimationFrame(step)
    }
    anim.current = requestAnimationFrame(step)
  }, [put])

  // the keyboard's pan (re-check 2, WCAG 2.1.1): the arrows move the view by a share of its size, within the same bounds
  // as a drag
  const panBy = useCallback((dx: number, dy: number) => {
    cancelAnimationFrame(anim.current)
    const v = vbRef.current
    put(clampView({ ...v, x: v.x + dx, y: v.y + dy }, S.current.home, S.current.W, S.current.H, v))
  }, [put])

  // callback ref: remember the stage and bind a native non-passive wheel listener; React 19 calls the returned cleanup
  // when the node goes (and between development's StrictMode double runs), so one tick never zooms twice
  const ref = useCallback((node: HTMLDivElement | null) => {
    setEl(node)
    if (!node) return
    const onWheel = (e: WheelEvent) => { e.preventDefault(); zoomAt(e.clientX, e.clientY, Math.exp(e.deltaY * 0.0016)) }
    node.addEventListener('wheel', onWheel, { passive: false })
    return () => { node.removeEventListener('wheel', onWheel); setEl(null) }
  }, [zoomAt])

  const span = () => {
    const [a, b] = [...fingers.current.values()]
    return { d: Math.hypot(b!.x - a!.x, b!.y - a!.y), x: (a!.x + b!.x) / 2, y: (a!.y + b!.y) / 2 }
  }
  const lift = (e: PointerEvent<HTMLDivElement>) => {
    fingers.current.delete(e.pointerId)
    if (fingers.current.size < 2) pinch.current = null
    drag.current = null
  }

  const handlers = {
    ref,
    onPointerDown: (e: PointerEvent<HTMLDivElement>) => {
      if (e.button !== 0) return
      cancelAnimationFrame(anim.current)
      if (e.pointerType === 'touch') fingers.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
      if (fingers.current.size === 2) {
        // a second finger: a pinch, never a tap or the drag the first finger began
        pinch.current = span()
        drag.current = null
        moved.current = true
        e.currentTarget.setPointerCapture?.(e.pointerId)
        return
      }
      drag.current = { x: e.clientX, y: e.clientY, vb }
      moved.current = false
    },
    onPointerMove: (e: PointerEvent<HTMLDivElement>) => {
      if (fingers.current.has(e.pointerId)) fingers.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
      const last = pinch.current
      if (last && fingers.current.size >= 2) {
        const now = span()
        const ctm = svgRef.current?.getScreenCTM()
        if (ctm) setVb((v) => clamp({ ...v, x: v.x - (now.x - last.x) / ctm.a, y: v.y - (now.y - last.y) / ctm.a }, v))
        if (now.d > 0) zoomAt(now.x, now.y, last.d / now.d)
        pinch.current = now
        return
      }
      const d = drag.current
      if (!d) return
      const dx = e.clientX - d.x, dy = e.clientY - d.y
      if (!moved.current && Math.hypot(dx, dy) < 4) return
      if (!moved.current) { moved.current = true; e.currentTarget.setPointerCapture?.(e.pointerId) }
      const ctm = svgRef.current?.getScreenCTM()
      if (!ctm) return
      put(clamp({ ...d.vb, x: d.vb.x - dx / ctm.a, y: d.vb.y - dy / ctm.a }, d.vb))
    },
    onPointerUp: lift,
    onPointerCancel: lift,
  }
  return { vb, size, home, zoomAt, flyTo, fitBox, panBy, handlers, wasDrag: () => moved.current }
}
