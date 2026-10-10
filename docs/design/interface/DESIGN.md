---
name: frondia-interface
description: Frondia's product interface, the atlas — a full-screen map of city sectors with floating cards, asking of every sector what is missing, what to place and what changed. A dense tool with fixed frames; the chrome is neutral, because colour means measurement.
colors:
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
  gain-1: "#3EB0A0"
  gain-2: "#22998D"
  gain-3: "#0F6B63"
  loss-1: "#EB7F7F"
  loss-2: "#E05F5F"
  loss-3: "#C9302F"
  lack-1: "#FEC44F"
  lack-2: "#FE9929"
  lack-3: "#EC7014"
  lack-4: "#CC4C02"
  lack-5: "#8C2D04"
  green-1: "#C7E9C0"
  green-2: "#A1D99B"
  green-3: "#74C476"
  green-4: "#41AB5D"
  green-5: "#238B45"
  card: "#F0EEE6"
  stage: "#E8E6DC"
  switch-track: "#E3DACC"
  foreground: "#141413"
  foreground-2: "#3D3D3A"
  muted-foreground: "#5E5D59"
  line: "#B0AEA5"
  noise: "#D1CFC5"
  primary: "#141413"
  on-primary: "#F0EEE6"
  tooltip: "#141413"
  on-tooltip: "#F0EEE6"
typography:
  counts:
    fontFamily: Instrument Serif
    fontSize: 64px
    fontWeight: "400"
    lineHeight: 70px
    letterSpacing: 0.5px
  reading:
    fontFamily: Instrument Serif
    fontSize: 35px
    fontWeight: "400"
    lineHeight: 36.75px
    letterSpacing: 0.01em
  title:
    fontFamily: Instrument Serif
    fontSize: 24px
    fontWeight: "400"
    lineHeight: 27px
    letterSpacing: 0.01em
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
  fine:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: "400"
    lineHeight: 16px
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
  number:
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
  swatch: 3px
  control: 14px
  card: 22px
  full: 999px
spacing:
  s-7: 7px
  s-10: 10px
  s-15: 15px
  s-24: 24px
  s-35: 35px
  inset: 12px
  pad: 16px
  bar: 46px
  panel: 267px
  drawer: 298px
components:
  floating-card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.card}"
    padding: 16px
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.full}"
    height: 34px
    padding: 14px
  segmented:
    backgroundColor: "{colors.card}"
    textColor: "{colors.foreground-2}"
    typography: "{typography.button}"
    rounded: "{rounded.full}"
    height: 36px
  chip:
    backgroundColor: "{colors.card}"
    textColor: "{colors.foreground}"
    typography: "{typography.tag}"
    rounded: "{rounded.full}"
    height: 30px
  choice-row:
    textColor: "{colors.foreground-2}"
    typography: "{typography.ui}"
    height: 40px
  point-named:
    backgroundColor: "{colors.primary}"
    rounded: "{rounded.full}"
    size: 10px
  point-control:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.full}"
    size: 10px
  tooltip:
    backgroundColor: "{colors.tooltip}"
    textColor: "{colors.on-tooltip}"
    typography: "{typography.ui}"
    rounded: "{rounded.full}"
    padding: 10px
  zoom:
    backgroundColor: "{colors.card}"
    textColor: "{colors.foreground-2}"
    rounded: "{rounded.control}"
    size: 40px
---

# Frondia · interface design system

## Overview

The atlas is where a reader checks a claim. It is a full-screen map of Statbel sectors that asks three questions of every sector, one at a time (docs/07-unified-frondia.md):
- **what is missing**: four lenses (everyday services for a life scenario, shops within reach, summer heat, the 3-30-300 rule), from Neighbourhood Fit Score, SpotFinder and Frondia's own layers;
- **what to place**: fourteen kinds of public-realm object, ranked by City Planner, the first ten of each named before anyone placed anything;
- **what changed**: greenness against twelve matched places, with the city's noise threshold.

Floating cards carry it:
- a panel on the left: the question's lens, its legend and a ranked list;
- a drawer on the right: a sector's page in three parts, one per question, or an audit with its twelve named controls;
- a thin top bar: city, the question, and a link back to the method.

