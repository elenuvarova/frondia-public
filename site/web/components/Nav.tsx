'use client'
import { useEffect, useRef, useState } from 'react'
import { Link } from '@/i18n/navigation'
import { localePath } from '@/i18n/locales'
import { atlasHref } from '@/lib/links'
import { EV } from '@/lib/analytics'
import { useT } from '@/lib/t-client'
import { LanguageSwitcher } from './LanguageSwitcher'
import { plain } from '@/lib/typography'

/* Over the hero the bar is transparent and lies on the field; it turns into a compact paper bar
   the moment it would slide over the hero card (`stickAfter`, a selector), so the wordmark and the
   pill never sit on the card's text (review, 26 Sep). Links follow the page's order. On the landing
   itself the links are same-document (#law), so a query string (?utm…, ?clean) never triggers a
   reload. On a phone the bar keeps Method and Audits and shortens the pill to "Atlas". From 560 px down, with a second
   language routed, the bar has two rows (Elena, 5 Oct): the wordmark and the switch, then every link. The switch is drawn
   twice, once at the end of the links (wider screens) and once after the wordmark (phones), and CSS shows one: the Tab
   order then follows the reading order on both (a moved element would keep its old place in the order). */
export function Nav({
  tone = 'paper',
  cta = true,
  sticky = false,
  stickAfter = null,
}: {
  tone?: 'paper' | 'night' | 'field'
  cta?: boolean
  sticky?: boolean
  stickAfter?: string | null
}) {
  const { t, loc } = useT('common')
  const [stuck, setStuck] = useState(false)
  useEffect(() => {
    if (!sticky) return
    const onScroll = () => {
      const el = stickAfter && document.querySelector(stickAfter)
      setStuck(el ? el.getBoundingClientRect().top < 80 : window.scrollY > window.innerHeight * 0.8)
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onScroll)
    return () => {
      window.removeEventListener('scroll', onScroll)
      window.removeEventListener('resize', onScroll)
    }
  }, [sticky, stickAfter])
  // the bar lies over the page (absolute), so each page starts a fixed distance down (dossier.css, tokens.css, landing.css).
  // A reader's own text spacing (WCAG 1.4.12) can wrap the bar to a third row, and it then covered the page's first line
  // (round-1 re-check, 6 Oct 2026): its height goes to --nav-h, and the pages start at least that far down. The stuck
  // bar (fixed, shorter) is not measured, so scrolling never moves the page
  const bar = useRef<HTMLElement>(null)
  useEffect(() => {
    const el = bar.current, root = document.documentElement
    if (!el) return
    const set = () => { if (!el.classList.contains('is-stuck')) root.style.setProperty('--nav-h', `${Math.ceil(el.getBoundingClientRect().height)}px`) }
    set()
    const ro = new ResizeObserver(set)
    ro.observe(el)
    return () => { ro.disconnect(); root.style.removeProperty('--nav-h') }
  }, [])
  // measured again whenever the bar comes unstuck: its size may have changed while it was stuck (a reader's text spacing
  // applied mid-page) and come back the same, so no resize is seen (round-3 re-check, 6 Oct 2026: the landing's card
  // stayed 28 px under a wrapped bar after a reload mid-page)
  useEffect(() => {
    const el = bar.current
    if (el && !stuck) document.documentElement.style.setProperty('--nav-h', `${Math.ceil(el.getBoundingClientRect().height)}px`)
  }, [stuck])
  const at = sticky ? '' : localePath(loc, '/')
  return (
    <header ref={bar} className={`nav nav--${tone}${sticky ? ' nav--sticky' : ''}${stuck ? ' is-stuck' : ''}`}>
      <div className="wrap">
        <Link href="/" className="wordmark" aria-label={plain(t('nav.home'))}>frondia</Link>
        <LanguageSwitcher className="lang--top" />
        <nav className="nav-links" aria-label={plain(t('nav.main'))}>
          <a href={`${at}#law`} className="nav-wide">{t('nav.law')}</a>
          <a href={`${at}#threshold`}>{t('nav.method')}</a>
          <a href={`${at}#cases`}>{t('nav.audits')}</a>
          {cta && (
            <a href={atlasHref(loc)} className={`pill pill--sm ${tone === 'night' ? 'pill--paper' : 'pill--ink'}`}
               data-ev={EV.atlas} data-ev-from="nav">
              <span className="nav-wide">{t('nav.atlas')}</span><span className="nav-narrow">{t('nav.atlasShort')}</span> <span className="arr">→</span>
            </a>
          )}
          <LanguageSwitcher />
        </nav>
      </div>
    </header>
  )
}
