// The checks every language's catalogue must pass (plan 5, task 9): the contract for tasks 10–13. Each section a
// catalogue has is whole and has the English shape, numbers, ids, glossary terms and its own quotes; a published
// language has every section and its data texts. Empty catalogues pass (no section yet); each check is proven on small
// broken catalogues in the task 9 report.
import fs from 'node:fs'
import path from 'node:path'
import { parse, TYPE, type MessageFormatElement } from '@formatjs/icu-messageformat-parser'
import { createTranslator } from 'next-intl'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { expect, test, vi } from 'vitest'
import en from '@/messages/en.json'
import same from '@/i18n/same.json'
import { LOCALES, PUBLISHED, tagOf, type Locale } from '@/i18n/locales'
import { ID } from '@/lib/pseudo'
import { numbersOf } from '../scripts/numbers.mjs'
import { parseTerms, terms } from './glossary'
import { Footer } from '@/components/Footer'

// the footer is a server component: getT is next-intl's translator on the English words, with the page's language
const page = vi.hoisted(() => ({ loc: 'en' as string }))
vi.mock('@/lib/t', async () => {
  const { createTranslator } = await import('next-intl')
  const words = (await import('@/messages/en.json')).default
  return {
    getT: async (ns: string) => {
      const t = createTranslator({ locale: 'en', messages: words as never, namespace: ns as never }) as unknown as
        { (k: string, v?: unknown): string; rich: (k: string, v?: unknown) => unknown; raw: (k: string) => unknown }
      return { loc: page.loc, t: (k: string, v?: unknown) => t(k, v), rich: (k: string, v?: unknown) => t.rich(k, v), raw: (k: string) => t.raw(k) }
    },
  }
})

type Tree = { [k: string]: unknown }
const read = (code: string): Tree => JSON.parse(fs.readFileSync(path.join(__dirname, `../messages/${code}.json`), 'utf8'))
const leaves = (o: unknown, p = ''): [string, unknown][] => o && typeof o === 'object'
  ? Object.entries(o).flatMap(([k, v]) => leaves(v, p ? `${p}.${k}` : k)) : [[p, o]]
const LANGS = LOCALES.filter((l) => l.code !== 'en' && !l.dev).map((l) => l.code) as Exclude<Locale, 'en' | 'xx'>[]
const EN = new Map(leaves(en))

interface Shape { args: string[]; tags: string[]; literal: string }
function shape(m: string): Shape {
  const args: string[] = [], tags: string[] = []; let literal = ''
  const walk = (els: MessageFormatElement[]) => {
    for (const e of els) {
      if (e.type === TYPE.literal) literal += e.value + ' '
      else if (e.type === TYPE.argument || e.type === TYPE.number || e.type === TYPE.date) args.push(`${e.type}:${e.value}`)
      else if (e.type === TYPE.select) { args.push(`select:${e.value}:${Object.keys(e.options).sort().join('|')}`); Object.values(e.options).forEach((o) => walk(o.value)) }
      else if (e.type === TYPE.plural) { args.push(`plural:${e.value}`); Object.values(e.options).forEach((o) => walk(o.value)) }
      else if (e.type === TYPE.tag) { tags.push(e.value); walk(e.children) }
    }
  }
  walk(parse(m, { ignoreTag: false }))
  return { args: [...new Set(args)].sort(), tags: tags.sort(), literal }
}
const pluralOptions = (m: string): string[][] => {
  const out: string[][] = []
  const walk = (els: MessageFormatElement[]) => { for (const e of els) {
    if (e.type === TYPE.plural) { out.push(Object.keys(e.options)); Object.values(e.options).forEach((o) => walk(o.value)) }
    else if (e.type === TYPE.select) Object.values(e.options).forEach((o) => walk(o.value))
    else if (e.type === TYPE.tag) walk(e.children)
  } }
  walk(parse(m, { ignoreTag: false }))
  return out
}

