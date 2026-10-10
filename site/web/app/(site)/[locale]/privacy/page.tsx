import type { Metadata } from 'next'
import { hasLocale } from 'next-intl'
import { getTranslations, setRequestLocale } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { ConsentReset } from '@/components/ConsentReset'
import { Footer } from '@/components/Footer'
import { Nav } from '@/components/Nav'
import { Reveal } from '@/components/Reveal'
import { PUBLISHED, alternates, localePath, tagOf } from '@/i18n/locales'
import { routing } from '@/i18n/routing'
import { ogImageMeta } from '@/lib/seo'
import { siteUrl } from '@/lib/site'
import { getT } from '@/lib/t'

const CONTACT_EMAIL = 'contact@frondia.eu'

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  const [t, landingTitle] = await Promise.all([
    getTranslations({ locale, namespace: 'privacy.meta' }),
    getTranslations({ locale, namespace: 'landing.meta' }).then((lt) => lt('title')),
  ])
  const site = siteUrl()
  const url = site + localePath(locale, '/privacy')
  return {
    metadataBase: new URL(site),
    title: t('title'),
    description: t('description'),
    alternates: { canonical: url, languages: alternates('/privacy', site) },
    openGraph: {
      title: t('title'), description: t('description'), url, locale: tagOf(locale).replace('-', '_'), type: 'website',
      // the og image itself is the landing's card (one file for the whole [locale] subtree), so
      // its alt text is the landing's own title, not this page's
      images: ogImageMeta(locale, site, landingTitle),
    },
  }
}

/* What this site records, where it goes, and how to change your mind. Every paragraph here is the
   honest counterpart of the consent banner (components/ConsentBanner.tsx) and the footer's privacy
   line (components/Footer.tsx) — same facts, said in full. The Clarity paragraph was checked against
   Microsoft's own Clarity docs before being written (see the task report for the sources). */
export default async function Privacy({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  setRequestLocale(locale)
  const { t, rich } = await getT('privacy')
  return (
    <>
      <Nav />
      <main id="main">
        <section className="section" id="privacy">
          <div className="wrap">
            <div className="split reveal">
              <h1 className="display-l">{t('title')}</h1>
              <div className="body">
                <p>{t('lede')}</p>
                <p>{rich('who', { email: CONTACT_EMAIL, mail: (c) => <a href={`mailto:${CONTACT_EMAIL}`}>{c}</a> })}</p>
                <p>{t('counts', { langs: PUBLISHED.length > 1 ? 'many' : 'one' })}</p>
                <p>{t('clarity')}</p>
                <p>{t('pause')}</p>
                <p>{t('none')}</p>
                <p>{t('hosting')}</p>
                <p>{t('basis')}</p>
                <p>{t('rights')}</p>
              </div>
            </div>
            {/* the choice is about Clarity alone: without it there is nothing to change */}
            {process.env.CLARITY_ID && <p><ConsentReset label={t('change')} /></p>}
          </div>
        </section>
      </main>
      <Footer />
      <Reveal />
    </>
  )
}
