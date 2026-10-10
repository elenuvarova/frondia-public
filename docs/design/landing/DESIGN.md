---
name: frondia-landing
description: Frondia's public landing page. Editorial and evidential — a cream Satoyama page with near-black text, CADRO's greens and lilac for the night, the light and the notes; on maps and charts colour still means measurement.
colors:
  sato-cream: "#F2EADE"
  sato-card: "#FBF9F5"
  sato-ink: "#1D1D1B"
  cadro-lime: "#C9ED73"
  cadro-forest: "#186E50"
  cadro-night: "#0F4E37"
  cadro-lavender: "#BDA7F9"
  cadro-pink: "#E4ACFF"
  cadro-pink-hot: "#F8B0FF"
  cadro-periwinkle: "#84A7D5"
  cadro-cream-ink: "#F0EBDD"
  ivory-light: "#FAF9F5"
  ivory-medium: "#F0EEE6"
  ivory-dark: "#E8E6DC"
  oat: "#E3DACC"
  cloud-light: "#D1CFC5"
  cloud-medium: "#B0AEA5"
  cloud-dark: "#87867F"
  slate-light: "#5E5D59"
  slate-medium: "#3D3D3A"
  slate-dark: "#141413"
  lime: "#F9FFD5"
  gain-1: "#3EB0A0"
  gain-2: "#22998D"
  gain-3: "#0F6B63"
  loss-1: "#EB7F7F"
  loss-2: "#E05F5F"
  loss-3: "#C9302F"
  background: "#F2EADE"
  background-2: "#FBF9F5"
  foreground: "#1D1D1B"
  foreground-2: "#1D1D1B"
  muted-foreground: "#1D1D1B"
  line: "#B0AEA5"
  night: "#0F4E37"
  night-foreground: "#F0EBDD"
  night-foreground-2: "#C9ED73"
  night-muted: "#F0EBDD"
  note: "#BDA7F9"
  plaque: "#C9ED73"
  glow-core: "#F8B0FF"
  glow-halo: "#BDA7F9"
  hero-ground: "#E3DACC"
  noise: "#D1CFC5"
  primary: "#1D1D1B"
  on-primary: "#F2EADE"
typography:
  hero:
    fontFamily: Instrument Serif
    fontSize: 64px
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: 0.01em
  h2:
    fontFamily: Instrument Serif
    fontSize: 50px
    fontWeight: "400"
    lineHeight: 55px
    letterSpacing: 0.01em
  h3:
    fontFamily: Instrument Serif
    fontSize: 45px
    fontWeight: "400"
    lineHeight: 47.25px
    letterSpacing: 0.01em
  card-title:
    fontFamily: Instrument Serif
    fontSize: 35px
    fontWeight: "400"
    lineHeight: 36.75px
    letterSpacing: 0.01em
  small-head:
    fontFamily: Instrument Serif
    fontSize: 24px
    fontWeight: "400"
    lineHeight: 27px
    letterSpacing: 0.01em
  number:
    fontFamily: Instrument Serif
    fontSize: 64px
    fontWeight: "400"
    lineHeight: 70px
    letterSpacing: 0.5px
  lead:
    fontFamily: Geist
    fontSize: 21px
    fontWeight: "400"
    lineHeight: 28.35px
    letterSpacing: 0.01em
  body:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 24px
    letterSpacing: 0.01em
  stat-label:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 22px
    letterSpacing: 0.1em
  ui:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 19.6px
    letterSpacing: 0.01em
  small:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 20px
    letterSpacing: 0.01em
  caps-label:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: "600"
    lineHeight: 18px
    letterSpacing: 0.1em
  button:
    fontFamily: Fragment Mono
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 14px
    letterSpacing: 0em
  number-mono:
    fontFamily: Fragment Mono
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 17.5px
    letterSpacing: 0em
  tag:
    fontFamily: Fragment Mono
    fontSize: 12px
    fontWeight: "400"
    lineHeight: 16.8px
    letterSpacing: 0em
rounded:
  none: 0px
  sm: 2px
  md: 16px
  lg: 22px
  full: 999px
