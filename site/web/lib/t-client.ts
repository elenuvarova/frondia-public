'use client'
import { useLocale, useTranslations } from 'next-intl'
import type { Locale } from './format'
import { checkCounts, type RichValues, type TValues } from './icu'
import { tie, tieRich } from './typography'

export function useT(ns: string) {
  const t = useTranslations(ns)
  const loc = useLocale() as Locale
  // outside production, a number put where the message does not count it fails the render (lib/icu.ts)
  const check = (key: string, values: object | undefined) => {
    // (a missing key is next-intl's to report, once: t() reports it)
    if (process.env.NODE_ENV !== 'production' && t.has(key)) checkCounts(`${ns}.${key}`, String(t.raw(key)), values as Record<string, unknown> | undefined)
  }
  return {
    loc,
    t: (key: string, values?: TValues) => { check(key, values); return tie(t(key, values), loc) },
    rich: (key: string, values?: RichValues) => { check(key, values); return tieRich(t.rich(key, values as never), loc) },
    // a catalogue array or object as it stands (a legend with gaps, a list's length), as getT's raw: untied
    raw: <T,>(key: string) => t.raw(key) as T,
  }
}
