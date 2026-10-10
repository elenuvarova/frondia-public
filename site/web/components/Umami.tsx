import Script from 'next/script'
import { SHARED_UMAMI as S, umamiConfig } from '@/lib/analytics'
import { Events } from './Events'

// No UMAMI_WEBSITE_ID — no counter at all, in local runs and previews. The nonce comes from the
// per-request CSP (proxy.ts); next/script does not read it from the response header on its own.
// The script is served from this site (/u/script.js); data-host-url is Umami's own origin, where
// the counts go directly; data-before-send names the filter Events installs (it drops the views the
// atlas's own address changes would add). Events (the data-ev clicks and the FAQ) ride on the same counter.
export function Umami({ nonce }: { nonce?: string }) {
  const c = umamiConfig()
  if (!c) return null
  return (
    <>
      <Script src={c.src} strategy="afterInteractive" nonce={nonce}
              data-website-id={c.websiteId} data-host-url={c.hostUrl}
              data-domains={c.domains} data-do-not-track="true"
              data-before-send={c.beforeSend} />
      {/* the shared dashboard's counter (lib/analytics SHARED_UMAMI): same options, loaded after ours (lazyOnload) so
          window.umami, and with it the click events, stays ours */}
      <Script src={S.src} strategy="lazyOnload" nonce={nonce}
              data-website-id={S.websiteId} data-host-url={S.hostUrl}
              data-domains={S.domains} data-do-not-track="true"
              data-before-send={S.beforeSend} />
      <Events />
    </>
  )
}
