/* No-break spaces, set when the text is rendered (27 Sep 2026 rules, per language). A line never ends
   on a one- or two-letter word, an article or a short preposition or conjunction; a number never parts
   from the word it counts; a spaced dash, an arrow or a middle dot never starts a line; a number range
   or "3-30-300" never breaks at its hyphen; "=" never parts from either side. French adds its own
   spaces: narrow no-break before ; ! ? and %, no-break before : and inside « ». A number sign (n°, nr., no.)
   keeps its number. The short words are the registry's (i18n/short-words.json, read by typo-audit too). The old site did this on the
   DOM after load; under Next it would rewrite server HTML and break hydration, so it runs on strings. */
import { Children, cloneElement, createElement, isValidElement, type ReactNode } from 'react'
import { infoOf, type Locale } from '@/i18n/locales'
import SOFT from '@/i18n/soft-hyphens.json'

export const NB = ' '
export const WJ = '⁠'
const NNBSP = ' '

// French fixed compounds never break at their hyphen: «…ha au- ⏎ delà du bruit» on a phone (re-check round 1, 5 Oct).
// U+2011 is a no-break hyphen; the site's three fonts have no glyph for it, but Chromium and WebKit draw the font's own
// hyphen in its place (same font, same width: checked in round 3).
const NBH = '‑'
const FR_FIXED = /(?<!\p{L})(?:au-delà|c[’']est-à-dire|peut-être|vis-à-vis|au-dessus|au-dessous|là-bas)(?!\p{L})/giu
// Dutch writes a code's compound with a hyphen: NIS-code, IP-adres, LBE-code, VN-indicator, NDVI-eenheden, GIS-software.
// A line never ends on «NIS-» (design wave, 5 Oct 2026): the hyphen after an abbreviation (a capital and one or more
// capitals or digits) and before a small letter is a no-break hyphen, as in the French fixed compounds. A place name keeps
// its breakable hyphen (Sint-Gillis, Sint-Joost-ten-Node: a capital and small letters is no abbreviation), and so does a
// number's word («3-30-300-regel»: digits alone are no abbreviation)
const NL_CODE = /(?<![\p{L}\p{N}])(\p{Lu}[\p{Lu}\p{N}]+)-(?=\p{Ll})/gu

const NUMBER = '[+−-]?\\d(?:[\\d.,:%×–\\u2060\\u202F]*[\\d%×])?'
const BEFORE = '(^|[\\s\\u00A0(\\[“‘"\'/–—«-])'

const rx = (loc: Locale) => ({
  short: new RegExp(`${BEFORE}(\\p{L}{1,2}|${infoOf(loc).short}) (?=\\S)`, 'giu'),
  num: new RegExp(`(^|[\\s\\u00A0(\\[“‘"'±+−-])(${NUMBER}) (?=[\\p{L}(“‘"'«])`, 'gu'),
  endWord: new RegExp(`${BEFORE}(\\p{L}{1,2}|${infoOf(loc).short})$`, 'iu'),
  endNum: new RegExp(`(^|[\\s\\u00A0(\\[“‘"'±+−-])(${NUMBER})$`, 'u'),
})
const CACHE = new Map<Locale, ReturnType<typeof rx>>()
const R = (loc: Locale) => { if (!CACHE.has(loc)) CACHE.set(loc, rx(loc)); return CACHE.get(loc)! }

// Dutch compounds that do not fit a narrow column carry soft hyphens at their joints (i18n/soft-hyphens.json, «|» marks
// a joint): headless Chromium and any browser without a Dutch hyphenation dictionary broke «vergelijkingsplaatsen»
// anywhere when it did not fit (typo-audit --no-hyphens, fix round 1). Case is the text's own; other languages untouched
const SOFT_RX = new Map<Locale, { rx: RegExp; at: Map<string, number[]> }>()
function softOf(loc: Locale) {
  if (SOFT_RX.has(loc)) return SOFT_RX.get(loc)
  const list = (SOFT as Record<string, string[]>)[loc]
  if (!list) return undefined
  const at = new Map<string, number[]>()
  for (const w of list) { const parts = w.split('|'); let n = 0; at.set(parts.join('').toLowerCase(), parts.slice(0, -1).map((p) => (n += p.length))) }
  // a word, not a piece of an address: never after a letter, a digit or . / @ : _ -, and never before a letter, a digit or
  // a dot, slash or @ that goes on («geodata.antwerpen.be», «info@antwerpen.be», «…/vergelijkingsplaatsen»): a soft
  // hyphen copied with a domain breaks it (final review I2). A sentence's own full stop («in Antwerpen.») still counts
  const rx = new RegExp(`(?<![\\p{L}\\p{N}./@:_-])(?:${[...at.keys()].sort((a, b) => b.length - a.length).join('|')})(?![\\p{L}\\p{N}]|[./@][\\p{L}\\p{N}])`, 'giu')
  SOFT_RX.set(loc, { rx, at })
  return SOFT_RX.get(loc)
}
function soften(text: string, loc: Locale): string {
  const s = softOf(loc)
  if (!s) return text
  return text.replace(s.rx, (w) => { let out = '', last = 0; for (const i of s.at.get(w.toLowerCase())!) { out += w.slice(last, i) + SHY; last = i } return out + w.slice(last) })
}
const SHY = '\u00AD'

// an attribute's text (aria-label, alt, title, placeholder): tie()'s no-break spaces stay, its soft hyphens go. A screen
// reader skips U+00AD, but it is noise in an accessible name and in any text a tool reads from it (final review M1). The
// French no-break hyphen becomes the ordinary one there too: an accessible name never breaks across lines
export const plain = (s: string): string => s.replace(/\u00AD/g, '').replace(/\u2011/g, '-')

export function tie(text: string, loc: Locale = 'en'): string {
  if (!text) return text
  text = soften(text, loc)
  const r = R(loc)
  // a number sign keeps its number ("n° 3", "nr. 3", "no. 3"). The trade-off: only before a digit, so "no. of" or a
  // sentence ending on "no." before a number ("said no. 3 days later") is glued too; that costs one line break at
  // worst, against a sign stranded at a line end every time
  let out = text.replace(/(^|\s)(n°|nr\.|no\.) (?=\d)/gi, `$1$2${NB}`)
  // French "45 %": the catalogue writes a plain space, as before ; : ! ?. Set before the number loop, so the number,
  // its % and the word after it hold together
  if (loc === 'fr') out = out.replace(/(\d) %/g, `$1${NNBSP}%`)
  for (let i = 0; i < 4; i++) {
    const next = out.replace(r.short, `$1$2${NB}`).replace(r.num, `$1$2${NB}`)
    if (next === out) break
    out = next
  }
  out = out
    .replace(/ (?=[—–] |[→↗·](?: |$))/g, NB)
    .replace(/(\d)([-–])(?=\d)/g, `$1$2${WJ}`)
    .replace(/[  ]([=≈≤≥<>]) (?=\S)/g, `${NB}$1${NB}`)
  // a spaced plus and a signed number after a word never start a line either ("(BE_ + NIS-code)", "canopy +16.8 ha";
  // after a colon the line may still break: "…: ±0,035 in Brussel" would make one long unbreakable run). Set in every
  // language: the translations' longer words first moved those breaks onto a phone's column (plan 5, task 14), and
  // English had the same stranded sign, «canopy ⏎ +16.8 ha» (P5-12, fix wave)
  out = out.replace(/ (?=\+ )|(?<=\p{L}) (?=[+−±]\d)/gu, NB)
  if (loc === 'nl') out = out.replace(NL_CODE, `$1${NBH}`)
  if (loc === 'fr') {
    out = out
      .replace(FR_FIXED, (w) => w.replace(/-/g, NBH))
      .replace(/ ([;!?])/g, `${NNBSP}$1`)
      .replace(/ :/g, `${NB}:`)
      .replace(/« /g, `«${NB}`)
      .replace(/ »/g, `${NB}»`)
  }
  return out
}

// the first text of a node at any depth: a string is itself, an element is its first child's first text
// (<a><span>→ atlas</span></a> opens with →); empty, null and false children render nothing and are skipped
function firstText(node: ReactNode): string {
  if (typeof node === 'string') return node
  if (typeof node === 'number') return String(node)
  if (Array.isArray(node)) {
    for (const k of node as ReactNode[]) { const t = firstText(k); if (t) return t }
    return ''
  }
  if (isValidElement<{ children?: ReactNode }>(node)) return firstText(node.props.children)
  return ''
}

// the last space of a string before an element becomes a no-break space when the string ends on a
// short word or a number ("became a <em>meadow park</em>"), or when the next piece opens with → or ·
function tieEdge(s: string, next: ReactNode, loc: Locale): string {
  if (!s.endsWith(' ')) return s
  const head = s.slice(0, -1)
  const r = R(loc)
  const nextText = firstText(next)
  if (r.endWord.test(head) || r.endNum.test(head) || /^[→↗·]/.test(nextText)) return head + NB
  return s
}

export function tieRich(node: ReactNode, loc: Locale): ReactNode {
  const kids = Children.toArray(node)
  const out = kids.map((k, i) => {
    if (typeof k === 'string') return tieEdge(tie(k, loc), kids.slice(i + 1), loc)
    if (isValidElement<{ children?: ReactNode }>(k) && k.props.children != null) {
      return cloneElement(k, undefined, tieRich(k.props.children, loc))
    }
    return k
  })
  return Array.isArray(node) ? out : out.length === 1 ? out[0] : out
}

// French writes a percentage-point difference «1,2 pt» (glossary: the abbreviation spares a decimal its agreement); read
// aloud, «pt» is two letters or a pint. The abbreviation is drawn and hidden from screen readers, and the full phrase
// (common.pointsSpoken, a plural on the number: «1,3 point de pourcentage», «11,0 points de pourcentage») is read in its
// place (plan 5, task 14). «pt» keeps its number but may end a line: tie() took it for a two-letter word and glued it to
// the next, and «11,0 pt en dessous» made one run too wide for a commune figure's 120-px note. Every other language
// comes back as it was given.
export function spokenPoints(text: string, loc: Locale, phrase: (n: number) => string): ReactNode {
  if (loc !== 'fr') return text
  const parts = text.split(/(?<=\d[\u00A0\u202F ])pt(?!\p{L})/u)
  if (parts.length === 1) return text
  return parts.flatMap((s, i) => {
    if (i === 0) return [s]
    // the number just before this «pt», in French notation: 1,3 · −0,6 · 1 234
    const m = parts[i - 1]!.match(/([+−-]?\d[\d\u202F\u00A0]*(?:,\d+)?)[\u00A0\u202F ]$/)
    const n = m ? Math.abs(Number(m[1]!.replace(/[\u202F\u00A0]/g, '').replace('−', '-').replace(',', '.'))) : 2
    return [
      createElement('span', { key: `a${i}`, 'aria-hidden': true }, 'pt'),
      createElement('span', { key: `b${i}`, className: 'sr-only' }, phrase(n)),
      s.replace(/^\u00A0/, ' '),
    ]
  })
}