const pluralUsesPound = (m: string): boolean => {
  let found = false
  const walk = (els: MessageFormatElement[], inPlural: boolean) => { for (const e of els) {
    if (e.type === TYPE.pound && inPlural) found = true
    else if (e.type === TYPE.plural) Object.values(e.options).forEach((o) => walk(o.value, true))
    else if (e.type === TYPE.select) Object.values(e.options).forEach((o) => walk(o.value, inPlural))
    else if (e.type === TYPE.tag) walk(e.children, inPlural)
  } }
  walk(parse(m, { ignoreTag: false }), false)
  return found
}
// the values a message is rendered with: n for counts, the first named option for a select, "X" for a text, tags as is
function valuesFor(m: string, n: number): Record<string, unknown> {
  const { args, tags } = shape(m)
  const values: Record<string, unknown> = {}
  for (const a of args) {
    const [type, name, opts] = a.split(':')
    values[name!] = type === 'plural' || type === 'number' ? n : type === 'select' ? opts!.split('|').find((o) => o !== 'other') ?? 'other' : 'X'
  }
  for (const tag of tags) values[tag] = (chunks: string) => chunks
  return values
}
// codes are written as their owners write them in every language (glossary, How to translate 7): a licence's version
// and a UN indicator's number are names, not quantities, so they keep their point and are left out of the number check
const CODES = /\bCC BY 4\.0\b|\bODbL 1\.0\b|\bindica\w* 11\.7\b/g
const uncoded = (s: string) => s.replace(CODES, ' ')
const COOLING = { nl: /koel|afkoel|verkoel/i, fr: /rafra[iî]ch|refroid|fraîcheur/i } as const

