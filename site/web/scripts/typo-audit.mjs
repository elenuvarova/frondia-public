// Line-break audit (27 Sep 2026 rules, ported from the Vite-site scratchpad reference). Every visible
// text block, every width. For each rendered line it looks at the last word and the first word: a line
// must not end on a short word, must not start with a dash, separator or closing sign, a number must
// not part from the word it counts, and a digit range must not break at its dash. Since re-check 1
// (3 Oct) it also flags an underlined block that wraps on a leading under 1.3, a page wider than the
// screen, and a header element that runs past the screen's edge; since re-check 3, a count or an area of
// four digits or more printed without its thousands separator; since plan 5's task 2, a pill, chip, tag or segmented
// pair that runs out of the box holding it (a drawer, a card, the screen).
//
// Usage: node web/scripts/typo-audit.mjs <base> [widths] [pages.json] [prefix]
//   <base>    e.g. https://frondia.ontwrpn.com or http://localhost:3000
//   [widths]  comma-separated, default the 16 widths from the 27 Sep run
//   [pages]   a JSON file of pages, default web/scripts/pages.json (the atlas's are web/scripts/atlas-pages.json)
//   [prefix]  a language prefix put before every path, e.g. /nl or /xx (the pseudo-language); "/" becomes the prefix
//             alone. An empty [widths] ('') keeps the default widths
//   --no-hyphens  Dutch without its hyphenation (:lang(nl) * { hyphens: manual }), and a word broken inside is then a
//             finding in Dutch too. Headless Chromium has no hyphenation dictionary: under hyphens: auto it breaks a long
//             word anywhere, so the allowance below hides a word that does not fit; this pass shows it (fix round 1)
//
// Page paths come from web/scripts/pages.json — an array of { "path": "/…" } objects (the reference
// script's own shape; a plain array of strings was the other option, this file picked the object shape
// so it also carries room for a future per-page override without changing the format again).
//
// The short-word list is picked per page by document.documentElement.lang (first two letters), not by
// a single global constant, because the Next site serves en/nl/fr. Since plan 5's task 14 the language adds its own
// rules: in French a line does not end on an opening « nor on n°, and does not start with », :, ;, ! or ? (BAD_START);
// in Dutch a line does not end on nr.; and a word broken inside itself (one token on two lines, the break between two
// letters or digits) is allowed only in Dutch, and only in the text it hyphenates (brand.css, hyphens: auto); with
// --no-hyphens not even there.
import { chromium } from 'playwright-core'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

const NO_HYPHENS = process.argv.includes('--no-hyphens')
const [base, widthsArg, pagesArg, prefixArg = ''] = process.argv.slice(2).filter((a) => a !== '--no-hyphens')
const prefix = prefixArg.replace(/\/+$/, '')   // '/xx/' and '/xx' are the same prefix
if (!base) {
  console.error('Usage: node web/scripts/typo-audit.mjs <base> [widths] [pages.json] [prefix]')
  process.exit(2)
}
const BASE = base
const WIDTHS = (widthsArg || '320,360,375,390,414,430,600,768,820,1024,1180,1280,1366,1440,1536,1920').split(',').map(Number)
const PAGES = JSON.parse(fs.readFileSync(pagesArg ? path.resolve(pagesArg) : new URL('./pages.json', import.meta.url)))
  .map((p) => (prefix && !p.path.startsWith('http') ? { ...p, path: p.path === '/' ? prefix : prefix + p.path } : p))
const EXE = path.join(os.homedir(), 'Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')

// the short words the site ties (lib/typography.ts reads them through i18n/locales.ts): one copy of the rules
const SHORT_BY_LANG = JSON.parse(fs.readFileSync(new URL('../i18n/short-words.json', import.meta.url)))

