import { expect, test } from 'vitest'
import manifest from '@/app/manifest'
import { ogImageMeta, websiteLd } from '@/lib/seo'

test('JSON-LD names the site, its language and its author', () => {
  const ld = websiteLd('en', 'https://frondia.eu') as Record<string, unknown>
  expect(ld['@type']).toBe('WebSite')
  expect(ld.url).toBe('https://frondia.eu/')
  expect(ld.inLanguage).toBe('en-GB')
  expect((ld.author as Record<string, unknown>).name).toBe('Elena Uvarova')
})

test('the manifest carries the palette and the icons', () => {
  const m = manifest()
  expect(m.name).toBe('Frondia')
  expect(m.theme_color).toBe('#F3F0E7')
  expect(m.icons?.map((i) => i.sizes)).toEqual(['192x192', '512x512'])
})

test('the og image is the prerendered JPEG of the page language, absolute, with its size and alt', () => {
  expect(ogImageMeta('en', 'https://frondia.eu', 'Frondia')).toEqual([
    { url: 'https://frondia.eu/og/en.jpg', width: 1200, height: 630, type: 'image/jpeg', alt: 'Frondia' },
  ])
})
