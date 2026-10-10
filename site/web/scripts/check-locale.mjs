// Every page in one language against the same page in English (plan 5, task 14). For each path of the page lists
// (unprefixed: the language's prefix is put before each path here, never stored in the lists — ruling P32), the English
// page and the language's page are read in headless Chromium, as parity.mjs reads them (?clean, details open, no skip
// link, the atlas once its panel heading is there), and checked:
//   1. head — <html lang> is the language's tag; <title> and the description are there and not the English ones;
//      og:locale is nl_BE / fr_BE;
//   2. numbers — the numbers of the visible text equal the English page's (scripts/numbers.mjs, the catalogue test's
//      rule), and no count of four digits or more goes without the language's thousands sign where English has its
//      own (or, five digits or more, anywhere): a value printed with String() is grouped by nobody;
//   3. leaks — no run of four words or more from the English catalogue's literals (split at arguments and tags) or from
//      the English data texts (downloads.json, register.json: measures, method, limits, why) shows on the page, unless the
//      language's own catalogue or data texts carry the same run (a credit kept as its rights holder wrote it);
//   4. no raw catalogue key (common.footer.label) on the page;
//   5. the known answers: official names of sectors, communes and cities, and the footer's translation line on every
//      page that has a footer; and, from the data, no place under another language's name where this language names it
//      its own way (Ixelles on a Dutch page, Ghent in a Dutch title), outside quotes and lines both pages share;
//   6. partial English: no run of five words from the English catalogue that the language's own texts do not also
//      have, and no line shared word for word with the English page (two words of three letters or more) that is not
//      a record of same.json, an untranslated data text or a name;
//   7. with --published: hreflang alternates en-GB → the English address, nl-BE → /nl…, fr-BE → /fr…, x-default → the
//      English address, and a canonical in this language.
// The console: an error or a CSP violation on the language's page is a finding too. So is a soft hyphen (U+00AD) in an
// attribute (aria-label, title, alt, placeholder, aria-valuetext, content) or an SVG <title>: tie()'s Dutch joints belong
// in running text, not in an accessible name or a tooltip (final review M1).
//
// Usage: node web/scripts/check-locale.mjs <base> <nl|fr> [--published] [pages.json …]
//   default lists: web/scripts/pages.json and web/scripts/atlas-pages.json. Only the base's host is reached (every
//   other request is aborted, Umami's with it). Prints addresses and findings only; the report is
//   web/.parity/locale-<loc>.json. Exit code 0 with no finding, 1 otherwise.
import { chromium } from 'playwright-core'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { parse, TYPE } from '@formatjs/icu-messageformat-parser'
import { numbersOf } from './numbers.mjs'

// Number differences allowed on a page: { '<path>': { reason: '…', en: ['…'], loc: ['…'] } }. Every entry needs a reason.
const KNOWN = {}

const args = process.argv.slice(2)
const published = args.includes('--published')
const [base, loc, ...lists] = args.filter((a) => a !== '--published')
const TAG = { nl: 'nl-BE', fr: 'fr-BE' }
if (!base || !(loc in TAG)) {
  console.error('Usage: node web/scripts/check-locale.mjs <base> <nl|fr> [--published] [pages.json …]')
  process.exit(2)
}
for (const [p, k] of Object.entries(KNOWN)) if (!k.reason) { console.error(`KNOWN ${p}: no reason`); process.exit(2) }

const HERE = import.meta.dirname
const WEB = path.join(HERE, '..')
const DATA = path.join(WEB, '../public/data')
const readJSON = (f) => JSON.parse(fs.readFileSync(f, 'utf8'))
const LISTS = lists.length ? lists.map((f) => path.resolve(f)) : [path.join(HERE, 'pages.json'), path.join(HERE, 'atlas-pages.json')]
const PREFIXED = /^\/(?:en|nl|fr|xx)(?:[/?]|$)/
const PATHS = [...new Set(LISTS.flatMap((f) => readJSON(f).map((p) => p.path)))]
const listed = PATHS.filter((p) => PREFIXED.test(p))
if (listed.length) {
  // P32: the lists are English addresses; a prefixed entry would be read as /nl/nl/…
  console.error(`the page lists must hold unprefixed paths; prefixed: ${listed.join(', ')}`)
  process.exit(2)
}
const at = (p) => (p === '/' ? `/${loc}` : `/${loc}${p}`)