This is a separate system from the landing's (`docs/design/landing/DESIGN.md`). The two share only brand primitives (`site/web/styles/brand.css`; until the tag `vite-apps-final`, `site/packages/shared/brand.css`). The interface is a dense tool, so its steps are smaller, its frames fixed and its type the small end of the same scale. Since the Next.js app (plan 4) it is built and deployed with the landing, one app in `site/web` (`app/(atlas)`; until the tag `vite-apps-final`, `site/apps/atlas`, port 5179), but keeps its own styles.

**References, one job each** (Figma `dNvUEJQwB2R8dFPRmHctOp`, page "Frondia · DS Interface"):

| Job | Reference | Where |
|---|---|---|
| Principal layout: the numbers | Felt web app, eight screens measured with redlines | 71:5; the ladder with its usage in 112:62 |
| Layout: where the weight sits | Felt legend + inspector; Felt selected item | 115:2, with computed mass maps |
| Type | the small end of David's system (landing DS, 96:4) | page "Frondia · DS Landing" |
| Elements | one reference per element (19; search and filter chips marked not built) | 125:2 |
| Colour | anthropic.com's palette; compared with two forest palettes | page "Frondia · Direction", 113:2 |
| Colour of a lack | ColorBrewer 7-class YlOrBr, classes 3–7, taken literally | 125:2 row 38; `brand.css` |
| Colour of a commune's green | ColorBrewer 7-class Greens, classes 2–6, taken literally | 125:2 row 44; `brand.css` |
| Elements of the unified atlas | chips (36, KAYAK), choice row (37, Mapbox Studio), legend for a lack (38, ColorBrewer and Windy), point roles (39, Forest’s map guide: one P filled for "must", outlined for "may"), sector page in parts (40, Mapbox Studio and Apple Maps), scrolling inside a card (41, Osmo "Hide Scrollbar"), question switch (42, row 19), who is short (43, Deel and Steep), communes (44, Grain, Zillow, ColorBrewer Greens), what if N more (45, Dub and Mixpanel), the whole city before and after (46, Leonardo AI, ElevenLabs, Higgsfield, Zillow), the dossier link (47, Telescope), the city picker (48, Sweatpals and DoorDash) | 125:2, rows 36–48 |

## Colors

Same two levels as the landing: primitives in `brand.css`, roles in `site/web/styles/atlas/tokens.css` (was `apps/atlas/src/styles/tokens.css`).

| Role | Primitive | Use |
|---|---|---|
| `--paper` | ivory-medium #F0EEE6 | top bar, drawer, zoom, chips; the lens panel at 86 % with a 16-px blur |
| `--paper-2` | ivory-dark #E8E6DC | hover, the ground of the "refused" hatch |
| `--paper-3` | oat #E3DACC | switch track (off) |
| `--stage` | ivory-dark #E8E6DC | the map's ground under the field image |
| `--ink` / `-2` / `-3` | slate-dark / medium / light | text 15.9 / 9.4 / 5.7 : 1; `--ink` also fills the tooltip, the pressed segment and the switch (on) |
| `--ink-4` | cloud-medium #B0AEA5 | hatching and lines only, never text |
| `--noise` | cloud-light #D1CFC5 | "within noise" in histogram bars and chips |

**The field under the verdicts is laid at 0.30** (`FIELD_UNDER_DATA`), multiplied onto the stage. Its darkest green (L* 79.7) stays lighter than the lightest fill (L* 65.4). The minimum ΔE00 between field and either ramp is 10.8 under normal, deutan, protan and tritan vision; the old teal field at 0.6 scored 0.8. The field lens, where no verdict is drawn, shows it at 0.95.

**What a neighbourhood lacks takes its own ramp**, never gain or loss: `--lack-1…5` are ColorBrewer's YlOrBr 7-class, classes 3–7 (`#FEC44F #FE9929 #EC7014 #CC4C02 #8C2D04`); light means less lacking. L* 82 → 33, monotone; adjacent steps ΔE00 ≥ 6.4 under protan, deutan and tritan simulation. Two greys that are not data stand beside it: blank (the stage shows through: not lacking, for example cooler than the median) and `--noise` for sectors with fewer than 200 residents, which are never ranked. A lack map carries no field: a blank sector would show green and read as greenness.

