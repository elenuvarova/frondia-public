'use client'
import { Fragment, type MouseEvent } from 'react'
import { useSearchParams } from 'next/navigation'
import { usePathname } from '@/i18n/navigation'
import { LOCALES, ROUTED } from '@/i18n/locales'
import { EV } from '@/lib/analytics'
import { switchHref } from '@/lib/links'
import { useT } from '@/lib/t-client'
import { plain } from '@/lib/typography'

// "EN · NL · FR": the same page with the same parameters in another language (L9). Only the languages this build routes,
// never the pseudo-language; with one such language (the English production until Task 15) there is no switch at all, so
// nothing on the page changes. A plain link, so the other language's page loads whole (its <html lang>, its words) and
// English keeps its address without a prefix. The atlas keeps its view in the address through history.replaceState;
// Next keeps useSearchParams in step with it, and a click still reads the address as it is at that moment, so the link
// never carries a view older than the one on screen.
const SHOWN = LOCALES.filter((l) => !l.dev && ROUTED.includes(l.code))

export function LanguageSwitcher({ className }: { className?: string } = {}) {
  // outside Next's router (a panel rendered on its own, in a test) both hooks give null: the switch then points at the page
  // itself, and a click reads the address anyway
  const pathname = usePathname() ?? '/'
  const search = useSearchParams()?.toString() ?? ''
  const { t, loc } = useT('common')
  if (SHOWN.length <= 1) return null
  const fresh = (e: MouseEvent<HTMLAnchorElement>) => {
    const a = e.currentTarget, code = SHOWN.find((l) => l.code === a.dataset.evTo)?.code
    if (code) a.setAttribute('href', switchHref(pathname, window.location.search.slice(1), code, window.location.hash))
  }
  return (
    <span className={className ? `lang ${className}` : 'lang'} role="group" aria-label={plain(t('nav.languages'))}>
      {SHOWN.map((l, i) => (
        <Fragment key={l.code}>
          {i > 0 && <span className="lang-sep" aria-hidden="true">·</span>}
          {/* named in its own language, «Nederlands (NL)»: a bare «EN», «NL» or «FR» is spelt out or read as a word,
              depending on the voice, and names no language. The visible code stays in the name for voice control
              (WCAG 2.5.3; re-check 2 after plan 5) */}
          <a
            href={switchHref(pathname, search, l.code)}
            lang={l.tag}
            hrefLang={l.tag}
            aria-label={`${l.name} (${l.label})`}
            aria-current={l.code === loc ? 'true' : undefined}
            onClick={fresh}
            onAuxClick={fresh}
            data-ev={EV.lang}
            data-ev-to={l.code}
          >
            {l.label}
          </a>
        </Fragment>
      ))}
    </span>
  )
}
