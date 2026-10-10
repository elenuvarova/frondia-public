// lib/icu.ts — what a value put into a message may be (plan 5, L8). A message's plain argument shows its value as it
// stands, so a number there would be ICU's to format: "since {year}" with 2017 reads "since 2,017", and a count of
// sectors would be grouped by ICU's rules, not lib/format's. So t() takes strings, formatted by lib/format in the page's
// language (or String(n) for a year, a code, a raw count), and a number goes in only through count(), only where the
// message counts it: a plural or selectordinal argument ({n, plural, one {# sector} other {# sectors}}).
//
// The check runs outside production (lib/t.ts, lib/t-client.ts). The messages are read with next-intl's own parser
// (intl-messageformat's, the copy use-intl formats every message with), so the check adds no second parser to a bundle.
import type { MessageFormatElement } from '@formatjs/icu-messageformat-parser'
import { IntlMessageFormat } from 'intl-messageformat'
import type { ReactNode } from 'react'

export type Count = number & { readonly __count: unique symbol }
// a number a plural argument counts: the only number t() takes
export const count = (n: number): Count => n as Count

export type TValues = Record<string, string | Count>
export type RichValues = Record<string, string | Count | ((chunks: ReactNode) => ReactNode)>

// the parser's element types (TYPE in @formatjs/icu-messageformat-parser): select, plural (cardinal and ordinal), tag
const SELECT = 5, PLURAL = 6, TAG = 8

const cache = new Map<string, Set<string>>()

// the names of the arguments a message counts — plural or selectordinal, however deep in a select, a plural or a tag
export function countArgs(message: string): Set<string> {
  const hit = cache.get(message)
  if (hit) return hit
  const out = new Set<string>()
  const walk = (els: MessageFormatElement[]) => {
    for (const el of els) {
      if (el.type === PLURAL) out.add(el.value)
      if (el.type === SELECT || el.type === PLURAL) for (const o of Object.values(el.options)) walk(o.value)
      else if (el.type === TAG) walk(el.children)
    }
  }
  walk(new IntlMessageFormat(message, 'en', undefined, { ignoreTag: false }).getAst())
  cache.set(message, out)
  return out
}

// a number put anywhere but into a counted argument: thrown, so the test or the dev page that rendered it fails
export function checkCounts(key: string, message: string, values: Record<string, unknown> | undefined): void {
  if (!values) return
  for (const [name, v] of Object.entries(values)) {
    if (typeof v === 'number' && !countArgs(message).has(name)) throw new Error(`${key}: {${name}} is not a plural; pass a string`)
  }
}
