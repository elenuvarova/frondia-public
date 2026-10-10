// The atlas's behaviour in a real browser (plan 4, Task 7; Review Focus 3 and 5), against a running server. Headless;
// only localhost is reached (every other host is aborted, so nothing ever reaches Umami, Clarity or Bing).
//
// 1. A bare /atlas settles on ?city=brussels, "What changed in Brussels".
// 2. The address follows the view without history or the server: ten clicks and keys across the questions, lenses,
//    views, the matched-places switch and the "what if" slider leave history.length as it was, send no document
//    request and no ?_rsc request, and Back leaves the atlas (to the blank start page).
// 3. A quick change of city (Brussels → Antwerp → Ghent, 100 ms apart, Antwerp's file held 1.5 s): Ghent is on
//    screen — heading, address and every one of its sectors — and the late Antwerp answer draws nothing.
// 4. Links into the atlas: a sector of Antwerp opens its card and stays in the address; a Brussels sector in Antwerp
//    is dropped (no card, ?city=antwerp); an audit of Antwerp opens its drawer on "What changed". The head and the view
//    agree (Q15): an audit of Brussels asked for on another question opens on "What changed" and the page's title
//    names it; an audit of Antwerp asked for in Brussels, or an unknown one, opens nothing and leaves the address.
// 5. The keyboard and the pointer: Tab order of the bar (since re-check 2 after the skip link, and the map after it),
//    the audit pin as a link (Enter opens it, also after a drag),
//    a drag that starts on the pin opens nothing, the zoom buttons' names, the photos' split and the "what if" slider
//    as sliders with their value texts.
// 6. No button without a name, and a console free of errors, hydration and CSP warnings, on four views.
// 7. The HTML carries no geometry (A2): /atlas?city=brussels, gzipped, under 40 KB and without the first sector's path.
// 8. Two fingers on a phone (re-check 1): spreading them zooms the map about their midpoint (the viewBox narrows about as
//    much as the fingers part), opens no card, and leaves the page itself unzoomed. Chromium, through CDP touch events.
//    Then a tap on a sector opens its card, and the hover tip (under the bottom sheet on a phone) is not drawn.
// 9. The city's file is downloaded once per visit, in Chromium and in WebKit (re-check 1: an as="fetch" preload is never
//    handed to fetch() by WebKit, so Safari read every city twice). Needs WebKit for playwright-core
//    (node node_modules/playwright-core/cli.js install webkit); without it the step fails and says so.
// 10. A link to an audit or a sector flies the map there without a layout shift (the field photo moves by transform; by
//    left/top it scored a CLS of 1.2–2.4, re-check 1).
// 11. The language switch keeps the view (L9, Review Focus 1). On a build that routes only English (/nl/atlas → 404) the
//    bar has no switch at all. On a preview build: /atlas?city=ghent, three changes of view (the "What's missing"
//    question, its Heat lens, sector 44021A00-), then "NL" in the bar → /nl/atlas with the address the view had before
//    the click; from there "EN" → /atlas with the same address. At 390 the bar's end is hidden and the switch is drawn once,
//    in the bottom sheet's kicker row (design wave, 5 Oct 2026).
// 12. The bar fits on one line at every desktop width (fix round 1 of Task 8): at 861, 900, 1000, 1100 and 1200 px, on
//    /atlas and, on a preview build, on /xx/atlas (the pseudo-language, the longest words), the bar does not scroll
//    sideways (scrollWidth ≤ clientWidth), keeps its height (≤ 47 px) and "How it decides" stays on one line (the English
//    production wrapped it at 861–880 until P5-8).
//
// Usage: node web/scripts/check-atlas.mjs [baseUrl]   (default http://localhost:5181)
// It runs against a server with or without UMAMI_WEBSITE_ID: this script aborts /u/script.js and /api/send, and step 6
// does not count that aborted request's ERR_FAILED as the page's error (final review M3). check-events.mjs is the run
// that lets the counter work.
// Prints ✓/✗ lines only — never a page, request or environment object; the exit code is the number of ✗.
import { chromium, webkit } from 'playwright-core'
import fs from 'node:fs'
import http from 'node:http'
import os from 'node:os'
import path from 'node:path'
import zlib from 'node:zlib'

