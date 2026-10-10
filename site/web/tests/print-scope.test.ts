import fs from 'node:fs'
import path from 'node:path'
import { expect, test } from 'vitest'

// the dossier's @media print block: every rule must apply only while a document page (main.doc) is on screen —
// the stylesheet outlives a client-side navigation away from the dossier
function printRules(css: string): string[] {
  css = css.replace(/\/\*[\s\S]*?\*\//g, '')   // comments are not selectors
  const at = css.indexOf('@media print')
  let depth = 0, i = css.indexOf('{', at), start = i + 1
  for (; i < css.length; i++) { if (css[i] === '{') depth++; else if (css[i] === '}' && --depth === 0) break }
  return css.slice(start, i).split('}').map((r) => r.split('{')[0]!.trim()).filter(Boolean)
}

test('the dossier prints only itself, and only while it is on screen', () => {
  const css = fs.readFileSync(path.join(__dirname, '../styles/dossier.css'), 'utf8')
  const selectors = printRules(css).filter((s) => !s.startsWith('@page'))
  expect(selectors.length).toBeGreaterThan(10)
  for (const s of selectors) for (const one of s.split(',')) {
    expect(one.trim(), s).toMatch(/^(:root:has\(main\.doc\)|body:has\(main\.doc\)|:where\(\.doc\)|\.doc\b)/)
  }
})
