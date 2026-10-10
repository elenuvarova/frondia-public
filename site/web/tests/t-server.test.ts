import { afterEach, expect, test, vi } from 'vitest'
import { count } from '@/lib/icu'

// The server's getT (lib/t.ts) runs the same check as the client's useT: outside production, a number put into a
// message's plain argument throws, so the test or the dev page that rendered it fails (plan 5, L8; Task 4's minor:
// the server path was untested). next-intl's server functions are replaced by its own translator on a small catalogue.
const messages = { x: { since: 'since {year}', sectors: '{n, plural, one {# sector} other {# sectors}}', rich: '<b>{n, plural, one {# sector} other {# sectors}}</b> since {year}' } }
vi.mock('next-intl/server', async () => {
  const { createTranslator } = await import('next-intl')
  return {
    getTranslations: async (namespace: string) => createTranslator({ locale: 'en', messages, namespace: namespace as 'x' }),
    getLocale: async () => 'en',
  }
})

afterEach(() => { vi.unstubAllEnvs() })

test('getT throws on a number in a plain argument and takes a count where the message counts it', async () => {
  vi.stubEnv('NODE_ENV', 'test')
  const { getT } = await import('@/lib/t')
  const { t, rich } = await getT('x')
  expect(() => t('since', { year: count(2017) })).toThrow(/x\.since: \{year\} is not a plural/)
  expect(() => rich('rich', { n: count(2), year: count(2017) })).toThrow(/x\.rich: \{year\}/)
  expect(t('since', { year: '2017' })).toBe('since 2017')
  expect(t('sectors', { n: count(3) }).replace(/ /g, ' ')).toBe('3 sectors')
})

test('in production getT does not check (the message formats, as next-intl would)', async () => {
  vi.stubEnv('NODE_ENV', 'production')
  const { getT } = await import('@/lib/t')
  const { t } = await getT('x')
  expect(() => t('since', { year: count(2017) })).not.toThrow()
})
