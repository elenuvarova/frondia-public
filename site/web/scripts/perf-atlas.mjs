// The atlas's performance budget (plan 4, Task 10): the old Vite atlas against the new one, same browser, same profile.
//
// Headless Chrome through CDP, 5 runs per address in a fresh context with the HTTP cache disabled, medians reported.
//   390 px  — the mobile Lighthouse profile: CPU ×4 slower, 1.6 Mbit/s down, 750 kbit/s up, RTT 150 ms;
//   1440 px — no CPU slowdown, 10 Mbit/s both ways, RTT 40 ms.
// LCP is the last buffered `largest-contentful-paint` entry, read 1 s after `.panel h1` is on screen (and, on a view
// that shows the field photo, once that photo is complete — on the slow profile it lands seconds later). Chrome does not
// always report the field photo (`img.sector-field`, the same element on both sites) as a candidate on the old atlas —
// some runs stop at the credit line's <p> though the photo is painted later — so each run also records the first
// animation frame in which that photo is complete, and the budget compares LCP* = max(LCP entry, photo complete):
// the moment the map's main picture is really there, measured the same way on both sites. Raw LCP is printed too, and
// so is the wall time from navigation to the panel's heading (`.panel h1`), the words a phone reader waits for (Q14).
// Bytes are the sum of `encodedDataLength` (Network.loadingFinished) per resource type — Script, Document — and, by
// address, everything under /data/ (the new atlas preloads the city's JSON, which Chrome types "Other", not "Fetch").
//
// Budget (exit code = number of breaches):
//   JS   (Script, compressed) of the new atlas ≤ 230 KB on every address;
//   HTML (Document, compressed) of the new atlas ≤ 40 KB on every address (A2: no data in the HTML);
//   LCP* of the new atlas ≤ LCP* of the old × 1.15 on every address, at both widths;
//   the landing's HTML (/, /nl, /fr: the only pages that carry maps in their HTML) ≤ 2 MiB raw and ≤ 480 KiB gzip -9 on
//   the new base (round-3 re-check, 6 Oct: the light classes' edges drawn as a second copy of their paths, and the whole
//   city package sent again as the maps' props, had brought it to 2.62 MB / 591 KB; 3 Oct 2.48 MB / 556 KB; after the
//   fix 1.94 MB / 464 KB). Measured from the uncompressed response, so the server's own compression does not matter.
//
// Only the two bases' hosts are reached: every other host is aborted, and so is anything that looks like analytics
// (Umami's script and /api/send, Clarity), so no run ever counts as a visit. Consent is stored as "denied" up front
// on both sites. Prints numbers and addresses only.
//
// Usage: node web/scripts/perf-atlas.mjs <oldBase> <newBase> [details.json]
//   e.g. node web/scripts/perf-atlas.mjs https://frondia.ontwrpn.com http://localhost:5183
//   [details.json] — optional: every run's numbers and the new atlas's scripts by size, for the report
import { chromium } from 'playwright-core'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import zlib from 'node:zlib'

