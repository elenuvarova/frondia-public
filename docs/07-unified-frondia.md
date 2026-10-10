# Unified Frondia — one flagship instead of five prototypes

Decided with Elena on 26 Sep 2026. Frondia absorbs the map projects; in the portfolio only the projects
merged into Frondia are removed (City Planner, Neighbourhood Fit Score, SpotFinder). Non-map projects stay.
The name stays Frondia for now; naming research continues.

## The product: one map, three questions, sector by sector

| Question | Lens | Source project | Brussels | Antwerp |
|---|---|---|---|---|
| **What does the neighbourhood lack?** | Everyday services by life scenario (family, remote work, seniors) | Neighbourhood Fit Score | ✓ | port (phase 1b) |
| | Shops within reach: distance to the nearest bakery, café, confectionery | SpotFinder | port (phase 1b) | ✓ |
| | Heat and shade: summer surface temperature over the city median, canopy share | Frondia (heat_2022_2025, rule_3_30_300) | ✓ | ✓ |
| | 3-30-300: canopy ≥ 30 %, a park of 1 ha within 300 m | Frondia (rule_3_30_300) | ✓ | ✓ |
| **What to place where?** | 14 kinds of public-realm objects, ranked by coverage gain with equity; named points and their controls | City Planner | ✓ | ✓ |
| **What actually changed?** | Greenness against 12 matched places, audits, monitoring | Frondia | ✓ | ✓ |

What is not taken: City Planner's London and Paris, SpotFinder's Leuven (Frondia is about Belgium; two
cities already show the method travels); SpotFinder's business "opportunity" score (Frondia reads the city
as a resident and a public body: distance to the nearest shop, not room for a competitor).
Tender Radar and Market Opportunity Map contribute ideas already inside Frondia (register before the works;
every number has a source), not layers.

## Phase 2 — new, never built in any of the projects

1. **"What if N more?"** — a budget slider per object type: where the next N go, how coverage grows,
   who gains. Needs the planner's coverage curve for ranks 1…40.
2. **Who is short** — under each lens, the lens measure by income tercile and the share of children and
   seniors in the worst third.
3. **The whole city before and after** — a swipe across true-colour Sentinel-2, summer 2017 against
   summer 2024, verdicts on top. Needs an Earth Engine export per city and year.
4. **Communes** — the Article 8(1) exemption for the 19 Brussels communes and Antwerp by the Commission's
   method, and the six projects registered before their works.

## Data for the site (scripts/site/site_data.py → site/public/data/)

Per sector, added to `<city>.json` (short keys, absent when not measured in that city):

| key | meaning | source layer |
|---|---|---|
| `fit` | `{family, remote, senior}` score 0–100 | fit_score |
| `low` | `{family, remote, senior}` three weakest services | fit_score |
| `hot` | summer surface temperature minus the city median, °C | heat_2022_2025 |
| `lst` | summer surface temperature, °C | heat_2022_2025 |
| `cs` | canopy share (ESA WorldCover) | rule_3_30_300 |
| `np` | share of the area within 300 m of a park ≥ 1 ha | rule_3_30_300 |
| `r3` | 0 none, 1 one of two, 2 both measurable parts of 3-30-300 | rule_3_30_300 |
| `kid`, `old` | share of children 0–14 and of people 65+ | population_age |
| `shop` | `{bakery, cafe, confectionery}` distance to the nearest, m | SpotFinder |

`points-<city>.json` — City Planner candidates: per type the coverage before/after (manifest) and the
40 ranked points (projected to the atlas SVG), each with its rank and, where registered, its role
(named / control) from `data/registry/named_points_<city>.json`.

## Colour

A lens that measures a lack needs its own sequential ramp: gain teal and loss red belong to change.
The lack ramp follows ColorBrewer's YlOrBr (Brewer 2003), light to dark = less to more lacking, checked
for monotone lightness and for step distinctness under protan, deutan and tritan vision. Warm reads as
"worse" for heat, missing services and distance alike. It never appears on a change map.

## Order of work

1a. Data export and atlas lenses with the data that exists; the sector page answers all three questions.
1b. Port Fit Score to Antwerp and SpotFinder to Brussels, so every lens exists in both cities.
1c. Landing: the three questions as one story; showcase, FAQ, colophon ("four prototypes, one product").
2.  The four new features above.
2b. Four more, added by Elena on 26 Sep:
    - **the sector dossier on the site**: the artefact the method exists to produce, printable from
      the atlas (passport, trend against control, who is short, the commitment, the limits);
    - **data download with its manifest**: each lens as CSV, with what it measures, how, from what
      source and with what threshold, so any number can be recomputed;
    - **the register of interventions read by a language model**, with a hand-labelled set and a
      published error rate (the rule baseline: 33 % precision at 100 % recall on 10 contracts);
    - **a third city, Ghent**: the Article 8 duty bites in Flanders, and Ghent is weak on 3-30-300.
3.  Portfolio: case study rewritten around the flagship; merged projects removed from the portfolio and
    their subdomains redirected to Frondia lenses — on Elena's command.

Every new part gets its references in Figma (her standing rule), and every lens its manifest entry.

## Phase 1 — done, 26 Sep 2026

**Every lens exists in both cities.** Each sector carries all four "what's missing" lenses and City
Planner's points: Brussels 724 sectors (627 with 200 residents or more), Antwerp 458 (352). Sectors
with fewer residents keep their numbers but are drawn grey and never ranked, so forests and the port
do not top a "lacking most" list. Fourteen kinds of object, 40 ranked points each, the first ten named
on 5 September 2026, the next ten their comparison.

- **Fit Score ported to Antwerp:** its pipeline gained an Antwerp config (16 REFNIS, bbox, 458 sectors)
  and reads De Lijn's GTFS as a stream (2.3 GB unpacked). STIB's feed would have given Antwerp no public
  transport at all. The layer's manifest says which feed each city uses.
- **SpotFinder ported to Brussels:** a Brussels entry in its config; the same five pipeline steps.
- These ports are **uncommitted changes in the two source repositories** (`neighbourhood_fit_score`:
  `pipeline/config.py`, `02_sectors.py`, `03_pois.py`; `spot-finder-geo`: `pipeline/config.py`). Their
  results are imported here by `scripts/report/import_projects.py` and registered in both manifests
  (Brussels 38 layers, Antwerp 36).

**The atlas asks three questions** (`site/apps/atlas`, lens logic shared in
`site/packages/shared/lib/lenses.js`): a question switch in the bar; one panel per question; a sector
page in three parts; deep links `?q=need&lens=…`, `?q=place&obj=…`, `?q=change`.

**The landing shows the three questions** as section (4) "One map, three questions": three live
maps, each opening the atlas on its lens.

**Checked against references before shipping** (Figma 125:2 rows 36–42, 124:2 row 18, 108:5 last
row). The check found and fixed:

- chips that wrapped and left one alone (now two by two);
- a second chip row, now a choice row (Mapbox Studio);
- part and field labels at one level on the sector page;
- a select radius off the scale;
- the system scrollbar cutting the cards' corners (Elena's call: a thin inset bar with edge fades, from
  Osmo's advice);
