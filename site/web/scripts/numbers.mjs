// The literal numbers of a text, in one notation, so a translation can be checked to carry the English numbers (plan 5,
// ruling T9/P29). The same rule as scripts/site/texts.py nums, and both read the cases in numbers-cases.json:
// placeholders ({x}) and quoted spans are dropped (a quote keeps its source's notation); a group mark (en ",", nl ".",
// fr U+202F or U+00A0) is removed only between a digit and exactly three digits not followed by a digit; then the
// language's decimal sign (en ".", nl/fr ",") becomes ".", and any other "." or "," between digits splits the number
// ("1.5 km" in Dutch is 1 and 5: an English decimal, the wrong notation). A plain space never groups: French writes
// "1 000" with U+202F.
const QUOTED = /«[^»]*»|“[^”]*”|„[^“”]*[“”]|‘[^’]*’|"[^"]*"/g
const GROUP = { en: /(?<=\d),(?=\d{3}(?!\d))/g, nl: /(?<=\d)\.(?=\d{3}(?!\d))/g, fr: /(?<=\d)[  ](?=\d{3}(?!\d))/g }

export function numbersOf(text, lang) {
  if (!(lang in GROUP)) throw new Error(`numbersOf: no notation for ${lang}`)
  let s = text.replace(/\{[^{}]*\}/g, ' ').replace(QUOTED, ' ').replace(GROUP[lang], '')
  if (lang !== 'en') s = s.replace(/\./g, ' ').replace(/,/g, '.')
  return (s.match(/\d+(?:\.\d+)?/g) ?? []).sort()
}