function audit({ shortWords, lang, noHyphens }) {
  const SHORT = new RegExp(`^(\\p{L}{1,2}|${shortWords})$`, 'iu')
  const BAD_START = /^[—–·→×%)\]}:;,.!?’”»/+=]/u
  const NUM = /^[+−\-±]?\d(?:[\d.,:%×–⁠]*[\d%×])?$/u
  const blockOf = (el) => { for (let p = el; p; p = p.parentElement) { const d = getComputedStyle(p).display; if (d !== 'inline' && d !== 'contents') return p } return document.body }
  const visible = (el) => { const r = el.getBoundingClientRect(); if (!r.width || !r.height) return false; const s = getComputedStyle(el); return s.visibility !== 'hidden' && s.opacity !== '0' }
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
  const blocks = new Map()
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const el = n.parentElement
    if (!el || el.closest('svg, script, style, [data-no-tie], [aria-hidden="true"], .odometer, noscript')) continue
    if (!n.nodeValue.trim() || !visible(el)) continue
    const b = blockOf(el)
    if (!blocks.has(b)) blocks.set(b, [])
    const text = n.nodeValue
    const toks = text.split(/([ \t\n\r]+)/)   // ordinary whitespace only: no-break spaces glue a token
    let i = 0
    for (const t of toks) {
      if (t && !/^[ \t\n\r]+$/.test(t)) {
        const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + t.length)
        const rects = [...r.getClientRects()].filter((q) => q.width > 0)
        if (rects.length) blocks.get(b).push({ t, el, node: n, off: i, rects, top: rects[0].top, bottom: rects[rects.length - 1].top })
      }
      i += t.length
    }
  }
  const issues = []
  for (const [b, toks] of blocks) {
    if (toks.length < 2) continue
    const lines = []
    let cur = [toks[0]]
    for (let k = 1; k < toks.length; k++) {
      const a = toks[k - 1], z = toks[k]
      const lh = Math.max(4, (a.rects[a.rects.length - 1].height || 10) * 0.5)
      if (z.top > a.bottom + lh) { lines.push(cur); cur = [z] } else cur.push(z)
    }
    lines.push(cur)
    const ctx = (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90)
    for (let L = 0; L < lines.length; L++) {
      const line = lines[L]
      const last = line[line.length - 1], first = line[0]
      const lastWord = last.t.split(/ /).pop()
      if (L < lines.length - 1) {
        const nxt = lines[L + 1][0]
        if (SHORT.test(lastWord)) issues.push({ kind: 'short word at line end', at: `${lastWord} ⏎ ${nxt.t}`, ctx })
        else if (lang === 'fr' && /^(?:«|n°)$/i.test(lastWord)) issues.push({ kind: 'sign at line end', at: `${lastWord} ⏎ ${nxt.t}`, ctx })
        else if (lang === 'nl' && /^nr\.$/i.test(lastWord)) issues.push({ kind: 'sign at line end', at: `${lastWord} ⏎ ${nxt.t}`, ctx })
        else if (NUM.test(lastWord) && /^\p{L}/u.test(nxt.t)) issues.push({ kind: 'number parted from word', at: `${lastWord} ⏎ ${nxt.t}`, ctx })
      }
      if (L > 0 && BAD_START.test(first.t)) issues.push({ kind: 'line starts with sign', at: `${lines[L - 1][lines[L - 1].length - 1].t} ⏎ ${first.t}`, ctx })
    }
    // an underlined block that wraps needs the room for its line: at a leading under 1.3 its underline runs through the
    // next line's letters (the landing's "Find your commune" link at 320 had 14 on 14, re-check 1)
    const bs = getComputedStyle(b)
    const under = toks.some((tk) => /underline/.test(getComputedStyle(tk.el).textDecorationLine))
    if (under && lines.length > 1 && parseFloat(bs.lineHeight) < 1.3 * parseFloat(bs.fontSize)) issues.push({ kind: 'underlined lines too tight', at: `${bs.fontSize}/${bs.lineHeight}`, ctx })
    for (const tk of toks) {
      if (/\d[-–]\d/.test(tk.t)) {
        const tops = new Set(tk.rects.map((q) => Math.round(q.top)))
        if (tops.size > 1) issues.push({ kind: 'range broken at dash', at: tk.t, ctx })
      } else if (!(lang === 'nl' && !noHyphens && getComputedStyle(tk.el).hyphens === 'auto') && new Set(tk.rects.map((q) => Math.round(q.top))).size > 1) {
        // a word on two lines: fine at its own punctuation (Bruxelles-Capitale, a code's lau2024.BE.<NIS>), a break
        // between two letters or digits is a hyphenation or a forced wrap, which only Dutch allows, and only where it
        // hyphenates (and not under --no-hyphens)
        const node = tk.node, start = tk.off
        {
          let prev = null
          for (let c = 0; c < tk.t.length; c++) {
            const r = document.createRange(); r.setStart(node, start + c); r.setEnd(node, start + c + 1)
            // the char's last box: a letter after a soft hyphen reports the hyphen drawn on the line before as well
            const q = [...r.getClientRects()].filter((x) => x.width > 0).pop()
            if (!q) continue
            if (prev != null && q.top > prev + 2 && /[\p{L}\p{N}]/u.test(tk.t[c - 1]) && /[\p{L}\p{N}]/u.test(tk.t[c])) { issues.push({ kind: 'word broken inside', at: `${tk.t.slice(0, c)} ⏎ ${tk.t.slice(c)}`, ctx }); break }
            prev = q.top
          }
        }
      }
    }
  }
  // a count or an area of four digits or more is grouped, as int() groups it (7,180 residents): the commune
  // page's zero measurement printed "10311 ha" beside "269,597" residents (re-check 3)
  for (const m of (document.body.innerText || '').matchAll(/(?<![\d.,])\d{4,}(?=[ \u00A0\u202F]?(?:ha|km²|km|m²|m|residents|trees|contracts|sectors|people|points|inwoners|bomen|contracten|sectoren|mensen|punten|habitants|arbres|contrats|secteurs|personnes)\b)/g)) {
    issues.push({ kind: 'number not grouped', at: m[0], ctx: document.body.innerText.slice(Math.max(0, m.index - 40), m.index + 20).replace(/\s+/g, ' ') })
  }
  // nothing wider than the screen: no sideways scroll, and no bar (a site's nav, the atlas's bar) running past the edge
  // (at 320 the nav's pill ended 2 px beyond it, re-check 1)
  const vw = document.documentElement.clientWidth
  // a bar that scrolls sideways on purpose (the atlas's, between 861 and its full width) keeps its overflow inside
  const scrollsInside = (el) => { for (let p = el.parentElement; p; p = p.parentElement) if (/auto|scroll/.test(getComputedStyle(p).overflowX)) return true; return false }
  if (document.documentElement.scrollWidth > vw) issues.push({ kind: 'page wider than the screen', at: `${document.documentElement.scrollWidth} > ${vw}`, ctx: 'the page' })
  for (const el of document.querySelectorAll('.nav *, .atlas-bar *')) {
    const r = el.getBoundingClientRect()
    if (r.width && visible(el) && (r.right > vw + 0.5 || r.left < -0.5) && !scrollsInside(el)) {
      issues.push({ kind: 'bar runs past the screen', at: `${el.tagName.toLowerCase()} ${Math.round(r.left)}–${Math.round(r.right)} of ${vw}`, ctx: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60) })
      break
    }
  }
  // a pill, a chip, a tag or a segmented pair never runs out of the box that holds it — the nearest ancestor that clips or
  // scrolls (a drawer, a card), or the screen. Only the bars above may scroll sideways on purpose; a drawer that does is a
  // bug (plan 5, task 2: the pseudo-language's dossier link made the 296-px drawer scroll, a refusal chip ran 80 px out)
  const boxOf = (el) => {
    for (let p = el.parentElement; p && p !== document.body && p !== document.documentElement; p = p.parentElement) {
      if (getComputedStyle(p).overflowX !== 'visible') {
        const r = p.getBoundingClientRect()
        return { el: p, left: r.left + p.clientLeft, right: r.left + p.clientLeft + p.clientWidth }
      }
    }
    return { el: null, left: 0, right: vw }
  }
  for (const el of document.querySelectorAll('.pill, .chip, .reg-chip, .seg, .tag, [class*="-tag"]')) {
    // the landing's before/after tags are left out on purpose: English's own "Before" tag is already cut by the photo's
    // frame at 320, 360 and 1024 (it shows from a 27 % split, narrower than the tag) — a design call, plan 5 task 2 report
    if (el.closest('svg, .nav, .atlas-bar, .splitter-tag') || !visible(el)) continue
    const r = el.getBoundingClientRect(), box = boxOf(el)
    if (r.right > box.right + 0.5 || r.left < box.left - 0.5) {
      const where = box.el ? `${box.el.tagName.toLowerCase()}.${[...box.el.classList].join('.')}` : 'screen'
      issues.push({ kind: 'control runs out of its box', at: `${el.tagName.toLowerCase()}.${[...el.classList].join('.')} ${Math.round(r.left)}–${Math.round(r.right)} of ${where} ${Math.round(box.left)}–${Math.round(box.right)}`, ctx: (el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60) })
    }
  }
  return issues
}

