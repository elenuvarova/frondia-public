import type { Metadata } from 'next'
import { hasLocale } from 'next-intl'
import { getTranslations, setRequestLocale } from 'next-intl/server'
import { headers } from 'next/headers'
import { notFound } from 'next/navigation'
import { preload } from 'react-dom'
import { Atlas } from '@/components/atlas/Atlas'
import { Icon } from '@/components/Icon'
import { routing } from '@/i18n/routing'
import { earlyFetchScript } from '@/lib/atlas/early'
import { fieldPreload, resolveAtlas } from '@/lib/atlas/resolve'
import type { RawQuery } from '@/lib/atlas/state'
import { sectorName, sectorPlace } from '@/lib/names'
import { atlasHeadWords, atlasMetadata } from '@/lib/seo'

type Params = Promise<{ locale: string }>
type Search = Promise<RawQuery>

// Each view's own head (words: lib/seo.ts atlasHeadWords), from the same resolveAtlas as the page (the city's file is
// read once per process, A2); canonical and og:url in lib/seo.ts atlasMetadata
export async function generateMetadata({ params, searchParams }: { params: Params; searchParams: Search }): Promise<Metadata> {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  const [t, tc, tl, r] = await Promise.all([
    getTranslations({ locale, namespace: 'atlas' }),
    getTranslations({ locale, namespace: 'common' }),
    getTranslations({ locale, namespace: 'landing' }),
    searchParams.then(resolveAtlas),
  ])
  // the sector's name and commune in the page's language (lib/names.ts); a nameless one is '' and falls through
  const sector = r.sector && { name: sectorName(r.sector, locale), place: sectorPlace(r.sector, locale) }
  const { title, description } = atlasHeadWords({ ...r, sector }, t, tc, tl)
  return atlasMetadata({ locale, r, title, description, ogAlt: tl('meta.title') })
}

// The atlas: the server reads the address (lib/atlas/resolve.ts) and hands the client tree the state alone, normalised
// as the head reads it (Q15); the map, the panels and the cards are client components that fetch the city's files
// themselves (A2 of plan 4)
export default async function AtlasPage({ params, searchParams }: { params: Params; searchParams: Search }) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  setRequestLocale(locale)
  const r = await resolveAtlas(await searchParams)
  // the browser fetches the city itself (A2): start both downloads with the HTML, never ship them in it. The city's file
  // is started by a nonced script whose promise the atlas adopts (lib/atlas/early.ts): WebKit never hands an
  // as="fetch" preload to fetch(), so a preload made Safari download the city twice
  const nonce = (await headers()).get('x-nonce') ?? undefined
  const field = fieldPreload(r.state, r.fieldSrc)
  if (field) preload(field.href, { as: 'image', fetchPriority: 'high', media: field.media })
  const icons = { pin: <Icon name="pin" size={16} />, need: <Icon name="thermometer" size={16} />, place: <Icon name="pin" size={16} />, change: <Icon name="layers" size={16} /> }
  return (
    <>
      {/* eslint-disable-next-line react/no-danger */}
      <script nonce={nonce} dangerouslySetInnerHTML={{ __html: earlyFetchScript(`/data/${r.state.city}.json`) }} />
      <Atlas initial={r.state} icons={icons} />
    </>
  )
}
