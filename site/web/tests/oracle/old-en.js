// Words live here; numbers come from /data/*.json (built from the city bundles).
// Every claim in this file was checked against the Russian source pages and CLAUDE.md.

// The cities the site carries, in the order of every city picker (atlas, data, dossier). A city is
// added here once its bundle and site data exist (docs/07-unified-frondia.md).
export const CITY_NAMES = { brussels: 'Brussels', antwerp: 'Antwerp', ghent: 'Ghent', liege: 'Liège', charleroi: 'Charleroi' }
export const cityOf = (key) => (CITY_NAMES[key] ? key : 'brussels')

export const CASES = {
  ninove: {
    city: 'Brussels',
    place: 'Porte de Ninove',
    title: ['A wasteland by the canal became a ', 'meadow park', '.'],
    story:
      'Parc de la Porte de Ninove opened in autumn 2019 on a vacant lot where Anderlecht, Molenbeek and the City of Brussels meet.',
    reading:
      'Sealed ground went down and grass went up, and a second instrument agrees. Canopy did not pass its own threshold: this is a meadow park, and the verdict says so.',
  },
  droogdokkenpark: {
    city: 'Antwerp',
    place: 'Droogdokkenpark',
    title: ['+0.29 on paper. ', 'Half of it', ' was a building site.'],
    story:
      'The Belvédère opened in September 2018 on the old dry docks of Eilandje. The standard “before” window caught the works in progress.',
    reading:
      'With a baseline taken before the works, the defensible effect is half the headline and still three times the threshold. That baseline rests on the two usable scenes of summer 2016.',
    imageNote: 'The “before” picture is the standard 2017–19 window, when the works were already under way. The number above uses the 2016 baseline instead.',
  },
  'spoor-noord': {
    city: 'Antwerp',
    place: 'Park Spoor Noord',
    title: ['A rail yard became ', 'nineteen hectares', ' of grass.'],
    story:
      'The NMBS marshalling yard opened as a park in 2008–2009. Sentinel-2 did not exist yet, so the audit uses Landsat, which reaches back to 2006.',
    reading:
      'The one summer in the noise is the 2018 drought, when a grass park loses its lead over everything around it. There is no second instrument for these years.',
  },
}

// Marks on the rings (viz/Rings.jsx) — only what a document or a second instrument says.
// Spoor Noord 2017 is simply missing from the series; the cause is not stated, so neither is it here.
export const RING_NOTES = {
  ninove: { 2022: { kind: 'note', text: 'dry summer, still above noise' } },
  droogdokkenpark: { 2025: { kind: 'scar', text: 'works on the docks: built-up +0.107' } },
  'spoor-noord': {
    2017: { kind: 'absent', text: 'no summer in the series' },
    2018: { kind: 'note', text: 'drought: within noise' },
  },
}

export const REFUSALS = [
  {
    key: 'cooling',
    icon: 'thermometer',
    head: 'Cooling',
    text: 'Our noise floor for surface temperature is larger than what a new park realistically does to it. So nowhere on this site does a park “cool the street by a degree”.',
  },
  {
    key: 'refused',
    icon: 'compare',
    head: 'Places with no fair comparison',
    text: 'A park at the edge of the scale has nothing similar to be compared with. When the matched places differ too much beforehand, Frondia refuses the verdict.',
  },
  {
    key: 'monitoring',
    icon: 'calendar',
    head: 'One-season alarms',
    text: 'A single brown summer is weather more often than loss. A drop is published only when a second, independent instrument sees the canopy go and no construction appear.',
  },
  {
    key: 'restorations',
    icon: 'tree',
    head: 'Restorations',
    text: 'Fixing paths, ponds and fountains in a park that is already green does not show from space. Older park projects, seven large restorations among them, each measured with its own window and threshold, sit within the noise.',
  },
  {
    key: 'cause',
    icon: 'document',
    head: 'Causes without documents',
    text: 'The strongest greening in Brussels, Zavelenberg, is a nature reserve where grazing stopped after the farmer died. Without a document, no cause is named.',
  },
]

// Who the page is for: the main segment first (landing brief, docs/design/landing/landing-brief.md)
export const AUDIENCES = [
  {
    key: 'regions',
    who: 'Regions reporting Article 8',
    text: 'Whether green space and canopy grew or shrank after the 2024 baseline, sector by sector, with the noise measured and every loss named. Bruxelles Environnement in Brussels; in Flanders, ANB and INBO, which runs the monitoring; in Wallonia, the SPW.',
    cta: 'See the cities in the atlas',
  },
  {
    key: 'municipalities',
    who: 'Municipalities that built something',
    text: 'Which sectors lack services, shops within reach, shade or a bench; where the next objects should go; and whether a new park changed the ground, summer after summer.',
    cta: 'Open an audit',
  },
  {
    key: 'funders',
    who: 'Funders',
    text: 'A check written into the grant before the works start. The outline, the baseline and the comparison places are fixed with a date, so nobody can draw the result to fit afterwards.',
    cta: 'How the outline is fixed',
  },
]

// Objections from the brief. Numbers come in through `n`, built from /data/*.json.
export const FAQ = [
  {
    id: 'scope',
    q: 'Is Frondia only about greenery?',
    a: () => 'No. The atlas also shows what each sector lacks, from everyday services and shops within reach to summer heat and the 3-30-300 rule, and where the next of fourteen kinds of public object should go. Only greenness is measured as change against the city’s own noise; the rest are states and recommendations, and the atlas labels them that way.',
  },
  {
    id: 'trees',
    q: 'Does it measure trees, or just “green”?',
    a: (n) => `The main instrument is greenness: the vegetation index from Sentinel-2. A second one, Dynamic World, tells trees, grass and sealed ground apart, and a loss of canopy is published only when both agree. By rank, Frondia’s canopy and the official and independent canopy layers agree at ${n.canopyR}.`,
  },
  {
    id: 'outline',
    q: 'Who draws the outline of a project? Could it be drawn to fit the result?',
    a: () => 'The outline is fixed before any number is computed: a named park polygon from OpenStreetMap, or the client’s own drawing. For works not yet started, the outline, the baseline and the twelve comparison places are registered with a date and a hash. Six Brussels projects are registered that way today.',
  },
  {
    id: 'wrong',
    q: 'How often is the detector wrong?',
    a: (n) => (n.check ? `Checked against an independent map made from aerial photographs, Groenkaart Vlaanderen 2018 against 2021 and 2024, in Antwerp and Ghent, with the same matched places and its own noise threshold. Where the satellite says a sector’s canopy stayed within noise, the aerial map agrees in ${n.check.spec}. Where it says the canopy changed beyond noise, the map agrees in only ${n.check.agree}. So a change beyond noise is a candidate, not a proof: a loss is named only when a second instrument and documents agree.` : ''),
  },
  {
    id: 'official',
    q: 'How is this different from the official Copernicus layers?',
    a: () => 'Those layers say how much green and canopy a city has. Frondia says whether that changed beyond the city’s own noise, where, and, with documents, why. It sits on top of them.',
  },
  {
    id: 'small',
    q: 'What about street trees and small squares?',
    a: () => 'Below about a hectare the signal drowns: four planted streets inside a 19-hectare sector add roughly half a hectare of canopy, diluted forty times. For small things Frondia checks something else: whether the object appeared at points named in advance, with points that were not named as the comparison.',
  },
  {
    id: 'cities',
    q: 'Which cities, and can it move to another one?',
    a: (n) => `${n.cities}. The threshold belongs to the pair of city and instrument: ${n.wider}. A new city gets its own calibration.`,
  },
  {
    id: 'current',
    q: 'How current is it?',
    a: (n) => `Summer composites from 2017 to 2026. Monitoring runs every season, ${n.seasons} so far in every city, and each season gets its own threshold.`,
  },
]

