'use client'
import { useEffect } from 'react'

/** What a rubber band past the end shows (Elena, 10 Oct 2026): above the top the hero's photograph, below the bottom
 *  the footer's green. The root first refuses the band (tokens.css: overscroll-behavior), so the photo and the footer
 *  simply stay at the edges; where a browser bounces anyway, it paints the gap with the root's background colour, and
 *  this flips that colour by the half of the page the reader is in: the top's tone, or the bottom's. */
export function EdgeTone() {
  useEffect(() => {
    const root = document.documentElement
    const set = () => {
      const half = (root.scrollHeight - innerHeight) / 2
      root.classList.toggle('edge-bottom', half > 0 && scrollY > half)
    }
    set()
    addEventListener('scroll', set, { passive: true })
    addEventListener('resize', set)
    return () => { removeEventListener('scroll', set); removeEventListener('resize', set) }
  }, [])
  return null
}
