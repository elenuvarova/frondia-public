import { expect, test } from 'vitest'
import { dec, fixed, int, longDate, NNBSP, pct, shortWindow, signed, times, titleCase } from '@/lib/format'

test('English matches the Vite site to the character', () => {
  expect(signed(0.2501, 3, 'en')).toBe('+0.250')
  expect(signed(-0.0373, 4, 'en')).toBe('−0.0373')
  expect(signed(-0.00004, 4, 'en')).toBe('0.0000')
  expect(signed(null, 3, 'en')).toBe('—')
  expect(fixed(-0.035, 3, 'en')).toBe('−0.035')
  expect(fixed(-0.0004, 3, 'en')).toBe('0.000')
  expect(int(1246136, 'en')).toBe('1,246,136')
  expect(pct(0.393, 1, 'en')).toBe('39.3%')
  expect(pct(0.39, 0, 'en')).toBe('39%')
  expect(times(0.147, 0.0373, 1, 'en')).toBe('3.9×')
})

test('Dutch: decimal comma, dot thousands, % closed up', () => {
  expect(fixed(0.035, 3, 'nl')).toBe('0,035')
  expect(signed(-0.0373, 4, 'nl')).toBe('−0,0373')
  expect(int(1246136, 'nl')).toBe('1.246.136')
  expect(pct(0.393, 1, 'nl')).toBe('39,3%')
  expect(times(0.147, 0.0373, 1, 'nl')).toBe('3,9×')
})

test('French: decimal comma, narrow no-break space in thousands and before %', () => {
  expect(fixed(0.035, 3, 'fr')).toBe('0,035')
  expect(int(1246136, 'fr')).toBe('1 246 136')
  expect(pct(0.393, 1, 'fr')).toBe('39,3 %')
  expect(signed(0.25, 3, 'fr')).toBe('+0,250')
})

test('names and windows keep their old behaviour', () => {
  expect(titleCase("RUE DE WAND")).toBe('Rue de Wand')
  expect(titleCase("'T MESTPUTTEKE")).toBe("'t Mestputteke")
  // re-check 3: a Roman numeral stays upright, a French elision inside a name stays low
  expect(titleCase('RUE JOSEPH II')).toBe('Rue Joseph II')
  expect(titleCase('QUARTIER DU XII')).toBe('Quartier du XII')
  expect(titleCase('FORT IV')).toBe('Fort IV')
  expect(titleCase('MESSIDOR I')).toBe('Messidor I')
  expect(titleCase("CHANTS D'OISEAUX")).toBe("Chants d'Oiseaux")
  expect(titleCase("CITE DE L'EUROPE")).toBe("Cite de l'Europe")
  expect(titleCase("ANVERS (CHAUSSEE D')-NORD")).toBe("Anvers (Chaussee d')-Nord")
  expect(titleCase("L'ECLUSE")).toBe("L'Ecluse")
  expect(titleCase('ALBERT I- QUARTIER')).toBe('Albert I- Quartier')
  expect(titleCase('VIVIER D OIE')).toBe('Vivier D Oie')
  expect(shortWindow('2017–2019 → 2021–2024')).toBe('2017–19 → 2021–24')
})

test('dec: a quantity with the decimals it has, grouped, with the house signs', () => {
  // the dossier's rules, as the old page printed them (Intl's default: up to 3 decimals)
  expect(dec(1, 'en')).toBe('1')
  expect(dec(1500 / 1000, 'en')).toBe('1.5')
  expect(dec(0.04, 'en')).toBe('0.04')
  expect(dec(1234.5, 'en')).toBe('1,234.5')
  expect(dec(0.12345, 'en')).toBe('0.123')
  expect(dec(0.12345, 'en', 1)).toBe('0.1')
  expect(dec(-0.04, 'en')).toBe('−0.04')
  expect(dec(-0.0001, 'en')).toBe('0')
  expect(dec(null, 'en')).toBe('—')
  expect(dec(1.5, 'fr')).toBe('1,5')
  expect(dec(1234.5, 'fr')).toBe(`1${NNBSP}234,5`)
  expect(dec(-0.04, 'fr')).toBe('−0,04')
  expect(dec(1234.5, 'nl')).toBe('1.234,5')
})

test('longDate: the day in words, on Brussels’s calendar', () => {
  expect(longDate('2026-09-05', 'en')).toBe('5 September 2026')
  expect(longDate('2026-09-05', 'fr')).toBe('5 septembre 2026')
  expect(longDate('2026-09-05', 'nl')).toBe('5 september 2026')
  // late evening UTC is already the next day in Brussels
  expect(longDate('2026-09-04T23:30:00Z', 'en')).toBe('5 September 2026')
})
