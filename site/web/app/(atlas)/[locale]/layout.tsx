import '@/styles/brand.css'
import '@/styles/atlas/tokens.css'
import '@/styles/viz.css'
import '@/styles/atlas/atlas.css'
import '@/styles/consent.css'
import type { Metadata, Viewport } from 'next'
import { hasLocale } from 'next-intl'
import { getMessages, setRequestLocale } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { routing } from '@/i18n/routing'
import { RootDocument, rootMetadata } from '@/components/RootDocument'
import { ATLAS_CLIENT_PATHS, clientMessages } from '@/lib/client-messages'

// The atlas's own document (A1 of plan 4): its interface design system (styles/atlas/tokens.css writes
// :root, body, h1, .pill, .seg as the landing's system does, differently), not the landing's. Next makes the
// move between this root layout and the site's (app/(site)/[locale]) a full page load, so the two systems
// never meet. The shell they share — html, the words provider, consent, Umami, Clarity — is RootDocument.

export function generateStaticParams() { return routing.locales.map((locale) => ({ locale })) }
export const dynamicParams = false

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  return rootMetadata(locale)
}
export const viewport: Viewport = { width: 'device-width', initialScale: 1, viewportFit: 'cover', themeColor: '#F3F0E7' }

export default async function Layout({ children, params }: { children: React.ReactNode; params: Promise<{ locale: string }> }) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  setRequestLocale(locale)
  // the atlas's client tree reads common, atlas and landing.cases (an audit's place and story)
  return <RootDocument locale={locale} messages={clientMessages(await getMessages(), ATLAS_CLIENT_PATHS)}>{children}</RootDocument>
}
