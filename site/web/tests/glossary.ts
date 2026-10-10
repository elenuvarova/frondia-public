// The checked terms of i18n/glossary.md (plan 5, task 9): the rows of the table under "## Terms" whose first three
// cells are `code`. Each cell is a regular expression, matched case-insensitively. In a cell, "\|" is the regex
// alternation, and a bare "|" ends the cell. A row with plain cells is guidance only (a polysemous word: a regex would
// trap good translations). A row that mixes the two is a mistake in the glossary and throws.
import fs from 'node:fs'
import path from 'node:path'

export interface Term { en: RegExp; nl: RegExp; fr: RegExp; source: string; why: string }

export const GLOSSARY = path.join(__dirname, '../i18n/glossary.md')

const CODE = /^`(.+)`$/

export function cells(row: string): string[] {
  return row.trim().replace(/^\||\|$/g, '').split(/(?<!\\)\|/).map((c) => c.trim().replace(/\\\|/g, '|'))
}

export function parseTerms(md: string): Term[] {
  const start = md.search(/^## Terms\s*$/m)
  if (start < 0) throw new Error('glossary: no "## Terms" section')
  const rest = md.slice(start).split('\n').slice(1)
  const end = rest.findIndex((l) => /^## /.test(l))
  const out: Term[] = []
  for (const line of end < 0 ? rest : rest.slice(0, end)) {
    if (!line.startsWith('|') || /^\|[\s|:-]+\|$/.test(line)) continue
    const c = cells(line)
    const coded = c.slice(0, 3).map((x) => CODE.exec(x)?.[1])
    if (coded.every((x) => x == null)) continue                 // the header, or a guidance row
    if (coded.some((x) => x == null) || c.length !== 5) throw new Error(`glossary: a row half in code, or not five cells: ${line}`)
    const [en, nl, fr] = coded.map((x) => new RegExp(x!, 'iu'))
    out.push({ en: en!, nl: nl!, fr: fr!, source: c[3]!, why: c[4]! })
  }
  return out
}

export const terms = (): Term[] => parseTerms(fs.readFileSync(GLOSSARY, 'utf8'))
