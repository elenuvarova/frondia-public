'use client'
import { NullHistogram } from '@/components/NullHistogram'
import { localePath } from '@/i18n/locales'
import { EV } from '@/lib/analytics'
import { fixed, int, pct, signed } from '@/lib/format'
import { sectorLabel, sectorPlace } from '@/lib/names'
import { MIN_RESIDENTS, SHOP_TYPES } from '@/lib/lenses'
import { caseHref } from '@/lib/links'
import { bbox } from '@/lib/atlas/geometry'
import type { AtlasCase, AtlasCity, AtlasPoints, Hist } from '@/lib/atlas/types'
import { km } from '@/lib/atlas/words'
import type { Sector } from '@/lib/types'
import { useT } from '@/lib/t-client'
import { Seq } from './bits'
import type { NeedOpt } from './NeedPanel'
import { useDrawerFocus } from './useDrawerFocus'
import { useMoreBelow } from './useMoreBelow'
import { tie, plain } from '@/lib/typography'

// the fields a sector page reads that lib/types.ts leaves in Sector's catch-all
type PassportSector = Sector & {
  fit?: Record<string, number> | null
  low?: Record<string, string[]> | null
  shop?: Record<string, number | null> | null
  r3?: number | null
  gap?: number | null
  be?: number | null
  bv?: string | null
}

const VERDICT: Record<string, string> = { up: 'up', down: 'down', noise: 'noise', refused: 'refused' }
const BUILT_WORDS = new Set(['up', 'down', 'noise', 'refused'])

interface PassportProps {
  s: Sector
  city: AtlasCity
  cases: AtlasCase[]
  points: AtlasPoints | null
  opt: NeedOpt
  onClose: () => void
  onOpenCase: (slug: string) => void
}

