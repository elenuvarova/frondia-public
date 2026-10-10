// Fields the landing and its charts read (checked against site/public/data/*.json 28 Sep 2026 —
// see task-4-report.md for the two spots where the pipeline's data disagreed with a first draft).
// Extended 28 Sep for the document pages (task-1-report.md of plan 3): the dossier reads a sector's
// state (t24/n24/b24…), its trend second instrument (te), and the seasons after its baseline (after).
export interface Sector {
  id: string; n: string; c: string; d: string
  // the official Dutch and French names (Statbel 2024), only where they differ from the English site's: lib/names.ts
  n_nl?: string; n_fr?: string; c_nl?: string; c_fr?: string
  pop?: number; inc?: number | null
  // where to plant first (tree_priority.py): rank 1–20 and its role — 1–10 named before any planting, 11–20 their comparison
  tr?: number; trl?: 'named' | 'control'
  ne?: number | null; te?: number | null; raw?: number | null
  nv?: 'up' | 'down' | 'noise' | 'refused' | null; tv?: 'up' | 'down' | 'noise' | 'refused' | null; cmp?: boolean
  t24?: number; n24?: number; b24?: number
  k15?: number; o65?: number; o80?: number; kid?: number; old?: number; lt3?: number
  cs?: number; hot?: number; p30?: 0 | 1; p300?: 0 | 1; np?: number; lst?: number
  // [year, kind, effect] — the seasons after the sector's baseline that crossed the threshold
  after?: [number, string, number][]
  [lens: string]: unknown // need-lens fields (services, shops, heat, r3…) read by lib/lenses
}
export interface DossierPick { n: number; ids: string[]; min_residents: number; min_heat: number }
export interface DossierRules { controls: number; exclusion_m: number; max_gap: number; min_scenes: number }
export interface DossierBlock {
  medians: { t24: number; n24: number; b24: number }
  cuts: [number, number]
  thirds: [{ income: number; t24: number; n24: number }, { income: number; t24: number; n24: number }]
  kids_third: number
  seasons: number[]
  pick: DossierPick
  rules: DossierRules
}
// the city package's own "communes" block (city.communes.list): the commune outline for the map plus
// its Article 8 green/canopy reading (absent for Antwerp, whose communes are an outline only) — a different, smaller shape than a communes.json row (Commune below)
export interface CityCommuneEntry {
  code: string; name: string; name_nl?: string; name_fr?: string; green?: number | null; exempt?: boolean
  [k: string]: unknown
}
export interface City {
  city: string; name: string; window: string
  tree_named_at?: string | null
  tree_target?: number
  tree_register_copy?: string | null
  svg: { W: number; H: number; [k: string]: unknown }
  units: { comparable: number; [k: string]: unknown }
  thresholds: { ndvi: number; trees: number; [k: string]: number }
  null_mean: { ndvi: number; [k: string]: number }
  counts: { refused: number; [k: string]: number }
  background: { n: number; raw_median: number; k_raw: number; k_eff: number; share_raw: number; [k: string]: unknown }
  hist: unknown
  field: { box: [number, number, number, number]; src: string; [k: string]: unknown }
  sectors: Sector[]
  dossier: DossierBlock
  communes: { list: CityCommuneEntry[] }
  heat_canopy_r: number
  // the latest season measured since the 2024 base; the pipeline writes it as a string ("2026")
  balance?: { latest?: string } | null
  [k: string]: unknown
}
export interface Instrument { key: string; effect: number; threshold: number }
export interface Case {
  slug: string; city: string; area_ha: number; completed: string | number
  window_before: string; window_after: string
  images: { before?: string; after?: string }
  instruments: Instrument[]; defensible_effect?: number | null
  series: { threshold: number; seasons: { effect: number; [k: string]: unknown }[]; [k: string]: unknown }
  controls: unknown[]
}
export interface CityFacts {
  name: string; comparable: number; threshold_ndvi: number
  art8: { laus: number; exempt: string[]; green_ucuc: number; green7_ucuc: number; green_nw_ucuc: number; stable: boolean; canopy_r: number[] }
}
export interface Facts {
  tests: number; lst_threshold_c: number; restorations_noise: number
  parks: { refused: number; total: number }
  monitoring: { season: number; candidates: number; confirmed: number; construction: number }[]
  cities: Record<string, CityFacts>
  check?: { pooled: { canopy: { specificity: { k: number; n: number }; agreement_when_ours_changed: { k: number; n: number } } } }
  // two editions of the official canopy layer, 2018 and 2021 (scripts/official/art8_official_change.py);
  // `aerial` only where an independent aerial map exists (Groenkaart, Flanders)
  editions?: Record<string, EditionFacts>
  // Bruxelles Environnement's vegetation map 2021 → 2023 through the atlas's threshold (brussels_vegetation_check.py)
  be_vegetation?: {
    years: number[]; share_2021: number; share_2023: number; threshold: number
    verdicts: Record<string, number>; loss_ha: number; gain_ha: number; raw_change_ha: number
    example?: { id: string; name: string; area_ha: number; veg_2021: number; veg_2023: number; effect: number }
  }
}
// site/public/proof/proof.json (scripts/site/proof_photos.py): the pairs of aerial photos and whose they are
export interface ProofPair {
  city: string; sector: string; width: number; height: number; files: Record<string, string>
  sources?: Record<string, { request: string; sha256: string }>; read?: string
  credit: string; credit_lang?: string | null; licence: string
}
export interface Proof { editions: ProofPair; region: ProofPair }
export interface EditionFacts {
  years: number[]
  canopy_2018: number; canopy_2021: number; green_2018: number; green_2021: number
  threshold_canopy: number; threshold_green: number; units: number; comparable: number
  aerial?: {
    units: number; official_canopy_2018: number; official_canopy_2021: number
    aerial_high_2018: number; aerial_high_2021: number
    example: { id: string; name: string; area_ha: number; official_2018: number; official_2021: number; aerial_2018: number; aerial_2021: number }
  }
}
// s: the sector id the point falls in (points-<city>.json — data disagreed with a first draft that
// omitted it and `registered_at`; the dossier reads both: `p.s` to find a sector's own points, and
// `registered_at` for the "named on …" date).
export interface Point { x: number; y: number; r: number; t: string; s: string; role?: 'named' | 'control' | null }
export interface Points { city?: string; registered_at: string; types?: unknown; points: Point[] }

