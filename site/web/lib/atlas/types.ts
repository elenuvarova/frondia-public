// What the atlas reads on top of the document pages' City (lib/types.ts), checked against
// site/public/data/{brussels,antwerp,ghent,liege,charleroi}.json and points-<city>.json on 2 Oct 2026 against
// site/apps/atlas/src/pages/Atlas.jsx. A block a city's pipeline has not produced is null (check: three of five
// cities; photos/built/balance are in every file today but the atlas guards them, so the type says so); the data's
// shape wins over any description of it.
import type { City, CityCommuneEntry, Points } from '@/lib/types'

export interface AtlasCase { slug: string; name: string; x: number; y: number; d: string }

export interface Hist { lo: number; hi: number; n: number; effect: number[]; raw: number[] }

export interface HaRow { lost_ha: number; gained_ha: number; net_ha: number; raw_net_ha: number; lost_sectors?: number; gained_sectors?: number }
export type AtlasSeason = Record<'green' | 'trees' | 'built', HaRow> & {
  thresholds?: Record<'green' | 'trees' | 'built', number>
  comparable?: number
}

export interface Rate { k: number; n: number }

// one lens's row: thirds by income (least → most), the share of every resident / of children / of 65+, and the income
// cut that splits them (null where the lens has no cut: 3-30-300)
export interface EquityRow { thirds: [number, number, number]; all: number; kid: number; old: number; cut: number | null }
export type EquityBlock = Record<string, EquityRow>

// Antwerp's communes carry an outline and an area only (no Article 8 reading yet), so every reading is optional
export type AtlasCommune = CityCommuneEntry & {
  d: string; x: number; y: number
  area?: number; canopy?: number; stable?: boolean; green7?: number; green_nw?: number; pop?: number
}

export interface AtlasRegistered {
  id: string; name: string; d: string; x: number; y: number
  comparable: boolean; type?: string; registered: string
  hash?: string; ndvi?: number; controls?: number; gap?: number
}

export interface AtlasCity extends City {
  cases: AtlasCase[]
  photos: { years: [number, number]; src: [string, string]; box?: [number, number, number, number] } | null
  built: {
    threshold: number
    counts: { up: number; down: number; noise: number; refused: number }
    pop?: { up: number; down: number }
    hist: Hist
  } | null
  balance: {
    base: number
    latest: string
    preliminary: Record<string, boolean>
    seasons: Record<string, AtlasSeason>
  } | null
  check: { green: { specificity: Rate; agreement_when_ours_changed: Rate } } | null
  equity: {
    income_cuts: [number, number]
    income_share?: [number, number, number]
    [lens: string]: EquityBlock | number[] | undefined
  }
  communes: {
    list: AtlasCommune[]
    tested: number
    exempt: number
    region?: { green: number; exempt?: boolean } | null
    leave_out?: { area: number; residents: number; woody: number; rest_green: number; rest: number } | null
  }
  registered: AtlasRegistered[]
  field: City['field'] & { year?: number }
}

// where the register of a named point stood: at = how many of the named (or control) points had the object by the
// snapshot, gap = the distance of the shortfall (null where there is no control), n = how many were named
export interface PointOfficial {
  date: string
  named: { at: number; gap: number | null; n: number }
  control: { at: number; gap: number | null; n: number }
}
export interface PointType {
  key: string; n: number; pool: number
  before?: number; after?: number; steps?: number[]
  official?: PointOfficial
}
export type AtlasPoints = Points & { types: PointType[] }
