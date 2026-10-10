'use client'
import { fixed, int, signed } from '@/lib/format'
import { sectorName } from '@/lib/names'
import type { Case } from '@/lib/types'
import { useT } from '@/lib/t-client'
import { Seq } from './bits'
import { useDrawerFocus } from './useDrawerFocus'
import { useMoreBelow } from './useMoreBelow'
import { tie, plain } from '@/lib/typography'

// the fields of an audit the drawer reads that lib/types.ts leaves loose (Case.controls is unknown[])
interface Control { id: string; name: string; name_nl?: string; name_fr?: string; dist_km?: number | null }
export type DrawerCase = Omit<Case, 'controls'> & { controls: Control[] }

// an audit, opened from its pin or from a sector page; its words are the landing's (landing.cases.<slug>)
// (Atlas.jsx 749–776)
export function CaseDrawer({ c, onClose }: { c: DrawerCase; onClose: () => void }) {
  const more = useMoreBelow<HTMLElement>()
  const head = useDrawerFocus<HTMLHeadingElement>(onClose, c.slug)
  const { t, loc } = useT('atlas')
  const { t: tl } = useT('landing')
  const place = tl(`cases.${c.slug}.place`)
  const nd = c.instruments[0]!
  const above = c.series.seasons.filter((p) => p.effect > c.series.threshold).length
  return (
    <aside className="drawer" ref={more} aria-label={plain(t('case.aria', { place }))}>
      <div className="drawer-head">
        <Seq className="label" text={t('case.head', { city: tl(`cases.${c.slug}.city`), completed: String(c.completed) })} />
        <button type="button" className="drawer-x" onClick={onClose} aria-label={plain(t('case.close'))}>×</button>
      </div>
      <h2 className="display-s" ref={head} tabIndex={-1}>{place}</h2>
      <span className="chip chip--up"><i />{t('verdict.up')}</span>
      <dl className="passport">
        <div className="wide"><dt className="label">{t('case.effect', { n: String(c.controls.length) })}</dt>
          <dd><span className="mono big">{signed(nd.effect, 3, loc)}</span><span className="small"> {t('case.threshold', { thr: fixed(nd.threshold, 3, loc) })}</span></dd></div>
        {c.defensible_effect != null && <div className="wide"><dt className="label">{t('case.defensible')}</dt><dd className="mono">{signed(c.defensible_effect, 3, loc)}</dd></div>}
        <div><dt className="label">{t('case.footprint')}</dt><dd className="mono">{t('units.ha', { v: fixed(c.area_ha, 2, loc) })}</dd></div>
        <div><dt className="label">{t('case.above')}</dt><dd className="mono">{t('case.aboveValue', { k: int(above, loc), n: int(c.series.seasons.length, loc) })}</dd></div>
      </dl>
      <p className="small">{tl(`cases.${c.slug}.reading`)}</p>
      <p className="label">{t('case.matched')}</p>
      <ol className="controls-list">
        {c.controls.map((x) => <li key={x.id}><span>{tie(sectorName({ n: x.name, n_nl: x.name_nl, n_fr: x.name_fr }, loc), loc)}</span><span className="mono">{t('units.km', { v: fixed(x.dist_km, 1, loc) })}</span></li>)}
      </ol>
    </aside>
  )
}
