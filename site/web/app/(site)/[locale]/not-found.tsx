import { Nav } from '@/components/Nav'
import { PhotoRustle } from '@/components/PhotoRustle'
import { Link } from '@/i18n/navigation'
import { EV } from '@/lib/analytics'
import { atlasHref } from '@/lib/links'
import { getT } from '@/lib/t'
import { plain } from '@/lib/typography'
import { LILAC, LILAC_PHONE } from './sections/words'

/* The 404 (10 Oct 2026). References (Mobbin): YLLW and Rivian — one huge number over a full-bleed photograph, a line and
   a button under it; Amplemarket — the number out of focus. Here the blur is the site's own metaphor: the address is
   rustle, not growth, so its number rustles behind the hero's cream card, on the hero's own photograph. The number is
   decoration (aria-hidden); the heading says it in words, and the card offers the two ways back. One screen, no footer
   and no scroll (Elena, 10 Oct): the number and the card shrink with the screen's height. */
export default async function NotFound() {
  const { t, rich } = await getT('common')
  const landing = await getT('landing')
  return (
    <>
      <Nav tone="field" />
      <main id="main">
        <PhotoRustle photo={LILAC} phone={LILAC_PHONE} className="hero-rustle nf" pauseLabel={plain(landing.t('hero.pause'))}>
          <p className="nf-num" aria-hidden="true"><span>4</span><span>0</span><span>4</span></p>
          <div className="rustle-card nf-card">
            <p className="label">{t('notFound.kicker')}</p>
            <h1 className="rustle-title">{rich('notFound.heading', { em: (c) => <em>{c}</em> })}</h1>
            <p className="small rustle-lede">{t('notFound.lede')}</p>
            <div className="hero-cta">
              <a href={atlasHref(landing.loc)} className="pill pill--ink" data-ev={EV.atlas} data-ev-from="404">{landing.t('cta.atlas')} <span className="arr">→</span></a>
              <Link href="/" className="pill pill--ghost">{t('notFound.home')}</Link>
            </div>
          </div>
          <p className="mono rustle-caption">{landing.t('hero.caption')}</p>
        </PhotoRustle>
      </main>
    </>
  )
}