**A commune's green takes its own ramp too**, on the commune view only: `--green-1…5` are ColorBrewer's Greens 7-class, classes 2–6 (`#C7E9C0 #A1D99B #74C476 #41AB5D #238B45`), in classes of 15, 30, 45 and 60 % of green in the commune's urban centres and clusters, so the 45 % test falls on a class edge. L* 89 → 51, monotone; adjacent steps ΔE00 ≥ 6.6 under protan, deutan and tritan simulation; the lightest sits 8.4 from the paper under deutan, so every commune is outlined. The field is off on this view.

**On the map, colour is measurement only.** Sectors take the gain ramp (`#3EB0A0 #22998D #0F6B63`) or the loss ramp (`#EB7F7F #E05F5F #C9302F`) at the threshold, 2× and 3×. Noise shows the field through. "No fair comparison" is a grey hatch. Sector outlines take the surface colour, never black. Under a forest palette the hatch turns green and reads as a gain (recolour test, 113:2), which is why the chrome stays neutral.

## Typography

The small end of the landing's scale, David Protein's system with Geist and Fragment Mono in place of the paid faces:

| Style | Face | Size / line | Where |
|---|---|---|---|
| counts | Instrument Serif | 64 / 70 (45 / 47.25 on a phone) | the two counts in the lens panel: the only big numbers in the interface |
| reading | Instrument Serif | 35 / 36.75 | the effect in a passport or an audit |
| title | Instrument Serif | 24 / 27 | panel and drawer titles; the wordmark in the bar |
| ui | Geist | 14 / 19.6 | switch, list rows, controls list, tooltip, the link in the bar |
| small | Geist | 14 / 20 | explanations under charts, the legend |
| fine | Geist | 12 / 16 | list subtitles (commune), the map credit |
| caps-label | Geist 600, +0.1em, uppercase | 12 / 18 | kickers, passport labels, list headers |
| button | Fragment Mono | 14 / 14 | segmented controls (height 28 in the bar), pills |
| number | Fragment Mono | 14 / 17.5 | passport values, list values |
| tag | Fragment Mono | 12 / 16.8 | chips, the analysis window, distances, the histogram pin |

In a column narrower than about 120 px, a stat label takes `ui` (14) instead of the landing's 16 + 0.1em, which wrapped into three lines at the panel's width.

**Line breaks (26 Sep 2026).** No line ends on a one- or two-letter word, an article (a, an, the) or a short preposition or conjunction (for, via, per, and, but, nor, yet, off); a number stays with the word it counts ("12 places", "7 of 7"); a spaced dash never starts a line. The space after such a word is a no-break space, set on every message by `tie()` (`site/web/lib/typography.ts`, called by `lib/t.ts` and `lib/t-client.ts` for the page's language; the Vite apps' `startTies` did it on the rendered text), so it covers every catalogue string in each language, and a later edit to the copy cannot bring a hanging word back. Charts (SVG) and anything inside `[data-no-tie]` are left alone. Checked on the landing and three atlas states at 320–1440 px: no hanging words, no horizontal scroll. A tie makes a short chain unbreakable, so a narrow cell must fit its value: readouts keep the unit in the label ("Summers above noise · 7 of 8"), not in the value.

## Layout

**The principal layout is Felt.** Its frames and steps are taken literally.

| Token | Value | Use |
|---|---|---|
| `--s-7` | 7 | binds a thing to its label: title ↔ kicker, list ↔ header, label ↔ value, legend rows |
| `--s-10` | 10 | hangs one thing on another: a chart on its numbers, list row padding, counts gap |
| `--s-15` | 15 | the default between related blocks in a card; top-bar items; passport grid |
| `--s-24` | 24 | opens a new group: the switch, the histogram block, the list header, the action |
| `--s-35` | 35 | card regions (head ↔ body); measured, not used yet |
| `--inset` | 12 | floating cards and the zoom stack from the stage's edge |
| `--pad` | 16 | inside every card |
| `--bar` | 46 | top bar (plus the safe area on phones) |
| `--panel` | 267 | lens panel, left |
| `--drawer` | 298 | sector or audit drawer, right |

Inside a card the gaps are never uniform. The four steps bind, hang, relate and separate, so a card reads as groups. The frames are fixed and content adapts inside them. Where content genuinely needs more, the fix goes into the content and is written down. For example, the histogram axis at 267 px drops its "0" label and draws the others larger in user units, so they read at 12 px.

