import { expect, test } from 'vitest'
import { dropView, isReplaceRepeat, umamiConfig, umamiOrigin, EV } from '@/lib/analytics'

test('no website id, no counter', () => {
  expect(umamiConfig({})).toBeNull()
})

test('the script comes from the site itself; the counts go straight to Umami', () => {
  const c = umamiConfig({ UMAMI_WEBSITE_ID: 'abc', UMAMI_HOST: 'https://stats.frondia.eu' })!
  expect(c.src).toBe('/u/script.js')
  expect(c.hostUrl).toBe('https://stats.frondia.eu')
  expect(c.domains).toBe('frondia.eu')
  expect(c.websiteId).toBe('abc')
})

test('the Umami host is reduced to its origin, with our own as the fallback', () => {
  expect(umamiOrigin({ UMAMI_HOST: 'https://stats.example.org/' })).toBe('https://stats.example.org')
  expect(umamiOrigin({ UMAMI_HOST: 'https://stats.example.org:8443/x/' })).toBe('https://stats.example.org:8443')
  expect(umamiOrigin({})).toBe('https://stats.frondia.eu')
  expect(umamiOrigin({ UMAMI_HOST: 'not a url' })).toBe('https://stats.frondia.eu')
})

test('event names are stable', () => {
  expect(EV).toEqual({ atlas: 'atlas-open', audit: 'audit-open', faq: 'faq-open', lang: 'lang-switch', consent: 'consent', download: 'download' })
})

test('only the tracker script is rewritten to Umami; sends are not proxied', async () => {
  process.env.UMAMI_HOST = 'https://stats.frondia.eu'
  const cfg = (await import('@/next.config')).default as { rewrites?: () => Promise<unknown> }
  const r = JSON.stringify(await cfg.rewrites!())
  expect(r).toContain('"source":"/u/script.js","destination":"https://stats.frondia.eu/script.js"')
  expect(r).toContain('"source":"/u/shared.js","destination":"https://stats.ontwrpn.com/script.js"')
  expect(r).not.toContain('/api/send')
})

const O = 'https://frondia.eu'
test('a page view the atlas causes by rewriting its own address is a repeat; arriving at the atlas is not', () => {
  expect(isReplaceRepeat(`${O}/atlas?city=antwerp`, `${O}/atlas?city=brussels`, O)).toBe(true)
  expect(isReplaceRepeat('/atlas?city=antwerp&q=need', '/atlas?city=antwerp', O)).toBe(true)        // older trackers send paths
  expect(isReplaceRepeat(`${O}/nl/atlas?city=gent`, `${O}/nl/atlas`, O)).toBe(true)
  expect(isReplaceRepeat(`${O}/atlas?city=brussels`, '', O)).toBe(false)                            // first view, no referrer
  expect(isReplaceRepeat(`${O}/atlas?city=brussels`, `${O}/`, O)).toBe(false)                       // from the landing
  expect(isReplaceRepeat(`${O}/atlas?city=brussels`, 'https://other.example/atlas', O)).toBe(false) // another site's /atlas
  expect(isReplaceRepeat(`${O}/dossier?city=brussels`, `${O}/dossier?city=antwerp`, O)).toBe(false)  // other pages count as before
  expect(isReplaceRepeat(`${O}/dossier?city=brussels`, `${O}/atlas?city=brussels`, O)).toBe(false)
})

test('the edges of a repeat: the same localised atlas, a trailing slash, another locale, a broken address, a hash', () => {
  expect(isReplaceRepeat(`${O}/fr/atlas?city=liege&q=need`, `${O}/fr/atlas?city=liege`, O)).toBe(true)
  // /atlas/ never sits in a history change (the server answers it with a 308 to /atlas, a load of its own): it and
  // /atlas are different paths, so the view counts
  expect(isReplaceRepeat(`${O}/atlas?city=ghent`, `${O}/atlas/?city=ghent`, O)).toBe(false)
  expect(isReplaceRepeat(`${O}/atlas/`, `${O}/atlas/`, O)).toBe(true)
  expect(isReplaceRepeat(`${O}/nl/atlas?city=gent`, `${O}/atlas?city=gent`, O)).toBe(false)      // a language switch counts
  expect(isReplaceRepeat(`${O}/atlas?city=ghent`, 'http://[', O)).toBe(false)                      // an address URL cannot read
  expect(isReplaceRepeat('http://[', `${O}/atlas`, O)).toBe(false)
  expect(isReplaceRepeat(`${O}/atlas?city=ghent`, `${O}/atlas?city=brussels#main`, O)).toBe(true)  // a hash changes nothing
})

test('the data page and the register rewrite their own address too (L10): a city or a filter is not a visit', () => {
  expect(isReplaceRepeat(`${O}/data?city=ghent`, `${O}/data?city=antwerp`, O)).toBe(true)
  expect(isReplaceRepeat(`${O}/nl/register?show=yes`, `${O}/nl/register`, O)).toBe(true)
  expect(isReplaceRepeat(`${O}/register?show=no&checked=1`, `${O}/register?show=no`, O)).toBe(true)
  expect(isReplaceRepeat(`${O}/dossier?sector=b`, `${O}/dossier?sector=a`, O)).toBe(false)       // a link: a visit
  expect(isReplaceRepeat(`${O}/commune?code=21004`, `${O}/commune?code=21001`, O)).toBe(false)
  expect(isReplaceRepeat(`${O}/nl/data`, `${O}/data`, O)).toBe(false)                           // a language switch: a visit
  expect(isReplaceRepeat(`${O}/data?city=ghent`, `${O}/register`, O)).toBe(false)
  expect(isReplaceRepeat(`${O}/data?city=ghent`, '', O)).toBe(false)                            // arriving: a visit
  expect(isReplaceRepeat(`${O}/data?city=ghent`, 'https://other.example/data', O)).toBe(false)
  expect(isReplaceRepeat(`${O}/database`, `${O}/database`, O)).toBe(false)                      // only the three paths
})

test('the filter drops only a repeat page view of the atlas, the data page or the register', () => {
  const repeat = { url: `${O}/atlas?city=antwerp`, referrer: `${O}/atlas?city=brussels` }
  expect(dropView('event', repeat, O)).toBe(true)
  expect(dropView('event', { ...repeat, name: 'audit-open' }, O)).toBe(false)                 // a named event always passes
  expect(dropView('identify', repeat, O)).toBe(false)
  expect(dropView('event', { url: `${O}/atlas?city=antwerp` }, O)).toBe(false)               // the first view: no referrer
  expect(dropView('event', { url: `${O}/atlas?city=antwerp`, referrer: '' }, O)).toBe(false)
  expect(dropView('event', { url: `${O}/dossier?city=antwerp`, referrer: `${O}/atlas?city=antwerp` }, O)).toBe(false)
  expect(dropView('event', {}, O)).toBe(false)
  expect(dropView('event', { url: `${O}/data?city=ghent`, referrer: `${O}/data?city=liege` }, O)).toBe(true)
  expect(dropView('event', { url: `${O}/register?show=yes`, referrer: `${O}/register` }, O)).toBe(true)
  expect(dropView('event', { url: `${O}/register?show=yes`, referrer: `${O}/register`, name: 'download' }, O)).toBe(false)
})

test('the counter names the filter it calls', () => {
  expect(umamiConfig({ UMAMI_WEBSITE_ID: 'x' })?.beforeSend).toBe('frondiaBeforeSend')
})
