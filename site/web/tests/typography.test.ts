import { expect, test } from 'vitest'
import { plain, spokenPoints, tie, tieRich } from '@/lib/typography'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

const show = (s: string) => s.replace(/ /g, '⍽').replace(/ /g, '˽').replace(/⁠/g, '‸')

test('English: short words, numbers, dashes, arrows, dots, ranges, equals', () => {
  expect(show(tie('It is a park of the city'))).toBe('It⍽is⍽a⍽park of⍽the⍽city')
  expect(show(tie('measured on 724 sectors'))).toBe('measured on⍽724⍽sectors')
  expect(show(tie('greener — a little'))).toBe('greener⍽— a⍽little')
  expect(show(tie('old docks → a quayside park'))).toBe('old docks⍽→ a⍽quayside park')
  expect(show(tie('2020–2026 · opened 2019'))).toBe('2020–‸2026⍽· opened 2019')
  expect(show(tie('the 3-30-300 rule'))).toBe('the⍽3-‸30-‸300⍽rule')
  expect(show(tie('r = −0.89 here'))).toBe('r⍽=⍽−0.89⍽here')
})

test('Dutch: its own short words', () => {
  expect(show(tie('de kroon van het park is een feit', 'nl'))).toBe('de⍽kroon van⍽het⍽park is⍽een⍽feit')
})

test('French: short words, space before ; ! ? and inside guillemets', () => {
  expect(show(tie('les parcs de la ville', 'fr'))).toBe('les⍽parcs de⍽la⍽ville')
  expect(show(tie('Pourquoi ? Voilà !', 'fr'))).toBe('Pourquoi˽? Voilà˽!')
  expect(show(tie('un seuil : 0,035', 'fr'))).toBe('un⍽seuil⍽: 0,035')
  expect(show(tie('« le bruit »', 'fr'))).toBe('«⍽le⍽bruit⍽»')
})

test('rich text: a short word before <em> keeps its partner', () => {
  const out = tieRich(['A wasteland became a ', createElement('em', { key: 1 }, 'meadow park'), '.'], 'en') as unknown[]
  expect(show(out[0] as string)).toBe('A⍽wasteland became a⍽')
})

test('a number sign keeps its number: n°, nr., no.', () => {
  expect(show(tie('voir le n° 3', 'fr'))).toBe('voir le⍽n°⍽3')
  expect(show(tie('zie nr. 3', 'nl'))).toBe('zie nr.⍽3')
  expect(show(tie('see no. 3', 'en'))).toBe('see no.⍽3')
})

test('French: a number keeps its % and the % keeps the word after it', () => {
  // the catalogue writes "45 %" with a plain space; pct() already gives a narrow no-break space
  expect(tie('45 % des secteurs', 'fr')).toBe('45 % des secteurs')
  expect(tie('40 % des secteurs', 'fr')).toBe('40 % des secteurs')
})

test('rich text: an arrow nested deeper in the next element still holds the space', () => {
  const out = tieRich(['see ', createElement('a', { key: 'a' }, createElement('span', null, '→ atlas'))], 'en') as unknown[]
  expect(out[0] as string).toBe('see ')
})

test('rich text: empty, null and false children before the arrow are skipped', () => {
  const out = tieRich(['see ', '', createElement('a', { key: 'a' }, null, false, '', createElement('span', null, '→ atlas'))], 'en') as unknown[]
  expect(out[0] as string).toBe('see ')
})

test('French «pt» is read as its full phrase; English and Dutch come back as given', () => {
  const fr = tie('1,2 pt au-dessus de la région', 'fr')
  expect(show(renderToStaticMarkup(createElement('p', null, spokenPoints(fr, 'fr', (n) => (n < 2 ? 'point de pourcentage' : 'points de pourcentage'))))))
    .toBe('<p>1,2⍽<span aria-hidden="true">pt</span><span class="sr-only">point de pourcentage</span> au\u2011dessus de⍽la⍽région</p>')
  expect(spokenPoints('Bruxelles est à 3,4 pt sous le seuil, 2 pt', 'fr', () => 'X')).toHaveLength(7)
  expect(spokenPoints('un point', 'fr', () => 'X')).toBe('un point')
  for (const [s, loc] of [['1.2 points below', 'en'], ['+3 pts', 'en'], ['1,2 procentpunt', 'nl'], ['+3 pt', 'nl']] as const) expect(spokenPoints(s, loc, () => 'X')).toBe(s)
})

