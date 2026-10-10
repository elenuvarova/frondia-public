// Re-check 4: privacy and the CSP, on a real browser against a running server. Every host other than the server is
// aborted, so nothing reaches Umami, Clarity, Bing or any CDN; the aborted requests are what this check reads.
//
// 1. Before any choice, on every page type (landing, atlas, a sector, an audit, dossier, commune, data, register,
//    privacy, the 404): no request leaves the site (no font, map tile, CDN, Google, Clarity), no cookie is set, and
//    the page logs no CSP violation (the nonce reaches every script: Next's, Umami's, the atlas's early fetch).
// 2. Needs CLARITY_ID (the banner is on): Clarity is requested only after Accept, and only from www.clarity.ms.
// 3. Withdrawal, across tabs: with Clarity's cookies present (_clck, _clsk — set here, since the real tag is aborted),
//    "Change your choice" → Decline on /privacy in a second tab reloads the first, both lose the cookies, and the
//    reloaded first tab asks Clarity for nothing.
// 4. Decline from the start: nothing from Clarity on a fresh load either.
// 5. The hero's pause (round-2 re-check, 6 Oct 2026): pressing it stores only «frondia.motion-paused» = "1" in session
//    storage (no cookie, nothing in local storage, no request), and /privacy names it in en, nl and fr.
// 6. Needs CLARITY_ID. The short card (≤ 400 px tall; round-3 re-check, 6 Oct 2026) asks the same question: in en, nl
//    and fr its line names Microsoft Clarity and its cookies and the card links that language's /privacy; nothing is
//    asked of Clarity and no cookie is set before a choice; Accept then asks for Clarity's tag only; Decline asks for
//    nothing, sets nothing, and the card stays away after a reload.
//
// Usage: node scripts/check-privacy.mjs [baseUrl]   (default http://localhost:5192; start it with CLARITY_ID=test)
// Prints strings only — never a whole page, request or environment object.
import { chromium } from 'playwright-core'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const base = process.argv[2] || 'http://localhost:5192'
const origin = new URL(base).origin
const EXE = path.join(os.homedir(), 'Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
let bad = 0
const ok = (cond, yes, no) => { if (cond) console.log(`✓ ${yes}`); else { bad++; console.log(`✗ ${no}`) } }

const browser = await chromium.launch({ headless: true, executablePath: fs.existsSync(EXE) ? EXE : undefined })

async function context(opts = {}) {
  const ctx = await browser.newContext(opts)
  const outside = []
  await ctx.route('**/*', (route) => {
    const u = new URL(route.request().url())
    if (u.origin === origin || u.protocol === 'data:' || u.protocol === 'blob:') return route.continue()
    outside.push(u.host + u.pathname)
    return route.abort()
  })
  return { ctx, outside }
}
const watchCsp = (page, into) => page.on('console', (m) => { if (/Content Security Policy/i.test(m.text())) into.push(m.text().slice(0, 140)) })

// ---- 1. before any choice ----
const PAGES = ['/', '/atlas', '/atlas?city=ghent&q=need', '/atlas?city=brussels&sector=21004A22-', '/atlas?city=brussels&audit=ninove',
  '/dossier', '/commune?code=21001', '/data?city=ghent', '/register', '/privacy', '/foo']
{
  const { ctx, outside } = await context()
  const csp = []
  for (const at of PAGES) {
    const page = await ctx.newPage()
    watchCsp(page, csp)
    const res = await page.goto(base + at, { waitUntil: 'networkidle' })
    await sleep(400)
    const h = res.headers()['content-security-policy'] || ''
    ok(/'nonce-[^']+'/.test(h) && !/script-src[^;]*unsafe-inline/.test(h), `${at}: CSP with a nonce, no unsafe-inline for scripts`, `${at}: CSP is “${h.slice(0, 80)}”`)
    await page.close()
  }
  ok(outside.length === 0, `before any choice, ${PAGES.length} pages: no request left the site`, `requests left the site: ${[...new Set(outside)].join(', ')}`)
  ok(csp.length === 0, 'no CSP violation on any page', `${csp.length} CSP violation(s), first: ${csp[0]}`)
  const cookies = await ctx.cookies()
  ok(cookies.length === 0, 'no cookie set before any choice', `cookies before any choice: ${cookies.map((c) => c.name).join(', ')}`)
  await ctx.close()
}

// ---- 2. Accept loads Clarity, and only then ----
const hasBanner = await (async () => { const { ctx } = await context(); const p = await ctx.newPage(); await p.goto(base + '/', { waitUntil: 'networkidle' }); const n = await p.waitForSelector('.consent-banner', { timeout: 4000 }).then(() => 1, () => 0); await ctx.close(); return n > 0 })()
if (!hasBanner) console.log('· no consent banner on this server (no CLARITY_ID): steps 2–4 are skipped')
else {
  const { ctx, outside } = await context()
  const page = await ctx.newPage()
  await page.goto(base + '/', { waitUntil: 'networkidle' }); await sleep(500)
  ok(outside.length === 0, 'with the banner up: nothing requested from Clarity', `before Accept: ${outside.join(', ')}`)
  await page.getByRole('button', { name: 'Accept' }).click(); await sleep(800)
  const after = [...new Set(outside)]
  ok(after.length > 0 && after.every((h) => h.startsWith('www.clarity.ms/tag/')), `after Accept: Clarity's tag requested (${after.join(', ')}), nothing else`, `after Accept: ${after.join(', ') || 'nothing requested'}`)

  // ---- 3. withdrawal in another tab ----
  const host = new URL(base).hostname
  await ctx.addCookies(['_clck', '_clsk'].map((name) => ({ name, value: 'x', domain: host, path: '/' })))
  const second = await ctx.newPage()
  await second.goto(base + '/privacy', { waitUntil: 'networkidle' })
  const mark = outside.length
  const reloaded = page.waitForEvent('load', { timeout: 8000 }).then(() => true, () => false)
  await second.getByRole('button', { name: 'Change your choice' }).click(); await sleep(300)
  await second.getByRole('button', { name: 'Decline' }).click()
  ok(await reloaded, 'Decline in another tab reloads the tab where Clarity ran', 'the first tab did not reload after Decline in the second')
  await sleep(1200)
  const left = (await ctx.cookies()).filter((c) => c.name === '_clck' || c.name === '_clsk').map((c) => c.name)
  ok(left.length === 0, 'Clarity’s cookies are gone after the withdrawal', `cookies left after Decline: ${left.join(', ')}`)
  ok(outside.slice(mark).length === 0, 'after the withdrawal nothing more is asked of Clarity', `after Decline: ${outside.slice(mark).join(', ')}`)
  await ctx.close()

  // ---- 4. Decline from the start ----
  const d = await context()
  const p = await d.ctx.newPage()
  await p.goto(base + '/', { waitUntil: 'networkidle' })
  await p.getByRole('button', { name: 'Decline' }).click(); await sleep(300)
  await p.reload({ waitUntil: 'networkidle' }); await sleep(500)
  ok(d.outside.length === 0 && (await d.ctx.cookies()).length === 0, 'Decline: no Clarity request and no cookie, before or after a reload', `Decline: ${d.outside.join(', ')}`)
  await d.ctx.close()
}

// ---- 5. the hero's pause: what it keeps, and /privacy says so ----
{
  const { ctx, outside } = await context()
  const page = await ctx.newPage()
  await page.goto(base + '/', { waitUntil: 'networkidle' })
  const btn = page.locator('.hero-rustle .rustle-pause')
  if (await btn.count()) {
    const n0 = outside.length
    await btn.click(); await sleep(300)
    const kept = await page.evaluate(() => [Object.keys(sessionStorage).map((k) => `${k}=${sessionStorage.getItem(k)}`).join(' '), Object.keys(localStorage).join(' ')])
    ok(kept[0] === 'frondia.motion-paused=1' && kept[1] === '' && (await ctx.cookies()).length === 0 && outside.length === n0,
      'the hero’s pause keeps only frondia.motion-paused=1 in session storage: no cookie, no local storage, no request',
      `the pause kept: session «${kept[0]}», local «${kept[1]}», ${(await ctx.cookies()).length} cookie(s), ${outside.length - n0} request(s) out`)
  } else ok(false, '', 'the landing has no pause button')
  const says = { '': [/pause/i, /session storage/i, /no personal data/i, /never leaves your browser/i],
    '/nl': [/pauzeert/i, /sessieopslag/i, /geen persoonsgegevens/i, /verlaat uw browser nooit/i],
    '/fr': [/en pause/i, /stockage de session/i, /aucune donnée personnelle/i, /ne quitte jamais votre navigateur/i] }
  for (const [pre, res] of Object.entries(says)) {
    await page.goto(base + pre + '/privacy', { waitUntil: 'networkidle' })
    // the typography's no-break spaces and soft hyphens read as plain spaces and nothing
    const text = (await page.locator('main').innerText()).replace(/[\u00a0\u202f]/g, ' ').replace(/\u00ad/g, '')
    const para = text.split(/\n+/).find((l) => res[1].test(l)) || ''
    ok(res.every((r) => r.test(para)), `${pre || '/en'}/privacy names the pause kept in session storage, with no personal data, never leaving the browser`,
      `${pre || '/en'}/privacy: no paragraph names the pause in session storage${para ? ` (found «${para.slice(0, 80)}»)` : ''}`)
  }
  await ctx.close()
}

// ---- 6. the short card asks the same question ----
if (hasBanner) {
  const SHORT = { width: 568, height: 320 }
  for (const pre of ['', '/nl', '/fr']) {
    const { ctx, outside } = await context({ viewport: SHORT })
    const page = await ctx.newPage()
    await page.goto(base + (pre || '/'), { waitUntil: 'networkidle' }); await page.waitForSelector('.consent-banner', { timeout: 4000 }).catch(() => {}); await sleep(400)
    const card = await page.evaluate(() => {
      const cb = document.querySelector('.consent-banner'); if (!cb) return null
      const shown = [...cb.querySelectorAll('p')].filter((p) => p.getClientRects().length).map((p) => p.innerText.replace(/[  ]/g, ' '))
      return { shown, buttons: [...cb.querySelectorAll('button')].filter((b) => b.getClientRects().length).map((b) => b.dataset.evChoice), href: cb.querySelector('a.consent-privacy')?.getAttribute('href') }
    })
    ok(!!card && card.shown.length === 1 && card.shown[0].length <= 90 && /Microsoft Clarity/.test(card.shown[0]) && /cookies/.test(card.shown[0]) && card.href === `${pre}/privacy` && card.buttons.join() === 'granted,denied',
      `${pre || '/en'} at 568 × 320: one short line naming Microsoft Clarity and its cookies, Accept and Decline, and ${pre}/privacy`,
      `${pre || '/en'} at 568 × 320: ${card ? `lines «${card.shown.join(' | ').slice(0, 90)}», buttons ${card.buttons.join()}, link ${card.href}` : 'no card'}`)
    ok(outside.length === 0 && (await ctx.cookies()).length === 0, `${pre || '/en'} short card up: nothing asked of Clarity, no cookie`, `${pre || '/en'} short card up: ${outside.join(', ')}`)
    const choice = pre === '/nl' ? 'granted' : 'denied'   // Decline in en and fr, Accept in nl
    await page.locator(`.consent-banner button[data-ev-choice="${choice}"]`).click(); await sleep(800)
    const after = [...new Set(outside)]
    if (choice === 'granted') ok(after.length > 0 && after.every((h) => h.startsWith('www.clarity.ms/tag/')), `${pre || '/en'} short card, Accept: Clarity's tag only`, `${pre || '/en'} short card, Accept: ${after.join(', ') || 'nothing requested'}`)
    else {
      await page.reload({ waitUntil: 'networkidle' }); await sleep(500)
      ok(outside.length === 0 && (await ctx.cookies()).length === 0 && !(await page.locator('.consent-banner').count()), `${pre || '/en'} short card, Decline: nothing asked, no cookie, no card after a reload`, `${pre || '/en'} short card, Decline: ${outside.join(', ')}`)
    }
    await ctx.close()
  }
}

await browser.close()
console.log(bad ? `\n${bad} check(s) failed` : '\nall privacy checks passed')
process.exit(bad ? 1 : 0)
