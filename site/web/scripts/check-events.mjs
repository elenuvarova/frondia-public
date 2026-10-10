// Guards that the site's events are wired and really leave the page. Rendering the landing's async
// server components (getTranslations) fails outside Next's own request context under Vitest, so this
// checks the real rendered page instead, against a running server.
//
// 1. Markup, on the landing and on the document pages that lead into the atlas (/dossier,
//    /commune?code=21001, /data?city=ghent): every <a> whose href goes to /atlas (any locale prefix)
//    carries data-ev="atlas-open" or "audit-open"; nothing still uses Umami's own data-umami-event.
//    On the landing, every FAQ question is also a <details class="faq-item" id="q-…">
//    (components/Events.tsx sends faq-open when one opens).
// 2. Real sends (needs a server started with UMAMI_WEBSITE_ID): the page is opened as http://frondia.eu
//    (mapped onto the server with --host-resolver-rules; every other host fails to resolve, so nothing
//    can reach the real Umami) and every POST to …/api/send is intercepted and answered here. Clicking
//    the text of a FAQ question, an audit link and the hero's "Open the atlas" must each produce
//    exactly one send with the right name and data — and with the send held for 4 s, the hero click
//    must still navigate in under 500 ms (nothing waits for Umami).
// 3. The data page (/data?city=ghent): every file link is a download (download="frondia-<city>-<file>")
//    carrying data-ev="download" with its file and city, and every atlas link carries atlas-open. A
//    click on a CSV sends exactly one `download` {file, city}, the browser really saves the file under
//    its frondia- name, and — with the send held 4 s — the download still starts in under 500 ms.
// 4. The register (/register): its two files (the CSV and the check's JSON, Brussels's) are downloads
//    under their old names carrying data-ev="download" with the file and city brussels; a click on
//    each sends exactly one `download` {file, city} and saves the file.
// 5. The atlas (A6, Review Focus 4), as a real visit on the mapped frondia.eu: landing → the hero's "Open the atlas"
//    → exactly one page view of the atlas; ten changes of view (questions, lenses, views, city and back) → no
//    page view at all, though the address changed every time (the data-before-send filter drops the views Umami
//    makes of replaceState); a drag that starts on the Porte de Ninove pin → nothing; a click on the pin → one
//    audit-open {case: ninove, from: atlas-map}, Enter on it → one more, Enter held down (the key repeating) → one
//    more; the sector card's "Audit: …" → one audit-open {case, from: atlas-passport}, and
//    the page stays; "Dossier for this sector" → exactly one page view, of /dossier; Back to the atlas → at most
//    one (a fresh load counts its first view; a page restored from the back/forward cache sends nothing); the
//    wordmark → one view of the landing; its hero → one view of the atlas again, and more changes of view → none.
//    The filter itself, called on the page: a repeat atlas view and a repeat data-page view → dropped; the first one,
//    other pages' views and named events → passed.
//
// 6. On a server that also has CLARITY_ID (the consent banner is on): the banner is the second Tab stop, after the skip
//    link (re-check 2, WCAG 2.4.3), and with it open no control reached by Tab sits behind it (re-check 1, WCAG 2.4.11);
//    on paper it is not drawn (re-check 5: it printed over every page); without CLARITY_ID the step says it is skipped.
// 7. The data page and the register rewrite their own address (router.replace) and are counted once per visit (L10):
//    landing → the footer's "data" link → two changes of city → the wordmark back: exactly three views, of /, /data?city=…
//    and /; on /register two changes of filter (a tab, the checkbox) → the arrival's view only. On a preview build (where
//    /nl answers 200) the language switch is clicked on /data?city=liege: "FR" sends exactly one lang-switch {to: fr} and
//    exactly one view, of /fr/data?city=liege; on an English-only build no page has a switch.
//
// Usage: node scripts/check-events.mjs [baseUrl]   (default http://localhost:5181)
// Prints strings only — never a whole page, request or environment object.
//
// The tracker, locally: the live stats.frondia.eu/script.js answers 302, and the real script is not vendored. Start the
// stub first, then the server with a fake id pointed at it (from site/; the env -u list is the plan's safety rule):
//   node web/scripts/serve-umami-stub.mjs 5185 &
//   env -u NODE_ENV UMAMI_WEBSITE_ID=test-id CLARITY_ID=test UMAMI_HOST=http://127.0.0.1:5185 npx -w web next start -p 5181
//   node web/scripts/check-events.mjs http://127.0.0.1:5181
// A Docker container (Docker Desktop reaches the host's 127.0.0.1 through host.docker.internal): the same stub, and
// -e UMAMI_HOST=http://host.docker.internal:5185 on docker run. Pass the base as localhost (http://localhost:5186): the
// resolver rules below send every other host, an IP literal too, nowhere. Every POST to …/api/send is intercepted here, so nothing is counted anywhere; the stub
// logs a send that reached it, which should never happen.
import { chromium } from 'playwright-core'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const base = process.argv[2] || 'http://localhost:5181'
const EXE = path.join(os.homedir(), 'Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
let bad = 0
const ok = (cond, yes, no) => { if (cond) console.log(`✓ ${yes}`); else { bad++; console.log(`✗ ${no}`) } }

const target = new URL(base)
const mapTo = `${target.hostname === 'localhost' ? '127.0.0.1' : target.hostname}:${target.port || 80}`
const browser = await chromium.launch({
  headless: true,
  executablePath: fs.existsSync(EXE) ? EXE : undefined,
  args: [`--host-resolver-rules=MAP frondia.eu ${mapTo}, MAP * ~NOTFOUND, EXCLUDE localhost`],
})

// ---- 1. markup ----
const ATLAS_SECTOR = '21004A22-'   // a Brussels sector whose box holds Porte de Ninove: its card links the audit
for (const at of ['/', '/dossier', '/commune?code=21001', '/data?city=ghent', `/atlas?city=brussels&sector=${ATLAS_SECTOR}`]) {
  const page = await browser.newPage()
  await page.goto(base + at, { waitUntil: 'networkidle' })
  if (at.startsWith('/atlas')) await page.waitForSelector('.drawer a[data-ev-from="atlas-passport"]', { timeout: 20000 }).catch(() => {})
  const r = await page.evaluate(() => {
    const atlasRe = /^\/(?:[a-z]{2}\/)?atlas(\?|$)/
    // the atlas bar's own language switch (a preview build) points at the atlas in another language: it counts lang-switch
    const links = [...document.querySelectorAll('a[href]')].filter((a) => atlasRe.test(a.getAttribute('href') || '') && a.getAttribute('data-ev') !== 'lang-switch')
    const badLinks = links.filter((a) => !['atlas-open', 'audit-open'].includes(a.getAttribute('data-ev') || '')).map((a) => a.outerHTML.slice(0, 160))
    const items = [...document.querySelectorAll('details.faq-item')]
    const badItems = items.filter((d) => !/^q-.+/.test(d.id)).map((d) => d.outerHTML.slice(0, 120))
    const legacy = document.querySelectorAll('[data-umami-event]').length
    return { linkCount: links.length, badLinks, itemCount: items.length, badItems, legacy }
  })
  await page.close()
  console.log(`${at}: atlas/audit links checked: ${r.linkCount}; FAQ questions checked: ${r.itemCount}`)
  ok(r.linkCount > 0 && r.badLinks.length === 0, `${at}: every link into the atlas carries data-ev atlas-open or audit-open`,
    r.linkCount === 0 ? `${at}: found no link into the atlas at all` : `${at}: ${r.badLinks.length} link(s) into the atlas carry no event:\n    ${r.badLinks.join('\n    ')}`)
  if (at === '/') {
    ok(r.itemCount > 0 && r.badItems.length === 0, 'every FAQ question is a details.faq-item with an id q-…',
      r.itemCount === 0 ? 'found no FAQ question at all' : `${r.badItems.length} FAQ item(s) without an id q-…`)
  }
  ok(r.legacy === 0, `${at}: nothing uses data-umami-event`, `${at}: ${r.legacy} element(s) still use data-umami-event`)
}

// ---- 2. real sends on a mapped frondia.eu ----
async function context({ delayMs = 0, declined = false } = {}) {
  const sends = []
  const blocked = []
  const ctx = await browser.newContext()
  if (declined) {
    await ctx.addInitScript(() => {
      try { localStorage.setItem('frondia.consent', JSON.stringify({ choice: 'denied', at: new Date().toISOString(), v: 1 })) } catch {}
    })
  }
  await ctx.route('**/*', async (route) => {
    const req = route.request()
    const u = new URL(req.url())
    if (u.pathname.endsWith('/api/send') && req.method() === 'POST') {
      let name = '', data = '{}', url = ''
      try {
        const j = JSON.parse(req.postData() || '{}')
        name = (j.payload && j.payload.name) || ''
        data = JSON.stringify((j.payload && j.payload.data) || {})
        const pu = new URL(String((j.payload && j.payload.url) || ''), 'http://frondia.eu')
        url = pu.pathname + pu.search
      } catch { name = '(unparsable)' }
      sends.push({ host: u.host, name, data, url })
      if (delayMs) await sleep(delayMs)
      await route.fulfill({ status: 200, contentType: 'application/json', headers: { 'access-control-allow-origin': '*' }, body: '{}' }).catch(() => {})
      return
    }
    if (u.hostname === 'frondia.eu') return route.continue()
    blocked.push(u.host)
    return route.abort()
  })
  const page = await ctx.newPage()
  return { ctx, page, sends, blocked }
}

const named = (sends, from) => sends.slice(from).filter((s) => s.name)
async function ready(page, sends, path = '/') {
  await page.goto('http://frondia.eu' + path, { waitUntil: 'networkidle' })
  await page.waitForFunction(() => typeof window.umami === 'object', null, { timeout: 10000 }).catch(() => {})
  for (let i = 0; i < 20 && !sends.some((s) => !s.name); i++) await sleep(250)
  return page.evaluate(() => typeof window.umami)
}

{
  const { ctx, page, sends, blocked } = await context()
  const umami = await ready(page, sends)
  if (umami !== 'object') {
    bad++
    console.log('✗ Umami did not load on http://frondia.eu (was the server started with UMAMI_WEBSITE_ID?)')
  } else {
    ok(sends.some((s) => !s.name), `the page view was sent (to ${sends[0]?.host})`, 'no page view was sent')

    // with the banner open (a server with CLARITY_ID), no link or button reached by Tab is left behind it
    if (await page.locator('.consent-banner').count()) {
      // the banner comes first in the Tab order, right after the skip link (re-check 2, WCAG 2.4.3: it was the last of
      // ~45 stops); then Tab goes on through the page
      const stops = []
      for (let i = 0; i < 2; i++) { await page.keyboard.press('Tab'); await sleep(60); stops.push(await page.evaluate(() => !!document.activeElement?.closest('.consent-banner'))) }
      ok(!stops[0] && stops[1], 'the consent banner is the second Tab stop, after the skip link', `Tab stops 1 and 2 in the banner: ${stops.join(', ')}`)
      let hidden = 0, first = ''
      for (let i = 0; i < 60; i++) {
        await page.keyboard.press('Tab'); await sleep(60)
        const r = await page.evaluate(() => {
          const e = document.activeElement, cb = document.querySelector('.consent-banner')
          if (!e || e === document.body || !cb || cb.contains(e)) return null
          const b = e.getBoundingClientRect(), c = cb.getBoundingClientRect()
          // behind it: the control's whole width under the card's span, and its top below the card's top
          return b.top >= c.top - 1 && b.left >= c.left - 1 && b.right <= c.right + 1 ? (e.textContent || '').trim().slice(0, 40) : null
        })
        if (r) { hidden++; first ||= r }
      }
      ok(hidden === 0, 'with the consent banner open, Tab reaches no control behind it', `${hidden} control(s) reached by Tab sat behind the consent banner (first: “${first}”)`)
      await page.evaluate(() => { document.activeElement?.blur(); scrollTo(0, 0) })
      // re-check 5: a printed page is not asked; the open card printed over the text of every page
      await page.emulateMedia({ media: 'print' })
      const printed = await page.evaluate(() => getComputedStyle(document.querySelector('.consent-banner')).display)
      await page.emulateMedia({ media: 'screen' })
      ok(printed === 'none', 'the open consent banner does not print', `the open consent banner prints (display ${printed})`)
    } else console.log('· the consent banner is not on this server (no CLARITY_ID): its focus step is skipped')

    let mark = sends.length
    if (await page.getByRole('button', { name: 'Decline' }).count()) {
      await page.getByRole('button', { name: 'Decline' }).click(); await sleep(800)
      const ev = named(sends, mark)
      ok(ev.length === 1 && ev[0].name === 'consent' && ev[0].data === '{"choice":"denied"}',
        `Decline: one send, consent ${ev[0]?.data}`, `Decline: ${ev.length} send(s): ${ev.map((s) => s.name + ' ' + s.data).join('; ')}`)
    }

    mark = sends.length
    const q = page.locator('details.faq-item').first()
    const qid = (await q.getAttribute('id')).slice(2)
    const h3 = q.locator('summary h3')
    await h3.scrollIntoViewIfNeeded(); await h3.click(); await sleep(1000)
    const faq = named(sends, mark)
    ok(faq.length === 1 && faq[0].name === 'faq-open' && faq[0].data === JSON.stringify({ id: qid }),
      `FAQ question text: one send, faq-open ${faq[0]?.data} (open=${await q.evaluate((d) => d.open)})`,
      `FAQ question text: ${faq.length} send(s): ${faq.map((s) => s.name + ' ' + s.data).join('; ')}`)

    mark = sends.length
    const audit = page.locator('a[data-ev="audit-open"]').first()
    const slug = await audit.getAttribute('data-ev-case')
    await audit.scrollIntoViewIfNeeded(); await audit.click()
    await page.waitForURL(/\/atlas/, { timeout: 10000, waitUntil: 'commit' }).catch(() => {})
    await sleep(1000)
    const au = named(sends, mark)
    ok(au.length === 1 && au[0].name === 'audit-open' && au[0].data === JSON.stringify({ case: slug }),
      `audit link: one send, audit-open ${au[0]?.data}, then at ${new URL(page.url()).pathname}${new URL(page.url()).search}`,
      `audit link: ${au.length} send(s): ${au.map((s) => s.name + ' ' + s.data).join('; ')}`)
  }
  ok(blocked.length === 0, 'no request left for any other host', `blocked requests to: ${[...new Set(blocked)].join(', ')}`)
  await ctx.close()
}

{
  const { ctx, page, sends, blocked } = await context({ delayMs: 4000, declined: true })
  if (await ready(page, sends) === 'object') {
    const mark = sends.length
    const hero = page.locator('.hero-cta a[data-ev="atlas-open"]').first()
    const t0 = Date.now()
    await hero.click({ noWaitAfter: true })
    await page.waitForURL(/\/atlas/, { timeout: 10000, waitUntil: 'commit' }).catch(() => {})
    const dt = Date.now() - t0
    await sleep(500)
    const ev = named(sends, mark)
    ok(ev.length === 1 && ev[0].name === 'atlas-open' && ev[0].data === '{"from":"hero"}',
      `hero "Open the atlas": one send, atlas-open ${ev[0]?.data}`,
      `hero "Open the atlas": ${ev.length} send(s): ${ev.map((s) => s.name + ' ' + s.data).join('; ')}`)
    ok(/\/atlas/.test(page.url()) && dt < 500, `with the send held 4 s, the click still navigated in ${dt} ms`,
      `with the send held 4 s, navigation took ${dt} ms (url ${page.url()})`)
  } else {
    bad++
    console.log('✗ Umami did not load in the slow-send run')
  }
  ok(blocked.length === 0, 'no request left for any other host (slow run)', `blocked requests to: ${[...new Set(blocked)].join(', ')}`)
  await ctx.close()
}

// ---- 3. the data page: downloads are counted and stay downloads ----
const DATA_CITY = 'ghent'
{
  const page = await browser.newPage()
  await page.goto(`${base}/data?city=${DATA_CITY}`, { waitUntil: 'networkidle' })
  const r = await page.evaluate((city) => {
    const files = [...document.querySelectorAll('a[href*="/downloads/"]')]
    const badFiles = files.filter((a) => {
      const file = (a.getAttribute('href') || '').split('/').pop()
      return a.getAttribute('data-ev') !== 'download' || a.getAttribute('data-ev-file') !== file
        || a.getAttribute('data-ev-city') !== city || a.getAttribute('download') !== `frondia-${city}-${file}`
    }).map((a) => a.outerHTML.slice(0, 200))
    const atlasRe = /^\/(?:[a-z]{2}\/)?atlas(\?|$)/
    const atlas = [...document.querySelectorAll('a[href]')].filter((a) => atlasRe.test(a.getAttribute('href') || ''))
    const badAtlas = atlas.filter((a) => a.getAttribute('data-ev') !== 'atlas-open').map((a) => a.outerHTML.slice(0, 160))
    const fromData = atlas.filter((a) => a.getAttribute('data-ev-from') === 'data').length
    return { fileCount: files.length, badFiles, atlasCount: atlas.length, badAtlas, fromData }
  }, DATA_CITY)
  await page.close()
  console.log(`data page: file links checked: ${r.fileCount}; atlas links checked: ${r.atlasCount}`)
  ok(r.fileCount > 20 && r.badFiles.length === 0, 'every file link is a frondia- download with data-ev download, its file and city',
    r.fileCount <= 20 ? `only ${r.fileCount} file link(s) found` : `${r.badFiles.length} file link(s) wrong:\n    ${r.badFiles.join('\n    ')}`)
  ok(r.badAtlas.length === 0 && r.fromData >= 1, `every atlas link carries atlas-open (${r.fromData} from data)`,
    `${r.badAtlas.length} atlas link(s) without the event, ${r.fromData} from data:\n    ${r.badAtlas.join('\n    ')}`)
}

for (const slow of [false, true]) {
  const { ctx, page, sends, blocked } = await context(slow ? { delayMs: 4000, declined: true } : {})
  const label = slow ? 'data page (send held 4 s)' : 'data page'
  if (await ready(page, sends, `/data?city=${DATA_CITY}`) !== 'object') {
    bad++
    console.log(`✗ Umami did not load on the ${label}`)
  } else {
    if (!slow && await page.getByRole('button', { name: 'Decline' }).count()) {
      await page.getByRole('button', { name: 'Decline' }).click(); await sleep(800)
    }
    const before = page.url()
    const mark = sends.length
    const link = page.locator('a[data-ev="download"][href$=".csv"]').first()
    const file = await link.getAttribute('data-ev-file')
    await link.scrollIntoViewIfNeeded()
    const t0 = Date.now()
    const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 10000 }), link.click({ noWaitAfter: true })])
    const dt = Date.now() - t0
    const saved = await dl.path().catch(() => null)
    const size = saved ? fs.statSync(saved).size : 0
    await sleep(slow ? 500 : 1000)
    const ev = named(sends, mark)
    const d = ev.length === 1 ? JSON.parse(ev[0].data) : {}
    ok(ev.length === 1 && ev[0].name === 'download' && d.file === file && d.city === DATA_CITY && Object.keys(d).length === 2,
      `${label}: CSV click, one send, download ${ev[0]?.data}`,
      `${label}: CSV click, ${ev.length} send(s): ${ev.map((s) => s.name + ' ' + s.data).join('; ')}`)
    ok(dl.suggestedFilename() === `frondia-${DATA_CITY}-${file}` && size > 0,
      `${label}: the file downloaded as ${dl.suggestedFilename()} (${size} bytes)`,
      `${label}: download named ${dl.suggestedFilename()}, ${size} bytes`)
    ok(page.url() === before, `${label}: the page stayed where it was`, `${label}: the page moved to ${page.url()}`)
    if (slow) ok(dt < 500, `${label}: the download started in ${dt} ms`, `${label}: the download took ${dt} ms to start`)
  }
  ok(blocked.length === 0, `no request left for any other host (${label})`, `blocked requests to: ${[...new Set(blocked)].join(', ')}`)
  await ctx.close()
}

