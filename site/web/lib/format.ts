// Numbers the way a measurement reads: fixed decimals, a real minus sign, an explicit plus — in the
// reader's language. Separators come from Intl; the signs stay ours in every language.
import { infoOf, tagOf, type Locale } from '@/i18n/locales'
export type { Locale }
export const MINUS = '−'
export const NNBSP = ' '

type N = number | null | undefined
const bad = (v: N): v is null | undefined => v == null || Number.isNaN(v)

function digits(abs: number, d: number, loc: Locale): string {
  const s = new Intl.NumberFormat(tagOf(loc), { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: false }).format(abs)
  return s
}

export function signed(v: N, d = 3, loc: Locale): string {
  if (bad(v)) return '—'
  const abs = Number(Math.abs(v).toFixed(d))
  if (abs === 0) return digits(0, d, loc)
  return (v < 0 ? MINUS : '+') + digits(abs, d, loc)
}

export function fixed(v: N, d = 3, loc: Locale): string {
  if (bad(v)) return '—'
  const abs = Number(Math.abs(v).toFixed(d))
  return (v < 0 && abs !== 0 ? MINUS : '') + digits(abs, d, loc)
}

export function int(v: N, loc: Locale): string {
  if (v == null) return '—'
  // French groups with a narrow no-break space; Intl already does, and so it stays
  return new Intl.NumberFormat(tagOf(loc), { maximumFractionDigits: 0 }).format(Math.round(v)).replace(/ /g, NNBSP)
}

export function pct(v: N, d = 0, loc: Locale): string {
  if (v == null) return '—'
  const n = digits(Number((v * 100).toFixed(d)), d, loc)
  return `${n}${infoOf(loc).percentSpace}%`
}

// A plain quantity, as many decimals as it has up to maxDigits (1, 1.5, 0.04): grouped as the
// language groups, with the real minus and French's narrow no-break space — the house rules int()
// and fixed() keep, for the numbers a sentence quotes from the data's rules.
export function dec(v: N, loc: Locale, maxDigits = 3): string {
  if (bad(v)) return '—'
  const abs = Number(Math.abs(v).toFixed(maxDigits))
  const s = new Intl.NumberFormat(tagOf(loc), { maximumFractionDigits: maxDigits }).format(abs).replace(/ /g, NNBSP)
  return (v < 0 && abs !== 0 ? MINUS : '') + s
}

// A day in words, in the reader's language and on Brussels's calendar: "5 September 2026"
export function longDate(iso: string, loc: Locale): string {
  return new Date(iso).toLocaleDateString(tagOf(loc), { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Brussels' })
}

export function times(a: number, b: number, d = 1, loc: Locale): string {
  return digits(Number((Math.abs(a) / Math.abs(b)).toFixed(d)), d, loc) + '×'
}

// Statbel names come in capitals: RUE DE WAND, CHEMIN DE FER, 'T MESTPUTTEKE.
const PARTICLES = new Set(['de', 'du', 'des', 'la', 'le', 'les', 'et', 'en', 'sur', 'aux', 'au', 'van', 'der', 'den', 'het', 'ten', 'op'])
// A Roman numeral stays upright (RUE JOSEPH II, QUARTIER DU XII, FORT IV), and a French elision inside a
// name stays low (CHANTS D'OISEAUX → Chants d'Oiseaux, CITE DE L'EUROPE → Cite de l'Europe) — re-check 3.
const ROMAN = /^(?=[ivx]{2,}$)x{0,3}(?:ix|iv|v?i{0,3})$/
export function titleCase(s: string): string {
  const low = s.toLowerCase()
  return low.replace(/(^|[\s\-('/.])(\p{L}+)/gu, (m, p: string, w: string, off: number) => {
    if (ROMAN.test(w)) return p + w.toUpperCase()
    if (off > 0 && p === ' ' && (PARTICLES.has(w) || (/^[dl]$/.test(w) && low[off + m.length] === "'"))) return p + w
    return p + w[0]!.toUpperCase() + w.slice(1)
  }).replace(/(^|\s)'t\b/gi, "$1't")
}

// "2017–2019 → 2021–2024" → "2017–19 → 2021–24"
export function shortWindow(w: string): string {
  return w.replace(/(\d{4})–\d{2}(\d{2})/g, '$1–$2')
}
