// A stand-in for Umami's tracker, for scripts/check-events.mjs (plan 5 fix wave). The live https://stats.frondia.eu/script.js
// answers 302 to scripts, and Umami's own script is not vendored here (its licence is not ours to copy), so this tiny server
// on 127.0.0.1 serves a stub with the parts of the tracker the site and its checks rely on, and nothing else:
//   - the script tag's data-website-id, data-host-url, data-domains, data-do-not-track and data-before-send;
//   - a page view on load and on every pushState / replaceState that changes the address, whose referrer is the previous
//     address (the first view's is document.referrer unless it is this site), as Umami's tracker does;
//   - window.umami.track(name, data): one event; every send is POST <data-host-url>/api/send with {type: 'event',
//     payload: {website, hostname, language, screen, title, url, referrer, name?, data?}}, after window[data-before-send]
//     (a null return drops it), with keepalive and without credentials, so nothing waits for the answer;
//   - no send at all off the listed domains or with Do Not Track on.
// check-events intercepts every POST to …/api/send in the browser, so no count ever leaves the page; this server answers
// one anyway (204) and logs it, so a send that got past the interception would show.
//
// Usage: node web/scripts/serve-umami-stub.mjs [port]   (default 5185, on 127.0.0.1; HOST overrides the address)
// then start the site with UMAMI_WEBSITE_ID=test-id UMAMI_HOST=http://127.0.0.1:5185 (a Docker Desktop container:
// UMAMI_HOST=http://host.docker.internal:5185, which reaches the host's 127.0.0.1). Stop it with Ctrl-C or by its port
// (lsof -ti:5185).
import http from 'node:http'

const port = Number(process.argv[2] || 5185)
const host = process.env.HOST || '127.0.0.1'

const TRACKER = `(() => {
  const script = document.currentScript
  if (!script) return
  const attr = (k) => script.getAttribute('data-' + k)
  const website = attr('website-id')
  const endpoint = (attr('host-url') || location.origin).replace(/\\/$/, '') + '/api/send'
  const domains = (attr('domains') || '').split(',').map((d) => d.trim()).filter(Boolean)
  const dnt = attr('do-not-track') === 'true' && (navigator.doNotTrack === '1' || window.doNotTrack === '1')
  const beforeSend = attr('before-send')
  const off = () => !website || dnt || (domains.length > 0 && !domains.includes(location.hostname))
  let url = location.href
  let referrer = document.referrer.startsWith(location.origin) ? '' : document.referrer
  const payload = () => ({ website, hostname: location.hostname, language: navigator.language, screen: screen.width + 'x' + screen.height, title: document.title, url, referrer })
  const send = (body, type = 'event') => {
    if (off()) return
    const filter = beforeSend && typeof window[beforeSend] === 'function' ? window[beforeSend] : null
    const p = filter ? filter(type, body) : body
    if (!p) return
    fetch(endpoint, { method: 'POST', body: JSON.stringify({ type, payload: p }), headers: { 'Content-Type': 'application/json' }, credentials: 'omit', keepalive: true }).catch(() => {})
  }
  const track = (name, data) => typeof name === 'string' ? send({ ...payload(), name, data }) : send(payload())
  const moved = (to) => {
    if (!to) return
    const next = new URL(to, location.href).toString()
    if (next === url) return
    referrer = url
    url = next
    setTimeout(() => track(), 300)
  }
  for (const m of ['pushState', 'replaceState']) {
    const orig = history[m]
    history[m] = function (state, title, to) { moved(to); return orig.apply(this, arguments) }
  }
  window.umami = { track, identify: () => {} }
  const first = () => { if (document.readyState === 'complete') { document.removeEventListener('readystatechange', first); track() } }
  if (document.readyState === 'complete') track(); else document.addEventListener('readystatechange', first)
})()
`

let sends = 0
const server = http.createServer((req, res) => {
  const path = new URL(req.url || '/', 'http://stub').pathname
  if (req.method === 'GET' && path === '/script.js') {
    res.writeHead(200, { 'content-type': 'application/javascript; charset=utf-8', 'cache-control': 'no-store' })
    res.end(TRACKER)
    console.log('GET /script.js')
    return
  }
  if (req.method === 'POST' && path === '/api/send') {
    sends++
    console.log(`POST /api/send reached the stub (${sends}); check-events should have intercepted it`)
    res.writeHead(204, { 'access-control-allow-origin': '*' })
    res.end()
    return
  }
  res.writeHead(404, { 'content-type': 'text/plain' })
  res.end('not found')
})
server.listen(port, host, () => console.log(`Umami stub on http://${host}:${port}/script.js`))
for (const sig of ['SIGINT', 'SIGTERM']) process.on(sig, () => server.close(() => process.exit(0)))
