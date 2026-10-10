import { createTranslator } from 'next-intl'
import { afterEach, expect, test } from 'vitest'
import { resolveAtlas } from '@/lib/atlas/resolve'
import type { Locale } from '@/lib/format'
import type { TValues } from '@/lib/icu'
import { sectorName, sectorPlace } from '@/lib/names'
import { atlasHeadWords, atlasMetadata } from '@/lib/seo'
import en from '@/messages/en.json'
import { PUBLISHED } from '@/i18n/locales'

// the atlas's head (lib/seo.ts atlasMetadata, A4 of plan 4): every view of a city canonicalises to the city,
// og:url is the view itself, normalised as the client normalises it; every URL on SITE_URL

const SITE = 'https://frondia.eu'
const saved = process.env.SITE_URL
afterEach(() => { if (saved === undefined) delete process.env.SITE_URL; else process.env.SITE_URL = saved })
const head = async (q: Record<string, string>) => {
  process.env.SITE_URL = SITE
  return atlasMetadata({ locale: 'en', r: await resolveAtlas(q), title: 'T', description: 'D', ogAlt: 'T' })
}
const ogUrl = (m: Awaited<ReturnType<typeof head>>) => (m.openGraph as { url: string }).url

test('every view of a city canonicalises to the city; og:url keeps the view', async () => {
  const m = await head({ city: 'antwerp', q: 'need', lens: 'heat' })
  expect(m.alternates?.canonical).toBe(`${SITE}/atlas?city=antwerp`)
  expect((m.alternates?.languages as Record<string, string>)['x-default']).toBe(`${SITE}/atlas?city=antwerp`)
  expect((m.alternates?.languages as Record<string, string>)['en-GB']).toBe(`${SITE}/atlas?city=antwerp`)
  expect(ogUrl(m)).toBe(`${SITE}/atlas?city=antwerp&q=need&lens=heat`)
  expect(m.robots).toBeUndefined()
  expect(m.title).toBe('T')
  expect((m.openGraph as { images: { url: string; alt: string }[] }).images[0]).toMatchObject({ url: `${SITE}/og/en.jpg`, alt: 'T' })
})

test('a Dutch or French atlas view canonicalises to its own city page; x-default and English stay as they were', async () => {
  process.env.SITE_URL = SITE
  const r = await resolveAtlas({ city: 'ghent', q: 'need', lens: 'heat' })
  for (const [loc, tag, og] of [['nl', 'nl-BE', 'nl_BE'], ['fr', 'fr-BE', 'fr_BE']] as const) {
    const m = atlasMetadata({ locale: loc, r, title: 'T', description: 'D', ogAlt: 'T' })
    const langs = m.alternates?.languages as Record<string, string>
    expect(m.alternates?.canonical).toBe(`${SITE}/${loc}/atlas?city=ghent`)
    expect(langs['x-default']).toBe(`${SITE}/atlas?city=ghent`)
    expect(langs['en-GB']).toBe(`${SITE}/atlas?city=ghent`)
    expect(langs[tag]).toBe(PUBLISHED.length > 1 ? `${SITE}/${loc}/atlas?city=ghent` : undefined)
    expect((m.openGraph as { locale: string }).locale).toBe(og)
    expect((m.openGraph as { images: { url: string }[] }).images[0]?.url).toBe(`${SITE}/og/${loc}.jpg`)
  }
})

test('a bare or stray address is Brussels; a sector of another city is dropped from og:url', async () => {
  expect((await head({})).alternates?.canonical).toBe(`${SITE}/atlas?city=brussels`)
  expect((await head({ city: 'paris' })).alternates?.canonical).toBe(`${SITE}/atlas?city=brussels`)
  expect(ogUrl(await head({ city: 'antwerp', sector: '21004E72-' }))).toBe(`${SITE}/atlas?city=antwerp`)
  expect(ogUrl(await head({ city: 'brussels', sector: '21004E72-' }))).toBe(`${SITE}/atlas?city=brussels&sector=21004E72-`)
})

test('an unknown or injected audit is dropped from og:url (Q12); nothing comes from the request host', async () => {
  const m = await head({ city: 'brussels', case: '<script>' })
  expect(ogUrl(m)).toBe(`${SITE}/atlas?city=brussels`)
  expect(m.alternates?.canonical).toBe(`${SITE}/atlas?city=brussels`)
  // an audit of another city (ninove is Brussels's) is unknown here too
  expect(ogUrl(await head({ city: 'antwerp', case: 'ninove' }))).toBe(`${SITE}/atlas?city=antwerp`)
  // a known one stays
  expect(ogUrl(await head({ city: 'brussels', case: 'ninove' }))).toBe(`${SITE}/atlas?city=brussels&case=ninove`)
})

