// Accessibility, WCAG 2.2 AA (re-check 2 of the Next site, 3 Oct 2026), against a running server. Headless; only
// localhost is reached (every other host is aborted). Each step guards a fix of that round and fails without it.
//
// 1. axe-core (pinned in devDependencies) finds nothing under wcag2a/aa, wcag21a/aa, wcag22aa and best-practice on
//    every page type — landing, privacy, dossier, commune, /data, /register, the 404, five atlas views — and on the
//    atlas with a sector's card, with an audit, at 390 with the bottom sheet, and on the commune page with the finder's
//    list open, at 1440 and 390 (the 404 had no <main>, the dossier two regions with one name).
// 2. The skip link: the first Tab on the landing, a document page and the atlas reaches a visible link to #main; after
//    Enter the next Tab lands inside <main> (2.4.1), and the address and history are as they were (re-check 5: a #main
//    entry let Back put the last city in the atlas's address under the new city's map).
// 3. The 404's heading sits below the bar, not under it (it was read over the wordmark; 2.4.11).
// 4. The commune finder: its active option carries a ring (paper-2 alone was 1.1 : 1; 2.4.7); a Tab out of the field
//    closes the list, which had stayed open over the next controls (2.4.11).
// 5. The atlas's cards and the keyboard (2.4.3): Enter on a list row and on an audit's pin moves focus into the card;
//    Escape closes it and focus goes back to the row or the pin; the card's × by keyboard does the same.
// 6. The map is a keyboard stop (2.1.1): a focusable, described group; an arrow pans it, + zooms it, Enter opens the
//    sector in its middle, Escape brings focus back to the map.
// 7. The open audit's pin shows its focus (it had no dot to ring; 2.4.7), in Chromium and WebKit.
// 8. A phone (390) with a card open: no Tab stop is entirely hidden under a card (the panel's controls were, under the
//    bottom sheet), a pin reached by Tab is flown into view (2.4.11), and every audit pin is a 24-px target (its label
//    was 9 px high; 2.5.8).
// 9. The page's title names the view on screen after a change of question and of city (2.4.2).
// 10. A change of view is said: the status takes the panel's new heading; the counts are a live region (4.1.3).
// 11. Colours (1.4.3, 1.4.11): the atlas's hatch against its ground ≥ 3 : 1; the panel's grey text ≥ 4.5 : 1 even over a
//     black map (the panel is translucent); the credit's plate keeps its grey text ≥ 4.5 : 1 over a black map.
// 12. Reduced motion: an opening card does not slide in.
// 13. Text spacing (1.4.12) at 320: with WCAG's override on the site's pages, nothing runs wider than the screen.
// 14. Print: the skip link is not drawn on paper (re-check 5: fixed, it printed at the foot of every page, over the text).
// 15. Reflow in Safari (1.4.10; re-check 1 after plan 5): in WebKit at 320 and 390 no page is wider than the screen (the
//     Dutch landing scrolled 287 px sideways: a start-aligned paragraph with text-wrap: pretty and soft hyphens took its
//     full 62ch), and in both engines, from 320 to 1440, the commune finder's placeholder fits its field (the head's row
//     shrank the field to 20 characters, and every language's placeholder was cut).
// 16. What a language changes (re-check 2 after plan 5): the English credits (and, since re-check 5, the licences' names
//     on /data) on a Dutch or French page are marked lang="en"
//     (3.1.2); the switcher's links are named by their language, with the visible code in the name (2.5.3); no <option>
//     carries a soft hyphen; at 320, in Chromium and WebKit, with and without text spacing and with every <details> open,
//     no text runs past the screen on /data, /dossier and /register (Safari sized a ≤ 560 px grid by a Dutch paragraph's
//     min-content: /nl/dossier was 2285 px wide, and /nl/data's limits ran 24 px past the screen, cut by html's clip); and
//     the atlas's counts stay in the panel at 320, 340, 1440 and, with text spacing, 390 («en désimperméabilisation» was cut
//     at 320–350 px and from 861 px, 1.4.10), and an Antwerp sector's card does not scroll sideways at 320 and 1440 (the
//     Dutch «voldoet aan een van de twee» ran 23 px out of it).
// 17–21. The design wave (5 Oct 2026), each failing on ac4570d: 17 the phone's two-row bar (320–560: wordmark and
//     EN · NL · FR, then every link; 24-px targets; Tab in reading order); 18 the switch in the atlas's bottom sheet
//     (≤ 1 019 px, no taller row, keeps the view); 19 the consent banner over the atlas (no Tab stop under it at 320, 390,
//     1440; the room comes back after a choice); 20 the top lists' rows inside their panel at 861–1440 and the place
//     counts on one row; 21 the hero's pause button (2.2.2), the pan keys and the split's tap (2.5.7), 3 : 1 for the noise
//     bars, the finder's border and the lightest map classes (1.4.11), the explanation pages' h1, the 404's switch.
//     Since round-1 of the re-checks (6 Oct): the pause lasts a reload, and the pan keys touch no card, credit or zoom
//     (390 × 664 and 390 × 844 with a card, 720 × 450 where they must show, 720 × 700, 900 × 700), nor the zoom the credit.
// 22. Round-2 of the re-checks (6 Oct), failing on 70b1fdf: after Accept or Decline focus goes back where it stood (2.4.3;
//     it fell to <body>), or to <main> unscrolled; 40 pan keys, 60 arrows or 20 drags leave the city on the free stage;
//     with the banner up at 320 × 568 and 320 × 480 the zoom stays whole and the sheet and a card end below it.
// 23–24. Round-3 of the re-checks: the short consent card; the bar measured again when it comes unstuck.
// 25–26. The small-fixes round (6 Oct), each failing on c440f0a: 25 the atlas's consent buttons are the site's ghost pills
//     (Chromium and WebKit, 320/390/1440 and the short card; hover, focus ring, forced colours, ≥ 4.5 : 1); 26 the pan keys
//     10 px (--s-10) from the zoom. Step 16 now walks every dossier and no longer lets the Dutch fairness note through.
//
// Usage: node scripts/check-a11y.mjs [baseUrl] [prefix]   (default http://localhost:5181; a server WITHOUT UMAMI_WEBSITE_ID;
//   steps 19, 22, 23, 25 and 26 need the consent banner, so a server with CLARITY_ID set — e.g. CLARITY_ID=test — runs every step)
//   A11Y_STEPS=17,19 runs only those steps
//   [prefix] a language's prefix, /nl or /fr (plan 5, task 14): put before every address here; the city names the steps
//   look for are then the language's (messages/<lang>.json, common.cities)
// WebKit for playwright-core is needed for step 7 (node node_modules/playwright-core/cli.js install webkit).
// Prints ✓/✗ lines only; the exit code is the number of ✗.
import { chromium, webkit } from 'playwright-core'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { createRequire } from 'node:module'

const base = process.argv[2] || 'http://localhost:5181'
const prefix = (process.argv[3] || '').replace(/\/+$/, '')
const at = (p) => (prefix ? (p === '/' ? prefix : prefix + p) : p)
const lang = prefix.slice(1) || 'en'
const CITY = JSON.parse(fs.readFileSync(new URL(`../messages/${lang}.json`, import.meta.url), 'utf8')).common.cities
const EXE = path.join(os.homedir(), 'Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
const AXE = fs.readFileSync(createRequire(import.meta.url).resolve('axe-core/axe.min.js'), 'utf8')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
let bad = 0
// A11Y_STEPS=17,18 runs only those steps (a step that guards two numbers answers to its first)
const step = (n) => !process.env.A11Y_STEPS || process.env.A11Y_STEPS.split(',').map(Number).includes(n)
const ok = (cond, yes, no = yes) => { if (cond) console.log(`✓ ${yes}`); else { bad++; console.log(`✗ ${no}`) } }
const local = new URL(base).host

const chrome = await chromium.launch({ headless: true, executablePath: fs.existsSync(EXE) ? EXE : undefined })
async function open(browser = chrome, { width = 1440, height = 900, reducedMotion = 'no-preference' } = {}) {
  const ctx = await browser.newContext({ viewport: { width, height }, reducedMotion })
  await ctx.addInitScript(() => { try { localStorage.setItem('frondia.consent', JSON.stringify({ choice: 'denied', at: '2026-01-01T00:00:00.000Z', v: 1 })) } catch {} })
  await ctx.route('**/*', (route) => {
    const u = new URL(route.request().url())
    return u.host !== local || /^\/(u\/script\.js|api\/send)/.test(u.pathname) ? route.abort() : route.continue()
  })
  return { page: await ctx.newPage(), close: () => ctx.close() }
}
const ready = (page) => page.waitForSelector('.atlas[data-ready="true"] .panel h1', { timeout: 20000 })
async function go(page, p) {
  await page.goto(base + at(p), { waitUntil: 'networkidle' })
  if (/^\/atlas(\?|$)/.test(p)) await ready(page)
  await sleep(500)
}
const focused = (page) => page.evaluate(() => {
  const e = document.activeElement
  if (!e || e === document.body) return 'body'
  const name = (e.getAttribute('aria-label') || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40)
  return `${e.tagName.toLowerCase()}${e.closest('.drawer') ? ' (in the card)' : ''} “${name}”`
})
// a computed colour — rgb(), rgba() or color(srgb …) (what color-mix() computes to) — as [r, g, b, alpha], channels 0–255
const rgba = (css) => {
  const n = css.match(/[\d.]+/g).map(Number)
  const rgb = css.startsWith('color(') ? n.slice(0, 3).map((c) => c * 255) : n.slice(0, 3)
  return [...rgb, n.length > 3 ? n[3] : 1]
}
const lum = (css) => {
  const [r, g, b] = rgba(css).slice(0, 3).map((c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4 })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05) }
// a colour with alpha laid over another, as rgb()
const over = (top, under) => {
  const t = rgba(top), u = rgba(under)
  return `rgb(${[0, 1, 2].map((i) => Math.round(t[i] * t[3] + u[i] * (1 - t[3]))).join(',')})`
}