/* ── the unified atlas: three questions (docs/07-unified-frondia.md) ─────────────────────────── */
export const QUESTIONS = {
  need: { short: 'Missing', long: 'What’s missing' },
  place: { short: 'Place', long: 'What to place' },
  change: { short: 'Changed', long: 'What changed' },
}

export const NEED = {
  services: {
    chip: 'Services', title: 'Everyday services',
    lede: 'How well a sector serves daily life, from a school and a GP to a park and a tram stop, weighted for one of three lives.',
    legend: ['Best-served fifth', 'Second fifth', 'Middle fifth', 'Fourth fifth', 'Worst-served fifth'],
    source: 'Neighbourhood Fit Score: 14 services within walking distance, from OpenStreetMap and Statbel sectors. The fifths are of the sectors where 200 people or more live.',
    limit: 'Built from OpenStreetMap: where the map is thin, the score is too.',
  },
  shops: {
    chip: 'Shops', title: 'Shops within reach',
    lede: 'How far the nearest bakery, café or confectionery is from each sector, in a straight line.',
    legend: ['300 to 600 m', '600 m to 1 km', '1 to 1.5 km', '1.5 to 2.5 km', 'Over 2.5 km'],
    source: 'SpotFinder: the nearest shop of each kind, from OpenStreetMap.',
    limit: 'A straight line, not a walk; closer than 300 m is left blank.',
  },
  heat: {
    chip: 'Heat', title: 'Summer heat',
    // the correlation is the city's own (site_data.heat_canopy_r): Brussels −0.89, Antwerp −0.66
    lede: (city) => `How much hotter the ground gets in summer than the city’s median sector. Canopy is the strongest shield: in ${city.name} the two move together at r = ${String(city.heat_canopy_r).replace('-', '−')}.`,
    legend: ['Up to 1 °C above', '1 to 2 °C', '2 to 3 °C', '3 to 4 °C', 'Over 4 °C above'],
    source: 'Landsat 8 and 9 surface temperature, the median of summers 2022 to 2025.',
    limit: 'A state, not an effect: the method cannot measure a park’s cooling (noise floor 1.32 °C).',
  },
  r3: {
    chip: '3-30-300', title: 'The 3-30-300 rule',
    lede: 'Two of its three parts can be measured from above: 30% tree canopy in the neighbourhood, and a park of a hectare or more within 300 m.',
    legend: [null, 'Meets one of the two', null, 'Meets neither', null],
    source: 'Canopy from ESA WorldCover (10 m); parks of 1 ha or more from OpenStreetMap.',
    limit: 'The third part, three trees in view from every window, is not measured and not guessed.',
  },
}
export const NOT_MEASURED = (city) => `Not measured in ${city} yet.`

export const SCENARIO_LABEL = { family: 'Family', remote: 'Remote work', senior: 'Seniors' }
export const SERVICE_LABEL = {
  cafe: 'café', childcare: 'childcare', convenience: 'corner shop', gp: 'GP', hospital: 'hospital',
  library: 'library', park: 'park', pharmacy: 'pharmacy', playground: 'playground', restaurant: 'restaurant',
  school: 'school', sport: 'sports ground', supermarket: 'supermarket', transit: 'public transport',
}
export const SHOP_LABEL = { bakery: 'Bakery', cafe: 'Café', confectionery: 'Confectionery' }

// "What if N more?" (phase 2, docs/07-unified-frondia.md): the planner's coverage after each rank
export const MORE = {
  title: (k) => `What if ${k} more?`,
  slider: 'How many to place, in rank order',
  read: 'of demand within 500 m',
  today: 'today', all: (n) => `all ${n}`,
  named: '10 named',
  who: (k, poor, cut) => `Of these ${k}, ${poor} stand where the poorest third of residents live (sector median income below ${cut}).`,
  whoOne: (poor, cut) => `It ${poor ? 'stands' : 'does not stand'} where the poorest third of residents live (sector median income below ${cut}).`,
  zero: 'Nothing placed yet: move the slider to place the next objects in rank order.',
}

// Communes (phase 2, docs/07-unified-frondia.md): Article 8(1) by commune, measured with the
// Commission's method, and the projects registered before their works
export const COMMUNES = {
  chip: 'Communes',
  title: (city) => `Communes the law counts in ${city}`,
  window: 'Article 8(1) · 2021 data',
  lede: 'A commune is left out of the national count of urban green when its urban centres and clusters are more than 45% green and more than 10% tree canopy. Measured here with the Commission’s own method on open data.',
  exempt: 'exempt', counted: 'counted',
  region: (n, g) => `All ${n} as one: ${g} green in urban centres and clusters, so the region as a whole is counted.`,
  leaveOut: (n, area, res, woody, rest, restGreen) => `Leaving out all ${n} would take ${area} of the region’s area and ${res} of its residents out of the count, but ${woody} of its woody vegetation. The duty of no net loss would rest on ${rest} dense communes, ${restGreen} green on average.`,
  scale: { lo: '0', mark: '45%, exempt above', hi: '100%' },
  listTitle: 'Green in urban centres and clusters',
  canopyToo: (c) => `canopy ${c}, under 10% as well`,
  untested: 'The other communes on this map lie outside Antwerp and were not tested.',
  // a verdict one of the test's other readings of Article 3(20) turns over:
  // Ghent 44.4%, with farmland 49.0%; Liège 46.0%, without water 41.4%
  unstable: (c, pts, g7, gnw) => (!c.exempt && c.green7 > 0.45
    ? `${c.name} is ${pts} points under the line. Counted with farmland as green, one of the other readings of Article 3(20) the test runs, it is ${g7}, and ${c.name} would be exempt: the verdict turns on that reading.`
    : c.exempt && c.green_nw <= 0.45
      ? `${c.name} is ${pts} points over the line. Without water counted as green, one of the other readings of Article 3(20) the test runs, it is ${gnw}, and ${c.name} would not be exempt: the verdict turns on that reading.`
      : `${c.name}’s verdict changes under the test’s other readings of Article 3(20).`),
  legend: ['Under 15%', '15 to 30%', '30 to 45%', '45 to 60%', '60% and more'],
  legendExempt: 'Exempt: outlined in ink',
  legendUntested: 'Outside the tested commune',
  legendRegistered: 'Registered before the works: outline, no fill',
  source: 'The EEA and JRC method (NRR_Art8) repeated on open data: LAU 2024, degree of urbanisation 2024, urban centres and clusters 2021 (1 km² grid), CLCplus Backbone 2021 for green, the Woody Vegetation Layer 2021 for canopy. The 2021 layers are allowed for draft plans only.',
}
// The whole city before and after (phase 2, docs/07-unified-frondia.md): a swipe between two
// true-colour summers, the measured verdicts drawn on top as outlines
export const PHOTOS = {
  chip: 'Photos',
  window: (a, b) => `Summers ${a} and ${b} · Sentinel-2`,
  tag: (y) => `Summer ${y}`,
  handle: (a, b) => `Split between summer ${a} and summer ${b}`,
  valueText: (p, a, b) => `${p}% of the map shows ${a}, the rest ${b}`,
  lede: (a, b) => `Drag the line: summer ${a} on its left, summer ${b} on its right.`,
  legend: { up: 'Greener beyond noise', down: 'Lost beyond noise', rawUp: 'Looks greener', rawDown: 'Looks browner' },
  note: (w) => `The photographs are for the eye, and no number is taken from them: two summers also differ in light, haze and harvest. The outlines are the measurement, made on summers ${w}.`,
}
// Sealed ground (phase 2c, docs/07-unified-frondia.md): Dynamic World's built-up class against the same
// twelve matched places as greenness, with its own threshold from the same run. France's Mon Diagnostic
// Artificialisation shows artificialised and renaturalised ground between two dates; this adds the
// noise threshold. A class probability, not a share of the ground: the words never say hectares.
export const BUILT = {
  measure: 'Measure',
  options: [['green', 'Greenness'], ['built', 'Built-up ground']],
  lede: 'Built-up ground is what Dynamic World reads as buildings, roads and paving, set against the same twelve matched places as greenness.',
  counts: { up: 'sealed beyond noise', down: 'unsealed beyond noise' },
  legend: { up: 'Sealed: threshold, 2×, 3×', down: 'Unsealed: threshold, 2×, 3×', noise: 'Within noise — the field shows through' },
  threshold: (t, n, city) => `Threshold ±${t} — this run’s own noise, measured on ${n} sectors of ${city} playing “intervention” once each.`,
  limit: 'A class probability, not a share of the ground: the map shows where sealing moved beyond noise, not how many hectares. Less built-up is not always a park: demolition down to bare ground reads the same.',
  rawOff: 'Shown against matched places only: this run kept each sector’s effect, not its own before and after.',
  top: 'Largest shifts beyond noise',
  passport: 'Built-up ground against matched places',
  word: { up: 'sealed', down: 'unsealed', noise: 'within noise', refused: 'refused' },
}

