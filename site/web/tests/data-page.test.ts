import { createTranslator } from 'next-intl'
import { expect, test } from 'vitest'
import { dataQuery, hasDataset, indexable, resolveData } from '@/lib/data-page'
import { downloadName, downloadPath, temporalCoverage } from '@/lib/downloads'
import { datasetLd, licenceLd } from '@/lib/seo'
import { CITIES } from '@/lib/cities'
import type { DownloadsCity } from '@/lib/types'
import en from '@/messages/en.json'

// the data page's known answers (plan 3, task 4): what an address opens, and each city's layers as a
// schema.org Dataset — checked against the production page 28 Sep 2026

const t = createTranslator({ locale: 'en', messages: en, namespace: 'data', onError: (e) => { throw e } })
const common = createTranslator({ locale: 'en', messages: en, namespace: 'common', onError: (e) => { throw e } })
const SITE = 'https://frondia.eu'

test('an address opens a city, and a stray city is Brussels without a Dataset — never an error', async () => {
  const bare = await resolveData({}, 'en')
  expect(bare.state).toBe('ok')
  expect(bare.city).toBe('brussels')
  expect(dataQuery(bare)).toBe('?city=brussels')
  expect(indexable(bare)).toBe(true)
  expect(hasDataset(bare)).toBe(true)

  for (const city of CITIES) {
    const r = await resolveData({ city }, 'en')
    expect(r.state === 'ok' && r.d.layers.length, city).toBeGreaterThan(20)
    expect(indexable(r)).toBe(true)
    expect(hasDataset(r)).toBe(true)
    expect(dataQuery(r)).toBe(`?city=${city}`)
  }
  const liege = await resolveData({ city: 'liege' }, 'en')
  expect(liege.state === 'ok' && liege.d.name).toBe('Liège')

  // URLSearchParams.get: an empty city is none, a repeated one reads its first value
  expect((await resolveData({ city: '' }, 'en')).city).toBe('brussels')
  expect(indexable(await resolveData({ city: '' }, 'en'))).toBe(true)
  expect((await resolveData({ city: ['ghent', 'liege'] }, 'en')).city).toBe('ghent')

  for (const odd of ['paris', 'Brussels', 'ANTWERP', '<x>']) {
    const r = await resolveData({ city: odd }, 'en')
    expect(r.state, odd).toBe('ok')
    expect(r.city).toBe('brussels')
    // ruling Q16: indexable under Brussels's canonical, like the dossier's stray ?city=; no Dataset
    expect(indexable(r), odd).toBe(true)
    expect(hasDataset(r), odd).toBe(false)
    expect(dataQuery(r)).toBe('?city=brussels')
  }
})

test('a page in Dutch reads its own data texts, with the English numbers and files (plan 5, task 13)', async () => {
  const [en, nl] = await Promise.all([resolveData({ city: 'liege' }, 'en'), resolveData({ city: 'liege' }, 'nl')])
  if (en.state !== 'ok' || nl.state !== 'ok') throw new Error('downloads unreadable')
  expect(nl.d.name).toBe('Luik')
  expect(nl.d.layers.map((l) => [l.key, l.file, l.threshold])).toEqual(en.d.layers.map((l) => [l.key, l.file, l.threshold]))
  expect(nl.d.layers.find((l) => l.key === 'sectors')?.title).toBe('Statistische sectoren')
  // the preview fallback to the English files (no file for the language) is tested in data.test.ts
})

test('the time span comes from the city data: the trend windows and the latest season', async () => {
  expect(temporalCoverage('2017–2019 → 2021–2024', 2026)).toBe('2017/2026')
  expect(temporalCoverage('2017–2019 → 2021–2024', null)).toBe('2017/2024')
  expect(temporalCoverage(undefined, null)).toBeNull()
  const r = await resolveData({ city: 'ghent' }, 'en')
  expect(r.state === 'ok' && r.temporal).toBe('2017/2026')
})

test('a download keeps its frondia- name and its static address', () => {
  expect(downloadPath('ghent', 'sectors.csv')).toBe('/downloads/ghent/sectors.csv')
  expect(downloadName('ghent', 'sectors.csv')).toBe('frondia-ghent-sectors.csv')
})

