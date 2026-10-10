'use client'
import { useCallback, useEffect, useMemo, useRef, useState, type FocusEvent, type KeyboardEvent, type ReactNode } from 'react'
import { SectorMap, FIELD_UNDER_DATA, builtFill, countFor, fillFor } from '@/components/SectorMap'
import { keptEnglish, localePath } from '@/i18n/locales'
import { CITIES, type CityKey } from '@/lib/cities'
import { int, pct } from '@/lib/format'
import { placeName, sectorLabel, sectorName, sectorPlace } from '@/lib/names'
import { needFill, needStep } from '@/lib/lenses'
import { bbox, greenStep, leftLabels, type Box } from '@/lib/atlas/geometry'
import { atlasHeadWords } from '@/lib/atlas/head'
import { atlasPath, firstMeasured, type AtlasState } from '@/lib/atlas/state'
import type { AtlasCity, AtlasPoints, AtlasRegistered } from '@/lib/atlas/types'
import { changeTip, needLabel } from '@/lib/atlas/words'
import type { Case, Point, Sector } from '@/lib/types'
import { track } from '@/components/Events'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'
import { EV } from '@/lib/analytics'
import { useT } from '@/lib/t-client'
import { tie, plain } from '@/lib/typography'
import { CaseDrawer, type DrawerCase } from './CaseDrawer'
import { ChangePanel } from './ChangePanel'
import { GREENS } from './CommuneBody'
import { MapLayers } from './MapLayers'
import { NeedPanel } from './NeedPanel'
import { Passport } from './Passport'
import { PlacePanel } from './PlacePanel'
import { SwipeHandle } from './SwipeHandle'
import { useJSON } from './useJSON'
import { useViewBox } from './useViewBox'

/* ── the atlas (Atlas.jsx 867–1134) ────────────────────────────────────────────────────────────────
   The server read the address once (lib/atlas/resolve.ts) and hands the first view here as `initial`; from then on
   the view is this component's state, and the address follows it through history.replaceState (A3 of plan 4):
   replaced, never pushed, and never a request to the server. The city's files come from the browser (A2). */
type Icons = Record<'pin' | 'need' | 'place' | 'change', ReactNode>
const QS = ['need', 'place', 'change'] as const

