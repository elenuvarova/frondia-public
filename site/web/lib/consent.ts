// Cookie choice: strictly-necessary storage (no consent needed to remember it), read and written by
// the banner and by Clarity. No cookie is set here — only localStorage, wrapped in try/catch for
// private-browsing modes where it throws. Every change fires a window event so components that don't
// share React state (the banner, Clarity, a future /privacy control) stay in sync.
export type Choice = 'granted' | 'denied'

export const CONSENT_KEY = 'frondia.consent'
// Bump the version when what the banner asks about changes: every saved choice is then asked again.
// A choice older than a year is asked again too (the usual shelf life of a consent).
export const CONSENT_VERSION = 1
export const CONSENT_MAX_AGE_DAYS = 365
const DAY_MS = 24 * 60 * 60 * 1000
export const CONSENT_EVENT = 'frondia:consent'
const OPEN_EVENT = 'frondia:open-consent'

function isChoice(v: unknown): v is Choice {
  return v === 'granted' || v === 'denied'
}

// `window.localStorage` is a getter that itself can throw (Safari private mode in some versions,
// storage disabled by policy, sandboxed iframes) — before any method on it is even called. Every
// call site reads through here instead of touching `window.localStorage` directly, so that throw
// never escapes to a component.
export function safeStorage(): Storage | null {
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage
  } catch {
    return null
  }
}

// A saved choice counts only if it is this version's and under a year old; anything else (another
// version, no or an unreadable date, a date in the future) reads as no choice, so the banner asks again.
export function readChoice(storage: Pick<Storage, 'getItem'> | null, now: Date = new Date()): Choice | null {
  if (!storage) return null
  try {
    const raw = storage.getItem(CONSENT_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as { choice?: unknown; at?: unknown; v?: unknown }
    if (!isChoice(parsed.choice) || parsed.v !== CONSENT_VERSION || typeof parsed.at !== 'string') return null
    const at = Date.parse(parsed.at)
    const age = now.getTime() - at
    if (Number.isNaN(at) || age < 0 || age > CONSENT_MAX_AGE_DAYS * DAY_MS) return null
    return parsed.choice
  } catch {
    return null
  }
}

function dispatch(detail: Choice | null): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent<Choice | null>(CONSENT_EVENT, { detail }))
}

export function saveChoice(storage: Pick<Storage, 'setItem'>, choice: Choice, now: Date = new Date()): void {
  try {
    storage.setItem(CONSENT_KEY, JSON.stringify({ choice, at: now.toISOString(), v: CONSENT_VERSION }))
  } catch {
    // private mode or quota: the choice just isn't remembered next visit
  }
  dispatch(choice)
}

export function clearChoice(storage: Pick<Storage, 'removeItem'>): void {
  try {
    storage.removeItem(CONSENT_KEY)
  } catch {
    // as above
  }
  dispatch(null)
}

// Reopens the banner from anywhere (the /privacy page's "change your choice" control).
export function openConsent(): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new Event(OPEN_EVENT))
}

export function onOpenConsent(handler: () => void): () => void {
  if (typeof window === 'undefined') return () => {}
  window.addEventListener(OPEN_EVENT, handler)
  return () => window.removeEventListener(OPEN_EVENT, handler)
}

// Cross-tab sync: the native `storage` event fires in every OTHER tab/document on the same origin
// when localStorage changes (never in the tab that made the change — that one already got the
// `frondia:consent` dispatch above). Filtered to our key, or `key === null` (Storage.clear()).
// Components add this alongside their `frondia:consent` listener, same handling either way.
export function onStorageChoice(handler: (choice: Choice | null) => void): () => void {
  if (typeof window === 'undefined') return () => {}
  function onStorage(e: StorageEvent) {
    if (e.key !== null && e.key !== CONSENT_KEY) return
    handler(readChoice(safeStorage()))
  }
  window.addEventListener('storage', onStorage)
  return () => window.removeEventListener('storage', onStorage)
}
