// Streamline Ultimate Light (1px stroke), premium, licensed under the author's Icons plan — https://streamlinehq.com
// (credit: icons/ultimate-light/CREDITS.md; open-source use needs it, redistribution is not allowed).
// Inlined so the stroke takes the text colour; decorative, hidden from assistive tech.
import 'server-only'
import { readFileSync } from 'node:fs'
import path from 'node:path'

// read from the app's own copy (icons/ultimate-light), not packages/shared: that app is retired
// once the Vite sites go, and this path must not depend on it still being there
const DIR = path.join(process.cwd(), 'icons', 'ultimate-light')
const CACHE = new Map<string, string | null>()

function load(name: string): string | null {
  if (CACHE.has(name)) return CACHE.get(name)!
  // icon names are a closed set of file basenames; reject anything that could leave the icons dir
  if (!/^[\w-]+$/.test(name)) return null
  let svg: string | null
  try {
    svg = readFileSync(path.join(DIR, `${name}.svg`), 'utf8')
      .replace(/<desc>[\s\S]*?<\/desc>/, '')
      .replace(/#161814/g, 'currentColor')
      .replace(/\sid="[^"]*"/, '')
  } catch {
    svg = null
  }
  CACHE.set(name, svg)
  return svg
}

export function Icon({ name, size = 20, className = '' }: { name: string; size?: number; className?: string }) {
  const svg = load(name)
  if (!svg) return null
  return (
    <span
      className={`icon ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  )
}
