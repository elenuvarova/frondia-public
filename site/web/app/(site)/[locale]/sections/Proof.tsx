import { Rule } from '@/components/Rule'
import { editionCompare } from '@/lib/editions'
import { dec, pct, signed } from '@/lib/format'
import { sectorLabel, sectorPlace } from '@/lib/names'
import { proofReady } from '@/lib/proof'
import { getT } from '@/lib/t'
import { plain } from '@/lib/typography'
import type { City, Facts, Proof as ProofData, ProofPair } from '@/lib/types'
import { inWords } from './words'

/* (2) Maps rustle too (9 Oct 2026). Reference: OpenAI's DALL·E 3 comparison — one claim, two equal pictures side by
   side, a short caption under each — with DALL·E 2's pair of numbers and Mapbox's source line (refs in
   docs/design/landing/refs/proof-band). Two figures: two editions of the official canopy map against aerial photos of
   one Antwerp sector, and Bruxelles Environnement's own map on its strongest loss beyond noise. Every number and year
   reads facts.json; the sectors are the ones the data chose, and the photos must be of those very sectors
   (proof.json's `sector`), or the band is left out. The numbers are not coloured: two sources compared, not an effect
   beyond a threshold. Re-check 1 (9 Oct): names through sectorName, one figcaption, the Flemish credit in Dutch. Re-check 3: the guards
   live in lib/proof.ts (tested on the real data), the numbers are read by the captions' years. */