export function Atlas({ initial, icons }: { initial: AtlasState; icons: Icons }) {
  const { t, loc } = useT('atlas')
  const { t: tc } = useT('common')
  const [cityKey, setCityKey] = useState<CityKey>(initial.city)
  const [caseSlug, setCaseSlug] = useState<string | null>(initial.caseSlug)
  // a link to a sector, not applied yet: held until its city's data is here, then opened and flown to once
  const [deep, setDeep] = useState<string | null>(initial.sector)
  const cityUrl = `/data/${cityKey}.json`, pointsUrl = `/data/points-${cityKey}.json`
  const { data: city, error: cityFail, url: cityAt } = useJSON<AtlasCity>(cityUrl)
  const { data: cases } = useJSON<Case[]>('/data/cases.json')
  const pointsRead = useJSON<AtlasPoints>(pointsUrl)
  // the last city's data stays on screen while the next city's file is on its way (useJSON), but its named points and a
  // failed read belong to that city alone: they are not this city's, so they are neither drawn nor reported here
  const cityError = cityAt === cityUrl ? cityFail : null
  const points = pointsRead.url === pointsUrl ? pointsRead.data : null
  const pointsError = pointsRead.url === pointsUrl ? pointsRead.error : null
  // the question: from the address, otherwise "what changed" — the landing's deep links (?case=, ?sector=) belong to it
  const [q, setQ] = useState<string>(initial.q)
  const [needLens, setNeedLens] = useState<string | null>(initial.lens)
  const [opt, setOpt] = useState({ scenario: initial.scenario, shop: initial.shop })
  const [obj, setObj] = useState(initial.obj)
  // what if N more: the ten named by default; the address keeps another choice
  const [moreN, setMoreN] = useState(initial.n)
  const [control, setControl] = useState(true)
  const [lens, setLens] = useState<string>(initial.view)
  const [measure, setMeasure] = useState<string>(initial.m)
  const [selected, setSelected] = useState<Sector | null>(null)
  const [hovered, setHovered] = useState<Sector | null>(null)
  const [hoverPt, setHoverPt] = useState<Point | null>(null)
  const svgRef = useRef<SVGSVGElement>(null), stageRef = useRef<HTMLElement>(null)
  const W = city?.svg.W || 1000, H = city?.svg.H || 1000
  const { vb, size: stageSize, home, zoomAt, flyTo, fitBox, panBy, handlers, wasDrag } = useViewBox(svgRef, W, H)
  // map units per screen pixel: the viewBox keeps the stage's aspect, so one scale holds both ways
  const unitPx = stageSize ? stageSize.w / vb.w : 1
  const labelFs = Math.max(vb.w / 78, 10 / unitPx), pinR = Math.max(vb.w / 100, 8 / unitPx), pinFs = Math.max(vb.w / 125, 8 / unitPx)

  const flown = useRef<string | null>(null)   // the sector the view last flew to: a link to it does not fly again
  useEffect(() => { setSelected(null); flown.current = null }, [cityKey])
  // until one is chosen, the first need lens this city measures; a chosen one that this city does not measure stays
  // chosen and says so (with a link to the city that does)
  const need = needLens || (city ? firstMeasured(city) : 'heat')
  // the link to a sector opens that sector's card and flies to it, once; a sector this city does not have is dropped
  // (only once this city's own data is here: until then the data on screen may still be the last city's)
  useEffect(() => {
    if (!city || !deep) return
    const s = city.sectors.find((x) => x.id === deep)
    if (!s) { if (city.city === cityKey) setDeep(null); return }
    if (selected?.id !== s.id) setSelected(s)
    if (flown.current !== s.id) {
      const box = fitBox(bbox(s.d), 3.2, true)
      if (box) { flyTo(box); flown.current = s.id; setDeep(null) }
    } else setDeep(null)
  }, [city, deep, fitBox]) // eslint-disable-line react-hooks/exhaustive-deps
  // an audit of this city opens on "what changed", flown to (Atlas.jsx 915–919); one this city does not have (unknown,
  // or another city's) is dropped once this city's own data is here (Q15: the old atlas opened another city's audit
  // over this city's map, and kept an unknown one in the address)
  useEffect(() => {
    if (!city || !caseSlug) return
    const c = city.cases.find((x) => x.slug === caseSlug)
    if (c) { setQ('change'); setSelected(null); flyTo(fitBox(bbox(c.d), 14, true)) }
    else if (city.city === cityKey) setCaseSlug(null)
  }, [city, caseSlug, fitBox]) // eslint-disable-line react-hooks/exhaustive-deps

  const mode = q !== 'change' || lens === 'field' ? 'field' : control ? 'effect' : 'raw'
  const thr = city?.thresholds.ndvi ?? 0
  const counts = useMemo(() => (city ? countFor(city.sectors, (mode === 'field' ? 'effect' : mode) as 'effect', thr) : { up: 0, down: 0 }), [city, mode, thr])
  const builtOn = q === 'change' && lens === 'change' && measure === 'built' && !!city?.built
  const top = useMemo(() => {
    if (!city) return []
    const be = (s: Sector) => Math.abs((s as Sector & { be?: number }).be ?? 0)
    if (builtOn) {
      return city.sectors.filter((s) => s.bv === 'up' || s.bv === 'down').sort((a, b) => be(b) - be(a)).slice(0, 8)
    }
    return city.sectors.filter((s) => fillFor(s, 'effect', thr) && s.nv !== 'refused')
      .sort((a, b) => Math.abs(b.ne ?? 0) - Math.abs(a.ne ?? 0)).slice(0, 8)
  }, [city, thr, builtOn])
  const sealFill = useCallback((s: Sector) => builtFill(s, city?.built?.threshold ?? NaN), [city])
  const fill = useCallback((s: Sector) => needFill(s, need, opt), [need, opt])
  const communesOn = q === 'change' && lens === 'communes'
  const photosOn = q === 'change' && lens === 'photos' && !!city?.photos
  const photoSrc = useMemo(() => (city?.photos ? city.photos.src.map((s) => '/' + s) as [string, string] : null), [city])
  const communeOf = useMemo(() => new Map((city?.communes?.list || []).map((c) => [c.code, c])), [city])
  const communeFill = useCallback((s: Sector) => {
    const c = communeOf.get(s.id.slice(0, 5))
    return c && c.green != null ? GREENS[greenStep(c.green)!]! : 'var(--noise)'
  }, [communeOf])
  const flyBox = (b: Box | null, pad: number) => { if (b) flyTo(fitBox(b, pad, true)) }
  const pickRegistered = (r: AtlasRegistered) => flyBox(bbox(r.d), 8)
  const { t: tl, raw: rl } = useT('landing')
  const known = rl<Record<string, { place?: string }>>('cases')
  const leftLabel = useMemo(() => leftLabels(city?.cases || [], (slug) => (known[slug]?.place ? tl(`cases.${slug}.place`) : undefined), vb.w),
    [city, vb.w]) // eslint-disable-line react-hooks/exhaustive-deps
  const noFill = useCallback(() => null, [])

  // the address follows the view (city, question, lens and its choice, object, the open sector or audit), so a copied
  // link opens what is on screen
  const here = atlasPath(loc, { city: cityKey, q: q as AtlasState['q'], lens: need, scenario: opt.scenario, shop: opt.shop, obj, n: moreN,
    view: lens as AtlasState['view'], m: measure as AtlasState['m'], caseSlug, sector: selected?.id ?? null })
  // a link to a sector of this city, not applied yet (a sector of the other city is dropped)
  const pending = !!deep && !selected && !!city?.sectors.some((x) => x.id === deep)
  useEffect(() => {
    if (!city || pending) return
    // A3: the address follows the view, replaced and never pushed, without a request to the server
    if (location.pathname + location.search !== here) window.history.replaceState(null, '', here)
  }, [here, city, pending])

  const toCity = (k: CityKey) => { setCityKey(k); setSelected(null); flown.current = null; setCaseSlug(null); setDeep(null) }
  // an audit pin is an SVG <g>, which Events' data-ev listener cannot read (no HTMLElement.dataset): it counts
  // itself; the send is fire-and-forget, the case opens at once
  const openPin = (slug: string) => {
    setCaseSlug(slug)
    track(EV.audit, { case: slug, from: 'atlas-map' })
  }
  const select = (s: Sector) => {
    if (wasDrag()) return
    flown.current = s.id   // clicked on the map: it is in view already
    setSelected(s)
    if (caseSlug) setCaseSlug(null)
  }
  const pick = (s: Sector | undefined) => { if (!s) return; setSelected(s); flyBox(bbox(s.d), 3.2); flown.current = s.id }
  const byId = useMemo(() => new Map((city?.sectors || []).map((s) => [s.id, s])), [city])
  const pickPoint = (p: Point, s?: Sector) => {
    if (s) { pick(s); return }
    const r = 40
    flyTo(fitBox({ x0: p.x - r, y0: p.y - r, x1: p.x + r, y1: p.y + r }, 1, true))
  }
  // cases.json holds every city's audits: only this city's opens here
  const openCase = q === 'change' && caseSlug ? cases?.find((c) => c.slug === caseSlug && c.city === cityKey) : undefined
  const otherCity = () => toCity(cityKey === 'brussels' ? 'antwerp' : 'brussels')
  const shown = q === 'place' && points ? points.points.filter((p) => p.t === obj).sort((a, b) => b.r - a.r) : []

  const hoverLine = (s: Sector): string => {
    if (q === 'need') return needStep(s, need, opt) == null ? t('tip.notMeasured') : needLabel(t, s, need, opt, loc)
    if (q === 'place') return t('tip.residents', { n: int(s.pop, loc) })
    if (communesOn) {
      const c = communeOf.get(s.id.slice(0, 5))
      return c?.green != null
        ? t('tip.commune', { name: placeName(c, loc), green: pct(c.green, 1, loc), exempt: c.exempt ? 'yes' : 'no' })
        : t('tip.communeUntested', { name: c ? placeName(c, loc) : '' })
    }
    if (builtOn) return changeTip(t, 'built', (s as Sector & { be?: number | null }).be, loc)
    return mode === 'raw' ? changeTip(t, 'raw', s.raw, loc) : changeTip(t, 'effect', s.ne, loc)
  }
  // the tip names a nameless sector by its code (common.sectorFallback)
  const label = (s: Sector) => sectorLabel(s, loc, (id) => tc('sectorFallback', { id }))
  const tip = hoverPt
    ? <><b>{tie(`${tc(`objects.one.${hoverPt.t}`)}${tc('sep.dot')}${tc('sep.rank', { n: String(hoverPt.r) })}`, loc)}</b>
        <span>{hoverPt.role === 'named' ? t('tip.named') : hoverPt.role === 'control' ? t('tip.control') : t('tip.further')}</span>
        <span className="mono">{hoverPt.s && byId.get(hoverPt.s) ? tie(label(byId.get(hoverPt.s)!), loc) : ''}</span></>
    : hovered && <><b>{tie(label(hovered), loc)}</b><span>{tie(sectorPlace(hovered, loc), loc)}</span><span className="mono">{hoverLine(hovered)}</span></>

  const credit = tie([
    q !== 'need' && t('credit.sentinel', { years: photosOn ? city!.photos!.years.join(tc('sep.list')) : city?.field?.year ? String(city.field.year) : 'none' }),
    q === 'need' && need === 'heat' && t('credit.landsat'),
    q === 'need' && need === 'r3' && t('credit.worldcover'),
    t('credit.statbel'), t('credit.osm'),
  ].filter(Boolean).join(tc('sep.dot')), loc)

  const ready = !!city && city.city === cityKey

  // ── the keyboard, screen readers and the map (re-check 2) ──────────────────────────────────────────────────────────
  // the part of the stage the cards leave free, in client pixels (as SwipeHandle measures it): left of an open drawer and
  // right of the panel on a wide screen, above the bottom sheets on a phone
  const freeArea = () => {
    const st = stageRef.current
    if (!st) return null
    const r = st.getBoundingClientRect()
    let l = r.left, rt = r.right, b = r.bottom
    const panel = st.querySelector(':scope > .panel'), drawer = st.querySelector(':scope > .drawer')
    if (matchMedia('(min-width: 861px)').matches) {
      if (panel) l = Math.max(l, panel.getBoundingClientRect().right)
      if (drawer) rt = Math.min(rt, drawer.getBoundingClientRect().left)
    } else for (const el of [panel, drawer]) if (el) b = Math.min(b, el.getBoundingClientRect().top)
    // and above the consent card while it is up (a pin flown into view must not land under it; WCAG 2.4.11)
    const cb = document.querySelector('.consent-banner')?.getBoundingClientRect()
    if (cb && cb.left < rt && cb.right > l) b = Math.min(b, cb.top)
    return { l, r: rt, t: r.top, b, x: (l + rt) / 2, y: (r.top + b) / 2 }
  }
  // the sector under the middle of the free map: what Enter opens (WCAG 2.1.1: the map's sectors were for the pointer only)
  const middleSector = (): Sector | null => {
    const f = freeArea(), g = svgRef.current?.querySelector('.sectors')
    if (!f || !g || !city) return null
    const hit = document.elementsFromPoint(f.x, f.y).find((el) => el.parentNode === g)
    return hit ? city.sectors[Array.prototype.indexOf.call(g.children, hit)] ?? null : null
  }
  // the map as a keyboard stop: arrows pan a tenth of the view, + and − zoom about the middle, Enter or Space opens the
  // sector there; while it has keyboard focus that sector is outlined and named in the tip (a status)
  const [mapKeys, setMapKeys] = useState(false)
  useEffect(() => { if (mapKeys) setHovered(middleSector()) }, [mapKeys, vb, city, q, lens]) // eslint-disable-line react-hooks/exhaustive-deps
  const svgProps = useMemo(() => ({
    tabIndex: 0,
    'aria-describedby': 'atlas-map-keys',
    // the keyboard's focus only: a click on the map focuses it too, and must not outline the middle
    onFocus: (e: FocusEvent<SVGSVGElement>) => { if (e.target === e.currentTarget && e.currentTarget.matches(':focus-visible')) setMapKeys(true) },
    onBlur: (e: FocusEvent<SVGSVGElement>) => { if (e.target === e.currentTarget) { setMapKeys(false); setHovered(null) } },
  }), [])
  const onMapKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if (e.target !== svgRef.current || e.altKey || e.ctrlKey || e.metaKey) return
    const arrow = ({ ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] } as Record<string, [number, number]>)[e.key]
    if (arrow) { e.preventDefault(); setMapKeys(true); panBy(arrow[0] * vb.w * 0.1, arrow[1] * vb.h * 0.1); return }
    const f = freeArea()
    if (f && ['+', '=', '-', '_'].includes(e.key)) { e.preventDefault(); setMapKeys(true); zoomAt(f.x, f.y, e.key === '-' || e.key === '_' ? 1.4 : 0.7) }
    else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      const s = middleSector()
      if (s) { flown.current = s.id; setSelected(s); if (caseSlug) setCaseSlug(null) }
    }
  }
  // an audit's pin reached by Tab under a card (the panel, a drawer, a phone's bottom sheet) is flown into the free map
  // (WCAG 2.4.11)
  const revealPin = (slug: string) => {
    const c = city?.cases.find((x) => x.slug === slug), f = freeArea(), ctm = svgRef.current?.getScreenCTM()
    if (!c || !f || !ctm) return
    const sx = ctm.a * c.x + ctm.e, sy = ctm.d * c.y + ctm.f
    if (sx > f.l + 24 && sx < f.r - 24 && sy > f.t + 24 && sy < f.b - 24) return
    flyTo({ ...vb, x: vb.x + c.x - (f.x - ctm.e) / ctm.a, y: vb.y + c.y - (f.y - ctm.f) / ctm.d })
  }
  // on a phone an open card covers the panel's sheet: its controls leave the Tab order while they cannot be seen
  // (WCAG 2.4.11)
  const [phone, setPhone] = useState(false)
  useEffect(() => {
    const m = matchMedia('(max-width: 860px)'), on = () => setPhone(m.matches)
    on(); m.addEventListener('change', on)
    return () => m.removeEventListener('change', on)
  }, [])
  const covered = phone && !!(selected || openCase)
  useEffect(() => {
    const p = stageRef.current?.querySelector<HTMLElement>(':scope > .panel')
    if (p) p.inert = covered
  })
  // the page's title names the view on screen, in the head's words (WCAG 2.4.2; the server's <title> named only the view
  // the page was opened on)
  useEffect(() => {
    if (!ready || pending) return
    const audit = caseSlug && city.cases.some((c) => c.slug === caseSlug) ? caseSlug : null
    document.title = atlasHeadWords({ state: { city: cityKey, q, obj }, lens: need, caseSlug: audit,
      sector: selected && { name: sectorName(selected, loc), place: sectorPlace(selected, loc) } }, t, tc, tl).title
  }, [ready, pending, cityKey, q, obj, need, caseSlug, selected]) // eslint-disable-line react-hooks/exhaustive-deps
  // a change of view is said once, by the panel's new heading (WCAG 4.1.3); the first view is the page itself
  const [said, setSaid] = useState('')
  const saidFirst = useRef(true)
  useEffect(() => {
    if (!ready) return
    const h = stageRef.current?.querySelector(':scope > .panel h1')?.textContent?.trim() ?? ''
    if (saidFirst.current) { saidFirst.current = false; return }
    setSaid(h)
  }, [ready, cityKey, q, need, lens, obj, measure])

  return (
    <div className="atlas" data-ready={ready ? 'true' : undefined}>
      <header className="atlas-bar">
        <a href={localePath(loc, '/')} className="wordmark" aria-label={plain(t('bar.home'))}>frondia</a>
        {/* the city as a pill with its pin (Sweatpals, DoorDash): a native select, so the keyboard, screen readers and
            a phone's own picker all work as they do everywhere */}
        <label className="city-pick">
          {icons.pin}
          <span className="sr-only">{t('bar.city')}</span>
          <select value={cityKey} onChange={(e) => toCity(e.target.value as CityKey)}>
            {/* an option never wraps: its soft hyphens (Ant\u00ADwer\u00ADpen) would only reach the screen reader */}
            {CITIES.map((k) => <option key={k} value={k}>{plain(tc(`cities.${k}`))}</option>)}
          </select>
          <span className="city-pick-mark" aria-hidden="true" />
        </label>
        {/* an audit belongs to "what changed": another question closes it, so a resize never pulls the view back to it */}
        <div className="seg seg--lens" role="group" aria-label={plain(t('bar.questions'))}>
          {QS.map((k) => (
            <button key={k} type="button" aria-pressed={q === k} onClick={() => { setQ(k); setHoverPt(null); if (k !== 'change') setCaseSlug(null) }}>
              {icons[k]}<span className="long">{t(`q.${k}.long`)}</span><span className="short">{t(`q.${k}.short`)}</span>
            </button>
          ))}
        </div>
        <div className="atlas-bar-end">
          <LanguageSwitcher />
          <a href={localePath(loc, '/') + '#threshold'}>{t('bar.decides')}</a>
        </div>
      </header>

      <main className="atlas-stage" id="main" ref={stageRef}>
        {city && (
          <div className="atlas-map" {...handlers} onKeyDown={onMapKey}>
            <SectorMap svgRef={svgRef} city={city} mode={mode} view={vb} selected={selected} hovered={hovered} activeCase={caseSlug ?? undefined}
                       onSelect={select} onHover={setHovered} showCases={q === 'change' && !communesOn}
                       field={q !== 'need' && !communesOn && !photosOn} photos={photosOn ? photoSrc : null}
                       fill={q === 'need' ? fill : q === 'place' || photosOn ? noFill : communesOn ? communeFill : builtOn ? sealFill : null}
                       fieldOpacity={q === 'change' && lens === 'field' ? 0.95 : FIELD_UNDER_DATA}
                       stroke={q === 'change' && lens === 'field' ? 'rgba(20,20,19,.18)' : q === 'place' ? 'rgba(20,20,19,.12)' : communesOn ? 'rgba(250,249,245,.35)' : photosOn ? 'rgba(250,249,245,.2)' : 'var(--paper)'}
                       className="atlas-svg" label={t('mapLabel', { city: tc(`cities.${city.city}`), n: String(city.sectors.length) })}
                       svgProps={svgProps}>
              <MapLayers city={city} q={q} communesOn={communesOn} caseSlug={caseSlug} vbw={vb.w} unitPx={unitPx}
                         labelFs={labelFs} pinR={pinR} pinFs={pinFs} leftLabel={leftLabel}
                         onCase={(slug) => { if (!wasDrag()) openPin(slug) }} onCaseKey={openPin} onCaseFocus={revealPin}
                         shown={shown} moreN={moreN} onHoverPoint={setHoverPt}
                         onPickPoint={(p) => { if (!wasDrag()) pickPoint(p, p.s ? byId.get(p.s) : undefined) }} />
            </SectorMap>
            {tip && <div className="atlas-tip" role="status">{tip}</div>}
            <p id="atlas-map-keys" hidden>{t('mapKeys')}</p>
          </div>
        )}

        {cityError && !city && (
          // A8: the old atlas stayed silent on a failed read (an empty stage); this one says so where the panel goes
          <section className="panel"><p className="small">{tc('unavailable')}</p><button type="button" className="link" onClick={() => location.reload()}>{t('reload')}</button></section>
        )}
        {photosOn && <SwipeHandle stageRef={stageRef} years={city!.photos!.years} />}
        {city && q === 'need' && (
          <NeedPanel city={city} lens={need} setLens={setNeedLens} opt={opt} setOpt={setOpt} onPick={pick} otherCity={otherCity} />
        )}
        {city && q === 'place' && (
          <PlacePanel city={city} points={points} pointsError={!!pointsError} obj={obj} setObj={setObj} onPick={pickPoint} n={moreN} setN={setMoreN} />
        )}
        {city && q === 'change' && (
          <ChangePanel city={city} lens={lens} setLens={setLens} measure={measure} setMeasure={setMeasure} control={control} setControl={setControl}
                       counts={counts} top={top} onPick={pick} onPickRegistered={pickRegistered} />
        )}

        {city && selected && !openCase && (
          <Passport s={selected} city={city} cases={city.cases} points={points} opt={opt}
                    onClose={() => { setSelected(null); setDeep(null) }} onOpenCase={(slug) => setCaseSlug(slug)} />
        )}
        {openCase && (
          <CaseDrawer c={openCase as unknown as DrawerCase} onClose={() => { setCaseSlug(null); flyTo(home) }} />
        )}

        <div className="zoom" role="group" aria-label={plain(t('zoom.group'))}>
          <button type="button" onClick={() => { const r = svgRef.current?.getBoundingClientRect(); if (r) zoomAt(r.left + r.width / 2, r.top + r.height / 2, 0.7) }} aria-label={plain(t('zoom.in'))}>+</button>
          <button type="button" onClick={() => { const r = svgRef.current?.getBoundingClientRect(); if (r) zoomAt(r.left + r.width / 2, r.top + r.height / 2, 1.4) }} aria-label={plain(t('zoom.out'))}>−</button>
          <button type="button" onClick={() => flyTo(home)} aria-label={plain(t('zoom.reset'))} className="mono">⤢</button>
        </div>
        {/* the map moves by a single tap too, not only by a drag (WCAG 2.5.7; re-check 2, 3 Oct; design wave, 5 Oct): four
            buttons, a fifth of the view each, as the arrow keys move a tenth; above the zoom on a wide screen, under it on
            a phone, or beside it where the sheet or a card leaves no room under it; left out only where neither fits
            (a short stage under 480 px wide: atlas.css) */}
        <div className="pan" role="group" aria-label={plain(t('pan.group'))}>
          {([['up', 0, -1], ['left', -1, 0], ['right', 1, 0], ['down', 0, 1]] as const).map(([k, x, y]) => (
            <button key={k} type="button" className={`pan-${k}`} aria-label={plain(t(`pan.${k}`))}
                    onClick={() => panBy(x * vb.w * 0.2, y * vb.h * 0.2)}>
              <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" style={{ transform: `rotate(${({ up: 0, right: 90, down: 180, left: 270 } as const)[k]}deg)` }}>
                <path d="M3.5 10 8 5.5 12.5 10" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          ))}
        </div>
        {/* every source on screen is credited: the field (change and place), Landsat (heat), ESA WorldCover's canopy
            (3-30-300; CC BY 4.0 asks for this wording) */}
        <p className="atlas-credit" lang={keptEnglish(loc)}>{credit}</p>
        <p className="sr-only" role="status">{said}</p>
      </main>
    </div>
  )
}
