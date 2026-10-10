import '@/styles/brand.css'
import '@/styles/tokens.css'
import '@/styles/viz.css'
import '@/styles/landing.css'
import '@/styles/consent.css'
// Every address no page answers (/foo, /atlas/foo, /dossier/x, an unpublished locale such as /nl/atlas): the site's
// own 404, rendered on the server as a page with its title and its words. It replaces a [...rest] catch-all under
// (site)/[locale] whose notFound() Next could not render on the server: the HTML arrived as Next's bare English
// "404: This page could not be found" (<html id="__next_error__">, no title) and the styled page appeared only after
// hydration (M7 of plan 4's final review). With two root layouts there is no app-wide layout, so this file brings
// its own document: the site's CSS and the shared RootDocument (consent, Umami, Clarity). The locale is the one
// proxy.ts resolved for the request (next-intl's header), so a future /nl/foo answers in Dutch.
import type { Metadata, Viewport } from 'next'
import { hasLocale } from 'next-intl'
import { getLocale, getMessages, getTranslations } from 'next-intl/server'
import { routing } from '@/i18n/routing'
import { RootDocument, rootMetadata } from '@/components/RootDocument'
import NotFound from '@/app/(site)/[locale]/not-found'
import { clientMessages, SITE_CLIENT_PATHS } from '@/lib/client-messages'

// as every site page: the browser bar's cream, and viewport-fit=cover for the safe-area insets
export const viewport: Viewport = { width: 'device-width', initialScale: 1, viewportFit: 'cover', themeColor: '#F3F0E7' }

const localeOf = async () => { const l = await getLocale(); return hasLocale(routing.locales, l) ? l : routing.defaultLocale }

export async function generateMetadata(): Promise<Metadata> {
  const locale = await localeOf()
  return { ...(await rootMetadata(locale)), title: (await getTranslations({ locale, namespace: 'common' }))('notFound.tab') }
}

export default async function GlobalNotFound() {
  const locale = await localeOf()
  return <RootDocument locale={locale} messages={clientMessages(await getMessages(), SITE_CLIENT_PATHS)}><NotFound /></RootDocument>
}