const base = process.argv[2] || 'http://localhost:5181'
const EXE = path.join(os.homedir(), 'Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
const DATA = path.join(import.meta.dirname, '../public/data')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const nb = (s) => (s || '').replace(/[  ]/g, ' ').replace(/⁠/g, '').trim()
let bad = 0
const ok = (cond, yes, no = yes) => { if (cond) console.log(`✓ ${yes}`); else { bad++; console.log(`✗ ${no}`) } }

const browser = await chromium.launch({ headless: true, executablePath: fs.existsSync(EXE) ? EXE : undefined })
const local = new URL(base).host

// a page that reaches this server only; `hold` delays one file's answer
async function open({ hold } = {}) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } })
  await ctx.addInitScript(() => { try { localStorage.setItem('frondia.consent', JSON.stringify({ choice: 'denied', at: '2026-01-01T00:00:00.000Z', v: 1 })) } catch {} })
  await ctx.route('**/*', async (route) => {
    const u = new URL(route.request().url())
    if (u.host !== local || /^\/(u\/script\.js|api\/send)/.test(u.pathname)) return route.abort()
    if (hold && hold.test(u.pathname)) await sleep(1500)
    return route.continue()
  })
  const page = await ctx.newPage()
  return { page, close: () => ctx.close() }
}
const ready = (page) => page.waitForSelector('.atlas[data-ready="true"] .panel h1', { timeout: 20000 })
const search = (page) => page.evaluate(() => location.search)
const h1 = async (page) => nb(await page.textContent('.panel h1'))

