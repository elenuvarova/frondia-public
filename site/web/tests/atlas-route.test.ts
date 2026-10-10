import { expect, test } from 'vitest'
import { FIELD_MEDIA, fieldPreload, resolveAtlas } from '@/lib/atlas/resolve'
import { parseAtlas } from '@/lib/atlas/state'

test('the server resolves the view, the first measured lens and only a sector or audit that exist', async () => {
  const a = await resolveAtlas({ city: 'brussels', sector: '21004E72-' })
  expect(a.ok).toBe(true)
  expect(a.sector?.id).toBe('21004E72-')
  expect(a.fieldSrc).toBe('/field/brussels-context-2024-light.jpg')
  expect((await resolveAtlas({ city: 'antwerp', sector: '21004E72-' })).sector).toBeNull()   // a Brussels sector in Antwerp
  expect((await resolveAtlas({ city: 'brussels', case: 'droogdokkenpark' })).caseSlug).toBeNull()
  expect((await resolveAtlas({ city: 'antwerp', case: 'droogdokkenpark' })).caseSlug).toBe('droogdokkenpark')
  expect((await resolveAtlas({ q: 'need' })).lens).toBe('services')   // Brussels measures services first
})

test('the state the client starts from is the head’s: an audit of this city opens on “what changed”, another is dropped (Q15)', async () => {
  const a = await resolveAtlas({ case: 'ninove', q: 'need', lens: 'heat' })
  expect(a.state.q).toBe('change')
  expect(a.state.caseSlug).toBe('ninove')
  expect(a.state.lens).toBe('heat')   // the chosen need lens stays for when the question changes back
  const b = await resolveAtlas({ city: 'brussels', case: 'droogdokkenpark' })
  expect(b.state.caseSlug).toBeNull()
  expect(b.state.q).toBe('change')
  const c = await resolveAtlas({ city: 'brussels', case: 'junk', q: 'need' })
  expect(c.state.caseSlug).toBeNull()
  expect(c.state.q).toBe('need')      // an unknown audit takes nothing with it
  const d = await resolveAtlas({ city: 'antwerp', case: 'droogdokkenpark', view: 'communes' })
  expect(d.state).toMatchObject({ q: 'change', caseSlug: 'droogdokkenpark', view: 'communes' })
})

test('the field photo is preloaded only where the view shows it, and only for wide screens (Q14)', () => {
  const src = '/field/brussels-context-2024-light.jpg'
  const st = (q: string) => parseAtlas(new URLSearchParams(q))
  expect(FIELD_MEDIA).toBe('(min-width: 861px)')
  expect(fieldPreload(st('city=brussels'), src)).toEqual({ href: src, media: '(min-width: 861px)' })
  expect(fieldPreload(st('city=brussels&view=field'), src)).toEqual({ href: src, media: '(min-width: 861px)' })
  expect(fieldPreload(st('city=brussels&q=place'), src)).toEqual({ href: src, media: '(min-width: 861px)' })
  expect(fieldPreload(st('city=brussels&q=need&lens=heat'), src)).toBeNull()
  expect(fieldPreload(st('city=brussels&view=communes'), src)).toBeNull()
  expect(fieldPreload(st('city=brussels&view=photos'), src)).toBeNull()
  expect(fieldPreload(st('city=brussels'), null)).toBeNull()     // a city with no field photo
})
