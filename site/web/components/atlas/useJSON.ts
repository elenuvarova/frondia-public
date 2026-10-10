'use client'
import { useEffect, useState } from 'react'
import { EARLY } from '@/lib/atlas/early'

// The atlas's files, read by the browser (A2 of plan 4), as packages/shared/lib/data.js did: one promise per address
// for the life of the tab (a city opened twice is read once; the HTTP cache and its ETag do the rest), a failed read
// leaves the cache so the next try fetches again; the answer for an address the view has moved on from is ignored
// (`live`), and the data on screen stays until the new data arrives — tagged with the address it came from, so a caller
// can tell the last address's answer from this one's.
const cache = new Map<string, Promise<unknown>>()

// the city's file, started with the HTML (lib/atlas/early.ts): the first read adopts that download
function adoptEarly(url: string): Promise<unknown> | undefined {
  const m = (globalThis as Record<string, unknown>)[EARLY] as Record<string, Promise<unknown>> | undefined
  const p = m?.[url]
  if (p) delete m[url]   // adopted once: a retry after a failure fetches again
  return p
}

export function load<T>(url: string): Promise<T> {
  let p = cache.get(url)
  if (!p) {
    p = adoptEarly(url) ?? fetch(url).then((r) => {
      if (!r.ok) throw new Error(`${url}: ${r.status}`)
      return r.json()
    })
    cache.set(url, p)
    p.catch(() => cache.delete(url))
  }
  return p as Promise<T>
}

export interface JSONState<T> { data: T | null; error: Error | null; url: string | null }

export function useJSON<T>(url: string | null): JSONState<T> {
  const [state, setState] = useState<JSONState<T>>({ data: null, error: null, url: null })
  useEffect(() => {
    let live = true
    if (!url) return
    load<T>(url).then(
      (data) => { if (live) setState({ data, error: null, url }) },
      (error: unknown) => { if (live) setState({ data: null, error: error instanceof Error ? error : new Error(String(error)), url }) },
    )
    return () => { live = false }
  }, [url])
  return state
}