spacing:
  s-8: 8px
  s-12: 12px
  s-16: 16px
  s-20: 20px
  s-32: 32px
  s-48: 48px
  s-64: 64px
  section: 96px
  section-large: 144px
  gutter: 70px
  max-width: 1440px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.full}"
    height: 42px
    padding: 20px
  button-ghost:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    typography: "{typography.button}"
    rounded: "{rounded.full}"
    height: 42px
    padding: 20px
  chip:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    typography: "{typography.tag}"
    rounded: "{rounded.full}"
    height: 26px
  segmented:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground-2}"
    typography: "{typography.button}"
    rounded: "{rounded.full}"
    height: 40px
  chart-card:
    backgroundColor: "{colors.background-2}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.lg}"
    padding: 32px
  hero-card:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    typography: "{typography.hero}"
    rounded: 20px
    padding: 44px
  band-tile:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    typography: "{typography.number}"
    rounded: "{rounded.md}"
    padding: 24px
  night-band:
    backgroundColor: "{colors.night}"
    textColor: "{colors.night-foreground}"
  night-text:
    backgroundColor: "{colors.night}"
    textColor: "{colors.night-foreground-2}"
  note-placeholder:
    backgroundColor: "{colors.note}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
  plaque:
    backgroundColor: "{colors.plaque}"
    textColor: "{colors.foreground}"
  splitter-handle:
    backgroundColor: "{colors.background-2}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.full}"
    size: 44px
---

# Frondia · landing design system

## Overview

The public page of Frondia, a product that measures what actually changed in a city's green and tells change from noise with a named threshold. The page has to read as **evidence, not marketing**: a real satellite field instead of a drawn gradient, serif statements, mono captions that say where each number comes from.

This is one of two design systems. The product interface (the atlas) has its own, in `docs/design/interface/DESIGN.md`. The two share only brand primitives (`site/web/styles/brand.css`; until the tag `vite-apps-final`, `site/packages/shared/brand.css`): the palette values, the three typefaces and the data ramps. Roles, type scale, spacing and components are defined separately in each app and are expected to diverge.

**References, one job each** (Figma `dNvUEJQwB2R8dFPRmHctOp`):

| Job | Reference | Where |
|---|---|---|
| Principal layout: the numbers | anthropic.com, eight sections measured live at 1440 | page "Frondia · DS Landing", sections 112:2 (spacing system) and 85:4 (redlines) |
| Layout: where the weight sits, per section | Daylight, Paraform, Function, Shade, Linear, Zipline, anthropic.com, Cosmos | 108:5, with computed mass maps |
| Type | David Protein's system, read live; paid faces replaced by Geist and Fragment Mono | 96:4 |
| Elements | one reference per element (33), set beside the element as built | 124:2 (v1 parts: 88:4) |
| The sector dossier: the numbers | anthropic.com's research articles, six pages measured live at 1440, each clean and redlined | "Frondia · DS Landing", 199:2 |
| The top of the page | layout 1 "Rustle": Copilot / CopilotHealth (a landscape smeared sideways), Aeth (a cream serif card on the blur), ABA (number tiles on a smeared strip) | page "Frondia · Concept", 165:4 (chosen 26 Sep 2026) |
| Colour | the Satoyama brochure's base (cream page, near-black text) with CADRO's greens and lilac, measured as OKLab clusters | "Frondia · Concept", 159:4 (measurements), 165:4 (approved 26 Sep 2026) |
| Interactions | Osmo Supply: Number Odometer, Before/After Split Slider, adapted to React with keyboard and reduced-motion added | `osmo-vault` skill |
| (4) the atlas showcase | Pastel, "How website annotations work": the product in a browser frame, notes beside it | page "Frondia · Concept", section v5 |
| (4) one map, three questions | anthropic.com's "Latest releases": three equal columns 32 apart (408 + 31 + 408 at 1425, measured), the action at the foot | 124:2 row 18; masses in 108:5, last row |
| (7) questions | Programa's FAQ: the list offset right with air on the left, a pair of buttons after it | page "Frondia · Concept", section v5 |
| Metaphor | the rustle and the ring: the field rustles (noise), facts stand still | page "Frondia · Direction", 110:2 |

