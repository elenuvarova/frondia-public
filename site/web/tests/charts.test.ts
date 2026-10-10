import { createElement, type ReactElement, type ReactNode } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { createTranslator, NextIntlClientProvider } from 'next-intl'
import { expect, test } from 'vitest'
import { BeforeAfter } from '@/components/BeforeAfter'
import { NullHistogram } from '@/components/NullHistogram'
import { Rings } from '@/components/Rings'
import { Series, type SeriesProps } from '@/components/Series'
import { tie, tieRich } from '@/lib/typography'
import en from '@/messages/en.json'
import fr from '@/messages/fr.json'
import nl from '@/messages/nl.json'

const hist = { raw: [1, 2, 1], effect: [1, 3, 1], n: 3, hi: 0.1, lo: -0.1 }
const series = { threshold: 0.05, seasons: [{ season: 2020, effect: 0.02 }, { season: 2021, effect: 0.123 }] }

// the client charts read common.charts from the provider, as on the page
const wrap = (el: ReactElement) => renderToStaticMarkup(createElement(NextIntlClientProvider, { locale: 'en', timeZone: 'Europe/Brussels', messages: en, children: el }))
// Series is a server component: it gets getT('common')'s { t, rich }; this is the same pair, tied the same way
const common = createTranslator({ locale: 'en', messages: en, namespace: 'common', onError: (e) => { throw e } })
const i18n: SeriesProps['i18n'] = {
  t: (key, v) => tie((common as unknown as (k: string, v?: object) => string)(key, v), 'en'),
  rich: (key, v) => tieRich((common.rich as unknown as (k: string, v?: object) => ReactNode)(key, v), 'en'),
}
// the words as read: tags gone, the no-break spaces and word joiners tie() sets read as plain spaces
const plain = (html: string) => html.replace(/[\u00a0\u202f]/g, ' ').replace(/\u2060/g, '')
const text = (html: string) => plain(html.replace(/<[^>]+>/g, ''))

test('the histogram axis and marker read in the page language', () => {
  const marker = { value: 0.25, label: 'Porte de Ninove' }
  const en = wrap(createElement(NullHistogram, { hist, thr: 0.0373, marker, loc: 'en' }))
  expect(en).toContain('+0.037')
  expect(en).toContain('+0.250')
  const fr = wrap(createElement(NullHistogram, { hist, thr: 0.0373, marker, loc: 'fr' }))
  expect(fr).toContain('−0,037')
  expect(fr).toContain('+0,250')
})

test('the histogram without a label names itself from the catalogue, its threshold in the page language', () => {
  expect(plain(wrap(createElement(NullHistogram, { hist, thr: 0.0373, loc: 'en' }))))
    .toContain('aria-label="Distribution of 5 sector effects; threshold ±0.037"')
  expect(plain(wrap(createElement(NullHistogram, { hist, thr: 0.0373, loc: 'fr' }))))
    .toContain('aria-label="Distribution of 5 sector effects; threshold ±0,037"')
  // a label the page passes still wins
  expect(wrap(createElement(NullHistogram, { hist, thr: 0.0373, label: 'Mine', loc: 'en' }))).toContain('aria-label="Mine"')
})

test('the before/after slider says its split from the catalogue', () => {
  const html = wrap(createElement(BeforeAfter, { before: '/a.jpg', after: '/b.jpg', altBefore: 'a', altAfter: 'b', tagBefore: 'A', tagAfter: 'B', label: 'Compare' }))
  expect(plain(html)).toContain('aria-valuetext="50% before, 50% after"')
})

test('the series titles read in the page language; English by default', () => {
  expect(renderToStaticMarkup(createElement(Series, { series, i18n, loc: 'en' }))).toContain('2021: +0.123')
  expect(renderToStaticMarkup(createElement(Series, { series, i18n, loc: 'nl' }))).toContain('2021: +0,123')
})

test('the series speaks from common.charts.series: caption, point titles, opening year, missing summers', () => {
  const html = renderToStaticMarkup(createElement(Series, { series, i18n, loc: 'en' }))
  expect(text(html)).toContain('Above the noise in 1 of 2 summers, 2020–2021')
  expect(html).toMatch(/<b>1[  ]of[  ]2<\/b>/)
  expect(html).toContain('<title>2021: +0.123</title>')
  expect(plain(html)).toContain('aria-label="Effect by summer, 2020–2021: above the threshold in 1 of 2 summers"')
  expect(text(html)).not.toContain('opened')
  expect(text(html)).not.toContain('no summer')

  expect(text(renderToStaticMarkup(createElement(Series, { series, i18n, completed: 2019, loc: 'en' })))).toContain('2020–2021 · opened 2019')

  const gap = { threshold: 0.05, seasons: [...series.seasons, { season: 2023, effect: 0.01, scenes: 12 }] }
  const g = renderToStaticMarkup(createElement(Series, { series: gap, i18n, loc: 'en' }))
  expect(text(g)).toContain('· no summer in the series: 2022')
  expect(text(g)).toContain('2023: +0.010 · 12 scenes')
})

