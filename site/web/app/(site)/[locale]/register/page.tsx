import type { Metadata } from 'next'
import { hasLocale } from 'next-intl'
import { getTranslations, setRequestLocale } from 'next-intl/server'
import { notFound } from 'next/navigation'
import type { ReactNode } from 'react'
import { DocShell } from '@/components/doc/DocShell'
import { Section } from '@/components/doc/Section'
import { RecordLink, RegisterFilters, type Tab } from '@/components/RegisterFilters'
import { routing } from '@/i18n/routing'
import { EV } from '@/lib/analytics'
import { downloadPath } from '@/lib/downloads'
import { int, pct, type Locale } from '@/lib/format'
import { indexable, REGISTER_CITY, REGISTER_FILES, registerQuery, resolveRegister } from '@/lib/register'
import { counts, kindOf, refOf, shownOf, type Search as RegisterSearch, type Show } from '@/lib/register-view'
import { docMetadata } from '@/lib/seo'
import { count, type TValues } from '@/lib/icu'
import { getT } from '@/lib/t'
import { tie } from '@/lib/typography'
import type { Register, RegisterContract, RegisterEval, RegisterLabels, RegisterRate } from '@/lib/types'

/* The register of interventions read by a language model (phase 2b, docs/07-unified-frondia.md): every
   neighbourhood contract with the words its label rests on, and how often the reading is wrong against
   30 contracts labelled by hand — or, while no person who reads French is at hand, read again by a
   second model, whose labels are never presented as a person's. Numbers from register.json
   (scripts/site/register.py), read on the server. Word for word the Vite page
   (site/apps/landing/src/pages/Register.jsx), on the dossier's layout. References (Figma 124:2, rows
   29–33): Dovetail's highlights for a measure (the quote marked, its source above, its tags under
   it); Adaline's evaluation and Cohere's comparison with a baseline for the rate; the dossier's bar
   with a tick (Churnkey) for an interval; Braintrust's failing rows for the disagreements; Intercom
   Fin's three-step rating for the labels, drawn by form as the atlas's point roles (Forest): the fill
   carries the stronger one; Maze's result tabs with their counts for the filter. The filter is a view
   of this one page: every view is known by the bare /register. */

const PATH = '/register'
const CITY = REGISTER_CITY
const FILES = REGISTER_FILES

type Search = Promise<RegisterSearch>
type Params = Promise<{ locale: string }>
type T = (key: string, values?: TValues) => string

// the standfirst: every contract read, and what the check found (en.js REGISTER.lede)
function lede(t: T, d: Register, loc: Locale): string {
  const all = t('readAll', { total: int(d.contracts.length, loc) })
  const e = d.eval
  const check = e ? t(`ref.${refOf(d)}.lede`, { n: int(e.n, loc), k: int(e.model.error.k, loc) }) : t('notFinished')
  return t('lede', { all, check })
}

export async function generateMetadata({ params, searchParams }: { params: Params; searchParams: Search }): Promise<Metadata> {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  const [t, landingTitle, r] = await Promise.all([
    getTranslations({ locale, namespace: 'register' }),
    getTranslations({ locale, namespace: 'landing.meta' }).then((lt) => lt('title')),
    searchParams.then((q) => resolveRegister(q, locale)),
  ])
  const description = r.state === 'ok' ? lede(t, r.d, locale) : t('title')
  return docMetadata({ locale, path: PATH, query: registerQuery(), title: t('meta.title'), description, indexable: indexable(r), ogAlt: landingTitle })
}