- "r =" left at a line end;
- a 43-px gutter where the principal layout measures 32.

Decided by Elena the same day:
- the hero's kicker names the whole atlas: "Evidence atlas · Brussels & Antwerp";
- the three-maps row may lean left: the heavier mass on the left is right;
- the concept pages (`/concepts`, `/directions`, `/rings`, `/lab/hero`) are not public: they are
  development-only and left out of the production build;
- the colophon carries her address as a `mailto:` link;
- the ports live in this repository: `pipelines/` holds the code of City Planner, Fit Score and
  SpotFinder with the Frondia ports (pipelines/README.md), and the importer reads their output first.

The point roles got their reference on 26 Sep, once Mobbin was back: Forest’s map guide draws one P filled
for a bay you must use and as an outline for one you may use (Figma 125:2, row 39). The fill carries the
stronger role, here "named".

## Five rounds of re-checks — 26 Sep 2026

Asked for by Elena after the phase 1 deploy. Each round came from its own angle: find, fix, check.

1. **Numbers against the data.**
   - The services "fifths" were fifths of all sectors, forests and the port included, so the worst
     fifth held only 10–16 % of the coloured ones. They are now fifths of the lived-in sectors
     (`fitq`, 18–21 % each).
   - The heat lede printed Brussels's r = −0.89 in Antwerp too; it is now the city's own (−0.66).
   - The colophon said 74 tests while there were 82; a test now keeps the published count in step
     with the suite.
2. **Code review.**
   - A sector outside the measured set was told "the difference is outside the city's own noise".
   - The raw view said "a third" of the city looked greener. It is 39 % in Brussels and 14 % in
     Antwerp, and now reads from the data.
   - The place view lacked the Copernicus credit and 3-30-300 lacked ESA WorldCover's.
   - A near-empty sector's page gave its numbers without saying it is not shaded or ranked.
   - The phone breakpoint was off by one pixel between the code and the CSS.
   - The address lost the question and lens on the first click. It now follows the view.
   - A stale sector from the other city stayed in the address after a switch; this was caught by
     the round's own test and fixed.
3. **Accessibility (axe, WCAG 2.2 AA; NN/g).**
   - The twin maps' first count failed contrast (2.2 : 1).
   - The interactive map was an image holding focusable pins.
   - Phone controls were 28–32 px; they are now 40, and 44 when alone.
   - On a phone the points' key was hidden, with no other key.
   - The scrollbar thumb was 1.9 : 1.
   - Focus could land under an edge fade.
   After the fixes axe finds nothing in 12 states.
4. **Every state at every width.** Fifty-three states × five widths: no errors, no overflow, no
   hanging words. By eye, two more fixes: four chips wrapped at 320, and paragraphs ended on a lone
   word (now `text-wrap: pretty`).
5. **Copy and documents.**
   - "meets one of two" now matches its legend.
   - "The first ten of fourteen kinds" was ambiguous.
   - The unmeasured-sector sentence was reworded.
   - Both design systems, this plan and the project notes are updated.

Tests: 87.

## Phase 2 — progress

### 1. Who is short — done, 26 Sep 2026

Under each need lens, a reading and two small blocks (`Equity` in `apps/atlas/src/pages/Atlas.jsx`,
numbers from `site_data.equity`):

- **By income:** the lens's own measure for each third of residents by the median taxable income of
  their sector (Statbel 2023). Thirds of residents, not of sectors: the poorest sectors are the most
  populous (40 % of Brussels residents live in the poorest third of sectors).
- **Who lives in the worst-off group:** all residents as the reference, then children under 15 and
  people aged 65 and over (2021 census) with their difference in points. The group is cut by the
  lens's own value, so equal values at the edge stay together and it can be named ("score 83 or less").
  For 3-30-300 the group is the sectors that meet neither part.

What it says, the same in both cities:

| | Brussels | Antwerp |
|---|---|---|
| Heat, poorest vs richest third | +1.6 °C vs −1.1 °C | +3.4 °C vs −0.7 °C |
| Children / 65+ in the hottest third, all residents | 37 % / 24 %, 34 % | 37 % / 25 %, 34 % |
| 3-30-300: meets neither part, poorest vs richest | 61 % vs 31 % | 64 % vs 28 % |
| Services for a family, poorest vs richest (score) | 89 vs 77 | 75 vs 56 |
| 65+ in the worst-served third, all residents | 43 %, 36 % | 40 %, 35 % |

The lack does not fall on one group. Heat and missing canopy fall on the poorest third and on
children; missing everyday services and distant shops fall on the richer outskirts and on older
people. The strip says both, lens by lens.

References (Figma 125:2, row 43): Deel's side panel for the rows (label and value on one line, a thin
bar on a hairline track) and Steep's breakdown for the age rows (each segment against the total, in
points). Bars are ink: the lack ramp means a class on the map. On a phone the blocks give way to the
reading, as the ramp stands in for the legend. Checked headless: axe finds nothing in four states, no
hanging words, no horizontal scroll. Two known-answer tests hold the findings.

### Loose ends closed the same day

- **Audit thresholds follow the case's own scheme.** A case matched its 12 places by greenness alone
  but took the instrument's threshold from the manifest (in Brussels matched on greenness and heat),
  and compared its land-cover classes as raw change against thresholds calibrated on effects against
  a control. Now `audit_case.py` calibrates every threshold from the same table with the case's own
  scheme, and the classes are effects against the same 12 places (`scripts/gee/sector_landcover.py`
  stores the per-sector classes; the new table reproduces the 1 September calibration to five
  decimals). Porte de Ninove: threshold 0.0373 → 0.0362 (6.8× instead of 6.6×); built-up −0.123,
  grass +0.098; shrub +0.004 is now noise (as a raw change it passed the instrument's threshold).
  Droogdokkenpark: numbers move in the third decimal, verdicts stay.
  Re-measuring the footprints today gives +0.244 and +0.286 instead of the published +0.246 and
  +0.289: the Sentinel-2 archive was reprocessed after the 1 September pool was measured. The
  published effects stay, because an effect and its threshold must come from one run.
- **Source repositories.** The ports (Fit Score to Antwerp, SpotFinder to Brussels, Brussels and six
  object types in City Planner) are committed on a `frondia-port` branch in each; `main` and the
  deployed apps are unchanged, nothing is pushed.

### 4. Communes — done, 26 Sep 2026

The second view of "what changed" (`?view=communes`): Article 8(1) by commune, measured with the
Commission's method, and the projects registered before their works.

- **The map:** each commune dissolved from its Statbel sectors (`site_data.communes`, shapely: a 1-m
  buffer closes the slivers between sectors, holes and crumbs are dropped), filled with its green
  share in urban centres and clusters (ColorBrewer Greens, 7-class, classes 2–6; classes of 15, 30,
  45 and 60 %, so the test falls on a class edge). Every commune outlined, an exempt one in heavy ink.
  Names are placed from the largest commune down and give way where they would collide; on a phone
  they keep a 10-px floor.
- **The panel:** 4 of 19 Brussels communes exempt (Watermael-Boitsfort 66.2 %, Uccle 60.9 %,
  Woluwe-Saint-Pierre 52.1 %, Auderghem 50.4 %); the region as one, 39.3 %, is counted. Leaving the
  four out would take 33 % of the area and 15 % of the residents out of the count, but 59 % of the
  woody vegetation; the duty would rest on 15 dense communes, 32 % green on average. The numbers are
  computed as on the Article 8 page. Antwerp, one commune: 39.7 %, counted; the neighbouring communes
  in its package were not tested, and say so.
- **Registered before the works:** the six Beliris footprints of 2 September as outlines with no fill,
  numbered pins, and a list with what each expects; Neerpede is the refusal fixed in advance. Antwerp
  has none, because AG Vespa publishes no "works not started" status.

References (Figma 125:2, row 44): Grain's scale for the list (the threshold labelled once above the
rows, marked on every bar), Zillow's drawn boundary for the registered footprints, ColorBrewer Greens
for the fill. Checked headless: axe finds nothing on the commune view in both cities and on a phone.
The short-word ties now take any letter (`\p{L}`), since the atlas names French places ("parc à
Neerpede"). Two tests hold the view: every commune outlined and its verdict the 45/10 rule, and the
known answers above.

### 1 (plan numbering). What if N more? — done, 26 Sep 2026

In the place view, a slider over the planner's own ranking: how many objects to place, 0 to 40, and
the coverage of demand within 500 m it buys, with the curve beside it. The curve is City Planner's
`coverage_steps` from the same run as the ranked points (checked on all 28 types: first and last values
and the ranked ids agree), carried into the package points files and from there to the site; the
importer now carries it too. One line says how many of the N stand where the poorest third of
residents live: for Brussels toilets, 9 of the first 20. References (Figma 125:2, row 45): Dub's
calculator (the value above the slider, the result under it) and Mixpanel's volume chart (the curve as
the context of the choice, a dashed line for the recommended amount, here the ten named). Checked
headless: axe finds nothing in four states, the slider answers the arrow keys and the address follows.

