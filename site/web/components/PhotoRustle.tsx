'use client'
import { useEffect, useId, useRef, useState, type ReactNode } from 'react'
import { stillFromPage } from '@/lib/still'

export interface Photo { src: string; w: number; h: number }

interface PhotoRustleProps {
  photo: Photo
  phone?: Photo | null
  children?: ReactNode
  still?: boolean
  className?: string
  /** the name of the pause button (WCAG 2.2.2): given, the moving photo gets one */
  pauseLabel?: string
}

/** The landing's background photograph, in the same wind as RustleHero's field.
 *  The photo is a generated image of a lilac bush panned sideways (docs/design/imagery,
 *  27 Sep 2026): a metaphor for the rustle, never data. The wind is the field's — turbulence
 *  that breathes and drifts displaces the leaves a little, so the smear keeps quivering — plus a
 *  slow sideways drift of the whole frame. Reduced motion: the same frame, not moving.
 *  A phone gets its own portrait frame (the lilac sits above the card) and no displacement:
 *  a full-screen filter re-rendered 20 times a second is the one thing that costs battery. */
const PAUSE_KEY = 'frondia.motion-paused'

export function PhotoRustle({ photo, phone = null, children, still = false, className = '', pauseLabel }: PhotoRustleProps) {
  // the phone frame and the wind filter both read the viewport/pointer, so the server (and the
  // client's first paint) render the wide frame with no filter; an effect corrects either once
  // mounted — the same timing the previous, SSR-less version already picked them at (on mount)
  const [pic, setPic] = useState<Photo>(photo)
  useEffect(() => {
    if (phone && window.matchMedia('(max-width: 720px)').matches) setPic(phone)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const { w, h } = pic
  const k = w / 1000
  const turb = useRef<SVGFETurbulenceElement>(null), gust = useRef<SVGFEOffsetElement>(null), root = useRef<HTMLDivElement>(null)
  const fid = `photo-rustle-${useId().replace(/:/g, '')}`
  const [wind, setWind] = useState(false)
  // `still` is the caller's override; without it the photo reads ?clean and reduced motion itself
  const [detected, setDetected] = useState(false)
  useEffect(() => {
    const quiet = stillFromPage()
    setDetected(quiet)
    if (still || quiet) { setWind(false); return }
    if (!window.matchMedia('(max-width: 720px), (pointer: coarse)').matches) setWind(true)
  }, [still])
  const quiet = still || detected
  // the hero moves for as long as it is on screen, so it has a pause button (WCAG 2.2.2; re-check 2, 3 Oct; design wave,
  // 5 Oct): pressed, the drift stops where it is (paused, not reset) and the wind's last frame stays
  const [paused, setPaused] = useState(false)
  // and it stays paused for the visit: a switch of language or a way back to the landing reloads the hero, which moved again
  // (round-1 re-check, 6 Oct 2026). Session storage, not a cookie: nothing leaves the browser, and a new visit starts moving
  useEffect(() => { try { if (sessionStorage.getItem(PAUSE_KEY) === '1') setPaused(true) } catch {} }, [])
  const togglePause = () => setPaused((p) => {
    try { if (p) sessionStorage.removeItem(PAUSE_KEY); else sessionStorage.setItem(PAUSE_KEY, '1') } catch {}
    return !p
  })
  useEffect(() => {
    if (!wind || paused) return
    let raf = 0, last = 0, onScreen = true
    const t0 = performance.now()
    const run = () => { if (!raf && onScreen && !document.hidden) raf = requestAnimationFrame(tick) }
    const stop = () => { cancelAnimationFrame(raf); raf = 0 }
    const io = new IntersectionObserver((es) => { onScreen = !!es[es.length - 1]?.isIntersecting; if (onScreen) run(); else stop() })
    if (root.current) io.observe(root.current)
    const onVis = () => (document.hidden ? stop() : run())
    document.addEventListener('visibilitychange', onVis)
    function tick(now: number) {
      raf = 0
      if (now - last > 50) {
        const t = (now - t0) / 1000
        const bx = (0.0022 + 0.0005 * Math.sin(t * 0.55)) / k, by = (0.012 - 0.002 * Math.sin(t * 0.37 + 1)) / k
        turb.current?.setAttribute('baseFrequency', `${bx.toFixed(5)} ${by.toFixed(5)}`)
        gust.current?.setAttribute('dx', (Math.sin(t * 0.21) * 60 * k).toFixed(1))
        last = now
      }
      run()
    }
    run()
    return () => { stop(); io.disconnect(); document.removeEventListener('visibilitychange', onVis) }
  }, [wind, k, paused])
  return (
    <div ref={root} className={`rustle-hero photo-rustle grain ${quiet ? '' : 'photo-rustle--drift'}${paused ? ' is-paused' : ''} ${className}`}>
      <svg className="rustle-field" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="xMidYMid slice" aria-hidden="true">
        {wind && (
          <defs>
            <filter id={fid} x={-w * 0.05} y={-h * 0.05} width={w * 1.1} height={h * 1.1}
                    filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
              <feTurbulence ref={turb} type="fractalNoise" baseFrequency={`${0.0022 / k} ${0.012 / k}`} numOctaves="2" seed="7" result="wind" />
              <feOffset ref={gust} in="wind" dx="0" dy="0" result="gust" />
              <feDisplacementMap in="SourceGraphic" in2="gust" scale={16 * k} xChannelSelector="R" yChannelSelector="G" result="quiver" />
              <feGaussianBlur in="quiver" stdDeviation={`${4 * k} 0`} />
            </filter>
          </defs>
        )}
        <image href={'/' + pic.src} x="0" y="0" width={w} height={h} preserveAspectRatio="none"
               filter={wind ? `url(#${fid})` : undefined} />
      </svg>
      {children}
      {pauseLabel && !quiet && (
        <button type="button" className="rustle-pause" aria-pressed={paused} aria-label={pauseLabel} onClick={togglePause}>
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
            {paused ? <path d="M5 3.5v9l7.5-4.5z" fill="currentColor" /> : <path d="M4.5 3.5h2.5v9H4.5zM9 3.5h2.5v9H9z" fill="currentColor" />}
          </svg>
        </button>
      )}
    </div>
  )
}