## Colors

Two levels. **Primitives** carry the hex values and live in `brand.css`, named after their source: anthropic's (kept for the hero ground, the noise grey and the atlas), `sato-*` from the Satoyama brochure (refs 143:193) and `cadro-*` from CADRO (refs 143:189). **Roles** point at primitives and live in `site/web/styles/tokens.css` (was `apps/landing/src/styles/tokens.css`). Components use roles only. The palette was approved by Elena on 26 Sep 2026; the brief is `landing-brief.md`.

| Role | Primitive | Hex | Contrast | Use |
|---|---|---|---|---|
| `--paper` | sato-cream | #F2EADE | — | page ground |
| `--paper-2` / `-3` | sato-card | #FBF9F5 | — | cards, the colophon band, the chart card on night |
| `--ink` / `-2` / `-3` | sato-ink | #1D1D1B | 14.2 on paper, 16.1 on cards | all text — the brochure sets almost all its text in this one near-black |
| `--ink-4` | cloud-medium | #B0AEA5 | — | lines only, never text; neutral on purpose |
| `--hatch` | cloud-dark | #87867F | 3.5 on its paper tile | the "no fair comparison" hatch: neutral, because a greenish hatch would read as a gain; cloud-medium gave 2.1, under WCAG 1.4.11's 3 : 1 for graphics |
| `--night` | cadro-night | #0F4E37 | — | the dark bands: method, refusals, footer. CADRO's largest cluster (#186E50, 17.6 %) darkened to Satoyama's forest lightness — on #186E50 the verdict rings fell to 2.3 : 1 |
| `--night-ink` / `-3` | cadro-cream-ink | #F0EBDD | 8.1 on night | text on night |
| `--night-ink-2` | cadro-lime | #C9ED73 | 7.3 on night | body text, icons and small labels on night |
| `--note-bg` | cadro-lavender | #BDA7F9 | ink on it 8.1 | notes, the picture-less case placeholder, and (mixed 42 % into paper) the marked quotes of the register |
| `--plaque` | cadro-lime | #C9ED73 | ink on it 12.7 | plaques (not used on the landing yet) |
| `--glow-core` / `-2` | cadro-pink-hot / cadro-pink | #F8B0FF / #E4ACFF | — | the core of the light over the field |
| `--glow-halo` / `-2` | cadro-lavender / cadro-periwinkle | #BDA7F9 / #84A7D5 | — | the screened halo that bridges the pink to the greens |
| `--oat` | oat | #E3DACC | — | hero ground behind the field image |
| `--noise` | cloud-light | #D1CFC5 | — | "within noise" in charts and maps |

**Why the lilac is a core and a halo.** Lilac laid thin over green averages to grey (they are nearly complementary). CADRO keeps its pink opaque and bridges to the greens through lavender, periwinkle and teal; the landing does the same — an opaque core in normal blend, a halo in `screen` blend (it lightens to pastel instead of greying), the hero isolated (`isolation: isolate`).

**The hero field in CADRO's greens.** Same NDVI, same order of lightness; palette `cadro` in `scripts/site/field.py`, the frame recoloured from the light one by `scripts/site/field_recolor.py` (residual median 1.8 sRGB units — the frame really is drawn in that palette). Under data maps the field stays the light palette at 0.30.

**The field under data.** The light field palette ends in leaf and forest green (`e6e39a cadb8e a1c873 72a652 4a7e3a`), not teal: under protanopia a teal forest was indistinguishable from "greener beyond noise" (ΔE00 0.8). Where verdict fills sit on the field it is laid at 0.30 opacity — the minimum ΔE00 against both ramps is then 10.8 under every colour-vision type (`FIELD_UNDER_DATA`, `viz/SectorMap.jsx`).

**Data colours are fixed and belong to measurement alone.** The gain ramp `#3EB0A0 #22998D #0F6B63` and the loss ramp `#EB7F7F #E05F5F #C9302F` mark the threshold, 2× and 3×. They were validated for lightness steps, deuteranopia and protanopia. Since the approved palette the chrome has greens of its own — the night surface and lime text on it — so the rule is narrower and stricter where it matters: **no chrome green or red ever sits inside a map, a chart or a verdict**; charts on a night band go on a paper card; the hatching for "no fair comparison" stays neutral grey; lilac is light and notes, never data.

