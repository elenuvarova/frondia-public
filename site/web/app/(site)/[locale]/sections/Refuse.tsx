import { Icon } from '@/components/Icon'
import { Rule } from '@/components/Rule'
import { fixed, signed } from '@/lib/format'
import { getT } from '@/lib/t'
import type { Facts, Sector } from '@/lib/types'

type Key = 'cooling' | 'refused' | 'monitoring' | 'restorations' | 'cause'
const ICON: Record<Key, string> = { cooling: 'thermometer', refused: 'compare', monitoring: 'calendar', restorations: 'tree', cause: 'document' }

// (6) What Frondia refuses to claim: each refusal with how often it fired on real data
export async function Refuse({ facts, zav }: { facts: Facts; zav?: Sector }) {
  const { t, rich, raw, loc } = await getT('landing')
  const mon = facts.monitoring
  const cand = mon.reduce((a, m) => a + m.candidates, 0)
  const conf = mon.reduce((a, m) => a + m.confirmed, 0)
  const cons = mon.reduce((a, m) => a + m.construction, 0)
  const nums: Record<Key, [string, string]> = {
    cooling: [t('refuse.nums.cooling', { v: fixed(facts.lst_threshold_c, 2, loc) }), t('refuse.nums.coolingLabel')],
    refused: [t('of', { k: String(facts.parks.refused), n: String(facts.parks.total) }), t('refuse.nums.refusedLabel')],
    monitoring: [t('of', { k: String(conf), n: String(cand) }), t('refuse.nums.monitoringLabel', { cons: String(cons) })],
    restorations: [String(facts.restorations_noise), t('refuse.nums.restorationsLabel')],
    cause: [zav ? signed(zav.ne, 3, loc) : '—', t('refuse.nums.causeLabel')],
  }
  return (
    <section id="refuse" className="section night grain">
      <div className="wrap">
        <Rule n={7} right={t('refuse.ruleRight')}>{t('refuse.rule')}</Rule>
        <div className="split reveal">
          <h2 className="display-l">{rich('refuse.title', { em: (c) => <em>{c}</em> })}</h2>
          <p className="body">{t('refuse.body')}</p>
        </div>
        <ul className="refusals">
          {raw<{ key: Key }[]>('refusals').map((r, i) => (
            <li key={r.key} className="reveal">
              <div className="refusal-num"><span className="num-l">{nums[r.key][0]}</span><span className="label">{nums[r.key][1]}</span></div>
              <div className="refusal-head"><Icon name={ICON[r.key]} size={30} /><h3 className="display-s">{t(`refusals.${i}.head`)}</h3></div>
              <p className="body">{t(`refusals.${i}.text`)}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
