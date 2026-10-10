'use client'
import { createContext, useContext, useEffect, useRef, useState, type HTMLAttributes, type ReactNode } from 'react'
import { stillFromPage } from '@/lib/still'

type GsapCore = typeof import('gsap')['gsap']

/* Number Odometer — adapted from Osmo Supply (osmo.supply/resource/number-odometer).
   Kept: the data-odometer-* attributes, the roller of 0–9 twice over, GSAP's power3.out, digits
   staggered 0.04 s from the right, elements 0.1 s apart, a ScrollTrigger at "top 80%", once, and
   the clean-up that puts the plain text back when the roll ends (Instrument Serif's digits are
   proportional: left as rollers, "263" would sit loose).
   Changed on the way in: the rollers are rendered in JSX, not built with innerHTML (React owns
   this DOM); screen readers read the value from visually hidden text, the rollers are aria-hidden;
   prefers-reduced-motion shows the final text at once (the original skipped the group and left
   it at 0). GSAP loads only when the group is on the page; if it fails, the text shows. */
const STEP = 1.1          // line-height ratio of the rolling text, in em
const CYCLES = 2
const Done = createContext(true)

interface OdometerGroupProps extends Omit<HTMLAttributes<HTMLDivElement>, 'className'> {
  children?: ReactNode
  className?: string
  still?: boolean
}

// `still` forces the final numbers at once; without it the group reads ?clean (a capture) and
// prefers-reduced-motion itself, on mount
export function OdometerGroup({ children, className = '', still = false, ...rest }: OdometerGroupProps) {
  const ref = useRef<HTMLDivElement>(null)
  const [done, setDone] = useState(still)
  useEffect(() => {
    const group = ref.current
    if (still || stillFromPage()) { setDone(true); return }
    if (!group) return
    let ctx: ReturnType<GsapCore['context']> | undefined, killed = false
    Promise.all([import('gsap'), import('gsap/ScrollTrigger')]).then(([{ gsap }, { ScrollTrigger }]) => {
      if (killed) return
      gsap.registerPlugin(ScrollTrigger)
      const els = [...group.querySelectorAll('[data-odometer-element]')]
      ctx = gsap.context(() => {
        const tl = gsap.timeline({ scrollTrigger: { trigger: group, start: 'top 80%', once: true }, onComplete: () => setDone(true) })
        els.forEach((el, i) => {
          const rollers = [...el.querySelectorAll<HTMLElement>('[data-odometer-part="roller"]')]
          rollers.forEach((r, d) => {
            const fromRight = rollers.length - 1 - d
            tl.to(r, { y: `${-Number(r.dataset.target) * STEP}em`, duration: 1.4, ease: 'power3.out', force3D: true }, i * 0.1 + fromRight * 0.04)
          })
        })
      }, group)
    }).catch(() => setDone(true))
    return () => { killed = true; ctx?.revert() }
  }, [still])
  return <Done.Provider value={done}><div ref={ref} data-odometer-group="" className={className} {...rest}>{children}</div></Done.Provider>
}

interface OdometerProps {
  value: string | number
  className?: string
}

export function Odometer({ value, className = '' }: OdometerProps) {
  const done = useContext(Done)
  const text = String(value)
  if (done) return <span data-odometer-element="" className={`odometer odometer--done ${className}`}>{text}</span>
  const cells = Array.from({ length: 10 * CYCLES }, (_, d) => d % 10).join('\n')
  return (
    <span data-odometer-element="" className={`odometer ${className}`}>
      <span className="sr-only">{text}</span>
      {[...text].map((ch, i) => /\d/.test(ch) ? (
        <span key={i} data-odometer-part="mask" aria-hidden="true">
          {/* start at 0; a 0 target rolls one full turn so every digit moves */}
          <span data-odometer-part="roller" data-target={Number(ch) > 0 ? Number(ch) : 10}>{cells}</span>
        </span>
      ) : <span key={i} data-odometer-part="static" aria-hidden="true">{ch}</span>)}
    </span>
  )
}
