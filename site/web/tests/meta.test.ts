import { expect, test } from 'vitest'
import sitemap from '@/app/sitemap'
import { PUBLISHED } from '@/i18n/locales'

test('the sitemap lists every published page with its language versions', async () => {
  process.env.SITE_URL = 'https://frondia.eu'
  const s = await sitemap()
  const home = s.find((e) => e.url === 'https://frondia.eu/')!
  expect(home.alternates?.languages).toEqual(PUBLISHED.length > 1
    ? { 'en-GB': 'https://frondia.eu/', 'nl-BE': 'https://frondia.eu/nl', 'fr-BE': 'https://frondia.eu/fr', 'x-default': 'https://frondia.eu/' }
    : { 'en-GB': 'https://frondia.eu/', 'x-default': 'https://frondia.eu/' })
  // each language's entry carries the same four alternates as the English one
  for (const u of ['https://frondia.eu/nl', 'https://frondia.eu/fr']) {
    const e = s.find((x) => x.url === u)
    if (PUBLISHED.length > 1) expect(e?.alternates?.languages, u).toEqual(home.alternates?.languages)
    else expect(e, u).toBeUndefined()
  }
})

test('the sitemap includes the privacy page', async () => {
  process.env.SITE_URL = 'https://frondia.eu'
  const s = await sitemap()
  expect(s.some((e) => e.url === 'https://frondia.eu/privacy')).toBe(true)
})
