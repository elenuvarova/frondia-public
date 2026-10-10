import { createTranslator } from 'next-intl'
import { expect, test } from 'vitest'
import { indexable, REGISTER_FILES, registerQuery, resolveRegister } from '@/lib/register'
import { counts, kindOf, readView, refOf, shownOf, viewQuery } from '@/lib/register-view'
import en from '@/messages/en.json'

// the register's known answers (plan 3, task 5): what an address shows, and the lines the page puts
// together — checked against the production page 28 Sep 2026

const t = createTranslator({ locale: 'en', messages: en, namespace: 'register', onError: (e) => { throw e } })

test('an address picks a view, the old router’s way — never an error', async () => {
  expect(readView({})).toEqual({ show: 'all', checked: false })
  for (const show of ['yes', 'weak', 'no', 'blank'] as const) expect(readView({ show }).show).toBe(show)
  // anything else shows all: garbage, case, empty, the value "all" itself
  for (const odd of ['мусор', 'YES', '', 'all', '<x>', 'described']) expect(readView({ show: odd }).show, odd).toBe('all')
  // URLSearchParams.get: a repeated parameter reads its first value
  expect(readView({ show: ['no', 'yes'] }).show).toBe('no')
  expect(readView({ show: ['junk', 'yes'] }).show).toBe('all')
  expect(readView({ checked: '1' }).checked).toBe(true)
  for (const odd of ['true', '0', '', 'yes', '01']) expect(readView({ checked: odd }).checked, odd).toBe(false)
  expect(readView({ checked: ['1', '0'] }).checked).toBe(true)

  const r = await resolveRegister({ show: 'мусор', checked: ['1'] }, 'en')
  expect(r.state).toBe('ok')
  expect(r.show).toBe('all')
  expect(r.checked).toBe(true)
  expect(indexable(r)).toBe(true)
  // every view is known by the bare page
  expect(registerQuery()).toBe('')
})

test('a page in French reads its own register texts; ids, labels and quotes stay (plan 5, task 13)', async () => {
  const [en, fr] = await Promise.all([resolveRegister({ show: 'yes' }, 'en'), resolveRegister({ show: 'yes' }, 'fr')])
  if (en.state !== 'ok' || fr.state !== 'ok') throw new Error('register unreadable')
  expect(fr.d.contracts.map((c) => [c.id, c.label, c.url])).toEqual(en.d.contracts.map((c) => [c.id, c.label, c.url]))
  const why = fr.d.contracts.find((c) => c.id === 46)?.why
  expect(why).toMatch(/^La clause « aménagement d’un parc »/)
  expect(why).not.toBe(en.d.contracts.find((c) => c.id === 46)?.why)
  // the preview fallback to the English file (no file for the language) is tested in data.test.ts
})

test('a view writes its address as the old page did', () => {
  expect(viewQuery('all', false)).toBe('')
  expect(viewQuery('yes', false)).toBe('?show=yes')
  expect(viewQuery('all', true)).toBe('?checked=1')
  expect(viewQuery('blank', true)).toBe('?show=blank&checked=1')
})

test('the counts and rows of each view', async () => {
  const r = await resolveRegister({}, 'en')
  if (r.state !== 'ok') throw new Error('register.json unreadable')
  const cs = r.d.contracts
  expect(cs).toHaveLength(98)
  expect(counts(cs, false)).toEqual({ all: 98, yes: 33, weak: 7, no: 17, blank: 41 })
  expect(counts(cs, true)).toEqual({ all: 30, yes: 20, weak: 2, no: 8, blank: 0 })
  expect(shownOf(cs, 'blank', true)).toHaveLength(0)
  expect(shownOf(cs, 'yes', true).every((c) => c.test && kindOf(c) === 'yes')).toBe(true)
  expect(shownOf(cs, 'all', false)).toHaveLength(98)
  expect(kindOf({ described: false, label: 'no' })).toBe('blank')
  expect(refOf(r.d)).toBe('model')
  expect(refOf(null)).toBe('person')
})

test('known lines', () => {
  expect(t('meta.title')).toBe('Register · Frondia')
  expect(t('lede', { all: t('readAll', { total: '98' }), check: t('ref.model.lede', { n: '30', k: '1' }) })).toBe(
    'Brussels has run 98 neighbourhood contracts since 1994. A language model read each contract’s page and listed every greening measure in the contract’s own words. Read again by another model that never saw its answers, the two readings differ on 1 of 30 contracts.')
  expect(t('list.count', { count: 1, n: '1' })).toBe('1 contract')
  expect(t('list.count', { count: 0, n: '0' })).toBe('0 contracts')
  expect(t('ref.model.differ', { g: 'weak' })).toBe('Second reading: an aim')
  expect(t('ref.person.differ', { g: 'no' })).toBe('Checked by hand: no measure')
  expect(t('check.interval', { pct: '3%', range: t('range', { lo: '1', hi: '17' }) })).toBe('3% · 95% interval 1–17%')
  expect(t('ref.person.colophon', { n: '30', by: 'X', dates: t('dates', { from: '2026-09-26', to: '2026-09-28' }) }))
    .toBe('30 contracts, labelled by X (2026-09-26 to 2026-09-28); the rule baseline read the same pages.')
  // the person's check has no second reason and no extra limit
  expect('refWhy' in en.register.ref.person).toBe(false)
  expect('limit' in en.register.ref.person).toBe(false)
})

test('the two files save under the name every layer on /data gets, the file’s own after frondia-brussels- (re-check 3)', () => {
  expect(REGISTER_FILES.map((f) => f.name)).toEqual(['frondia-brussels-register.csv', 'frondia-brussels-register_check.json'])
  // and that is the name the colophon gives the file
  expect(en.register.colophon.files.v).toContain('register_check.json')
})

