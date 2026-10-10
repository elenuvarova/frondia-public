import { afterEach, expect, test, vi } from 'vitest'
import { stillFromPage } from '@/lib/still'

const page = (search: string, reduce: boolean) =>
  vi.stubGlobal('window', { location: { search }, matchMedia: (q: string) => ({ matches: reduce && q.includes('reduce') }) })

afterEach(() => { vi.unstubAllGlobals() })

test('no window (the server): moving', () => {
  expect(stillFromPage()).toBe(false)
})
test('?clean holds the page still, with or without a value', () => {
  page('?clean', false); expect(stillFromPage()).toBe(true)
  page('?city=ghent&clean=', false); expect(stillFromPage()).toBe(true)
})
test('reduced motion holds the page still', () => {
  page('', true); expect(stillFromPage()).toBe(true)
})
test('an ordinary visit moves', () => {
  page('?utm=x', false); expect(stillFromPage()).toBe(false)
})