// ---- 1. axe ----
if (step(1)) {
  const states = {
    'atlas, a sector’s card': async (page) => go(page, '/atlas?city=brussels&sector=21004E72-'),
    'atlas, an audit': async (page) => go(page, '/atlas?case=ninove'),
    'commune, the finder’s list open': async (page) => { await go(page, '/commune?code=21001'); await page.locator('input[role=combobox]').focus(); await page.keyboard.type('an'); await sleep(200) },
  }
  const pages = ['/', '/privacy', '/dossier', '/dossier?city=ghent&sector=44021A00-', '/commune', '/commune?code=21001', '/data', '/register', '/foo', '/atlas/foo',
    '/atlas?city=brussels', '/atlas?city=antwerp&q=need&lens=heat', '/atlas?city=ghent&q=place', '/atlas?city=liege&view=communes', '/atlas?city=ghent&view=photos']
  for (const width of [1440, 390]) {
    const { page, close } = await open(chrome, { width })
    const found = []
    const run = async (label) => {
      await page.addScriptTag({ content: AXE })
      // on a phone an open card covers the panel, which is inert then (step 8), its h1 with it: the card's h2 is the page
      const covered = width < 861 && /card|audit/.test(label)
      const v = await page.evaluate(async (covered) => (await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] }, rules: covered ? { 'page-has-heading-one': { enabled: false } } : {} }))
        .violations.map((x) => `${x.id} (${x.nodes.slice(0, 2).map((n) => n.target.join(' ')).join(', ')})`), covered)
      for (const x of v) found.push(`${label}: ${x}`)
    }
    for (const p of pages) { await go(page, p); await run(p) }
    for (const [label, set] of Object.entries(states)) { await set(page); await run(label) }
    ok(found.length === 0, `axe at ${width}: no violation on ${pages.length} pages and ${Object.keys(states).length} states`, `axe at ${width}: ${found.slice(0, 8).join(' · ')}`)
    await close()
  }
}

// ---- 2. the skip link ----
if (step(2)) {
  const { page, close } = await open()
  for (const p of ['/', '/register', '/atlas?city=brussels']) {
    await go(page, p)
    await page.keyboard.press('Tab')
    const first = await page.evaluate(() => {
      const e = document.activeElement, r = e.getBoundingClientRect()
      return { href: e.getAttribute('href'), seen: r.top >= 0 && r.bottom <= innerHeight && r.width > 40 && getComputedStyle(e).opacity !== '0', main: !!document.querySelector('main#main') }
    })
    const was = await page.evaluate(() => ({ url: location.href, n: history.length }))
    await page.keyboard.press('Enter')
    await sleep(200)
    // re-check 5: the link moves focus itself; a #main entry in history let Back put another city in the atlas's address
    const now = await page.evaluate(() => ({ url: location.href, n: history.length }))
    const still = now.url === was.url && now.n === was.n
    await page.keyboard.press('Tab')
    const inMain = await page.evaluate(() => !!document.activeElement?.closest('main'))
    ok(first.href === '#main' && first.seen && first.main && inMain && still, `${p}: the first Tab shows the skip link; after it the next Tab is in <main>, address and history unchanged`,
      `${p}: first Tab ${first.href} (visible ${first.seen}, main#main ${first.main}), next Tab in main ${inMain}, address and history unchanged ${still}`)
  }
  await close()
}

// ---- 3. the 404 ----
if (step(3)) {
  for (const width of [1440, 390]) {
    const { page, close } = await open(chrome, { width })
    await go(page, '/foo')
    const r = await page.evaluate(() => ({ h1: document.querySelector('h1').getBoundingClientRect().top, bar: document.querySelector('.nav .wrap').getBoundingClientRect().bottom }))
    ok(r.h1 >= r.bar, `/foo at ${width}: the heading starts below the bar (${Math.round(r.h1)} ≥ ${Math.round(r.bar)})`, `/foo at ${width}: the heading (top ${Math.round(r.h1)}) sits under the bar (bottom ${Math.round(r.bar)})`)
    await close()
  }
}

// ---- 4. the commune finder ----
if (step(4)) {
  const { page, close } = await open()
  await go(page, '/commune?code=21001')
  const input = page.locator('input[role=combobox]')
  await input.focus()
  await page.keyboard.type('ixel')
  await page.keyboard.press('ArrowDown')
  const ring = await page.evaluate(() => {
    const o = document.getElementById(document.querySelector('input[role=combobox]').getAttribute('aria-activedescendant'))
    const cs = getComputedStyle(o)
    return { shadow: cs.boxShadow, outline: cs.outlineStyle, bg: cs.backgroundColor, list: getComputedStyle(o.parentElement).backgroundColor }
  })
  const ringed = ring.shadow !== 'none' || ring.outline !== 'none'
  ok(ringed, 'the finder’s active option carries a ring', `the active option has no ring: background ${ring.bg} on ${ring.list} (${ratio(ring.bg, ring.list).toFixed(2)} : 1)`)
  await page.keyboard.press('Tab')
  await sleep(150)
  const openAfter = await page.locator('[role=listbox]').count()
  ok(openAfter === 0 && (await input.getAttribute('aria-expanded')) === 'false', 'a Tab out of the field closes the list', `after a Tab out the list is still open (${openAfter})`)
  await close()
}

// ---- 5. cards and the keyboard ----
if (step(5)) {
  const { page, close } = await open()
  await go(page, '/atlas?city=brussels&q=need&lens=services')
  const row = page.locator('.panel .toplist button, .panel li button').first()
  await row.focus()
  const rowName = await focused(page)
  await page.keyboard.press('Enter')
  await sleep(700)
  const into = await focused(page)
  await page.keyboard.press('Escape')
  await sleep(300)
  const closed = await page.locator('.drawer').count(), back = await focused(page)
  ok(/in the card/.test(into), 'Enter on a list row moves focus into the sector’s card', `after Enter on a row focus is on ${into}`)
  ok(closed === 0 && back === rowName, 'Escape closes the card and focus is back on the row', `after Escape: ${closed} card(s), focus on ${back} (the row: ${rowName})`)

  await go(page, '/atlas?city=brussels')
  const pin = page.locator('g.case-pin[aria-label*="Ninove"]')
  await pin.focus()
  await page.keyboard.press('Enter')
  await sleep(800)
  const intoPin = await focused(page)
  await page.locator('.drawer-x').focus()
  await page.keyboard.press('Enter')
  await sleep(300)
  const backPin = await focused(page)
  ok(/in the card/.test(intoPin) && /Ninove/.test(backPin) && /^g /.test(backPin), 'a pin’s audit: focus into the drawer, its × by keyboard brings it back to the pin',
    `pin → ${intoPin}; × → ${backPin}`)
  await close()
}

// ---- 6. the map and the keyboard ----
if (step(6)) {
  const { page, close } = await open()
  await go(page, '/atlas?city=brussels')
  const svg = page.locator('.atlas-map svg[role="group"]')
  const info = await svg.evaluate((s) => ({ tab: s.getAttribute('tabindex'), desc: (s.getAttribute('aria-describedby') || '').split(' ').map((id) => document.getElementById(id)?.textContent || '').join(' ').trim() }))
  ok(info.tab === '0' && info.desc.length > 20, `the map is a Tab stop described for the keyboard (“${info.desc.slice(0, 50)}…”)`, `the map: tabindex ${info.tab}, description “${info.desc}”`)
  await svg.focus()
  await page.keyboard.press('Tab'); await page.keyboard.press('Shift+Tab')   // reach it as a keyboard does
  const vb0 = await svg.getAttribute('viewBox')
  await page.keyboard.press('ArrowRight'); await sleep(100)
  const vb1 = await svg.getAttribute('viewBox')
  await page.keyboard.press('+'); await sleep(100)
  const vb2 = await svg.getAttribute('viewBox')
  const w = (v) => Number(v.split(' ')[2])
  ok(vb1 !== vb0 && w(vb2) < w(vb1), 'an arrow pans the map and + zooms it', `viewBox ${vb0} → (→) ${vb1} → (+) ${vb2}`)
  const tip = nbsp(await page.locator('.atlas-tip').textContent().catch(() => ''))
  await page.keyboard.press('Enter'); await sleep(600)
  const card = await page.locator('.drawer h2').textContent().catch(() => null)
  ok(!!card && !!tip && tip.includes(nbsp(card)), `Enter opens the sector named in the tip (${nbsp(card || '')})`, `tip “${tip}”, card “${card}”`)
  await page.keyboard.press('Escape'); await sleep(300)
  ok((await focused(page)).startsWith('svg'), 'Escape closes it and focus is back on the map', `after Escape focus is on ${await focused(page)}`)
  await close()
}
function nbsp(s) { return (s || '').replace(/[  ]/g, ' ').replace(/⁠/g, '').replace(/\s+/g, ' ').trim() }

// ---- 7. the open audit's pin shows its focus ----
if (step(7)) {
  let wk = null
  try { wk = await webkit.launch({ headless: true }) } catch { ok(false, '', 'WebKit for playwright-core is not installed: step 7 needs it') }
  for (const [name, browser] of [['Chromium', chrome], ['WebKit', wk]]) {
    if (!browser) continue
    const { page, close } = await open(browser)
    await go(page, '/atlas?case=ninove')
    await sleep(1000)
    const pin = page.locator('g.case-pin[aria-label*="Ninove"]')
    const box = await pin.boundingBox()
    const clip = { x: box.x - 4, y: box.y - 4, width: box.width + 8, height: box.height + 8 }
    const a = await page.screenshot({ clip })
    await pin.focus()
    await page.keyboard.press('Shift+Tab'); await page.keyboard.press('Tab')   // keyboard focus, so :focus-visible
    await sleep(200)
    const isPin = await page.evaluate(() => document.activeElement?.classList.contains('case-pin'))
    const b = await page.screenshot({ clip })
    ok(isPin && !a.equals(b), `${name}: the open audit’s pin changes when it has keyboard focus`, `${name}: the open audit’s pin looks the same focused (focus on the pin: ${isPin})`)
    await close()
  }
  await wk?.close()
}

// ---- 8. a phone with a card open ----
if (step(8)) {
  const { page, close } = await open(chrome, { width: 390, height: 844 })
  await go(page, '/atlas?city=brussels&sector=21004E72-')
  const hidden = []
  let pinSeen = null
  for (let i = 0; i < 30; i++) {
    await page.keyboard.press('Tab')
    await sleep(900)
    const r = await page.evaluate(() => {
      const e = document.activeElement
      if (!e || e === document.body) return null
      const b = e.getBoundingClientRect()
      const pts = [[.5, .5], [.2, .2], [.8, .2], [.2, .8], [.8, .8]].map(([fx, fy]) => [b.left + b.width * fx, b.top + b.height * fy])
      const seen = pts.some(([x, y]) => { const t = document.elementFromPoint(x, y); return t && (t === e || e.contains(t) || t.contains(e)) })
      return { name: (e.getAttribute('aria-label') || e.textContent || '').trim().slice(0, 30), seen, pin: e.classList.contains('case-pin'), last: e.classList.contains('mono') && !!e.closest('.zoom') }
    })
    if (!r) break
    if (!r.seen) hidden.push(r.name)
    if (r.pin) pinSeen = r.seen
    if (r.last) break
  }
  ok(hidden.length === 0, 'at 390 with a card open no Tab stop is hidden under a card', `hidden under a card: ${hidden.join(', ')}`)
  ok(pinSeen === true, 'at 390 a pin reached by Tab is in view', `the pin reached by Tab was in view: ${pinSeen}`)
  const hit = await page.evaluate(() => [...document.querySelectorAll('.case-pin')].map((g) => { const b = g.getBoundingClientRect(); return Math.min(b.width, b.height) }))
  ok(hit.length > 0 && hit.every((d) => d >= 23.5), `at 390 every audit pin is a 24-px target or more (${hit.map((d) => Math.round(d)).join(', ')} px)`, `at 390 audit pins measure ${hit.map((d) => Math.round(d)).join(', ')} px across (WCAG 2.5.8)`)
  await close()
}