export async function Proof({ facts, proof, ant, bxl }: { facts: Facts; proof: ProofData; ant: City; bxl: City }) {
  const { t, rich, raw, loc } = await getT('landing')
  const cmp = editionCompare(facts)
  const parts = proofReady(facts, proof, ant, bxl)
  if (!cmp || !parts) return null
  const { ed, ex, bv, bx, sa, sb } = parts
  const em = (c: React.ReactNode) => <em>{c}</em>
  const [e0 = '', e1 = ''] = ed.years.map(String)
  const [r0 = '', r1 = ''] = bv.years.map(String)
  const common = await getT('common')
  const fallback = (id: string) => common.t('sectorFallback', { id })
  const editionsPlace = t('proof.editions.place', { name: sectorLabel(sa, loc, fallback), district: sectorPlace(sa, loc) })
  const regionPlace = t('proof.region.place', { name: sectorLabel(sb, loc, fallback), district: sectorPlace(sb, loc) })
  const en = (c: React.ReactNode) => <span lang="en">{c}</span>
  // the arrow and the source's separator are the catalogue's (proof.change, proof.source), as every separator on the site
  const arrow = (a: number, b: number) => t('proof.change', { a: pct(a, 0, loc).replace(/\s*%$/, ''), b: pct(b, 0, loc) })
  // each caption's text is ONE flex child of .twin-cap (a column): a bare lang span beside text would split the line (re-check 3)
  // numbers by the years the captions name (proofReady checked the keys exist)
  const num = (o: object, p: string, y: string) => (o as Record<string, number>)[`${p}_${y}`] ?? NaN
  const fl = (k: 'antwerp' | 'ghent', f: 'official' | 'aerial') => dec(cmp.flemish[k][f], loc, 1)
  return (
    <section id="proof" className="section">
      <div className="wrap">
        <Rule n={2} right={t('proof.ruleRight', { a: e0, b: e1, c: r0, d: r1 })}>{t('proof.rule')}</Rule>
        <div className="split reveal">
          <h2 className="display-l">{rich('proof.title', { em })}</h2>
          <p className="body">{t('proof.body')}</p>
        </div>

        <figure className="proof-ring reveal">
          <Pair pair={proof.editions} place={editionsPlace} photo={(y) => t('proof.photo', { year: y })} alt={(y) => t('proof.alt', { place: editionsPlace, year: y })} />
          <figcaption>
            <div className="twin twin--plain">
              <div className="twin-map">
                <div className="proof-num"><span className="num-xl">{arrow(num(ex, 'official', e0), num(ex, 'official', e1))}</span>
                  <span className="twin-cap"><span className="label">{t('proof.editions.officialLabel')}</span><span>{rich('proof.editions.officialCap', { a: e0, b: e1, en })}</span></span></div>
              </div>
              <div className="twin-map">
                <div className="proof-num"><span className="num-xl">{arrow(num(ex, 'aerial', e0), num(ex, 'aerial', e1))}</span>
                  <span className="twin-cap"><span className="label">{t('proof.editions.aerialLabel')}</span><span>{t('proof.editions.aerialCap')}</span></span></div>
              </div>
            </div>
            <p className="small proof-close">{t('proof.editions.close', {
              a: e0, b: e1, count: inWords(raw<string[]>('words'), cmp.cities).toLowerCase(),
              min: dec(cmp.officialMin, loc, 1), max: dec(cmp.officialMax, loc, 1),
              oa: fl('antwerp', 'official'), og: fl('ghent', 'official'), pa: fl('antwerp', 'aerial'), pg: fl('ghent', 'aerial'),
            })}</p>
            <Source pair={proof.editions} line={t('proof.source', { credit: proof.editions.credit, licence: proof.editions.licence })} />
          </figcaption>
        </figure>

        <figure className="proof-ring reveal">
          <Pair pair={proof.region} place={regionPlace} photo={(y) => t('proof.photo', { year: y })} alt={(y) => t('proof.alt', { place: regionPlace, year: y })} />
          <figcaption>
            <div className="twin twin--plain">
              <div className="twin-map">
                <div className="proof-num"><span className="num-xl">{arrow(num(bx, 'veg', r0), num(bx, 'veg', r1))}</span>
                  <span className="twin-cap"><span className="label">{t('proof.region.mapLabel')}</span><span>{t('proof.region.mapCap', { a: r0, b: r1 })}</span></span></div>
              </div>
              <div className="twin-map">
                <div className="proof-num"><span className="num-xl">{signed(bx.effect * 100, 0, loc)}</span>
                  <span className="twin-cap"><span className="label">{t('proof.region.effectLabel')}</span><span>{t('proof.region.effectCap', { thr: dec(bv.threshold * 100, loc, 1) })}</span></span></div>
              </div>
            </div>
            <p className="small proof-close">{t('proof.region.close', {
              a: r0, b: r1, s21: pct(bv.share_2021, 1, loc), s23: pct(bv.share_2023, 1, loc),
              loss: String(bv.verdicts['потеря'] ?? 0), gain: String(bv.verdicts['прирост'] ?? 0),
            })}</p>
            <Source pair={proof.region} line={t('proof.source', { credit: proof.region.credit, licence: proof.region.licence })} />
          </figcaption>
        </figure>
      </div>
    </section>
  )
}

function Pair({ pair, place, photo, alt }: { pair: ProofPair; place: string; photo: (y: string) => string; alt: (y: string) => string }) {
  return (
    <>
    {/* where the photos are, visible (re-check 2: it was only in the alt and the group's name) */}
    <p className="label proof-place" aria-hidden="true">{place}</p>
    <div className="proof-pair" role="group" aria-label={plain(place)}>
      {Object.entries(pair.files).map(([year, file]) => (
        <div className="proof-photo" key={year}>
          <img src={`/proof/${file}`} width={pair.width} height={pair.height} alt={plain(alt(year))} loading="lazy" decoding="async" />
          {/* the year is in the alt already: the visible label is not read twice */}
          <span className="label" aria-hidden="true">{photo(year)}</span>
        </div>
      ))}
    </div>
    </>
  )
}

// the rights holder's credit is quoted in its own language (WCAG 3.1.2): the Flemish one is Dutch on every page
function Source({ pair, line }: { pair: ProofPair; line: string }) {
  return <p className="mono proof-source" lang={pair.credit_lang ?? undefined}>{line}</p>
}