// ── what the language's page must say ──────────────────────────────────────────────────────────────
const EN = readJSON(path.join(WEB, 'messages/en.json'))
const OWN = readJSON(path.join(WEB, `messages/${loc}.json`))
const ANSWERS = {
  nl: {
    '/atlas?city=brussels&sector=21001A00-': ['Verzet', 'Anderlecht'],
    '/atlas?city=brussels&sector=21004E72-': ['Roodhuisplein-Zuid', 'Brussel'],
    '/commune?code=21002': ['Oudergem'],
    '/commune?code=62063': ['Luik'],
    '/data?city=liege': ['Luik'],
  },
  fr: {
    '/atlas?city=brussels&sector=21004E72-': ['Maison Rouge (Place)-Sud', 'Bruxelles'],
    '/commune?code=44021': ['Gand'],
  },
}[loc]
// the city picker names the city as the language does
const PICKED = { fr: { '/atlas?city=antwerp': 'Anvers' } }[loc] ?? {}
// a title the catalogue keeps as English on purpose (same.json: Atlas, Audit, Dossier, Register are the same words), with
// a name that is the same in both languages (Charleroi, Ten Eekhove), is the English title: allowed, by that record
const SAME = readJSON(path.join(WEB, 'i18n/same.json'))[loc] ?? {}
const flat = (o, p = '') => (o && typeof o === 'object' ? Object.entries(o).flatMap(([k, v]) => flat(v, p ? `${p}.${k}` : k)) : [[p, o]])
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
// the {city} slot takes only this language's own city names (a Dutch title naming Ghent is not the same-word title)
const OWN_CITIES = `(?:${Object.values(OWN.common.cities).map(esc).join('|')})`
const SAME_TITLES = flat(OWN).filter(([k, v]) => /\.meta\.title/.test(k) && SAME[k] && typeof v === 'string')
  .map(([, v]) => new RegExp(`^${v.split(/(\{[^{}]+\})/).map((x) => (x === '{city}' ? OWN_CITIES : /^\{/.test(x) ? '.+' : esc(x))).join('')}$`))
const FOOTER = { en: EN.common.footer.translation, own: OWN.common.footer.translation }