// The balance after the 2024 base, in hectares (phase 2c, item 2; scripts/gee/art8_balance.py). France's Mon
// Diagnostic Artificialisation shows each commune three bars: artificialised, renaturalised, net. Here the same
// for green, canopy and built-up, counted only where a sector moved beyond noise against its matched places.
// the detector against Groenkaart Vlaanderen (phase 2c, item 5), under the greenness view of a Flemish city
export const CHECK = {
  line: (c) => `Checked against an independent aerial map (Groenkaart Vlaanderen, 2018 against 2021–24): where this map says a sector stayed within noise, the aerial map agrees in ${c.specificity.k} of ${c.specificity.n}; where it says a sector changed beyond noise, in ${c.agreement_when_ours_changed.k} of ${c.agreement_when_ours_changed.n}. A change beyond noise is a candidate, not a proof.`,
}

export const BALANCE = {
  title: (base) => `Since the ${base} base`,
  lede: (base, s) => `Summer ${base} against summer ${s}, in hectares as Dynamic World classifies the ground; urban green as the Regulation reads it, trees, grass, shrub and water, not farmland. A sector counts only where it moved beyond noise against its twelve matched places.`,
  rows: { green: 'Urban green', trees: 'Tree canopy', built: 'Built-up' },
  net: (v) => `${v} net`,
  split: (lost, gained) => `lost ${lost} · gained ${gained}`,
  raw: (city, s, g, b) => `Without subtracting matched places, ${city} would show ${g} of green and ${b} built-up between summer 2024 and summer ${s}. The classes shift from one summer to the next; the matched places take that shift out.`,
  preliminary: (y) => `Summer ${y} has fewer than eight usable scenes: its figures are preliminary.`,
  limit: 'Hectares as a satellite classifier reads them, not the official CLCplus and Woody Vegetation layers, which do not exist yet for 2025 and 2026. One summer against another is noisier than a four-year window. A park that loses trees can read as more built-up, when a mixed pixel changes class.',
}

