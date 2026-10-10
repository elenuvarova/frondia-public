import { fixed, int } from '@/lib/format'
import { getT } from '@/lib/t'
import type { City, Sector } from '@/lib/types'

const MEASURES = ['t24', 'n24', 'b24'] as const

// the sector's value against the city's median, on a scale to the city's maximum — markup 1:1 with
// Scale in site/apps/landing/src/pages/Dossier.jsx; the reading under each bar says it in words
export async function Scale({ s, city }: { s: Sector; city: City }) {
  const { t, loc } = await getT('dossier.scale')
  const med = city.dossier.medians
  return (
    <div className="doc-scale" role="list">
      {MEASURES.map((k) => {
        const max = Math.max(...city.sectors.map((x) => x[k] ?? 0))
        const v = Number(s[k])
        const share = v / med[k]
        const side = Math.abs(share - 1) < 0.05 ? 'at' : share < 1 ? 'below' : 'above'
        return (
          <div className="doc-scale-row" role="listitem" key={k}>
            <p className="doc-scale-name">{t(`rows.${k}`)}<small>{t('median')} {fixed(med[k], 3, loc)}</small></p>
            <span className="doc-scale-track" aria-hidden="true">
              <i style={{ width: `${(100 * v) / max}%` }} />
              <u style={{ left: `${(100 * med[k]) / max}%` }} />
            </span>
            <p className="doc-scale-v mono">{fixed(v, 3, loc)}</p>
            <p className="doc-scale-read">{t('reading', { side, p: int(Math.round(100 * Math.abs(share - 1)), loc) })}</p>
          </div>
        )
      })}
    </div>
  )
}