### 3. The whole city before and after — done, 26 Sep 2026

A fourth view of "what changed", Photos (`?view=photos`): true-colour Sentinel-2 of summer 2017 left of
a line and summer 2024 right of it, across the whole map, with the sectors that changed beyond noise
drawn on top as outlines, not fills, so the ground stays visible. The switch "Subtract matched places"
works here too: off, 263 of 668 Brussels sectors are outlined as "looks greener" (Antwerp 60 of 423),
on, 16 (Antwerp 6). The case for the control, seen on the photograph.

- **The photographs** (`scripts/site/field.py --photos 2017,2024`): Level-1C for both years, because the
  catalogue's atmospherically corrected summer of 2017 leaves a black wedge west of Brussels; Cloud
  Score+ at 0.7 (the instrument uses 0.6) and the 30th percentile of the summer instead of the median:
  haze only brightens, and the median of 2017 (20 scenes, 3 to 5 clear per pixel) left north-east
  Antwerp blue. Each band is stretched between its own 1st and 99th percentile inside the city's frame,
  per year, gamma 1.35. They lie in the field's `wide` frame, so exactly under the sectors (a test
  checks the frame and the aspect). 1.5 MB each, loaded only when the view opens. No number is taken
  from them, and the panel says so, with the reason two summers still differ: light, haze and harvest.
- **The handle** (`SwipeHandle` in `apps/atlas/src/pages/Atlas.jsx`): the landing's split slider in the
  same hand, laid over the map. It writes `--split` on the stage and the upper photo's `clip-path`
  reads it, so a drag re-renders nothing but the handle. It stays on the free map (24 px from the panel
  and from an open drawer). The knob sits in the lower quarter on a desktop and just above the card on
  a phone, measured: at the centre it covered the very park a link to an audit flies to. A slider for
  the keyboard: arrows ±2 %, Page ±10 %, Home / End.
- **On the way:** audit labels no longer run into each other (Droogdokkenpark and Park Spoor Noord are
  75 map units apart: the left one's label goes left of its pin; zoomed in, both go right); parts joined
  by " · " (the panel's window line, the sector and audit headers) no longer leave a dot at the end of
  a line.

References (Figma 125:2, row 46): Leonardo AI's upscaler (the line across the whole canvas beside a
floating panel, both labels riding on the handle), ElevenLabs (the round knob with arrows), Higgsfield
(compare as one switch among the views), Zillow (the handle kept off the middle of the picture).
Checked headless at seven widths from 320 to 1440: axe finds nothing, no hanging words, no horizontal
scroll, the 44-px knob in view and on top of the map.

## Phase 2b — progress

### 1. The sector dossier on the site — done, 26 Sep 2026

`/dossier?city=<city>&sector=<id>` on the landing's side (a document, so in the landing's system), opened
from the sector card in the atlas ("Dossier for this sector"); without `sector=` it opens the sector the
open rule picks. It is `scripts/report/dossier_html.py` in English, section by section: passport, where
the sector stands on the city's scale, the trend against twelve matched places and what it does not
prove, the law's line for its commune, who is short (income thirds, children, 3-30-300 and heat), what
City Planner would place here, three measured cases instead of promises, the six-point commitment with
its refusals, the limits, the colophon. It prints on A4 from the browser (five pages; no section parted
from its title; the page's address on the sheet).

- **The numbers are the Russian dossier's, computed the same way** (`site_data.dossier`): medians over
  measured sectors, income thirds by sector with the Article 8 summary's population-weighted canopy, the
  third of sectors with the least canopy (flagged `lt3`) and the share of children in it (Brussels 46.3 %,
  Antwerp 50.2 %; the 45.9 and 49.7 in older notes came from the layer before its re-run), the seasons
  after the 2024 baseline read with the bulletin's own functions (43 Brussels sectors and 30 Antwerp
  ones carry an event), the rule's pick (Antwerp: Ten Eekhove first of 77; Brussels: Etangs Noirs third of
  110). Two tests recompute them from the layers. New per-sector fields: `b24`, `ha`, `k15`/`o65`/`o80`,
  `p30`/`p300` (the layer's own 3-30-300 flags, since a share rounded to 0.300 can belong to a sector
  that fails), `lt3`, `after`.
- **Headlines are computed, never written:** "canopy 41% below the city's median", "half the canopy" only
  at a ratio up to 0.6, the heat–canopy link "strong" or "almost deterministic" from the city's own r.
- **Layout from a measured principal:** anthropic.com's research articles, six pages measured headless
  (Figma 199:2, clean and redlined): a centred head, a reading column of 640, figures and tables 880,
  16 between paragraphs, 64 between sections, 96 from the head to the body. Type stays David's system.
- **Elements after references** (Figma 124:2, rows 19–26; 125:2, row 47): Elicit's report head and
  Dovetail's metadata rows (label and value, so no dot is left at a line's end), Sana's key figures,
  Churnkey's bar with a tick and Klima's reading in words, Notion's callout (framed by rules in print, as
  the AI in Design Report does), Bonsai's clauses, Stripe's table with its as-of line, OpenAI's
  colophon, komoot's print view, Telescope's place-panel action. Refero was not reachable: its server
  answers 403 "Invalid Host header" to authenticated requests (checked directly with curl).