// ---- 1. the bare address ----
{
  const { page, close } = await open()
  await page.goto(base + '/atlas', { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(300)
  const s = await search(page), h = await h1(page)
  ok(s === '?city=brussels' && h === 'What changed in Brussels', '/atlas settles on ?city=brussels, “What changed in Brussels”', `/atlas: ${s} · ${h}`)
  await close()
}

// ---- 2. history and the server ----
{
  const { page, close } = await open()
  await page.goto('about:blank')
  await page.goto(base + '/atlas?city=brussels', { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(300)
  const len0 = await page.evaluate(() => history.length)
  let docs = 0, rsc = 0
  page.on('request', (r) => {
    if (r.resourceType() === 'document') docs++
    if (r.url().includes('_rsc')) rsc++
  })
  const seg = (i) => page.locator('.seg--lens button').nth(i)
  const steps = [
    ['Missing', () => seg(0).click()],
    ['a need lens', () => page.locator('.panel .chips button[aria-pressed="false"]').first().click()],
    ['Place', () => seg(1).click()],
    ['Changed', () => seg(2).click()],
    ['view Communes', () => page.locator('.panel .chips button', { hasText: 'Communes' }).click()],
    ['view Sectors', () => page.locator('.panel .chips button', { hasText: 'Sectors' }).click()],
    ['Subtract matched places off', () => page.locator('.panel .switch').click()],
    ['Subtract matched places on', () => page.locator('.panel .switch').click()],
    ['Place again', () => seg(1).click()],
    ['what if, one key', async () => { await page.locator('.more-range').focus(); await page.keyboard.press('ArrowRight') }],
    ['what if, another key', () => page.keyboard.press('ArrowRight')],
  ]
  const seen = new Set()
  for (const [, act] of steps) {
    await act()
    await sleep(250)
    seen.add(await search(page))
  }
  const len1 = await page.evaluate(() => history.length)
  const last = await search(page)
  ok(seen.size >= 6, `the address followed the view (${seen.size} different addresses over ${steps.length} actions)`)
  ok(/q=place/.test(last) && /n=/.test(last), `the “what if” keys reached the address (${last})`)
  ok(len1 === len0, `history.length unchanged over ${steps.length} actions (${len0})`, `history.length ${len0} → ${len1}`)
  ok(docs === 0 && rsc === 0, 'no document request and no ?_rsc request while the view changed', `documents ${docs}, _rsc ${rsc}`)
  await page.goBack()
  ok(page.url() === 'about:blank', 'Back leaves the atlas for the page before it', `Back went to ${page.url()}`)
  await close()
}

// ---- 3. a quick change of city ----
{
  const { page, close } = await open({ hold: /\/data\/antwerp\.json$/ })
  await page.goto(base + '/atlas?city=brussels', { waitUntil: 'networkidle' })
  await ready(page)
  await page.selectOption('.city-pick select', 'antwerp')
  await sleep(100)
  await page.selectOption('.city-pick select', 'ghent')
  await sleep(3000)
  const ghent = JSON.parse(fs.readFileSync(path.join(DATA, 'ghent.json'), 'utf8')).sectors.length
  const h = await h1(page), s = await search(page)
  const paths = await page.evaluate(() => document.querySelectorAll('.sectors path').length)
  ok(h === 'What changed in Ghent', 'after Brussels → Antwerp → Ghent the heading is Ghent’s', `heading: ${h}`)
  ok(s.startsWith('?city=ghent'), 'the address is Ghent’s', `address: ${s}`)
  ok(paths === ghent, `the map draws Ghent’s ${ghent} sectors, not the late Antwerp`, `the map draws ${paths} sectors (Ghent has ${ghent})`)
  await close()
}

// ---- 4. links into the atlas ----
{
  const { page, close } = await open()
  await page.goto(base + '/atlas?city=antwerp&sector=11001A01-', { waitUntil: 'networkidle' })
  await ready(page)
  await page.waitForSelector('.drawer h2', { timeout: 10000 }).catch(() => {})
  await sleep(500)
  const name = nb(await page.textContent('.drawer h2').catch(() => ''))
  const s1 = await search(page)
  ok(name === 'De Leeuwerik' && s1.includes('sector=11001A01-'), 'a sector of Antwerp opens its card (De Leeuwerik) and stays in the address', `card “${name}”, address ${s1}`)

  await page.goto(base + '/atlas?city=antwerp&sector=21004E72-', { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(500)
  const drawers = await page.locator('.drawer').count(), s2 = await search(page)
  ok(drawers === 0 && s2 === '?city=antwerp', 'a Brussels sector in Antwerp is dropped: no card, ?city=antwerp', `${drawers} card(s), address ${s2}`)

  await page.goto(base + '/atlas?city=antwerp&case=droogdokkenpark', { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(500)
  const aria = await page.getAttribute('.drawer', 'aria-label').catch(() => null)
  const pressed = nb(await page.locator('.seg--lens button[aria-pressed="true"] .long').textContent().catch(() => ''))
  ok(!!aria && /Droogdokkenpark/i.test(aria) && pressed === 'What changed', 'an audit of Antwerp opens its drawer on “What changed”', `drawer ${aria}, pressed ${pressed}`)

  // Q15: what the head says is what opens
  await page.goto(base + '/atlas?case=ninove&q=need', { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(500)
  const ariaN = await page.getAttribute('.drawer', 'aria-label').catch(() => null)
  const pressedN = nb(await page.locator('.seg--lens button[aria-pressed="true"] .long').textContent().catch(() => ''))
  const titleN = nb(await page.title()), sN = await search(page)
  ok(!!ariaN && /Ninove/.test(nb(ariaN)) && pressedN === 'What changed' && titleN.includes('Porte de Ninove') && sN === '?city=brussels&case=ninove',
    'an audit asked for on “What’s missing” opens on “What changed”, and the title names it (Porte de Ninove)',
    `?case=ninove&q=need: drawer ${ariaN}, pressed ${pressedN}, title “${titleN}”, address ${sN}`)

  for (const [at, want] of [['/atlas?city=brussels&case=droogdokkenpark', '?city=brussels'], ['/atlas?city=brussels&case=junk&q=need', '?city=brussels&q=need&lens=services']]) {
    await page.goto(base + at, { waitUntil: 'networkidle' })
    await ready(page)
    await sleep(500)
    const n = await page.locator('.drawer').count(), s = await search(page), title = nb(await page.title())
    ok(n === 0 && s === want && !/Audit/.test(title), `${at.slice(6)}: no drawer, the address is ${want}`, `${at.slice(6)}: ${n} drawer(s), address ${s}, title “${title}”`)
  }
  await close()
}

// ---- 5. the keyboard ----
{
  const { page, close } = await open()
  await page.goto(base + '/atlas?city=brussels', { waitUntil: 'networkidle' })
  await ready(page)
  const order = []
  // a preview build adds the language switch (EN · NL · FR) at the start of the bar's end: three more stops
  const langs = await page.locator('.atlas-bar-end .lang a').count()
  for (let i = 0; i < 8 + langs; i++) {
    await page.keyboard.press('Tab')
    order.push(await page.evaluate(() => {
      const e = document.activeElement
      if (!e) return '?'
      if (e.classList.contains('skip-link')) return 'skip'
      if (e.tagName === 'svg' && e.closest('.atlas-map')) return 'map'
      if (e.classList.contains('wordmark')) return 'wordmark'
      if (e.tagName === 'SELECT' && e.closest('.city-pick')) return 'city'
      if (e.closest('.seg--lens') && e.hasAttribute('aria-pressed')) return 'question'
      if (e.closest('.atlas-bar-end .lang')) return 'lang'
      if (e.closest('.atlas-bar-end')) return 'decides'
      return e.tagName.toLowerCase() + '.' + e.className
    }))
  }
  const want = ['skip', 'wordmark', 'city', 'question', 'question', 'question', ...Array(langs).fill('lang'), 'decides', 'map']
  ok(order.join() === want.join(), `Tab: skip link → wordmark → city → three questions (aria-pressed) → ${langs ? `${langs} languages → ` : ''}How it decides → the map`, `Tab order: ${order.join(' → ')}`)

  // the name is read with its no-break spaces as spaces (the catalogue ties them, as every aria label on the site)
  const pins = page.locator('g.case-pin[role="link"][tabindex="0"]')
  const names = (await pins.evaluateAll((gs) => gs.map((g) => g.getAttribute('aria-label') || ''))).map(nb)
  const at = names.indexOf('Audit: Porte de Ninove')
  ok(at >= 0, 'the Ninove audit pin is a focusable link named “Audit: Porte de Ninove”', `audit pins: ${names.join(', ')}`)
  const pin = pins.nth(Math.max(0, at))
  await pin.focus()
  await page.keyboard.press('Enter')
  await sleep(500)
  const s = await search(page)
  ok(await page.locator('.drawer').count() === 1 && s.includes('case=ninove'), 'Enter on the pin opens the audit', `drawer ${await page.locator('.drawer').count()}, address ${s}`)

  const zoomNames = await page.$$eval('.zoom button', (bs) => bs.map((b) => b.getAttribute('aria-label') || ''))
  ok(zoomNames.length === 3 && zoomNames.every(Boolean), `the three zoom buttons are named (${zoomNames.join(', ')})`)

  // a drag of the map, then Enter on a pin: the keyboard is never taken for the end of a drag
  await page.goto(base + '/atlas?city=brussels', { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(300)
  await page.mouse.move(900, 450)
  await page.mouse.down()
  await page.mouse.move(960, 480, { steps: 6 })
  await page.mouse.up()
  await sleep(200)
  const pins2 = page.locator('g.case-pin[role="link"][tabindex="0"]')
  const names2 = (await pins2.evaluateAll((gs) => gs.map((g) => g.getAttribute('aria-label') || ''))).map(nb)
  await pins2.nth(Math.max(0, names2.indexOf('Audit: Porte de Ninove'))).focus()
  await page.keyboard.press('Enter')
  await sleep(500)
  const s2 = await search(page)
  ok(await page.locator('.drawer').count() === 1 && s2.includes('case=ninove'), 'after a drag of the map, Enter on the pin still opens the audit', `after a drag: drawer ${await page.locator('.drawer').count()}, address ${s2}`)

  // a drag that starts on the pin (the map follows the pointer, so it ends there too) opens nothing
  await page.goto(base + '/atlas?city=brussels', { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(300)
  const pins3 = page.locator('g.case-pin[role="link"][tabindex="0"]')
  const names3 = (await pins3.evaluateAll((gs) => gs.map((g) => g.getAttribute('aria-label') || ''))).map(nb)
  const dot = await pins3.nth(Math.max(0, names3.indexOf('Audit: Porte de Ninove'))).locator('circle.case-pin-dot').boundingBox()
  if (dot) {
    const x = dot.x + dot.width / 2, y = dot.y + dot.height / 2
    await page.mouse.move(x, y)
    await page.mouse.down()
    await page.mouse.move(x + 30, y, { steps: 6 })
    await page.mouse.up()
    await sleep(500)
  }
  const s3 = await search(page), n3 = await page.locator('.drawer').count()
  ok(!!dot && n3 === 0 && !s3.includes('case='), 'a drag that starts on the Ninove pin and is released opens no audit', `after a drag from the pin: ${n3} drawer(s), address ${s3}`)

  // an open audit, then "What's missing", then a resize: the view stays on the question asked
  await page.goto(base + '/atlas?case=ninove', { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(500)
  await page.locator('.seg--lens button').nth(0).click()
  await sleep(300)
  await page.setViewportSize({ width: 1200, height: 800 })
  await sleep(900)
  const pressedR = nb(await page.locator('.seg--lens button[aria-pressed="true"] .long').textContent().catch(() => ''))
  const sR = await search(page)
  await page.setViewportSize({ width: 1440, height: 900 })
  ok(pressedR === 'What’s missing' && /q=need/.test(sR) && !sR.includes('case='), 'with an audit open, “What’s missing” then a resize stays on “What’s missing”, the audit gone from the address', `after a resize: pressed “${pressedR}”, address ${sR}`)

  await page.goto(base + '/atlas?city=ghent&view=photos', { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(500)
  const knob = page.locator('.swipe-knob[role="slider"]')
  ok(await knob.count() === 1, 'the photos’ split is a slider')
  if (await knob.count()) {
    await knob.focus()
    const v = async () => [Number(await knob.getAttribute('aria-valuenow')), await knob.getAttribute('aria-valuetext')]
    const [v0] = await v()
    await page.keyboard.press('ArrowRight'); await sleep(100)
    const [v1, t1] = await v()
    ok(v1 === v0 + 2, `ArrowRight moves the split by 2 (${v0} → ${v1})`)
    await page.keyboard.press('End'); await sleep(100)
    const [v2] = await v()
    await page.keyboard.press('Home'); await sleep(100)
    const [v3, t3] = await v()
    ok(v2 !== v1 && v3 !== v2, `End and Home move it to the ends (${v2}, ${v3})`)
    ok(/% of the map shows \d{4}, the rest \d{4}/.test(nb(t1)) && t1 !== t3, `its value text follows (“${nb(t3)}”)`)
  }

  await page.goto(base + '/atlas?city=brussels&q=place', { waitUntil: 'networkidle' })
  await ready(page)
  const range = page.locator('.more-range')
  await range.focus()
  const a = await range.getAttribute('aria-valuetext')
  await page.keyboard.press('ArrowRight'); await sleep(150)
  const b = await range.getAttribute('aria-valuetext')
  ok(!!a && !!b && a !== b, `the “what if” slider’s value text follows the key (“${nb(a)}” → “${nb(b)}”)`)
  await close()
}

// ---- 6. names and the console ----
for (const at of ['/atlas', '/atlas?q=need&lens=services', '/atlas?q=place', '/atlas?city=ghent&view=photos']) {
  const { page, close } = await open()
  const msgs = []
  page.on('console', (m) => {
    const loc = m.location()?.url || ''
    if (loc && new URL(loc, base).host !== local) return   // an aborted outside host (none expected)
    if (/\/u\/script\.js|\/api\/send/.test(loc)) return   // the tracker this script aborts itself (final review M3)
    if (m.type() === 'error' || m.type() === 'warning' || /hydrat|Content Security Policy/i.test(m.text())) msgs.push(`${m.type()}: ${m.text().slice(0, 140)}`)
  })
  page.on('pageerror', (e) => msgs.push(`pageerror: ${String(e.message).slice(0, 140)}`))
  await page.goto(base + at, { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(800)
  const nameless = await page.evaluate(() => [...document.querySelectorAll('button')].filter((b) => !b.textContent.trim() && !b.getAttribute('aria-label')).length)
  ok(nameless === 0, `${at}: every button has a name`, `${at}: ${nameless} button(s) without a name`)
  ok(msgs.length === 0, `${at}: console clean (no errors, hydration or CSP warnings)`, `${at}: ${msgs.join(' | ')}`)
  await close()
}

// ---- 7. no geometry in the HTML ----
{
  const first = JSON.parse(fs.readFileSync(path.join(DATA, 'brussels.json'), 'utf8')).sectors[0].d.slice(0, 40)
  const raw = await new Promise((resolve, reject) => {
    http.get(base + '/atlas?city=brussels', { headers: { 'Accept-Encoding': 'gzip' } }, (res) => {
      const chunks = []
      res.on('data', (c) => chunks.push(c))
      res.on('end', () => resolve({ body: Buffer.concat(chunks), enc: res.headers['content-encoding'] || '' }))
    }).on('error', reject)
  })
  const html = (raw.enc === 'gzip' ? zlib.gunzipSync(raw.body) : raw.body).toString('utf8')
  const kb = Math.round(raw.body.length / 102.4) / 10
  ok(raw.enc === 'gzip' && raw.body.length < 40 * 1024, `the HTML of /atlas?city=brussels is ${kb} KB gzipped (< 40 KB)`, `the HTML is ${kb} KB (${raw.enc || 'not gzipped'})`)
  ok(!html.includes(first), 'the HTML holds no sector geometry (the first sector’s path is not in it)')
}

// ---- 8. a pinch on a phone ----
{
  const ctx = await browser.newContext({ viewport: { width: 390, height: 760 }, hasTouch: true, isMobile: true })
  await ctx.addInitScript(() => { try { localStorage.setItem('frondia.consent', JSON.stringify({ choice: 'denied', at: '2026-01-01T00:00:00.000Z', v: 1 })) } catch {} })
  await ctx.route('**/*', (route) => { const u = new URL(route.request().url()); return u.host !== local || /^\/(u\/script\.js|api\/send)/.test(u.pathname) ? route.abort() : route.continue() })
  const page = await ctx.newPage()
  await page.goto(base + '/atlas?city=brussels', { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(900)
  const width = async () => Number((await page.evaluate(() => document.querySelector('.atlas-map svg')?.getAttribute('viewBox') || '0 0 0 0')).split(' ')[2])
  const stage = await page.locator('.atlas-stage').boundingBox()
  const cx = stage.x + stage.width / 2, cy = stage.y + stage.height * 0.3
  const fingers = (d) => [{ x: cx - d, y: cy, id: 1 }, { x: cx + d, y: cy, id: 2 }]
  const cdp = await ctx.newCDPSession(page)
  const w0 = await width()
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: fingers(20) })
  for (let d = 25; d <= 80; d += 5) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: fingers(d) }); await sleep(16) }
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  await sleep(400)
  const w1 = await width(), cards = await page.locator('.drawer').count(), scale = await page.evaluate(() => window.visualViewport?.scale ?? 1)
  const k = w0 / w1   // the fingers parted ×4
  // a tap on a sector: its card opens, and no hover tip shows beside it (the tip lives under the bottom sheet)
  await page.touchscreen.tap(cx, cy)
  await sleep(700)
  const tips = await page.locator('.atlas-tip').evaluateAll((els) => els.filter((e) => e.getClientRects().length).length)
  ok(tips === 0 && await page.locator('.drawer').count() === 1, 'a tap on a sector opens its card, with no hover tip beside it', `a tap on a sector: ${await page.locator('.drawer').count()} card(s), ${tips} tip(s) on screen`)
  ok(k > 3 && k < 5 && cards === 0 && scale === 1, `two fingers spread ×4 zoom the map ×${k.toFixed(2)}, open no card, leave the page unzoomed`,
    `a pinch: the map zoomed ×${k.toFixed(2)} (width ${Math.round(w0)} → ${Math.round(w1)}), ${cards} card(s), page scale ${scale}`)
  await ctx.close()
}

// ---- 9. the city's file, once per visit ----
async function readsOf(b, name) {
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } })
  await ctx.addInitScript(() => { try { localStorage.setItem('frondia.consent', JSON.stringify({ choice: 'denied', at: '2026-01-01T00:00:00.000Z', v: 1 })) } catch {} })
  const page = await ctx.newPage()
  let n = 0
  page.on('request', (r) => { const u = new URL(r.url()); if (u.host === local && u.pathname === '/data/ghent.json') n++ })
  // no routing here: an intercepted request would bypass the browser's own matching of an early download
  await page.goto(base + '/atlas?city=ghent', { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(1500)
  ok(n === 1, `${name}: /atlas?city=ghent downloads ghent.json once`, `${name}: /atlas?city=ghent downloads ghent.json ${n} times`)
  await ctx.close()
}
// ---- 10. a flight moves no layout ----
for (const at of ['/atlas?case=ninove', '/atlas?city=antwerp&sector=11001A01-']) {
  const { page, close } = await open()
  await page.addInitScript(() => {
    window.__shift = 0
    new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) window.__shift += e.value }).observe({ type: 'layout-shift', buffered: true })
  })
  await page.goto(base + at, { waitUntil: 'networkidle' })
  await ready(page)
  await sleep(2000)
  const cls = await page.evaluate(() => window.__shift)
  ok(cls < 0.05, `${at.slice(6)}: the flight to it shifts no layout (CLS ${cls.toFixed(3)})`, `${at.slice(6)}: the flight scored a layout shift of ${cls.toFixed(3)}`)
  await close()
}

// ---- 11. the language switch keeps the view ----
{
  const preview = await fetch(base + '/nl/atlas', { redirect: 'manual' }).then((r) => r.status === 200).catch(() => false)
  const { page, close } = await open()
  await page.goto(base + '/atlas?city=ghent', { waitUntil: 'networkidle' })
  await ready(page)
  const links = page.locator('.atlas-bar-end .lang a')
  if (!preview) {
    ok(await page.locator('.lang').count() === 0, 'one language routed: the atlas bar has no language switch', `one language routed, yet the atlas has ${await page.locator('.lang').count()} language switch(es)`)
  } else {
    const labels = await links.allTextContents()
    ok(labels.join(' ') === 'EN NL FR', 'the atlas bar offers EN · NL · FR (no pseudo-language)', `the atlas bar offers: ${labels.join(' ') || 'nothing'}`)
    const SECTOR = '44021A00-'
    await page.locator('.seg--lens button').nth(0).click(); await sleep(400)
    await page.locator('.panel .chips button', { hasText: 'Heat' }).click(); await sleep(400)
    // by its geometry, not its index: the map paints the lightest classes last (round-3 re-check, 6 Oct)
    await page.evaluate(async (id) => { const d = (await (await fetch('/data/ghent.json')).json()).sectors.find((x) => x.id === id)?.d; [...document.querySelectorAll('.sectors path')].find((p) => p.getAttribute('d') === d)?.setAttribute('data-pick', id) }, SECTOR)
    await page.locator(`.sectors path[data-pick="${SECTOR}"]`).dispatchEvent('click')
    await page.waitForSelector('.drawer', { timeout: 10000 }).catch(() => {})
    await sleep(600)
    const view = await search(page)
    const shaped = view.includes('city=ghent') && view.includes('q=need') && view.includes('lens=heat') && view.includes(`sector=${SECTOR}`)
    ok(shaped, `three changes of view put them in the address (${view})`, `after three changes of view the address is ${view}`)
    const cur = await page.locator('.atlas-bar-end .lang a[aria-current="true"]').allTextContents()
    ok(cur.join() === 'EN', 'English is the current language (aria-current)', `aria-current on: ${cur.join() || 'nothing'}`)
    await page.locator('.atlas-bar-end .lang a', { hasText: 'NL' }).click()
    await page.waitForURL((u) => new URL(u).pathname === '/nl/atlas', { timeout: 10000 }).catch(() => {})
    await ready(page).catch(() => {}); await sleep(600)
    let at = await page.evaluate(() => ({ p: location.pathname, s: location.search, lang: document.documentElement.lang }))
    ok(at.p === '/nl/atlas' && at.s === view, `"NL" keeps the view: ${at.p}${at.s} (lang ${at.lang})`, `"NL" went to ${at.p}${at.s}, the view was ${view}`)
    await page.locator('.atlas-bar-end .lang a', { hasText: 'EN' }).click()
    await page.waitForURL((u) => new URL(u).pathname === '/atlas', { timeout: 10000 }).catch(() => {})
    await ready(page).catch(() => {}); await sleep(600)
    at = await page.evaluate(() => ({ p: location.pathname, s: location.search }))
    ok(at.p === '/atlas' && at.s === view, `"EN" from /nl/atlas comes back without a prefix: ${at.p}${at.s}`, `"EN" went to ${at.p}${at.s}, the view was ${view}`)
    await page.setViewportSize({ width: 390, height: 844 }); await sleep(400)
    // the bar's end is hidden on a phone; the switch is in the bottom sheet's kicker row instead (design wave, 5 Oct)
    const shown = await page.locator('.lang').evaluateAll((els) => els.filter((e) => e.getClientRects().length).map((e) => e.closest('.panel-kicker') ? 'sheet' : 'bar'))
    ok(shown.join() === 'sheet', 'at 390 the language switch is in the bottom sheet, not the bar', `at 390 the atlas draws switches in: ${shown.join(', ') || 'nothing'}`)
  }
  await close()
}

// ---- 12. the bar on one line at desktop widths ----
{
  const preview = await fetch(base + '/xx/atlas', { redirect: 'manual' }).then((r) => r.status === 200).catch(() => false)
  const { page, close } = await open()
  const fails = []
  let seen = 0
  for (const at of ['/atlas?city=brussels', ...(preview ? ['/xx/atlas?city=brussels'] : [])]) {
    await page.goto(base + at, { waitUntil: 'networkidle' })
    await ready(page)
    for (const w of [861, 900, 1000, 1100, 1200]) {
      await page.setViewportSize({ width: w, height: 900 }); await sleep(300)
      const r = await page.evaluate(() => {
        const bar = document.querySelector('.atlas-bar')
        const end = [...document.querySelectorAll('.atlas-bar-end > a')].pop()
        return { sw: bar.scrollWidth, cw: bar.clientWidth, h: Math.round(bar.getBoundingClientRect().height), lines: end ? end.getClientRects().length : 0,
          right: end ? Math.round(end.getBoundingClientRect().right) : 0, vw: innerWidth }
      })
      seen++
      if (r.sw > r.cw || r.h > 47 || r.lines !== 1 || r.right > r.vw) fails.push(`${at} @${w}: scroll ${r.sw}/${r.cw}, height ${r.h}, "How it decides" on ${r.lines} line(s), right edge ${r.right}/${r.vw}`)
    }
  }
  ok(fails.length === 0, `the bar fits on one line at 861–1200 px (${seen} views${preview ? ', /xx/atlas included' : ''})`, `the bar breaks: ${fails.join(' · ')}`)
  await close()
}

await readsOf(browser, 'Chromium')
const wk = await webkit.launch({ headless: true }).catch(() => null)
if (wk) { await readsOf(wk, 'WebKit'); await wk.close() }
else ok(false, '', 'WebKit is not installed for playwright-core: node node_modules/playwright-core/cli.js install webkit')

await browser.close()
console.log(bad ? `\n${bad} failed` : '\nall passed')
process.exit(bad)