// The commune page (phase 2c, item 3; data: scripts/site/site_data.py → communes.json). What the law counts in one
// commune and what changed there. The entry is "enter your commune" as France's Mon Diagnostic Artificialisation
// searches a territory; the key figures as Kermap's Nos Villes Vertes sets them, each against a reference.
// no two-letter words: the non-breaking rule (lib/typography.js) would chain "+22.3 pt on the region" into one
// unbreakable run that a 320-px phone cannot hold
const POINTS = (v) => `${Math.abs(v).toFixed(1)} points ${v >= 0 ? 'above' : 'below'}`
export const COMMUNE = {
  find: { label: 'Find a commune', placeholder: 'Commune name or NIS code', none: 'No commune of the five cities matches.',
    hint: (n) => `${n} communes in Brussels, Antwerp, Ghent, Liège and Charleroi` },
  index: { kicker: 'Communes', title: 'What the law counts in your commune', lede: 'Article 8 of the Nature Restoration Regulation counts urban green and tree canopy commune by commune. Find yours: its test, its zero measurement in hectares, and what changed since the 2024 base.' },
  kicker: (region, code) => `Commune · ${region} · NIS ${code}`,
  title: (name, exempt) => `${name}: ${exempt ? 'left out of Article 8’s count' : 'counted in Article 8’s total'}`,
  standfirst: 'What the Nature Restoration Regulation counts in this commune, what changed since its 2024 base, and where to look in the atlas.',
  meta: (c) => [['Residents', c.pop.toLocaleString('en-GB')], ['Area', `${c.area_km2.toFixed(1)}\u00A0km²`], ['Sectors measured', `${c.measured} of ${c.sectors}`], ['LAU', c.lau_id]],
  inAtlas: 'Open in the atlas', data: 'Data and the Reportnet file',
  law: {
    eyebrow: 'Article 8(1)',
    title: (a) => (a.exempt ? 'Over both lines: left out of the count'
      : a.green <= 0.45 && a.canopy <= 0.1 ? 'Under both lines: counted'
        : a.green <= 0.45 ? `${(100 * (0.45 - a.green)).toFixed(1)} points under the green line: counted` : 'Under the canopy line: counted'),
    green: 'Green in urban centres and clusters', canopy: 'Tree canopy there', perResident: 'Tree canopy per resident, whole commune', verdict: 'Verdict',
    exempt: 'Exempt', counted: 'Counted', vsLine: (v, line) => `${POINTS(100 * (v - line))} the ${Math.round(100 * line)}% line`,
    vsRegion: (v, r) => `${POINTS(100 * (v - r))} the region`, m2: 'm²',
    holds: 'holds under every reading', turns: 'turns on a reading',
    reading: (c, a) => `Its urban centres and clusters are ${(100 * a.green).toFixed(1)}% green and ${(100 * a.canopy).toFixed(1)}% tree canopy. A commune is left out of the national count only above 45% and 10%; ${c.name} ${a.exempt ? 'is' : 'is not'}. ${a.stable ? 'The verdict holds under every reading of Article 3(20) the test runs.' : 'One of the other readings of Article 3(20) turns the verdict: see the table.'}`,
    region: (r) => `All ${r.n} communes together: ${(100 * r.green).toFixed(1)}% green and ${(100 * r.canopy).toFixed(1)}% canopy, so the region as a whole is ${r.exempt ? 'left out' : 'counted'}.`,
    readings: { official: 'Official reading', with_arable: 'Arable land counted as green', without_water: 'Water not counted as green', statbel_sectors: 'Commune built from Statbel sectors' },
    cols: ['Reading', 'Green', 'Canopy', 'Verdict'], notComputed: 'not computed',
  },
  base: {
    eyebrow: 'The zero measurement',
    title: 'In hectares, on the latest open data (2021)',
    cols: ['Urban ecosystem', 'Area', 'Green', 'Canopy'], ucuc: 'Urban centres and clusters', lau: 'The whole commune',
    note: 'The form of the Dutch national zero measurement (PBL, 25 August 2026), with both boundaries the Commission leaves to a country. The Woody Vegetation Layer 2021 is allowed for draft plans only; the 2024 layer is shared with national authorities, not published.',
  },
  balance: {
    eyebrow: (b) => `Since the ${b} base`,
    title: (k, v, s) => `${k} ${v} beyond noise by summer ${s}`,
    rows: { green: 'Urban green', trees: 'Tree canopy', built: 'Built-up' },
    cols: (s) => [`Summer ${s}`, 'Lost', 'Gained', 'Net'],
    note: 'Hectares as Dynamic World classifies the ground, summed over this commune’s sectors that moved beyond noise against their twelve matched places. Not the official layers, which do not exist yet for 2025 and 2026.',
    events: 'What the season bulletins name here',
    none: (a, b) => `No sector here was named a canopy loss or a building site in ${a} or ${b}.`,
    kinds: { 'canopy loss': 'canopy loss, two instruments agree', construction: 'building site' },
  },
  change: {
    eyebrow: (w) => `Summers ${w}`,
    title: (c, m) => `${c.up} ${c.up === 1 ? 'sector' : 'sectors'} greener and ${c.down} lost beyond noise, of ${m} measured`,
    green: 'Greenness against matched places', built: 'Built-up ground against matched places',
    words: { up: 'greener', down: 'lost', sealed: 'sealed', unsealed: 'unsealed' },
    noneGreen: 'No sector here moved beyond noise.', noneBuilt: 'No sector here was sealed or unsealed beyond noise.',
    counts: (b) => `Built-up ground: ${b.up} sealed and ${b.down} unsealed beyond noise.`,
  },
  record: {
    eyebrow: 'On the record', title: 'Registered, audited and the dossier',
    registered: 'Registered before the works', cases: 'Audits', dossier: 'The dossier the open rule picks',
    refused: 'no comparable places: refused before the works',
  },
  trees: {
    eyebrow: 'The city’s tree register',
    title: (n) => `${n} trees the city manages`,
    snapshot: (d) => `A snapshot of the register was taken on ${d}. From the next one, the trees that leave it (felled, dead or re-surveyed; the register does not say which) will be counted by sector.`,
    plantedTitle: 'Planted, by year', total: (n, a, b) => `${n} trees planted from ${a} to ${b}, by the register’s own planting year.`,
    whereTitle: 'Where the plantings went, 2020–2025',
    cols: ['Third of lived-in sectors', 'Plantings', 'Residents', 'Per 1,000 residents, this third vs the rest', 'Per 10 ha, this third vs the rest'],
    rows: { least_canopy: 'Least canopy', poorest: 'Poorest', hottest: 'Hottest' },
    vs: (a, b) => `${a.toFixed(1)} vs ${b.toFixed(1)}`,
    reading: (w) => `Per resident, fewer trees went to the third with the least canopy: ${w.least_canopy.per_1000_in_third.toFixed(1)} per 1,000 residents against ${w.least_canopy.per_1000_elsewhere.toFixed(1)} in the rest. Per hectare, more did: ${w.least_canopy.per_10ha_in_third.toFixed(1)} per 10 ha against ${w.least_canopy.per_10ha_elsewhere.toFixed(1)}. Those sectors are dense, so both readings are true; neither says whether the trees were needed more there.`,
    source: (l) => `The city’s own register, ${l}. Only trees the city manages; gardens and private land are not in it.`,
  },
  limits: ['Article 8(1) is measured with the Commission’s method on open 2021 data; the 2024 Woody Vegetation Layer is not public.',
    'Matching CLCplus classes to Article 3(20) is our reading, which is why the table re-runs the verdict under the others.',
    'Hectares after the base are a satellite classifier’s: a park that loses trees can read as more built-up.',
    'A number beyond noise says that something changed, not why. The cause comes from documents.'],
  missing: 'No commune of the five cities has this code.',
  loading: 'Loading the commune…',
}