test('each city is a Dataset with Google’s required fields and absolute files on SITE_URL', async () => {
  for (const city of CITIES) {
    const r = await resolveData({ city }, 'en')
    if (r.state !== 'ok') throw new Error(r.state)
    const name = t('ld.name', { city: common(`cities.${city}`) })
    const ld = datasetLd(city, r.d, SITE, { loc: 'en', name, place: common(`cities.${city}`), description: t('lede'), country: t('ld.country'), temporalCoverage: r.temporal })
    expect(ld['@context']).toBe('https://schema.org')
    expect(ld['@type']).toBe('Dataset')
    // Google Dataset Search requires name and description (50–5000 characters)
    expect(ld.name).toBe(`Frondia — ${r.d.name}: every layer behind the atlas`)
    const desc = ld.description as string
    expect(desc.length).toBeGreaterThanOrEqual(50)
    expect(desc.length).toBeLessThanOrEqual(5000)
    expect(ld.url).toBe(`${SITE}/data?city=${city}`)
    expect(ld.creator).toEqual({ '@type': 'Person', name: 'Elena Uvarova' })
    expect(ld.spatialCoverage).toEqual({ '@type': 'Place', name: r.d.name, containedInPlace: { '@type': 'Country', name: 'Belgium' } })
    expect(ld.temporalCoverage).toBe('2017/2026')

    const dist = ld.distribution as Record<string, unknown>[]
    expect(dist).toHaveLength(r.d.layers.length + 1)
    for (const d of dist) {
      expect(d['@type']).toBe('DataDownload')
      const u = new URL(d.contentUrl as string)   // absolute, or this throws
      expect(u.origin).toBe(SITE)
      expect(u.pathname.startsWith(`/downloads/${city}/`), u.pathname).toBe(true)
      expect(['text/csv', 'application/geopackage+sqlite3', 'application/json']).toContain(d.encodingFormat)
    }
    expect(dist.at(-1)).toMatchObject({ name: 'manifest.json', contentUrl: `${SITE}/downloads/${city}/manifest.json`, encodingFormat: 'application/json' })

    // every layer's own licence, word for word from downloads.json; the cities mix CC BY with ODbL,
    // so the dataset as a whole claims none
    r.d.layers.forEach((l, i) => expect((dist[i]!.license as { name: string }).name).toBe(l.licence))
    expect(new Set(r.d.layers.map((l) => l.licence)).size).toBeGreaterThan(1)
    expect(ld.license).toBeUndefined()
    expect(dist.at(-1)!.license).toBeUndefined()
  }
})

test('a city whose layers share one licence gets it on the dataset too, and nothing is assumed', () => {
  const layer = { key: 'a', group: 'Sectors', title: 'A', file: 'a.csv', format: null, rows: 1, bytes: 1, computed: null, measures: 'm', method: '', source: '', threshold: null, threshold_from: '', limits: [], licence: 'CC BY 4.0', credit: [], columns: [] }
  const d: DownloadsCity = { name: 'Ghent', manifest_bytes: 1, layers: [layer, { ...layer, key: 'b', file: 'b.gpkg', format: 'GeoPackage', computed: '2026-09-27' }] }
  const ld = datasetLd('ghent', d, 'https://example.org', { loc: 'en', name: 'n', place: 'Ghent', description: 'd', country: 'Belgium' })
  expect(ld.license).toEqual({ '@type': 'CreativeWork', name: 'CC BY 4.0', url: 'https://creativecommons.org/licenses/by/4.0/' })
  expect(ld.temporalCoverage).toBeUndefined()
  expect(ld.dateModified).toBe('2026-09-27')
  const dist = ld.distribution as Record<string, unknown>[]
  expect(dist[0]).toMatchObject({ contentUrl: 'https://example.org/downloads/ghent/a.csv', encodingFormat: 'text/csv' })
  expect(dist[0]!.dateModified).toBeUndefined()
  expect(dist[1]).toMatchObject({ encodingFormat: 'application/geopackage+sqlite3', dateModified: '2026-09-27' })
  expect(dist[2]!.license).toEqual(ld.license)
  // a licence the data names but this code doesn't know keeps its name and gets no invented address
  expect(licenceLd('Something else')).toEqual({ '@type': 'CreativeWork', name: 'Something else' })
  expect(licenceLd('ODbL 1.0 (derived from OpenStreetMap)').url).toBe('https://opendatacommons.org/licenses/odbl/1-0/')
})

test('the Dataset names the language its name and description are written in, as the WebSite does (re-check 4, 5 Oct)', () => {
  const layer = { key: 'a', group: 'Sectors', title: 'A', file: 'a.csv', format: null, rows: 1, bytes: 1, computed: null, measures: 'm', method: '', source: '', threshold: null, threshold_from: '', limits: [], licence: 'CC BY 4.0', credit: [], columns: [] }
  const d: DownloadsCity = { name: 'Ghent', manifest_bytes: 1, layers: [layer] }
  const text = { name: 'n', place: 'Gent', description: 'd', country: 'België' }
  expect(datasetLd('ghent', d, 'https://example.org', { loc: 'en', ...text }).inLanguage).toBe('en-GB')
  expect(datasetLd('ghent', d, 'https://example.org', { loc: 'nl', ...text }).inLanguage).toBe('nl-BE')
  expect(datasetLd('ghent', d, 'https://example.org', { loc: 'fr', ...text }).inLanguage).toBe('fr-BE')
})

test('the catalogue keeps the old page’s lines', () => {
  expect(t('title')).toBe('Every number, and how it was made')
  expect(t('meta.title', { city: 'Liège' })).toBe('Data · Liège · Frondia')
  expect(t('file.rows', { count: 1, n: '1' })).toBe('1 row')
  expect(t('file.rows', { count: 2172, n: '2,172' })).toBe('2,172 rows')
  expect(t('file.polygons', { count: 1, n: '1' })).toBe('1 polygon')
  expect(t('file.polygons', { count: 19, n: '19' })).toBe('19 polygons')
  expect(t('download', { fmt: 'GeoPackage' })).toBe('Download GeoPackage')
  // the literal <layer title> and <city> are ICU-quoted ('<'); the typed translator's parser does not
  // follow the quotes and sees no {site}, so this one call goes through a plain signature
  const plain = t as unknown as (key: string, values: Record<string, string>) => string
  expect(plain('colophon.1.v', { site: 'frondia.ontwrpn.com/data' }))
    .toBe('Frondia, “<layer title>”, <city>, frondia.ontwrpn.com/data, with the date the layer was computed.')
})