test('a spaced plus and a signed number after a word keep to the left, in every language', () => {
  expect(show(tie('LBE-code (BE_ + NIS-code)', 'nl'))).toBe('LBE\u2011code (BE_⍽+ NIS\u2011code)')
  expect(show(tie('boomkruin +16,8 ha', 'nl'))).toBe('boomkruin⍽+16,8⍽ha')
  expect(show(tie('se termine : ±0,035 à Bruxelles', 'fr'))).toBe('se⍽termine⍽: ±0,035⍽à⍽Bruxelles')
  // English too (P5-12): «canopy ⏎ +16.8 ha» stranded the sign at a phone's line start
  expect(show(tie('LAU code (BE_ + NIS code)', 'en'))).toBe('LAU code (BE_⍽+ NIS code)')
  expect(show(tie('canopy +16.8 ha', 'en'))).toBe('canopy⍽+16.8⍽ha')
  expect(show(tie('ends at: −0.6 in Ghent', 'en'))).toBe('ends at: −0.6⍽in⍽Ghent')
})

test('French «pt» agrees with its number: one below 2, plural from 2', () => {
  const said: number[] = []
  const phrase = (n: number) => { said.push(n); return n < 2 ? 'point' : 'points' }
  renderToStaticMarkup(createElement('p', null, spokenPoints(tie('0,6 pt sous ; 1,3 pt ; 11,0 pt ; −2,4 pt ; +3 pt ; 1\u202F234,5 pt', 'fr'), 'fr', phrase)))
  expect(said).toEqual([0.6, 1.3, 11, 2.4, 3, 1234.5])
})

test('Dutch compounds get soft hyphens at their joints; other languages and other words do not', () => {
  const soft = (x: string) => x.replace(/\u00AD/g, '|')
  expect(soft(tie('ten opzichte van 12 vergelijkingsplaatsen', 'nl'))).toContain('ver|ge|lij|kings|plaatsen')
  expect(soft(tie('Boomkroonbedekking in die zones', 'nl'))).toContain('Boom|kroon|bedekking')
  expect(soft(tie('die van Antwerpen', 'nl'))).toContain('Ant|wer|pen')
  expect(soft(tie('vergelijkingsplaatsenregister', 'nl'))).not.toContain('|')
  expect(tie('Antwerpen', 'fr')).toBe('Antwerpen')
  expect(tie('Antwerp', 'en')).toBe('Antwerp')
})

test('no soft hyphen inside a domain, an email or a path; the same word in a sentence still gets them', () => {
  const soft = (x: string) => x.replace(/\u00AD/g, '|')
  // a domain, whole and with its scheme
  expect(soft(tie('Bron: geodata.antwerpen.be, open data', 'nl'))).toContain('geodata.antwerpen.be')
  expect(soft(tie('https://www.vergelijkingsplaatsen.be/kaart', 'nl'))).toBe('https://www.vergelijkingsplaatsen.be/kaart')
  expect(soft(tie('antwerpen.be', 'nl'))).toBe('antwerpen.be')
  // an email
  expect(soft(tie('Mail info@antwerpen.be of bel', 'nl'))).toContain('info@antwerpen.be')
  expect(soft(tie('vergelijkingsplaatsen@stad.be', 'nl'))).toBe('vergelijkingsplaatsen@stad.be')
  // a path
  expect(soft(tie('zie /data/vergelijkingsplaatsen/antwerpen.csv', 'nl'))).toContain('/data/vergelijkingsplaatsen/antwerpen.csv')
  expect(soft(tie('kaart_antwerpen-noord', 'nl'))).toBe('kaart_antwerpen-noord')
  // the word itself, before a sentence's full stop, a comma or in brackets, still breaks at its joints
  expect(soft(tie('Wij meten in Antwerpen.', 'nl'))).toContain('Ant|wer|pen.')
  expect(soft(tie('(Antwerpen), Gent', 'nl'))).toContain('(Ant|wer|pen)')
  expect(soft(tie('12 vergelijkingsplaatsen. Daarna', 'nl'))).toContain('ver|ge|lij|kings|plaatsen.')
})

