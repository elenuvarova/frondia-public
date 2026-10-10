import { hasLocale } from 'next-intl'
import { getRequestConfig } from 'next-intl/server'
import en from '../messages/en.json'
import { isPublished } from './locales'
import { routing } from './routing'
import { mergeFallback, pseudoCatalogue, type Tree } from '@/lib/pseudo'

// a published language serves its own catalogue only (it is complete); a preview language borrows the English of every
// key it lacks, so its pages render and the page checks find the English left in them; the pseudo-language is made
// from English on the fly (lib/pseudo.ts), once per server, and never stored
let xx: Tree | undefined
export default getRequestConfig(async ({ requestLocale }) => {
  const asked = await requestLocale
  const locale = hasLocale(routing.locales, asked) ? asked : routing.defaultLocale
  if (locale === 'en') return { locale, messages: en }
  if (locale === 'xx') return { locale, messages: (xx ??= pseudoCatalogue(en as Tree)) }
  const own = (await import(`../messages/${locale}.json`)).default as Tree
  return { locale, messages: isPublished(locale) ? own : mergeFallback(en as Tree, own) }
})
