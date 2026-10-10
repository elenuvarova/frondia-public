import type { Metadata } from 'next'
import { hasLocale } from 'next-intl'
import { getTranslations, setRequestLocale } from 'next-intl/server'
import { headers } from 'next/headers'
import { notFound } from 'next/navigation'
import { preload } from 'react-dom'
import { FaqAnchors } from '@/components/FaqAnchors'
import { Footer } from '@/components/Footer'
import { JsonLd } from '@/components/JsonLd'
import { Nav } from '@/components/Nav'
import { Reveal } from '@/components/Reveal'
import { alternates, localePath, tagOf } from '@/i18n/locales'
import { routing } from '@/i18n/routing'
import { getLanding } from '@/lib/data'
import { ogImageMeta, websiteLd } from '@/lib/seo'
import { siteUrl } from '@/lib/site'
import { Anyway } from './sections/Anyway'
import { Cases } from './sections/Cases'
import { Hero } from './sections/Hero'
import { Law } from './sections/Law'
import { Proof } from './sections/Proof'
import { Questions } from './sections/Questions'
import { Refuse } from './sections/Refuse'
import { Showcase } from './sections/Showcase'
import { Threshold } from './sections/Threshold'
import { LILAC, LILAC_PHONE } from './sections/words'

export async function generateMetadata({ params }: { params: Promise<{ locale: string }> }): Promise<Metadata> {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  const t = await getTranslations({ locale, namespace: 'landing.meta' })
  const site = siteUrl()
  const url = site + localePath(locale, '/')
  return {
    metadataBase: new URL(site),
    title: t('title'),
    description: t('description'),
    alternates: { canonical: url, languages: alternates('/', site) },
    openGraph: {
      title: t('title'), description: t('description'), url, locale: tagOf(locale).replace('-', '_'), type: 'website',
      images: ogImageMeta(locale, site, t('title')),
    },
  }
}

/* The landing (26 Sep 2026; Next since 28 Sep): the rustle and the growth on two maps, the law and
   who it is for, the method, the atlas itself, three audits, the refusals, questions; who built it is one link in the footer.
   Every word is in messages/<locale>.json under `landing`. The data is read on the server, so a
   link to #threshold or #q-outline lands on a page that already has its sections. */
export default async function Home({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  setRequestLocale(locale)
  const nonce = (await headers()).get('x-nonce') ?? undefined
  const site = siteUrl()
  const description = (await getTranslations({ locale, namespace: 'landing.meta' }))('description')
  // the hero photo starts loading with the head, one file per screen (as the Vite index.html did)
  preload('/' + LILAC.src, { as: 'image', type: 'image/webp', media: '(min-width: 721px)' })
  preload('/' + LILAC_PHONE.src, { as: 'image', type: 'image/webp', media: '(max-width: 720px)' })
  const { facts, bxl, ant, cases, points, proof } = await getLanding()
  const ninove = cases.find((c) => c.slug === 'ninove')
  const zav = bxl.sectors.find((s) => s.n === 'ZAVELENBERG')
  return (
    <>
      <JsonLd data={websiteLd(locale, site, description)} nonce={nonce} />
      <Nav tone="field" sticky stickAfter=".rustle-card" />
      <main id="main">
        <Hero cities={Object.keys(facts.cities).length} />
        <Anyway city={bxl} other={ant} ninove={ninove} />
        {proof && <Proof facts={facts} proof={proof} ant={ant} bxl={bxl} />}
        <Law facts={facts} />
        <Threshold city={bxl} ninove={ninove} />
        {ninove && <Showcase city={bxl} ninove={ninove} points={points} />}
        <Cases cases={cases} />
        <Refuse facts={facts} zav={zav} />
        <Questions facts={facts} />
      </main>
      <Footer home="" />
      <Reveal />
      <FaqAnchors />
    </>
  )
}
