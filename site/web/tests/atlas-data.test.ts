import { expect, test } from 'vitest'
import en from '@/messages/en.json'
import { CITIES } from '@/lib/cities'
import { getCity, getPoints } from '@/lib/data'
import type { AtlasCity, AtlasPoints } from '@/lib/atlas/types'

// what the atlas reads, present in every city's file: a city without a block the atlas draws is a pipeline bug,
// not something the page should paper over. The data's own name equals the catalogue's (the atlas titles use the catalogue)
test.each(CITIES)('%s carries every block the atlas draws', async (key) => {
  const c = (await getCity(key)) as AtlasCity
  expect(c.name).toBe((en.common.cities as Record<string, string>)[key])
  expect(c.sectors.length).toBeGreaterThan(100)
  expect(typeof c.field.src).toBe('string')
  expect(c.photos?.src).toHaveLength(2)
  expect(c.built?.threshold).toBeGreaterThan(0)
  expect(c.balance?.seasons[c.balance.latest]).toBeTruthy()
  expect(c.equity.income_cuts).toHaveLength(2)
  expect(Array.isArray(c.communes.list) && Array.isArray(c.registered) && Array.isArray(c.cases)).toBe(true)
  const p = (await getPoints(key)) as AtlasPoints
  expect(p.types.length).toBe(14)
  expect(p.points.some((x) => x.role === 'named')).toBe(true)
})
