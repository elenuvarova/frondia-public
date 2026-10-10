// The document shell every root layout shares (A1 of plan 4): the site — app/(site)/[locale] — and
// the atlas — app/(atlas)/[locale] — are separate root layouts, because each brings its own design
// system (both write :root, body, h1, .pill, .seg) and React 19 never removes a stylesheet it has
// inserted; Next makes the move between two root layouts a full page load, so the two systems never
// meet in one document. What they have in common lives here: <html lang>, the words provider, the
// consent banner, Umami and Clarity. Each layout imports its own CSS and picks its own words.
import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { NextIntlClientProvider } from 'next-intl'
import { getTranslations } from 'next-intl/server'
import { headers } from 'next/headers'
import { isPublished, tagOf } from '@/i18n/locales'
import { Clarity } from '@/components/Clarity'
import { EdgeTone } from '@/components/EdgeTone'
import { ConsentBanner } from '@/components/ConsentBanner'
import { SkipLink } from '@/components/SkipLink'
import { Umami } from '@/components/Umami'
import type { Locale } from '@/lib/format'
import { ogImageMeta } from '@/lib/seo'
import { siteUrl } from '@/lib/site'

// the head tags of the Vite landing's index.html: the icon and the og card by default.
// favicon.svg stays the tab icon (unchanged) — but declaring `icons` here at all replaces, rather
// than merges with, the file-convention results from the app-root icon.tsx/apple-icon.tsx (plan
// 2's task 4), so their PNGs and the apple-touch-icon have to be listed explicitly or the browser
// never sees them.
// metadataBase: every relative URL in the head resolves on SITE_URL, never on the request's own
// host. The og card is the default for pages that set no openGraph of their own (the 404); a page
// that sets openGraph replaces this whole object and names the card itself. Read per request, so
// the running container's SITE_URL wins over whatever the build saw. A language not yet published (routed only by a
// local preview build, NEXT_PUBLIC_PREVIEW_LOCALES) is never indexed; a page that sets robots itself says noindex too.
export async function rootMetadata(locale: Locale): Promise<Metadata> {
  const site = siteUrl()
  const title = (await getTranslations({ locale, namespace: 'landing.meta' }))('title')
  return {
    metadataBase: new URL(site),
    openGraph: { images: ogImageMeta(locale, site, title) },
    icons: {
      icon: [
        { url: '/favicon.svg', type: 'image/svg+xml' },
        { url: '/icon/0', type: 'image/png', sizes: '192x192' },
        { url: '/icon/1', type: 'image/png', sizes: '512x512' },
      ],
      apple: '/apple-icon',
    },
    ...(isPublished(locale) ? {} : { robots: { index: false, follow: false } }),
  }
}

// `messages`: only the words the layout's client components read (lib/client-messages.ts), not the
// whole catalogue
export async function RootDocument({ locale, messages, children }: { locale: Locale; messages: Record<string, unknown>; children: ReactNode }) {
  const nonce = (await headers()).get('x-nonce') ?? undefined   // per-request: matches the CSP header
  const skip = (await getTranslations({ locale, namespace: 'common' }))('skip')
  return (
    <html lang={tagOf(locale)}>
      <body>
        {/* the first Tab stop on every page, shown only when focused: past the bar to the page's own <main id="main">
            (WCAG 2.4.1; re-check 2) */}
        <SkipLink label={skip} />
        <EdgeTone />
        <NextIntlClientProvider messages={messages}>
          {/* the banner asks about Clarity alone: no Clarity, nothing to ask. It comes before the page in the DOM
              (fixed in the corner, so nothing moves): a keyboard reaches Accept in two Tabs instead of after every link
              of the page, and a screen reader meets the question first (re-check 2, decided on WCAG 2.4.3) */}
          {process.env.CLARITY_ID && <ConsentBanner />}
          {children}
        </NextIntlClientProvider>
        <Umami nonce={nonce} />
        {process.env.CLARITY_ID && <Clarity id={process.env.CLARITY_ID} nonce={nonce} />}
      </body>
    </html>
  )
}