// ── /commune, /data, /register: the document pages (plan 3, task 1) ─────────────────────────────
export interface CommuneArt8Reading { reading: string; green: number | null; canopy: number | null; exempt: boolean | null }
export interface CommuneArt8 {
  green: number; canopy: number; exempt: boolean; stable: boolean
  readings: CommuneArt8Reading[]
  canopy_m2_per_resident: number | null
  region?: { green: number; canopy: number; exempt: boolean; n: number }
}
export interface CommuneBaseline {
  uea_ucuc_ha: number; green_ucuc_ha: number; green_ucuc_pct: number; canopy_ucuc_ha: number; canopy_ucuc_pct: number
  uea_lau_ha: number; green_lau_ha: number; green_lau_pct: number; canopy_lau_ha: number; canopy_lau_pct: number
}
export interface CommuneBalanceRow { lost: number; gained: number; net: number }
export interface CommuneBalanceSeason { green: CommuneBalanceRow; trees: CommuneBalanceRow; built: CommuneBalanceRow }
export interface CommuneBalance { base: number; latest: string; preliminary: Record<string, boolean>; seasons: Record<string, CommuneBalanceSeason> }
export interface CommuneChangeItem { id: string; n: string; n_nl?: string; n_fr?: string; e: number; v: 'up' | 'down' }
export interface CommuneChange {
  window: string; counts: { up: number; down: number; noise: number; refused: number }
  built: { up: number; down: number }
  top: CommuneChangeItem[]; top_built: CommuneChangeItem[]
}
export interface CommuneEvent { season: number; id: string; name: string; name_nl?: string; name_fr?: string; kind: string; effect: number | null }
export interface CommuneRegistered { id: string; name: string; type?: string; comparable: boolean }
export interface CommuneTreesWhereRow {
  planted_share: number; residents_share: number
  per_1000_in_third: number; per_1000_elsewhere: number; per_10ha_in_third: number; per_10ha_elsewhere: number
}
export interface CommuneTrees {
  date: string; trees: number; previous: number | null; licence: string
  planted?: Record<string, number>
  where?: { least_canopy: CommuneTreesWhereRow; poorest: CommuneTreesWhereRow; hottest: CommuneTreesWhereRow }
}
// one row of communes.json — not to be confused with City['communes'] above (the city package's own,
// smaller block: an outline and a green/exempt reading, no balance/change/trees/register history)
export interface Commune {
  // the city's and the region's English names are in the data too, and left out here: a page prints common.cities.<city>
  // and common.regions.<region_key> (tests/names.test.ts)
  code: string; city: string; region_key: 'brussels' | 'flanders' | 'wallonia'
  name: string; name_nl?: string; name_fr?: string; official: string; lau_id: string
  pop: number; area_km2: number; sectors: number; measured: number
  art8: CommuneArt8
  baseline?: CommuneBaseline | null
  balance?: CommuneBalance | null
  change: CommuneChange
  events: CommuneEvent[]
  registered: CommuneRegistered[]
  cases: string[]
  trees?: CommuneTrees | null
  dossier?: { id: string; n: string; n_nl?: string; n_fr?: string } | null
}

