import { parse, TYPE, type MessageFormatElement } from '@formatjs/icu-messageformat-parser'
import { expect, test } from 'vitest'
import en from '@/messages/en.json'
import { ID, mergeFallback, pseudo, pseudoCatalogue } from '@/lib/pseudo'

// the ICU shape of a message: its arguments, plural/select keywords with their options (the printer sorts them), and
// tags, in order
const argsOf = (m: string): string[] => {
  const out: string[] = []
  const walk = (els: MessageFormatElement[]) => {
    for (const e of els) {
      if (e.type === TYPE.argument || e.type === TYPE.number) out.push(`${e.type}:${e.value}`)
      if (e.type === TYPE.pound) out.push('#')
      if (e.type === TYPE.plural || e.type === TYPE.select) { out.push(`${e.type}:${e.value}:${Object.keys(e.options).sort().join('|')}`); for (const o of Object.values(e.options)) walk(o.value) }
      if (e.type === TYPE.tag) { out.push(`tag:${e.value}`); walk(e.children) }
    }
  }
  walk(parse(m, { ignoreTag: false }))
  return out
}
// the literal text of a message (every literal, in options and tags too) — never its ICU syntax
const literals = (m: string): string => {
  const walk = (els: MessageFormatElement[]): string => els.map((e) =>
    e.type === TYPE.literal ? e.value : e.type === TYPE.tag ? walk(e.children)
      : e.type === TYPE.plural || e.type === TYPE.select ? Object.values(e.options).map((o) => walk(o.value)).join(' ') : '').join('')
  return walk(parse(m, { ignoreTag: false }))
}
// the text a reader sees: the literals, a tag's children, the longest option of a plural or select
const visibleLength = (m: string): number => {
  const walk = (els: MessageFormatElement[]): number => els.reduce((n, e) => n + (
    e.type === TYPE.literal ? e.value.length : e.type === TYPE.tag ? walk(e.children)
      : e.type === TYPE.plural || e.type === TYPE.select ? Math.max(...Object.values(e.options).map((o) => walk(o.value))) : 0), 0)
  return walk(parse(m, { ignoreTag: false }))
}

test('a pseudo message keeps its arguments, options and tags, accents every letter and is a third longer', () => {
  const m = 'A wasteland by the canal became a <em>meadow park</em> in {n, plural, one {# year} other {# years}}, {city}.'
  const p = pseudo(m)
  expect(argsOf(p)).toEqual(argsOf(m))
  expect(p).toContain('{city}')
  expect(p).toMatch(/\{n, ?plural, ?one ?\{# ýéåŕ\} ?other ?\{# ýéåŕš\}\}/)    // ICU keywords stay English
  expect(literals(p)).not.toMatch(/[a-zA-Z]/)                         // every letter of the text is accented
  expect(visibleLength(p)).toBeGreaterThanOrEqual(Math.ceil(visibleLength(m) * 1.35))
  expect(pseudo('')).toBe('')
  expect(pseudo('Search')).toBe('Šéåŕçħ ẍẍẍ')
  expect(pseudo('{n, plural, one {# sector} other {# sectors}}')).toMatch(/^\{n, ?plural, ?.*\} ẍẍẍ$/)
})

test('the padding never leaves a word of one or two letters', () => {
  for (let n = 1; n <= 60; n++) {
    const p = pseudo('a'.repeat(n))
    for (const w of p.split(' ').slice(1)) expect(w.length, `${n}: ${p}`).toBeGreaterThanOrEqual(Math.min(3, Math.ceil(0.35 * n)))
  }
})

test('the whole English catalogue survives the pseudo pass with the same ICU shape, and ids stay English', () => {
  const xx = pseudoCatalogue(en as never) as typeof en
  const leaves = (o: unknown, p = ''): [string, unknown][] => o && typeof o === 'object'
    ? Object.entries(o).flatMap(([k, v]) => leaves(v, p ? `${p}.${k}` : k)) : [[p, o]]
  const a = new Map(leaves(en)), b = new Map(leaves(xx))
  expect([...b.keys()]).toEqual([...a.keys()])
  let ids = 0
  for (const [k, v] of a) {
    if (typeof v !== 'string') { expect(b.get(k), k).toBe(v); continue }
    const x = b.get(k) as string
    if (ID.test(k)) { ids++; expect(x, k).toBe(v); continue }
    expect(argsOf(x), k).toEqual(argsOf(v))
    expect(literals(x), k).not.toMatch(/[a-zA-Z]/)
    expect(visibleLength(x), k).toBeGreaterThanOrEqual(Math.ceil(visibleLength(v) * 1.35))
  }
  expect(ids).toBeGreaterThan(20)
  // the ids the code compares: a register filter, a register reader, a FAQ entry, a landing section
  expect(xx.register.list.filters.map((f) => f.k)).toEqual(['all', 'yes', 'weak', 'no', 'blank'])
  expect(xx.register.check.readers.map((r) => r.who)).toEqual(['model', 'rule'])
  expect(xx.landing.faq[0]?.id).toBe('scope')
  expect(xx.landing.audiences[0]?.key).toBe('regions')
  expect(xx.landing.audiences[0]?.who).not.toBe(en.landing.audiences[0]?.who)   // a word beside an id is still a word
})

test('a preview language falls back to English key by key', () => {
  expect(mergeFallback({ a: { b: 'B', c: 'C' }, d: ['x'] }, { a: { b: 'b' } })).toEqual({ a: { b: 'b', c: 'C' }, d: ['x'] })
  // a value of the wrong shape never replaces English's: a page that maps a list never meets a string
  expect(mergeFallback({ l: ['x', 'y'], o: { p: 'P' } }, { l: 'x', o: 'o' })).toEqual({ l: ['x', 'y'], o: { p: 'P' } })
})

test('the fallback reads own keys only, never a prototype, and a null translation is missing', () => {
  const evil = JSON.parse('{"__proto__":{"x":1},"a":"own a"}') as Record<string, unknown>
  const out = mergeFallback({ a: 'A', toString: 'English toString', constructor: 'C' }, evil)
  expect(out.a).toBe('own a')
  expect(Object.hasOwn(out, 'toString')).toBe(true)
  expect(out.toString).toBe('English toString')         // English's own key, not Object.prototype.toString from `own`
  expect(Object.hasOwn(out, '__proto__')).toBe(false)
  expect(({} as Record<string, unknown>).x).toBeUndefined()
  expect((out as Record<string, unknown>).x).toBeUndefined()
  expect(mergeFallback({ toString: 'T' }, {})).toEqual({ toString: 'T' })
  expect(mergeFallback({ a: 'A', o: { p: 'P' } }, { a: null, o: null })).toEqual({ a: 'A', o: { p: 'P' } })
  // a base that carries __proto__ as its own key never sets the merged object's prototype
  const base = JSON.parse('{"__proto__":{"polluted":true},"k":"K"}') as Record<string, unknown>
  const merged = mergeFallback(base, {})
  expect(Object.getPrototypeOf(merged)).toBe(Object.prototype)
  expect((merged as Record<string, unknown>).polluted).toBeUndefined()
})
