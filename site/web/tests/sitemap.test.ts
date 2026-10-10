import { expect, test } from 'vitest'
import sitemap from '@/app/sitemap'
import { getCommunes } from '@/lib/data'
import { CODES, PUBLISHED, localePath, tagOf } from '@/i18n/locales'

// the sitemap's known answers (plan 3, task 6): the document pages it lists, and how many —
// checked against the resolvers the pages themselves use, not a second hard-coded list

const SITE = 'https://frondia.eu'

test('lists the fixed pages, the picked dossiers, every commune, the five atlas and data cities, and bare register', async () => {
  process.env.SITE_URL = SITE
  const entries = await sitemap()
  const all = entries.map((e) => e.url)
  // the English addresses: every entry with no language prefix (the known answers below are theirs)
  const urls = all.filter((u) => !/^https:\/\/frondia\.eu\/(nl|fr|xx|en)(\/|\?|$)/.test(u))
  const communes = await getCommunes()

  // fixed pages, unchanged by this task
  expect(urls).toContain(`${SITE}/`)
  expect(urls).toContain(`${SITE}/privacy`)

  // register: only the bare address, never a filtered view
  expect(urls).toContain(`${SITE}/register`)
  expect(urls.filter((u) => u.includes('/register')).length).toBe(1)

  // dossier: the canonical long form for brussels, antwerp and ghent (their rule picks a sector);
  // liège and charleroi (noPick, Article 8(1)) list no dossier of their own
  expect(urls).toContain(`${SITE}/dossier?city=brussels&amp;sector=21004E72-`)
  expect(urls).toContain(`${SITE}/dossier?city=antwerp&amp;sector=11002R13-`)
  expect(urls).toContain(`${SITE}/dossier?city=ghent&amp;sector=44021G00-`)
  expect(urls.some((u) => u.includes('/dossier') && u.includes('liege'))).toBe(false)
  expect(urls.some((u) => u.includes('/dossier') && u.includes('charleroi'))).toBe(false)
  expect(urls).not.toContain(`${SITE}/dossier`)
  expect(urls.filter((u) => u.includes('/dossier')).length).toBe(3)

  // commune: the index plus one address per commune (23 on 28 Sep 2026), never the bare address twice
  expect(urls).toContain(`${SITE}/commune`)
  expect(urls).toContain(`${SITE}/commune?code=21001`)
  expect(communes).toHaveLength(23)
  expect(urls.filter((u) => u.includes('/commune')).length).toBe(1 + communes.length)

  // data: the five cities, never the bare address
  for (const city of ['brussels', 'antwerp', 'ghent', 'liege', 'charleroi']) {
    expect(urls).toContain(`${SITE}/data?city=${city}`)
  }
  expect(urls).not.toContain(`${SITE}/data`)
  expect(urls.filter((u) => u.includes('/data')).length).toBe(5)

  // atlas: the five cities' canonical pages (A4/A5 of plan 4), never the bare address nor a view inside a city
  for (const city of ['brussels', 'antwerp', 'ghent', 'liege', 'charleroi']) {
    expect(urls).toContain(`${SITE}/atlas?city=${city}`)
  }
  expect(urls).not.toContain(`${SITE}/atlas`)
  expect(urls.filter((u) => u.includes('/atlas')).length).toBe(5)

  // 40 English addresses on 28 Sep 2026 (3 + 5 + 3 + 24 + 5), the same in every state of the languages
  expect(urls).toHaveLength(3 + 5 + 3 + (1 + communes.length) + 5)

  // each English address once per published language, with that language's prefix; nothing else
  expect(all).toHaveLength(urls.length * PUBLISHED.length)
  for (const loc of PUBLISHED) {
    for (const u of urls) {
      const p = u.slice(SITE.length)
      const [pathPart = '/', query = ''] = p.split('?')
      expect(all, loc).toContain(SITE + localePath(loc, pathPart) + (query ? `?${query}` : ''))
    }
  }
  for (const loc of CODES.filter((c) => !PUBLISHED.includes(c))) {
    expect(all.some((u) => u.startsWith(`${SITE}/${loc}/`) || u === `${SITE}/${loc}` || u.startsWith(`${SITE}/${loc}?`)), loc).toBe(false)
  }

  // every entry lists the published languages and x-default, x-default the English address
  const tags = [...PUBLISHED.map(tagOf), 'x-default'].sort()
  for (const e of entries) {
    const langs = e.alternates?.languages as Record<string, string>
    expect(Object.keys(langs).sort(), e.url).toEqual(tags)
    expect(urls, e.url).toContain(langs['x-default'])
    expect(langs['en-GB']).toBe(langs['x-default'])
    expect(Object.values(langs), e.url).toContain(e.url)
  }

  // every entry builds on SITE_URL, and every '&' in a <loc> is escaped for XML
  for (const u of all) {
    expect(u.startsWith(SITE)).toBe(true)
    expect(u.includes('&') && !u.includes('&amp;')).toBe(false)
  }
})

test('the language alternates escape "&" the same way the url does', async () => {
  process.env.SITE_URL = SITE
  const entries = await sitemap()
  const dossier = entries.find((e) => e.url.includes('/dossier') && e.url.includes('brussels'))
  expect(dossier?.alternates?.languages?.['en-GB']).toBe(`${SITE}/dossier?city=brussels&amp;sector=21004E72-`)
  expect(dossier?.alternates?.languages?.['x-default']).toBe(`${SITE}/dossier?city=brussels&amp;sector=21004E72-`)
  if (PUBLISHED.includes('nl')) {
    expect(dossier?.alternates?.languages?.['nl-BE']).toBe(`${SITE}/nl/dossier?city=brussels&amp;sector=21004E72-`)
    expect(dossier?.alternates?.languages?.['fr-BE']).toBe(`${SITE}/fr/dossier?city=brussels&amp;sector=21004E72-`)
    expect(entries.map((e) => e.url)).toContain(`${SITE}/fr/commune?code=21002`)
    expect(entries.map((e) => e.url)).toContain(`${SITE}/nl/data?city=liege`)
    expect(entries.map((e) => e.url)).toContain(`${SITE}/nl/atlas?city=ghent`)
  }
})

test('the address is built from SITE_URL, not left at the default when the env var is set', async () => {
  process.env.SITE_URL = 'https://example.test'
  const entries = await sitemap()
  expect(entries.every((e) => e.url.startsWith('https://example.test'))).toBe(true)
  process.env.SITE_URL = SITE
})
