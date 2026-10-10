'use client'
import { atlasHref } from '@/lib/links'
import { EV } from '@/lib/analytics'
import { useT } from '@/lib/t-client'

// the data behind the landing did not load (a missing or broken /data file): as the old load-error block.
// Reload is a real reload: Next's reset() only re-renders the cached payload and meets the same error.
export default function ErrorPage() {
  const { t, loc } = useT('landing')
  return (
    <main id="main">
      <section className="section load-error" role="alert">
        <div className="wrap">
          <p className="body">{t('loadError.text')}</p>
          <div className="hero-cta hero-cta--left">
            <button type="button" className="pill pill--ghost" onClick={() => location.reload()}>{t('loadError.reload')}</button>
            <a href={atlasHref(loc)} className="pill pill--ink" data-ev={EV.atlas} data-ev-from="error">{t('loadError.atlas')} <span className="arr">→</span></a>
          </div>
        </div>
      </section>
    </main>
  )
}