## Typography

David Protein's system, taken whole. The two paid faces are swapped for free ones, chosen by measurement: glyph overlap at equal cap height, then line width at David's sizes.

- **Instrument Serif** (OFL) for every heading, 400, +0.01em.
- **Geist** instead of Suisse Int'l, for text and UI, +0.01em. Shape overlap 0.813; line width +0.8 / 0 / +0.3 % at 46 / 18 / 14 px.
- **Fragment Mono** instead of ABC Monument Grotesk Mono, for buttons, tags and numbers. Tracking 0, set as written. Shape overlap 0.799; line width −0.4 / −0.4 / −1.3 %. Weight 400 only, so there is never a bold mono.

| Style | Face | Size / line | Tracking | Where |
|---|---|---|---|---|
| hero | Instrument Serif | clamp(44px, 5vw, 64px) / 1 | +0.01em | "What actually changed." in the hero card — since layout 1 the hero is inside David's scale (his largest style is 64); the old 176-px exception (`--hero-size`) stays in the tokens for the concept pages only |
| h2 | Instrument Serif | 50 / 55, down to 36 | +0.01em | section statements, max 22ch |
| h3 | Instrument Serif | 45 / 47.25 | +0.01em | — |
| card-title | Instrument Serif | 35 / 36.75 | +0.01em | case titles, wordmark |
| small-head | Instrument Serif | 24 / 27 | +0.01em | refusal titles |
| number | Instrument Serif | 64 / 70 | +0.5px | stats, refusal counts |
| lead | Geist | 21 / 28.35 | +0.01em | hero lede |
| body | Geist | 16 / 24 | +0.01em | running text |
| stat-label | Geist | 16 / 22 | +0.1em | the label under a big number, sentence case |
| ui | Geist | 14 / 19.6 | +0.01em | nav and footer links, index |
| small | Geist | 14 / 20 | +0.01em | notes under charts |
| caps-label | Geist 600 | 12 / 18 | +0.1em, uppercase | kickers, readout labels, label rules |
| button | Fragment Mono | 14 / 14 | 0 | pills, segmented control |
| number-mono | Fragment Mono | 14 / 17.5 | 0 | readout values |
| tag | Fragment Mono | 12 / 16.8 | 0 | captions, image tags, chips, chart axes |

**Line breaks (26 Sep 2026).** No line ends on a one- or two-letter word, an article (a, an, the) or a short preposition or conjunction (for, via, per, and, but, nor, yet, off); a number stays with the word it counts ("12 places", "7 of 7"); a spaced dash never starts a line. The space after such a word is a no-break space, set on every message by `tie()` (`site/web/lib/typography.ts`, called by `lib/t.ts` and `lib/t-client.ts` for the page's language; the Vite apps' `startTies` did it on the rendered text), so it covers every catalogue string in each language, and a later edit to the copy cannot bring a hanging word back. Charts (SVG) and anything inside `[data-no-tie]` are left alone. Checked on the landing and three atlas states at 320–1440 px: no hanging words, no horizontal scroll. A tie makes a short chain unbreakable, so a narrow cell must fit its value: readouts keep the unit in the label ("Summers above noise · 7 of 8"), not in the value.

## Layout

**The principal layout is anthropic.com.** Its numbers are taken literally: the value that repeats across unrelated sections is the step. Each step has one job.

| Token | Value | Use |
|---|---|---|
| `--s-8` | 8 | inside one component: label ↔ value, number ↔ its label |
| `--s-12` | 12 | close siblings: pill ↔ pill, case-card parts |
| `--s-16` | 16 | elements in one block: row padding, figure ↔ caption |
| `--s-20` | 20 | the hero stack; the smallest card padding |
| `--s-32` | 32 | between blocks: stats columns, heading ↔ body, lede ↔ actions |
| `--s-48` | 48 | groups inside a section: cards gap, split margin |
| `--s-64` | 64 | before a closing row: body → stats |
| `--section` | 96 (64 on narrow screens) | top and bottom of every content section |
| `--section-l` | 144 (96 on narrow screens) | the hero and the dark band only |
| `--gutter` | clamp(16px, 4.86vw, 70px) | page inset: 70 at 1440, 16 on a phone |
| `--maxw` | 1440 | content 1300 wide at 1440 |

