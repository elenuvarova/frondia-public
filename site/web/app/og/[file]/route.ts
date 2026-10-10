// The og card as a JPEG, one per published language: /og/en.jpg. Drawn by lib/og.tsx (the same
// drawing the old /opengraph-image route sent as a 1.3 MB PNG, redrawn on every request), then
// re-encoded once by sharp. Prerendered at build (force-static + generateStaticParams), so a preview
// bot gets a file of about 100 KB that is never redrawn; an unpublished language (/og/nl.jpg) is a 404.
// Outside [locale] on purpose: a path with an extension skips the proxy, and the file is one per
// language by its own name, not by a locale prefix.
import { hasLocale } from 'next-intl'
import { getTranslations } from 'next-intl/server'
import sharp from 'sharp'
import { routing } from '@/i18n/routing'
import { loadJSON } from '@/lib/data'
import { ogCard, ogPhoto } from '@/lib/og'
import type { Facts } from '@/lib/types'
import { inWords } from '@/app/(site)/[locale]/sections/words'

export const runtime = 'nodejs'
export const dynamic = 'force-static'
export const dynamicParams = false

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ file: `${locale}.jpg` }))
}

export async function GET(_req: Request, { params }: { params: Promise<{ file: string }> }): Promise<Response> {
  const { file } = await params
  const locale = file.replace(/\.jpg$/, '')
  if (!file.endsWith('.jpg') || !hasLocale(routing.locales, locale)) return new Response('Not found', { status: 404 })
  const [t, facts, photo] = await Promise.all([
    getTranslations({ locale, namespace: 'landing' }),
    loadJSON<Facts>('facts.json'),
    ogPhoto(),
  ])
  const cities = Object.keys(facts.cities).length
  const kicker = t('hero.kicker', { count: inWords(t.raw('words'), cities).toLowerCase() })
  const title = (t.raw('hero.title') as string).replace(/<\/?em>/g, '')
  const png = Buffer.from(await (await ogCard({ kicker, title, photo })).arrayBuffer())
  const jpg = await sharp(png).jpeg({ quality: 82, mozjpeg: true }).toBuffer()
  return new Response(new Uint8Array(jpg), {
    headers: {
      'Content-Type': 'image/jpeg',
      // a day: a changed card reaches previews within one, with no hashed name to keep in step
      'Cache-Control': 'public, max-age=86400',
    },
  })
}