test('the rings speak from common.charts.rings: an absent summer, a note, no scenes, a place 0 km away or with no distance', () => {
  // 2021 is missing (an absent ring); 2022 carries a note and 0 scenes; 2023 is within noise with 9 scenes
  const c = {
    completed: 2019,
    series: { threshold: 0.05, seasons: [{ season: 2020, effect: 0.12, scenes: 14 }, { season: 2022, effect: 0.2, scenes: 0 }, { season: 2023, effect: 0.01, scenes: 9 }] },
    controls: [{ id: 'a', name: 'RUE DE WAND', dist_km: 0 }, { id: 'b', name: 'GARE' }, { id: 'c', name: 'HOPITAUX', dist_km: 4.1 }],
  }
  const html = plain(wrap(createElement(Rings, { c, place: 'Porte de Ninove', notes: { 2021: { text: 'no clear sky' }, 2022: { text: 'works on the site' } }, animate: false })))
  const titles = [...html.matchAll(/<title>([^<]*)<\/title>/g)].map((m) => m[1])
  // the twelve dots: a place 0 km away keeps its distance (one decimal, as the case drawer prints it); one with none
  // says nothing about it
  expect(titles).toContain('Matched place 1: Rue de Wand · 0.0 km')
  expect(titles).toContain('Matched place 2: Gare')
  expect(titles).toContain('Matched place 3: Hopitaux · 4.1 km')
  // a summer missing from the series, with its note; a year never grouped ("2,021")
  expect(titles).toContain('2021: no summer in the series — no clear sky')
  // 0 scenes reads as none at all (no " · 0 scenes"), the note follows
  expect(titles).toContain('2022: +0.200 · 4.0× the threshold — works on the site')
  expect(titles).toContain('2020: +0.120 · 2.4× the threshold · 14 scenes')
  expect(titles).toContain('2023: +0.010 · within noise · 9 scenes')
  expect(html).toContain('aria-label="Porte de Ninove: 3 summers since 2019, beyond the noise in 2. Ring width is the effect against 3 matched places, threshold 0.050."')
  expect(html).not.toMatch(/2,0\d\d|common\.charts/)
})

// the rings in another language: the provider's locale and catalogue, as the nl and fr pages render them
const wrapIn = (loc: 'nl' | 'fr', el: ReactElement) =>
  renderToStaticMarkup(createElement(NextIntlClientProvider, { locale: loc, timeZone: 'Europe/Brussels', messages: loc === 'nl' ? nl : fr, children: el }))
const ringCase = (controls: { id: string; name: string; dist_km?: number }[], seasons = [{ season: 2020, effect: 0.12, scenes: 14 }, { season: 2022, effect: 0.2, scenes: 3 }]) =>
  ({ completed: 2019, series: { threshold: 0.05, seasons }, controls })

test('a matched place’s distance reads in the page’s notation: «4,5 km» and «2,0 km» in French and Dutch (I1)', () => {
  const c = ringCase([{ id: 'a', name: 'GARE', dist_km: 4.5 }, { id: 'b', name: 'PARC', dist_km: 2 }])
  for (const loc of ['fr', 'nl'] as const) {
    const titles = [...plain(wrapIn(loc, createElement(Rings, { c, place: 'X', animate: false }))).matchAll(/<title>([^<]*)<\/title>/g)].map((m) => m[1]!)
    const dots = titles.filter((t) => /km$/.test(t))
    expect(dots, loc).toHaveLength(2)
    expect(dots[0], loc).toMatch(/ · 4,5 km$/)
    expect(dots[1], loc).toMatch(/ · 2,0 km$/)
    expect(titles.join(' '), loc).not.toMatch(/\d\.\d/)
  }
  const titles = plain(wrap(createElement(Rings, { c, place: 'X', animate: false })))
  expect(titles).toContain('Matched place 1: Gare · 4.5 km')
  expect(titles).toContain('Matched place 2: Parc · 2.0 km')
})

test('the rings’ name counts its summers: one summer reads singular in every language; English plural unchanged (M4)', () => {
  const one = ringCase([{ id: 'a', name: 'GARE', dist_km: 1 }], [{ season: 2020, effect: 0.12, scenes: 14 }])
  const two = ringCase([{ id: 'a', name: 'GARE', dist_km: 1 }])
  const aria = (html: string) => /aria-label="([^"]*)"/.exec(plain(html))![1]!
  expect(aria(wrap(createElement(Rings, { c: one, place: 'X', animate: false })))).toBe('X: 1 summer since 2019, beyond the noise in 1. Ring width is the effect against 1 matched places, threshold 0.050.')
  expect(aria(wrap(createElement(Rings, { c: two, place: 'X', animate: false })))).toBe('X: 2 summers since 2019, beyond the noise in 2. Ring width is the effect against 1 matched places, threshold 0.050.')
  expect(aria(wrapIn('nl', createElement(Rings, { c: one, place: 'X', animate: false })))).toContain('boven de ruis in 1 van 1 zomer.')
  expect(aria(wrapIn('nl', createElement(Rings, { c: two, place: 'X', animate: false })))).toContain('boven de ruis in 2 van 2 zomers.')
  expect(aria(wrapIn('fr', createElement(Rings, { c: one, place: 'X', animate: false })))).toContain('au-delà du bruit pendant 1 sur 1 été.')
  expect(aria(wrapIn('fr', createElement(Rings, { c: two, place: 'X', animate: false })))).toContain('au-delà du bruit pendant 2 des 2 étés.')
})
