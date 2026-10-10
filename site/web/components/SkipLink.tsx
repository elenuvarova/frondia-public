'use client'
import type { MouseEvent } from 'react'

// The first Tab stop on every page (WCAG 2.4.1; re-check 2). A plain href="#main" pushed a history entry: in the atlas,
// whose address follows the view by replaceState, a city switch then replaced that entry and Back put the old city in
// the address under the new city's map (re-check 5). So once hydrated it moves focus to <main> itself, address and
// history untouched; before hydration the href still works as a link.
export function SkipLink({ label }: { label: string }) {
  const onClick = (e: MouseEvent<HTMLAnchorElement>) => {
    const main = document.getElementById('main')
    if (!main) return
    e.preventDefault()
    if (!main.hasAttribute('tabindex')) main.tabIndex = -1
    main.focus()
  }
  return <a className="skip-link" href="#main" onClick={onClick}>{label}</a>
}
