import { afterEach, expect, test, vi } from 'vitest'
import { load } from '@/components/atlas/useJSON'
import { EARLY, earlyFetchScript } from '@/lib/atlas/early'

// the atlas's file reads (components/atlas/useJSON.ts load): one fetch per address for the life of the tab; a failed
// read — a bad status or a body that is not JSON — leaves the cache, so the next try fetches again

const ok = (body: string) => new Response(body, { status: 200, headers: { 'content-type': 'application/json' } })
afterEach(() => { vi.unstubAllGlobals() })

test('two reads of one address share one fetch', async () => {
  const f = vi.fn(async () => ok('{"a":1}'))
  vi.stubGlobal('fetch', f)
  const [a, b] = await Promise.all([load('/t/shared.json'), load('/t/shared.json')])
  expect(a).toEqual({ a: 1 })
  expect(b).toBe(a)
  expect(await load('/t/shared.json')).toBe(a)
  expect(f).toHaveBeenCalledTimes(1)
})

test('a 500 rejects and is forgotten: the next read fetches again', async () => {
  const f = vi.fn()
    .mockResolvedValueOnce(new Response('no', { status: 500 }))
    .mockResolvedValueOnce(ok('[1]'))
  vi.stubGlobal('fetch', f)
  await expect(load('/t/flaky.json')).rejects.toThrow('/t/flaky.json: 500')
  await Promise.resolve()   // the eviction runs on the rejected promise's own catch
  expect(await load('/t/flaky.json')).toEqual([1])
  expect(f).toHaveBeenCalledTimes(2)
})

test('a body that is not JSON rejects and is forgotten too', async () => {
  const f = vi.fn()
    .mockResolvedValueOnce(ok('<html>'))
    .mockResolvedValueOnce(ok('{"b":2}'))
  vi.stubGlobal('fetch', f)
  await expect(load('/t/broken.json')).rejects.toThrow()
  await Promise.resolve()
  expect(await load('/t/broken.json')).toEqual({ b: 2 })
  expect(f).toHaveBeenCalledTimes(2)
})

// the city's file is started by a script in the HTML (lib/atlas/early.ts), not by <link rel="preload" as="fetch">,
// which WebKit never hands to fetch(): Safari read every city twice (re-check 1, 3 Oct)
test('the first read adopts the download the page started, and only once', async () => {
  const f = vi.fn(async () => ok('{"late":1}'))
  vi.stubGlobal('fetch', f)
  vi.stubGlobal(EARLY, { '/t/early.json': Promise.resolve({ early: 1 }) })
  expect(await load('/t/early.json')).toEqual({ early: 1 })
  expect(await load('/t/early.json')).toEqual({ early: 1 })
  expect(f).not.toHaveBeenCalled()
  expect((globalThis as unknown as Record<string, Record<string, unknown>>)[EARLY]!['/t/early.json']).toBeUndefined()
})

test('a failed early download is forgotten: the next read fetches again', async () => {
  const f = vi.fn(async () => ok('{"again":1}'))
  vi.stubGlobal('fetch', f)
  const failed = Promise.reject(new Error('/t/early-bad.json: 503'))
  failed.catch(() => {})
  vi.stubGlobal(EARLY, { '/t/early-bad.json': failed })
  await expect(load('/t/early-bad.json')).rejects.toThrow('503')
  await Promise.resolve()
  expect(await load('/t/early-bad.json')).toEqual({ again: 1 })
  expect(f).toHaveBeenCalledTimes(1)
})

test('the page’s script starts the read that load expects: same address, same checks, nothing to break out of the tag', async () => {
  const src = earlyFetchScript('/data/brussels.json')
  expect(src).not.toMatch(/</)
  expect(earlyFetchScript('/data/</script>.json')).not.toMatch(/<\/script/i)
  const win: Record<string, unknown> = {}
  const f = vi.fn(async () => ok('{"city":"brussels"}'))
  new Function('window', 'fetch', src)(win, f)
  expect(f).toHaveBeenCalledWith('/data/brussels.json')
  expect(await (win[EARLY] as Record<string, Promise<unknown>>)['/data/brussels.json']).toEqual({ city: 'brussels' })
  const bad = vi.fn(async () => new Response('no', { status: 404 }))
  new Function('window', 'fetch', earlyFetchScript('/data/x.json'))(win, bad)
  await expect((win[EARLY] as Record<string, Promise<unknown>>)['/data/x.json']).rejects.toThrow('/data/x.json: 404')
})
