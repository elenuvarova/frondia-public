import { expect, test } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { LACK, MIN_RESIDENTS, needFill } from '@/lib/lenses'
import type { City } from '@/lib/types'

const bxl = JSON.parse(readFileSync(path.join(__dirname, '../public/data/brussels.json'), 'utf8')) as City

test('an empty sector is not shaded; a lived-in one takes a step of the lack ramp', () => {
  expect(needFill({ id: 'x', n: '', c: '', d: '', pop: MIN_RESIDENTS - 1 }, 'services', { scenario: 'family' })).toBe('var(--noise)')
  const lived = bxl.sectors.find((s) => (s.pop ?? 0) > 1000)!
  const f = needFill(lived, 'services', { scenario: 'family' })
  expect(f === null || LACK.includes(f)).toBe(true)
})
