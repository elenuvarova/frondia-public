'use client'
import { useEffect } from 'react'

/* A question opened from elsewhere: #q-… in the address (a shared /#q-outline, on load and on
   hashchange) or a link on the page to one (the funders' "How the outline is fixed" — a click on a
   link to the hash already in the address fires no hashchange, so clicks are caught too).
   The server renders every <details> closed; this opens the one asked for. */
function openQuestion(hash: string) {
  const m = hash.match(/^#q-(.+)$/)
  if (!m) return
  const el = document.getElementById(`q-${decodeURIComponent(m[1]!)}`)
  if (el instanceof HTMLDetailsElement) el.open = true
}

export function FaqAnchors() {
  useEffect(() => {
    const fromHash = () => openQuestion(location.hash)
    const onClick = (e: MouseEvent) => {
      const a = (e.target as Element | null)?.closest?.('a[href^="#q-"]')
      if (a) openQuestion(a.getAttribute('href')!)
    }
    fromHash()
    window.addEventListener('hashchange', fromHash)
    document.addEventListener('click', onClick)
    return () => {
      window.removeEventListener('hashchange', fromHash)
      document.removeEventListener('click', onClick)
    }
  }, [])
  return null
}
