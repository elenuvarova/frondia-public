import { expect, test } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { editionCompare } from '@/lib/editions'
import { proofReady } from '@/lib/proof'
import type { City, Facts, Proof } from '@/lib/types'

const facts = JSON.parse(readFileSync(path.join(__dirname, '../public/data/facts.json'), 'utf8')) as Facts

test('the proof band compares the same Flemish sectors on both sides, from the data (re-check 1)', () => {
  const c = editionCompare(facts)
  expect(c).not.toBeNull()
  // measured answers (9 Oct 2026): the official map over the sectors the aerial map covers, against the aerial map
  expect(c!.cities).toBe(5)
  expect(c!.flemish.antwerp.official).toBeCloseTo(3.6, 1)
  expect(c!.flemish.ghent.official).toBeCloseTo(3.6, 1)
  expect(c!.flemish.antwerp.aerial).toBeCloseTo(1.3, 1)
  expect(c!.flemish.ghent.aerial).toBeCloseTo(0.2, 1)
  expect(c!.officialMin).toBeCloseTo(3.6, 1)
  expect(c!.officialMax).toBeCloseTo(9.1, 1)
  for (const k of ['antwerp', 'ghent'] as const) expect(c!.flemish[k].official).toBeGreaterThan(2 * c!.flemish[k].aerial)
})

test('without editions there is no comparison (the proof band is left out)', () => {
  expect(editionCompare({ ...(facts), editions: undefined })).toBeNull()
})

test('the proof band stands on the real data: its photos are of the data’s sectors, its years are the numbers’ keys (re-check 3)', () => {
  const read = (f: string) => JSON.parse(readFileSync(path.join(__dirname, '../public', f), 'utf8'))
  const proof = read('proof/proof.json') as Proof
  const ant = read('data/antwerp.json') as City, bxl = read('data/brussels.json') as City
  const p = proofReady(facts, proof, ant, bxl)
  expect(p).not.toBeNull()
  // measured answers (9 Oct 2026): Park in Merksem, 8 → 62 % on the map, 41 → 47 % on the photographs; Germinal II
  expect(p!.sa.c).toBe('Merksem')
  expect(p!.ex.official_2018 * 100).toBeCloseTo(8, 0)
  expect(p!.ex.official_2021 * 100).toBeCloseTo(62, 0)
  expect(p!.bx.name).toMatch(/GERMINAL/i)
  // a photo of another sector leaves the band out
  expect(proofReady(facts, { ...proof, region: { ...proof.region, sector: 'x' } }, ant, bxl)).toBeNull()
  expect(proofReady(facts, null, ant, bxl)).toBeNull()
})
