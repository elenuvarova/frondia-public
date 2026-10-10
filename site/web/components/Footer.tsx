import { DEFAULT, keptEnglish, localePath } from '@/i18n/locales'
import { atlasHref } from '@/lib/links'
import { EV } from '@/lib/analytics'
import { getT } from '@/lib/t'
import { plain } from '@/lib/typography'

// its section links lead to the landing's sections (/#law); the landing itself passes home="" so
// they stay same-document (#law)
export async function Footer({ home }: { home?: string }) {
  const { t, rich, loc } = await getT('common')
  home ??= localePath(loc, '/')
  return (
    <footer className="footer night grain">
      <div className="wrap">
        <div className="footer-top">
          <p className="footer-mark">frondia<span className="it">{t('footer.motto')}</span></p>
          <nav className="footer-links" aria-label={plain(t('footer.label'))}>
            <a href={atlasHref(loc)} data-ev={EV.atlas} data-ev-from="footer">{t('footer.links.atlas')}</a>
            <a href={`${home}#law`}>{t('footer.links.law')}</a>
            <a href={`${home}#threshold`}>{t('footer.links.method')}</a>
            <a href={`${home}#cases`}>{t('footer.links.audits')}</a>
            <a href={`${home}#faq`}>{t('footer.links.faq')}</a>
            <a href={localePath(loc, '/data')}>{t('footer.links.data')}</a>
            <a href={localePath(loc, '/register')}>{t('footer.links.register')}</a>
            <a href={localePath(loc, '/privacy')}>{t('footer.links.privacy')}</a>
          </nav>
        </div>
        <div className="footer-grid">
          <div className="footer-about">
            <p className="small">
              {rich('footer.built', { a: (c) => <a href="https://ontwrpn.com/">{c}</a> })}
            </p>
            <p className="small">
              {t('footer.privacy')}
            </p>
            {/* a translated page says who translated it and who has not read it yet (spec §2); English never shows it */}
            {loc !== DEFAULT && <p className="small">{t('footer.translation')}</p>}
          </div>
          {/* the rights holders' credits stay in their own words, English, on every page (same.json) */}
          <p className="small" lang={keptEnglish(loc)}>
            {t('footer.credits')}
          </p>
        </div>
      </div>
    </footer>
  )
}
