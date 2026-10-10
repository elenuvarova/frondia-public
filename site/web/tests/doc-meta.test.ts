import { afterEach, beforeEach, expect, test } from 'vitest'
import { dossierAddress } from '@/lib/dossier'
import { docMetadata } from '@/lib/seo'
import { firstParam, siteUrl } from '@/lib/site'
import { PUBLISHED } from '@/i18n/locales'

const LIVE = PUBLISHED.length > 1

// the document pages' head (lib/seo.ts docMetadata) and the dossier's printed address: every URL on
// SITE_URL, the page's own query kept on the canonical and on each language, noindex only when asked

const saved = process.env.SITE_URL
beforeEach(() => { process.env.SITE_URL = 'https://frondia.example' })
afterEach(() => { if (saved === undefined) delete process.env.SITE_URL; else process.env.SITE_URL = saved })

const head = (over: Partial<Parameters<typeof docMetadata>[0]> = {}) => docMetadata({
  locale: 'en', path: '/dossier', query: '?city=antwerp&sector=11002R13-', title: 'T', description: 'D', indexable: true, ogAlt: 'Frondia', ...over,
})

test('siteUrl reads SITE_URL, with frondia.eu when unset; firstParam reads a query as URLSearchParams.get', () => {
  expect(siteUrl()).toBe('https://frondia.example')
  delete process.env.SITE_URL
  expect(siteUrl()).toBe('https://frondia.eu')
  expect(firstParam('a')).toBe('a')
  expect(firstParam(['b', 'c'])).toBe('b')
  expect(firstParam(undefined)).toBe('')
  expect(firstParam('')).toBe('')
})

test('the canonical and every language keep the page’s query; og:url is the canonical', () => {
  const m = head()
  const url = 'https://frondia.example/dossier?city=antwerp&sector=11002R13-'
  expect(String(m.metadataBase)).toBe('https://frondia.example/')
  expect(m.alternates?.canonical).toBe(url)
  expect(m.alternates?.languages).toEqual(LIVE ? {
    'en-GB': url,
    'nl-BE': 'https://frondia.example/nl/dossier?city=antwerp&sector=11002R13-',
    'fr-BE': 'https://frondia.example/fr/dossier?city=antwerp&sector=11002R13-',
    'x-default': url,
  } : { 'en-GB': url, 'x-default': url })
  const og = m.openGraph as Record<string, unknown>
  expect(og.url).toBe(url)
  expect(og.title).toBe('T')
  expect(og.description).toBe('D')
  expect(og.locale).toBe('en_GB')
  expect(og.images).toEqual([{ url: 'https://frondia.example/og/en.jpg', width: 1200, height: 630, type: 'image/jpeg', alt: 'Frondia' }])
  expect(m.title).toBe('T')
  expect(m.description).toBe('D')
})

test('a Dutch or French page is its own canonical, with its own og locale and card; x-default stays English', () => {
  for (const [loc, og] of [['nl', 'nl_BE'], ['fr', 'fr_BE']] as const) {
    const m = head({ locale: loc, path: '/commune', query: '?code=21002' })
    const own = `https://frondia.example/${loc}/commune?code=21002`
    expect(m.alternates?.canonical).toBe(own)
    const langs = m.alternates?.languages as Record<string, string>
    expect(langs['x-default']).toBe('https://frondia.example/commune?code=21002')
    if (LIVE) expect(langs[loc === 'nl' ? 'nl-BE' : 'fr-BE']).toBe(own)
    const o = m.openGraph as Record<string, unknown>
    expect(o.url).toBe(own)
    expect(o.locale).toBe(og)
    expect((o.images as { url: string }[])[0]?.url).toBe(`https://frondia.example/og/${loc}.jpg`)
  }
  // English is unchanged by the other languages: the same canonical as before them
  expect(head({ path: '/commune', query: '?code=21002' }).alternates?.canonical).toBe('https://frondia.example/commune?code=21002')
})

test('robots only when the page is not to be found', () => {
  expect(head()).not.toHaveProperty('robots')
  expect(head({ indexable: false }).robots).toEqual({ index: false })
})

test('a page without a query is its bare address', () => {
  const m = head({ path: '/register', query: '' })
  expect(m.alternates?.canonical).toBe('https://frondia.example/register')
  expect((m.openGraph as Record<string, unknown>).url).toBe('https://frondia.example/register')
})

test('the dossier’s printed address is the site’s host, never the request’s, with the city and sector', () => {
  expect(dossierAddress('https://frondia.ontwrpn.com', 'en', 'brussels', '21004E72-')).toBe('frondia.ontwrpn.com/dossier?city=brussels&sector=21004E72-')
  expect(dossierAddress('https://frondia.eu', 'fr', 'ghent', '44021G00-')).toBe('frondia.eu/fr/dossier?city=ghent&sector=44021G00-')
  expect(dossierAddress('http://localhost:3100', 'en', 'antwerp', 'X')).toBe('localhost:3100/dossier?city=antwerp&sector=X')
})
