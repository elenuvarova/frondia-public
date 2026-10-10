// lib/t.ts — every word the page shows passes through tie() for its language
import { getLocale, getTranslations } from 'next-intl/server'
import type { Locale } from './format'
import { checkCounts, type RichValues, type TValues } from './icu'
import { tie, tieRich } from './typography'

export async function getT(ns: string) {
  const [t, loc] = await Promise.all([getTranslations(ns), getLocale() as Promise<Locale>])
  // outside production, a number put where the message does not count it fails the render (lib/icu.ts)
  const check = (key: string, values: object | undefined) => {
    // (a missing key is next-intl's to report, once: t() reports it)
    if (process.env.NODE_ENV !== 'production' && t.has(key)) checkCounts(`${ns}.${key}`, String(t.raw(key)), values as Record<string, unknown> | undefined)
  }
  return {
    loc,
    t: (key: string, values?: TValues) => { check(key, values); return tie(t(key, values), loc) },
    rich: (key: string, values?: RichValues) => { check(key, values); return tieRich(t.rich(key, values as never), loc) },
    raw: <T,>(key: string) => t.raw(key) as T,
  }
}
