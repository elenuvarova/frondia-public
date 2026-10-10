// The words of a language under review (plan 5, L2–L3): the key-by-key fallback a preview language reads its missing
// keys from (English), so its pages render while their catalogue fills and the page checks find the English left in
// them (a published language never gets it: its catalogue is complete), and the pseudo-language made from English.
import { parse, TYPE, type MessageFormatElement } from '@formatjs/icu-messageformat-parser'
import { printAST } from '@formatjs/icu-messageformat-parser/printer.js'

export type Tree = Record<string, unknown>

const isTree = (v: unknown): v is Tree => v != null && typeof v === 'object' && !Array.isArray(v)
// keys that would reach an object's prototype: a catalogue never has them, and a merge never copies them
const UNSAFE = new Set(['__proto__', 'constructor', 'prototype'])

// a deep merge: the value of `own` where it has one, the value of `base` elsewhere. An array is a leaf (a list of
// cards or words is translated whole, never item by item), and so is any value of a different shape than base's.
// Only own keys count (a "toString" in English is a key, not Object.prototype's), and a null translation is missing
export function mergeFallback(base: Tree, own: Tree): Tree {
  const out: Tree = {}
  for (const k of Object.keys(base)) {
    if (UNSAFE.has(k)) continue
    const b = base[k]
    const o = Object.hasOwn(own, k) ? own[k] : undefined
    if (o == null) out[k] = b
    else if (isTree(b) && isTree(o)) out[k] = mergeFallback(b, o)
    else if (isTree(b) !== isTree(o) || Array.isArray(b) !== Array.isArray(o)) out[k] = b
    else out[k] = o
  }
  return out
}

// ── The pseudo-language `xx` (plan 5, L3) ──────────────────────────────────────────────────────────────────────────────
// English with every letter accented and a third more text, so a page in it shows at once where a word was left out of
// the catalogue (plain letters) and where a longer language would break the layout (Dutch and French run 20–35 % longer
// than English). Made from en.json on the fly (i18n/request.ts), never stored. The ICU shape stays: arguments, plural
// and select keywords, `#` and tags are kept; the texts of the plural and select options are pseudo too.

// the leaves that are ids the code reads, not words: a FAQ's id, a section's key, a register filter, a register reader.
// One copy, read by tests/pseudo.test.ts and the catalogue test (plan 5, task 9): a translation keeps them as English
export const ID = /(^|\.)(id|key)$|^register\.list\.filters\.\d+\.k$|^register\.check\.readers\.\d+\.who$/

const PLAIN = [...'abcdefghijklmnopqrstuvwxyz'], ACCENTED = [...'åƀçðéƒĝħîĵķłɱñöþǫŕšţûṽŵẋýž']
const ACCENT = new Map(PLAIN.flatMap((c, i) => {
  const a = ACCENTED[i] ?? c
  return [[c, a], [c.toUpperCase(), a.toUpperCase()]] as [string, string][]
}))
const accent = (s: string) => s.replace(/[a-zA-Z]/g, (c) => ACCENT.get(c) ?? c)

// the visible text of a message: its literals, a tag's children, and the longest option of a plural or select
// (one option shows at a time); arguments are values, not text
function visible(els: MessageFormatElement[]): number {
  let n = 0
  for (const e of els) {
    if (e.type === TYPE.literal) n += e.value.length
    else if (e.type === TYPE.tag) n += visible(e.children)
    else if (e.type === TYPE.plural || e.type === TYPE.select) n += Math.max(0, ...Object.values(e.options).map((o) => visible(o.value)))
  }
  return n
}

function accentAll(els: MessageFormatElement[]): MessageFormatElement[] {
  return els.map((e) => {
    if (e.type === TYPE.literal) return { ...e, value: accent(e.value) }
    if (e.type === TYPE.tag) return { ...e, children: accentAll(e.children) }
    if (e.type === TYPE.plural || e.type === TYPE.select) {
      const options = Object.fromEntries(Object.entries(e.options).map(([k, o]) => [k, { ...o, value: accentAll(o.value) }]))
      return { ...e, options } as MessageFormatElement
    }
    return e
  })
}

// n more characters as words of six «ẍ» (a last word under three letters joins the one before it, so the padding
// never ends a line on a short word of its own), each word after a space
function padding(n: number): string {
  if (n <= 0) return ''
  const words: number[] = []
  for (let left = n; left > 0; left -= 6) words.push(Math.min(6, left))
  const last = words[words.length - 1] ?? 0
  if (words.length > 1 && last < 3) { words.pop(); words[words.length - 1] = (words[words.length - 1] ?? 0) + last }
  return words.map((k) => ' ' + 'ẍ'.repeat(k)).join('')
}

// A `<` stays literal text unless an ASCII letter or `/` follows it: the parser's (and the printer's) tag check is
// ASCII-only, so an accented `<ţåĝ>` would never become a tag. Accenting happens after parsing, on literals only, so a
// real tag in English keeps its name, and a literal `<` before a non-ASCII letter is printed back as it was
export function pseudo(message: string): string {
  const ast = parse(message, { ignoreTag: false })
  const extra = padding(Math.ceil(0.35 * visible(ast)))
  const out = accentAll(ast)
  if (extra) {
    const last = out[out.length - 1]
    if (last?.type === TYPE.literal) out[out.length - 1] = { ...last, value: last.value + extra }
    else out.push({ type: TYPE.literal, value: extra })
  }
  return printAST(out)
}

// the whole catalogue: every string leaf but the ids (ID) goes through pseudo(); arrays and objects keep their shape,
// a null stays null (a legend's empty step)
export function pseudoCatalogue(tree: Tree): Tree {
  const walk = (v: unknown, path: string): unknown => {
    if (typeof v === 'string') return ID.test(path) ? v : pseudo(v)
    if (Array.isArray(v)) return v.map((x, i) => walk(x, `${path}.${i}`))
    if (isTree(v)) return Object.fromEntries(Object.keys(v).filter((k) => !UNSAFE.has(k)).map((k) => [k, walk(v[k], path ? `${path}.${k}` : k)]))
    return v
  }
  return walk(tree, '') as Tree
}