// ---- 4. the register: its two files are counted and stay downloads ----
{
  // saved as frondia-brussels-<the file's own name>, as every layer on /data (re-check 3; was register-check.json)
  const want = { 'register.csv': 'frondia-brussels-register.csv', 'register_check.json': 'frondia-brussels-register_check.json' }
  const { ctx, page, sends, blocked } = await context({ declined: true })
  if (await ready(page, sends, '/register') !== 'object') {
    bad++
    console.log('✗ Umami did not load on the register')
  } else {
    const links = await page.evaluate(() => [...document.querySelectorAll('a[href*="/downloads/"]')].map((a) => ({
      href: a.getAttribute('href'), ev: a.getAttribute('data-ev'), file: a.getAttribute('data-ev-file'),
      city: a.getAttribute('data-ev-city'), download: a.getAttribute('download'),
    })))
    const wrong = links.filter((l) => l.ev !== 'download' || l.city !== 'brussels' || want[l.file] !== l.download || l.href !== `/downloads/brussels/${l.file}`)
    ok(links.length === 2 && wrong.length === 0, 'register: both files are downloads with data-ev download, their file and city brussels',
      `register: ${links.length} file link(s), ${wrong.length} wrong: ${wrong.map((l) => `${l.href} ${l.ev} ${l.file} ${l.city} ${l.download}`).join('; ')}`)
    for (const file of Object.keys(want)) {
      const mark = sends.length
      const before = page.url()
      const link = page.locator(`a[data-ev="download"][data-ev-file="${file}"]`)
      const [dl] = await Promise.all([page.waitForEvent('download', { timeout: 10000 }), link.click({ noWaitAfter: true })])
      const saved = await dl.path().catch(() => null)
      const size = saved ? fs.statSync(saved).size : 0
      await sleep(1000)
      const ev = named(sends, mark)
      const d = ev.length === 1 ? JSON.parse(ev[0].data) : {}
      ok(ev.length === 1 && ev[0].name === 'download' && d.file === file && d.city === 'brussels' && Object.keys(d).length === 2,
        `register: ${file} click, one send, download ${ev[0]?.data}`,
        `register: ${file} click, ${ev.length} send(s): ${ev.map((x) => x.name + ' ' + x.data).join('; ')}`)
      ok(dl.suggestedFilename() === want[file] && size > 0, `register: saved as ${dl.suggestedFilename()} (${size} bytes)`,
        `register: download named ${dl.suggestedFilename()}, ${size} bytes`)
      ok(page.url() === before, `register: the page stayed where it was after ${file}`, `register: the page moved to ${page.url()}`)
    }
  }
  ok(blocked.length === 0, 'no request left for any other host (register)', `blocked requests to: ${[...new Set(blocked)].join(', ')}`)
  await ctx.close()
}