export interface DownloadColumn { name: string; description: string }
export interface DownloadLayer {
  key: string; group: string; title: string; file: string; format?: string | null
  rows: number | null; bytes: number; computed: string | null
  measures: string; method: string; source: string
  threshold: number | null; threshold_from: string
  limits: string[]; licence: string; credit: string[]
  columns: DownloadColumn[]
}
export interface DownloadsCity { name: string; manifest_bytes: number; layers: DownloadLayer[] }
// downloads.json is an object keyed by city, not an array — Record rather than Partial: every one
// of the five cities has a downloads block (the pipeline runs on all five)
export type Downloads = Record<import('./cities').CityKey, DownloadsCity>

export interface RegisterRate { k: number; n: number; value: number; ci95: [number, number] }
export interface RegisterEvalSide { precision: RegisterRate; recall: RegisterRate; error: RegisterRate; tp: number; fp: number; fn: number }
export interface RegisterDisagreement {
  id: number; name: string; gold: string; model: string; rule: string; model_why: string; check_why: string | null
}
export interface RegisterEval {
  kind: 'person' | 'model'
  labelled_by: string; labelled_from: string; labelled_to: string
  n: number; gold: unknown
  model: { error: RegisterRate; yes: RegisterEvalSide; any: RegisterEvalSide; kappa?: number; confusion?: unknown }
  rule: { yes: RegisterEvalSide; any: RegisterEvalSide }
  disagreements: RegisterDisagreement[]
}
export interface RegisterMeasure { q: string; status: string; kind: string; place: string | null }
export interface RegisterShownMeasure { q: string; status: string; kinds: string[]; places: string[] }
export interface RegisterContract {
  id: number; name: string; commune: string; years: [number, number]; url: string
  label: 'yes' | 'weak' | 'no'; why: string; rule: 'yes' | 'weak' | 'no'
  measures: RegisterMeasure[]; shown: RegisterShownMeasure[]
  described: boolean; test: boolean; gold: string | null
}
export interface RegisterLabels { kind: Record<string, string>; status: Record<string, string>; label: Record<string, string> }
export interface Register {
  version: string; model: string; prompt_sha: string; schema_sha: string
  read_from: string; read_to: string; fetched: string; source: string
  counts: { yes: number; weak: number; no: number; undescribed: number }
  quotes: RegisterRate
  testset: { seed: string; pool: number; n: number; development: number }
  eval: RegisterEval | null
  development: unknown
  labels: RegisterLabels
  contracts: RegisterContract[]
}
