// The preview languages (plan 5, L2): fixed when the site is built, routed only with the variable, never indexed.
import { afterEach, expect, test, vi } from 'vitest'

vi.mock('next-intl/server', () => ({ getTranslations: async () => (key: string) => key }))
vi.mock('next/headers', () => ({ headers: async () => new Headers() }))

afterEach(() => { vi.unstubAllEnvs(); vi.resetModules() })

const unset = () => { vi.stubEnv('NEXT_PUBLIC_PREVIEW_LOCALES', undefined as unknown as string); delete process.env.NEXT_PUBLIC_PREVIEW_LOCALES }

test('the build bakes the variable in, empty when unset: a run-time value never adds a language', async () => {
  unset()
  vi.resetModules()
  const off = (await import('@/next.config')).default
  expect(off.env?.NEXT_PUBLIC_PREVIEW_LOCALES).toBe('')
  vi.stubEnv('NEXT_PUBLIC_PREVIEW_LOCALES', 'nl,fr')
  vi.resetModules()
  const on = (await import('@/next.config')).default
  expect(on.env?.NEXT_PUBLIC_PREVIEW_LOCALES).toBe('nl,fr')
})

test('without the variable only the published languages are routed, and the router reads the registry', async () => {
  unset()
  vi.resetModules()
  const { ROUTED, PUBLISHED } = await import('@/i18n/locales')
  const { routing } = await import('@/i18n/routing')
  expect(ROUTED).toEqual(PUBLISHED)
  expect(routing.locales).toEqual(PUBLISHED)
  expect(ROUTED).not.toContain('xx')
})

test('a preview build routes the registry’s codes from the variable, and nothing else', async () => {
  vi.stubEnv('NEXT_PUBLIC_PREVIEW_LOCALES', 'nl,fr,de,xx')
  vi.resetModules()
  const { ROUTED, isRouted, isPublished } = await import('@/i18n/locales')
  const { routing } = await import('@/i18n/routing')
  expect(ROUTED).toEqual(['en', 'nl', 'fr', 'xx'])
  expect(routing.locales).toEqual(ROUTED)
  expect(isRouted('nl')).toBe(true)
  expect(isRouted('xx')).toBe(true)
  expect(isRouted('de')).toBe(false)
  expect(isPublished('xx')).toBe(false)
})

test('a language not yet published is never indexed; a published one sets no robots of its own', async () => {
  const { rootMetadata } = await import('@/components/RootDocument')
  const { isPublished } = await import('@/i18n/locales')
  const xx = await rootMetadata('xx')
  expect(xx.robots).toEqual({ index: false, follow: false })
  for (const loc of ['nl', 'fr'] as const) {
    expect((await rootMetadata(loc)).robots, loc).toEqual(isPublished(loc) ? undefined : { index: false, follow: false })
  }
  expect((await rootMetadata('en')).robots).toBeUndefined()
})
