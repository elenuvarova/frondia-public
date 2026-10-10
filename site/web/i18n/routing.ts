import { defineRouting } from 'next-intl/routing'
import { DEFAULT, ROUTED } from './locales'

export const routing = defineRouting({
  // the published languages, plus a local preview build's NEXT_PUBLIC_PREVIEW_LOCALES (i18n/locales.ts)
  locales: ROUTED,
  defaultLocale: DEFAULT,
  localePrefix: 'as-needed',
  // the address decides the language; the browser's languages are never used to redirect
  localeDetection: false,
  // …and so no NEXT_LOCALE cookie either: the footer says the site sets none
  localeCookie: false,
})