// ---- 5. the atlas: one view per visit, the audit counted ----
{
  const { ctx, page, sends, blocked } = await context({ declined: true })
  const views = (from) => sends.slice(from).filter((s) => !s.name)
  const list = (xs) => xs.map((s) => (s.name ? `${s.name} ${s.data}` : `view ${s.url}`)).join('; ') || 'none'
  const atlasReady = () => page.waitForSelector('.atlas[data-ready="true"] .panel h1', { timeout: 20000 })
  const settle = () => sleep(1200)   // Umami sends a history change's view 300 ms after it
  const search = () => page.evaluate(() => location.search)
  if (await ready(page, sends, '/') !== 'object') {
    bad++
    console.log('✗ Umami did not load for the atlas run')
  } else {
    // landing → atlas
    let mark = sends.length
    await page.locator('.hero-cta a[data-ev="atlas-open"]').first().click()
    await page.waitForURL(/\/atlas/, { timeout: 10000 })
    await atlasReady(); await settle()
    let v = views(mark), ev = named(sends, mark)
    ok(v.length === 1 && /^\/atlas/.test(v[0].url) && ev.length === 1 && ev[0].name === 'atlas-open',
      `atlas: arriving from the landing is one view (${v[0]?.url}) and one atlas-open`,
      `atlas: arriving sent ${list(sends.slice(mark))}`)
    const filterOn = await page.evaluate(() => typeof window.frondiaBeforeSend === 'function')
    ok(filterOn, 'atlas: the before-send filter is installed', 'atlas: window.frondiaBeforeSend is missing')

    // ten changes of view
    mark = sends.length
    const seg = (i) => page.locator('.seg--lens button').nth(i)
    const city = async (c) => { await page.selectOption('.city-pick select', c); await atlasReady(); await sleep(300) }
    const steps = [
      () => seg(0).click(),
      () => page.locator('.panel .chips button[aria-pressed="false"]').first().click(),
      () => seg(1).click(),
      () => seg(2).click(),
      () => page.locator('.panel .chips button', { hasText: 'Communes' }).click(),
      () => page.locator('.panel .chips button', { hasText: 'Sectors' }).click(),
      () => city('antwerp'),
      () => seg(0).click(),
      () => city('brussels'),
      () => seg(2).click(),
    ]
    // count what the filter drops, to show the views were made by Umami and refused, not never made
    await page.evaluate(() => {
      const f = window.frondiaBeforeSend
      window.__dropped = 0
      window.frondiaBeforeSend = (type, payload) => { const r = f(type, payload); if (r === null) window.__dropped++; return r }
    })
    let changes = 0, prev = await search()
    const seen = new Set([prev])
    for (const act of steps) { await act(); await sleep(400); const s = await search(); if (s !== prev) changes++; prev = s; seen.add(s) }
    await settle()
    const dropped = await page.evaluate(() => window.__dropped)
    v = views(mark); ev = named(sends, mark)
    ok(changes === steps.length && v.length === 0 && ev.length === 0 && dropped === changes,
      `atlas: ${steps.length} changes of view (${seen.size} addresses, city switched and back): ${dropped} views made by Umami, all dropped, nothing sent`,
      `atlas: ${changes} of ${steps.length} actions changed the address, the filter dropped ${dropped}, sent ${list(sends.slice(mark))}`)

    // the audit pin: a drag from it, a click, Enter, Enter held
    const pin = page.locator('g.case-pin[role="link"]')
    const names = await pin.evaluateAll((gs) => gs.map((g) => (g.getAttribute('aria-label') || '').replace(/[  ⁠]/g, ' ')))
    const ninove = pin.nth(Math.max(0, names.indexOf('Audit: Porte de Ninove')))
    mark = sends.length
    const dot = await ninove.locator('circle.case-pin-dot').boundingBox()
    if (dot) {
      const x = dot.x + dot.width / 2, y = dot.y + dot.height / 2
      await page.mouse.move(x, y); await page.mouse.down(); await page.mouse.move(x + 30, y, { steps: 6 }); await page.mouse.up()
    }
    await settle()
    v = views(mark); ev = named(sends, mark)
    ok(!!dot && ev.length === 0 && v.length === 0 && !(await search()).includes('case='),
      'atlas: a drag that starts on the Porte de Ninove pin sends nothing and opens nothing',
      `atlas: a drag from the pin sent ${list(sends.slice(mark))} (address ${await search()})`)
    mark = sends.length
    await ninove.locator('circle.case-pin-dot').click()
    await settle()
    v = views(mark); ev = named(sends, mark)
    ok(ev.length === 1 && ev[0].name === 'audit-open' && ev[0].data === '{"case":"ninove","from":"atlas-map"}' && v.length === 0
       && (await search()).includes('case=ninove'),
      `atlas: a click on the Porte de Ninove pin opens it and sends one audit-open ${ev[0]?.data}, no view`,
      `atlas: the pin click sent ${list(sends.slice(mark))} (address ${await search()})`)
    mark = sends.length
    await ninove.focus(); await page.keyboard.press('Enter')
    await settle()
    v = views(mark); ev = named(sends, mark)
    ok(ev.length === 1 && ev[0].name === 'audit-open' && ev[0].data === '{"case":"ninove","from":"atlas-map"}' && v.length === 0,
      `atlas: Enter on the pin sends one audit-open ${ev[0]?.data}, no view`, `atlas: Enter on the pin sent ${list(sends.slice(mark))}`)
    // a held key repeats its keydown (event.repeat): the pin opens, and counts, once
    mark = sends.length
    await ninove.focus()
    for (let i = 0; i < 5; i++) { await page.keyboard.down('Enter'); await sleep(40) }
    await page.keyboard.up('Enter')
    await settle()
    v = views(mark); ev = named(sends, mark)
    ok(ev.length === 1 && ev[0].name === 'audit-open' && v.length === 0,
      'atlas: Enter held down on the pin (five keydowns, four repeats) sends one audit-open',
      `atlas: Enter held on the pin sent ${list(sends.slice(mark))}`)

    // the sector card's audit link, then its dossier link
    const pickSector = async () => {
      // by its geometry, not its index: the map paints the lightest classes last (round-3 re-check, 6 Oct)
      await page.evaluate(async (id) => { const d = (await (await fetch('/data/brussels.json')).json()).sectors.find((x) => x.id === id)?.d; [...document.querySelectorAll('.sectors path')].find((p) => p.getAttribute('d') === d)?.setAttribute('data-pick', id) }, ATLAS_SECTOR)
      await page.locator(`.sectors path[data-pick="${ATLAS_SECTOR}"]`).dispatchEvent('click')
      await page.waitForSelector('.drawer a.drawer-dossier', { timeout: 10000 })
    }
    await pickSector(); await settle()
    mark = sends.length
    const before = page.url()
    await page.locator('.drawer a[data-ev-from="atlas-passport"]').click()
    await settle()
    v = views(mark); ev = named(sends, mark)
    ok(ev.length === 1 && ev[0].name === 'audit-open' && ev[0].data === '{"case":"ninove","from":"atlas-passport"}' && v.length === 0
       && new URL(page.url()).pathname === new URL(before).pathname,
      `atlas: the card's "Audit: …" sends one audit-open ${ev[0]?.data}, no view, and stays in the atlas`,
      `atlas: the card's audit link sent ${list(sends.slice(mark))} (at ${page.url()})`)

    await pickSector(); await settle()
    mark = sends.length
    await page.locator('.drawer a.drawer-dossier').click()
    await page.waitForURL(/\/dossier/, { timeout: 10000 })
    await page.waitForLoadState('networkidle'); await settle()
    v = views(mark); ev = named(sends, mark)
    ok(v.length === 1 && v[0].url.startsWith('/dossier') && ev.length === 0,
      `atlas → dossier: exactly one new view (${v[0]?.url})`, `atlas → dossier sent ${list(sends.slice(mark))}`)

    // Back to the atlas
    mark = sends.length
    await page.goBack({ waitUntil: 'load' })
    await atlasReady(); await settle()
    v = views(mark); ev = named(sends, mark)
    ok(v.length <= 1 && v.every((x) => x.url.startsWith('/atlas')) && ev.length === 0,
      `Back to the atlas: ${v.length} view(s) (${v.length ? 'a fresh load counts its first view' : 'restored from the back/forward cache'})`,
      `Back to the atlas sent ${list(sends.slice(mark))}`)

    // the wordmark to the landing, the hero back to the atlas
    mark = sends.length
    await page.locator('.atlas a.wordmark').click()
    await page.waitForURL((u) => new URL(u).pathname === '/', { timeout: 10000 })
    await page.waitForLoadState('networkidle'); await settle()
    v = views(mark); ev = named(sends, mark)
    ok(v.length === 1 && v[0].url === '/' && ev.length === 0, 'atlas → landing by the wordmark: one view of the landing',
      `atlas → landing sent ${list(sends.slice(mark))}`)
    const kept = await page.evaluate(() => {
      const f = window.frondiaBeforeSend, O = location.origin
      if (typeof f !== 'function') return 'missing'
      const p = (url, referrer, name) => ({ url: O + url, referrer: referrer && O + referrer, ...(name ? { name } : {}) })
      return [
        f('event', p('/atlas?city=ghent', '/atlas?city=brussels')) === null,               // repeat → dropped
        f('event', p('/atlas?city=brussels', '')) !== null,                                // first view → kept
        f('event', p('/atlas?city=brussels', '/')) !== null,                               // from the landing → kept
        f('event', p('/', '/atlas?city=brussels')) !== null,                               // another page → kept
        f('event', p('/data?city=ghent', '/data?city=antwerp')) === null,                  // the data page's own change → dropped (L10)
        f('event', p('/atlas?city=ghent', '/atlas?city=brussels', 'audit-open')) !== null, // a named event → kept
        f('identify', p('/atlas?city=ghent', '/atlas?city=brussels')) !== null,            // not a view → kept
      ].join('')
    })
    ok(kept === 'truetruetruetruetruetruetrue', 'the filter drops only a repeat view of the atlas or the data page (7 cases, on the landing)', `the filter answered ${kept}`)

    mark = sends.length
    await page.locator('.hero-cta a[data-ev="atlas-open"]').first().click()
    await page.waitForURL(/\/atlas/, { timeout: 10000 })
    await atlasReady(); await settle()
    await seg(0).click(); await sleep(400); await seg(1).click(); await sleep(400); await seg(2).click()
    await settle()
    v = views(mark); ev = named(sends, mark)
    ok(v.length === 1 && /^\/atlas/.test(v[0].url) && ev.length === 1 && ev[0].name === 'atlas-open',
      `landing → atlas again, three changes of view: one view (${v[0]?.url}) and one atlas-open`,
      `landing → atlas again sent ${list(sends.slice(mark))}`)
  }
  ok(blocked.length === 0, 'no request left for any other host (atlas)', `blocked requests to: ${[...new Set(blocked)].join(', ')}`)
  await ctx.close()
}