// The sector dossier (phase 2b, docs/07-unified-frondia.md): the Russian dossier
// (scripts/report/dossier_html.py) in English. The numbers come from the site's data; the page puts
// them into these words, and every headline is computed, never written: "half the canopy" at a ratio
// of 0.6 would be the kind of overstatement the method exists to prevent.
export const DOSSIER = {
  kicker: (commune, id) => `Dossier · ${commune} · sector ${id}`,
  title: (name, gap, pop) => `${name}: ${gap}, ${pop} residents`,
  gap: (share) => (share <= 0.55 ? 'half the city’s median canopy'
    : share < 0.95 ? `canopy ${Math.round(100 * (1 - share))}% below the city’s median`
      : share <= 1.05 ? 'canopy at the city’s median'
        : `canopy ${Math.round(100 * (share - 1))}% above the city’s median`),
  standfirst: 'Why money for greening should come to this sector, and how the result will be checked with the same method that measured its state.',
  // the facts of the document as label and value (Dovetail's metadata rows), not a line of dots
  meta: (last) => [['Unit', 'Statbel sector'], ['Baseline', 'summer 2024'], ['Imagery', 'Sentinel-2, Dynamic World'], ['Measured to', `summer ${last}`]],
  print: 'Print or save as PDF',
  inAtlas: 'Open in the atlas',
  online: 'This page',
  loading: 'Loading the dossier…',
  missing: 'This sector is not in the measured part of the city, so there is no dossier for it. Pick another one in the atlas.',
  // the open rule asks for a commune the law counts; in an exempt city it finds none, and says so
  noPick: (city, green) => `The open rule picks no sector in ${city}. It asks for a commune the law counts, and ${city} is exempt under Article 8(1): ${green} green in its urban centres and clusters. Every sector still has its dossier; pick one in the atlas.`,
  picked: (rule, n) => `How the sector was picked. By a rule, not by hand: ${rule}. ${n} sectors fit; this dossier is about the first.`,
  rule: (minHeat, minRes) => `the lowest third by income, the lowest third by canopy, a summer surface at least ${minHeat} °C hotter than the city’s median, a commune that does not pass the Article 8(1) exemption, at least ${minRes} residents; among those, the sector with the most children under 15`,

  passport: { eyebrow: 'Passport', title: 'Who lives here and what is around',
    residents: 'residents', children: 'children under 15', seniors: 'aged 65 and over', income: 'median taxable income, Statbel 2023',
    canopy: 'tree canopy, class probability', built: 'built-up and paved, class probability', area: 'hectares' },
  standing: (tp, np) => `By canopy the sector stands in the lowest ${tp}% of the city, by greenness in the lowest ${np}%.`,
  income: {
    both: (cut) => `Income is below the lower third’s cut (€${cut}): two shortages meet here, little green and little money.`,
    one: (inc, cut) => `The sector’s median income is €${inc}, against the lower third’s cut of €${cut}.`,
    none: 'There is no income figure for this sector.',
  },

  scale: { eyebrow: 'State', title: 'Where the sector stands on the city’s scale', median: 'city median',
    rows: { t24: 'Tree canopy', n24: 'Greenness', b24: 'Built-up' },
    // the reading in words under each bar (Klima: "21% below average")
    reading: (share) => (Math.abs(share - 1) < 0.05 ? 'at the city’s median'
      : `${Math.round(100 * Math.abs(share - 1))}% ${share < 1 ? 'below' : 'above'} the city’s median`),
    note: 'The tick is the city’s median, the bar the sector. Class values are probabilities, not shares of ground: compare them between sectors, but do not read them as percentages of area.' },

  trend: { eyebrow: 'Trend', title: 'It will not improve by itself',
    body: (w, ne, nt, te, tt) => `Against twelve matched control sectors, from summers ${w}, greenness changed by ${ne} against a significance threshold of ${nt}, and canopy by ${te} against ${tt}.`,
    means: { noise: 'The change did not cross the threshold: the sector is standing still.',
      down: 'Greenness fell significantly against comparable sectors.',
      up: 'Greenness rose significantly against comparable sectors.',
      refused: 'No comparable control sectors exist for this one, so no verdict is given.' },
    background: (shift, kRaw, n, share, kEff) => `The comparison is with a control, not with the sector’s own past. Without subtracting matched places, the city-wide shift of ${shift} makes ${kRaw} of ${n} sectors (${share}) look “significantly greener”, against ${kEff} once they are subtracted.`,
    after: (span, items) => `After the baseline, in seasons ${span}: ${items}.`,
    afterNone: (span) => `After the baseline, in seasons ${span}, nothing in the sector crossed the threshold.`,
    kinds: { construction: 'construction, by the second instrument', confirmed: 'canopy loss, both instruments agree',
      unconfirmed: 'greenness loss the second instrument did not confirm', gained: 'greenness gained beyond the threshold' },
    notProof: ['What this does not prove.', 'No growth is not proof that the city did nothing: works the method cannot see may have gone on here. Restoring existing green does not show in these numbers by construction, and scattered street planting drowns in the sector’s area.'],
    law: {
      counted: (c, g) => ['The law counts this sector.', `${c} does not pass the Article 8(1) exemption: ${g} green in its urban centres and clusters against a 45% threshold (the Commission’s method, CLCplus 2021). Whatever is planted or lost here enters the national count of no net loss.`],
      exempt: (c, g) => ['The commune may fall outside the law.', `${c} passes the Article 8(1) exemption: ${g} green in its urban centres and clusters against a 45% threshold. If the state leaves it out, changes here do not enter the national count, and the case rests on fairness and heat rather than on the law.`],
    } },

  fair: { eyebrow: 'Fairness',
    title: (ratio) => (ratio < 0.4 ? 'The poorest third of the city lives with less than half the canopy'
      : ratio <= 0.6 ? 'The poorest third of the city lives with half the canopy'
        : ratio < 0.95 ? `The poorest third has ${Math.round(100 * (1 - ratio))}% less canopy than the richest`
          : 'Canopy is shared almost evenly between income groups'),
    head: ['Group', 'Median income', 'Canopy 2024', 'Greenness 2024'],
    rows: ['Lowest third by income', 'Highest third'],
    asOf: 'Levels of summer 2024, weighted by population; income thirds by sector, Statbel 2023.',
    note: (ratio) => `The lowest third’s canopy is ${ratio} of the highest third’s. Regulation (EU) 2024/1991 requires no net loss of green and canopy by 2030 but says nothing about how they are shared between neighbourhoods; UN indicator 11.7 and the Tree Equity Score do.`,
    group: { below: 'The sector lies below the average even for its own group.',
      level: 'For its group the sector is no worse than average: the shortage here is shared by the whole lowest third.',
      out: 'The sector is not in the lowest income third.' },
    kids: (k, kp, o, op, o80, third, inThird, hardest) => ['Who lacks shade here.', `${k} children under 15 live in the sector (${kp} of its residents) and ${o} people aged 65 and over (${op}), ${o80} of them over 80: the groups heat endangers most. Across the city, ${third} of all children live in the third of sectors with the least canopy${hardest ? ', so the shortage of shade is not shared equally, and it falls hardest on them' : ', close to their share of the city'}.${inThird ? ' This sector is in that third.' : ''}`],
    rule: {
      lead: (both) => (both ? 'The rule and the heat meet here.' : 'The 3-30-300 rule and heat.'),
      verdict: (fails) => (fails.length === 2 ? `neither measurable part of the rule is met: ${fails.join('; ')}`
        : fails.length === 1 ? `one part of the rule is not met: ${fails[0]}` : 'both measurable parts of the rule are met'),
      canopyFail: (c) => `canopy covers ${c} of the sector against 30%`,
      parkFail: (p) => `${p} of its area lies within 300 m of a park, against half`,
      strength: (r) => (r <= -0.8 ? 'almost deterministic' : r <= -0.5 ? 'strong' : 'noticeable'),
      body: (verdict, lst, exc, above, strength, r, both) => `By the 3-30-300 rule of urban forestry, ${verdict}. The summer surface here is ${lst}\u00A0°C, ${exc}\u00A0°C ${above ? 'above' : 'below'} the city’s median. The less canopy, the hotter: across the city the link is ${strength} (r = ${r})${both ? ', and this sector sits at the bad end of both scales at once' : ''}. Temperature here describes a state: the project does not measure cooling from an intervention, because the significance threshold for it is larger than a realistic park effect.`,
    } },

  place: { eyebrow: 'What to place here', title: 'Where City Planner puts the first objects',
    lede: (n, date) => `${n} of the planner’s ranked points fall in this sector. The first ten of each kind were named on ${date}, the next ten are their comparison: whether an object appears will be checked against the map’s history, at the same address this dossier names.`,
    none: 'None of City Planner’s first twenty candidates of any kind falls in this sector.',
    role: { named: 'named', control: 'comparison' } },

  cases: { eyebrow: 'What an intervention can deliver', title: 'Three measured cases instead of promises',
    head: ['Intervention', 'Effect', 'Threshold', 'Times', 'Reading'],
    what: { ninove: 'wasteland by the canal → park, 2.2 ha', droogdokkenpark: 'old docks → a quayside park', 'spoor-noord': 'rail yard → park, 19.5 ha' },
    series: (k, n) => `Above noise in ${k} of ${n} summers after it opened.`,
    note: 'This is not a forecast for this sector but the range measured on comparable works: a change of cover over most of a site gives an effect three or more times the threshold, and it holds for years. The size depends on what was there before: wasteland gives more than a quayside that was already green.',
    left: ['What this table leaves out on purpose.', 'Cooling: the significance threshold for surface temperature came out at 1.32\u00A0°C, more than the realistic effect of an urban park, so there are no claims about degrees here. The cost of an effect: prices compare only within one type of work, and the budgets of comparable projects are published only in part.'] },

  commitment: { eyebrow: 'Commitment', title: 'What exactly we will check, and when we will refuse',
    items: (r) => [
      ['The footprint of the works is fixed before they start.', 'The polygon, its hash and the date enter the register before the first day of works. Drawing it afterwards around whatever turned green becomes impossible.'],
      ['The control is named at the same time.', `${r.controls} sectors that resemble the site in its state before the works, none closer than ${(r.exclusion_m / 1000).toLocaleString('en-GB')} km. The list is published before the measurement; if no comparable control exists, that is recorded as a refusal, not adjusted.`],
      ['The threshold comes from the city’s calibration,', 'not chosen for the result: the null distribution is computed with the same matching and the same images as the audit itself, the way the trend’s threshold above was.'],
      ['The comparison window is built from the completion date:', 'a baseline before the works begin, the assessment two years after they end. If the works fall inside a window, the audit declines to compute.'],
      ['The verdict takes two instruments.', 'Greenness and land-cover classes from the same images: the first says that something changed, the second what exactly, down to “unsealed but not planted”.'],
      ['A refusal is a published outcome.', `Fewer than ${r.min_scenes} images in a window, a gap to the control above ${r.max_gap}, works outside the window: no verdict is given, and that is printed alongside the results.`],
    ] },

  limits: { eyebrow: 'Limits', title: 'What the method will not measure, even when everything is done right',
    items: [
      'Cooling of air or surface: the channel’s noise is larger than a realistic effect.',
      'Restoration of existing green: repairing paths and ponds does not change vegetation.',
      'Scattered street planting measured at the level of a sector: half a hectare of new canopy on nineteen hectares is lost.',
      'The cause of a change: the satellite names the place, documents name the cause. Without a document a change is published as a measurement, not as anyone’s credit.',
      'Young plantings in their first years: saplings on a meadow read less green than the grass they replaced, and honest greening can measure as a loss.',
    ] },

  // the colophon as rows, a label on the left (OpenAI's research footer)
  colophon: [
    ['Sources', 'The city package’s Article 8 layer (2024 levels and the trend against control), the city manifest (thresholds and where they come from), the audit cases, the register of named points, Statbel (sectors, population, income, the 2021 census). Imagery: Copernicus Sentinel-2 with the Cloud Score+ mask, Google Dynamic World V1.'],
    ['Evidence', 'Every number leads to a layer of the city package, and the limits are printed next to the numbers, not in a footnote. The evidence does not change with the wording: numbers, thresholds and controls are recomputed from those files.'],
  ],
}