const browser = await chromium.launch({ headless: true, executablePath: fs.existsSync(EXE) ? EXE : undefined })
const ctx = await browser.newContext({ deviceScaleFactor: 1 })
const page = await ctx.newPage()
// never a real count: Umami's tracker and sends, Clarity and Microsoft's pixel are answered here
await page.route(/stats\.frondia\.eu|\/u\/script\.js|\/api\/send|clarity\.ms|c\.bing\.com/, (r) => r.abort())
const all = []
for (const p of PAGES) {
  const url = p.path.startsWith('http') ? p.path : BASE + p.path
  await page.setViewportSize({ width: 1440, height: 900 })
  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 })
    // the atlas reads its city in the browser: its panel heading is there once the data is
    if (/^\/(?:[a-z]{2}\/)?atlas\/?$/.test(new URL(url).pathname)) await page.waitForSelector('.panel h1', { timeout: 20000 })
  } catch (e) { all.push({ page: p.path, error: String(e).slice(0, 120) }); continue }
  await page.waitForTimeout(1500)
  await page.evaluate(() => document.querySelectorAll('details').forEach((d) => { d.open = true }))
  if (NO_HYPHENS) await page.addStyleTag({ content: ':lang(nl) * { hyphens: manual !important; }' })
  const lang = (await page.evaluate(() => document.documentElement.lang) || 'en').slice(0, 2).toLowerCase()
  const shortWords = SHORT_BY_LANG[lang] || SHORT_BY_LANG.en
  for (const w of WIDTHS) {
    await page.setViewportSize({ width: w, height: w < 700 ? 844 : 900 })
    await page.waitForTimeout(350)
    const issues = await page.evaluate(audit, { shortWords, lang, noHyphens: NO_HYPHENS })
    for (const i of issues) all.push({ page: p.path, width: w, ...i })
  }
  process.stderr.write(`${p.path}: done\n`)
}
await browser.close()
const g = new Map()
for (const i of all) { const k = `${i.page} | ${i.kind} | ${i.at}`; if (!g.has(k)) g.set(k, { ...i, widths: [] }); if (i.width) g.get(k).widths.push(i.width) }
for (const v of g.values()) console.log(`${v.page}\t${v.kind}\t«${v.at}»\t[${v.widths.join(',')}]\t${v.ctx || v.error}`)
console.log(`\n${g.size} distinct, ${all.length} total`)
process.exit(g.size ? 1 : 0)