// ---- 7. the data page and the register: a visit is one view; the language switch is one event and one view ----
{
  const { ctx, page, sends, blocked } = await context({ declined: true })
  const views = (from) => sends.slice(from).filter((s) => !s.name)
  const list = (xs) => xs.map((s) => (s.name ? `${s.name} ${s.data}` : `view ${s.url}`)).join('; ') || 'none'
  const settle = () => sleep(1200)
  const preview = await fetch(base + '/nl', { redirect: 'manual' }).then((r) => r.status === 200).catch(() => false)
  if (await ready(page, sends, '/') !== 'object') {
    bad++
    console.log('✗ Umami did not load for the data/register run')
  } else {
    if (!preview) ok(await page.locator('.lang').count() === 0, 'one language routed: the landing has no language switch',
      `one language routed, yet the landing has ${await page.locator('.lang').count()} language switch(es)`)
    // landing → /data (the footer's link) → two cities → the wordmark back to the landing
    const mark = 0   // a fresh context: its sends begin with the landing's own first view
    await page.locator('footer a[href="/data"]').first().click()
    await page.waitForURL((u) => new URL(u).pathname === '/data', { timeout: 10000 })
    await page.waitForLoadState('networkidle'); await settle()
    const cityPath = async (c) => {
      await page.selectOption('.city-pick select', c)
      await page.waitForURL((u) => new URL(u).search === `?city=${c}`, { timeout: 10000 }).catch(() => {})
      await page.waitForLoadState('networkidle'); await sleep(500)
    }
    await cityPath('liege'); await cityPath('antwerp'); await settle()
    const atData = await page.evaluate(() => location.pathname + location.search)
    await page.locator('header a.wordmark').first().click()
    await page.waitForURL((u) => new URL(u).pathname === '/', { timeout: 10000 })
    await page.waitForLoadState('networkidle'); await settle()
    const v = views(mark).map((x) => x.url)
    ok(atData === '/data?city=antwerp' && v.length === 3 && v[0] === '/' && /^\/data(\?|$)/.test(v[1]) && v[2] === '/',
      `landing → data → two cities → landing: three views (${v.join(', ')}), the city changes uncounted`,
      `landing → data → two cities (at ${atData}) → landing sent views: ${v.join(', ') || 'none'}`)

    // the register: two changes of filter after arriving
    let m2 = sends.length
    await page.goto('http://frondia.eu/register', { waitUntil: 'networkidle' }); await settle()
    const tab = page.locator('.reg-tabs button[aria-pressed="false"]:not([disabled])').first()
    await tab.click()
    await page.waitForURL((u) => new URL(u).search.includes('show='), { timeout: 10000 }).catch(() => {})
    await page.waitForLoadState('networkidle'); await sleep(500)
    await page.locator('#reg-checked').check()
    await page.waitForURL((u) => new URL(u).search.includes('checked='), { timeout: 10000 }).catch(() => {})
    await page.waitForLoadState('networkidle'); await settle()
    const atReg = await page.evaluate(() => location.search)
    const rv = views(m2)
    ok(atReg.includes('show=') && atReg.includes('checked=') && rv.length === 1 && rv[0].url === '/register' && named(sends, m2).length === 0,
      `register: arriving and two changes of filter (${atReg}) are one view (${rv[0]?.url})`,
      `register: arriving and two filters (${atReg}) sent ${list(sends.slice(m2))}`)

    // the language switch, on a preview build
    if (preview) {
      m2 = sends.length
      await page.goto('http://frondia.eu/data?city=liege', { waitUntil: 'networkidle' }); await settle()
      const arrive = views(m2).length
      m2 = sends.length
      const fr = page.locator('.nav .lang a:visible', { hasText: 'FR' })   // the bar draws the switch twice, one per width (design wave)
      const attrs = await fr.evaluate((a) => `${a.getAttribute('lang')} ${a.getAttribute('hreflang')} ${a.getAttribute('href')}`)
      await fr.click()
      await page.waitForURL((u) => new URL(u).pathname === '/fr/data', { timeout: 10000 }).catch(() => {})
      await page.waitForLoadState('networkidle'); await settle()
      const ev = named(sends, m2), lv = views(m2)
      ok(arrive === 1 && ev.length === 1 && ev[0].name === 'lang-switch' && ev[0].data === '{"to":"fr"}'
         && lv.length === 1 && lv[0].url === '/fr/data?city=liege',
        `/data?city=liege → "FR" (${attrs}): one lang-switch ${ev[0]?.data} and one view of ${lv[0]?.url}`,
        `/data?city=liege → "FR" (${attrs}; arrival ${arrive} view(s)) sent ${list(sends.slice(m2))}`)
    } else console.log('· one language routed: the language-switch send is checked on a preview build')
  }
  ok(blocked.length === 0, 'no request left for any other host (data and register)', `blocked requests to: ${[...new Set(blocked)].join(', ')}`)
  await ctx.close()
}

await browser.close()
process.exit(bad ? 1 : 0)
