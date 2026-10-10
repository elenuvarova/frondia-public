import { expect, test } from 'vitest'
import { checkCounts, count, countArgs } from '@/lib/icu'

test('plural arguments are found, nested too', () => {
  expect([...countArgs('{n, plural, one {# sector} other {# sectors}} in {city}')]).toEqual(['n'])
  expect([...countArgs('{a, select, yes {{k, plural, one {#} other {#}}} other {}}')]).toEqual(['k'])
})

test('a number goes only where a plural counts it: a year in a plain argument would read "2,017"', () => {
  expect(() => checkCounts('k', 'since {year}', { year: 2017 as never })).toThrow(/year/)
  expect(() => checkCounts('k', 'since {year}', { year: '2017' })).not.toThrow()
  expect(() => checkCounts('k', '{n, plural, one {#} other {#}}', { n: count(3) })).not.toThrow()
})

test('selectordinal and tags: an ordinal counts its argument, and a plural inside a tag is still found (Task 4)', () => {
  const ordinal = '{n, selectordinal, one {#st} two {#nd} few {#rd} other {#th}} summer'
  expect([...countArgs(ordinal)]).toEqual(['n'])
  expect(() => checkCounts('k', ordinal, { n: count(2) })).not.toThrow()
  const tagged = '<b>{n, plural, one {# sector} other {# sectors}}</b> since <i>{year}</i>'
  expect([...countArgs(tagged)]).toEqual(['n'])
  expect(() => checkCounts('k', tagged, { n: count(2), year: '2017' })).not.toThrow()
  // a number in a tag's plain argument is still a number ICU would group
  expect(() => checkCounts('k', tagged, { n: count(2), year: 2017 as never })).toThrow(/year/)
  // nested: an ordinal inside a select inside a tag
  expect([...countArgs('<a>{s, select, yes {{r, selectordinal, other {#th}}} other {}}</a>')]).toEqual(['r'])
})
