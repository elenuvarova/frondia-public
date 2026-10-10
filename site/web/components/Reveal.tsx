'use client'
import { useEffect } from 'react'

// Adds `.in` to every `.reveal` once it scrolls into view. One observer per page; put at the end.
export function Reveal() {
  useEffect(() => {
    const els = document.querySelectorAll('.reveal:not(.in)')
    // a Figma capture (dev) or a browser without observers sees everything at once
    const capture = location.hash.includes('figmacapture')
    if (capture || !('IntersectionObserver' in window)) {
      els.forEach((e) => e.classList.add('in'))
      return
    }
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target) }
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 })
    els.forEach((e) => io.observe(e))
    return () => io.disconnect()
  }, [])
  return null
}