// The data download (phase 2b): every layer behind the atlas as a CSV, with its manifest
export const DATA = {
  kicker: 'Data',
  title: 'Every number, and how it was made',
  lede: 'Each layer behind the atlas as a CSV, and the Article 8 file as the GeoPackage the Commission asks for, with what it measures, how, from what source and with what threshold, so any number on the site can be recomputed from the files alone.',
  meta: (n, name, formats) => [['City', name], ['Layers', String(n)], ['Format', formats], ['Join key', 'Statbel sector id; LAU code for the law']],
  manifest: 'Manifest (JSON)',
  download: (fmt) => `Download ${fmt}`,
  details: 'Method, source and columns',
  file: (fmt, n, kb) => `${fmt} · ${n} ${fmt === 'GeoPackage' ? (n === '1' ? 'polygon' : 'polygons') : (n === '1' ? 'row' : 'rows')} · ${kb} KB`,
  computed: (d) => `computed ${d}`,
  rows: { method: 'Method', source: 'Source', threshold: 'Threshold', limits: 'Limits', licence: 'Licence', credit: 'Credit' },
  columns: ['Column', 'What it holds'],
  groups: {
    'What changed': 'The trend against matched places, and each season since the 2024 baseline.',
    'The law': 'The Commission’s own test for leaving a commune out of Article 8, the zero measurement in hectares, and the file a country uploads.',
    'What’s missing': 'States, not changes: what a sector lacks today.',
    'What to place': 'City Planner’s ranked places and the coverage they buy.',
    'Cross-checks': 'Independent instruments our tree class is checked against.',
    Sectors: 'The unit every file is joined on.',
  },
  colophon: [
    ['Licences', 'Frondia’s layers are offered under CC BY 4.0, their sources credited in each layer. Layers built on OpenStreetMap are derived databases and stay under the ODbL 1.0.'],
    ['Cite as', 'Frondia, “<layer title>”, <city>, frondia.ontwrpn.com/data, with the date the layer was computed.'],
    ['Recompute', 'The manifest lists every column. Sector boundaries are Statbel’s open data: join on id.'],
  ],
}

