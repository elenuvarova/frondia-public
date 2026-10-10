import fs from 'node:fs'
import path from 'node:path'
import { expect, test } from 'vitest'
import { CODES, LOCALES, PUBLISHED, alternates, infoOf, isPublished, localePath, routedLocales, tagOf } from '@/i18n/locales'
import { pct } from '@/lib/format'

// Dutch and French are published together, by one commit (plan 5, task 15) that `git revert` undoes. These tests
// hold in both states, so the revert leaves them green: English alone, or the three languages, nothing in between.
const THREE = ['en', 'nl', 'fr']
const LIVE = PUBLISHED.length > 1

test('English is the unprefixed default; Dutch and French are published together, never the pseudo-language', () => {
  expect(LOCALES.map((l) => l.code)).toEqual([...CODES])
  expect(tagOf('nl')).toBe('nl-BE')
  expect(tagOf('fr')).toBe('fr-BE')
  expect([['en'], THREE]).toContainEqual(PUBLISHED)
  expect(PUBLISHED[0]).toBe('en')
  expect(isPublished('nl')).toBe(isPublished('fr'))
  expect(isPublished('xx')).toBe(false)
})

test('the published state: nl and fr say so in the registry, after their reviews (plan 5, task 15)', () => {
  const src = fs.readFileSync(path.join(__dirname, '../i18n/locales.ts'), 'utf8')
  if (LIVE) expect(src).toContain('the reviews are in i18n/reviews/')
  expect(fs.existsSync(path.join(__dirname, '../i18n/reviews'))).toBe(true)
})

test('preview languages come only from the build variable, never a code the registry lacks', () => {
  expect(routedLocales({})).toEqual(PUBLISHED)
  expect(routedLocales({ NEXT_PUBLIC_PREVIEW_LOCALES: 'nl, fr,xx,de,en' })).toEqual(['en', 'nl', 'fr', 'xx'])
  expect(routedLocales({ NEXT_PUBLIC_PREVIEW_LOCALES: 'xx' })).toEqual([...PUBLISHED, 'xx'])
  expect(routedLocales({ NEXT_PUBLIC_PREVIEW_LOCALES: '' })).toEqual(PUBLISHED)
})

test('the pseudo-language is a development language with English rules', () => {
  const xx = infoOf('xx')
  expect(xx.dev).toBe(true)
  expect(xx.tag).toBe('en-XA')
  expect(xx.short).toBe(infoOf('en').short)
  expect(pct(0.393, 1, 'xx')).toBe('39.3%')
  expect(pct(0.393, 1, 'fr')).toBe('39,3 %')
})

test('paths and hreflang read only published languages', () => {
  expect(localePath('en', '/data')).toBe('/data')
  expect(localePath('nl', '/data')).toBe('/nl/data')
  expect(localePath('fr', '/')).toBe('/fr')
  expect(alternates('/data', 'https://frondia.eu')).toEqual(LIVE ? {
    'en-GB': 'https://frondia.eu/data', 'nl-BE': 'https://frondia.eu/nl/data', 'fr-BE': 'https://frondia.eu/fr/data',
    'x-default': 'https://frondia.eu/data',
  } : {
    'en-GB': 'https://frondia.eu/data', 'x-default': 'https://frondia.eu/data',
  })
  expect(alternates('/', 'https://frondia.eu')).toEqual(LIVE ? {
    'en-GB': 'https://frondia.eu/', 'nl-BE': 'https://frondia.eu/nl', 'fr-BE': 'https://frondia.eu/fr', 'x-default': 'https://frondia.eu/',
  } : { 'en-GB': 'https://frondia.eu/', 'x-default': 'https://frondia.eu/' })
})

test('typo-audit reads the same short words the site ties', () => {
  const src = fs.readFileSync(path.join(__dirname, '../scripts/typo-audit.mjs'), 'utf8')
  expect(src).toContain('short-words.json')
  expect(src).not.toMatch(/const SHORT_WORDS = \{/)
})
