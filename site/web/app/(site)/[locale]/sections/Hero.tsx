import { PhotoRustle } from '@/components/PhotoRustle'
import { atlasHref } from '@/lib/links'
import { EV } from '@/lib/analytics'
import { getT } from '@/lib/t'
import { plain } from '@/lib/typography'
import { LILAC, LILAC_PHONE, inWords } from './words'

/* The top is layout 1, "Rustle", as approved on the concept board (Figma 165:4): the cream card on a
   photograph of a lilac bush in the wind. The kicker names the whole atlas (three questions); the
   title keeps the one only Frondia answers. The lede is two sentences: the numbers it once carried are the proof band's,
   right below (9 Oct: six lines of figures on the card were too many). */
export async function Hero({ cities }: { cities: number }) {
  const { t, rich, raw, loc } = await getT('landing')
  return (
    <PhotoRustle photo={LILAC} phone={LILAC_PHONE} className="hero-rustle" pauseLabel={plain(t('hero.pause'))}>
      <div className="rustle-card">
        <p className="label">{t('hero.kicker', { count: inWords(raw<string[]>('words'), cities).toLowerCase() })}</p>
        <h1 className="rustle-title">{rich('hero.title', { em: (c) => <em>{c}</em> })}</h1>
        <p className="small rustle-lede">{t('hero.lede')}</p>
        <div className="hero-cta">
          <a href={atlasHref(loc)} className="pill pill--ink" data-ev={EV.atlas} data-ev-from="hero">{t('cta.atlas')} <span className="arr">→</span></a>
          <a href="#threshold" className="pill pill--ghost">{t('cta.decides')}</a>
        </div>
      </div>
      <p className="mono rustle-caption">{t('hero.caption')}</p>
    </PhotoRustle>
  )
}
