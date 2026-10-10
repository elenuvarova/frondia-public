import type { City, EditionFacts, Facts, Proof, Sector } from './types'

/* Whether the proof band can stand (re-check 3, 9 Oct): the data's examples, the photos of those very sectors, the
   sectors on the map, and the years the captions name equal to the photos' years and to the numbers' keys. Anything
   missing leaves the band out — so the test on the real data says whether the page shows it. */
export interface ProofParts {
  ed: EditionFacts
  ex: NonNullable<EditionFacts['aerial']>['example']
  bv: NonNullable<Facts['be_vegetation']>
  bx: NonNullable<NonNullable<Facts['be_vegetation']>['example']>
  sa: Sector
  sb: Sector
}

export function proofReady(facts: Facts, proof: Proof | null, ant: City, bxl: City): ProofParts | null {
  const ed = facts.editions?.antwerp
  const ex = ed?.aerial?.example
  const bv = facts.be_vegetation
  const bx = bv?.example
  if (!proof || !ed || !ex || !bv || !bx) return null
  if (proof.editions.sector !== ex.id || proof.region.sector !== bx.id) return null
  const sa = ant.sectors.find((s) => s.id === ex.id)
  const sb = bxl.sectors.find((s) => s.id === bx.id)
  if (!sa || !sb) return null
  // the years the captions name must be the photos' years and the numbers' keys
  if (Object.keys(proof.editions.files).join() !== ed.years.join() || Object.keys(proof.region.files).join() !== bv.years.join()) return null
  if (!ed.years.every((y) => `official_${y}` in ex && `aerial_${y}` in ex) || !bv.years.every((y) => `veg_${y}` in bx)) return null
  return { ed, ex, bv, bx, sa, sb }
}