The rhythm follows distance in meaning. Parts of one thing sit 8–16 apart, things in one block 20–32, blocks in a section 48–64, and sections 96–144 apart. Uniform space groups nothing. A value off the ladder needs a written reason.

**Mass per section** (108:5, computed from the images) sets what is heavy in each section:

| Section | Heavy |
|---|---|
| hero | the full-bleed rustling field; one floating cream card is the focal, the lilac light sits right of it |
| (1) the rustle | a full-bleed band of four number tiles (the light on its left), then two equal maps, each with a number |
| (2) the law, who it is for | the stats, then three audience columns, each ending in a link |
| (3) method | night; one chart card on paper; the steps stay light |
| (4) the atlas | one browser frame with the atlas and three numbered marks; three numbered notes beside it |
| (5) audits | three equal cards, each led by its before/after slider and closed by a link to the audit |
| (6) refusals | even rows on night |
| (7) questions | the statement on the left, the list of questions on the right, two pills after it |
| (8) colophon | air between the statement and the text |
| footer | the mark, on night |

The order was changed after the review of 26 Sep: the law moved from (6) to (2), because the reader who arrives from a region or a municipality needs to know who it is for before the method.

**The sector dossier** (`/dossier?city=&sector=`, phase 2b) is a document in this system: its principal is the same site's article pages (199:2), whose numbers repeat on all six measured:

