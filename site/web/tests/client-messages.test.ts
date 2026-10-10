import fs from 'node:fs'
import path from 'node:path'
import { expect, test } from 'vitest'
import { ATLAS_CLIENT_PATHS, clientMessages, SITE_CLIENT_PATHS } from '@/lib/client-messages'
import en from '@/messages/en.json'

// The browser gets a subset of the catalogue (lib/client-messages.ts). A client component that reads
// a key outside it prints the key instead of the word — silently, and only in the browser. So every
// 'use client' file is read here: each useT('<ns>') / useTranslations('<ns>') namespace, and every
// key its t()/rich() calls name, must be in the shipped subset — the site's, the atlas's, or both
// for a component the atlas imports (two root layouts, two providers: lib/client-messages.ts).

const ROOT = path.resolve(__dirname, '..')
const DIRS = ['app', 'components', 'lib']
// the hook itself: it passes its namespace through, it names none
const SKIP = new Set(['lib/t-client.ts'])

type Tree = { [k: string]: unknown }
const shipped = clientMessages(en as unknown as Tree, SITE_CLIENT_PATHS)
const atlas = clientMessages(en as unknown as Tree, ATLAS_CLIENT_PATHS)
const SUBSET: Record<'site' | 'atlas', Tree> = { site: shipped, atlas }

