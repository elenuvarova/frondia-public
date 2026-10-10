import { afterEach, expect, test, vi } from 'vitest'
import { CITIES, cityOf } from '@/lib/cities'
import { _memo, DataError, getCases, getCity, getCommunes, getDownloads, getLanding, getPoints, getRegister, loadJSON } from '@/lib/data'

// one file with a broken body, served by a stand-in readFile, any file a test puts in `fake.files`, and every name in
// `fake.missing` reported as not there (ENOENT); every other
// file is read for real (a broken file never goes into site/public)
const fake = vi.hoisted(() => ({ files: {} as Record<string, string>, missing: [] as string[] }))
vi.mock('node:fs/promises', async (importOriginal) => {
  const real = await importOriginal<typeof import('node:fs/promises')>()
  const readFile = ((file: string, ...rest: unknown[]) => {
    const name = String(file).split('/').pop() as string
    if (name in fake.files) return Promise.resolve(fake.files[name])
    if (fake.missing.includes(name)) {         // a language file not written yet (plan 5, task 13: nl and fr now are)
      return Promise.reject(Object.assign(new Error(`ENOENT: no such file or directory, open '${String(file)}'`),
        { code: 'ENOENT', errno: -2, syscall: 'open', path: String(file) }))
    }
    return name === 'broken.json' ? Promise.resolve('{"cities": [') : (real.readFile as (...a: unknown[]) => unknown)(file, ...rest)
  }) as typeof real.readFile
  return { ...real, default: { ...real, readFile }, readFile }
})

test('the landing data loads from site/public/data', async () => {
  const d = await getLanding()
  expect(d.bxl.name).toBe('Brussels')
  expect(d.ant.name).toBe('Antwerp')
  expect(d.cases.map((c) => c.slug)).toContain('ninove')
  expect(typeof d.facts.tests).toBe('number')
  expect(d.bxl.thresholds.ndvi).toBeGreaterThan(0)
})

test('a missing file says which file', async () => {
  await expect(loadJSON('nope.json')).rejects.toBeInstanceOf(DataError)
  await expect(loadJSON('nope.json')).rejects.toThrow(/nope\.json/)
})

test('a malformed file says which file', async () => {
  await expect(loadJSON('broken.json')).rejects.toBeInstanceOf(DataError)
  await expect(loadJSON('broken.json')).rejects.toThrow(/data\/broken\.json: .*JSON/)
})

// ── document pages' loaders and cityOf (plan 3, task 1) ─────────────────────────────────────────

test('cityOf resolves every known key and falls back to brussels on anything else', () => {
  for (const key of CITIES) expect(cityOf(key)).toBe(key)
  expect(cityOf('nope')).toBe('brussels')
  expect(cityOf(null)).toBe('brussels')
  expect(cityOf(undefined)).toBe('brussels')
  expect(cityOf('')).toBe('brussels')
})

test('getCity reads each city’s own file', async () => {
  const [bxl, ant, ghent, liege, charleroi] = await Promise.all([
    getCity('brussels'), getCity('antwerp'), getCity('ghent'), getCity('liege'), getCity('charleroi'),
  ])
  expect(bxl.name).toBe('Brussels')
  expect(ant.name).toBe('Antwerp')
  expect(ghent.name).toBe('Ghent')
  expect(liege.name).toBe('Liège')
  expect(charleroi.name).toBe('Charleroi')
  // the dossier reads these directly off the city, not through the lens index signature
  expect(bxl.dossier.pick.ids.length).toBeGreaterThan(0)
  expect(typeof bxl.heat_canopy_r).toBe('number')
})

test('getCases reads cases.json', async () => {
  const cases = await getCases()
  expect(cases.map((c) => c.slug)).toContain('ninove')
})

test('getPoints reads a city’s named points, and is null rather than throwing when a city has none', async () => {
  const bxl = await getPoints('brussels')
  expect(bxl?.points.length).toBeGreaterThan(0)
  expect(typeof bxl?.registered_at).toBe('string')
  await expect(loadJSON('points-nope.json')).rejects.toBeInstanceOf(DataError) // loadJSON itself still throws…
  expect(await getPoints('nope' as never)).toBeNull() // …getPoints turns that into null
})

test('getCommunes reads the flat list of all five cities’ communes', async () => {
  const communes = await getCommunes()
  expect(communes.length).toBeGreaterThan(0)
  expect(communes.every((c) => typeof c.code === 'string')).toBe(true)
})

test('getDownloads reads the per-city download manifests', async () => {
  const downloads = await getDownloads('en')
  for (const key of CITIES) expect(downloads[key].layers.length).toBeGreaterThan(0)
})

test('getRegister reads the register of interventions', async () => {
  const register = await getRegister('en')
  expect(register.contracts.length).toBeGreaterThan(0)
  expect(register.labels.label.yes).toBeTruthy()
})

// ── plan 5, task 7: the data texts in the page's language ────────────────────────────────────────

// nl and fr in their preview state (only English published), whatever the registry says today: the fallback rule is the
// preview's, and the registry flips at plan 5, task 15 (a published language gets no fallback: the test after these)
async function asPreview<T>(run: (data: typeof import('@/lib/data')) => Promise<T>): Promise<T> {
  vi.resetModules()
  vi.doMock('@/i18n/locales', async (importOriginal) => {
    const real = await importOriginal<typeof import('@/i18n/locales')>()
    return { ...real, isPublished: (code: string) => code === 'en' }
  })
  try {
    return await run(await import('@/lib/data'))
  } finally {
    vi.doUnmock('@/i18n/locales')
    vi.resetModules()
  }
}