test('tie() is idempotent, with its soft hyphens and its no-break spaces', () => {
  for (const [s, loc] of [
    ['Bron: geodata.antwerpen.be — 12 vergelijkingsplaatsen in Antwerpen, boomkruin +16,8 ha', 'nl'],
    ['Mail info@antwerpen.be of zie /data/vergelijkingsplaatsen', 'nl'],
    ['canopy +16.8 ha of a park — see no. 3', 'en'],
    ['« 45 % » : le couvert arboré, +1,2 pt', 'fr'],
    ['Au-delà du bruit, c’est-à-dire au-dessus du seuil : peut-être là-bas, vis-à-vis du parc, au-dessous de 3 %', 'fr'],
  ] as const) expect(tie(tie(s, loc), loc)).toBe(tie(s, loc))
})

test('plain() drops the soft hyphens an attribute must not carry and keeps the no-break spaces', () => {
  const tied = tie('Het geritsel: 12 vergelijkingsplaatsen in Antwerpen', 'nl')
  expect(tied).toContain('\u00AD')
  expect(plain(tied)).not.toContain('\u00AD')
  expect(plain(tied).replace(/\u00A0/g, ' ')).toBe('Het geritsel: 12 vergelijkingsplaatsen in Antwerpen')
  expect(plain(tied)).toContain('\u00A0')
})

test('French fixed compounds keep their hyphen unbroken (U+2011); other hyphens, other languages and lookalikes do not', () => {
  const nbh = (t: string) => t.replace(/\u2011/g, '‑̲')
  expect(nbh(tie('3 ha au-delà du bruit', 'fr'))).toContain('au‑̲delà')
  expect(nbh(tie('Au-delà du seuil', 'fr'))).toContain('Au‑̲delà')
  for (const w of ['c’est-à-dire', "c'est-à-dire", 'peut-être', 'vis-à-vis', 'au-dessus', 'au-dessous', 'là-bas']) {
    expect(tie(`il est ${w} ici`, 'fr')).toContain(w.replace(/-/g, '\u2011'))
  }
  // only the listed compounds: a commune name, a sub-score, a pronoun and a code keep their ordinary hyphen
  for (const w of ['Saint-Gilles', 'sous-score', 'elle-même', 'ci-dessus', 'NIS-code', 'beau-delà']) expect(tie(`le ${w} est`, 'fr')).not.toContain('\u2011')
  expect(tie('au-delà', 'en')).toBe('au-delà')
  expect(tie('au-delà', 'nl')).toBe('au-delà')
})

test('Dutch code compounds keep their hyphen unbroken (U+2011); place names, numbers, other languages do not (design wave)', () => {
  for (const w of ['NIS-code', 'IP-adres', 'IP-adressen', 'LBE-code', 'VN-indicator', 'NDVI-eenheden', 'GIS-software', 'LBE-polygoon']) {
    expect(tie(`de ${w} hier`, 'nl')).toContain(w.replace('-', '\u2011'))
  }
  expect(tie('(BE_ + NIS-code)', 'nl')).toContain('NIS\u2011code')
  expect(tie('NIS-code', 'nl')).toBe('NIS\u2011code')
  // a place name, a number's word, a lower-case compound and a code at a word's end keep the ordinary hyphen
  for (const w of ['Sint-Gillis', 'Sint-Joost-ten-Node', '3-30-300-regel', 'zuid-oost', 'NIS-', 'Noord-Brabant', 'A-merk']) {
    expect(tie(`de ${w} hier`, 'nl')).not.toContain('\u2011')
  }
  // English and French are untouched
  expect(tie('the NIS-code', 'en')).not.toContain('\u2011')
  expect(tie('le NIS-code', 'fr')).not.toContain('\u2011')
  // idempotent: tying a tied string changes nothing
  for (const t of ['De NIS-code en het IP-adres van Sint-Gillis', 'Gemeente of NIS-code', 'VN-indicator 11.7.1']) {
    expect(tie(tie(t, 'nl'), 'nl')).toBe(tie(t, 'nl'))
  }
  expect(plain(tie('Gemeente of NIS-code', 'nl')).replace(/\u00A0/g, ' ')).toBe('Gemeente of NIS-code')
})

test('plain() gives an attribute the ordinary hyphen back', () => {
  expect(plain(tie('plus vert au-delà du bruit', 'fr'))).toContain('au-delà')
})