// ---- 9. the title follows the view; 10. a change of view is said ----
const said = (page) => page.evaluate(() => document.querySelector('main [role="status"].sr-only')?.textContent ?? '')
if (step(9)) {
  const { page, close } = await open()
  await go(page, '/atlas?city=brussels')
  await page.locator('.seg--lens button').first().click()
  await sleep(500)
  const t1 = nbsp(await page.title()), said1 = nbsp(await said(page))
  const h1a = nbsp(await page.locator('.panel h1').textContent())
  await page.selectOption('.city-pick select', 'ghent')
  await page.waitForFunction((g) => (document.querySelector('.panel h1')?.textContent || '').includes(g), CITY.ghent)
  await sleep(500)
  const t2 = nbsp(await page.title()), said2 = nbsp(await said(page))
  // the view's words are checked in English; in another language the title is the view's, not the city's plain one
  const viewWords = lang === 'en' ? /services|missing|heat|shops|3-30-300|°/i.test(t1) : true
  ok(t1.includes(CITY.brussels) && viewWords && t1 !== `Atlas · ${CITY.brussels} · Frondia` && t2.includes(CITY.ghent),
    `the title follows the view (“${t1}” → “${t2}”)`, `titles after a question and a city: “${t1}”, “${t2}”`)
  ok(said1 === h1a && said2.includes(CITY.ghent), `a change of view is said (“${said1}” → “${said2}”)`, `status: “${said1}” (heading “${h1a}”), then “${said2}”`)
  await page.locator('.seg--lens button').nth(2).click()
  await sleep(400)
  ok(await page.locator('.counts[aria-live="polite"]').count() === 1, 'the counts are a polite live region', 'the counts are not a live region')
  await close()
}

// ---- 11. colours ----
if (step(11)) {
  const { page, close } = await open()
  await go(page, '/atlas?city=brussels')
  const c = await page.evaluate(() => {
    const probe = (v) => { const d = document.createElement('i'); d.style.color = v; document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c }
    const pat = document.querySelector('.sector-map pattern')
    const line = pat && getComputedStyle(pat.querySelector('line')).stroke, ground = pat && getComputedStyle(pat.querySelector('rect')).fill
    const panel = getComputedStyle(document.querySelector('.panel')).backgroundColor
    const credit = getComputedStyle(document.querySelector('.atlas-credit')).backgroundColor
    return { line, ground, panel, credit, ink3: probe('var(--ink-3)') }
  })
  const hatch = ratio(c.line, c.ground)
  ok(hatch >= 3, `the atlas’s hatch: ${hatch.toFixed(2)} : 1 on its ground`, `the atlas’s hatch: ${hatch.toFixed(2)} : 1 (${c.line} on ${c.ground}), under 3`)
  const black = 'rgb(0,0,0)'
  const onPanel = ratio(c.ink3, over(c.panel, black)), onCredit = rgba(c.credit)[3] ? ratio(c.ink3, over(c.credit, black)) : 0
  ok(onPanel >= 4.5, `the panel’s grey text over a black map: ${onPanel.toFixed(2)} : 1`, `the panel’s grey text over a black map: ${onPanel.toFixed(2)} : 1 (panel ${c.panel})`)
  ok(onCredit >= 4.5, `the credit over a black map: ${onCredit.toFixed(2)} : 1`, `the credit over a black map: ${onCredit.toFixed(2)} : 1 (plate ${c.credit})`)
  await close()
}

// ---- 12. reduced motion ----
if (step(12)) {
  const { page, close } = await open(chrome, { reducedMotion: 'reduce' })
  await go(page, '/atlas?city=brussels')
  await page.locator('.toplist button').first().click()
  await sleep(30)
  const slides = await page.evaluate(() => document.getAnimations().filter((a) => a.animationName === 'drawerIn' && a.playState === 'running').length)
  ok(slides === 0, 'reduced motion: an opening card does not slide in', `reduced motion: ${slides} card animation(s) running`)
  await close()
}

// ---- 13. text spacing at 320 ----
if (step(13)) {
  const { page, close } = await open(chrome, { width: 320, height: 640 })
  const wide = []
  // /commune?code=11002: Antwerp's long sector names beside their values ran 48 px past the screen (P5-12, fix wave)
  for (const p of ['/', '/privacy', '/dossier', '/commune?code=21001', '/commune?code=11002', '/data', '/register', '/foo']) {
    await go(page, p)
    await page.addStyleTag({ content: '* { line-height: 1.5 !important; letter-spacing: .12em !important; word-spacing: .16em !important; } p { margin-bottom: 2em !important; }' })
    await sleep(300)
    const w = await page.evaluate(() => document.documentElement.scrollWidth)
    if (w > 321) wide.push(`${p} ${w} px`)
  }
  ok(wide.length === 0, 'text spacing at 320: no page is wider than the screen (8 pages)', `text spacing at 320, wider than the screen: ${wide.join(', ')}`)
  await close()
}

// ---- 14. print ----
if (step(14)) {
  const { page, close } = await open()
  const shown = []
  for (const p of ['/', '/dossier', '/commune?code=21001', '/data', '/register', '/privacy', '/atlas?city=brussels']) {
    await go(page, p)
    await page.emulateMedia({ media: 'print' })
    if (await page.evaluate(() => { const e = document.querySelector('.skip-link'); return !!e && getComputedStyle(e).display !== 'none' })) shown.push(p)
    await page.emulateMedia({ media: 'screen' })
  }
  ok(shown.length === 0, 'print: the skip link is not on paper (7 pages)', `print: the skip link prints at the foot of every page on ${shown.join(', ')}`)
  await close()
}

