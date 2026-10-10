import fs from 'node:fs'
import path from 'node:path'
import { expect, test } from 'vitest'
import { createTranslator } from 'next-intl'
import en from '@/messages/en.json'
import { EV } from '@/lib/analytics'
import { PUBLISHED } from '@/i18n/locales'

// re-check 4: the privacy page names every kind of click the site counts. A new event in lib/analytics EV fails here
// until its words are added to privacy.counts. The language switch counts only once a second language is published, so
// the message is a select on `langs` (the page passes 'many' when PUBLISHED has more than one language, else 'one').
const WORDS: Record<keyof typeof EV, RegExp> = {
  atlas: /opening the atlas/, audit: /an audit/, faq: /a question/, consent: /cookie choice/, download: /downloading a file/,
  lang: /language/,
}
const t = createTranslator({ locale: 'en', messages: en, namespace: 'privacy' })

test('privacy.counts names every counted event once languages are published', () => {
  const text = t('counts', { langs: 'many' })
  for (const k of Object.keys(EV) as (keyof typeof EV)[]) expect(text, k).toMatch(WORDS[k])
})

test('with one language, privacy.counts names every event but the language switch', () => {
  const text = t('counts', { langs: 'one' })
  for (const k of Object.keys(EV) as (keyof typeof EV)[]) {
    if (k === 'lang') expect(text, k).not.toMatch(WORDS[k])
    else expect(text, k).toMatch(WORDS[k])
  }
})

// the English page says today exactly what it said before the select (round 4 added the downloads)
test('the one-language text is the text the page has today', () => {
  expect(t('counts', { langs: 'one' })).toBe('Visit counts. The site counts page views, a few clicks (opening the atlas, an audit or a question, downloading a file) and your cookie choice with Umami, running on our own server in Germany (Hetzner); page views are also counted by a second Umami of ours on the same server, for an overview of all our sites. No cookies are set, no IP address is stored, and browsers that send Do Not Track are not counted. The counts cannot identify you: they are aggregate numbers without personal data, kept as long as the site runs.')
})

// the page picks the branch from the registry: with nl and fr published (plan 5, task 15) it names the language switch
test('the privacy page passes many once a second language is published, one before', () => {
  const src = fs.readFileSync(path.join(__dirname, '../app/(site)/[locale]/privacy/page.tsx'), 'utf8')
  expect(src).toContain("t('counts', { langs: PUBLISHED.length > 1 ? 'many' : 'one' })")
  const shown = t('counts', { langs: PUBLISHED.length > 1 ? 'many' : 'one' })
  if (PUBLISHED.length > 1) expect(shown).toMatch(/switching the language/)
  else expect(shown).not.toMatch(/language/)
})
