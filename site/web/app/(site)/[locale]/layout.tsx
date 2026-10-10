import '@/styles/brand.css'
import '@/styles/tokens.css'
import '@/styles/viz.css'
import '@/styles/landing.css'
import '@/styles/consent.css'
import type { Metadata, Viewport } from 'next'
import { hasLocale } from 'next-intl'
import { getMessages, setRequestLocale } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { routing } from '@/i18n/routing'
import { RootDocument, rootMetadata } from '@/components/RootDocument'
import { clientMessages, SITE_CLIENT_PATHS } from '@/lib/client-messages'

// The root layout of the site — landing, privacy and the document pages. The atlas has a root layout
// of its own (app/(atlas)/[locale]) with its own design system; the shell they share — html, the
// words provider, consent, Umami, Clarity — is components/RootDocument.tsx.

export function generateStaticParams() { return routing.locales.map((locale) => ({ locale })) }
// only the published locales exist: /favicon.ico or /.env (paths the proxy skips) are a 404, not a locale
export const dynamicParams = false

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  return rootMetadata(locale)
}
// the cream of the browser bar, and viewport-fit=cover, which the env(safe-area-inset-*) rules in the CSS need
export const viewport: Viewport = { width: 'device-width', initialScale: 1, viewportFit: 'cover', themeColor: '#F3F0E7' }

export default async function Layout({ children, params }: { children: React.ReactNode; params: Promise<{ locale: string }> }) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  setRequestLocale(locale)
  // the browser gets only the words its client components read, not the whole catalogue
  return <RootDocument locale={locale} messages={clientMessages(await getMessages(), SITE_CLIENT_PATHS)}>{children}</RootDocument>
}
