import fs from 'node:fs'
import path from 'node:path'
import { expect, test } from 'vitest'
import en from '@/messages/en.json'
import fr from '@/messages/fr.json'
import nl from '@/messages/nl.json'

// The consent card on a short screen (≤ 400 px tall; round-3 re-check, 6 Oct 2026): one short line in place of the
// paragraph, the Privacy link for the rest, the same two buttons. Fails on bd8848d (no short line, no short layout).
const C = { en: en.common.consent, nl: nl.common.consent, fr: fr.common.consent } as Record<string, Record<string, string>>

test.each(['en', 'nl', 'fr'])('%s: the short line names Clarity and its cookies, asks, and is well under the paragraph', (l) => {
  const c = C[l]!
  expect(c.short).toBeTruthy()
  expect(c.short).toMatch(/Microsoft Clarity/)
  expect(c.short).toMatch(/cookies/)
  expect(c.short).toMatch(/\?$/)
  expect(c.short!.length).toBeLessThan(c.text!.length * 0.45)
  expect(c.short!.length).toBeLessThanOrEqual(76)   // two lines at 320 px wide, with the ties (all three measured: 2 lines)
  // the buttons and the link are the same words in both cards: one set of keys
  expect(Object.keys(c).sort()).toEqual(['accept', 'decline', 'label', 'privacy', 'short', 'text'])
})

test('the short card is CSS only: it swaps the text at ≤ 400 px tall and keeps both buttons alike', () => {
  const css = fs.readFileSync(path.join(__dirname, '../styles/consent.css'), 'utf8')
  const short = css.slice(css.indexOf('@media (max-height: 400px)'))
  expect(short).toMatch(/\.consent-text--full \{ display: none; \}/)
  expect(short).toMatch(/\.consent-text--short \{ display: block;/)
  expect(short).toMatch(/\.consent-actions \.pill \{ height: auto; min-height: 32px;/)   // both pills, one rule
  const tsx = fs.readFileSync(path.join(__dirname, '../components/ConsentBanner.tsx'), 'utf8')
  expect(tsx.match(/className="pill pill--ghost"/g)).toHaveLength(2)
  expect(tsx).not.toMatch(/type="checkbox"|defaultChecked/)
})