const [oldBase, newBase, detailsOut] = process.argv.slice(2)
if (!oldBase || !newBase) {
  console.error('Usage: node web/scripts/perf-atlas.mjs <oldBase> <newBase> [details.json]')
  process.exit(2)
}
const EXE = path.join(os.homedir(), 'Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
const RUNS = 5
const BUDGET = { js: 230 * 1024, html: 40 * 1024, lcp: 1.15, landingRaw: 2 * 1024 * 1024, landingGz: 480 * 1024 }
const LANDING = ['/', '/nl', '/fr']
const ADDRESSES = ['/atlas?city=brussels', '/atlas?city=brussels&q=need&lens=services', '/atlas?case=ninove']
const PROFILES = {
  390: {
    viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, cpu: 4,
    net: { latency: 150, downloadThroughput: (1.6 * 1024 * 1024) / 8, uploadThroughput: (750 * 1024) / 8 },
  },
  1440: {
    viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, isMobile: false, hasTouch: false, cpu: 1,
    net: { latency: 40, downloadThroughput: (10 * 1024 * 1024) / 8, uploadThroughput: (10 * 1024 * 1024) / 8 },
  },
}
// the old Vite atlas (tag vite-apps-final) is served at /atlas/ only; a Next base answers /atlas/ with a 308 to the same view
const oldPath = (p) => p.replace(/^\/atlas(?=\?|$)/, '/atlas/')
const ANALYTICS = /(^|\/)(u\/)?script\.js$|\/api\/send|clarity|umami|bing/i
const median = (xs) => { const s = [...xs].sort((a, b) => a - b); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2 }
const kb = (b) => (b / 1024).toFixed(1)

const browser = await chromium.launch({ headless: true, executablePath: fs.existsSync(EXE) ? EXE : undefined })

async function run(base, address, width) {
  const p = PROFILES[width]
  const host = new URL(base).host
  const ctx = await browser.newContext({ viewport: p.viewport, deviceScaleFactor: p.deviceScaleFactor, isMobile: p.isMobile, hasTouch: p.hasTouch })
  await ctx.addInitScript(() => {
    try { localStorage.setItem('frondia.consent', JSON.stringify({ choice: 'denied', at: '2026-01-01T00:00:00.000Z', v: 1 })) } catch {}
    // the first frame in which the field photo is decoded and laid out
    window.__field = null
    const tick = () => {
      const i = document.querySelector('img.sector-field')
      if (i && i.complete && i.naturalWidth && i.getBoundingClientRect().width) { window.__field = performance.now(); return }
      requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  })
  await ctx.route((u) => u.host !== host || ANALYTICS.test(u.pathname), (route) => route.abort())
  const page = await ctx.newPage()
  const cdp = await ctx.newCDPSession(page)
  await cdp.send('Network.enable')
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true })
  await cdp.send('Network.emulateNetworkConditions', { offline: false, ...p.net })
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: p.cpu })
  const types = new Map()
  const urls = new Map()
  const bytes = { Script: 0, Document: 0, Data: 0 }
  const scripts = []
  cdp.on('Network.responseReceived', (e) => { types.set(e.requestId, e.type); urls.set(e.requestId, e.response.url) })
  cdp.on('Network.loadingFinished', (e) => {
    const t = types.get(e.requestId)
    if (t === 'Script' || t === 'Document') bytes[t] += e.encodedDataLength
    if (/\/data\/[^/]+\.json$/.test(new URL(urls.get(e.requestId) || 'http://x/').pathname)) bytes.Data += e.encodedDataLength
    if (t === 'Script') scripts.push({ path: new URL(urls.get(e.requestId)).pathname, bytes: e.encodedDataLength })
  })
  const t0 = Date.now()
  await page.goto(base + address, { waitUntil: 'commit', timeout: 120000 })
  await page.waitForSelector('.panel h1', { timeout: 120000 })
  const h1At = Date.now() - t0
  await page.waitForTimeout(1000)
  // a view with the field photo is not "there" until the photo is: on the slow profile it takes seconds after the heading
  if (await page.$('img.sector-field')) await page.waitForFunction(() => window.__field != null, null, { timeout: 120000 })
  const lcp =await page.evaluate(() => new Promise((resolve) => {
    new PerformanceObserver((list) => {
      const es = list.getEntries(); const e = es[es.length - 1]
      resolve({ t: e.startTime, el: e.element ? e.element.tagName.toLowerCase() : '', url: e.url ? new URL(e.url).pathname : '' })
    }).observe({ type: 'largest-contentful-paint', buffered: true })
    setTimeout(() => resolve({ t: NaN, el: '', url: '' }), 3000)
  }))
  const field = await page.evaluate(() => window.__field)
  await ctx.close()
  return { lcp: lcp.t, field, lcpStar: Math.max(lcp.t, field ?? 0), lcpEl: lcp.el, lcpUrl: lcp.url, h1At, js: bytes.Script, html: bytes.Document, data: bytes.Data, scripts }
}

