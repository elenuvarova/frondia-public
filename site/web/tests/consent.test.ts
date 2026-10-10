import { expect, test } from 'vitest'
import { CONSENT_KEY, CONSENT_MAX_AGE_DAYS, CONSENT_VERSION, clearChoice, readChoice, safeStorage, saveChoice } from '@/lib/consent'

const mem = () => { const m = new Map<string, string>(); return { getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v), removeItem: (k: string) => void m.delete(k) } }

test('no storage or nothing saved means no choice yet', () => {
  expect(readChoice(null)).toBeNull()
  expect(readChoice(mem())).toBeNull()
})

test('a saved choice reads back; a broken value reads as no choice', () => {
  const s = mem()
  saveChoice(s, 'granted', new Date('2026-09-28T10:00:00Z'))
  expect(readChoice(s, new Date('2026-09-29T10:00:00Z'))).toBe('granted')
  s.setItem('frondia.consent', '{nope')
  expect(readChoice(s)).toBeNull()
  saveChoice(s, 'denied'); clearChoice(s)
  expect(readChoice(s)).toBeNull()
})

// vitest's environment is 'node' — no `window` — so this doubles as the "sandboxed context where the
// localStorage property itself throws" case: safeStorage() must swallow that and hand back null, and
// readChoice(null) must still be the safe, no-choice answer.
test('no window (or a blocked storage property) is still no choice, safely', () => {
  expect(safeStorage()).toBeNull()
  expect(readChoice(safeStorage())).toBeNull()
})

test('a storage whose getItem itself throws reads as no choice, not a crash', () => {
  const hostile: Pick<Storage, 'getItem'> = { getItem() { throw new Error('blocked') } }
  expect(readChoice(hostile)).toBeNull()
})

test('a choice saved under another version of the question reads as no choice', () => {
  const s = mem()
  const at = new Date('2026-09-28T10:00:00Z')
  const now = new Date('2026-10-01T10:00:00Z')
  saveChoice(s, 'granted', at)
  expect(JSON.parse(s.getItem(CONSENT_KEY)!).v).toBe(CONSENT_VERSION)
  expect(readChoice(s, now)).toBe('granted')
  s.setItem(CONSENT_KEY, JSON.stringify({ choice: 'granted', at: at.toISOString(), v: CONSENT_VERSION + 1 }))
  expect(readChoice(s, now)).toBeNull()
  s.setItem(CONSENT_KEY, JSON.stringify({ choice: 'granted', at: at.toISOString() }))
  expect(readChoice(s, now)).toBeNull()
})

test('a choice older than the max age, or with no readable date, reads as no choice', () => {
  const s = mem()
  const at = new Date('2026-09-28T10:00:00Z')
  const day = 24 * 60 * 60 * 1000
  saveChoice(s, 'denied', at)
  expect(readChoice(s, new Date(at.getTime() + CONSENT_MAX_AGE_DAYS * day))).toBe('denied')
  expect(readChoice(s, new Date(at.getTime() + CONSENT_MAX_AGE_DAYS * day + 1))).toBeNull()
  // a date in the future (a wrong clock) is not trusted either
  expect(readChoice(s, new Date(at.getTime() - day))).toBeNull()
  for (const bad of [undefined, 'yesterday', 12345]) {
    s.setItem(CONSENT_KEY, JSON.stringify({ choice: 'denied', at: bad, v: CONSENT_VERSION }))
    expect(readChoice(s, at)).toBeNull()
  }
})
