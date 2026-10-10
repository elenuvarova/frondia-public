import fs from 'node:fs'
import path from 'node:path'
import { expect, test } from 'vitest'
import { getCases } from '@/lib/data'
import { inLang, placeName, sectorLabel, sectorName, sectorPlace } from '@/lib/names'
import en from '@/messages/en.json'

test('a name in the page language where Statbel has one, the English site’s own otherwise', () => {
  const s = { n: 'RESISTANCE', n_nl: 'VERZET', c: 'Anderlecht' }
  expect(sectorName(s, 'en')).toBe('Resistance')
  expect(sectorName(s, 'nl')).toBe('Verzet')
  expect(sectorName(s, 'fr')).toBe('Resistance')
  expect(sectorName(s, 'xx')).toBe('Resistance')
  expect(sectorPlace({ c: 'Molenbeek', c_nl: 'Sint-Jans-Molenbeek', c_fr: 'Molenbeek-Saint-Jean' }, 'fr')).toBe('Molenbeek-Saint-Jean')
  expect(placeName({ name: 'Ghent', name_nl: 'Gent', name_fr: 'Gand' }, 'fr')).toBe('Gand')
  expect(inLang({ n: 'X', n_nl: '' }, 'n', 'nl')).toBe('X')
})

test('Dutch names keep their particles low', () => {
  expect(sectorName({ n: 'X', n_nl: "VAN DER MEERSCHSTRAAT 'T HOF" }, 'nl')).toBe("Van der Meerschstraat 't Hof")
})

// Liège 62063L0AP is named "None" in the source: a nameless sector, like the five Brussels sectors named ""
test('“None”, empty and blank are no name, in every language', () => {
  for (const n of ['None', '', '  ', ' None ']) {
    for (const loc of ['en', 'nl', 'fr', 'xx'] as const) expect(sectorName({ n }, loc)).toBe('')
  }
  expect(sectorName({ n: 'X', n_nl: 'None' }, 'nl')).toBe('X')
  expect(sectorName({ n: 'None', n_fr: 'Y' }, 'fr')).toBe('Y')
  expect(placeName({ name: 'Ixelles', name_nl: '  ' }, 'nl')).toBe('Ixelles')
})

test('a nameless sector is called by its code where its name is a label or a heading', () => {
  const fb = (id: string) => en.common.sectorFallback.replace('{id}', id)
  expect(en.common.sectorFallback).toBe('Sector {id}')
  expect(sectorLabel({ id: '62063L0AP', n: 'None' }, 'en', fb)).toBe('Sector 62063L0AP')
  expect(sectorLabel({ id: '21004A19-', n: '' }, 'nl', fb)).toBe('Sector 21004A19-')
  expect(sectorLabel({ id: '21001A00-', n: 'RESISTANCE', n_nl: 'VERZET' }, 'nl', fb)).toBe('Verzet')
})

// the matched places of every audit: a control with a Dutch or French name prints it on that page, through the helper
test('every control in cases.json with a language variant renders it through the helper', async () => {
  let seen = 0
  for (const c of await getCases()) {
    for (const x of (c.controls as { name: string; name_nl?: string; name_fr?: string }[])) {
      const r = { n: x.name, n_nl: x.name_nl, n_fr: x.name_fr }
      expect(sectorName(r, 'en'), x.name).toBe(sectorName({ n: x.name }, 'en'))
      for (const loc of ['nl', 'fr'] as const) {
        const v = x[`name_${loc}`]
        if (v == null) { expect(sectorName(r, loc)).toBe(sectorName({ n: x.name }, 'en')); continue }
        seen++
        expect(v.trim()).not.toBe('')
        expect(v).not.toBe(x.name)
        expect(sectorName(r, loc), v).toBe(sectorName({ n: v }, 'en'))
        expect(sectorName(r, loc)).not.toBe(sectorName({ n: x.name }, 'en'))
      }
    }
  }
  expect(seen).toBeGreaterThan(0)
})

// every place name a page prints goes through lib/names; the city is common.cities, the region common.regions
const ROOT = path.resolve(__dirname, '..')
const files = (d: string): string[] => fs.readdirSync(path.join(ROOT, d), { withFileTypes: true })
  .flatMap((e) => e.isDirectory() ? files(path.join(d, e.name)) : /\.tsx?$/.test(e.name) ? [path.join(d, e.name)] : [])
const CONTRACT = /\b(c|commune|law)\??\.name\b/
const RAW_SECTOR = /\b(s|sector|hovered|selected)\??\.[nc]\b/          // a sector's own name or commune, read raw
const LANG_FIELD = /\.(n_nl|n_fr|c_nl|c_fr|name_nl|name_fr)\b/        // a language variant, read past the helper
const BAD = [/\btitleCase\(/, /\bcity_name\b/, /\bc\.region\b/, /\bcity[!?]?\.name\b/, /\br\.city\.name\b/, CONTRACT, RAW_SECTOR, LANG_FIELD]
// each allow names the very pattern it excuses (the guard compares sources), so a file is let off that one and no other:
// the register's `c` is a contract, whose name is the project's own (L6), not a place; the landing finds Zavelenberg by
// its register name (a lookup, nothing printed); the atlas's resolver copies the sector's fields for the head; the
// variants are handed to the helper whole where a row's fields are named otherwise (a control's or an event's `name`),
// and the finder searches every language
const VARIANTS = ['lib/commune.ts', 'lib/atlas/resolve.ts', 'components/Rings.tsx', 'components/atlas/CaseDrawer.tsx', 'app/(site)/[locale]/commune/page.tsx']
const ALLOW: Record<string, RegExp[]> = {
  'app/(site)/[locale]/register/page.tsx': [CONTRACT],
  'app/(site)/[locale]/page.tsx': [RAW_SECTOR],
  ...Object.fromEntries(VARIANTS.map((f) => [f, [LANG_FIELD]])),
}
ALLOW['lib/atlas/resolve.ts']!.push(RAW_SECTOR)
const offences = (rel: string, src: string) =>
  BAD.filter((re) => !(ALLOW[rel] ?? []).some((a) => a.source === re.source) && re.test(src)).map((re) => `${rel}: ${re}`)

test('no page or component reads a place name past lib/names', () => {
  const found: string[] = []
  for (const f of [...files('app'), ...files('components'), ...files('lib')]) {
    const rel = f.split(path.sep).join('/')
    if (/^lib\/(names|format)\.ts$/.test(rel)) continue
    found.push(...offences(rel, fs.readFileSync(path.join(ROOT, f), 'utf8')))
  }
  expect(found).toEqual([])
})

test('the guard catches a raw name or a variant read by hand, and each allow excuses only what it names', () => {
  expect(offences('components/X.tsx', '<b>{s.n}</b>')).toHaveLength(1)
  expect(offences('components/X.tsx', 'const t = `${s.c}`')).toHaveLength(1)
  expect(offences('components/X.tsx', 'x.n_nl ?? x.n')).toHaveLength(1)
  expect(offences('components/X.tsx', '{hovered?.n}')).toHaveLength(1)
  expect(offences('components/X.tsx', '{city?.name}')).toHaveLength(1)
  // the register's contract name would fail without its allow, and that allow does not cover a raw sector name
  const reg = fs.readFileSync(path.join(ROOT, 'app/(site)/[locale]/register/page.tsx'), 'utf8')
  expect(CONTRACT.test(reg)).toBe(true)
  expect(offences('app/(site)/[locale]/register/page.tsx', '{s.n}')).toHaveLength(1)
  expect(offences('lib/commune.ts', '{s.n}')).toHaveLength(1)
})