const rows = []
const details = []
let bad = 0
// the landing's HTML: raw bytes and gzip -9 of them, both bases; the budget holds for the new one
const landing = async (base, p) => {
  const r = await fetch(base + p, { headers: { 'accept-encoding': 'identity' }, redirect: 'manual' })
  const b = Buffer.from(await r.arrayBuffer())
  return { status: r.status, raw: b.length, gz: zlib.gzipSync(b, { level: 9 }).length }
}
for (const p of LANDING) {
  const o = await landing(oldBase, p), n = await landing(newBase, p)
  const ok = n.status === 200 && n.raw <= BUDGET.landingRaw && n.gz <= BUDGET.landingGz
  bad += !ok
  console.log(`${ok ? '✓' : '✗'} landing ${p}  HTML ${kb(o.raw)} → ${kb(n.raw)} KB raw${n.raw <= BUDGET.landingRaw ? '' : ' > 2048'}  ${kb(o.gz)} → ${kb(n.gz)} KB gzip${n.gz <= BUDGET.landingGz ? '' : ' > 480'}${n.status === 200 ? '' : ` (status ${n.status})`}`)
}
for (const width of [390, 1440]) {
  for (const address of ADDRESSES) {
    const res = {}
    const sides = [['old', oldBase, oldPath(address)], ['new', newBase, address]]
    const runs = { old: [], new: [] }
    // old and new alternate, each run in a fresh context, so a slow minute of the network hits both
    for (let i = 0; i < RUNS; i++) for (const [side, base, addr] of sides) runs[side].push(await run(base, addr, width))
    for (const [side, , addr] of sides) {
      const rs = runs[side]
      const fields = rs.map((r) => r.field).filter((f) => f != null)
      res[side] = {
        lcp: median(rs.map((r) => r.lcp)), h1: median(rs.map((r) => r.h1At)), lcpStar: median(rs.map((r) => r.lcpStar)), field: fields.length ? median(fields) : null,
        js: median(rs.map((r) => r.js)), html: median(rs.map((r) => r.html)), data: median(rs.map((r) => r.data)),
        photoAsLcp: rs.filter((r) => /field/.test(r.lcpUrl)).length,
      }
      details.push({ side, width, address: addr, runs: rs })
    }
    const o = res.old, n = res.new
    const lcpOk = n.lcpStar <= o.lcpStar * BUDGET.lcp, jsOk = n.js <= BUDGET.js, htmlOk = n.html <= BUDGET.html
    bad += !lcpOk + !jsOk + !htmlOk
    rows.push({ width, address, o, n, lcpOk, jsOk, htmlOk })
    console.log(`${lcpOk && jsOk && htmlOk ? '✓' : '✗'} @${width} ${address}  LCP* ${Math.round(o.lcpStar)} → ${Math.round(n.lcpStar)} ms (×${(n.lcpStar / o.lcpStar).toFixed(2)}${lcpOk ? '' : ' > 1.15'})  JS ${kb(o.js)} → ${kb(n.js)} KB${jsOk ? '' : ' > 230'}  HTML ${kb(o.html)} → ${kb(n.html)} KB${htmlOk ? '' : ' > 40'}`)
  }
}
await browser.close()

const ms = (x) => (x == null ? '—' : String(Math.round(x)))
console.log('\n| width | address | LCP* old ms | LCP* new ms | ratio | panel h1 old / new ms | raw LCP old / new ms | photo complete old / new ms | photo reported as LCP old / new (of 5) | JS old / new KB | HTML old / new KB | /data old / new KB |')
console.log('|---|---|---|---|---|---|---|---|---|---|---|---|')
for (const r of rows) {
  console.log(`| ${r.width} | \`${r.address}\` | ${ms(r.o.lcpStar)} | ${ms(r.n.lcpStar)}${r.lcpOk ? '' : ' ✗'} | ${(r.n.lcpStar / r.o.lcpStar).toFixed(2)} | ${ms(r.o.h1)} / ${ms(r.n.h1)} | ${ms(r.o.lcp)} / ${ms(r.n.lcp)} | ${ms(r.o.field)} / ${ms(r.n.field)} | ${r.o.photoAsLcp} / ${r.n.photoAsLcp} | ${kb(r.o.js)} / ${kb(r.n.js)}${r.jsOk ? '' : ' ✗'} | ${kb(r.o.html)} / ${kb(r.n.html)}${r.htmlOk ? '' : ' ✗'} | ${kb(r.o.data)} / ${kb(r.n.data)} |`)
}
if (detailsOut) fs.writeFileSync(detailsOut, JSON.stringify(details, null, 1))
console.log(`\n${bad} breach${bad === 1 ? '' : 'es'} of the budget (JS ≤ 230 KB, HTML ≤ 40 KB, LCP* ≤ old × 1.15, landing HTML ≤ 2048 KB raw / 480 KB gzip)`)
process.exit(bad)