/* ── the sector page: the three questions, top to bottom (Atlas.jsx 188–290) ─────────────────── */
export function Passport({ s: sector, city, cases, points, opt, onClose, onOpenCase }: PassportProps) {
  const more = useMoreBelow<HTMLElement>()
  const head = useDrawerFocus<HTMLHeadingElement>(onClose, sector.id)
  const { t, loc } = useT('atlas')
  // rc('sep.dot') where a bare " · " sat between two values: t would tie its first space, which the English never had
  const { t: tc, raw: rc } = useT('common')
  const { t: tl, raw: rl } = useT('landing')
  const s = sector as PassportSector
  const name = tc(`cities.${city.city}`)
  // the card's heading: a nameless sector is called by its code (common.sectorFallback); its label, already "Sector {name}"
  // (passport.aria), takes the bare code
  const label = sectorLabel(s, loc, (id) => tc('sectorFallback', { id }))
  const thr = city.thresholds.ndvi
  const cls = (s.nv && VERDICT[s.nv]) || 'noise'
  const text = s.nv && VERDICT[s.nv] ? t(`verdict.${s.nv}`) : t('verdict.none')
  const k = s.ne != null ? Math.abs(s.ne) / thr : null
  const box = bbox(s.d)
  const caseHere = box ? cases.find((c) => c.x >= box.x0 && c.x <= box.x1 && c.y >= box.y0 && c.y <= box.y1) : undefined
  const here = (points?.points || []).filter((p) => p.s === s.id && p.r <= 20)
    .sort((a, b) => (a.role === 'named' ? 0 : 1) - (b.role === 'named' ? 0 : 1) || a.r - b.r)
  const scen = opt.scenario
  const hist = city.hist as Hist
  const place = caseHere && rl<Record<string, { place?: string }>>('cases')[caseHere.slug]?.place ? tl(`cases.${caseHere.slug}.place`) : caseHere?.name
  const built = s.bv && BUILT_WORDS.has(s.bv) ? s.bv : 'none'
  return (
    <aside className="drawer" ref={more} aria-label={plain(t('passport.aria', { name: sectorLabel(s, loc, (id) => id) }))}>
      <div className="drawer-head">
        <Seq className="label" text={t('passport.head', { id: s.id, commune: sectorPlace(s, loc) })} />
        <button type="button" className="drawer-x" onClick={onClose} aria-label={plain(t('passport.close'))}>×</button>
      </div>
      <h2 className="display-s" ref={head} tabIndex={-1}>{tie(label, loc)}</h2>
      <p className="mono drawer-people">{t('passport.people', { n: int(s.pop, loc), inc: s.inc ? int(s.inc, loc) : 'none' })}</p>
      {/* the printable dossier lives in the site's other layout (a document, in its system): a full load */}
      {s.t24 != null && (
        <a className="pill pill--sm pill--line drawer-dossier" href={`${localePath(loc, '/dossier')}?city=${city.city}&sector=${s.id}`}>
          {t('passport.dossier')} <span className="arr">→</span>
        </a>
      )}

      <section className="drawer-part">
        <h3 className="part-title">{t('q.need.long')}</h3>
        {(s.pop || 0) < MIN_RESIDENTS && (
          <p className="small">{t('passport.few', { min: String(MIN_RESIDENTS) })}</p>
        )}
        <dl className="passport">
          {s.fit && (
            <div className="wide"><dt className="label">{t('passport.services', { scenario: t(`need.scenario.${scen}`) })}</dt>
              <dd><span className="mono big">{int(s.fit[scen], loc)}</span><span className="small"> {t('passport.servicesValue', { list: (s.low?.[scen] ?? []).map((x) => t(`need.service.${x}`)).join(tc('sep.list')) })}</span></dd></div>
          )}
          {s.shop && SHOP_TYPES.map((sh) => (
            <div key={sh}><dt className="label">{t('passport.nearest', { shop: sh })}</dt><dd className="mono">{km(t, s.shop![sh], loc)}</dd></div>
          ))}
          {s.hot != null && <div><dt className="label">{t('passport.heat')}</dt><dd className="mono">{t('passport.heatValue', { v: signed(s.hot, 1, loc) })}</dd></div>}
          {s.cs != null && <div><dt className="label">{t('passport.canopy')}</dt><dd className="mono">{pct(s.cs, 0, loc)}</dd></div>}
          {s.r3 != null && <div><dt className="label">{t('passport.r3')}</dt><dd className="mono">{t(`passport.r3Value.${s.r3}`)}</dd></div>}
          {s.kid != null && <div><dt className="label">{t('passport.ages')}</dt><dd className="mono">{pct(s.kid, 0, loc)}{rc<string>('sep.dot')}{pct(s.old, 0, loc)}</dd></div>}
        </dl>
      </section>

      <section className="drawer-part">
        <h3 className="part-title">{t('q.place.long')}</h3>
        {here.length ? (
          <ul className="proposals">
            {here.map((p) => (
              <li key={`${p.t}-${p.r}`}><i className={`pt pt-${p.role || 'more'}`} />
                <span>{tc(`objects.one.${p.t}`)}</span>
                <span className="mono">{tc('sep.rank', { n: String(p.r) })}{p.role === 'named' ? t('passport.role.named') : p.role === 'control' ? t('passport.role.control') : ''}</span></li>
            ))}
          </ul>
        ) : <p className="small">{t('passport.noProposals')}</p>}
      </section>

      <section className="drawer-part">
        <h3 className="part-title">{t('q.change.long')}</h3>
        <span className={`chip chip--${cls}`}><i />{text}</span>
        <dl className="passport">
          <div className="wide"><dt className="label">{t('passport.effect')}</dt>
            <dd><span className="mono big">{signed(s.ne, 3, loc)}</span>
              {k != null && s.nv !== 'refused' && <span className="small"> {t('passport.times', { k: fixed(k, 1, loc), thr: fixed(thr, 3, loc) })}</span>}</dd></div>
          <div><dt className="label">{t('passport.raw')}</dt><dd className="mono">{signed(s.raw, 3, loc)}</dd></div>
          <div><dt className="label">{t('passport.gap')}</dt><dd className="mono">{signed(s.gap, 3, loc)}</dd></div>
          <div><dt className="label">{t('passport.veg')}</dt><dd className="mono">{fixed(s.n24, 3, loc)}</dd></div>
          <div><dt className="label">{t('passport.canopy24')}</dt><dd className="mono">{fixed(s.t24, 3, loc)}</dd></div>
          {s.be != null && city.built && (
            <div className="wide"><dt className="label">{t('built.passport')}</dt>
              <dd><span className="mono">{signed(s.be, 3, loc)}</span>
                <span className="small"> {t('passport.builtValue', { word: t(`built.word.${built}`), refused: s.bv === 'refused' ? 'yes' : 'no', thr: fixed(city.built.threshold, 3, loc) })}</span></dd></div>
          )}
        </dl>
        <div className="drawer-hist">
          <p className="label">{t('passport.where')}</p>
          <NullHistogram hist={hist} thr={thr} height={150} compact showAxis loc={loc}
                         label={t('passport.histAria', { city: name, v: signed(s.ne, 3, loc) })} />
          {s.ne != null && (
            <span className="drawer-pin" style={{ left: `${Math.min(100, Math.max(0, ((s.ne - hist.lo) / (hist.hi - hist.lo)) * 100))}%` }}>
              <i />{signed(s.ne, 3, loc)}
            </span>
          )}
        </div>
        <p className="small">
          {s.nv == null
            ? t('passport.notMeasured')
            : s.nv === 'refused'
            ? t('passport.refused')
            : t('passport.compared', { before: city.window.split('→')[0]!.trim(), noise: s.nv === 'noise' ? 'yes' : 'no' })}
        </p>
        {caseHere && (
          <a href={caseHref(loc, { city: city.city, slug: caseHere.slug })} className="pill pill--sm pill--ink"
             data-ev={EV.audit} data-ev-case={caseHere.slug} data-ev-from="atlas-passport"
             onClick={(e) => {
               // a modified or middle click opens the audit's own address, in a new tab or window
               if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
               e.preventDefault(); onOpenCase(caseHere.slug)
             }}>
            {t('passport.audit', { place: place ?? caseHere.name })} <span className="arr">→</span>
          </a>
        )}
      </section>
    </aside>
  )
}