On a phone (≤ 860 px) the panel and the drawer become bottom sheets inset 8. Controls there are 40 tall in a row (the bar's segments, the chips) and 44 when alone (the drawer's close), NN/g's touch minimum. The zoom stack moves to the top right and the credit to the top left.

## Elevation & Depth

One elevation for floating cards: `0 1px 0 rgba(250,249,245,.6) inset, 0 18px 48px -18px rgba(20,20,19,.22)`, with a 1-px rule. The lens panel is the only translucent card (86 %, `blur(16px) saturate(1.15)`), so the field shows through the left edge. Everything else is flat. The drawer slides in 14 px over 0.5 s; reduced motion disables it.

## Shapes

- Cards: radius 22.
- Zoom stack: 14.
- Pills, segments, chips, the tooltip, the close button: full (999).
- Legend swatches: 3.
- Rules: 1-px hairlines at 14 % and 32 % of the ink.

## Components

- **Top bar**: wordmark (title 24), city segmented control, the question switch, "How it decides" (ui) at the end. Height 46, gaps 15. On a phone the question switch takes its own full-width row under the city.
- **Address**: it follows the view: city, question, lens and its choice (`for`, `shop`), object, and the open sector or audit. A copied link opens what is on screen. It is replaced, not pushed, so the back button does not walk through every click. A deep link to a sector flies to it once; a sector clicked on the map is in view already and does not move it. A sector of the other city in a link is dropped.
- **Credit line**: it names each source on screen: the field (Copernicus Sentinel, on change and place, with both years under the photos), Landsat (heat), ESA WorldCover in its own CC BY wording (3-30-300), Statbel and OpenStreetMap always.
- **Question switch**: three segments, a 16-px icon and the question in mono 14 ("What's missing", "What to place", "What changed"); the pressed one is ink. Felt's segments are icon-only (19); the questions need their words. On a phone each shortens to one word: Missing, Place, Changed.
- **Segmented control**: 28-px buttons in the bar, mono 14; the pressed one is ink on paper.
- **Panel**, one per question:
  - what is missing: kicker and title (7 apart); the lens chips; the choice row for a scenario or a shop, 10 under the chips; the lede; the legend for a lack; source and limit; "Who is short", 24 below; "Lacking most" and its list (24 and 7 below);
  - what to place: kicker, title and the pool line; the choice row for the object; the counts (coverage today, with all placed); "What if N more?", 24 below; the point legend; the lede and the date the points were named; source and limit; "Named first" and its list;
  - what changed: kicker and title; the view chips (sectors, communes, field, photos: two by two); the switch, 24 below; the counts, 15 below; the histogram and legend, 10 below each (in photos, the lede and the outline key, 7 apart); the note, 15 below (in photos, then the note on the photographs); the list header and list, 24 and 7 below.