// The register of interventions read by a language model (phase 2b, docs/07-unified-frondia.md). Numbers
// come from register.json (scripts/site/register.py); the page puts the readings together from these words.
// The check is worded by who gave the reference labels (`eval.kind`): a person, "by hand", or, while no
// person who reads French planning texts is at hand, a second model, whose labels are never presented as
// a person's.
const LABEL_SHORT = { yes: 'Commits', weak: 'An aim', no: 'No measure' }
const READ_ALL = (total) => `Brussels has run ${total} neighbourhood contracts since 1994. A language model read each contract’s page and listed every greening measure in the contract’s own words.`
const DRAWN = (d) => `${d.testset.n} contracts drawn by the seed “${d.testset.seed}” from the ${d.testset.pool} whose page has at least 600 characters of its own, before any of them was read.`
const BARS = 'Each bar is the Wilson 95% interval, and its tick the estimate.'
const DATES = (e) => (e.labelled_from === e.labelled_to ? e.labelled_from : `${e.labelled_from} to ${e.labelled_to}`)
const REF = {
  person: {
    label: 'Checked by hand',
    title: 'How often it is wrong',
    meta: 'Checked by hand',
    lede: (n, k) => `Checked by hand on ${n} contracts, its label differs on ${k}.`,
    wrong: 'Contracts where its label differs from the hand label',
    missed: 'Contracts that commit, missed',
    groups: [
      ['recall', 'Finds the contracts that commit', (m, r) => `The model finds ${m.k} of ${m.n}; the rule, ${r.k} of ${r.n}.`],
      ['precision', 'Right when it says a contract commits', (m, r) => `Of the contracts the model says commit, ${m.k} of ${m.n} do; of the rule’s, ${r.k} of ${r.n}.`],
      ['error', 'Wrong about whether a contract commits', (m, r) => `The model is wrong on ${m.k} of ${m.n} contracts; the rule, on ${r.k}.`],
    ],
    asof: (d) => `${DRAWN(d)} Labelled by ${d.eval.labelled_by} without seeing either reader’s answer. ${BARS}`,
    ref: 'Hand label',
    refWhy: null,
    first: 'Model',
    firstWhy: 'The model’s reason',
    none: (n) => `It agrees with the hand label on all ${n}.`,
    only: 'Only the 30 checked by hand',
    agree: 'Checked by hand: agrees',
    differ: (g) => `Checked by hand: ${LABEL_SHORT[g].toLowerCase()}`,
    limit: null,
    colophon: (e) => `${e.n} contracts, labelled by ${e.labelled_by} (${DATES(e)}); the rule baseline read the same pages.`,
  },
  model: {
    label: 'Checked by a second model',
    title: 'How often two readings differ',
    meta: 'Read twice',
    lede: (n, k) => `Read again by another model that never saw its answers, the two readings differ on ${k} of ${n} contracts.`,
    wrong: 'Contracts where the two readings give different labels',
    missed: 'Contracts the second reading says commit, missed by the first',
    groups: [
      ['recall', 'Finds the contracts the second reading says commit', (m, r) => `The model finds ${m.k} of ${m.n}; the rule, ${r.k} of ${r.n}.`],
      ['precision', 'When it says a contract commits, the second reading agrees', (m, r) => `Of the contracts the model says commit, the second reading agrees on ${m.k} of ${m.n}; of the rule’s, on ${r.k} of ${r.n}.`],
      ['error', 'Differs from the second reading on whether a contract commits', (m, r) => `The model differs on ${m.k} of ${m.n} contracts; the rule, on ${r.k}.`],
    ],
    asof: (d) => `${DRAWN(d)} Read again by ${d.eval.labelled_by} with a prompt of its own, in a fresh process that never saw the first reader’s answers. Two models of one family can misread a sentence the same way, so their agreement overstates accuracy; every quote and its source are below for a person to check. ${BARS}`,
    ref: 'Second reading',
    refWhy: 'The second reading’s reason',
    first: 'First reading',
    firstWhy: 'The first reading’s reason',
    none: (n) => `The two readings agree on all ${n}.`,
    only: 'Only the 30 read twice',
    agree: 'Second reading: agrees',
    differ: (g) => `Second reading: ${LABEL_SHORT[g].toLowerCase()}`,
    limit: 'The check is a second model, not a person. It shows where the reading is unstable, not where it is right: a person who reads French can check any contract from its quotes and its source.',
    colophon: (e) => `${e.n} contracts read again by ${e.labelled_by} (${DATES(e)}) with the prompt greening_check_v1; the rule baseline read the same pages. A person’s labels replace these once they are made.`,
  },
}
export const REGISTER = {
  kicker: 'Register of interventions · Brussels',
  title: 'What the neighbourhood contracts commit to',
  ref: (d) => REF[d?.eval?.kind === 'model' ? 'model' : 'person'],
  lede: (d) => (d.eval ? `${READ_ALL(d.contracts.length)} ${REF[d.eval.kind === 'model' ? 'model' : 'person'].lede(d.eval.n, d.eval.model.error.k)}` : `${READ_ALL(d.contracts.length)} The check is not finished.`),
  meta: (d, K) => [['Contracts', String(d.contracts.length)], ['Described', String(d.contracts.filter((c) => c.described).length)], ['Read by', 'Claude Sonnet 5'], [K.meta, String(d.testset.n)]],
  csv: 'Register (CSV)',
  checkFile: 'The check (JSON)',
  short: LABEL_SHORT,
  check: {
    figures: (e, q, K) => [
      [K.wrong, `${e.model.error.k} of ${e.n}`],
      [K.missed, `${e.model.yes.fn} of ${e.model.yes.tp + e.model.yes.fn}`],
      ['Quotes not found in the contract’s page', `${q.n - q.k} of ${q.n}`],
    ],
    readers: [['model', 'Language model', 'Claude Sonnet 5, prompt greening_v1'], ['rule', 'Rule', 'a greening word and a future marker in one sentence']],
    pending: 'The 30 contracts are being checked. The rates appear here once every label is in.',
  },
  miss: {
    label: 'Disagreements',
    title: 'Where it reads a contract differently',
    labels: (m, K) => [[K.ref, LABEL_SHORT[m.gold]], [K.first, LABEL_SHORT[m.model]], ['Rule', LABEL_SHORT[m.rule]]],
    quotes: 'Its quotes',
  },
  method: {
    label: 'Method',
    title: 'How it reads',
    rules: [
      'It never counts, estimates or ranks: every number on this site stays with the engine.',
      'Every measure carries the words it rests on, and a quote counts only if it is found word for word in the contract’s page.',
      'A contract commits when it plans, funds or carries out a measure that changes vegetation cover. Greening named only as an aim, a need or better access is an aim. A description of what exists, a diagnosis or a place name is no measure.',
      'The prompt, the output schema and the model are fixed and hashed. A changed prompt is a new version with a new check.',
      'The 30 test contracts were drawn by seed before any of them was read. The ten the prompt was written against are kept apart and never counted in the rate.',
      'It ran through Claude Code on the author’s own account with tools, connectors and project files switched off: it saw the prompt and one contract’s text, nothing else.',
    ],
  },
  list: {
    label: 'The register',
    title: 'Ninety-eight contracts, in their own words',
    filters: [['all', 'All'], ['yes', 'Commits'], ['weak', 'An aim'], ['no', 'No measure'], ['blank', 'Not described']],
    blank: 'The page gives no description: only photo credits and the budget.',
    empty: 'No greening in the text.',
    reason: 'Why this label',
    source: 'Source',
    count: (n) => `${n} ${n === 1 ? 'contract' : 'contracts'}`,
  },
  limits: {
    label: 'Limits',
    title: 'What it does not tell you',
    items: (K) => [
      '“Commits” records a promise made in a contract. Whether the ground changed is the atlas’s question, and it can answer only where a footprint of about a hectare exists; most of these measures are streets, courtyards and squares below that.',
      'The contracts publish no perimeter in a machine-readable form, so a measure cannot be placed on the map. Its place is the name the text gives.',
      'It reads the summary on quartiers.brussels, not the programme documents. The pages of 41 contracts, all started between 1994 and 2006, carry no summary at all.',
      'Beliris projects and the region’s own parks are not in this register.',
      ...(K.limit ? [K.limit] : []),
      'Thirty contracts give a wide interval, printed with every rate. The rate holds for this prompt and this model only.',
    ],
  },
  colophon: (d, K) => [
    ['Source', `${d.source}, ${d.contracts.length} contract pages, read on ${d.fetched}.`],
    ['Reader', `Claude Sonnet 5 through Claude Code in print mode, one call per contract, ${d.read_to}.`],
    ['Prompt', `${d.version} · prompt ${d.prompt_sha} · schema ${d.schema_sha}`],
    ['Check', d.eval ? K.colophon(d.eval) : 'In progress.'],
    ['Files', 'register.csv holds one row per quoted measure; register_check.json holds the check with every disagreement.'],
  ],
}

export const REGISTERED = {
  title: 'Registered before the works',
  lede: (n, date, source) => `${n} ${source} were fixed on ${date}, before any work began: the footprint with a hash, a 2023–25 baseline, and twelve control places named, or a refusal fixed in advance. An audit after the works cannot move the boundary to where it turned green.`,
  // whose projects a city's records are: the source that says the works have not started
  source: {
    brussels: 'Beliris projects',
    ghent: 'projects from the City of Ghent’s own register',
  },
  expects: {
    restoration: 'expects no change beyond noise: a restoration does not change vegetation',
    park_redesign: 'expects no change, or less sealed ground',
    boulevard_redesign: 'expects less sealed ground',
    square_redesign: 'expects less sealed ground and more grass',
    urban_development: 'expects a loss: a new quarter on grassland',
    park_creation: 'expects more trees as the planting grows; greenness may dip first, as young planting on grass can read as a loss',
    green_realisation: 'expects less built ground where buildings come down, the rest of the valley within noise',
  },
  refused: 'refused in advance: no comparable places',
  named: '12 control places named',
  // why a city has no record: what its sources were read for and what is still missing
  // (docs/research/2026-09-27-registers-before-works.md)
  none: (key, name) => ({
    antwerp: 'None yet. AG Vespa publishes no “works not started” status, so a record here can only come from a tender feed.',
    liege: 'None yet. Wallonia keeps no register like Beliris. The new parks at Fontainebleau (works from autumn 2027) and Chênée are dated, but their outlines exist only as drawings in the city’s brochures, so a record waits for a traced outline.',
    charleroi: 'None yet. The one greening project of a hectare or more not yet started, Square Hiernaux (a 1.7-hectare roundabout to become a planted square), has no published outline, so a record waits for the permit plans.',
  }[key] ?? `None yet. No source listing ${name}’s projects before their works has been read, so nothing was fixed in advance.`),
}