export default async function RegisterPage({ params, searchParams }: { params: Params; searchParams: Search }) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) notFound()
  setRequestLocale(locale)
  const [{ t }, r] = await Promise.all([getT('register'), searchParams.then((q) => resolveRegister(q, locale))])
  // register.json unreadable: the one line the old page showed then (its "Loading…" never ended), in
  // the terse shape of the dossier's and the commune's own error — still 200, not indexed
  if (r.state === 'error') return <DocShell className="reg"><p className="doc-missing">{(await getT('common')).t('unavailable')}</p></DocShell>
  const loc: Locale = locale
  const d = r.d
  const K = refOf(d)
  const k = (key: string) => `ref.${K}.${key}`
  const x = (s: string) => tie(s, loc)

  return (
    <DocShell className="reg">
      <header className="doc-head">
        <p className="label">{t('kicker')}</p>
        <h1 className="display-l">{t('title')}</h1>
        <p className="lede doc-standfirst">{x(lede(t, d, loc))}</p>
        <dl className="doc-meta">
          {[
            [t('facts.contracts'), int(d.contracts.length, loc)],
            [t('facts.described'), int(d.contracts.filter((c) => c.described).length, loc)],
            [t('facts.readBy'), t('facts.reader')],
            [t(k('meta')), int(d.testset.n, loc)],
          ].map(([dt, dd]) => <div key={dt}><dt className="label">{dt}</dt><dd className="mono">{dd}</dd></div>)}
        </dl>
        <div className="doc-actions">
          {FILES.map((f) => (
            <a key={f.file} className="pill pill--ghost pill--sm" href={downloadPath(CITY, f.file)} download={f.name}
               data-ev={EV.download} data-ev-file={f.file} data-ev-city={CITY}>{t(f.key)} <span className="arr">↓</span></a>
          ))}
        </div>
      </header>

      <Body d={d} show={r.show} checked={r.checked} loc={loc} />
    </DocShell>
  )
}

async function Body({ d, show, checked, loc }: { d: Register; show: Show; checked: boolean; loc: Locale }) {
  const { t, raw } = await getT('register')
  const x = (s: string) => tie(s, loc)
  const K = refOf(d)
  const k = (key: string) => `ref.${K}.${key}`
  const ref = raw<Record<string, unknown>>(`ref.${K}`)
  const n = counts(d.contracts, checked)
  const shown = shownOf(d.contracts, show, checked)
  const e = d.eval
  const tabs: Tab[] = raw<{ k: Tab['k'] }[]>('list.filters').map(({ k: f }, i) => ({
    k: f, name: t(`list.filters.${i}.name`), n: int(n[f] || 0, loc), count: n[f] || 0,
  }))
  const limits = [...raw<string[]>('limits.items').map((_, i) => t(`limits.items.${i}`)), ...('limit' in ref ? [t(k('limit'))] : []), t('limits.last')]
  const dates = (ev: RegisterEval) => (ev.labelled_from === ev.labelled_to ? ev.labelled_from : t('dates', { from: ev.labelled_from, to: ev.labelled_to }))
  const colophon: [string, string, boolean][] = [
    [t('colophon.source.k'), t('colophon.source.v', { source: d.source, n: int(d.contracts.length, loc), fetched: d.fetched }), false],
    [t('colophon.reader.k'), t('colophon.reader.v', { to: d.read_to }), false],
    [t('colophon.prompt.k'), t('colophon.prompt.v', { version: d.version, prompt: d.prompt_sha, schema: d.schema_sha }), true],
    [t('colophon.check.k'), e ? t(k('colophon'), { n: int(e.n, loc), by: e.labelled_by, dates: dates(e) }) : t('colophon.check.v'), false],
    [t('colophon.files.k'), t('colophon.files.v'), false],
  ]

  return (
    <>
      <Section id="check" eyebrow={t(k('label'))} title={t(k('title'))} wide>
        {e ? <Check d={d} e={e} loc={loc} /> : <p>{t('check.pending')}</p>}
      </Section>

      {e && (
        <Section id="disagreements" eyebrow={t('miss.label')} title={t('miss.title')} wide>
          {e.disagreements.length ? (
            <ul className="reg-misses">
              {e.disagreements.map((m) => (
                <li className="reg-miss" key={m.id}>
                  <div className="reg-miss-head">
                    <h3 className="reg-name">{x(m.name)}</h3>
                    <RecordLink id={m.id}>{t('miss.quotes')} <span aria-hidden="true">↓</span></RecordLink>
                  </div>
                  <dl className="reg-miss-labels">
                    {[[t(k('ref')), m.gold], [t(k('first')), m.model], [t('miss.rule'), m.rule]].map(([dt, g]) => (
                      <div key={dt}><dt>{dt}</dt><dd className="mono">{t(`miss.short.${g}`)}</dd></div>
                    ))}
                  </dl>
                  {'refWhy' in ref && m.check_why && <p className="reg-miss-why"><span className="reg-miss-why-k">{t(k('refWhy'))}.</span> {x(m.check_why)}</p>}
                  <p className="reg-miss-why"><span className="reg-miss-why-k">{t(k('firstWhy'))}.</span> {x(m.model_why)}</p>
                </li>
              ))}
            </ul>
          ) : <p>{t(k('none'), { n: int(e.n, loc) })}</p>}
        </Section>
      )}

      <Section id="method" eyebrow={t('method.label')} title={t('method.title')}>
        <ul className="doc-limits">{raw<string[]>('method.rules').map((_, i) => <li key={i}>{t(`method.rules.${i}`)}</li>)}</ul>
      </Section>

      <Section id="register" eyebrow={t('list.label')} title={t('list.title')} wide>
        <RegisterFilters show={show} checked={checked} tabs={tabs} label={t('list.show')} only={t(k('only'))}
          live={t('list.count', { count: count(shown.length), n: int(shown.length, loc) })}>
          {shown.map((c) => <Contract key={c.id} c={c} L={d.labels} K={K} />)}
        </RegisterFilters>
      </Section>

      <Section id="limits" eyebrow={t('limits.label')} title={t('limits.title')}>
        <ul className="doc-limits">{limits.map((s) => <li key={s}>{s}</li>)}</ul>
      </Section>

      <footer className="doc-foot">
        <dl className="doc-colophon">
          {colophon.map(([dt, dd, mono]) => <div key={dt}><dt>{dt}</dt><dd className={mono ? 'mono' : undefined}>{dd}</dd></div>)}
        </dl>
      </footer>
    </>
  )
}