// ── the English runs a page must not show ──────────────────────────────────────────────────────────
const leaves = (o) => (o && typeof o === 'object' ? Object.values(o).flatMap(leaves) : typeof o === 'string' ? [o] : [])
// a message's literal pieces: arguments and tags split it, a plural's or a select's options are pieces of their own
function pieces(m) {
  const out = []; let cur = ''
  const cut = () => { if (cur.trim()) out.push(cur); cur = '' }
  const walk = (els) => {
    for (const e of els) {
      if (e.type === TYPE.literal) cur += e.value
      else if (e.type === TYPE.select || e.type === TYPE.plural) { cut(); for (const o of Object.values(e.options)) { walk(o.value); cut() } }
      else if (e.type === TYPE.tag) { cut(); walk(e.children); cut() }
      else cut()
    }
  }
  try { walk(parse(m, { ignoreTag: false })) } catch { cur = m }
  cut()
  return out
}
const norm = (s) => s.replace(/[\u00A0\u202F]/g, ' ').replace(/[\u2060\u00AD]/g, '').replace(/\s+/g, ' ').trim()
// a sentence or a clause of four words or more: the unit a leak is found by
const runs = (s) => norm(s).split(/(?<=[.?!;:])\s+|\s+[—–]\s+|\s*[\n·]\s*/).map((r) => r.trim().replace(/[.;:,]$/, ''))
  .filter((r) => (r.match(/\p{L}[\p{L}’'-]*/gu) ?? []).length >= 4)
const DATA_FIELDS = new Set(['measures', 'method', 'limits', 'why'])
function dataTexts(file) {
  if (!fs.existsSync(file)) return []
  const out = []
  const walk = (o, key) => {
    if (typeof o === 'string') { if (DATA_FIELDS.has(key)) out.push(o) }
    else if (Array.isArray(o)) o.forEach((v) => walk(v, key))
    else if (o && typeof o === 'object') for (const [k, v] of Object.entries(o)) walk(v, DATA_FIELDS.has(key) ? key : k)
  }
  walk(readJSON(file), '')
  return out
}
const enTexts = [...leaves(EN).flatMap(pieces), ...dataTexts(path.join(DATA, 'downloads.json')), ...dataTexts(path.join(DATA, 'register.json'))]
const ownText = norm([...leaves(OWN).flatMap(pieces), ...dataTexts(path.join(DATA, `downloads.${loc}.json`)), ...dataTexts(path.join(DATA, `register.${loc}.json`))].join('\n'))
const LEAKS = [...new Set(enTexts.flatMap(runs))].filter((r) => !ownText.includes(r))

// ── place names: the other languages' forms this language must not show ─────────────────────────────
// Each city's file names its sectors (n, n_nl, n_fr), their communes (c, c_nl, c_fr) and its communes (name, name_nl,
// name_fr); common.cities names the cities. Where this language's form differs, the English and the other language's
// forms are forbidden, unless one of them is this language's own name for some place (case does not count: the data is
// in capitals, the page in title case)
const OTHER = loc === 'nl' ? 'fr' : 'nl'
const CITY_FILES = ['brussels', 'antwerp', 'ghent', 'liege', 'charleroi'].map((c) => readJSON(path.join(DATA, `${c}.json`)))
const triples = []   // [english, own, other]
const sectorNames = []   // sector names: a one-word one (CENTRE, GARE, BOIS, JARDINS) is a common word, not a name to police
for (const k of Object.keys(EN.common.cities)) triples.push([EN.common.cities[k], OWN.common.cities[k], readJSON(path.join(WEB, `messages/${OTHER}.json`)).common.cities[k]])
for (const city of CITY_FILES) {
  for (const s of city.sectors ?? []) { sectorNames.push([s.n, s[`n_${loc}`] ?? s.n, s[`n_${OTHER}`] ?? s.n]); if (s.c) triples.push([s.c, s[`c_${loc}`] ?? s.c, s[`c_${OTHER}`] ?? s.c]) }
  for (const c of city.communes?.list ?? []) triples.push([c.name, c[`name_${loc}`] ?? c.name, c[`name_${OTHER}`] ?? c.name])
}
triples.push(...sectorNames.map((t) => t.map((x, i) => (i === 1 || /[\s-]/.test(String(x ?? '').trim()) ? x : null))).filter(([e, o, x]) => o && (e || x)))
// a form this language uses too, with its reason
const ALLOWED = {
  nl: { brussels: 'a Dutch adjective as well: Brussels Hoofdstedelijk Gewest' },
  fr: {},
}[loc]
const low = (x) => norm(String(x ?? '')).toLowerCase()
const OWN_FORMS = new Set(triples.map(([, o]) => low(o)))
// a short form of this language's own name is that name (Molenbeek for Sint-Jans-Molenbeek, Saint-Josse for
// Saint-Josse-ten-Noode), not another language's
const partOf = (w, o) => ` ${low(o).replace(/-/g, ' ')} `.includes(` ${low(w).replace(/-/g, ' ')} `)
const WRONG = new Map()   // lower-case wrong form → this language's form
for (const [e, o, x] of triples) for (const w of [e, x]) {
  if (w && low(w) !== low(o) && !OWN_FORMS.has(low(w)) && !partOf(w, o) && !ALLOWED[low(w)]) WRONG.set(low(w), o)
}
// this language's own names of several words are left alone where they contain another form (Gent Centrum, a district
// that keeps its name in French)
const OWN_MULTI = [...OWN_FORMS].filter((o) => /[\s-]/.test(o)).sort((a, b) => b.length - a.length)
const OWN_RX = OWN_MULTI.length ? new RegExp(`(?<![\\p{L}\\p{N}])(?:${OWN_MULTI.map(esc).join('|')})(?![\\p{L}\\p{N}])`, 'giu') : null
// a line that is a data text left as it was written (a contract's quote on /register: «Anvers», «Etangs Noirs»)
const inPool = (k) => DATA_SAME.has(k)
// a rights holder is named as it names itself in a credit: Ville de Bruxelles, Stad Antwerpen, Stad Gent
const OWNER = /(?:Ville de|Ville d’|Stad|Commune de|Gemeente)\s$/u
// a name starts with a capital on the page (a file name, frondia-brussels-sectors.csv, or an address does not)
const WRONG_RX = WRONG.size ? new RegExp(`(?<![\\p{L}\\p{N}.@/_-])(?=\\p{Lu})(?:${[...WRONG.keys()].sort((a, b) => b.length - a.length).map(esc).join('|')})(?![\\p{L}\\p{N}_])`, 'giu') : null
// quoted text keeps its source's names (a contract, a register's title)
const QUOTES_ANY = /«[^»]*»|“[^”]*”|‘(?:[^’]|’(?=\p{L}))*’(?!\p{L})|"[^"]*"/gu
function wrongNames(text, other) {
  const out = []
  if (!WRONG_RX) return out
  const keep = lineBag(other)
  for (const line of text.split('\n')) {
    const k = norm(line)
    // a line both pages share is the source's own text (a project's title, a contract's quote) when it says more than
    // the name: a heading that is only the name, the same as English, is the wrong name itself (Ixelles over a Dutch page)
    if (keep.get(k)) { keep.set(k, keep.get(k) - 1); if (wordy2(k.replace(WRONG_RX, ' ')) || inPool(k)) continue }
    const t = norm(line).replace(QUOTES_ANY, ' ').replace(OWN_RX ?? /$^/, (x) => ' '.repeat(x.length))
    for (const m of t.matchAll(WRONG_RX)) {
      if (!/^\p{Lu}/u.test(m[0]) || OWNER.test(t.slice(0, m.index))) continue
      // the place in both languages (an official bilingual name: Auderghem / Oudergem) names it this language's way too
      const mine = WRONG.get(m[0].toLowerCase())
      if (new RegExp(`(?<![\\p{L}])${esc(low(mine))}(?![\\p{L}])`, 'iu').test(low(k))) continue
      out.push(`“${m[0]}” (here: ${WRONG.get(m[0].toLowerCase())}) in “${t.slice(Math.max(0, m.index - 40), m.index + 50)}”`)
    }
  }
  return out
}
// two words of three letters or more (Schansakker is one word, 0,036 none)
function wordy2(k) { return (k.match(/\p{L}{3,}/gu) ?? []).length >= 2 }
function lineBag(text) { const m = new Map(); for (const line of text.split('\n')) { const k = norm(line); m.set(k, (m.get(k) || 0) + 1) } return m }

// ── partial English: five-word shingles, and lines shared word for word ─────────────────────────────────
const stringsOf = (o) => (o && typeof o === 'object' ? Object.values(o).flatMap(stringsOf) : typeof o === 'string' ? [o] : [])
const words = (s) => norm(s).toLowerCase().match(/[\p{L}\p{N}][\p{L}\p{N}’'-]*/gu) ?? []
const shingles = (s, n = 5) => { const w = words(s), out = []; for (let i = 0; i + n <= w.length; i++) out.push(w.slice(i, i + n)); return out }
// a shingle of names and numbers says nothing about the language: three words of three letters or more
const wordy = (sh) => sh.filter((w) => /\p{L}{3,}/u.test(w)).length >= 3
// (the language's own texts: its catalogue and every string of its data files, credits kept as their holders wrote them
// included)
const ownData = (f) => { const b = path.join(DATA, `${f}.${loc}.json`); return fs.existsSync(b) ? stringsOf(readJSON(b)) : [] }
const OWN_SHINGLES = new Set([...leaves(OWN).flatMap(pieces), ...ownData('downloads'), ...ownData('register')]
  .flatMap((t) => shingles(t)).map((sh) => sh.join(' ')))
const EN_SHINGLES = new Set(leaves(EN).flatMap(pieces).flatMap((t) => shingles(t)).filter(wordy).map((sh) => sh.join(' ')).filter((sh) => !OWN_SHINGLES.has(sh)))
function englishShingles(text) {
  const hits = []
  for (const line of text.split('\n')) for (const sh of shingles(line)) { const k = sh.join(' '); if (EN_SHINGLES.has(k)) hits.push(k) }
  return [...new Set(hits)]
}
// what may be the same on both pages: a catalogue line same.json keeps in English with a reason, a data text the
// language's file leaves as it is (a contract's quote, a project's title, a licence), and any place's name
const dataPair = (f) => { const a = path.join(DATA, `${f}.json`), b = path.join(DATA, `${f}.${loc}.json`); if (!fs.existsSync(b)) return []; const B = new Set(stringsOf(readJSON(b)).map(norm)); return stringsOf(readJSON(a)).map(norm).filter((x) => B.has(x)) }
// the landing's photo credits (public/proof/proof.json): quoted as their rights holders write them, in every language,
// as landing.proof.source joins them (re-check 1, 9 Oct)
const PROOF = path.join(DATA, '../proof/proof.json')
const proofCredits = () => (fs.existsSync(PROOF) ? Object.values(readJSON(PROOF)).flatMap((p) => [p.credit, p.licence, `${p.credit} · ${p.licence}`]) : []).map(norm)
const SAME_POOL = [...new Set([
  ...flat(OWN).filter(([k, v]) => SAME[k] && typeof v === 'string').flatMap(([, v]) => pieces(v)).map(norm),
  ...dataPair('downloads'), ...dataPair('register'), ...proofCredits(),
  ...triples.flat().filter(Boolean).map(norm),
  ...CITY_FILES.flatMap((c) => [...(c.cases ?? []), ...(c.registered ?? [])].flatMap((x) => [x.name, x.place, x.title].filter((v) => typeof v === 'string').map(norm))),
])].filter((x) => x.length > 2).sort((a, b) => b.length - a.length)
const POOL_LOW = SAME_POOL.map((x) => x.toLowerCase())
const POOL_SET = new Set(POOL_LOW)
const POOL_MULTI = POOL_LOW.filter((x) => wordy2(x))
// (only pieces and names that are one word themselves: the words of a long credit kept in English, «Statistical sectors
// and income © Statbel», must not excuse «Statistical sectors» on its own)
const ONE_WORD = [...new Set([
  ...flat(OWN).filter(([k, v]) => SAME[k] && typeof v === 'string').flatMap(([, v]) => pieces(v)),
  ...triples.flat().filter(Boolean),
].map((x) => norm(String(x)).toLowerCase().match(/\p{L}{3,}/gu) ?? []).filter((w) => w.length === 1).flat())]
const ONE_WORD_RX = new RegExp(`(?<!\\p{L})(?:${ONE_WORD.map(esc).join('|') || '(?!)'})(?!\\p{L})`, 'gu')
const DATA_SAME = new Set([...dataPair('downloads'), ...dataPair('register')])
// the words a shared line is judged by: three letters or more, written as words are (lower case, or a capital first; all
// capitals when the whole line is set in capitals); CSV, GeoPackage, ODbL are names of things
function plainWords(k) {
  const caps = k === k.toUpperCase()
  // (a word stands alone: «bbb» inside a hash, 04b2f4f2e080bbb2, or «greening» in the id greening_v1 is not one)
  return (k.match(/(?<![\p{L}\p{N}_])\p{L}{3,}(?![\p{L}\p{N}_])/gu) ?? []).filter((w) => (caps ? true : w === w.toLowerCase() || (w[0] === w[0].toUpperCase() && w.slice(1) === w.slice(1).toLowerCase())))
}
function sharedLines(text, other) {
  const keep = lineBag(other), out = []
  for (const line of text.split('\n')) {
    const k = norm(line)
    if (!keep.get(k)) continue
    keep.set(k, keep.get(k) - 1)
    // a table's row is read cell by cell (a column's code, then its description)
    for (const cell of line.split('\t').map(norm)) {
      if (plainWords(cell).length < 2) continue
      // a record, a data text or a name that is the whole cell; a record or a data text of several words wherever it
      // stands; a one-word same.json record or place name as a whole word (a one-word data identifier, the group
      // Sectors, would otherwise excuse «Statistical sectors»)
      let rest = cell.toLowerCase()
      if (POOL_SET.has(rest)) continue
      for (const x of POOL_MULTI) if (rest.includes(x)) rest = rest.split(x).join(' ')
      rest = rest.replace(ONE_WORD_RX, ' ')
      if (plainWords(cell === cell.toUpperCase() ? rest.toUpperCase() : rest).length >= 2) out.push(cell.slice(0, 120))
    }
  }
  return out
}

// ── numbers ────────────────────────────────────────────────────────────────────────────────────────
const GROUPED = { en: /\d{1,3}(?:,\d{3})+(?![\d,]*\d)/g, nl: /\d{1,3}(?:\.\d{3})+(?![\d.]*\d)/g, fr: /\d{1,3}(?:[\u202F\u00A0]\d{3})+(?!\d)/g }
const values = (text, l) => {
  const m = new Map()
  for (const g of text.match(GROUPED[l]) ?? []) { const v = g.replace(/\D/g, ''); m.set(v, (m.get(v) || 0) + 1) }
  return m
}
function ungrouped(text, enText) {
  const out = []
  const en = values(enText, 'en'), own = values(text, loc)
  for (const [v, n] of en) if ((own.get(v) || 0) < n) out.push(`${v} grouped ${n}× in English, ${own.get(v) || 0}× here`)
  // five digits or more with no group sign, away from letters (a sector code, 21004E72-, and a NIS code (INS in French), 21001, are names)
  for (const m of text.matchAll(/(?<![\p{L}\d.,\u202F\u00A0-]|(?:NIS|INS)[\s\u00A0])\d{5,}(?![\p{L}\d-])/gu)) out.push(`${m[0]} without its thousands sign`)
  // four digits that are not a year (1900–2099) are a count too, whatever English printed (String() groups nobody)
  for (const m of text.matchAll(/(?<![\p{L}\d.,:  /-])\d{4}(?![\p{L}\d-])/gu)) if (!/^(?:19|20)\d\d$/.test(m[0])) out.push(`${m[0]} without its thousands sign`)
  return out
}
// codes are written as their owners write them in every language (glossary, How to translate 7; the catalogue test's
// CODES): a licence's version, a UN indicator's number and a model's name keep their point and are not quantities
const CODES = /\bCC[\s\u00A0]BY[\s\u00A0]4\.0\b|\bODbL[\s\u00A0]1\.0\b|\bindica\w*[\s\u00A0]11\.7\b|\bClaude[\s\u00A0](?:Opus|Sonnet|Haiku)[\s\u00A0]\d+(?:\.\d+)?/g
// a Dutch quote holds French apostrophes (‘intérieur d’îlot’): its closing sign is a ’ not followed by a letter, so the
// shared rule, which stops at the first ’, would leave the rest of the quote's numbers in the text
const QUOTE_NL = /‘(?:[^’]|’(?=\p{L}))*’(?!\p{L})/gu
// the numbers a page says in its own words: a line the two pages share word for word (a contract's French quote, a
// project's name, a seed) is the source's own text and notation, the same on both by definition, and is left out
// (a line of words: two of three letters or more; a bare figure, 0.036 on a Dutch page, is checked like any other)
function said(text, other, l) {
  const keep = lineBag(other)
  const lines = text.split('\n').filter((line) => { const k = norm(line); if (keep.get(k) && wordy2(k)) { keep.set(k, keep.get(k) - 1); return false } return true })
  // line by line: a quote never runs past its paragraph, and one stray sign must not pair the quotes of the rest
  return lines.flatMap((line) => numbersOf(line.replace(CODES, ' ').replace(QUOTE_NL, ' '), l)).sort()
}
const diff = (a, b) => {
  const m = new Map(); for (const x of a) m.set(x, (m.get(x) || 0) + 1)
  const extra = []; for (const x of b) { if (m.get(x)) m.set(x, m.get(x) - 1); else extra.push(x) }
  const missing = [...m].flatMap(([k, n]) => Array(n).fill(k))
  return { missing, extra }
}
const RAW_KEY = /\b[a-z][a-zA-Z]+(?:\.[a-zA-Z0-9_]+){2,}\b/g
const DOMAIN = /\.(?:be|eu|com|org|brussels|net|io)\b/

// ── the browser ────────────────────────────────────────────────────────────────────────────────────
const EXE = path.join(os.homedir(), 'Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
const browser = await chromium.launch({ headless: true, executablePath: fs.existsSync(EXE) ? EXE : undefined })
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } })
const host = new URL(base).host
await ctx.route('**/*', (r) => {
  const u = new URL(r.request().url())
  return u.host !== host || /^\/(?:u\/script\.js|api\/send)/.test(u.pathname) ? r.abort() : r.continue()
})
await ctx.addInitScript(() => { try { localStorage.setItem('frondia.consent', JSON.stringify({ choice: 'denied', at: '2026-01-01T00:00:00.000Z', v: 1 })) } catch {} })
const page = await ctx.newPage()
let console_ = []
// the tracker this script aborts itself (above) logs «Failed to load resource» when the server has a Umami id: that is
// not the page's error (final review M3), so a console error located at /u/script.js or /api/send is not a finding
const OWN_ABORT = /\/u\/script\.js|\/api\/send/
page.on('console', (m) => { if (m.type() === 'error' && !OWN_ABORT.test(m.location()?.url || '')) console_.push(m.text().slice(0, 160)) })
page.on('pageerror', (e) => console_.push(String(e).slice(0, 160)))

const isAtlas = (p) => /^\/(?:[a-z]{2}\/)?atlas\/?(?:\?|$)/.test(p)
async function grab(p) {
  const u = new URL(base + p)
  u.searchParams.set('clean', '')
  console_ = []
  const res = await page.goto(u.toString(), { waitUntil: 'networkidle', timeout: 60000 })
  if (isAtlas(p) && res?.status() === 200) await page.waitForSelector('.panel h1', { timeout: 20000 }).catch(() => {})
  await page.evaluate(() => document.querySelectorAll('details').forEach((d) => { d.open = true }))
  await page.evaluate(() => document.querySelector('.skip-link')?.remove())
  await page.waitForTimeout(800)
  return page.evaluate(() => {
    const meta = (sel) => document.querySelector(sel)?.getAttribute('content') ?? ''
    return {
      status: 0,
      text: document.body.innerText,
      lang: document.documentElement.lang,
      title: document.title,
      description: meta('meta[name="description"]'),
      ogLocale: meta('meta[property="og:locale"]'),
      canonical: document.querySelector('link[rel="canonical"]')?.getAttribute('href') ?? '',
      alternates: Object.fromEntries([...document.querySelectorAll('link[rel="alternate"][hreflang]')].map((l) => [l.getAttribute('hreflang'), l.getAttribute('href')])),
      hasFooter: !!document.querySelector('footer'),
      picked: document.querySelector('.city-pick select')?.selectedOptions[0]?.textContent ?? '',
      // soft hyphens (U+00AD) in an attribute or an SVG title: an accessible name or a tooltip, never broken across lines
      shy: (() => {
        const out = [], A = ['aria-label', 'aria-description', 'aria-valuetext', 'title', 'alt', 'placeholder', 'content']
        for (const el of document.querySelectorAll(A.map((a) => `[${a}]`).join(','))) {
          for (const a of A) { const v = el.getAttribute(a); if (v && v.includes('\u00AD')) out.push(`${el.tagName.toLowerCase()}[${a}] “${v.replace(/\u00AD/g, '|').slice(0, 90)}”`) }
        }
        for (const t of document.querySelectorAll('svg title')) if (t.textContent.includes('\u00AD')) out.push(`svg title “${t.textContent.replace(/\u00AD/g, '|').slice(0, 90)}”`)
        return out
      })(),
    }
  }).then((r) => ({ ...r, status: res?.status() ?? 0, console: [...console_] }))
}

const findings = []
const add = (p, kind, detail) => { findings.push({ page: at(p), kind, detail }); console.log(`  ✗ ${kind}: ${detail}`) }

for (const p of PATHS) {
  console.log(at(p))
  let en, own
  try { en = await grab(p); own = await grab(at(p)) } catch (e) { add(p, 'error', String(e).slice(0, 160)); continue }
  if (own.status !== en.status) add(p, 'status', `${own.status}, English ${en.status}`)
  // 1. head
  if (own.lang !== TAG[loc]) add(p, 'lang', `<html lang="${own.lang}">`)
  if (!own.title.trim()) add(p, 'title', 'empty')
  else if (norm(own.title) === norm(en.title) && !SAME_TITLES.some((r) => r.test(norm(own.title)))) add(p, 'title', `the English one: ${own.title}`)
  if (!own.description.trim()) add(p, 'description', 'empty')
  else if (norm(own.description) === norm(en.description)) add(p, 'description', 'the English one')
  if (own.ogLocale !== TAG[loc].replace('-', '_')) add(p, 'og:locale', own.ogLocale || 'none')
  // 2. numbers
  const known = KNOWN[p]
  const d = diff(said(en.text, own.text, 'en'), said(own.text, en.text, loc))
  if (known) { d.missing = diff(known.en ?? [], d.missing).extra; d.extra = diff(known.loc ?? [], d.extra).extra }
  if (d.missing.length || d.extra.length) add(p, 'numbers', `English only: ${d.missing.join(' ') || '—'}; here only: ${d.extra.join(' ') || '—'}`)
  for (const u of ungrouped(own.text, en.text)) add(p, 'not grouped', u)
  // 3. leaks
  const text = norm(own.text)
  for (const r of LEAKS) if (text.includes(r)) add(p, 'English', r.slice(0, 120))
  // partial English
  for (const sh of englishShingles(own.text)) add(p, 'English', `… ${sh} …`)
  for (const l of sharedLines(own.text, en.text)) add(p, 'same as English', l)
  // place names, in the text and in the head
  for (const w of [...wrongNames(own.text, en.text), ...wrongNames(own.title, ''), ...wrongNames(own.description, '')]) add(p, 'name', w)
  // 4. raw keys
  for (const m of own.text.matchAll(RAW_KEY)) if (!DOMAIN.test(m[0]) && !/^www\./.test(m[0])) add(p, 'raw key', m[0])
  // 5. known answers
  for (const a of ANSWERS[p] ?? []) if (!text.includes(a)) add(p, 'name', `“${a}” missing`)
  if (PICKED[p] && norm(own.picked) !== PICKED[p]) add(p, 'name', `city picker shows “${own.picked}”, not “${PICKED[p]}”`)
  if (own.hasFooter && !text.includes(norm(FOOTER.own))) add(p, 'footer', 'the translation line is missing')
  // 6. published
  if (published) {
    const where = (h) => { try { const u = new URL(own.alternates[h]); return u.pathname + u.search } catch { return null } }
    for (const h of ['en-GB', 'nl-BE', 'fr-BE', 'x-default']) if (!own.alternates[h]) add(p, 'hreflang', `${h} missing`)
    const enAt = where('en-GB')
    if (enAt != null) {
      const pre = (l) => (enAt === '/' || enAt.startsWith('/?') ? `/${l}${enAt.slice(1)}` : `/${l}${enAt}`)
      if (/^\/(?:nl|fr|xx|en)(?:[/?]|$)/.test(enAt)) add(p, 'hreflang', `en-GB → ${enAt}, not an English address`)
      if (where('nl-BE') != null && where('nl-BE') !== pre('nl')) add(p, 'hreflang', `nl-BE → ${where('nl-BE')}, not ${pre('nl')}`)
      if (where('fr-BE') != null && where('fr-BE') !== pre('fr')) add(p, 'hreflang', `fr-BE → ${where('fr-BE')}, not ${pre('fr')}`)
      if (own.alternates['x-default'] && own.alternates['x-default'] !== own.alternates['en-GB']) add(p, 'hreflang', `x-default → ${where('x-default')}, not the English ${enAt}`)
    }
    const c = own.canonical && new URL(own.canonical).pathname
    if (!c || !(c === `/${loc}` || c.startsWith(`/${loc}/`))) add(p, 'canonical', own.canonical || 'none')
  }
  for (const x of own.shy) add(p, 'soft hyphen in an attribute', x)
  for (const c of own.console) add(p, 'console', c)
}

// the known answers on pages outside the lists
for (const p of [...Object.keys(ANSWERS), ...Object.keys(PICKED)].filter((x) => !PATHS.includes(x))) {
  console.log(at(p))
  let own
  try { own = await grab(at(p)) } catch (e) { add(p, 'error', String(e).slice(0, 160)); continue }
  const text = norm(own.text)
  if (own.status !== 200) add(p, 'status', String(own.status))
  for (const a of ANSWERS[p] ?? []) if (!text.includes(a)) add(p, 'name', `“${a}” missing`)
  if (PICKED[p] && norm(own.picked) !== PICKED[p]) add(p, 'name', `city picker shows “${own.picked}”, not “${PICKED[p]}”`)
  for (const w of [...wrongNames(own.text, ''), ...wrongNames(own.title, '')]) add(p, 'name', w)
  for (const c of own.console) add(p, 'console', c)
}

await browser.close()
fs.mkdirSync(path.join(WEB, '.parity'), { recursive: true })
fs.writeFileSync(path.join(WEB, `.parity/locale-${loc}.json`), JSON.stringify({ base, loc, published, pages: PATHS.length, findings }, null, 2))
console.log(`\n${loc}: ${PATHS.length} pages, ${findings.length} finding(s)`)
process.exit(findings.length ? 1 : 0)
