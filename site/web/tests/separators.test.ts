import fs from 'node:fs'
import path from 'node:path'
import ts from 'typescript'
import { expect, test } from 'vitest'

// A separator typed into code is English typography in every language: "·", ",", ";", "→", "#", "×" and "–" between
// words come from the catalogue (common.sep), never from a string next to an expression. One rule, read off the
// syntax tree of every page, component and library file: a separator in
//   - a template literal's text beside a ${…}                       `${a} · ${b}`, `#${r}`
//   - a string joined to an expression with +                      '#' + r, a + ", " + b
//   - a string handed to join()                                    xs.join('; ')
//   - JSX text beside a {…}                                        {a} · {b}, >#{r}<
// whatever its quotes. The catalogue (messages/*.json) is not code, and common.sep is where the separators live.
const ROOT = path.resolve(__dirname, '..')
const SEP = /[·,;→#×–]/

export interface Hit { file: string; line: number; text: string }

export function separatorsIn(file: string, src: string): Hit[] {
  const sf = ts.createSourceFile(file, src, ts.ScriptTarget.Latest, true, file.endsWith('x') ? ts.ScriptKind.TSX : ts.ScriptKind.TS)
  const hits: Hit[] = []
  const hit = (n: ts.Node, text: string) => {
    if (SEP.test(text)) hits.push({ file, line: sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1, text })
  }
  const isStr = (n: ts.Node): n is ts.StringLiteral | ts.NoSubstitutionTemplateLiteral =>
    ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)
  const visit = (n: ts.Node) => {
    if (ts.isTemplateExpression(n)) {
      hit(n.head, n.head.text)
      for (const s of n.templateSpans) hit(s.literal, s.literal.text)
    } else if (ts.isBinaryExpression(n) && n.operatorToken.kind === ts.SyntaxKind.PlusToken) {
      for (const side of [n.left, n.right]) if (isStr(side)) hit(side, side.text)
    } else if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && n.expression.name.text === 'join') {
      for (const arg of n.arguments) if (isStr(arg)) hit(arg, arg.text)
    } else if (ts.isJsxText(n)) {
      const kids = (n.parent as ts.JsxElement | ts.JsxFragment).children
      const i = kids.indexOf(n as never)
      if (kids[i - 1] && ts.isJsxExpression(kids[i - 1]!) || kids[i + 1] && ts.isJsxExpression(kids[i + 1]!)) hit(n, n.text)
    }
    ts.forEachChild(n, visit)
  }
  visit(sf)
  return hits
}

// What stays, and why: code, not words. A hit is allowed when its file matches and its text matches the pattern.
const ALLOW: { file: RegExp; text: RegExp; why: string }[] = [
  // glyphs that read the same in every language (no translator would change them)
  { file: /dossier\/page\.tsx$/, text: /^ →$/, why: 'the arrow after a link’s words ("Open in the atlas →") is the link glyph' },
  { file: /atlas\/MoreN\.tsx$/, text: /^ → $/, why: 'the arrow between two coverages ("41 % → 63 %") reads "from … to", a glyph' },
  { file: /dossier\/page\.tsx$/, text: /^×$/, why: 'the times sign after a ratio ("2.4×") is a unit glyph' },
  { file: /lib\/format\.ts$/, text: /^×$/, why: 'times(): the times sign after a ratio, the same glyph in every language' },
  { file: /(dossier|register)\/page\.tsx$/, text: /^–$/, why: 'a range of years ("2017–2024") takes an en dash in nl and fr too' },
  // addresses: a fragment of a URL or an SVG reference, not a word
  { file: /(commune\/page|Footer|Nav|atlas\/Atlas|RegisterFilters)\.tsx$/, text: /^#[\w-]*$/, why: 'an in-page anchor (#law, #c12): part of the address' },
  { file: /(PhotoRustle|SectorMap)\.tsx$/, text: /^url\(#[\w-]*$/, why: 'an SVG paint server reference, url(#id)' },
  { file: /lib\/og\.tsx$/, text: /^data:image\/jpeg;base64,$/, why: 'a data: URL' },
  // drawing: SVG path data and CSS values use commas as syntax
  { file: /(NullHistogram|Rings|SectorMap|Series|atlas\/MoreN)\.tsx$/, text: /^(M|L|M0)?,(\d+( L)?)?$|^,$/, why: 'SVG path coordinates (M x,y L x,y)' },
  { file: /SectorMap\.tsx$/, text: /^px, $/, why: 'a CSS translate(x, y) value' },
  // protocol strings: headers, cookies, a script
  { file: /lib\/csp\.ts$/, text: /^; $/, why: 'Content-Security-Policy directives are joined with "; "' },
  { file: /lib\/headers\.ts$/, text: /^, $/, why: 'a Permissions-Policy header list' },
  { file: /Clarity\.tsx$/, text: /expires=|^; domain=$/, why: 'a cookie string (document.cookie syntax)' },
  { file: /lib\/atlas\/early\.ts$/, text: /./, why: 'an inline script built as a string: JavaScript, not words' },
  { file: /lib\/icu\.ts$/, text: /^\} is not a plural; pass a string$/, why: 'checkCounts()’s error, thrown in development and tests, never shown on a page' },
  { file: /lib\/atlas\/words\.ts$/, text: /^\(\^\|\[\^0-9\.,\]\)$/, why: 'glue()’s regular expression: a value not preceded by a digit, a point or a comma' },
  { file: /lib\/typography\.ts$/, text: /^\(\\p\{L\}\{1,2\}\|$/, why: 'a regular expression’s source ({1,2} is a quantifier)' },
]

const files = (d: string): string[] => fs.readdirSync(path.join(ROOT, d), { withFileTypes: true })
  .flatMap((e) => e.isDirectory() ? files(path.join(d, e.name)) : /\.tsx?$/.test(e.name) ? [path.join(d, e.name)] : [])

test('no separator is typed into a page, a component or a library file', () => {
  const found = ['app', 'components', 'lib'].flatMap(files)
    .flatMap((f) => separatorsIn(f, fs.readFileSync(path.join(ROOT, f), 'utf8')))
    .filter((h) => !ALLOW.some((a) => a.file.test(h.file) && a.text.test(h.text)))
  expect(found.map((h) => `${h.file}:${h.line} ${JSON.stringify(h.text)}`)).toEqual([])
})

// the rule is about the syntax, not the old strings: any quotes, any of the separators, any of the four forms
test('the rule catches a separator whatever its quotes and its form', () => {
  const caught = (src: string) => separatorsIn('x.tsx', src).length > 0
  expect(caught('const s = a + " · " + b')).toBe(true)
  expect(caught("const s = a + ' · ' + b")).toBe(true)
  expect(caught('const s = `${a} · ${b}`')).toBe(true)
  expect(caught('const s = `${a} → ${b}`')).toBe(true)
  expect(caught("const s = '#' + r")).toBe(true)
  expect(caught('const s = xs.join("; ")')).toBe(true)
  expect(caught('const s = xs.join(`, `)')).toBe(true)
  expect(caught('const e = <p>{a} – {b}</p>')).toBe(true)
  expect(caught('const e = <p>#{r}</p>')).toBe(true)
  expect(caught('const e = <p>{a}×</p>')).toBe(true)
  // not caught: a glyph standing alone, a separator from the catalogue
  expect(caught('const e = <button>×</button>')).toBe(false)
  expect(caught("const s = xs.join(tc('sep.list'))")).toBe(false)
  expect(caught("const s = `${a}${tc('sep.dot')}${b}`")).toBe(false)
})
