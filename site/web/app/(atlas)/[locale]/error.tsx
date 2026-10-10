'use client'
import { localePath } from '@/i18n/locales'
import { useT } from '@/lib/t-client'
import { plain } from '@/lib/typography'

// the atlas's page failed on the server (as the site's app/(site)/[locale]/error.tsx): the atlas's own frame — its bar
// with the wordmark home, and a stage under it (.atlas gives the stage its height: a bare .atlas-stage is 0 px high) —
// holding the same line and button the atlas shows where its panel goes when the city's file does not load (A8), with
// words from the atlas's own subset. Reload is a real reload: Next's reset() only re-renders the cached payload.
export default function ErrorPage() {
  const { t, loc } = useT('atlas')
  const { t: tc } = useT('common')
  return (
    <div className="atlas">
      <header className="atlas-bar">
        <a href={localePath(loc, '/')} className="wordmark" aria-label={plain(t('bar.home'))}>frondia</a>
      </header>
      <main className="atlas-stage" id="main">
        <section className="panel" role="alert">
          <p className="small">{tc('unavailable')}</p>
          <button type="button" className="link" onClick={() => location.reload()}>{t('reload')}</button>
        </section>
      </main>
    </div>
  )
}