// "Who is short" under each need lens (phase 2, docs/07-unified-frondia.md). The numbers come from
// site_data.equity; the atlas puts the reading together from these words.
const SCENARIO_FOR = { family: 'a family', remote: 'remote work', senior: 'seniors' }
const SHOP_ONE = { bakery: 'bakery', cafe: 'café', confectionery: 'confectionery' }
export const EQUITY = {
  title: 'Who is short',
  thirds: ['Poorest third', 'Middle third', 'Richest third'],
  all: 'All residents', kid: 'Children under 15', old: 'Aged 65 and over',
  kidNoun: 'children', oldNoun: 'people aged 65 and over',
  byIncome: {
    services: (o) => `Average score for ${SCENARIO_FOR[o]}, out of 100, by income`,
    shops: (o) => `Average distance to the nearest ${SHOP_ONE[o]}, by income`,
    heat: () => 'Summer ground temperature against the city’s median sector, by income',
    r3: () => 'Share living where neither part is met, by income',
  },
  group: { services: 'the worst-served third', shops: 'the farthest third', heat: 'the hottest third', r3: 'the sectors that meet neither part' },
  cut: { services: (v) => `score ${v} or less`, shops: (v) => `${v} or farther`, heat: (v) => `${v} or more` },
  livesIn: (group, cut) => `Who lives in ${group}${cut ? ` (${cut})` : ''}`,
  vs: 'against all residents',
  // the poorest third against the richest, in the lens's own terms
  reading: {
    services: (worse, p, r) => `The poorest third is ${worse ? 'less well' : 'better'} served than the richest: ${p} against ${r}.`,
    shops: (worse, p, r, o) => `The poorest third lives ${worse ? 'farther from' : 'closer to'} a ${SHOP_ONE[o]} than the richest: ${p} against ${r}.`,
    heat: (worse, p, r) => `The poorest third is ${worse ? 'hotter' : 'cooler'} than the richest: ${p} against ${r}.`,
    r3: (worse, p, r) => `The poorest third misses both parts ${worse ? 'more' : 'less'} often than the richest: ${p} against ${r}.`,
  },
  // who lives in the worst-off group, against all residents (named from 2 points of difference)
  ages: {
    none: (g) => `Children and people aged 65 and over live in ${g} about as often as everyone else.`,
    one: (who, more, g, x, all) => `${who[0].toUpperCase()}${who.slice(1)} live in ${g} ${more ? 'more' : 'less'} often than residents overall: ${x} against ${all}.`,
    split: (more, less, g, x, y, all) => `${more[0].toUpperCase()}${more.slice(1)} live in ${g} more often than residents overall, ${less} less often: ${x} and ${y} against ${all}.`,
    both: (more, g, x, y, all) => `Children and people aged 65 and over both live in ${g} ${more ? 'more' : 'less'} often than residents overall: ${x} and ${y} against ${all}.`,
  },
  source: (lo, hi) => `Thirds of residents by the median taxable income of their sector (Statbel 2023): the poorest below ${lo}, the richest above ${hi}. Ages from the 2021 census.`,
}

export const OBJECTS = {
  benches: 'Benches', bicycle_repair: 'Bike repair stands', bike_parking: 'Bike parking',
  defibrillators: 'Defibrillators', dog_areas: 'Dog areas', drinking_water: 'Drinking fountains',
  fitness_stations: 'Outdoor fitness', picnic_tables: 'Picnic tables', playgrounds: 'Playgrounds',
  public_bookcases: 'Book exchanges', recycling: 'Recycling points', shelters: 'Shelters',
  toilets: 'Public toilets', waste_bins: 'Litter bins',
}
export const OBJECT_ONE = {
  benches: 'bench', bicycle_repair: 'bike repair stand', bike_parking: 'bike parking', defibrillators: 'defibrillator',
  dog_areas: 'dog area', drinking_water: 'drinking fountain', fitness_stations: 'outdoor fitness station',
  picnic_tables: 'picnic table', playgrounds: 'playground', public_bookcases: 'book exchange',
  recycling: 'recycling point', shelters: 'shelter', toilets: 'public toilet', waste_bins: 'litter bin',
}

export const PLACE = {
  lede: 'Each point is ranked by how much unmet demand it would cover within 500 m, weighted towards deprived sectors.',
  named: (date) => `The first ten of every kind were named on ${date}, before anyone placed anything; the next ten are their comparison. A later summer shows whether objects appeared where Frondia named them, more often than at the comparison points.`,
  legend: ['Named: ranks 1 to 10', 'Comparison: ranks 11 to 20', 'Further candidates: 21 to 40'],
  source: 'City Planner: a greedy solver on a demand grid, from OpenStreetMap and Statbel.',
  limit: 'A recommendation, not an effect: a bench changes no satellite reading, so only its appearance is checked.',
  // the manifest's own limit: existing objects are the state of the map, not of the city
  mapped: 'Today’s coverage counts what OpenStreetMap has mapped; where the map is thin, it reads lower than the street.',
  // the city's own register at the named points (research on the neighbours, items 1–3, 27 Sep 2026)
  register: (o, kind) => [
    o.named.at || o.control.at ? `By the city’s own register, ${/^[aeiou]/i.test(kind) ? 'an' : 'a'} ${kind} already stands within 50 m of ${o.named.at} named and ${o.control.at} comparison points: those leave the check, since an appearance there would be mapping.` : `By the city’s own register, no ${kind} stands within 50 m of any named or comparison point.`,
    o.named.gap != null ? `Within 500 m, ${o.named.gap} of ${o.named.n} named and ${o.control.gap} of ${o.control.n} comparison points have one that OpenStreetMap lacked when they were named: part of the gap was the map’s.` : '',
    // the rule written into the check on 27 Sep 2026: a gap more common in one group by 20 points or more is a caution
    o.named.gap != null && Math.abs(o.named.gap / o.named.n - o.control.gap / o.control.n) >= 0.2 ? `The ${o.named.gap / o.named.n > o.control.gap / o.control.n ? 'named' : 'comparison'} points sit in such gaps more often, so the check will say that mapping may explain part of any difference.` : '',
  ].filter(Boolean).join(' '),
  registerSnap: (d) => `Registers read ${d}; kept from now on, so an object that appears can be dated.`,
}

// the landing's "one map, three questions" cards (links open the atlas on that lens)
export const THREE = [
  { key: 'need', title: 'What’s missing',
    text: 'Everyday services for a family, from a school to a tram stop: the worst-served fifth of the city is the darkest. The same lens shows shops within reach, summer heat and the 3-30-300 rule.',
    cta: 'Open the lens', query: '?q=need&lens=services' },
  { key: 'place', title: 'What to place',
    text: 'Where the next public toilets should go, ranked by the demand each one would cover. Ten points of each of fourteen kinds of object were named on 5 September 2026, before anyone placed anything.',
    cta: 'Open the points', query: '?q=place&obj=toilets' },
  { key: 'change', title: 'What changed',
    text: 'Greener or browner beyond the city’s own noise, against twelve places that looked the same beforehand. Only this step is a measurement of change; the other two describe and recommend.',
    cta: 'Open the change', query: '?q=change' },
]

// the colophon's contact: Elena asked for her address to be on the page (26 Sep 2026)
export const CONTACT = { email: 'contact@frondia.eu' }