// the old page's pct() and range(): whole percents, the Wilson interval as "lo–hi%"
function rates(t: T, loc: Locale) {
  const range = (r: RegisterRate) => (r.ci95 ? t('range', { lo: int(r.ci95[0] * 100, loc), hi: int(r.ci95[1] * 100, loc) }) : '')
  const p = (v: number) => pct(v, 0, loc)
  return { range, p }
}

// the Wilson interval as a pale span on 0–100 %, the estimate as its tick
function Interval({ r }: { r: RegisterRate }) {
  return (
    <span className="doc-scale-track reg-int-track" aria-hidden="true">
      {r.n > 0 && <i style={{ left: `${r.ci95[0] * 100}%`, width: `${(r.ci95[1] - r.ci95[0]) * 100}%` }} />}
      {r.n > 0 && <u style={{ left: `${r.value * 100}%` }} />}
    </span>
  )
}

async function Check({ d, e, loc }: { d: Register; e: RegisterEval; loc: Locale }) {
  const { t, raw } = await getT('register')
  const K = refOf(d)
  const k = (key: string) => `ref.${K}.${key}`
  const { range, p } = rates(t, loc)
  const q = d.quotes
  const figs: [string, string][] = [
    [t(k('wrong')), t('of', { k: int(e.model.error.k, loc), n: int(e.n, loc) })],
    [t(k('missed')), t('of', { k: int(e.model.yes.fn, loc), n: int(e.model.yes.tp + e.model.yes.fn, loc) })],
    [t('check.quotesMissing'), t('of', { k: int(q.n - q.k, loc), n: int(q.n, loc) })],
  ]
  const readers = raw<{ who: 'model' | 'rule' }[]>('check.readers')
  const groups = raw<{ key: 'recall' | 'precision' | 'error' }[]>(k('groups'))
  const asof = t(k('asof'), {
    drawn: t('check.drawn', { n: int(d.testset.n, loc), seed: d.testset.seed, pool: int(d.testset.pool, loc) }),
    by: e.labelled_by,
    bars: t('check.bars'),
  })
  return (
    <>
      <dl className="doc-figures">
        {figs.map(([dt, v], i) => (
          <div key={dt}>
            <dt>{dt}</dt>
            <dd>{v}{i === 0 && <small>{t('check.interval', { pct: p(e.model.error.value), range: range(e.model.error) })}</small>}</dd>
          </div>
        ))}
      </dl>
      <div className="doc-scale reg-int">
        {groups.map(({ key }, gi) => {
          const m = e.model.yes[key], r = e.rule.yes[key]
          return (
            <div className="reg-int-group" key={key}>
              <p className="label reg-int-title">{t(`${k('groups')}.${gi}.title`)}</p>
              {readers.map(({ who }, ri) => {
                const v = who === 'model' ? m : r
                return (
                  <div className="doc-scale-row reg-int-row" key={who}>
                    <p className="doc-scale-name">{t(`check.readers.${ri}.name`)}<small>{t(`check.readers.${ri}.sub`)}</small></p>
                    <Interval r={v} />
                    <p className="doc-scale-v mono">
                      {t('of', { k: int(v.k, loc), n: int(v.n, loc) })}
                      <small>{v.n ? t('rate', { pct: p(v.value), range: range(v) }) : ''}</small>
                    </p>
                  </div>
                )
              })}
              <p className="doc-scale-read reg-int-read">{t(`${k('groups')}.${gi}.read`, { mk: int(m.k, loc), mn: int(m.n, loc), rk: int(r.k, loc), rn: int(r.n, loc) })}</p>
            </div>
          )
        })}
      </div>
      <p className="doc-asof">{tie(`${asof} ${t('check.quotesFound', { k: int(q.k, loc), n: int(q.n, loc) })}`, loc)}</p>
    </>
  )
}