// ---- 15. reflow in Safari, and the finder's placeholder ----
if (step(15)) {
  let wk = null
  try { wk = await webkit.launch({ headless: true }) } catch { ok(false, '', 'WebKit for playwright-core is not installed: step 15 needs it') }
  if (wk) {
    const wide = []
    for (const width of [320, 390]) {
      const { page, close } = await open(wk, { width, height: 844 })
      for (const p of ['/', '/privacy', '/dossier', '/commune', '/commune?code=11002', '/data', '/register', '/foo']) {
        await go(page, p)
        const w = await page.evaluate(() => document.documentElement.scrollWidth)
        if (w > width + 1) wide.push(`${p} at ${width}: ${w} px`)
      }
      await close()
    }
    ok(wide.length === 0, 'WebKit at 320 and 390: no page is wider than the screen (8 pages)', `WebKit, wider than the screen: ${wide.join(', ')}`)
  }
  const cut = []
  for (const [name, browser] of [['Chromium', chrome], ['WebKit', wk]]) {
    if (!browser) continue
    for (const width of [320, 390, 1440]) {
      const { page, close } = await open(browser, { width, height: 844 })
      for (const p of ['/commune', '/commune?code=21004']) {
        await go(page, p)
        const r = await page.evaluate(() => {
          const i = document.querySelector('.finder input'), cs = getComputedStyle(i), c = document.createElement('canvas').getContext('2d')
          c.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`
          return { text: c.measureText(i.placeholder).width, room: i.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight) }
        })
        if (r.text > r.room) cut.push(`${name} ${p} at ${width}: ${Math.round(r.text)} px in ${Math.round(r.room)}`)
      }
      await close()
    }
  }
  ok(cut.length === 0, 'the commune finder’s placeholder fits its field (Chromium and WebKit, 320–1440)', `the finder’s placeholder is cut: ${cut.join(', ')}`)
  await wk?.close()
}

// ---- 16. what a language changes (re-check 2 after plan 5) ----
if (step(16)) {
  // the rights holders' credits stay English on a Dutch or French page, and say so (3.1.2); on an English page the html's lang does
  const { page, close } = await open()
  const unmarked = []
  // and so do the licences' names on /data («ODbL 1.0 (derived from OpenStreetMap)», L6; re-check 5 after plan 5), every one
  for (const [p, sel] of [['/', 'footer .footer-grid > p.small'], ['/data', '.data-facts > div:last-child ul'], ['/data', '.data-card-meta > span:last-child'],
    ['/data', '.data-facts > div:nth-last-child(2) > dd'], ['/atlas?city=brussels', '.atlas-credit'], ['/atlas?city=brussels&q=need&lens=heat', '.atlas-credit']]) {
    await go(page, p)
    const ls = await page.evaluate((sel) => { const es = [...document.querySelectorAll(sel)]; return es.length ? [...new Set(es.map((e) => e.closest('[lang]').getAttribute('lang')))] : ['missing'] }, sel)
    for (const l of ls) if (!/^en\b/.test(l)) unmarked.push(`${p} ${sel}: ${l}`)
  }
  ok(unmarked.length === 0, 'the English credits and licences are marked as English (footer, data, atlas)', `credits or licences not marked as English: ${unmarked.join(', ')}`)
  // the switcher's links are named by their language, in that language, with the visible code in the name (2.5.3)
  await go(page, '/')
  const sw = await page.evaluate(() => [...document.querySelectorAll('.lang a')].filter((a) => a.getClientRects().length).map((a) => ({ code: a.textContent.trim(), name: a.getAttribute('aria-label') || '', lang: a.lang, hreflang: a.hreflang })))
  const badSw = sw.filter((a) => !a.name.includes(a.code) || a.name.length < a.code.length + 4 || !a.lang || a.lang !== a.hreflang)
  ok(sw.length === 3 && badSw.length === 0, `the switcher names each language in its own words (${sw.map((a) => a.name).join(', ')})`, `the switcher’s names: ${JSON.stringify(sw)}`)
  // a select's options carry no soft hyphen: an option never wraps, so it would only reach the screen reader
  const shy = []
  for (const p of ['/data', '/atlas?city=brussels', '/atlas?city=brussels&q=place']) {
    await go(page, p)
    shy.push(...(await page.evaluate(() => [...document.querySelectorAll('option')].filter((o) => /­/.test(o.textContent)).map((o) => o.textContent.replace(/­/g, '~')))).map((s) => `${p}: ${s}`))
  }
  ok(shy.length === 0, 'no option carries a soft hyphen', `options with a soft hyphen: ${shy.slice(0, 4).join(', ')}`)
  await close()

  // reflow in both engines: no text runs past a 320 screen on the document pages, with and without WCAG's text spacing
  // (Safari sized a ≤ 560 px grid by a Dutch paragraph's min-content: /nl/dossier 2285 px wide, /nl/data's limits cut by
  // html's clip), and the atlas's counts stay in the panel («en désimperméabilisation» was cut at 320–350 px and from 861 px)
  const SPACING = '* { line-height: 1.5 !important; letter-spacing: .12em !important; word-spacing: .16em !important; } p { margin-bottom: 2em !important; }'
  let wk = null
  try { wk = await webkit.launch({ headless: true }) } catch { ok(false, '', 'WebKit for playwright-core is not installed: step 16 needs it') }
  const past = []
  for (const [name, browser] of [['Chromium', chrome], ['WebKit', wk]]) {
    if (!browser) continue
    const { page, close } = await open(browser, { width: 320, height: 640 })
    // every dossier variant (small-fixes round, 6 Oct 2026): the five cities, a named sector, Ghent's coded one, a missing one
    for (const spacing of [false, true]) for (const p of ['/data', '/register', '/dossier', '/dossier?city=antwerp', '/dossier?city=brussels&sector=21004E72-',
      '/dossier?city=charleroi', '/dossier?city=ghent', '/dossier?city=liege', '/dossier?sector=nope', '/dossier?city=ghent&sector=44021A00-']) {
      await go(page, p)
      if (spacing) await page.addStyleTag({ content: SPACING })
      // /data's limits and credits sit in each layer's details: what a reader sees once they are open
      await page.evaluate(() => { for (const d of document.querySelectorAll('details')) d.open = true })
      await sleep(300)
      const { wide, runs } = await page.evaluate(() => {
        const vw = document.documentElement.clientWidth, tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT), runs = []
        while (tw.nextNode()) {
          const n = tw.currentNode
          if (!n.textContent.trim() || n.parentElement.closest('.doc-table-wrap, .data-cols-wrap, .sr-only, .skip-link, script, style')) continue
          const rg = document.createRange(); rg.selectNodeContents(n)
          for (const q of rg.getClientRects()) if (q.width && q.right > vw + 1) { runs.push(`“${n.textContent.replace(/\u00AD/g, '').trim().slice(0, 30)}” ends at ${Math.round(q.right)}`); break }
        }
        return { wide: document.documentElement.scrollWidth > vw + 1 ? `${document.documentElement.scrollWidth} px wide` : null, runs }
      })
      // the Dutch fairness note ran 10–14 px out in Safari under the override (its tied run broken only at «hoogs-te»), and
      // was let through here until the small-fixes round (6 Oct 2026): it fails on c440f0a now, and passes with the fix
      const r = runs.length ? runs.join(', ') : wide
      if (r) past.push(`${name} ${p}${spacing ? ' (text spacing)' : ''}: ${r}`)
    }
    for (const [w, spacing] of [[320, false], [340, false], [390, true], [1440, false]]) {
      await page.setViewportSize({ width: w, height: 640 })
      await go(page, '/atlas?city=antwerp&m=built')
      if (spacing) { await page.addStyleTag({ content: SPACING }); await sleep(300) }
      const r = await page.evaluate(() => { const pn = document.querySelector('.panel'); const cut = [...document.querySelectorAll('.counts .label')].filter((e) => e.getBoundingClientRect().right > pn.getBoundingClientRect().right + 1); return pn.scrollWidth > pn.clientWidth + 1 || cut.length ? `panel ${pn.scrollWidth} in ${pn.clientWidth}: ${cut.map((e) => e.textContent).join(' | ')}` : null })
      if (r) past.push(`${name} atlas counts at ${w}${spacing ? ' (text spacing)' : ''}: ${r}`)
    }
    // the sector card: «voldoet aan een van de twee», one tied run of 164 px, ran 23 px out of its 125-px column
    for (const w of [320, 1440]) {
      await page.setViewportSize({ width: w, height: 800 })
      await go(page, '/atlas?city=antwerp&sector=11001A01-')
      const r = await page.evaluate(() => [...document.querySelectorAll('.drawer')].filter((d) => d.getClientRects().length && d.scrollWidth > d.clientWidth + 1).map((d) => `card ${d.scrollWidth} in ${d.clientWidth}`).join(', '))
      if (r) past.push(`${name} Antwerp sector card at ${w}: ${r}`)
    }
    await close()
  }
  ok(past.length === 0, 'at 320 no text runs past the screen (/data, /register, every dossier; Chromium and WebKit, with and without text spacing), and the atlas’s counts and an Antwerp card stay in their boxes',
    `text past the screen: ${past.slice(0, 6).join(' · ')}`)
  await wk?.close()
}

// ---- 17. the phone's two-row bar (design wave, 5 Oct 2026) ----
if (step(17)) {
  // from 560 px down the bar has two rows: the wordmark and EN · NL · FR, then every link (Article 8, Method, Audits, the
  // atlas pill) — none hidden, no burger (the one-row bar hid Method and Audits). Every target is at least 24 × 24 (2.5.8),
  // nothing runs past the screen, the page's first heading starts below the bar, and Tab follows the reading order
  const { page, close } = await open(chrome, { width: 390, height: 800 })
  const fails = []
  for (const p of ['/', '/privacy', '/data', '/dossier', '/register', '/commune?code=21002', '/foo']) {
    for (const w of [320, 360, 390, 430, 480, 560]) {
      await page.setViewportSize({ width: w, height: 800 })
      await go(page, p)
      const r = await page.evaluate(() => {
        const vw = document.documentElement.clientWidth, nav = document.querySelector('header.nav'), out = []
        const vis = (e) => e && e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden'
        const box = (e) => e.getBoundingClientRect()
        const word = nav.querySelector('.wordmark'), langs = [...nav.querySelectorAll('.lang')].filter(vis)
        const links = [...nav.querySelectorAll('.nav-links > a')]
        if (langs.length !== 1) out.push(`${langs.length} switches drawn`)
        const hidden = links.filter((a) => !vis(a)).map((a) => a.textContent.trim())
        if (hidden.length) out.push(`hidden: ${hidden.join(', ')}`)
        const lang = langs[0]
        if (lang) {
          const lb = box(lang), wb = box(word)
          if (Math.abs((lb.top + lb.bottom) / 2 - (wb.top + wb.bottom) / 2) > 12) out.push('the switch is not on the wordmark’s row')
          for (const a of links.filter(vis)) if (box(a).top < wb.bottom - 4) out.push(`“${a.textContent.trim()}” is on the first row`)
          for (const a of lang.querySelectorAll('a')) { const b = box(a); if (b.width < 24 || b.height < 24) out.push(`${a.textContent} ${Math.round(b.width)}×${Math.round(b.height)}`) }
        }
        for (const a of links.filter(vis)) { const b = box(a); if (b.width < 24 || b.height < 24) out.push(`“${a.textContent.trim()}” ${Math.round(b.width)}×${Math.round(b.height)}`); if (b.right > vw + 1) out.push(`“${a.textContent.trim()}” ends at ${Math.round(b.right)}`) }
        if (document.documentElement.scrollWidth > vw + 1) out.push(`page ${document.documentElement.scrollWidth} wide`)
        const h1 = document.querySelector('main h1')
        if (h1 && vis(h1) && box(h1).top < box(nav).bottom - 1) out.push(`the h1 starts at ${Math.round(box(h1).top)}, under the bar (${Math.round(box(nav).bottom)})`)
        return out.join('; ')
      })
      if (r) fails.push(`${p} ${w}: ${r}`)
    }
  }
  // the Tab order is the reading order: skip link, wordmark, the three languages, then the links of the second row
  await page.setViewportSize({ width: 390, height: 800 })
  await go(page, '/data')
  const order = []
  for (let i = 0; i < 9; i++) {
    await page.keyboard.press('Tab')
    order.push(await page.evaluate(() => { const e = document.activeElement; return e.closest('.lang') ? 'lang' : e.classList.contains('wordmark') ? 'wordmark' : e.classList.contains('skip-link') ? 'skip' : e.closest('.nav-links') ? 'link' : e.tagName.toLowerCase() }))
  }
  const want = 'skip,wordmark,lang,lang,lang,link,link,link,link'
  if (order.join() !== want) fails.push(`/data 390 Tab: ${order.join(' → ')}`)
  ok(fails.length === 0, 'phone bar (320–560): two rows, wordmark and EN · NL · FR above every link, none hidden, targets ≥ 24 px, nothing past the screen or under the bar, Tab in reading order',
    `phone bar: ${fails.slice(0, 5).join(' · ')}${fails.length > 5 ? ` (+${fails.length - 5})` : ''}`)
  await close()
}

// ---- 18. the language switch in the atlas's bottom sheet (design wave, 5 Oct 2026) ----
if (step(18)) {
  // on a phone the bar has no switch (its end is hidden ≤ 860) and from 861 to 1 019 it has no room: the panel's kicker row
  // carries a small EN · NL · FR beside the question, above the city's name. Its targets are 24 × 24 (2.5.8), it adds no
  // height to the row (the sheet's collapsed height, 44 % of the stage, is unchanged), and it keeps the view
  const { page, close } = await open(chrome, { width: 390, height: 844 })
  const fails = []
  for (const [w, h] of [[320, 640], [390, 844], [860, 900], [900, 900], [1020, 900], [1440, 900]]) {
    await page.setViewportSize({ width: w, height: h })
    for (const v of ['/atlas?city=brussels', '/atlas?city=ghent&q=need&lens=heat', '/atlas?city=liege&q=place']) {
      await go(page, v)
      const r = await page.evaluate((w) => {
        const vis = (e) => e && e.getClientRects().length > 0
        const out = [], pn = document.querySelector('.atlas-stage > .panel')
        const shown = [...document.querySelectorAll('.lang')].filter(vis)
        const sheet = pn?.querySelector('.panel-kicker .lang')
        if (w <= 1019) {
          if (shown.length !== 1 || !vis(sheet)) return `${shown.length} switches drawn, the sheet’s ${vis(sheet) ? 'shown' : 'missing'}`
          const k = pn.querySelector('.panel-kicker'), lb = k.querySelector('.label').getBoundingClientRect(), kb = k.getBoundingClientRect()
          if (kb.height > lb.height + 0.5) out.push(`the kicker row is ${kb.height} tall, its label ${lb.height}`)
          const h1 = pn.querySelector('h1').getBoundingClientRect(), sb = sheet.getBoundingClientRect()
          if (sb.bottom > h1.top + 4) out.push('the switch is not above the city’s name')
          if (sb.right > pn.getBoundingClientRect().right - 8) out.push('the switch runs into the sheet’s edge')
          for (const a of sheet.querySelectorAll('a')) { const b = a.getBoundingClientRect(); if (b.width < 24 || b.height < 24) out.push(`${a.textContent} ${Math.round(b.width)}×${Math.round(b.height)}`) }
          if (w <= 860 && getComputedStyle(pn).maxHeight !== '44%') out.push(`the sheet’s max-height is ${getComputedStyle(pn).maxHeight}`)
        } else if (shown.length !== 1 || vis(sheet)) out.push(`${shown.length} switches drawn at ${w}, the sheet’s ${vis(sheet) ? 'shown' : 'hidden'}`)
        return out.join('; ')
      }, w)
      if (r) fails.push(`${v} ${w}: ${r}`)
    }
  }
  // the sheet's switch keeps the view: three changes of view, then the other languages, at 390
  await page.setViewportSize({ width: 390, height: 844 })
  await go(page, '/atlas?city=ghent')
  await page.locator('.seg--lens button').nth(0).click(); await sleep(400)
  await page.locator('.panel .chips button').nth(2).click(); await sleep(400)
  const view = await page.evaluate(() => location.search)
  const target = prefix === '/fr' ? 'NL' : 'FR', want = target === 'NL' ? '/nl/atlas' : '/fr/atlas'
  const link = page.locator('.panel-kicker .lang a', { hasText: target })
  if (!(await link.count())) fails.push('no switch in the sheet at 390')
  else {
    await link.click()
    await page.waitForURL((u) => new URL(u).pathname === want, { timeout: 10000 }).catch(() => {})
    await ready(page).catch(() => {}); await sleep(500)
    const at = await page.evaluate(() => location.pathname + location.search)
    if (at !== want + view) fails.push(`“${target}” in the sheet went to ${at}, the view was ${view}`)
  }
  ok(fails.length === 0, 'the atlas’s sheet (≤ 1 019 px) has the language switch beside its question: one switch drawn, 24-px targets, no taller row, the sheet still 44 %, and it keeps the view',
    `sheet switch: ${fails.slice(0, 5).join(' · ')}${fails.length > 5 ? ` (+${fails.length - 5})` : ''}`)
  await close()
}

// ---- 19. the consent banner in the atlas (design wave, 5 Oct 2026; needs a server with CLARITY_ID) ----
if (step(19)) {
  // while the banner is up the atlas makes room: on a phone the stage ends above it, on a wide screen the zoom, the pan
  // keys and a card end above it. No Tab stop is hidden under it (2.4.11), at 320, 390 and 1440, and after a choice the
  // atlas takes its room back. Nothing slides (reduced motion has nothing to stop)
  const fails = []
  let banners = 0
  for (const [w, h] of [[320, 640], [390, 844], [1440, 900]]) for (const v of ['/atlas?city=brussels', '/atlas?city=antwerp&q=need&lens=r3', '/atlas?city=brussels&sector=21004E72-']) {
    const ctx = await chrome.newContext({ viewport: { width: w, height: h } })
    await ctx.route('**/*', (route) => { const u = new URL(route.request().url()); return u.host !== local || /^\/(u\/script\.js|api\/send)/.test(u.pathname) ? route.abort() : route.continue() })
    const page = await ctx.newPage()
    await page.goto(base + at(v), { waitUntil: 'networkidle' }); await ready(page); await sleep(700)
    if (!(await page.locator('.consent-banner').count())) { await ctx.close(); continue }
    banners++
    const hidden = []
    for (let i = 0; i < 90; i++) {
      await page.keyboard.press('Tab')
      const r = await page.evaluate(() => {
        const e = document.activeElement, cb = document.querySelector('.consent-banner')
        if (!e || e === document.body || !cb || cb.contains(e)) return null
        const a = e.getBoundingClientRect(), b = cb.getBoundingClientRect()
        if (!a.width || !a.height) return null
        const covered = a.left >= b.left - 0.5 && a.right <= b.right + 0.5 && a.top >= b.top - 0.5 && a.bottom <= b.bottom + 0.5
        return covered ? (e.getAttribute('aria-label') || e.textContent || e.tagName).replace(/\s+/g, ' ').trim().slice(0, 30) : ''
      })
      if (r) hidden.push(r)
    }
    if (hidden.length) fails.push(`${v} ${w}: ${[...new Set(hidden)].join(', ')} under the banner`)
    // the zoom and the sheet clear the banner's top; after a choice the stage is the full height again
    const r = await page.evaluate(() => {
      const top = document.querySelector('.consent-banner').getBoundingClientRect().top, out = []
      for (const sel of ['.zoom', '.atlas-stage > .panel', '.atlas-stage > .drawer']) {
        const el = document.querySelector(sel); if (!el || !el.getClientRects().length) continue
        const b = el.getBoundingClientRect(), bn = document.querySelector('.consent-banner').getBoundingClientRect()
        if (b.bottom > top && b.right > bn.left && b.left < bn.right) out.push(`${sel} ends at ${Math.round(b.bottom)}, the banner starts at ${Math.round(top)}`)
      }
      return out.join(', ')
    })
    if (r) fails.push(`${v} ${w}: ${r}`)
    await page.locator('.consent-banner button').nth(1).click(); await sleep(400)
    const back = await page.evaluate(() => [document.querySelector('.atlas-stage').getBoundingClientRect().bottom, innerHeight, getComputedStyle(document.querySelector('.zoom')).bottom])
    if (Math.abs(back[0] - back[1]) > 1) fails.push(`${v} ${w}: after a choice the stage ends at ${back[0]} of ${back[1]}`)
    await ctx.close()
  }
  if (!banners) fails.push('no consent banner on this server: run check-a11y against a server started with CLARITY_ID')
  ok(fails.length === 0, `the consent banner in the atlas hides no Tab stop and nothing ends under it (${banners} views at 320, 390, 1440), and the atlas takes its room back after a choice`,
    `banner over the atlas: ${fails.slice(0, 5).join(' · ')}${fails.length > 5 ? ` (+${fails.length - 5})` : ''}`)
}

// ---- 20. the atlas's top lists and the place counts (design wave, 5 Oct 2026) ----
if (step(20)) {
  // a list row whose value no longer fits beside the name puts the value under it: no row, value or panel runs past its
  // box at 861, 1 020, 1 280 and 1 440 («Oude Schippersdokken(Zuidwijk)», the French 3-30-300 values ran 2–6 px out);
  // and the place view's two counts share one row at 1 440 in every language (the French pair stacked)
  const { page, close } = await open(chrome, { width: 1440, height: 900 })
  const fails = []
  const views = []
  for (const c of ['brussels', 'antwerp', 'ghent', 'liege', 'charleroi']) {
    views.push(`/atlas?city=${c}`, `/atlas?city=${c}&m=built`)
    for (const l of ['services', 'shops', 'heat', 'r3']) views.push(`/atlas?city=${c}&q=need&lens=${l}`)
    views.push(`/atlas?city=${c}&q=place`)
  }
  for (const w of [861, 1020, 1280, 1440]) {
    await page.setViewportSize({ width: w, height: 900 })
    for (const v of views) {
      await go(page, v)
      const r = await page.evaluate(() => {
        const pn = document.querySelector('.atlas-stage > .panel'), out = []
        if (!pn) return ''
        if (pn.scrollWidth > pn.clientWidth + 1) out.push(`panel ${pn.scrollWidth} in ${pn.clientWidth}`)
        for (const b of pn.querySelectorAll('.toplist button')) {
          const bb = b.getBoundingClientRect()
          for (const k of b.children) { const kb = k.getBoundingClientRect(); if (kb.right > bb.right + 0.5) { out.push(`«${b.textContent.slice(0, 30)}» ${Math.round(kb.right - bb.right)} px out`); break } }
        }
        return out.slice(0, 3).join(', ')
      })
      if (r) fails.push(`${v} ${w}: ${r}`)
      if (w === 1440 && /q=place/.test(v)) {
        const rows = await page.evaluate(() => [...new Set([...document.querySelectorAll('.panel .counts > div')].map((d) => Math.round(d.getBoundingClientRect().top)))].length)
        if (rows > 1) fails.push(`${v} 1440: the two counts stack`)
      }
    }
  }
  ok(fails.length === 0, `top lists: every row, value and panel inside its box (${views.length} views × 861, 1 020, 1 280, 1 440), and the place counts on one row at 1 440`,
    `top lists: ${fails.slice(0, 5).join(' · ')}${fails.length > 5 ? ` (+${fails.length - 5})` : ''}`)
  await close()
}

// ---- 21. the rest of the design wave: 2.2.2, 2.5.7, 1.4.11, a heading, the 404's switch (5 Oct 2026) ----
if (step(21)) {
  const fails = []
  const { page, close } = await open(chrome, { width: 1440, height: 900 })
  // 2.2.2: the hero's photo moves for as long as it is on screen; its pause button stops the drift where it is
  await go(page, '/')
  const btn = page.locator('.hero-rustle .rustle-pause')
  if (!(await btn.count())) fails.push('the hero has no pause button')
  else {
    const name = await btn.getAttribute('aria-label')
    await btn.click(); await sleep(300)
    const st = await page.evaluate(() => [document.querySelector('.hero-rustle .rustle-pause').getAttribute('aria-pressed'), getComputedStyle(document.querySelector('.hero-rustle .rustle-field')).animationPlayState])
    if (!name || st[0] !== 'true' || st[1] !== 'paused') fails.push(`the pause button («${name}») left the hero ${st.join(' / ')}`)
    const b = await btn.boundingBox(); if (!b || b.width < 24 || b.height < 24) fails.push('the pause button is under 24 px')
    // and the hero stays paused for the visit (round-1 re-check, 6 Oct: a language switch or a reload set it moving again)
    await go(page, '/'); await sleep(300)
    const kept = await page.evaluate(() => [document.querySelector('.hero-rustle .rustle-pause')?.getAttribute('aria-pressed'), getComputedStyle(document.querySelector('.hero-rustle .rustle-field')).animationPlayState])
    if (kept[0] !== 'true' || kept[1] !== 'paused') fails.push(`the pause did not last a reload: ${kept.join(' / ')}`)
    await page.locator('.hero-rustle .rustle-pause').click(); await sleep(200)
  }
  // 2.5.7: the map moves without a drag: four pan keys, one press moves the view; a tap on a year moves the photos' split
  for (const w of [390, 1440]) {
    await page.setViewportSize({ width: w, height: w === 390 ? 844 : 900 })
    await go(page, '/atlas?city=brussels')
    await page.locator('.zoom button').first().click(); await sleep(900)
    const vb0 = await page.evaluate(() => document.querySelector('.atlas-map svg').getAttribute('viewBox'))
    const keys = page.locator('.pan button')
    if ((await keys.count()) !== 4) { fails.push(`${w}: ${await keys.count()} pan keys`); continue }
    await keys.nth(2).click(); await sleep(300)
    const vb1 = await page.evaluate(() => document.querySelector('.atlas-map svg').getAttribute('viewBox'))
    if (vb0 === vb1) fails.push(`${w}: “right” did not move the map (${vb0})`)
    const small = await keys.evaluateAll((bs) => bs.filter((b) => { const r = b.getBoundingClientRect(); return r.width < 24 || r.height < 24 }).length)
    if (small) fails.push(`${w}: ${small} pan keys under 24 px`)
  }
  // where the pan keys stand (round-1 re-check, 6 Oct): with a card open on a phone they were drawn over its head and close
  // button, and a laptop at 200 % zoom (720 × 450, a short stage) had none. Shown, they touch no card, credit or zoom
  for (const [w, h, path] of [[390, 664, '/atlas?city=antwerp&sector=11002A00-'], [390, 844, '/atlas?city=brussels&case=ninove'], [720, 450, '/atlas?city=brussels'], [720, 700, '/atlas?city=antwerp&sector=11002A00-'], [900, 700, '/atlas?city=brussels&case=ninove']]) {
    await page.setViewportSize({ width: w, height: h }); await go(page, path); await sleep(600)
    const r = await page.evaluate(() => {
      // the zoom, moved left of an open card, kept off the credit (861 to about 1 000 px: it covered the credit's end)
      const z = document.querySelector('.zoom').getBoundingClientRect(), c = document.querySelector('.atlas-credit').getBoundingClientRect()
      const zc = Math.min(z.right, c.right) - Math.max(z.left, c.left) > 0.5 && Math.min(z.bottom, c.bottom) - Math.max(z.top, c.top) > 0.5 ? ['zoom over the credit'] : []
      const pan = document.querySelector('.pan'); if (!pan || getComputedStyle(pan).display === 'none') return { shown: false, hits: zc }
      const p = pan.getBoundingClientRect(), hits = []
      for (const s of ['.atlas-stage > .panel', '.atlas-stage > .drawer', '.atlas-credit', '.zoom']) { const e = document.querySelector(s); if (!e) continue; const b = e.getBoundingClientRect()
        if (Math.min(p.right, b.right) - Math.max(p.left, b.left) > 0.5 && Math.min(p.bottom, b.bottom) - Math.max(p.top, b.top) > 0.5) hits.push(s) }
      return { shown: true, hits: [...hits, ...zc] }
    })
    if (r.hits.length) fails.push(`${w} × ${h} ${path}: overlap: ${r.hits.join(', ')}`)
    if (w === 720 && h === 450 && !r.shown) fails.push('720 × 450 (200 % zoom): no pan keys')
  }
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.setViewportSize({ width: 1440, height: 900 })
  await go(page, '/atlas?city=ghent&view=photos')
  const tag = page.locator('.swipe-tag.is-after')
  if (await tag.count()) {
    const before = await page.evaluate(() => document.querySelector('.swipe-knob').getAttribute('aria-valuenow'))
    await tag.click(); await sleep(300)
    const after = await page.evaluate(() => document.querySelector('.swipe-knob').getAttribute('aria-valuenow'))
    if (Number(after) <= Number(before)) fails.push(`a tap on the after year left the split at ${before} → ${after}`)
  } else fails.push('no photos view in Ghent')
  // 1.4.11: a histogram's bars within noise, the finder's border and the map's lightest classes reach 3 : 1
  await go(page, '/atlas?city=brussels')
  const bar = await page.evaluate(() => { const r = [...document.querySelectorAll('.panel .hist rect, .panel svg rect')].find((x) => /noise-bar/.test(x.getAttribute('fill') || '')); return r ? [getComputedStyle(r).fill, getComputedStyle(document.querySelector('.atlas-stage > .panel')).backgroundColor] : null })
  if (!bar) fails.push('the atlas histogram draws no bar in --noise-bar')
  else if (ratio(bar[0], over(bar[1], 'rgb(240,238,230)')) < 3) fails.push(`noise bar ${ratio(bar[0], over(bar[1], 'rgb(240,238,230)')).toFixed(2)} : 1`)
  await go(page, '/atlas?city=brussels&q=need&lens=services')
  // the edge is the light sector's own stroke, its geometry drawn once (round-3 re-check, 6 Oct)
  const edges = await page.evaluate(() => [...document.querySelectorAll('.sectors path.is-light')].map((p) => getComputedStyle(p).stroke))
  if (await page.locator('.light-edges').count()) fails.push('the lightest classes’ edges are a second copy of their geometry')
  const ground = await page.evaluate(() => getComputedStyle(document.querySelector('.atlas-stage')).backgroundColor)
  const weak = [...new Set(edges)].filter((c) => ratio(c, ground) < 3)
  if (!edges.length) fails.push('the lightest classes get no edge')
  if (weak.length) fails.push(`edges under 3 : 1: ${weak.join(', ')}`)
  await go(page, '/commune')
  const fb = await page.evaluate(() => { const f = document.querySelector('.finder-field'); return f ? [getComputedStyle(f).borderTopColor, getComputedStyle(document.body).backgroundColor] : null })
  if (!fb || ratio(over(fb[0], fb[1]), fb[1]) < 3) fails.push(`the finder’s border ${fb ? ratio(over(fb[0], fb[1]), fb[1]).toFixed(2) : '?'} : 1`)
  // a heading: the explanation pages have their h1
  for (const p of ['/dossier?city=liege', '/dossier?sector=nope', '/commune?code=00000']) {
    await go(page, p)
    if ((await page.locator('main h1').count()) !== 1) fails.push(`${p} has no h1`)
  }
  // the 404 under a language: its switch never doubles a prefix
  for (const p of ['/nl/foo.php', '/fr/x.json']) {
    await page.goto(base + p, { waitUntil: 'networkidle' })
    const hrefs = await page.evaluate(() => [...document.querySelectorAll('.lang a')].map((a) => a.getAttribute('href')))
    if (hrefs.some((h) => /^\/(nl|fr)\/(nl|fr)(\/|$)/.test(h))) fails.push(`${p}: the switch offers ${hrefs.join(' ')}`)
  }
  await close()
  ok(fails.length === 0, 'the hero has a pause button, the map moves by four keys and the split by a tap, the noise bars, the finder and the lightest classes reach 3 : 1, the explanation pages have an h1, and the 404’s switch never doubles a prefix',
    `design wave: ${fails.slice(0, 6).join(' · ')}${fails.length > 6 ? ` (+${fails.length - 6})` : ''}`)
}

// ---- 22. round-2 re-check (6 Oct 2026): focus after a consent choice, the pan's bounds, the banner on short phones ----
if (step(22)) {
  const fails = []
  let banners = 0
  const bare = async (w, h) => {
    const ctx = await chrome.newContext({ viewport: { width: w, height: h } })
    await ctx.route('**/*', (route) => { const u = new URL(route.request().url()); return u.host !== local || /^\/(u\/script\.js|api\/send)/.test(u.pathname) ? route.abort() : route.continue() })
    return { ctx, page: await ctx.newPage() }
  }
  const inBanner = (page) => page.evaluate(() => !!document.querySelector('.consent-banner')?.contains(document.activeElement))
  const mark = (page) => page.evaluate(() => { const e = document.activeElement; if (!e || e === document.body) return 'body'; e.dataset.r2 = '1'; return e.id === 'main' ? 'main' : (e.getAttribute('aria-label') || e.textContent || e.tagName).replace(/\s+/g, ' ').trim().slice(0, 30) })
  // 2.4.3: after Accept or Decline, focus goes back to where it stood before the card (the last stop before it, the
  // control that reopened it on /privacy), else to <main> without scrolling to the top; never to <body>
  for (const [w, h, p, choice] of [[1440, 900, '/', 0], [390, 844, '/data', 1], [1440, 900, '/atlas?city=brussels', 1], [390, 664, '/atlas?city=ghent', 0]]) {
    const { ctx, page } = await bare(w, h)
    await page.goto(base + at(p), { waitUntil: 'load' })
    if (/atlas/.test(p)) await ready(page)
    await sleep(700)
    if (!(await page.locator('.consent-banner').count())) { await ctx.close(); continue }
    banners++
    let last = 'body'
    for (let i = 0; i < 400 && !(await inBanner(page)); i++) {
      await page.evaluate(() => document.querySelectorAll('[data-r2]').forEach((e) => delete e.dataset.r2))
      last = await mark(page)
      await page.keyboard.press('Tab')
    }
    if (!(await inBanner(page))) { fails.push(`${p} ${w}: Tab never reached the banner`); await ctx.close(); continue }
    for (let i = 0; i < choice; i++) await page.keyboard.press('Tab')
    await page.keyboard.press('Enter'); await sleep(400)
    const r = await page.evaluate(() => { const e = document.activeElement; return { back: !!e?.dataset?.r2, body: !e || e === document.body } })
    if (!r.back) fails.push(`${p} ${w}: after the choice focus is on ${r.body ? '<body>' : await focused(page)}, not «${last}»`)
    await ctx.close()
  }
  {
    // /privacy: the reset reopens the card; a choice made at once gives focus back to the reset
    const { ctx, page } = await bare(390, 844)
    await ctx.addInitScript(() => { try { localStorage.setItem('frondia.consent', JSON.stringify({ choice: 'denied', at: '2026-01-01T00:00:00.000Z', v: 1 })) } catch {} })
    await page.goto(base + at('/privacy'), { waitUntil: 'load' }); await sleep(500)
    const reset = page.locator('main button.pill').last()
    if (await reset.count()) {
      await reset.focus(); await page.keyboard.press('Enter'); await sleep(300)
      const cb = page.locator('.consent-banner button').first()
      if (await cb.count()) {
        await cb.focus(); await page.keyboard.press('Enter'); await sleep(300)
        const back = await page.evaluate(() => { const e = document.activeElement; return !!e && e.tagName === 'BUTTON' && !!e.closest('main') })
        if (!back) fails.push(`/privacy: after reset and a choice focus is on ${await focused(page)}`)
      }
    }
    await ctx.close()
  }
  {
    // nothing focused before (a choice by a Tab backwards from the top): <main>, the page not scrolled to its top
    const { ctx, page } = await bare(390, 844)
    await page.goto(base + at('/'), { waitUntil: 'load' }); await sleep(600)
    await page.evaluate(() => scrollTo(0, 900)); await sleep(200)
    const y0 = await page.evaluate(() => scrollY)
    await page.locator('.consent-banner button').nth(1).focus(); await page.keyboard.press('Enter'); await sleep(300)
    const r = await page.evaluate(() => [document.activeElement?.id, scrollY])
    if (r[0] !== 'main' || Math.abs(r[1] - y0) > 1) fails.push(`no stop before the card: focus on «${r[0] || 'body'}», scroll ${y0} → ${r[1]}`)
    await ctx.close()
  }
  // the pan's bounds: 40 presses of a pan key, 60 of an arrow on the map, or 20 long drags leave the city on the stage's
  // free part (at least 40 px of it across and down), at 1440 and 390, every way
  for (const [w, h] of [[1440, 900], [390, 844]]) {
    const { page, close } = await open(chrome, { width: w, height: h })
    for (const how of ['keys', 'arrows', 'drag']) for (const dir of ['left', 'right', 'up', 'down']) {
      await go(page, '/atlas?city=brussels')
      if (how === 'keys') {
        const k = page.locator(`.pan .pan-${dir}`)
        if (!(await k.count()) || !(await k.isVisible())) { fails.push(`${w}: no ${dir} pan key`); continue }
        for (let i = 0; i < 40; i++) await k.click()
      } else if (how === 'arrows') {
        await page.locator('.atlas-map svg').first().focus()
        const key = { left: 'ArrowLeft', right: 'ArrowRight', up: 'ArrowUp', down: 'ArrowDown' }[dir]
        for (let i = 0; i < 60; i++) await page.keyboard.press(key)
      } else {
        const st = await page.evaluate(() => { const b = document.querySelector('.atlas-stage').getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height * (innerWidth > 860 ? 0.5 : 0.3)] })
        const d = { left: [300, 0], right: [-300, 0], up: [0, 200], down: [0, -200] }[dir].map((x) => (w < 500 ? x / 2 : x))
        for (let i = 0; i < 20; i++) { await page.mouse.move(st[0], st[1]); await page.mouse.down(); await page.mouse.move(st[0] + d[0], st[1] + d[1], { steps: 4 }); await page.mouse.up() }
      }
      await sleep(300)
      const o = await page.evaluate(() => {
        const st = document.querySelector('.atlas-stage').getBoundingClientRect(), pn = document.querySelector('.atlas-stage > .panel')?.getBoundingClientRect()
        const { left: x0, top: y0, right: x1, bottom: y1 } = document.querySelector('.atlas-map svg g.sectors').getBoundingClientRect()   // the city's sectors
        const fl = innerWidth > 860 && pn ? pn.right : st.left, fb = innerWidth <= 860 && pn ? pn.top : st.bottom
        return [Math.round(Math.min(x1, st.right) - Math.max(x0, fl)), Math.round(Math.min(y1, fb) - Math.max(y0, st.top))]
      })
      if (o[0] < 40 || o[1] < 40) fails.push(`${w} ${how} ${dir}: ${o[0]} × ${o[1]} px of the city left on the free stage`)
    }
    await close()
  }
  // the banner up on a short phone (320 × 568, 320 × 480): the zoom stays whole on the stage, the sheet and a card end
  // below it, and no Tab stop is hidden under the banner
  for (const [w, h] of [[320, 568], [320, 480]]) for (const v of ['/atlas?city=brussels', '/atlas?city=antwerp&sector=11002A00-']) {
    const { ctx, page } = await bare(w, h)
    await page.goto(base + at(v), { waitUntil: 'load' }); await ready(page); await sleep(700)
    if (!(await page.locator('.consent-banner').count())) { await ctx.close(); continue }
    banners++
    await page.evaluate(() => scrollTo(0, document.documentElement.scrollHeight)); await sleep(200)
    const r = await page.evaluate(() => {
      const R = (s) => { const e = document.querySelector(s); return e && e.getClientRects().length ? e.getBoundingClientRect() : null }
      const st = R('.atlas-stage'), z = R('.zoom'), cb = R('.consent-banner'), out = []
      if (z.top < st.top - 0.5 || z.bottom > st.bottom + 0.5) out.push(`zoom ${Math.round(z.top)}–${Math.round(z.bottom)} off the stage ${Math.round(st.top)}–${Math.round(st.bottom)}`)
      if (z.bottom > cb.top + 0.5) out.push(`zoom under the banner`)
      for (const s of ['.atlas-stage > .panel', '.atlas-stage > .drawer']) { const b = R(s); if (b && b.top < z.bottom + 0.5) out.push(`${s.slice(14)} starts at ${Math.round(b.top)}, over the zoom (to ${Math.round(z.bottom)})`) }
      return out.join(', ')
    })
    if (r) fails.push(`${v} ${w}×${h}: ${r}`)
    await page.evaluate(() => scrollTo(0, 0))
    const hidden = []
    for (let i = 0; i < 70; i++) {
      await page.keyboard.press('Tab')
      const c = await page.evaluate(() => {
        const e = document.activeElement, cb = document.querySelector('.consent-banner')
        if (!e || e === document.body || !cb || cb.contains(e)) return ''
        const a = e.getBoundingClientRect(), b = cb.getBoundingClientRect()
        if (!a.width || !a.height) return ''
        return a.left >= b.left - 0.5 && a.right <= b.right + 0.5 && a.top >= b.top - 0.5 && a.bottom <= b.bottom + 0.5 ? (e.getAttribute('aria-label') || e.textContent || e.tagName).replace(/\s+/g, ' ').trim().slice(0, 30) : ''
      })
      if (c) hidden.push(c)
    }
    if (hidden.length) fails.push(`${v} ${w}×${h}: ${[...new Set(hidden)].join(', ')} under the banner`)
    await ctx.close()
  }
  if (!banners) fails.push('no consent banner on this server: run check-a11y against a server started with CLARITY_ID')
  ok(fails.length === 0, 'after a consent choice focus goes back where it stood (or to <main>, unscrolled); no pan, arrow or drag takes the city off the stage; with the banner up on a short phone the zoom stays whole and the sheet ends below it',
    `round 2: ${fails.slice(0, 6).join(' · ')}${fails.length > 6 ? ` (+${fails.length - 6})` : ''}`)
}

// ---- 23. the consent card on a short screen (round-3 re-check, 6 Oct 2026; needs a server with CLARITY_ID) ----
if (step(23)) {
  // ≤ 400 px tall (a phone on its side, 400 % zoom at 1280 × 1024 = 320 × 256): the card shows its short line, not the
  // paragraph, with the same two buttons alike (≥ 24 px) and the Privacy link; the atlas's zoom can be scrolled whole
  // into view above it with map beside it, and no Tab stop hides under it. Taller screens keep the paragraph.
  // Fails on bd8848d (the card was 214 of 256 px; at 844 × 390 the zoom ran under it)
  const fails = []
  let banners = 0
  for (const [w, h] of [[320, 256], [568, 320], [844, 390], [1280, 360], [320, 568], [390, 844]]) for (const v of ['/atlas?city=brussels', '/atlas?city=antwerp&sector=11002A00-', '/']) {
    const ctx = await chrome.newContext({ viewport: { width: w, height: h } })
    await ctx.route('**/*', (route) => { const u = new URL(route.request().url()); return u.host !== local || /^\/(u\/script\.js|api\/send)/.test(u.pathname) ? route.abort() : route.continue() })
    const page = await ctx.newPage()
    await page.goto(base + at(v), { waitUntil: 'load' })
    if (/atlas/.test(v)) await ready(page)
    await sleep(700)
    if (!(await page.locator('.consent-banner').count())) { await ctx.close(); continue }
    banners++
    const short = h <= 400
    const r = await page.evaluate((short) => {
      const out = [], cb = document.querySelector('.consent-banner'), shown = (e) => !!e && e.getClientRects().length > 0
      const full = cb.querySelector('.consent-text--full'), line = cb.querySelector('.consent-text--short')
      if (shown(full) === short || shown(line) !== short) out.push(`shows the ${shown(line) ? 'short line' : 'paragraph'}`)
      const btns = [...cb.querySelectorAll('button')].filter(shown).map((b) => [b.className, Math.round(b.getBoundingClientRect().height), Math.round(b.getBoundingClientRect().width)])
      if (btns.length !== 2) out.push(`${btns.length} buttons`)
      else if (btns[0][0] !== btns[1][0] || btns[0][1] !== btns[1][1] || btns.some((b) => b[1] < 24 || b[2] < 24)) out.push(`buttons differ or under 24 px: ${btns.map((b) => `${b[2]}×${b[1]}`).join(', ')}`)
      if (cb.querySelector('input, [role="checkbox"], [role="switch"]')) out.push('a pre-set control in the card')
      // each button's word on one line, inside its border (nl «Aan-vaar-den» broke into three lines at 320 px)
      for (const b of [...cb.querySelectorAll('button')].filter(shown)) {
        const r = document.createRange(); r.selectNodeContents(b)
        const rows = new Set([...r.getClientRects()].filter((x) => x.width > 1).map((x) => Math.round(x.top))).size
        if (rows !== 1 || b.scrollWidth > b.clientWidth + 1) out.push(`«${b.textContent.trim()}» in ${rows} lines${b.scrollWidth > b.clientWidth + 1 ? ', past its border' : ''}`)
      }
      const a = cb.querySelector('a.consent-privacy')
      if (!shown(a) || !/\/privacy$/.test(a.getAttribute('href') || '')) out.push('no Privacy link')
      if (short && cb.getBoundingClientRect().height > innerHeight * 0.4) out.push(`card ${Math.round(cb.getBoundingClientRect().height)} of ${innerHeight} px`)
      const z = document.querySelector('.zoom')
      if (z && shown(z)) {
        scrollTo(0, Math.max(0, z.getBoundingClientRect().top + scrollY - 12))
        const zb = z.getBoundingClientRect(), top = cb.getBoundingClientRect().top, st = document.querySelector('.atlas-stage').getBoundingClientRect()
        if (zb.top < 0 || zb.bottom > top + 0.5) out.push(`zoom ${Math.round(zb.top)}–${Math.round(zb.bottom)}, the card from ${Math.round(top)}`)
        if (Math.min(st.bottom, top) - Math.max(st.top, 0) < 134) out.push(`${Math.round(Math.min(st.bottom, top) - Math.max(st.top, 0))} px of the stage above the card`)
        scrollTo(0, 0)
      }
      return out.join(', ')
    }, short)
    if (r) fails.push(`${v} ${w}×${h}: ${r}`)
    const hidden = []
    for (let i = 0; i < (v === '/' ? 40 : 60); i++) {
      await page.keyboard.press('Tab')
      const c = await page.evaluate(() => {
        const e = document.activeElement, cb = document.querySelector('.consent-banner')
        if (!e || e === document.body || !cb || cb.contains(e)) return ''
        const a = e.getBoundingClientRect(), b = cb.getBoundingClientRect()
        if (!a.width || !a.height) return ''
        return a.left >= b.left - 0.5 && a.right <= b.right + 0.5 && a.top >= b.top - 0.5 && a.bottom <= b.bottom + 0.5 ? (e.getAttribute('aria-label') || e.textContent || e.tagName).replace(/\s+/g, ' ').trim().slice(0, 30) : ''
      })
      if (c) hidden.push(c)
    }
    if (hidden.length) fails.push(`${v} ${w}×${h}: ${[...new Set(hidden)].join(', ')} under the card`)
    await ctx.close()
  }
  if (!banners) fails.push('no consent banner on this server: run check-a11y against a server started with CLARITY_ID')
  ok(fails.length === 0, `on a short screen the consent card shows its short line with the same two buttons and the Privacy link, the zoom scrolls whole into view above it, and no Tab stop hides under it (${banners} views)`,
    `short card: ${fails.slice(0, 6).join(' · ')}${fails.length > 6 ? ` (+${fails.length - 6})` : ''}`)
}

// ---- 24. round-3 re-check (6 Oct 2026): the bar measured again when it comes unstuck ----
if (step(24)) {
  // a reader's text spacing applied while the landing is scrolled (the bar stuck): back at the top the bar wraps to more
  // rows and the hero card must start below it. Fails on 76f64d1 (--nav-h kept the one-row height, the card 28 px under)
  const fails = []
  for (const pre of ['', '/nl', '/fr'].filter((x) => !prefix || x === prefix)) {
    const { page, close } = await open(chrome, { width: 320, height: 640 })
    await page.goto(base + (pre || '/'), { waitUntil: 'load' }); await sleep(500)
    await page.evaluate(() => scrollTo(0, 1400)); await sleep(400)
    await page.addStyleTag({ content: '* { line-height: 1.5 !important; letter-spacing: .12em !important; word-spacing: .16em !important; } p { margin-bottom: 2em !important; }' })
    await sleep(400); await page.evaluate(() => scrollTo(0, 0)); await sleep(600)
    const r = await page.evaluate(() => { const n = document.querySelector('header.nav').getBoundingClientRect(), c = document.querySelector('.rustle-card').getBoundingClientRect(); return [Math.round(n.bottom), Math.round(c.top)] })
    if (r[1] < r[0]) fails.push(`${pre || '/'}: the card starts at ${r[1]}, the bar ends at ${r[0]}`)
    await close()
  }
  ok(fails.length === 0, 'text spacing applied while the bar is stuck: back at the top the hero card starts below the wrapped bar',
    `bar after unsticking: ${fails.join(' · ')}`)
}

// ---- 25. small-fixes round (6 Oct 2026): the atlas's consent buttons are the site's ghost pills ----
if (step(25)) {
  // the atlas's tokens have no .pill--ghost, so its two consent buttons showed the browser's face (WebKit grey #c0c0c0,
  // no outline, 42 px on a phone). Against a site page (/data) at the same size, in Chromium and WebKit, the full card
  // and the short one: the same box, radius, font and padding; the ghost fill and blur; a 1-px outline in the page's own
  // --rule-2 and text in its --ink at ≥ 4.5 : 1 on the card, at rest and on hover; Tab's focus ring (2.4.7); and in
  // forced colours (Chromium) an outline that stays. Fails on c440f0a
  let wk = null
  try { wk = await webkit.launch({ headless: true }) } catch { ok(false, '', 'WebKit for playwright-core is not installed: step 25 needs it') }
  const fails = []
  let seen = 0
  const look = (page) => page.evaluate(() => {
    const cb = document.querySelector('.consent-banner')
    if (!cb) return null
    const tok = (v) => { const d = document.createElement('i'); d.style.color = `var(${v})`; cb.append(d); const c = getComputedStyle(d).color; d.remove(); return c }
    return { card: getComputedStyle(cb).backgroundColor, ink: tok('--ink'), rule2: tok('--rule-2'),
      btns: [...cb.querySelectorAll('button')].map((b) => { const c = getComputedStyle(b), q = b.getBoundingClientRect()
        return { w: Math.round(q.width), h: Math.round(q.height), bg: c.backgroundColor, bw: c.borderTopWidth, bs: c.borderTopStyle, bc: c.borderTopColor,
          r: c.borderTopLeftRadius, col: c.color, font: `${c.fontFamily} ${c.fontSize}/${c.lineHeight}`, pad: `${c.paddingTop} ${c.paddingRight} ${c.paddingBottom} ${c.paddingLeft}`,
          blur: c.backdropFilter || c.webkitBackdropFilter || 'none' } }) }
  })
  const SAME = ['w', 'h', 'r', 'font', 'pad', 'bw', 'bs', 'bg', 'blur']
  for (const [name, browser] of [['Chromium', chrome], ['WebKit', wk]]) {
    if (!browser) continue
    for (const [w, h] of [[320, 640], [390, 844], [1440, 900], [568, 320], [320, 256]]) {
      const got = {}
      for (const v of ['/data', '/atlas?city=brussels']) {
        const ctx = await browser.newContext({ viewport: { width: w, height: h } })
        await ctx.route('**/*', (route) => { const u = new URL(route.request().url()); return u.host !== local || /^\/(u\/script\.js|api\/send)/.test(u.pathname) ? route.abort() : route.continue() })
        const page = await ctx.newPage()
        await page.goto(base + at(v), { waitUntil: 'load' })
        if (/atlas/.test(v)) await ready(page)
        await sleep(600)
        const g = await look(page)
        if (!g) { await ctx.close(); continue }
        seen++
        const where = `${name} ${w}×${h} ${v}`
        for (const b of g.btns) {
          if (b.bc !== g.rule2 || b.bs !== 'solid' || b.bw !== '1px') fails.push(`${where}: outline ${b.bw} ${b.bs} ${b.bc}, not 1px solid ${g.rule2}`)
          if (b.col !== g.ink) fails.push(`${where}: text ${b.col}, not the page's ink ${g.ink}`)
          const c = ratio(b.col, over(b.bg, g.card))
          if (c < 4.5) fails.push(`${where}: text ${c.toFixed(2)} : 1 on ${b.bg}`)
        }
        // hover: the ghost fill thickens, the text keeps its contrast
        await page.locator('.consent-banner button').first().hover(); await sleep(350)
        const hv = await page.evaluate(() => getComputedStyle(document.querySelector('.consent-banner button')).backgroundColor)
        const rest = g.btns[0].bg
        if (hv === rest) fails.push(`${where}: no hover (${hv})`)
        else if (ratio(g.btns[0].col, over(hv, g.card)) < 4.5) fails.push(`${where}: hover text under 4.5 : 1`)
        // Tab from Accept to Decline (Option+Tab in WebKit, whose plain Tab skips buttons): the focus ring shows
        await page.locator('.consent-banner button').first().focus()
        await page.keyboard.press(name === 'WebKit' ? 'Alt+Tab' : 'Tab'); await sleep(150)
        const ring = await page.evaluate(() => { const e = document.activeElement, c = getComputedStyle(e); return e.matches('.consent-banner button:focus-visible') ? `${c.outlineStyle} ${c.outlineWidth} ${c.outlineColor}` : `focus on ${e.tagName}` })
        if (!/^solid 2px /.test(ring)) fails.push(`${where}: focus ring ${ring}`)
        got[v] = { ...g, hover: hv }
        await ctx.close()
      }
      const [s, a] = [got['/data'], got['/atlas?city=brussels']]
      if (!s || !a) { fails.push(`${name} ${w}×${h}: no banner on ${!s ? '/data' : 'the atlas'}`); continue }
      for (let i = 0; i < 2; i++) for (const k of SAME) if (s.btns[i][k] !== a.btns[i][k]) fails.push(`${name} ${w}×${h} button ${i + 1}: ${k} ${a.btns[i][k]} on the atlas, ${s.btns[i][k]} on /data`)
      if (s.hover !== a.hover) fails.push(`${name} ${w}×${h}: hover ${a.hover} on the atlas, ${s.hover} on /data`)
    }
  }
  // forced colours (Chromium only emulates them): the outline is still drawn, as on the site's pages
  for (const v of ['/data', '/atlas?city=brussels']) {
    const ctx = await chrome.newContext({ viewport: { width: 390, height: 844 }, forcedColors: 'active' })
    await ctx.route('**/*', (route) => { const u = new URL(route.request().url()); return u.host !== local || /^\/(u\/script\.js|api\/send)/.test(u.pathname) ? route.abort() : route.continue() })
    const page = await ctx.newPage()
    await page.goto(base + at(v), { waitUntil: 'load' })
    if (/atlas/.test(v)) await ready(page)
    await sleep(600)
    const r = await page.evaluate(() => [...document.querySelectorAll('.consent-banner button')].map((b) => { const c = getComputedStyle(b); return `${c.borderTopStyle} ${c.borderTopWidth} ${c.borderTopColor} | ${c.color} on ${c.backgroundColor}` }))
    seen++
    for (const x of r) if (!/^solid 1px rgb\(/.test(x)) fails.push(`forced colours ${v}: ${x}`)
    if (r.length !== 2) fails.push(`forced colours ${v}: ${r.length} buttons`)
    await ctx.close()
  }
  ok(fails.length === 0 && seen > 2, `the atlas's consent buttons are the site's ghost pills: same box, fill, outline, hover, focus ring and forced-colour outline, text ≥ 4.5 : 1 (Chromium and WebKit; 320, 390, 1440, the short card at 568 × 320 and 320 × 256)`,
    seen <= 2 ? 'no consent banner on this server: run check-a11y against a server started with CLARITY_ID' : `consent pills: ${fails.slice(0, 6).join(' · ')}${fails.length > 6 ? ` (+${fails.length - 6})` : ''}`)
  await wk?.close()
}

// ---- 26. small-fixes round (6 Oct 2026): the pan keys hang --s-10 from the zoom ----
if (step(26)) {
  // the Felt ladder's hang step (10) between the cross and the zoom, as beside it: above the zoom on a desktop (with and
  // without a card, with the consent banner up), under it on a phone, and 10 to its left on a short stage. Fails on
  // c440f0a (8 above and under)
  const fails = []
  for (const [w, h, v, banner, side] of [[1440, 900, '/atlas?city=brussels', false, 'above'], [1440, 900, '/atlas?city=brussels&sector=21004E72-', false, 'above'],
    [1440, 900, '/atlas?city=brussels', true, 'above'], [390, 844, '/atlas?city=brussels', false, 'under'], [720, 450, '/atlas?city=brussels', false, 'beside']]) {
    const ctx = await chrome.newContext({ viewport: { width: w, height: h } })
    if (!banner) await ctx.addInitScript(() => { try { localStorage.setItem('frondia.consent', JSON.stringify({ choice: 'denied', at: '2026-01-01T00:00:00.000Z', v: 1 })) } catch {} })
    await ctx.route('**/*', (route) => { const u = new URL(route.request().url()); return u.host !== local || /^\/(u\/script\.js|api\/send)/.test(u.pathname) ? route.abort() : route.continue() })
    const page = await ctx.newPage()
    await page.goto(base + at(v), { waitUntil: 'load' }); await ready(page); await sleep(600)
    const r = await page.evaluate(() => {
      const p = document.querySelector('.pan'), z = document.querySelector('.zoom')
      if (!p || !p.getClientRects().length) return null
      const a = p.getBoundingClientRect(), b = z.getBoundingClientRect()
      return { above: b.top - a.bottom, under: a.top - b.bottom, beside: b.left - a.right, banner: !!document.querySelector('.consent-banner') }
    })
    const where = `${w}×${h} ${v}${banner ? ' (banner up)' : ''}`
    if (!r) fails.push(`${where}: no pan keys`)
    else if (banner && !r.banner) fails.push(`${where}: no consent banner (start the server with CLARITY_ID)`)
    else if (Math.abs(r[side] - 10) > 0.5) fails.push(`${where}: ${Math.round(r[side] * 10) / 10} px ${side} the zoom`)
    await ctx.close()
  }
  ok(fails.length === 0, 'the pan keys sit 10 px (--s-10) from the zoom: above it on a desktop, with a card and with the banner, under it on a phone, beside it on a short stage',
    `pan gap: ${fails.join(' · ')}`)
}

await chrome.close()
console.log(bad ? `\n${bad} ✗` : '\nall ✓')
process.exit(bad)
