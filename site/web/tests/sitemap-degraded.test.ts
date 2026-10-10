import { expect, test, vi } from 'vitest'

// without communes.json the sitemap still answers (as /commune does), listing the commune index alone
vi.mock('@/lib/data', async (importOriginal) => {
  const real = await importOriginal<typeof import('@/lib/data')>()
  return { ...real, getCommunes: () => Promise.reject(new real.DataError('communes.json', new Error('ENOENT'))) }
})

test('a missing communes.json leaves /commune alone in the sitemap, not a 500', async () => {
  process.env.SITE_URL = 'https://frondia.eu'
  const { default: sitemap } = await import('@/app/sitemap')
  const { PUBLISHED, localePath } = await import('@/i18n/locales')
  const urls = (await sitemap()).map((e) => e.url)
  expect(urls.filter((u) => u.includes('/commune'))).toEqual(PUBLISHED.map((l) => `https://frondia.eu${localePath(l, '/commune')}`))
  // the rest is unchanged: 3 fixed pages, 5 atlas cities, 3 dossiers, 5 data cities, in each published language
  expect(urls).toHaveLength((1 + 3 + 5 + 3 + 5) * PUBLISHED.length)
})
