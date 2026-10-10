import 'server-only'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { cache } from 'react'
import { infoOf, isPublished, type Locale } from '@/i18n/locales'
import type { CityKey } from './cities'
import type { Case, City, Commune, Downloads, Facts, Points, Register, Proof } from './types'

// The pipeline writes site/public/data (scripts/site/site_data.py); the app reads the same files on
// the server, so a page arrives with its numbers instead of fetching them after load.
const DATA = path.join(process.cwd(), 'public', 'data')

export class DataError extends Error {
  // the system's error code when the file could not be read ('ENOENT': not there); undefined for a file that is there but broken
  readonly code: string | undefined
  constructor(public file: string, cause: unknown) {
    super(`data/${file}: ${cause instanceof Error ? cause.message : String(cause)}`)
    const c = (cause as { code?: unknown } | null)?.code
    this.code = typeof c === 'string' ? c : undefined
  }
}

const MEMO = new Map<string, Promise<unknown>>()
export const _memo = MEMO // tests only

function freeze<T>(o: T): T {
  if (o && typeof o === 'object' && !Object.isFrozen(o)) {
    Object.freeze(o)
    for (const v of Object.values(o)) freeze(v)
  }
  return o
}

async function parse(name: string): Promise<unknown> {
  try {
    return JSON.parse(await readFile(path.join(DATA, name), 'utf8'))
  } catch (e) {
    throw new DataError(name, e)
  }
}

// production: the files are baked into the image, so each is parsed once per process (Brussels is 653 KB, ~3 ms of parse
// per request saved; the rest of a request is render); a failed read leaves the map, so a file that appears later is read. Elsewhere a fresh
// read every request — the pipeline rewrites public/data while `next dev` runs — deep-frozen, so code that sorts or edits
// the shared object in place breaks here, in development, instead of corrupting production's one copy
function readOnce(name: string): Promise<unknown> {
  if (process.env.NODE_ENV !== 'production') return parse(name).then(freeze)
  let p = MEMO.get(name)
  if (!p) {
    p = parse(name)
    MEMO.set(name, p)
    p.catch(() => MEMO.delete(name))
  }
  return p
}

// one read per file per request on top (cache() — the generic lives on the wrapper, cache() would drop it)
const read = cache(readOnce)

export function loadJSON<T>(name: string): Promise<T> {
  return read(name) as Promise<T>
}

// the proof photos' own file sits beside the data (public/proof, written by scripts/site/proof_photos.py)
const PROOF = '../proof/proof.json'

export interface LandingData { facts: Facts; bxl: City; ant: City; cases: Case[]; points: Points | null; proof: Proof | null }

export async function getLanding(): Promise<LandingData> {
  const [facts, bxl, ant, cases] = await Promise.all([
    loadJSON<Facts>('facts.json'), loadJSON<City>('brussels.json'),
    loadJSON<City>('antwerp.json'), loadJSON<Case[]>('cases.json'),
  ])
  // the points feed one card only: the page does not fail without them
  const points = await loadJSON<Points>('points-brussels.json').catch(() => null)
  // the proof photos sit beside the data (public/proof); without them the band is left out, not broken
  const proof = await loadJSON<Proof>(PROOF).catch(() => null)
  return { facts, bxl, ant, cases, points, proof }
}

// ── document pages (plan 3): dossier, commune, data, register ──────────────────────────────────
export const getCity = (key: CityKey): Promise<City> => loadJSON<City>(`${key}.json`)
export const getCases = (): Promise<Case[]> => loadJSON<Case[]>('cases.json')
export const getCommunes = (): Promise<Commune[]> => loadJSON<Commune[]>('communes.json')
// a language's own data texts (downloads.<loc>.json, register.<loc>.json, written by scripts/site/downloads.py and
// register.py from scripts/site/i18n/<loc>.json); a preview language without its file yet reads the English one, a
// published language must have its own (tests/catalogues.test.ts checks the files exist for every published language).
// Only a file that is not there falls back: a language's file that is there but broken is an error in every language
async function localised<T>(base: string, loc: Locale): Promise<T> {
  if (loc === 'en' || infoOf(loc).dev) return loadJSON<T>(`${base}.json`)
  try {
    return await loadJSON<T>(`${base}.${loc}.json`)
  } catch (e) {
    if (e instanceof DataError && e.code === 'ENOENT' && !isPublished(loc)) return loadJSON<T>(`${base}.json`)
    throw e
  }
}
export const getDownloads = (loc: Locale): Promise<Downloads> => localised<Downloads>('downloads', loc)
export const getRegister = (loc: Locale): Promise<Register> => localised<Register>('register', loc)
// not every city has a named-points file yet (the pipeline runs city by city): null, not a thrown
// DataError, so a dossier can still render its other sections without "what to place here"
export const getPoints = (key: CityKey): Promise<Points | null> =>
  loadJSON<Points>(`points-${key}.json`).catch(() => null)