function files(dir: string): string[] {
  return fs.readdirSync(path.join(ROOT, dir), { withFileTypes: true }).flatMap((e) => {
    const rel = path.join(dir, e.name)
    return e.isDirectory() ? files(rel) : /\.tsx?$/.test(e.name) ? [rel] : []
  })
}
const isClient = (src: string) => /^\s*(['"])use client\1/.test(src)

const at = (tree: unknown, key: string): unknown =>
  key.split('.').reduce<unknown>((n, k) => (n && typeof n === 'object' ? (n as Tree)[k] : undefined), tree)

// the first argument of a call starting at `open` (the index of its '('), as source text
function firstArg(src: string, open: number): string {
  let depth = 0, quote = ''
  for (let i = open + 1; i < src.length; i++) {
    const ch = src[i]!
    if (quote) { if (ch === '\\') i++; else if (ch === quote) quote = ''; continue }
    if (ch === '\'' || ch === '"' || ch === '`') quote = ch
    else if ('([{'.includes(ch)) depth++
    else if (')]}'.includes(ch)) { if (depth === 0) return src.slice(open + 1, i); depth-- }
    else if (ch === ',' && depth === 0) return src.slice(open + 1, i)
  }
  return src.slice(open + 1)
}

// the keys a first argument can name: its string literals, except the ones it only compares with
// (mode === 'effect' ? 'threshold.hist.effect' : …); a template literal names the prefix before ${
function keysOf(arg: string): { key: string; prefix: boolean }[] {
  const out: { key: string; prefix: boolean }[] = []
  for (const m of arg.matchAll(/(['"`])((?:\\.|(?!\1).)*)\1/g)) {
    if (/(?:===|!==|==|!=)\s*$/.test(arg.slice(0, m.index))) continue
    const body = m[2]!
    const dyn = m[1] === '`' ? body.indexOf('${') : -1
    out.push(dyn >= 0 ? { key: body.slice(0, dyn).replace(/\.$/, ''), prefix: true } : { key: body, prefix: false })
  }
  return out
}

// which call names read which namespace: `const { t, rich, raw } = useT('ns')` binds t and rich (and raw) to ns,
// `const t = useT('ns').t` binds t (and `const r = useT('ns').raw` a raw reader r),
// `const { t: ta } = useT('atlas')` binds ta, `const T = useT('ns')` binds T.t, T.rich and T.raw, `const t =
// useTranslations('ns')` binds t, t.rich, t.markup and t.raw. A file with two hooks (an atlas panel reads `atlas` and
// `common`) is checked call by call through these bindings. A hook read at once (`useT('ns').t('key')`) is chained: its
// calls are chainedCalls'. A hook bound to no name and read at no call cannot be followed: it is reported, so the test
// fails rather than passing on calls it never saw.
interface Hook { ns: string | null; raw: string; names: string[]; raws: string[]; chained?: boolean; unbound?: boolean }
const CHAIN = /^\.(t|rich|raw|markup)\(/
const MEMBER = /^\.(t|rich|raw|markup)\b(?!\s*[(<])/
function hooksOf(src: string): Hook[] {
  const out: Hook[] = []
  for (const m of src.matchAll(/(?:\b(?:const|let)\s+(\{[^}]*\}|[\w$]+)\s*=\s*)?\b(useT|useTranslations)\(\s*([^)]*?)\s*\)/g)) {
    const lit = /^(['"])([^'"]+)\1$/.exec(m[3]!)
    const bound = m[1]
    const translations = m[2] === 'useTranslations'
    // `const t = useT('ns').t`: a property read off the hook, not called on it
    const member = bound && !bound.startsWith('{') ? MEMBER.exec(src.slice(m.index! + m[0].length))?.[1] : undefined
    const names: string[] = [], raws: string[] = []
    // a whole object (useT's { t, rich, raw, loc }, or a rest element) read through its properties
    const whole = (x: string) => { names.push(`${x}.t`, `${x}.rich`); raws.push(`${x}.raw`) }
    if (bound?.startsWith('{')) {
      for (const part of bound.slice(1, -1).split(',')) {
        const p = part.trim()
        if (p.startsWith('...')) { whole(p.slice(3).trim()); continue }
        const [from, to] = p.split(':').map((x) => x.trim())
        if (from === 't' || from === 'rich') names.push(to || from!)
        else if (from === 'raw') raws.push(to || from)
      }
    } else if (bound && member) {
      // one function taken off the hook: `const t = useT('ns').t` binds t itself (a `.raw` binds a raw reader)
      if (member === 'raw') raws.push(bound)
      else names.push(bound)
    } else if (bound && translations) { names.push(bound, `${bound}.rich`, `${bound}.markup`); raws.push(`${bound}.raw`) }
    else if (bound) whole(bound)
    const chained = !bound && CHAIN.test(src.slice(m.index! + m[0].length))
    out.push({ ns: lit ? lit[2]! : null, raw: m[3]!, names, raws, ...(chained && { chained: true }), ...(!bound && !chained && { unbound: true }) })
  }
  return out
}

// the calls of a hook read at once: useT('ns').t('key'), .rich(…), .raw(…), useTranslations('ns').markup(…) — each key in
// that hook's namespace (raw marks a raw read, as a bound hook's raw does)
function chainedCalls(src: string): { ns: string; key: string; prefix: boolean; raw?: true }[] {
  return [...src.matchAll(/\b(useT|useTranslations)\(\s*(['"])([^'"]+)\2\s*\)\.(t|rich|raw|markup)\(/g)].flatMap((m) =>
    keysOf(firstArg(src, m.index! + m[0].length - 1)).map((k) => ({ ns: m[3]!, ...k, ...(m[4] === 'raw' && { raw: true as const }) })))
}

function callsOf(src: string, names: string[]): { key: string; prefix: boolean }[] {
  if (!names.length) return []
  const esc = names.map((n) => n.replace(/[$.]/g, '\\$&')).join('|')
  // a call may carry type arguments, which nest: raw<(string | null)[]>(…), raw<Record<string, X>>(…)
  return [...src.matchAll(new RegExp(`(?<![\\w.$])(?:${esc})(?=[<(])`, 'g'))].flatMap((m) => {
    let i = m.index! + m[0].length
    if (src[i] === '<') {
      for (let depth = 0; i < src.length; i++) {
        if (src[i] === '<') depth++
        else if (src[i] === '>' && src[i - 1] !== '=' && --depth === 0) { i++; break }
      }
    }
    return src[i] === '(' ? keysOf(firstArg(src, i)) : []
  })
}

// the subset a file's words come from: the atlas's own files get the atlas's provider; a component the
// atlas imports renders under both providers, so both must carry its words; everything else is the site's
const ATLAS_DIRS = ['components/atlas/', 'app/(atlas)/']
const inAtlas = (file: string) => ATLAS_DIRS.some((d) => file.split(path.sep).join('/').startsWith(d))
// every component the atlas reaches, however deep: a client leaf imported by a component the atlas imports renders
// under the atlas's provider too. Followed through `@/components/…` and relative imports between components.
function atlasImports(all: string[], read: (file: string) => string = (f) => fs.readFileSync(path.join(ROOT, f), 'utf8')): Set<string> {
  const out = new Set<string>()
  const known = new Map(all.map((f) => [f.split(path.sep).join('/').replace(/\.tsx?$/, ''), f]))
  const queue = all.filter(inAtlas)
  const seen = new Set(queue)
  while (queue.length) {
    const file = queue.shift()!
    const dir = path.posix.dirname(file.split(path.sep).join('/'))
    for (const m of read(file).matchAll(/from\s+['"](@\/components\/[\w/-]+|\.{1,2}\/[\w/.-]+)['"]/g)) {
      const spec = m[1]!
      const target = spec.startsWith('@/') ? spec.slice(2) : path.posix.normalize(path.posix.join(dir, spec))
      if (!target.startsWith('components/')) continue
      out.add(target)
      const next = known.get(target)
      if (next && !seen.has(next)) { seen.add(next); queue.push(next) }
    }
  }
  return out
}
type Scope = 'site' | 'atlas'
function scopesOf(file: string, imported: Set<string>): Scope[] {
  const f = file.split(path.sep).join('/')
  if (inAtlas(f)) return ['atlas']
  return imported.has(f.replace(/\.tsx?$/, '')) ? ['site', 'atlas'] : ['site']
}

interface Read { file: string; ns: string; key: string | null; prefix: boolean; scopes: Scope[]; raw?: boolean }
// what one client file reads: each hook's namespace, and every key its calls name
function readsOf(file: string, src: string, scopes: Scope[]): Read[] {
  const out: Read[] = []
  for (const h of hooksOf(src)) {
    // a namespace the source doesn't name can't be checked: name it
    if (!h.ns) { out.push({ file, ns: `<not a literal: ${h.raw}>`, key: null, prefix: false, scopes }); continue }
    // a hook whose calls cannot be followed: name it, as a namespace no subset ships
    if (h.unbound) { out.push({ file, ns: `<not bound to a name: ${h.ns}>`, key: null, prefix: false, scopes }); continue }
    out.push({ file, ns: h.ns, key: null, prefix: false, scopes })
    for (const k of callsOf(src, h.names)) out.push({ file, ns: h.ns, ...k, scopes })
    // raw() reads a catalogue array or object as it stands: the key must be shipped, whatever its shape
    for (const k of callsOf(src, h.raws)) out.push({ file, ns: h.ns, ...k, scopes, raw: true })
  }
  for (const c of chainedCalls(src)) out.push({ file, ...c, scopes })
  return out
}
function reads(): Read[] {
  const all = DIRS.flatMap(files)
  const imported = atlasImports(all)
  return all.flatMap((file) => {
    if (SKIP.has(file)) return []
    const src = fs.readFileSync(path.join(ROOT, file), 'utf8')
    return isClient(src) ? readsOf(file, src, scopesOf(file, imported)) : []
  })
}

test('keysOf reads the keys a call names, not what it compares with', () => {
  expect(keysOf(`mode === 'effect' ? 'threshold.hist.effect' : 'threshold.hist.raw'`))
    .toEqual([{ key: 'threshold.hist.effect', prefix: false }, { key: 'threshold.hist.raw', prefix: false }])
  expect(keysOf('`cities.${k}`')).toEqual([{ key: 'cities', prefix: true }])
  expect(keysOf(`'nav.home'`)).toEqual([{ key: 'nav.home', prefix: false }])
})

test('a file with two hooks reads each call in its own hook’s namespace', () => {
  const src = `
    const { t, loc } = useT('atlas')
    const { t: tc, rich: rc } = useT('common')
    t('bar.city'); tc('cities.ghent'); rc('charts.series.caption'); x.t('not.a.call')`
  const hs = hooksOf(src)
  expect(hs.map((h) => [h.ns, h.names])).toEqual([['atlas', ['t']], ['common', ['tc', 'rc']]])
  expect(callsOf(src, hs[0]!.names)).toEqual([{ key: 'bar.city', prefix: false }])
  expect(callsOf(src, hs[1]!.names)).toEqual([{ key: 'cities.ghent', prefix: false }, { key: 'charts.series.caption', prefix: false }])
})

test('a hook not destructured is read through its properties; one bound to no name fails the check', () => {
  // useT's object: T.t(…), T.rich(…) and T.raw(…) are its calls
  const src = `const T = useT('landing'); const { raw: r, ...rest } = useT('atlas'); const tt = useTranslations('common')
    T.t('loadError.title'); T.rich('threshold.title'); T.raw('threshold.steps'); t('not.mine')
    r('need.lenses.r3.legend'); rest.t('bar.city'); tt('nav.home'); tt.rich('charts.series.caption'); tt.raw('cities')`
  const [T, A, C] = hooksOf(src)
  expect(T).toMatchObject({ ns: 'landing', names: ['T.t', 'T.rich'], raws: ['T.raw'] })
  expect(callsOf(src, T!.names)).toEqual([{ key: 'loadError.title', prefix: false }, { key: 'threshold.title', prefix: false }])
  expect(callsOf(src, T!.raws)).toEqual([{ key: 'threshold.steps', prefix: false }])
  expect(callsOf(src, A!.raws)).toEqual([{ key: 'need.lenses.r3.legend', prefix: false }])
  expect(callsOf(src, A!.names)).toEqual([{ key: 'bar.city', prefix: false }])
  expect(callsOf(src, C!.names)).toEqual([{ key: 'nav.home', prefix: false }, { key: 'charts.series.caption', prefix: false }])
  expect(callsOf(src, C!.raws)).toEqual([{ key: 'cities', prefix: false }])
  // type arguments between the name and the call, nested, with an arrow type inside
  expect(callsOf(`raw<(string | null)[]>('a.b'); raw<Record<string, () => X>>('c'); raw < 2`, ['raw']))
    .toEqual([{ key: 'a.b', prefix: false }, { key: 'c', prefix: false }])
  // useT('landing').t(…): no name to follow, but the call itself names the key in the hook's namespace
  expect(chainedCalls(`useT('landing').t('hero.title')`)).toEqual([{ ns: 'landing', key: 'hero.title', prefix: false }])
  expect(hooksOf(`useT('landing').t('hero.title')`)).toEqual([{ ns: 'landing', raw: `'landing'`, names: [], raws: [], chained: true }])
  // unbound is left for a hook with neither a name nor a call on it
  expect(hooksOf(`f(useT(ns))`)).toEqual([{ ns: null, raw: 'ns', names: [], raws: [], unbound: true }])
})

test('a function taken off the hook, const t = useT(ns).t, and destructured aliases are followed to their calls', () => {
  const src = `const t = useT('landing').t
    const r = useT('atlas').raw
    const tr = useTranslations('common').rich
    const { t: tx, rich: rx, raw: rw } = useT('dossier')
    t('loadError.title'); r('need.lenses.r3.legend'); tr('charts.series.caption'); tx('a.b'); rx('c.d'); rw('e.f'); t.x('not.a.call')`
  const [L, A, C, D] = hooksOf(src)
  expect(L).toMatchObject({ ns: 'landing', names: ['t'], raws: [] })
  expect(A).toMatchObject({ ns: 'atlas', names: [], raws: ['r'] })
  expect(C).toMatchObject({ ns: 'common', names: ['tr'], raws: [] })
  expect(D).toMatchObject({ ns: 'dossier', names: ['tx', 'rx'], raws: ['rw'] })
  for (const h of [L, A, C, D]) expect(h).not.toHaveProperty('unbound')
  expect(readsOf('components/X.tsx', src, ['site']).filter((r) => r.key != null).map((r) => `${r.ns}.${r.key}${r.raw ? ' (raw)' : ''}`)).toEqual([
    'landing.loadError.title', 'atlas.need.lenses.r3.legend (raw)', 'common.charts.series.caption', 'dossier.a.b', 'dossier.c.d', 'dossier.e.f (raw)',
  ])
  // so a key the subset lacks, read through such a binding, is caught (it used to be read as t.t(…) and missed)
  const missing = readsOf('components/X.tsx', `const t = useT('common').t\n t('footer.label')`, ['site'])
    .filter((r) => r.key != null && typeof at(SUBSET.site, `${r.ns}.${r.key}`) !== 'string')
  expect(missing.map((r) => r.key)).toEqual(['footer.label'])
})

test('a hook read at once, useT(ns).t(key), is checked in its namespace, not reported as unbound', () => {
  const src = `useT('landing').t('hero.title'); useTranslations('atlas').rich(\`bar.\${k}\`); useT('common').raw('cities')`
  expect(readsOf('components/X.tsx', src, ['site'])).toEqual([
    { file: 'components/X.tsx', ns: 'landing', key: null, prefix: false, scopes: ['site'] },
    { file: 'components/X.tsx', ns: 'atlas', key: null, prefix: false, scopes: ['site'] },
    { file: 'components/X.tsx', ns: 'common', key: null, prefix: false, scopes: ['site'] },
    { file: 'components/X.tsx', ns: 'landing', key: 'hero.title', prefix: false, scopes: ['site'] },
    { file: 'components/X.tsx', ns: 'atlas', key: 'bar', prefix: true, scopes: ['site'] },
    { file: 'components/X.tsx', ns: 'common', key: 'cities', prefix: false, scopes: ['site'], raw: true },
  ])
  // a hook neither bound nor read at once still cannot be followed, and is still reported
  expect(readsOf('components/X.tsx', `const words = [useT('landing')]`, ['site']))
    .toEqual([{ file: 'components/X.tsx', ns: '<not bound to a name: landing>', key: null, prefix: false, scopes: ['site'] }])
})

test('the atlas’s reach follows imports past the first level, through @/components and relative paths', () => {
  const src: Record<string, string> = {
    'components/atlas/Panel.tsx': `import { A } from '@/components/A'\nimport { Seq } from './bits'`,
    'components/atlas/bits.tsx': `import { Leaf2 } from '@/components/charts/Leaf2'`,
    'components/A.tsx': `import { Leaf } from './Leaf'`,
    'components/Leaf.tsx': `import { lib } from '@/lib/format'`,
    'components/charts/Leaf2.tsx': `import { Deep } from '../Deep'`,
    'components/Deep.tsx': '',
    'components/Nav.tsx': '',
  }
  const got = atlasImports(Object.keys(src), (f) => src[f]!)
  expect([...got].sort()).toEqual(['components/A', 'components/Deep', 'components/Leaf', 'components/atlas/bits', 'components/charts/Leaf2'])
  expect(scopesOf('components/Leaf.tsx', got)).toEqual(['site', 'atlas'])
  expect(scopesOf('components/Deep.tsx', got)).toEqual(['site', 'atlas'])
  expect(scopesOf('components/Nav.tsx', got)).toEqual(['site'])
})

test('the atlas’s files read the atlas’s subset; a component the atlas imports reads both', () => {
  const imported = new Set(['components/SectorMap'])
  expect(scopesOf('components/atlas/Passport.tsx', imported)).toEqual(['atlas'])
  expect(scopesOf('app/(atlas)/[locale]/atlas/page.tsx', imported)).toEqual(['atlas'])
  expect(scopesOf('components/SectorMap.tsx', imported)).toEqual(['site', 'atlas'])
  expect(scopesOf('components/Nav.tsx', imported)).toEqual(['site'])
})

test('the site’s subset is small: common’s three client parts and the landing’s two, no document page', () => {
  expect(Object.keys(shipped).sort()).toEqual(['common', 'landing'])
  expect(Object.keys(shipped.landing as Tree).sort()).toEqual(['loadError', 'threshold'])
  expect(Object.keys((shipped.landing as Tree).threshold as Tree)).toEqual(['hist'])
  for (const ns of ['dossier', 'commune', 'data', 'register', 'privacy', 'atlas']) expect(shipped).not.toHaveProperty(ns)
  // common is cut to what the site's client components read (plan 5 fix wave, P5-2): the footer (a server
  // component), the city and object names, the separators and the 404's words stay on the server
  expect(Object.keys(shipped.common as Tree).sort()).toEqual(['charts', 'consent', 'nav'])
  for (const k of ['footer', 'objects', 'cities', 'sep', 'notFound', 'regions']) expect(shipped.common).not.toHaveProperty(k)
  // 5 000 again (plan 4, task 3's limit; plan 5, task 3 had raised it to 5 500 for common.objects.a/no)
  expect(JSON.stringify(shipped).length).toBeLessThan(5000)
})

test('the atlas’s subset: common with the charts, its own section, the audits’ place names; no landing, no documents', () => {
  expect(ATLAS_CLIENT_PATHS).toEqual(['common', 'atlas', 'landing.cases'])
  expect(at(atlas, 'common.charts.series.caption')).toBe(en.common.charts.series.caption)
  expect(at(atlas, 'common.cities.liege')).toBe('Liège')
  expect(at(atlas, 'landing.cases.ninove.place')).toBe(en.landing.cases.ninove.place)
  // the atlas section is the catalogue's own (it lands with plan 4, task 4)
  expect(atlas.atlas).toEqual((en as unknown as Tree).atlas)
  expect(at(atlas, 'landing.hero')).toBeUndefined()
  expect(Object.keys(atlas.landing as Tree)).toEqual(['cases'])
  for (const ns of ['dossier', 'commune', 'data', 'register', 'privacy']) expect(atlas).not.toHaveProperty(ns)
})

test('every key a client component reads is in the subset the browser gets', () => {
  const all = reads()
  const missing = all.flatMap(({ file, ns, key, prefix, scopes, raw }) => scopes.flatMap((scope) => {
    const where = `${file} (${scope})`
    const nsNode = at(SUBSET[scope], ns)
    if (!nsNode || typeof nsNode !== 'object') return [`${where}: namespace ${ns} is not shipped`]
    if (key == null) return []
    const node = key ? at(nsNode, key) : nsNode
    if (raw ? node === undefined : prefix ? !node || typeof node !== 'object' : typeof node !== 'string') return [`${where}: ${ns}.${key}${prefix ? '.*' : ''} is not shipped`]
    return []
  }))
  expect(missing).toEqual([])
  // the check found the client components that do read words (so it is not passing on nothing); the
  // atlas's files join this list as they land, so it is a floor, not the whole set
  const found = new Set(all.map((r) => r.file.split(path.sep).join('/')))
  for (const f of [
    'app/(site)/[locale]/error.tsx', 'app/(atlas)/[locale]/error.tsx', 'components/Nav.tsx', 'components/LanguageSwitcher.tsx',
    'components/ConsentBanner.tsx', 'components/HistogramBlock.tsx',
    'components/NullHistogram.tsx', 'components/BeforeAfter.tsx', 'components/Rings.tsx',
    'components/atlas/NeedPanel.tsx', 'components/atlas/Equity.tsx', 'components/atlas/PlacePanel.tsx', 'components/atlas/MoreN.tsx',
    'components/atlas/ChangePanel.tsx', 'components/atlas/BuiltBody.tsx', 'components/atlas/CommuneBody.tsx',
    'components/atlas/Balance.tsx', 'components/atlas/Passport.tsx', 'components/atlas/CaseDrawer.tsx',
  ]) expect(found, f).toContain(f)
  // the atlas's panels are read against the atlas's subset, and the charts they render against both
  const scoped = new Map(all.map((r) => [r.file.split(path.sep).join('/'), r.scopes]))
  expect(scoped.get('components/atlas/Passport.tsx')).toEqual(['atlas'])
  // each root layout's error page reads its own layout's subset
  expect(scoped.get('app/(atlas)/[locale]/error.tsx')).toEqual(['atlas'])
  expect(scoped.get('app/(site)/[locale]/error.tsx')).toEqual(['site'])
  expect(scoped.get('components/NullHistogram.tsx')).toEqual(['site', 'atlas'])
  // raw() reads are checked too (the legends with gaps)
  expect(all.some((r) => r.raw && r.file.endsWith('NeedPanel.tsx'))).toBe(true)
  expect(all.filter((r) => r.key != null).length).toBeGreaterThan(25)
})
