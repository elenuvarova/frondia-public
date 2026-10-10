import type { Facts } from './types'

/* What two editions of the official canopy map say, against aerial photographs where they exist (re-check 1, 9 Oct):
   the five cities' official range, and — for a fair comparison — the official map and the photographs over the very
   same Flemish sectors (facts.editions.<city>.aerial: sectors classified ≥ 90 % on the photographs). Points of canopy
   (share × 100); null when the data is missing, and the proof band is then left out. */
export interface FlemishPair { official: number; aerial: number }
export interface EditionCompare {
  cities: number; officialMin: number; officialMax: number
  flemish: { antwerp: FlemishPair; ghent: FlemishPair }
}

export function editionCompare(facts: Facts): EditionCompare | null {
  const ed = facts.editions
  if (!ed || !Object.keys(ed).length) return null
  const official = Object.values(ed).map((e) => (e.canopy_2021 - e.canopy_2018) * 100)
  const pair = (k: string): FlemishPair | null => {
    const a = ed[k]?.aerial
    return a ? { official: (a.official_canopy_2021 - a.official_canopy_2018) * 100, aerial: (a.aerial_high_2021 - a.aerial_high_2018) * 100 } : null
  }
  const antwerp = pair('antwerp'), ghent = pair('ghent')
  if (!antwerp || !ghent) return null
  return { cities: official.length, officialMin: Math.min(...official), officialMax: Math.max(...official), flemish: { antwerp, ghent } }
}