test('a preview language without its data files reads the English ones; the pseudo-language always does', async () => {
  const [downloads, register] = await Promise.all([getDownloads('en'), getRegister('en')])
  expect(await getDownloads('xx')).toEqual(downloads)      // the language files of nl and fr are there: xx still English
  await asPreview(async ({ getDownloads, getRegister }) => {
    try {
      fake.missing = ['downloads.nl.json', 'downloads.fr.json', 'register.nl.json', 'register.fr.json']
      for (const loc of ['nl', 'fr', 'xx'] as const) {
        expect(await getDownloads(loc), loc).toEqual(downloads)
        expect(await getRegister(loc), loc).toEqual(register)
      }
    } finally {
      fake.missing = []
    }
  })
})

test('the committed Dutch and French data files are read (plan 5, task 13)', async () => {
  const [nl, fr] = await Promise.all([getDownloads('nl'), getRegister('fr')])
  expect(nl.ghent.name).toBe('Gent')
  expect(fr.contracts.map((c) => c.commune)).toContain('Bruxelles')
  expect((await getDownloads('fr')).antwerp.name).toBe('Anvers')
})

test('a language with its own data files reads them', async () => {
  try {
    fake.files['downloads.nl.json'] = JSON.stringify({ ghent: { name: 'Gent', manifest_bytes: 1, layers: [] } })
    fake.files['register.fr.json'] = JSON.stringify({ contracts: [{ id: 1, commune: 'Bruxelles' }] })
    expect((await getDownloads('nl')).ghent.name).toBe('Gent')
    expect((await getRegister('fr')).contracts[0]?.commune).toBe('Bruxelles')
    fake.files['downloads.xx.json'] = '{}'                 // never read: xx is English with accents, its data the English
    expect((await getDownloads('xx')).ghent.name).toBe('Ghent')
  } finally {
    fake.files = {}
  }
})

test('a preview language’s data file that is there but broken is an error, not the English', async () => {
  await asPreview(async ({ getDownloads, loadJSON, DataError }) => {
    try {
      fake.files['downloads.nl.json'] = '{"ghent": {'
      await expect(getDownloads('nl')).rejects.toBeInstanceOf(DataError)
      await expect(getDownloads('nl')).rejects.toThrow(/downloads\.nl\.json: .*JSON/)
      fake.missing = ['downloads.fr.json']
      await expect(loadJSON('downloads.fr.json')).rejects.toMatchObject({ code: 'ENOENT' })   // not there: falls back
      expect((await getDownloads('fr')).ghent.name).toBe('Ghent')
    } finally {
      fake.files = {}
      fake.missing = []
    }
  })
})

test('a published language without its data files is an error, not English', async () => {
  vi.resetModules()
  vi.doMock('@/i18n/locales', async (importOriginal) => {
    const real = await importOriginal<typeof import('@/i18n/locales')>()
    return { ...real, isPublished: (code: string) => code === 'en' || code === 'nl' }
  })
  try {
    fake.missing = ['downloads.nl.json', 'downloads.fr.json', 'register.nl.json', 'register.fr.json']
    const data = await import('@/lib/data')
    await expect(data.getDownloads('nl')).rejects.toBeInstanceOf(data.DataError)
    await expect(data.getRegister('nl')).rejects.toThrow(/register\.nl\.json/)
    expect((await data.getDownloads('fr')).ghent.name).toBe('Ghent')   // fr still in preview
  } finally {
    fake.missing = []
    vi.doUnmock('@/i18n/locales')
    vi.resetModules()
  }
})

// ── plan 4, task 2: one parse per file per process in production, frozen reads elsewhere ───────────

afterEach(() => { vi.unstubAllEnvs(); _memo.clear() })

test('production reads a data file once per process; a failed read is not remembered', async () => {
  vi.stubEnv('NODE_ENV', 'production')
  const a = await loadJSON<unknown[]>('cases.json')
  const b = await loadJSON<unknown[]>('cases.json')
  expect(a).toBe(b)
  expect(_memo.has('cases.json')).toBe(true)
  _memo.clear()
  const [c, d] = await Promise.all([loadJSON('cases.json'), loadJSON('cases.json')])
  expect(c).toBe(d)   // two first reads at once share one parse
  await expect(loadJSON('no-such-file.json')).rejects.toBeInstanceOf(DataError)
  await new Promise((r) => setTimeout(r, 0))
  expect(_memo.has('no-such-file.json')).toBe(false)
})

test('outside production every read is fresh and frozen, so sorting shared data in place fails loudly', async () => {
  vi.stubEnv('NODE_ENV', 'development')
  const a = await loadJSON<{ slug: string }[]>('cases.json')
  expect(Object.isFrozen(a)).toBe(true)
  expect(Object.isFrozen(a[0])).toBe(true)
  expect(() => a.sort()).toThrow(TypeError)
  expect(await loadJSON('cases.json')).not.toBe(a)   // fresh every read
  const city = await loadJSON<{ sectors: object[] }>('brussels.json')
  expect(Object.isFrozen(city.sectors[0])).toBe(true)   // deep, not just the top
  expect(_memo.size).toBe(0)
})