- **Window line and card headers**: parts joined by " · " ("Summers 2017 and 2024 · Sentinel-2", "Sector · 21003A283 · Berchem-Sainte-Agathe"). A part that wraps takes the next line whole and leaves its dot behind: each part carries its dot in front, and the first part's dot sits outside the column, where the paragraph clips it.
- **Chips** (36): 30 tall (40 on a phone), mono 12, a 32 % outline; the pressed one is filled ink (KAYAK's applied filter). In the panel on a desktop, and on a phone narrower than 360, they sit in a two-column grid, so four lenses stand two by two; a wrapped row had left one alone. On other phones they fit one row.
- **Choice row** (37, Mapbox Studio): the name on the left in ui 14 (ink-2), the value on the right in Geist 500 14 with a 6-px chevron, a hairline above, 40 tall; a native select underneath, so a phone opens its own picker.
- **Legend for a lack** (38): a 30 × 10 swatch and a label per bin; blank as an outline on the stage; few residents in noise grey with their count. On a phone the list hides and a 10-px stepped bar with its two end labels (fine 12/16) takes its place.
- **Points** (39): named (ranks 1–10) ink with a 1.4 paper stroke; comparison (11–20) paper with a 1.8 ink stroke; further candidates (21–40) a small ink-3 dot at 70 %. Strokes keep their width at any zoom; hover rings a point in lack-3. Legend dots are 10 px (further 6). On a phone, where the other legends hide, the points' key stays as one compact row: the three roles have no other key. Reference: Forest’s map guide draws the same P filled for a bay you must use and as an outline for one you may use, each with one line of meaning — the fill carries the stronger role, here "named" (mobbin.com/screens/83c860b4-5bbc-4eb5-9b57-f5e900113f13).
- **Who is short** (43): under each need lens, a caps label, a reading 7 below it, and two blocks 15 apart, each a small title and its rows 7 below. By income: the lens's own measure (score, distance, °C against the city's median sector, share meeting neither part) for each third of residents by the median taxable income of their sector. Who lives in the worst-off group, cut by the lens's value and named by it ("score 83 or less"; for 3-30-300, the sectors that meet neither part): all residents as the reference row, then children under 15 and people aged 65 and over with their difference in points. Rows as in Deel's side panel: label (ui 14, ink-2) and value (mono 13, ink) on one line, a 4-px bar on a 1-px hairline track, 10 between rows; the age rows add Steep's "against the total" column (mono 12, ink-3). Bars are ink-3, the reference row ink-4: the lack ramp means a class on the map, not a bar. Heat bars leave a centre tick (the city's median sector) to either side. The reading names a group only from 2 points of difference. On a phone the blocks hide and the reading stays, as the ramp stands in for the legend (mobbin.com/screens/25d42744-d70a-435f-bb25-f3601c96b240, mobbin.com/screens/1e8d089a-9735-43ac-a9a4-da924a968a48).
- **Communes** (44): the second view of what changed (`?view=communes`). The map: sectors filled with their commune's green class, every commune outlined in ink at 50 % (0.8 px), an exempt one at 2.4 px; names in ui with a paper halo, at least 10 px on screen, the larger commune placed first and a name that would collide moved a line or left out. The panel: lede, counts (exempt, counted), the region as one, what leaving out every exempt commune would take (area, residents, woody vegetation), then Grain's scale: the list of tested communes with their green share, bars in their class colour, the 45 % test labelled once above the rows and marked on every bar; "exempt" and a failed canopy under the name. The key stays on a phone as one compact row. "Registered before the works": each footprint an outline with no fill (Zillow's drawn boundary), a numbered pin at its centre so a boulevard can be found at city scale, the same number in the list; the refusal fixed in advance in ink-3 (mobbin.com/screens/3a835485-de17-4355-9861-d6c27942e875, mobbin.com/screens/a31b47bb-0dd0-4084-a2fc-f09b870256d8).
- **What if N more?** (45): a caps title that carries the number ("What if 20 more?", kept on a phone), a native range 0–40 in ink (`accent-color`), 7 under it; the result in serif 24 ("28% → 41%") with its unit in ui 14; the planner's coverage curve, 64 tall: the area up to N in ink-4 at 45 %, the line in ink-2, a 1.6-px ink marker at N, the ten named as a 3-3 dashed ink-3 line with a mono 11 tag on the side away from the marker; "today" and "all 40" under it; one line on how many of the N stand where the poorest third of residents live. Points past N step back to 22 % on the map. N is in the address (`n`, 10 by default) (mobbin.com/screens/87d51352-d0f9-4daa-9065-69a8fbaa2a6f, mobbin.com/screens/370f2e3f-f694-4cd0-b8bd-3142c12011d5).
- **The whole city before and after** (46): the fourth view of what changed (`?view=photos`). True-colour Sentinel-2, summer 2017 left of a line and summer 2024 right of it, in the field's frame; the sectors beyond noise as outlines, not fills: a 3.6-px paper casing under a 1.8-px line in gain-3 or loss-3, so they read on dark forest and on white roofs; sector edges in paper at 20 %; audit footprints as paper outlines; hover and selection gain a paper casing. The handle is the landing's split slider laid over the map (Leonardo AI's upscaler: the line across the whole canvas beside the floating panel, both labels riding on the handle): a 2-px paper-2 line with a hairline shadow, a 24-px drag strip, a 44-px round knob with arrows (ElevenLabs), two mono 12 year tags on paper beside it that fade where their side has no 120 px. The knob sits in the lower quarter on a desktop and just above the card on a phone, measured, because a picked place lands mid-map (Zillow keeps its handle off the middle); the line stops 24 px from the panel and from an open drawer. Compare is one of the view chips (Higgsfield). The knob is a slider: arrows ±2 %, Page ±10 %, Home / End; its focus ring is ink round a paper gap. The panel says what the photographs are not: no number is taken from them (mobbin.com/screens/47b549a4-9c26-488e-a885-b275effe1e3f, mobbin.com/screens/6122f8c4-37a2-4073-b1d2-0b4de495a6b4, mobbin.com/screens/90e428d2-caab-4983-ac75-f0f694cdce3e, mobbin.com/screens/4c1a4d29-0a92-4aeb-abe0-92ded9de4ffc).
- **Dossier link** (47): in the sector card, under the name and the residents line, one outlined small pill ("Dossier for this sector →", rule-2 outline) opens the sector's printable dossier on the landing. As in Telescope's place panel, one small action beside the title leads to the place's own page elsewhere. Only for sectors the method measured; it does not shrink in the card's scrolling flex column (mobbin.com/screens/a089c071-415c-43e2-b53c-015688862418).
- **City picker** (48): the city as a pill in the bar, the pin icon, the city in mono 14 and a typographic chevron over a native `<select>` (36 px on the bar, 44 on a phone; rule-coloured border, the seg's translucent paper). As Sweatpals names the city in its map bar and DoorDash the address in its header. It replaced a segmented control when the atlas grew past two cities: five no longer fit, and a native select keeps the keyboard, screen readers and a phone's own picker working. The list comes from `CITY_NAMES` in `content/en.js`, shared with the landing's data page (mobbin.com/screens/713f58ac-dd3b-4935-aebc-0317cb3e747c, mobbin.com/screens/44b254ed-92b9-4a00-96d0-d7b2e41858ea).
- **Switch**: 42 × 24 track, 18-px knob; label in ui 14.
- **Counts**: two columns 10 apart, hairline above; number (counts) in tone-up / tone-down, label in ui.
- **Legend**: 30 × 10 swatches of the ramps, noise outline, refused hatch; small 14/20.
- **Ranked list row**: dot (8), name (ui) with commune (fine), value (number) on the right; 10 padding, hairline above.
- **Drawer**:
  - head: kicker plus a round close button, 32;
  - title, 7 below; chip, 10 below;
  - passport, 15 below; histogram with pin, 24 below;
  - explanation, 15 below; action or controls list, 24 below.
- **Sector page** (40): head, title and a mono line of residents and median income; then three parts 24 apart. Each part opens with a hairline and its question as a part title (Geist 600 14/19.6, sentence case, one level above the caps field labels, as Mapbox and Apple Maps head a section), 15 above its first block. What is missing: a passport of the need lenses. What to place: the candidates of any kind in the sector (dot, object, rank and role). What changed: verdict chip, passport, the histogram with its pin, the explanation, the audit link.
- **Scrolling inside a card** (41): a 4-px cloud-dark bar (3.1 : 1 on paper, as a control needs; ink-3 on hover) whose track stops 22 short of each end, the card's radius; a 48-px fade to paper on the lower edge while more waits below, and a 32-px fade on the upper edge once scrolled (`data-more-below`, `data-more-above`, set by `useMoreBelow`). Osmo's "Hide Scrollbar" asks for a fade as the cue when the bar goes; the atlas keeps the bar and adds the fade. Firefox takes `scrollbar-width: thin` in the same colour. The card keeps 32 / 48 of scroll padding, so a control reached with the keyboard scrolls clear of the fades.
- **Passport**: two-column grid, caps-label above a mono value. Label and value rows are shared across the columns (subgrid), so values line up even when only one label wraps.
- **Histogram with pin**: the city's noise distribution, the sector's value as a 2-px ink pin with a tag.
- **Controls list**: name (ui), distance (tag) on the right, 7 padding.
- **Tooltip**: an ink pill 24 above the bottom, sector name and effect.
- **Zoom stack**: +, −, reset in a 40-px column; it moves left of the drawer when one is open.
- **Pan keys** (WCAG 2.5.7; design wave, 5 Oct): a cross of four keys in the zoom's look (paper, 1-px rule, radius 14, a 14-px chevron in ink-2) that move the view a fifth of its size. On a desktop the keys are 32 px, 10 above the zoom (`--s-10`, the Felt ladder's hang step; 8 until Elena's call of 6 Oct), and they follow it left of a card and above the consent banner. On a phone they are 28 px, 10 under the zoom. Where the bottom sheet or a card leaves no room there (a stage under 440 px, or under 661 px with a card open), they go 10 left of the zoom, top-aligned. They are left out where that would reach the credit (a stage under 480 px wide) or where the stage is too short for them beside the zoom (under 192 px, or under 300 px with a card open).
- **Language switch in the panel** (≤ 1 019 px; Elena, 5 Oct): EN · NL · FR on the kicker's row, right-aligned, ui 12 in ink-2 (the current one ink, underlined), 24-px targets that reach 3 px into the ladder's gaps, so the row stays 18 tall.
- **Room for the consent banner** (Elena, 5 Oct): while the card is up, on a phone the stage ends 13 px above it; on a desktop the zoom, the pan keys and a drawer end above it, and the panel never reaches it. On a short phone (Elena, 6 Oct) the bottom sheet and a card end 8 below the zoom (at most 44 % / 64 % of the stage, and never above inset + 122 + 8), and the stage keeps at least 206 px (the zoom and 56 px of sheet): where the screen has less, the page scrolls above the card instead. On a short screen (≤ 400 px tall: a phone on its side, 400 % zoom at 320 × 256; Elena, 6 Oct) the card is compact: one short line («May Microsoft Clarity set cookies and record your visit?») instead of the paragraph, the Privacy link for the rest, the same two buttons at 32 px, insets 10/14 and 8 from the edge; below 861 px it spans the foot of the screen with the line beside the buttons where they fit (59 px tall at 844 × 390, 99 at 320 × 256 against 174 and 214), so the zoom scrolls whole into view above it. A button is never narrower than its word and never hyphenated. Both buttons are the site pages' ghost pill (one rule in `consent.css`: 1-px `--rule-2` outline, ivory at 35 %, 70 % on hover, 48 px tall under 721 px), in the atlas's own ink and rule; until 6 Oct the atlas showed the browser's grey button.
- **Pan bounds** (Elena, 6 Oct): keys, arrows, a drag and a zoom about the pointer stop when a corner of the city reaches the middle of the free stage (where home puts the city's centre), so at least a quarter of the free stage stays city.
- **Focus after a consent choice** (WCAG 2.4.3; Elena, 6 Oct): Accept or Decline gives focus back to the last control focused outside the card (the skip link on a fresh page, «Change your choice» on /privacy), else to `<main>` without scrolling.
- **Light classes' edge** (WCAG 1.4.11; design wave, 5 Oct): the lightest steps of each ramp (lack-1/2, green-1/2, gain-1, loss-1) get a 0.8-px hairline in their ramp's dark step (lack-4, green-5, gain-3, loss-3), so the shape reads against the stage. The hairline is the sector's own stroke in place of the paper one, and those sectors are painted after the rest so no neighbour's paper outline covers it; never a second copy of the path (round 3, 6 Oct: the copy cost the landing 136 KB). Histogram bars within noise are `--noise-bar` (cloud-dark, 3.2 : 1), not `--noise`.
- **Map pins**: an ink dot with a paper stroke; the case name in italic serif.
- **Credit line**: fine 12/16, after the panel.

## Do's and Don'ts

- **Do** take frames and gaps from the Felt ladder. A new step needs a Felt measurement or a written derivation.
- **Do** keep the map's colour for measurement. The chrome has no green or red.
- **Do** show where every number comes from. The window and instrument go under the title, and each control is named.
- **Don't** make gaps uniform inside a card.
- **Do** set prose in cards with `text-wrap: pretty`, so a paragraph does not end on a lone word.
- **Do** make a map a labelled group when it holds controls (the audit pins), and a labelled image when it only shows.
- **Don't** let a chip, a word or a sign sit alone on a line: a wrapped chip row becomes a grid, and a short word or "=" ties to its neighbour (`typography.js`).
- **Don't** import landing components. Copy what the interface needs into its own tokens, and let them diverge.
- **Consider (open)**: Felt answers a selection with a small card beside the item (115:2). The atlas opens a full-height drawer. A light card first, with the drawer on demand, is the candidate next step.