// parts joined by " · ", none left at a line's end (the atlas's rule)
function Seq({ parts }: { parts: (string | null | undefined | false)[] }) {
  return <span className="seq-wrap"><span className="seq">{parts.filter(Boolean).map((s, i) => <span key={i}>{s}</span>)}</span></span>
}

async function Contract({ c, L, K }: { c: RegisterContract; L: RegisterLabels; K: 'model' | 'person' }) {
  const [{ t, raw, loc }, { t: tc }] = await Promise.all([getT('register'), getT('common')])
  const x = (s: string) => tie(s, loc)
  const kind = kindOf(c)
  // "Not described": the blank filter's own name, found by its key
  const blankName = t(`list.filters.${raw<{ k: string }[]>('list.filters').findIndex((f) => f.k === 'blank')}.name`)
  let body: ReactNode
  if (kind === 'blank') body = <p className="reg-note">{t('list.blank')}</p>
  else if (c.shown.length) {
    body = (
      <ul className="reg-quotes">
        {c.shown.map((m, i) => (
          <li key={i}>
            <p className="reg-q" lang="fr"><mark>{x(m.q)}</mark></p>
            <p className="mono reg-q-meta"><Seq parts={[x(L.status[m.status] ?? ''), x(m.kinds.map((y) => L.kind[y]).join(tc('sep.list'))), ...m.places.map(x)]} /></p>
          </li>
        ))}
      </ul>
    )
  } else body = <p className="reg-note">{t('list.empty')}</p>
  return (
    <article className="reg-row" id={`c${c.id}`} tabIndex={-1} aria-labelledby={`c${c.id}-h`}>
      <header className="reg-row-head">
        <h3 className="reg-name" id={`c${c.id}-h`}>{x(c.name)}</h3>
        <p className="mono reg-meta"><Seq parts={[x(c.commune), `${c.years[0]}–${c.years[1]}`]} /></p>
      </header>
      <div className="reg-row-body">
        <p className="reg-chips">
          <span className={`chip reg-chip reg-chip--${kind}`}><i aria-hidden="true" />{kind === 'blank' ? blankName : x(L.label[c.label] ?? '')}</span>
          {c.test && c.gold && <span className="mono reg-checked">{c.gold === c.label ? t(`ref.${K}.agree`) : t(`ref.${K}.differ`, { g: c.gold })}</span>}
        </p>
        {body}
        <div className="reg-foot">
          {kind !== 'blank' && (
            <details className="reg-why">
              <summary>{t('list.reason')}</summary>
              <p className="reg-why-text">{x(c.why)}</p>
            </details>
          )}
          <a className="reg-src" href={c.url} target="_blank" rel="noopener noreferrer">{t('list.source')} <span aria-hidden="true">↗</span></a>
        </div>
      </div>
    </article>
  )
}