for (const loc of LANGS) {
  const cat = read(loc)
  const sections = Object.keys(cat)
  const own = new Map(leaves(cat))
  const inSections = [...EN].filter(([k]) => sections.includes(k.split('.')[0]!))

  test(`${loc}: each section it has is whole, with nothing extra`, () => {
    for (const s of sections) expect(Object.keys(en), s).toContain(s)
    expect([...own.keys()].sort()).toEqual(inSections.map(([k]) => k).sort())
  })
  test(`${loc}: same arguments, options and tags`, () => {
    for (const [k, v] of inSections) if (typeof v === 'string' && !ID.test(k)) {
      const a = shape(v), b = shape(own.get(k) as string)
      expect(b.args, k).toEqual(a.args); expect(b.tags, k).toEqual(a.tags)
      for (const opts of pluralOptions(own.get(k) as string)) expect(opts, k).toContain('other')
    }
  })
  test(`${loc}: the same numbers, in its own notation`, () => {
    for (const [k, v] of inSections) if (typeof v === 'string' && !ID.test(k)) {
      expect(numbersOf(uncoded(shape(own.get(k) as string).literal), loc), k).toEqual(numbersOf(uncoded(shape(v).literal), 'en'))
    }
  })
  test(`${loc}: ids in lists unchanged, lists as long`, () => {
    for (const [k, v] of inSections) if (ID.test(k)) expect(own.get(k), k).toBe(v)
  })
  test(`${loc}: no line left in English unless listed with a reason`, () => {
    const allowed = (same as Record<string, Record<string, string>>)[loc] ?? {}
    for (const [k, v] of inSections) if (typeof v === 'string' && !ID.test(k) && own.get(k) === v) expect(allowed[k], `${k} is still English`).toBeTruthy()
  })
  test(`${loc}: glossary terms where the English uses them`, () => {
    // a line kept in English with a reason in same.json (the rights holders' credits) is not translated: no terms apply
    const kept = (k: string, v: string) => own.get(k) === v && !!(same as Record<string, Record<string, string>>)[loc]?.[k]
    for (const g of terms()) for (const [k, v] of inSections) if (typeof v === 'string' && !ID.test(k) && !kept(k, v) && g.en.test(v)) {
      expect(own.get(k), `${k}: ${g.en}`).toMatch(g[loc])
    }
  })
  test(`${loc}: its own quotes and apostrophes`, () => {
    for (const [k, v] of own) if (typeof v === 'string' && !ID.test(k)) {
      expect(v, k).not.toMatch(/[“”]/)                              // nl ‘ ’, fr « » (i18n/locales.ts)
      expect(v, k).not.toMatch(/\p{L}'\p{L}/u)                       // the apostrophe is ’
      expect(v, k).not.toContain(' ')                           // no-break spaces are tie()'s job
      if (loc === 'nl') expect(v, k).not.toMatch(/[«»]/)
      if (loc === 'fr') {
        expect(v, k).not.toMatch(/‘/)
        expect(v, k).not.toMatch(/\p{L}[;!?]/u)                      // a space before ; ! ? (tie() makes it narrow)
        expect(v, k).not.toMatch(/«(?! )|(?<! )»/)                   // a space inside « » (tie() makes it no-break)
      }
    }
  })
  // French counts 0 with 1 («0 secteur»): a plural that prints its number has `one`, no `zero` (not a French category)
  // and no `=N` (which would part 0 from 1), and reads the same at 0 as at 1 but for the digit
  if (loc === 'fr') test('fr: a plural treats 0 as 1', () => {
    for (const [k, v] of inSections) if (typeof v === 'string' && pluralOptions(v).length) {
      const m = own.get(k) as string
      for (const opts of pluralOptions(m)) {
        expect(opts.filter((o) => o === 'zero' || /^=\d+$/.test(o)), `${k}: zero or =N`).toEqual([])
        if (pluralUsesPound(m)) expect(opts, `${k}: one`).toContain('one')
      }
      const [ns, ...rest] = k.split('.')
      const t = createTranslator({ locale: tagOf(loc), messages: cat as never, namespace: ns as never })
      const at = (n: number) => (t as unknown as { markup: (k: string, v: unknown) => string }).markup(rest.join('.'), valuesFor(own.get(k) as string, n)).split(/\s+/)
      const zero = at(0), one = at(1)
      expect(zero.length, `${k} @ 0 vs 1`).toBe(one.length)
      // each word at 0 is the word at 1, or the same word with its count 1 written 0
      zero.forEach((w, i) => expect([one[i], one[i]!.replace(/(?<![\d.,])1(?![\d.,])/g, '0')], `${k} @ 0: ${zero.join(' ')} / @ 1: ${one.join(' ')}`).toContain(w))
    }
  })
  // the site never promises cooling: a cooling word in a translation only where the English key speaks of cooling
  test(`${loc}: no cooling the English does not mention`, () => {
    for (const [k, v] of inSections) if (typeof v === 'string' && !ID.test(k) && !/cool/i.test(v)) {
      expect(own.get(k), `${k}: cooling`).not.toMatch(COOLING[loc])
    }
  })
  test(`${loc}: every plural renders at 0, 1, 2 and 1000`, () => {
    for (const [k, v] of inSections) if (typeof v === 'string' && pluralOptions(v).length) {
      const [ns, ...rest] = k.split('.')
      const t = createTranslator({ locale: tagOf(loc), messages: cat as never, namespace: ns as never })
      for (const n of [0, 1, 2, 1000]) {
        const out = (t as unknown as { markup: (k: string, v: unknown) => string }).markup(rest.join('.'), valuesFor(own.get(k) as string, n))
        expect(out, `${k} @ ${n}`).not.toMatch(/[{}]/)
      }
    }
  })
}

test('a published language has every section, and its data texts', () => {
  for (const loc of PUBLISHED.filter((l) => l !== 'en')) {
    expect(Object.keys(read(loc)).sort(), loc).toEqual(Object.keys(en).sort())
    for (const f of ['downloads', 'register']) expect(fs.existsSync(path.join(__dirname, `../../public/data/${f}.${loc}.json`)), `${f}.${loc}.json`).toBe(true)
  }
})

// ── the number rule, shared with Python (scripts/site/texts.py nums, tests/test_texts.py) ─────────────────────────────
const CASES = JSON.parse(fs.readFileSync(path.join(__dirname, '../scripts/numbers-cases.json'), 'utf8')).cases as [string, 'en' | 'nl' | 'fr', string[], string][]

test('numbersOf reads each notation alike, and a wrong notation differs', () => {
  expect(numbersOf('1,246,136 people, 0.0373', 'en')).toEqual(['0.0373', '1246136'])
  expect(numbersOf('1.246.136 inwoners, 0,0373', 'nl')).toEqual(['0.0373', '1246136'])
  expect(numbersOf('1 246 136 habitants, 0,0373', 'fr')).toEqual(['0.0373', '1246136'])
  expect(numbersOf('2017–2024', 'nl')).toEqual(['2017', '2024'])
  expect(numbersOf('1.5 km', 'nl')).not.toEqual(['1.5'])            // an English decimal is no Dutch number
  expect(numbersOf('Pour 1 000 habitants', 'fr')).not.toEqual(numbersOf('Per 1,000 residents', 'en'))   // plain space
})

test('numbersOf gives every shared case the answer Python gives', () => {
  expect(CASES.length).toBeGreaterThanOrEqual(20)
  for (const [text, lang, want, why] of CASES) expect(numbersOf(text, lang), `${text} (${lang}): ${why}`).toEqual(want)
})

// ── the glossary itself ──────────────────────────────────────────────────────────────────────────────────────────────
const SOURCE = (lang: 'nl' | 'fr') => fs.readFileSync(path.join(__dirname, `../i18n/sources/eurlex-32024R1991-${lang}.txt`), 'utf8')

test('the glossary parses, and each Regulation term is the wording of its EUR-Lex excerpt', () => {
  const all = terms()
  expect(all.length).toBeGreaterThanOrEqual(20)
  const eurlex = all.filter((g) => g.source.startsWith('EUR-Lex'))
  expect(eurlex.length).toBeGreaterThanOrEqual(10)
  const nl = SOURCE('nl'), fr = SOURCE('fr')
  for (const g of eurlex) { expect(nl, `${g.nl}`).toMatch(g.nl); expect(fr, `${g.fr}`).toMatch(g.fr) }
  for (const lang of ['nl', 'fr'] as const) {
    const first = SOURCE(lang).split('\n')[0]!
    expect(first).toMatch(new RegExp(`^Source: https://eur-lex\\.europa\\.eu/legal-content/${lang.toUpperCase()}/TXT/HTML/\\?uri=CELEX:32024R1991 \\(read \\d{4}-\\d{2}-\\d{2}`))
  }
})

test('the glossary covers the Regulation, the units and Frondia’s own district labels', () => {
  const all = terms()
  const covered = (en: string, nl: string, fr: string) =>
    expect(all.some((g) => g.en.test(en) && g.nl.test(nl) && g.fr.test(fr)), en).toBe(true)
  covered('Nature Restoration Regulation', 'natuurherstelverordening', 'règlement relatif à la restauration de la nature')
  covered('urban ecosystems', 'stedelijke ecosystemen', 'écosystèmes urbains')
  covered('urban green space', 'stedelijke groene ruimte', 'espaces verts urbains')
  covered('urban tree canopy', 'stedelijke boomkroonbedekking', 'couvert arboré urbain')
  covered('urban ecosystem areas', 'stedelijke ecosysteemgebieden', 'zones d’écosystème urbain')
  covered('no net loss', 'geen nettoverlies', 'pas de perte nette')
  covered('no net loss', 'geen nettoverlies', 'absence de perte nette')
  covered('greenness', 'groenheid', 'indice de végétation (NDVI)')
  covered('greener beyond noise', 'groener boven de ruis', 'plus vert au-delà du bruit')
  covered('greening', 'vergroening', 'verdissement')
  covered('12 matched places', '12 vergelijkingsplaatsen', '12 zones témoins')
  covered('comparison sectors', 'vergelijkingssectoren', 'secteurs témoins')
  covered('Open the lens', 'Open deze weergave', 'Ouvrir cette vue')
  covered('local administrative unit', 'lokale bestuurlijke eenheid', 'unité administrative locale')
  covered('statistical sector', 'statistische sector', 'secteur statistique')
  covered('commune', 'gemeente', 'commune')
  // site_data.py DISTRICT_I18N, one row each
  covered('Liège (north)', 'Luik (noord)', 'Liège (nord)')
  covered('Liège (south)', 'Luik (zuid)', 'Liège (sud)')
  covered('Haven', 'Haven', 'Port')
  // the candidates EUR-Lex does not use are not accepted as the official term
  expect(all.find((g) => g.en.test('urban ecosystem area'))!.fr.test('zones d’écosystèmes urbains')).toBe(false)
  expect(all.find((g) => g.en.test('local administrative unit'))!.nl.test('lokale administratieve eenheid')).toBe(false)
  expect(all.find((g) => g.en.test('no net loss'))!.fr.test('aucune perte nette')).toBe(false)
  expect(all.find((g) => g.en.test('greenness'))!.fr.test('la verdeur')).toBe(false)
  expect(all.find((g) => g.en.test('matched places'))!.fr.test('lieux témoins')).toBe(false)
  expect(all.find((g) => g.en.test('the lens'))!.fr.test('la lentille')).toBe(false)
})

test('a glossary row half in code is refused, a guidance row is skipped, and \\| is an alternation', () => {
  const md = (row: string) => `## Terms\n\n| en | nl | fr | source | why |\n|---|---|---|---|---|\n${row}\n\n## How to translate\n| \`x\` | \`y\` | \`z\` | s | w |\n`
  expect(parseTerms(md('| lens | lens | lentille | method | a view |'))).toEqual([])
  expect(() => parseTerms(md('| `a` | b | `c` | s | w |'))).toThrow(/half in code/)
  const [g] = parseTerms(md('| `cat\\|dog` | `kat` | `chat` | s | w |'))
  expect(g!.en.test('a DOG')).toBe(true)
  expect(parseTerms(md('| `a` | `b` | `c` | s | w |'))).toHaveLength(1)   // the row under "How to translate" is not read
})

test('same.json lists only real keys, each with a reason', () => {
  for (const [loc, keys] of Object.entries(same as Record<string, Record<string, string>>)) {
    expect(LANGS as string[], loc).toContain(loc)
    for (const [k, why] of Object.entries(keys)) { expect(EN.has(k), `${loc}: ${k}`).toBe(true); expect(why.trim(), k).not.toBe('') }
  }
})

test('the colophon says the translation is by machine, on a translated page only', async () => {
  const line = en.common.footer.translation
  expect(line).toBe('Machine-translated with Claude and reviewed by a second model; not yet reviewed by a native speaker.')
  const footer = async (loc: string) => { page.loc = loc; return renderToStaticMarkup(await Footer({})) }
  expect(await footer('en')).not.toContain(line)
  for (const loc of LANGS) expect(await footer(loc), loc).toContain(`<p class="small">${line}</p>`)
  page.loc = 'en'
})

// the spec's colophon line, word for word (§2): a translated page says it was translated by machine and read by a model only
test('the colophon line of each translation is the spec’s, word for word', () => {
  const SPEC: Record<string, string> = {
    nl: 'Machinaal vertaald met Claude en nagelezen door een tweede model; nog niet nagelezen door een moedertaalspreker.',
    fr: 'Traduit automatiquement avec Claude et relu par un second modèle ; pas encore relu par un locuteur natif.',
  }
  for (const loc of LANGS) {
    const cat = read(loc) as { common?: { footer?: { translation?: string } } }
    if (cat.common) expect(cat.common.footer?.translation, loc).toBe(SPEC[loc])
  }
  expect(Object.keys(SPEC).sort()).toEqual([...LANGS].sort())
})