test('a valid sector survives next to an unknown audit', async () => {
  expect(ogUrl(await head({ city: 'brussels', case: 'nope', sector: '21004E72-' }))).toBe(`${SITE}/atlas?city=brussels&sector=21004E72-`)
})

test('noindex only when the city’s file could not be read', async () => {
  process.env.SITE_URL = SITE
  const r = await resolveAtlas({ city: 'ghent' })
  expect(atlasMetadata({ locale: 'en', r: { ...r, ok: false }, title: 'T', description: 'D', ogAlt: 'T' }).robots).toEqual({ index: false })
})

// the head's words (atlasHeadWords), against the real catalogue
const tr = (namespace: string) => {
  const f = createTranslator({ locale: 'en', messages: en, namespace: namespace as never, onError: (e) => { throw e } })
  return (key: string, values?: TValues) => f(key as never, values as never)
}
// as the page passes it: the sector's name and commune in the page's language (lib/names.ts)
const words = async (q: Record<string, string>, loc: Locale = 'en') => {
  const r = await resolveAtlas(q)
  const sector = r.sector && { name: sectorName(r.sector, loc), place: sectorPlace(r.sector, loc) }
  return atlasHeadWords({ ...r, sector }, tr('atlas'), tr('common'), tr('landing'))
}

test('the title names the view: an audit on change, a sector, a lens, an object, the city', async () => {
  expect((await words({ case: 'ninove' })).title).toBe('Porte de Ninove · Audit · Atlas · Frondia')
  expect((await words({ case: 'ninove' })).description).toBe(en.landing.cases.ninove.story)
  expect((await words({ city: 'brussels', sector: '21004E72-' })).title).toBe('Maison Rouge (Place)-Sud · Brussels · Atlas · Frondia')
  expect((await words({ city: 'antwerp', q: 'need', lens: 'heat' })).title).toBe('Summer heat · Antwerp · Atlas · Frondia')
  expect((await words({ city: 'ghent', q: 'place', obj: 'benches' })).title).toBe('Benches · Ghent · Atlas · Frondia')
  expect((await words({})).title).toBe('Atlas · Brussels · Frondia')
})

test('an audit of this city opens on “what changed” whatever question the address names, and the head says so (Q15)', async () => {
  const w = await words({ case: 'ninove', q: 'need', lens: 'heat' })
  expect(w.title).toBe('Porte de Ninove · Audit · Atlas · Frondia')
  expect(w.description).toBe(en.landing.cases.ninove.story)
  expect(ogUrl(await head({ case: 'ninove', q: 'need', lens: 'heat' }))).toBe(`${SITE}/atlas?city=brussels&case=ninove`)
  // another city's audit is dropped, and the question the address named stays
  const other = await words({ city: 'brussels', case: 'droogdokkenpark', q: 'need', lens: 'heat' })
  expect(other.title).toBe('Summer heat · Brussels · Atlas · Frondia')
  expect(ogUrl(await head({ city: 'brussels', case: 'droogdokkenpark', q: 'need', lens: 'heat' }))).toBe(`${SITE}/atlas?city=brussels&q=need&lens=heat`)
})

test('a sector with no name falls through to the view, not to “ · Brussels”', async () => {
  const r = await resolveAtlas({ city: 'brussels', sector: '21004A19-' })
  expect(r.sector?.n.trim()).toBe('')
  const w = await words({ city: 'brussels', sector: '21004A19-' })
  expect(w.title).toBe('Atlas · Brussels · Frondia')
  expect(w.description).toBe(en.atlas.meta.description)
})

test('a Brussels sector is named in the page’s language: Verzet on /nl/atlas, Resistance in English and French', async () => {
  const q = { city: 'brussels', sector: '21001A00-' }
  expect((await words(q, 'nl')).title).toBe('Verzet · Brussels · Atlas · Frondia')
  expect((await words(q, 'en')).title).toBe('Resistance · Brussels · Atlas · Frondia')
  expect((await words(q, 'fr')).title).toBe('Resistance · Brussels · Atlas · Frondia')
  // the commune in the description too: Bruxelles is Brussel in Dutch
  expect((await words({ city: 'brussels', sector: '21004E72-' }, 'nl')).description).toContain('Brussel')
  expect((await words({ city: 'brussels', sector: '21004E72-' }, 'nl')).title).toBe('Roodhuisplein-Zuid · Brussels · Atlas · Frondia')
})

test('Liège’s sector named “None” in the source is nameless: its head falls through like the Brussels five', async () => {
  const r = await resolveAtlas({ city: 'liege', sector: '62063L0AP' })
  expect(r.sector?.n).toBe('None')
  for (const loc of ['en', 'nl', 'fr'] as const) {
    const w = await words({ city: 'liege', sector: '62063L0AP' }, loc)
    expect(w.title).toBe('Atlas · Liège · Frondia')
    expect(w.description).toBe(en.atlas.meta.description)
  }
})