| Token / value | Value | Use |
|---|---|---|
| `--doc-col` | 640 | the reading column, centred (anthropic: 640 at 400 from the edge at 1440) |
| `--doc-wide` | 880 | the head, key figures, scales and tables (anthropic's figures: 880 at 280) |
| `--s-16` | 16 | between paragraphs, and between a note and the paragraph before it |
| `--s-32` | 32 | a section's title to its first block |
| `--s-64` | 64 | between sections (anthropic's large heading); the eyebrow sits 8 above the title |
| `--s-96` | 96 | from the head to the first section |
| reading text | Geist 18 / 27 | David's size at the principal's leading (1.55 there, 1.5 here) |
| on A4 | 10.5 pt, sections 20 pt apart | print styles: no bar, no buttons, no section parted from its title |

## Elevation & Depth

One shadow: the hero card floats on the field (`0 20px 60px` at 18 % ink), taken from Aeth's card on its blur. Everything else is flat. Depth comes from the dark bands, the lilac light over the field, and a film grain (`--grain`) laid over the field and the night surfaces at 28 % and 16 %. The ghost button and the cards on the field are translucent cream (92–94 %).

## Shapes

Buttons, chips and the segmented control are full pills (999). Cards are rounded 22 (the chart card) and 16 (case images). Rules are 1-px hairlines at 14 % and 32 % of the ink. The focus ring is 2 px ink with a 3-px offset.

## Components

- **Pill button**: Fragment Mono 14/14, height 42 (34 small); on a phone 48 (44 small), NN/g's touch minimum. Padding 20 (14), an arrow that moves 3 px on hover. Four variants:
  - ink: primary, dark on light;
  - paper: on dark;
  - ghost: outline 32 % over the field, translucent;
  - night: outline on dark.
- **Segmented control**: two to three options in a pill track; the pressed one is ink on paper. On a phone each option is 44 tall and drops to the 12-px tag size to fit 390.
- **Verdict chip**: a dot plus a tag. Gain dot = gain-2, loss dot = loss-3, noise = cloud-light, refused = an empty ring.
- **Label rule**: `(n) ——— TITLE ——— note` in caps-label, 1-px rules at 22 %. On a phone the note drops.
- **Index with dotted leaders**: number (tag) · dotted rule · title (ui).
- **Stat**: a number (64/70 serif), then a stat-label, with a 32 % hairline above.
- **Readout**: a caps-label above a mono value (14/17.5), in a row of 3–4.
- **Chart card**: paper-2, radius 22, padding 20–32, a head row of caps-label and segmented control. On a night band it is the only paper, so the chart keeps its data colours.
- **Hero card** (layout 1; Aeth): cream at 92 %, radius 20, padding clamp(28–44), centred: caps-label kicker ("Evidence atlas · Brussels & Antwerp": it names the whole atlas, while the title keeps the one question only Frondia answers), the hero title, a small lede of 40ch, two pills. The field caption — what the field is — sits bottom-left in a translucent tag.
  - **Pause** (WCAG 2.2.2; design wave, 5 Oct): the moving hero has a 32-px plate in its bottom-right corner (paper at 70 %, radius 8, a 16-px pause / play glyph in ink), `aria-pressed`. It holds the drift where it is and stops the wind, for the rest of the visit (session storage). Absent under reduced motion, on `?clean` and in print. The centred caption keeps 56 px clear of it on each side.
- **Rustle band** (ABA): the field again, full bleed, 48–96 top and bottom; four tiles of cream at 94 %, radius 16, padding 24, each a big number over its stat-label. The numbers roll in once (Osmo Number Odometer: 0–9 rollers, power3.out, 0.04 s per digit from the right; plain text again when done; still under reduced motion).
- **Light** (CADRO): two ellipses sharing one centre — a screened lavender→periwinkle halo and an opaque pink core. Right of the hero card, left of the band's first tile, above the card on a phone.
- **Showcase** (the course's product showcase, screenshot fallback for maps; Pastel): a browser frame — 38-px bar with three dots and the deep link — around a real atlas screenshot rendered at 2× (webp, JPEG fallback) and linked to the same state; three numbered ink marks (28 px, paper ring) on the picture match three numbered notes beside it. On a phone the picture is swapped (`<picture>`) for a crop of the audit card alone; the marks and the two notes about the lens and the map hide, and the audit's note loses its number.
- **Three maps** (`.three`; the principal's "Latest releases" row): three equal columns, gap `clamp(20, 2.2vw, 32)`, one per question of the atlas. Each: a live map in a 16-radius frame that lifts 2 px on hover and opens the atlas on that lens; an index (tag) with the lens's key at the right (the lack ramp, the three point roles, or teal–noise–red); a card title; two to four lines of small; a text link at the foot. Only the third map carries the field and the verdict colours; the first paints every sector with the lack ramp, the second puts ink points on the field. Mass map (108:5): the first tile is the heaviest block of the row, so the row leans left. Decided on 26 Sep (Elena): the heavier mass on the left is right, and the row stays.
- **Load states**: while the four data files load, a 100svh placeholder holds the footer below the hero; if one fails, a notice with "Reload" and "Open the atlas" takes the place of the sections. Once the data is in, the page jumps to the address's `#…` (the browser tried before the sections existed); a back/forward visit keeps the restored scroll.
- **Case card**: a before/after slider (Osmo Before/After Split Slider: clip-path mask, Draggable; added: role="slider", arrows ±5, Page ±20, Home/End; the whole picture is the drag surface — a tap, or a drag once it is horizontal, moves the split under the finger, while a vertical swipe scrolls the page; `zIndexBoost` off and the slider isolated, so the handle never rises over the nav; 44-px knob at the bottom; starts at 30 % so the footprint shows "after"; each tag — "Before" / "After" over its window, two lines of tag type — rides in its own layer beside the split and fades when its half is too narrow), or a lavender note when there is no picture; meta line (tag), card title, the big number with its "× audit threshold", readout, series chart (the line breaks at a missing summer; noise summers carry their year under the dot, a missing summer its year on the axis row), reading (small; a note on the picture, when one is needed, closes it, so the three cards keep one top line), then a text link to the audit in the atlas.
- **Text link** (`.case-link`): Fragment Mono 14, underlined at a 32 % rule that turns ink on hover, an arrow that moves 3 px; 44 px tall. Used where a card or a column hands the reader to the atlas.
- **Refusal row**: number and stat-label | icon and small-head | body, with hairlines between rows.
- **Audience column**: 32 % hairline, small-head, body, a text link — three in a row. Regions → the atlas; municipalities → the Ninove audit; funders → opens the FAQ answer on fixing the outline (`#q-outline`).
- **Question**: native `<details>` with an id (`q-trees`, `q-outline`…; `#q-…` in the address opens it); small-head in the summary, a 44-px round mark that turns into ×, body answer to 60ch. The list ends with the pair "Open the atlas" / "Read the method".
- **Nav**: wordmark (card-title 35), links in the page's order (Article 8 · Method · Audits, ui 14), small pill. On the landing it is fixed: transparent over the field, then a 56-px paper bar with a hairline the moment it would slide over the hero card (wordmark 28). On a phone it keeps Method and Audits (44 px tall) and the pill says "Atlas". Every in-page target keeps 72 px of scroll margin, and the page 72 px of scroll padding, so neither an anchor jump nor keyboard focus lands under the bar. On the landing the links are same-document (`#law`), so a query string never reloads the page.
  - **Two rows on a phone** (≤ 560 px, with a second language routed; Elena, 5 Oct 2026): the wordmark and EN · NL · FR (ui 14, 44-px rows), then Article 8, Method, Audits and the pill pushed right. The bar is 113 tall (106 at ≤ 340), so the document pages start at 156 and scroll padding is 116. The switch is drawn twice (after the wordmark, at the end of the links) and CSS shows one, so Tab follows the reading order.
  - **Clearance** (round-1 re-check, 6 Oct): the bar lies over the page, and the page keeps a fixed gap under its measured height (`--nav-h`): 38 to a document page's first line, 22 to the hero card (96 under a one-row bar, 136 under two rows), 10 to /privacy's heading. A reader's text spacing can wrap the bar to a third row; the page then starts lower instead of under it.
- **Colophon contact**: Elena's address as a text link (`mailto:`) under the colophon's two paragraphs. She asked for it on 26 Sep; it lives in `content/en.js` as `CONTACT`.
- **Twin maps' counts**: only a measured change carries a data colour. The rustle's count (sectors that look greener) is set in ink; the growth's count (beyond noise) is gain-3, 5.3 : 1 on cream. The rustle's count used to be gain-1, 2.2 : 1, below WCAG's 3 : 1 for large text.
- **Footer**: statement mark in serif, links (ui 14, padded to 44), the author line and "no cookies, no analytics, no tracking" (small 14/20), credits, on night. Off the landing its section links lead home first (`/#law`).
- **Dossier head** (124:2 row 19; Elicit, Dovetail): centred as the principal's articles — caps-label kicker (dossier · commune · sector), a display-l title that states the finding and is computed, never written ("canopy 41% below the city's median"), a lede of 40ch, then the document's facts as label and value on a hairline (unit, baseline, imagery, measured to), four across and two on a phone, then Print and "Open in the atlas" as small pills.
- **Key figures** (row 20; Sana): six cells three across, hairlines only between the cells, the serif number (35) at the top and its label (14) at the foot; the share of residents in mono beside a count. Two across on a phone.
- **Value against the median** (row 21; Churnkey, Klima): a row per measure — name with the city's median in mono, a 10-px bar on a rule-coloured track with a 2-px ink tick at the median (paper halo), the value right-aligned in mono, and the reading in words under the bar.
- **Note** (row 22; Notion, AI in Design Report): paper-2 tint, radius 16, no border, a bold first sentence running into 16/24 text. In print: no tint, framed by a top and a bottom rule.
- **Pledges** (row 23; Bonsai): an ordered list, the markers in mono ink-3, each item a bold run-in sentence and its explanation, 16 apart.
- **Comparison table** (row 24; Stripe): groups as rows, caps-label heads, numbers right-aligned in mono, the sector's own row closing the table on an ink rule, the "as of" line (small) right under it. On a phone the numeric heads wrap and a table that still overflows is a focusable region.
- **Colophon** (row 25; OpenAI): rows on hairlines, a 120-px label column; the last row is the page's own address.
- **A file to download** (row 27; Optimal Workshop, Skillshare), on `/data`: a paper-2 card per layer, radius 16 — the title in serif 24, the file's tag in mono 12 (CSV · rows · KB · the date computed, parts joined by dots that never end a line), one line on what it measures (16/24), the threshold and the licence (small), a small ink pill "Download CSV ↓" that saves the file under a Frondia name, then a `<details>` row of 44 px whose mark turns into ×.
- **Column dictionary** (row 28; Snowflake): inside the details, the layer's facts as colophon rows (method, source, threshold and its origin, limits, licence, credit), then a table of every column: the name in mono 12, what it holds in 14/20, hairlines. On a narrow phone the table is a focusable region.
- **A measure and its quote** (row 29; Dovetail), on `/register`: a row per contract on hairlines, the wide column split 240 / the rest — on the left the contract (serif 24 name, commune and years in mono 12), on the right its reading: the label chip, then each measure as its quote marked in the note colour mixed 42 % into paper (`lang="fr"`, the mark cloned across line breaks) and its tags in mono 12 under it (status · kind · place, dots never ending a line). A quote the model gave twice, for two kinds of measure, is shown once with both. The model's reason sits in a `<details>`, the source link at the right. One column on a phone.
- **The rate and its interval** (row 30; Adaline, Cohere, and the dossier's bar after Churnkey): the key figures first, then one group per question, the language model and the rule each on a 0–100 % scale: a hairline track, the Wilson 95 % interval as an opaque 10-px span (ink mixed 28 % into paper, so the hairline never shows through), the estimate as the 2-px ink tick with its paper halo, "k of n" in mono with the rate and the interval in 12 under it, and the reading in words under the pair. The group's title is a sentence-case 16/22 heading, so it never reads as the section's caps label.
- **A disagreement** (row 31; Braintrust): a paper-2 card, radius 16 — the contract's name in serif 24 and a link to its quotes (it clears the register's filter first), then the reference label (a second model's until a person's is made; the column is named after whoever gave it), the first reading's and the rule's in three columns on a hairline, then the reasons (16/24): a second model's is published, a person's working notes never are.
- **Labels by form** (row 32; Intercom Fin's three-step rating, drawn as the atlas's point roles after Forest): chips in mono 12 — commits: a filled ink dot; an aim: an ink ring; no measure: no dot; not described: a dashed border in ink-3. The labels classify text, so no data colour is used; colour stays with measurement.
- **Filter with counts** (row 33; Maze): pill toggles in mono 14 with their counts, wrapping to two rows on a phone (44 px tall there); a tab with nothing in it is disabled; a checkbox narrows the list to the 30 test contracts (“read twice”, or “checked by hand” once a person labels them), and the counts follow it. The view lives in the address (`?show=…&checked=1`), and `#c<id>` opens one contract.
- **City picker on the data page**: the atlas's pill (interface row 48, Sweatpals and DoorDash) in the landing's small-pill metrics — 34 px, rule-2 border, translucent paper, 44 px on a phone — over a native select of `CITY_NAMES`.
- **The law's row of figures**: one column per figure up to four, then rows of three (`--n`), two columns under 960 px, one on a phone: a row never leaves a figure alone. Brussels's municipalities and region first, then each city; a verdict the test's other reading of Article 3(20) overturns carries that reading beside it ("Ghent: below 45% · 49.0% with farmland counted").
- **Printed sheet** (row 26; komoot): A4 from the browser's print, the address at the top of the first sheet, eyebrow and title kept with the block that follows (`break-after: avoid`), notes and tables never split.

## Do's and Don'ts

- **Do** take every value from a token. A new value first goes into this file and the tokens, with its reference.
- **Do** keep the verdict ramps for data. Chrome greens (night, lime) and lilac never enter a map, a chart or a verdict.
- **Do** give every number its source nearby (caption, tag or footnote).
- **Do** set prose with `text-wrap: pretty`, so a paragraph does not end on a lone word.
- **Do** vary gaps by meaning, never set them uniformly.
- **Don't** add a second exception to the type scale without a reference. The footer mark is the candidate (Cosmos, 108:5), and it is not decided yet.
- **Don't** use bold mono (Fragment Mono has 400 only), capitals in mono, or tracking on mono.
- **Don't** repeat the landing's components in the atlas by importing them. The interface copies what it needs into its own system.
