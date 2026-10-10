// Visible text of the old and the new site, page by page: the move to Next must not change a word.
import { chromium } from 'playwright-core'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const [oldBase, newBase, ...paths] = process.argv.slice(2)
const PATHS = paths.length ? paths : ['/']
const EXE = path.join(os.homedir(), 'Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
const OUT = path.join(import.meta.dirname, '../.parity')
fs.mkdirSync(OUT, { recursive: true })

const norm = (s) => s.replace(/[  ]/g, ' ').replace(/⁠/g, '').split('\n').map((l) => l.replace(/\s+/g, ' ').trim()).filter(Boolean)

// the old Vite atlas (tag vite-apps-final) is served at /atlas/ only; a Next base answers /atlas/ with a 308 to the same view
const oldPath = (p) => p.replace(/^\/atlas(?=\?|$)/, '/atlas/')
const isAtlas = (url) => /^\/(?:[a-z]{2}\/)?atlas\/?$/.test(new URL(url).pathname)

async function grab(page, url, width) {
  await page.setViewportSize({ width, height: 900 })
  const u = new URL(url)
  u.searchParams.set('clean', '')
  await page.goto(u.toString(), { waitUntil: 'networkidle' })
  // the atlas reads its city in the browser: its panel heading is there once the data is
  if (isAtlas(url)) await page.waitForSelector('.panel h1', { timeout: 20000 })
  await page.evaluate(() => document.querySelectorAll('details').forEach((d) => { d.open = true }))
  // the skip link (re-check 2) is on every new page and on none of the old ones: words of the page only
  await page.evaluate(() => document.querySelector('.skip-link')?.remove())
  await page.waitForTimeout(800)
  return norm(await page.evaluate(() => document.body.innerText))
}

// Shift-proof comparison: one inserted or removed line must not flood the report with a wall of
// off-by-one noise. Compare the two line lists as multisets first (what's missing from the new
// page, what's extra in it, regardless of position), then separately point at the first line
// where the two texts actually diverge, with a little context, so a real rewrite is still easy
// to spot.
function multisetDiff(a, b) {
  const remA = new Map()
  for (const l of a) remA.set(l, (remA.get(l) || 0) + 1)
  const remB = new Map()
  for (const l of b) remB.set(l, (remB.get(l) || 0) + 1)
  for (const [k, cb] of remB) {
    const ca = remA.get(k) || 0
    const matched = Math.min(ca, cb)
    remA.set(k, ca - matched)
    remB.set(k, cb - matched)
  }
  const missing = []
  for (const [k, c] of remA) for (let i = 0; i < c; i++) missing.push(k)
  const extra = []
  for (const [k, c] of remB) for (let i = 0; i < c; i++) extra.push(k)
  return { missing, extra }
}

function report(p, w, a, b) {
  const { missing, extra } = multisetDiff(a, b)
  if (!missing.length && !extra.length) { console.log(`✓ ${p} @${w} (${a.length} lines)`); return true }
  console.log(`✗ ${p} @${w}`)
  if (missing.length) {
    console.log(`  missing in new (${missing.length}):`)
    for (const l of missing.slice(0, 15)) console.log(`    - ${l}`)
  }
  if (extra.length) {
    console.log(`  extra in new (${extra.length}):`)
    for (const l of extra.slice(0, 15)) console.log(`    + ${l}`)
  }
  let firstDiv = -1
  for (let i = 0; i < Math.max(a.length, b.length); i++) if (a[i] !== b[i]) { firstDiv = i; break }
  if (firstDiv >= 0) {
    const lo = Math.max(0, firstDiv - 2), hi = firstDiv + 2
    console.log(`  first divergence at line ${firstDiv}:`)
    console.log(`  old[${lo}..${hi}]:`)
    for (let i = lo; i <= hi && i < a.length; i++) console.log(`    ${i}: ${a[i]}`)
    console.log(`  new[${lo}..${hi}]:`)
    for (let i = lo; i <= hi && i < b.length; i++) console.log(`    ${i}: ${b[i]}`)
  }
  return false
}

const browser = await chromium.launch({ headless: true, executablePath: fs.existsSync(EXE) ? EXE : undefined })
const page = await browser.newPage()
// never a real count: Umami's tracker and sends, Clarity and Microsoft's pixel are answered here
await page.route(/stats\.frondia\.eu|\/u\/script\.js|\/api\/send|clarity\.ms|c\.bing\.com/, (r) => r.abort())
// The consent banner is client-side and checked separately (the live check below); pre-set a
// denied choice so its text never shows up as an "extra" line in this comparison.
await page.addInitScript(() => localStorage.setItem('frondia.consent', JSON.stringify({ choice: 'denied', at: '2026-01-01T00:00:00.000Z', v: 1 })))
let bad = 0
for (const p of PATHS) for (const w of [1440, 390]) {
  const a = await grab(page, oldBase + oldPath(p), w)
  await page.screenshot({ path: path.join(OUT, `${p.replace(/\W+/g, '_')}-${w}-old.png`), fullPage: false })
  const b = await grab(page, newBase + p, w)
  await page.screenshot({ path: path.join(OUT, `${p.replace(/\W+/g, '_')}-${w}-new.png`), fullPage: false })
  if (!report(p, w, a, b)) bad++
}
await browser.close()
process.exit(bad ? 1 : 0)