- Checked headless: axe finds nothing at 320–1440 in both cities, no hanging words, no horizontal scroll;
  a table that still scrolls sideways on a narrow phone is a focusable region.

### 2. The data download with its manifest — done, 26 Sep 2026

`/data?city=<city>` on the landing: every layer behind the atlas as a CSV, fifteen per city, grouped by
the atlas's questions (what changed, the law, what's missing, what to place, cross-checks, sectors). Each
card says what the layer measures, its threshold and licence, and opens onto its method, source, where the
threshold comes from, its limits, its credit and every column. The manifest of each city is one JSON.

- **The package stays the source** (`scripts/site/downloads.py`, run by `site_data.py`): the layers and
  their Russian manifests are read, never changed. The English files translate what the package writes in
  words (verdicts `up / down / noise / refused`, the second instrument's `construction / canopy loss / not
  confirmed`, the commune test's reason rebuilt from its numbers) and add what a reader needs to recompute:
  sector centroids, the planner's forty places per kind with the sector each falls in, and the coverage
  after each place (the curve under "What if N more?").
- **Each season carries the bulletin's reading after documents** next to the instruments' one: Peterbos
  2026 is a canopy loss by both instruments and construction by the documents.
- **Thresholds and where they come from** are written from the run that made them (the Article 8 summary,
  the season's calibration file), not from the Russian text.
- **Terms of reuse:** layers built on OpenStreetMap (services, shops, 3-30-300, the planner's places) are
  derived databases and stay under the ODbL 1.0; the rest are offered under CC BY 4.0 with every source
  credited (Statbel's own terms are CC BY 4.0 with "Source: Statbel"). CC BY 4.0 for Frondia's own layers is
  a default that Elena may change.
- References (Figma 124:2, rows 27–28): Optimal Workshop's downloads and Skillshare's files for the card,
  Snowflake's data dictionary for the columns. Checked headless: axe finds nothing at 320–1440 with every
  card open; two tests hold the files (no Russian left, rows equal to the package's, every column
  described, ODbL where OpenStreetMap is used; the bulletin's reading of Peterbos).

### 3. The register of interventions read by a language model — done, 26 Sep 2026

`/register` on the landing: the 98 Brussels neighbourhood contracts (contrats de quartier durables), each
with its label and the words the label rests on, and how often the reading differs from a second one.

- **The reader** (`scripts/registry/extract_greening_llm.py`): Claude Sonnet 5 through Claude Code in print
  mode, one call per contract, tools, connectors and project files off, run from an empty folder. One frozen
  prompt and output schema (`prompts/greening_v1.*`), hashed; every answer is cached with the hashes and the
  contract text's, so a changed prompt shows as a new version. It lists every greening measure with a quote,
  a status (a commitment, an aim, a description), a kind and a place, then labels the contract: commits, an
  aim, no measure. The model never counts. **All 110 quotes are found word for word** in their contracts;
  the labels follow the prompt's own rule on all 98 (a test holds both).
- **41 of the 98 pages describe nothing**: every contract started in 1994–2006 has only photo credits and a
  budget on quartiers.brussels. The page shows them as "Not described", never as "no measure". Of the 57
  described: 33 commit, 7 name greening only as an aim, 17 have no measure. Four pages of 2022–23 lost their
  commune to the scraper; each description names it (`COMMUNE` in `scripts/site/register.py`).
- **The check.** 30 test contracts were drawn by seed (`greening_testset.json`, sha256 of seed:id, the ten
  development contracts left out) before any of them was read. The plan was a person's blind labels (a
  labelling page with a database, still open). Elena does not read French, and labelling French planning
  texts is not her job, so the reference is **a second model** (`check_greening_llm.py`: Claude Opus 5.5,
  its own prompt `greening_check_v1`, one label, the deciding quote and a reason, a fresh process that never
  saw the first reader's answers). Every title on the page says "second model", never "by hand"; a person's
  labels (`eval_greening.py --import`) replace these and the wording follows (`eval.kind`).
- **Result** (`eval_greening.py` → `greening_eval.json`, Wilson 95 % intervals): the two readings differ on
  **1 of 30 contracts** (3 %, 1–17 %; Cohen's kappa 0.93). Of the 19 contracts the second reading says
  commit, the first finds all 19; it names one more (19 of 20 agreed). The rule baseline on the same 30:
  18 of 19 found, 18 of 20 agreed. The one disagreement is Christine: "doit prioritairement bénéficier
  d'investissements qui permettront… des espaces verts de proximité" reads as a commitment to one model and
  as a need to the other; the page shows both reasons.
- **What the check does not say.** Two models of one family can misread a sentence alike, so agreement
  overstates accuracy; the page says so and keeps every quote and source link for a person to check. The
  rule does well here because the test pool is the richly described contracts, where measures are plain; on
  the ten development contracts it was 3 of 9 (33 %) against the old labels. On those ten the second reading
  agrees with the first reader on 8 and with the 1 September labels on 6: the old labels were too strict
  (88, 91).
- **Site and data** (`scripts/site/register.py`, run by `site_data.py`): `register.json`, a CSV with one
  row per quoted measure, and the check as JSON. The page groups a quote the model gave twice (one clause,
  two kinds) and decodes the two HTML entities the scraped texts keep.
- References (Figma 124:2, rows 29–33): Dovetail's highlights (a measure and its quote), Adaline and Cohere
  (the rate against a baseline, on the dossier's interval bar), Braintrust (a failing row), Intercom Fin (a
  three-step rating, drawn by form as the point roles), Maze (tabs with counts). Checked headless: axe finds
  nothing at 320–1440, no hanging words at six widths, no horizontal scroll. Tests 117.

### 4. A third city, Ghent — done, 26 Sep 2026

Ghent is the municipality itself (REFNIS 44021), not a box around it: 201 sectors of Statbel's 2024
register, 269,299 residents on 1 January 2024 (`scripts/registry/city_sectors.py`, which builds any city
the same way and also carries Liège and Charleroi). The engine takes it as a Flemish city built like
Antwerp (`engine/adapters/ghent.py` subclasses the Antwerp adapter; only paths and the default district
differ). Every layer the other two cities have was made for it in one afternoon:

- **Calibration** (201 sectors, each playing "intervention" once): NDVI threshold 0.0481, mean −0.0002,
  unbiased; Ghent is noisier than Brussels (0.0373) and Antwerp (0.0458) on the same instrument. The five
  Dynamic World classes are unbiased too. The Article 8 layer's own run gives 0.0404.
- **Article 8 layer, 2024 baseline** (population-weighted): NDVI 0.428, canopy 0.089. Trend against matched
  places: green −4 / +5 sectors, canopy −1 / +5. The poorest third lives with 0.073 canopy, the richest with
  0.132: a ratio of 0.55, as in Brussels (0.57) and Antwerp (0.51). Without matched places 54 of 185
  comparable sectors (29 %) would look greener; with them, 5.
- **Article 8(1) exemption** by the Commission's method: Ghent's urban centres and clusters are **44.4 %
  green**, 0.6 points under the line, with canopy at 18.9 %. Counting farmland as green (the test's other
  reading of Article 3(20)) gives 49.0 %, and Ghent would be exempt: the first city whose verdict turns on
  the reading. The atlas's communes panel and the landing's law row say so.
- **Monitoring, three seasons**: 5 candidate losses each season, none confirmed as canopy loss in 2024 and
  2025; in 2026 two constructions (Kiekebossen, two seasons running; Klosse) and one canopy loss confirmed by
  both instruments (Lake, 40 ha, no residents), cause not yet established from documents.
- **State layers**: summer heat (the hottest sectors, Flora, Sint-Jacobs, Kouter and Ledeberg-Centrum, run
  5–6 °C above the city's median; heat and canopy correlate at r = −0.53, weaker than Brussels −0.89 and
  Antwerp −0.66); canopy by ESA WorldCover and Proba-V (rank agreement with our trees class r = 0.85 and with
  WorldCover 0.71, lower than the other cities: many small inner-city sectors on a 100-m grid); the official
  canopy (WVL) against ours r = 0.81; 3-30-300 — 40.6 % live with 30 % canopy, 53.3 % within 300 m of a park,
  21.7 % meet both, 27.8 % neither. **Ghent does better than both other cities on 3-30-300** (Brussels 13.3 %
  both, Antwerp 8.3 %); the premise that it is weak, from a 2024 national ranking, is not borne out here.
- **Parks**: 68 named OSM parks of a hectare or more; the batch audit calls 21 greener, 1 lost, 23 noise and
  refuses 23 for want of comparable places.
- **The three merged lenses**: services (Fit Score, De Lijn's GTFS, 2,623 stops), shops (SpotFinder, the box's
  474 sectors cut to the city's 201: the importer now keeps a city's own units) and City Planner's 14 kinds
  (BIMD 2011 for deprivation, 184 of 201 sectors joined). Overpass refused connections halfway through the
  planner runs, and one run (defibrillators) came back "complete" with zero demand points — the trap already
  met in Antwerp. It was rerun through the lz4 mirror, and every run now fails loudly when a fetch warning
  or zero demand points appear.
- **Site**: a city picker replaces the two-button switch (a pill over a native select, after Sweatpals and
  DoorDash; `CITY_NAMES` in `content/en.js` feeds the atlas, the data page and the dossier); the landing's
  kicker, the cities answer, the law row and the canopy line read from the list of cities.

### 5. Liège and Charleroi: all three regions — done, 26 Sep 2026

Elena's decision after Ghent: the atlas stands in Flanders, Brussels and Wallonia. Both cities are the
municipality itself: Liège 184 sectors, 195,659 residents (REFNIS 62063); Charleroi 291 sectors, 204,205
(52011). Every Earth Engine layer ran on the Mac; the three merged pipelines ran in a cloud session
(`docs/research/2026-09-26-pipelines-runlog.md`).

- **Calibration**: the NDVI instrument's threshold is 0.0536 in Liège and 0.0396 in Charleroi; the Article 8
  layer's own run gives 0.0516 and 0.0408 (Liège's the widest of the five, 50 % wider than Brussels' 0.0345).
  All unbiased. The handoff note of 26 Sep called the layer's thresholds "calibration"; they are not.
- **The city greens by itself, or not**: without matched places Charleroi would show 48 of 269 sectors
  "greener" (18 %), with them 5. Liège barely greened at all between the two windows: the raw median change is
  +0.014 against +0.026–0.033 in the other four cities, so only 3 of 163 would look greener without control
  and 1 does with it. The landing's rustle-against-growth argument stays on Brussels, where it is measured.
- **Article 8(1)** by the Commission's method: **Liège exempt on the line** (46.0 % green in urban centres and
  clusters; without water as green 41.4 %, and it would not be); **Charleroi exempt** under every reading
  (48.9 %). The atlas's communes panel and the landing's law row print both, with Liège's unstable reading.
- **Equity**: the poorest third lives with half the canopy of the richest in Liège (0.50), two thirds in
  Charleroi (0.66). Heat and canopy: r = −0.80 and −0.78.
- **Who is short**: the gaps are smaller in Wallonia. People aged 65 and over live in the hottest third less
  often than residents overall in every city, by 3–4 points in Wallonia against 8–10 elsewhere; children live
  there less often in Liège (−3.9) and about as often in Charleroi (+0.6); 65+ live in the worst-served third
  slightly more often in Liège (+2.1) and as often in Charleroi (+0.1). `WHO_IS_SHORT` in
  `tests/test_unified_site.py` keeps each city's own answer.
- **Merged lenses**: Fit Score with TEC's GTFS; SpotFinder and City Planner's 14 kinds from the Geofabrik
  extract of 25 Sep 2026 (`--pbf`), because Overpass refused first the cloud and then the Mac. Checked against
  Ghent's seven kinds run through Overpass the same day: equal to the unit on existing objects and demand
  points. **Charleroi's OpenStreetMap is thin** (11 toilets, 6 defibrillators, 1 drinking fountain for 204,000
  people): its low coverage "today" partly measures the map. The place panel now says so for every city
  (`PLACE.mapped`), from the limit each manifest already carried.
- **Execution line**: City Planner's points named for both, 140 named and 140 control each
  (`data/registry/named_points_{liege,charleroi}.json`, 26 Sep 2026).
- **The dossier rule picks no sector** in either city: it asks for a commune the law counts, and both are
  exempt. The rule is not loosened; `/dossier?city=liege` without a sector says why and points to the atlas.
  Any sector's dossier still opens from the atlas.
- **Found on the way**: "Registered before the works" printed Antwerp's reason ("AG Vespa publishes no …
  status") for every city without records, Ghent included. Now only Antwerp's source was read and has no such
  status; for the others the page says no source has been read yet.
- **Checks**: 176 tests; both builds; headless on 27 states × 5 widths (320–1440): no horizontal scroll, no
  hanging words, axe clean at 1440 and 390, no console errors.

## Phase 2c — ideas taken from the neighbours (decided by Elena, 26 Sep 2026)

After the competitor scan of the Netherlands and France (Cobra, NL Greenlabel, PBL; Kermap, Mon Diagnostic
Artificialisation, APUR, Lyon's Plan Canopée, Ecoteka), Elena took all six:

1. **Sealed and unsealed ground** — from France's Mon Diagnostic Artificialisation (artificialised /
   renaturalised between two dates per commune), with our noise threshold. — **done, below.**
2. **Net balance in hectares against the 2024 base** — the same tool's net bar chart; Article 8 counts net
   area, and the atlas counts sectors. Needs a hard classification per pixel and its own calibration; the
   trajectory to 2030 is not forecast, only "how much must come back to cover the measured losses".
3. **A commune page with "enter your commune"** — Kermap's Nos Villes Vertes, Lyon's commune canopy
   atlases, NL Greenlabel's dashboards.
4. **The zero measurement in PBL's form and the Commission's export (`t8_UEAPolygons`)** — from the Dutch.
5. **The detector's published error rate against regional LiDAR and orthophotos** — how APUR, Lyon, Kermap
   and Cobra measure; their data as outside truth, not as competition.
6. **Plantings and fellings from municipal tree inventories** — Cobra's municipal planting data, Ecoteka's
   tree register; an execution line, named points against control.

Research for 5 and 6 (and a scan of players for bins, defibrillators and the other point objects) goes to
cloud sessions, reports on branches `cloud/research-data-lidar-trees` and `cloud/research-point-objects`.

### 1. Sealed and unsealed ground — done, 26 Sep 2026

The Article 8 layer already held each sector's **built-up effect against the same twelve matched places** as
greenness (`built_eff`) but no threshold of its own. Those effects are the instrument's null distribution
(every sector played "intervention" once), so the threshold comes from them without Earth Engine:
`engine.calibrate.from_effects`, `article8_data.py --city <c> --from-layer`. The mode first recomputes the
greenness and canopy thresholds from the stored effects and refuses to write unless they match the summary
(they do, to 0.00004 in all five cities). A future Earth Engine run calibrates built-up with greenness and
canopy in the same pass.

| | threshold (same run) | instrument's own | sealed beyond noise | unsealed beyond noise |
|---|---|---|---|---|
| Brussels | 0.0245 | 0.0247 | 8 (3,238 residents) | 18 (10,305) |
| Antwerp | 0.0263 | 0.0279 | 7 (6,782) | 9 (3,983) |
| Ghent | 0.0304 | 0.0327 | 5 (1,979) | 4 (1,084) |
| Liège | 0.0419 | 0.0382 | 3 (3,945) | 4 (1,476) |
| Charleroi | 0.0339 | 0.0345 | 8 (1,051) | 6 (387) |

All five null distributions are unbiased. The instrument knows what the documents know: Tour et Taxis and
Chemin de Fer (Molenbeek), building sites of 2021–2024, are sealed beyond noise; Gare de Formation (Evere), a
marshalling yard, is unsealed while its greenness stays within noise — **less built-up is not always a park**:
demolition down to bare ground reads the same, and the panel says so (the Quai des Matériaux lesson).

Atlas: "What changed · Sectors" gets a **Measure** row (Greenness / Built-up ground; `?m=built`), the choice
row already referenced by Mapbox Studio. Sealed takes the loss ramp and unsealed the gain ramp, as the French
tool colours artificialised red and renaturalised green; the legend is the distribution of the same effects
(step 0.005, as greenness); the toggle "Subtract matched places" gives way to a line saying there is no raw
view (the run kept each sector's effect, not its own before and after). The sector page adds a row
"Built-up ground against matched places". The data page exports `built_verdict` with its dictionary entry.
A class probability is not a share of the ground, and the words never say hectares — that is item 2.

Figma 125:2, row 49: our view beside Mon Diagnostic Artificialisation's map (Lyon, OCS GE 2017 → 2020) and its
net bar chart, kept as the form for item 2. Tests: `test_article8_sealing_threshold_is_the_same_runs_noise`
(five cities), `test_article8_sealing_known_answers`, `test_sealed_ground_on_the_atlas_is_the_layers_verdict`
(five cities). 187 tests.

### 4. The zero measurement in PBL's form and the Commission's file — done, 26 Sep 2026

`scripts/official/art8_baseline.py --city <c>` repackages what `art8_official.py` measured; nothing is
recomputed and nothing needs the network while its cache is there. Three outputs per city, each in the manifest
with its reason for having no threshold (a level for one year, as in the Commission's own format):

- **`art8_baseline_2021.csv`** — the Dutch form (PBL, *Definitieve nulmeting groen*, 25 Aug 2026): one row per
  commune, the urban ecosystem's area and the green and canopy inside it in hectares and per cent, for both
  boundaries the Commission leaves to the country (urban centres and clusters inside the LAU; the whole LAU),
  the verdict and whether it is stable; a city of several communes adds "all together". Brussels: the region's
  urban centres and clusters are 14,546 ha, 39.3% green, 30.3% canopy — counted.
- **`art8_sensitivity_2021.csv`** — the 45/10 verdict under every reading the test runs (official, arable as
  green, without water, commune from Statbel sectors): PBL writes that the result "depends strongly on the
  method", and here that is a row per reading.
- **`t8_UEAPolygons_ucuc.gpkg`, `t8_UEAPolygons_lau.gpkg`** — the file a country uploads to Reportnet 3, on the
  schema of the EEA/JRC example (github.com/eea/NRR_Art8, commit of 22 Sep 2026, cloned and read on 26 Sep, not
  taken from the cloud report): EPSG:3035, MULTIPOLYGON, `fid` inherited from GISCO, `lau_id` as
  `lau2024.BE.21001`, `area_tcc` as text with five decimals, `area_ugs` filled with our reading of Art. 3(20)
  (empty in the Commission's example, and the manifest says so). The GeoPackage is written with sqlite alone:
  GISCO's geometry blobs are already MULTIPOLYGON in 3035 and go in unchanged. **Checked with GDAL 3.12**
  (pyogrio in a scratch environment): all ten files open, and their layer, CRS, geometry type, field names and
  types equal the Commission's example.

The data page's "The law" group now offers the two CSVs and the two GeoPackages (a `format` field per layer;
a GeoPackage goes out byte for byte). WVL 2021 is allowed for draft plans only: every file says so.
Test: `test_art8_baseline_is_the_official_layer_repackaged` (five cities). 192 tests.

### 2. The balance since the 2024 base, in hectares — done, 26 Sep 2026

`scripts/gee/art8_balance.py --project <id> --city <c>`: one Earth Engine run per city (15–60 s). Hectares need a
hard class, since a Dynamic World probability is not a share of the ground: each summer (June–August) the class
with the highest mean probability wins each 10 m pixel, and a class's share of the sector times its area gives
hectares. Urban green is the Regulation's reading used by the official layer (CLCplus 2,3,4,5,6,8,10): trees,
grass, shrub, flooded vegetation and water, not crops. The base is summer 2024 (the law's), the seasons 2025 and
2026. Each sector's change in share is set against the 12 places most alike in 2024 by greenness and surface
temperature (the Article 8 layer's scheme), and **each class and season gets its own threshold from the same
run** (30 null distributions, all unbiased). Hectares beyond noise = effect × area; net = gained − lost beyond
noise, comparable sectors only.

| 2024 → 2026, beyond noise | urban green | tree canopy | built-up | raw green / built-up, no control |
|---|---|---|---|---|
| Brussels | −33.0 / +16.1 = **−16.9 ha** | −31.7 / +11.5 = **−20.2** | −1.7 / +30.8 = **+29.1** | −114.5 / +157.5 |
| Antwerp | −36.4 / +75.1 = **+38.7** | −20.1 / +20.5 = **+0.4** | −5.3 / +26.2 = **+20.9** | −585.9 / +573.3 |
| Ghent | −9.4 / +23.5 = **+14.1** | −40.0 / +56.8 = **+16.8** | −41.0 / +18.7 = **−22.3** | −470.7 / +291.8 |
| Liège | −3.2 / +34.1 = **+30.9** | −15.9 / +8.6 = **−7.3** | 0 / +9.0 = **+9.0** | −77.3 / +135.6 |
| Charleroi | −62.1 / +28.5 = **−33.6** | −41.3 / +0.8 = **−40.5** | −18.0 / +51.1 = **+33.1** | −99.0 / +177.0 |

**The raw totals are the argument again.** Without matched places Antwerp would have lost 586 ha of green and
sealed 573 ha in two summers — the classes shift from one summer to the next. One summer against another is noisy:
the thresholds are 3.4–11 % of a sector's area, against 1.4–4.2 % for class probabilities over the four-year windows.

Known answers: **Wolvendael** (Uccle; the storm of 9 July 2024, about a hundred trees felled) loses canopy beyond
noise in both seasons (1.4 and 2.2 ha), as in the monitoring bulletins; **Parc Forestier** is refused (too green to
match). Wolvendael also reads as more built-up beyond noise: when trees fall, a mixed pixel's winning class can
become built-up — a limit printed with the numbers.

Atlas: the Communes view gets **"Since the 2024 base"** under the exemption test: urban green, canopy and built-up,
lost / gained / net in hectares for the latest summer, as rows on a hairline track with a centre line (left less,
right more; more built-up takes the loss colour), the raw city total under them as the reason for the matched
places, and the limits. By commune the same sums are in the city JSON for item 3. Data page: `art8_balance_2025`,
`art8_balance_2026` under "The law", each with its three thresholds. Figma 125:2, row 50 (beside Mon Diagnostic
Artificialisation's net bars). Tests: `test_art8_balance_hectares_are_the_same_runs_noise` (5 cities × 2 seasons),
`test_art8_balance_known_answers`. 203 tests.

### 3. The commune page, "enter your commune" — done, 26 Sep 2026

`/commune?code=<NIS>` on the landing (a document, in its system, on the dossier's layout); `/commune` without a code is
the index: the finder and the 23 communes by city with their verdict chips. Data: `site_data.commune_pages()` →
`site/public/data/communes.json` (43 KB, one file for all five cities) — every commune the Commission's test ran on
(Brussels 19, the other four cities one each). Nothing is recomputed: the test and its readings (art8_official,
art8_sensitivity), the zero measurement in hectares (art8_baseline), the balance since 2024 summed from the sectors
beyond noise (art8_balance), the 2017–2024 verdicts of the commune's sectors, the season bulletins after documents
(`downloads._monitoring`), the projects registered before their works (point in sector), the audit cases and the
dossier sector when the open rule picks one here.

The page: head (kind of territory, region, NIS; residents, area, sectors measured, LAU code), the **finder** and the
way to the atlas and the data page; **Article 8(1)** — green and canopy in urban centres and clusters, each written
against the region (Brussels) or the 45 % and 10 % lines, canopy per resident in m² (Kermap's figure), the reading in
words and the table of readings; **the zero measurement** in hectares for both boundaries; **since the 2024 base**,
lost / gained / net per class for 2025 and 2026, and what the bulletins name here (Uccle: Wolvendael, canopy loss,
both seasons); **2017–2024** sectors greener and lost, sealed and unsealed, each a link into the atlas; **on the
record** — registered projects (Anderlecht: Neerpede, refused before the works), audits (Anderlecht: Porte de Ninove;
Antwerp: Droogdokkenpark, Park Spoor Noord) and the dossier (Antwerp: Ten Eekhove).

The finder is an ARIA 1.2 combobox with a listbox (the APG's pattern): accents folded, both official names and the
NIS code matched, arrows / Enter / Escape, 44-px options. Ways in: the landing's law row ("Find your commune"), and
every commune's name in the atlas's Communes view.

**Found and fixed on the way: a double rounding in the atlas.** The Communes view read the layer's four-decimal
shares and rounded again to a tenth: Uccle printed 60.9 % and Molenbeek 27.1 %, against 60.8 and 27.0 on the Article 8
pages (0.60848, 0.270466). The site now reads the summary's six decimals, and `art8_baseline_2021.csv` keeps its
percentages to four places. Figure references are written without two-letter words ("21.5 points above the region"):
the non-breaking rule chained "+22.3 pt on the region" into a run a 320-px phone could not hold.

Checked headless: 6 pages × 4 widths (320, 390, 768, 1440) — no horizontal scroll, no hanging words; the finder by
keyboard. References in Figma 125:2: row 51 (finder beside Mon Diagnostic Artificialisation's territory search), row
52 (the page beside Kermap's key figures for Lyon and the French summary strip). Test:
`test_commune_pages_read_the_packages`. 204 tests.

### 5. How often the detector is wrong — against Groenkaart Vlaanderen, done, 27 Sep 2026

The outside truth the plan asked for exists in Flanders: **Groenkaart Vlaanderen** (ANB / Digitaal Vlaanderen, open,
Modellicentie Gratis Hergebruik), a 1 m classification of summer aerial photographs into high green (over 3 m), low
green, farmland and no green, published every three years **2009–2024** on the ANB web coverage service. Different
sensor, resolution and method from Sentinel-2. Brussels and Wallonia have no two comparable editions (Brussels'
vegetation map is consistent only from 2020; Wallonia's LiDAR is 2013–14 and 2021–22), so the check is Antwerp and Ghent.

`scripts/official/groenkaart_check.py` (the rule is written in its docstring before any result): before = 2018,
after = the mean of 2021 and 2024, as the detector's windows 2017–19 → 2021–24; shares per Statbel sector at 4 m
(1 m sampled by nearest neighbour; answers of 4 MB took a minute, of 1 MB half a second); the map goes through **the
same method** — the same 12 matched places, its own null-distribution threshold, the same refusal — so its verdict,
not its raw difference (it shifts between editions, and summer 2018 was a drought), is what ours is set against.
Pure Python: a 40-line TIFF reader (checked against rasterio on a tile), sectors exported once to Lambert 72
(`data/{antwerp,ghent}_sectors_31370.geojson` from the Statbel 2024 register). Alignment checked: the map's
high-green level and WorldCover's canopy correlate r = 0.93 (Antwerp) and 0.88 (Ghent) by sector.

| | canopy: noise agreed | canopy: "changed" agreed | canopy: GK change caught | greenness: noise | greenness: "changed" |
|---|---|---|---|---|---|
| Antwerp | 395 / 406 (97 %) | 5 / 16 (31 %) | 5 / 17 | 396 / 408 | 4 / 16 |
| Ghent | 174 / 177 (98 %) | 2 / 6 | 2 / 8 | 171 / 180 | 0 / 9 |
| **Both** | **569 / 583 (98 %)** | **7 / 22 (32 %)** | 7 / 25 | 567 / 588 | 4 / 25 |

No opposite signs on canopy in Antwerp, one in Ghent; Spearman between the two effects 0.31–0.46. **The two instruments
agree almost always on "nothing changed" and about a third of the time on which sector did.** A sector's "changed beyond
noise" is a candidate, not a proof — which is how the project already treats it (a loss is named only when two
instruments and documents agree). Published where the claim is made: a line under the greenness view of Antwerp and
Ghent in the atlas, a FAQ answer on the landing ("How often is the detector wrong?", pooled canopy), and the layer with
its check on /data under "Cross-checks". Test: `test_groenkaart_check_reproduces_and_is_aligned`.

### 6. Tree registers as an execution line — done, 27 Sep 2026

`scripts/registry/tree_registers.py --city <c>`: a snapshot of the city's open tree register with stable ids in
`data/registry/snapshots/trees_<city>_<date>.csv.gz` (Antwerp's 36-character GUIDs as 12 characters of their SHA-1,
coordinates to about a metre), each tree placed in its sector, and the layer `trees_register` by sector for the commune
the register covers (a sector of another commune is not "0 trees"). From the next snapshot, trees that leave the
register are counted by sector — felled, dead or re-surveyed; the register does not say which.

- **Ghent** (`locaties-bomen-gent`, 68,240 trees, updated daily): 18,085 carry a planting year; 7,716 planted in
  2020–2025 (2024: 2,258). **Where they went**, by thirds of lived-in sectors: the least-canopy third got 24 % of the
  plantings and holds 48 % of residents — 13.2 trees per 1,000 residents against 39.0 in the rest — but **per hectare
  it got more**: 9.6 per 10 ha against 6.9. The same for the poorest third (10.8 vs 6.7 per 10 ha). Those sectors are
  dense; both readings are printed, and neither is turned into "planted in the wrong place".
- **Antwerp** (`boom`, 134,873 trees, 1,880 "future trees"): no planting year; the source states no licence, so only
  counts per sector are published. **Brussels** (Ville de Bruxelles register, 31,674 trees, CC BY 4.0): the commune of
  Bruxelles only, no planting year.

On the site: the commune page's "The city's tree register" (Bruxelles, Antwerp, Ghent; Ghent with plantings by year and
the where-they-went table), and `trees_register` on /data under "What to place". Test:
`test_tree_register_layer_matches_its_snapshot`. ⚠️ If the repository goes public, Antwerp's raw snapshot needs its
licence checked or leaves the repository.

No new kind of element was introduced by 5 and 6 (a FAQ item, a panel line, the dossier's figures and table), so no new
Figma row. 209 tests.

### The city registers at the named points — from the players research, items 1–3, 27 Sep 2026

The cloud research on who else places, registers and monitors street objects
(`docs/research/2026-09-26-point-objects-players.md`) found no one naming points in advance with a control group, and
official open registers beside OSM in four of the five cities — some with installation dates. Three of its proposals
are done (`scripts/registry/object_registers.py`):

1. **Snapshots from today.** 31 open sources (Antwerp's ArcGIS layers, Brussels Mobility's UrbIS street furniture and
   regional bike parking by WFS, Ville de Bruxelles, Ghent and Liège on Opendatasoft) in
   `data/registry/snapshots/objects_<city>_<date>.csv.gz`, with an index of address, licence, count and a hash of the
   normalised rows, and what each date field means (installed, opened, recorded in the GIS). No portal keeps its history,
   so only kept snapshots will date an appearance. Charleroi has no portal; Ghent's toilets have no coordinates.
2. **A second column for the execution line** (`data/registry/named_points_<city>_official.csv`): per named and
   comparison point, the nearest official object of its kind, those within its 50 m check radius with their dates,
   those within 500 m.
3. **Map gaps marked.** An official object within 500 m that the planner's OpenStreetMap (its runs of 4–5 Sep, copied into
   `data/registry/planner_existing_<city>.csv.gz`) did not have within 50 m is a gap of the map, not of the street.
   Antwerp's defibrillators: 4 of 10 named and 3 of 10 comparison points — the number the cloud session found by
   itself. **Map gaps are more common at named points** (Antwerp toilets 9 vs 5, Brussels recycling 8 vs 3, Brussels
   benches 4 vs 0): the planner picks where the map looks empty, and part of that emptiness is the map's.

Two rules written into the check before its first run (`osm_appearance.py`, `AppearanceResult.gap_caution`): a point
where an official object already stood within the radius (dated before registration, or undated at the first
snapshot) **leaves the named-against-comparison count** — 9 in Antwerp, 1 in Brussels, 3 in Liège; and a map-gap share
that differs between the groups by 20 points or more **puts a caution into the verdict**. The atlas says both under
each kind in "What to place"; the planner points on /data carry the four new columns. The points, their hashes and
their date are untouched. Tests: `test_city_registers_mark_the_named_points`, `test_appearance_verdict_warns_on_a_map_gap_imbalance`.
211 tests. To keep the snapshots useful, `object_registers.py` and `tree_registers.py` are to be run each season.

### Registered before the works in Ghent; sources read for Liège and Charleroi — 27 Sep 2026

The open item from the handoff: no source listing the three newer cities' projects before their works had
been read. Two parallel desk searches, every source opened (`docs/research/2026-09-27-registers-before-works.md`).

- **Ghent keeps its own register** of spatial projects on data.stad.gent (359, status and the city's own
  polygons) beside the parks department's parks (status "gepland"). `scripts/registry/fetch_ghent_projects.py`
  snapshots both (Opendatasoft keeps no versions, so our snapshot is the moment of fixation), lists the green
  projects "In voorbereiding" of a hectare or more, prints status changes since the last snapshot, and asks
  GIPOD, the Flemish register of works in the public space, which city works already run inside each
  footprint. GIPOD sees only the public space; its WFS takes longitude first and silently returns records from
  the far end of Flanders in the other order.
- **Two records** (`scripts/registry/preregister_ghent.py`): Papiermolenpark (9.4 ha, the parks department's
  polygon; the page, archived 14 Nov 2025, says "In voorbereiding" and gives no timing) with 12 controls named
  (gap +0.0397), and Groenrealisatie Rosdambeekvallei (20.2 ha; the register's status and a demolition permit
  granted 20 Aug 2026) **refused in advance**, gap +0.0476. Eight candidates were not written, each for a
  stated reason (works under way, planting or demolition inside the 2023–25 baseline, no footprint, no
  funding) — listed in the script.
- **The baseline and control scripts only append now.** Both used to recompute every record and overwrite the
  file: run for Ghent, they would have replaced Brussels' baseline of 2 September with one taken later. The
  control pool is the record's own city (it was Brussels for every record) and leaves out any sector that
  touches another registered footprint. Found on the way: Josaphat's control of 2 September includes the
  sector CINQUANTENAIRE (PARC), 15 % of the Cinquantenaire restoration's footprint; a fixed control is not
  renamed, the rule holds from now on (`test_preregistered_controls_avoid_other_footprints`).
- **Site.** The atlas's lede names each city's source ("projects from the City of Ghent's own register");
  two new expectations (`park_creation`, `green_realisation`). Liège and Charleroi no longer say no source was
  read: Wallonia has no register like Beliris; Fontainebleau (works from autumn 2027) and Chênée wait for a
  traced outline of the published plans, Square Hiernaux (1.7 ha) for its permit plans.
- **For Antwerp** the same GIPOD and Omgevingsloket (96 AG Vespa permit filings since 2024) can supply the
  dates and the "works started" signal AG Vespa lacks — the next step there.
