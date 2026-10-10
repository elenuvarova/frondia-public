import { expect, test } from 'vitest'
import { atlasHref, switchHref } from '@/lib/links'

test('the atlas is a route of the same site now, prefixed by language', () => {
  expect(atlasHref('en')).toBe('/atlas')
  expect(atlasHref('en', '?case=ninove')).toBe('/atlas?case=ninove')
  expect(atlasHref('nl', '?q=need&lens=services')).toBe('/nl/atlas?q=need&lens=services')
})

test('the switch keeps the page and its parameters', () => {
  expect(switchHref('/atlas', 'city=ghent&q=need&lens=heat&sector=44021A00-')).toBe('/atlas?city=ghent&q=need&lens=heat&sector=44021A00-')
  expect(switchHref('/data', '')).toBe('/data')
  expect(switchHref('/', 'x=1')).toBe('/?x=1')
})

test('the switch puts the target language’s prefix on the page, none for English', () => {
  expect(switchHref('/atlas', 'city=ghent&q=need', 'nl')).toBe('/nl/atlas?city=ghent&q=need')
  expect(switchHref('/data', 'city=liege', 'fr')).toBe('/fr/data?city=liege')
  expect(switchHref('/', '', 'fr')).toBe('/fr')
  expect(switchHref('/', 'x=1', 'nl')).toBe('/nl?x=1')
  expect(switchHref('/dossier', 'city=brussels&sector=21004E72-', 'en')).toBe('/dossier?city=brussels&sector=21004E72-')
})

test('at the click the switch also keeps the place on the page', () => {
  expect(switchHref('/register', 'show=yes', 'nl', '#c87')).toBe('/nl/register?show=yes#c87')
  expect(switchHref('/', '', 'fr', '#law')).toBe('/fr#law')
  expect(switchHref('/data', 'city=ghent', 'en', '')).toBe('/data?city=ghent')
})

test('switchHref never doubles a language prefix still in the path (a dotted 404 under /nl or /fr; design wave)', () => {
  expect(switchHref('/nl/foo.php', '', 'nl')).toBe('/nl/foo.php')
  expect(switchHref('/nl/foo.php', '', 'fr')).toBe('/fr/foo.php')
  expect(switchHref('/nl/foo.php', '', 'en')).toBe('/foo.php')
  expect(switchHref('/fr/x.json', 'a=1', 'nl')).toBe('/nl/x.json?a=1')
  expect(switchHref('/fr', '', 'nl')).toBe('/nl')
  expect(switchHref('/nl', '', 'en')).toBe('/')
  // a path that merely starts with the letters is left alone
  expect(switchHref('/nlx/foo', '', 'fr')).toBe('/fr/nlx/foo')
  expect(switchHref('/frondia', '', 'nl')).toBe('/nl/frondia')
})
