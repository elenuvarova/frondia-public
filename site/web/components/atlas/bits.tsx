'use client'
import type { ReactNode } from 'react'
import { LanguageSwitcher } from '@/components/LanguageSwitcher'
import { plain } from '@/lib/typography'

// The atlas's small controls, ported from site/apps/atlas/src/pages/Atlas.jsx (141–185, 643–645): markup and
// classes as there; the words come in as props from the panels, which read them from the catalogue.

export function Toggle({ on, onChange, children }: { on: boolean; onChange: (on: boolean) => void; children: ReactNode }) {
  return (
    <button type="button" role="switch" aria-checked={on} className={`switch ${on ? 'on' : ''}`} onClick={() => onChange(!on)}>
      <span className="switch-track"><span className="switch-knob" /></span>
      <span>{children}</span>
    </button>
  )
}

export type Options = readonly (readonly [string, string])[]

export function Chips({ label, value, options, onChange }: { label: string; value: string; options: Options; onChange: (k: string) => void }) {
  return (
    <div className="chips" role="group" aria-label={plain(label)}>
      {options.map(([k, text]) => (
        <button key={k} type="button" aria-pressed={k === value} onClick={() => onChange(k)}>{text}</button>
      ))}
    </div>
  )
}

// a second choice inside a lens, or one among many: one row, the name left and the value with a caret
// right (Mapbox Studio's style panel). A native select, so a phone opens its own picker.
export function Choice({ label, value, options, onChange }: { label: string; value: string; options: Options; onChange: (k: string) => void }) {
  return (
    <label className="choice">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map(([k, text]) => <option key={k} value={k}>{plain(text)}</option>)}
      </select>
      <i className="caret" aria-hidden="true" />
    </label>
  )
}

/* parts joined by " · ": a part that wraps to the next line leaves its dot behind (atlas.css .seq). The
   translator ties the space before "·" into a no-break space, so the split takes any space (\s holds U+00A0). */
export function Seq({ text, className }: { text: string; className: string }) {
  return <p className={`${className} seq-wrap`}><span className="seq">{text.split(/\s·\s/).map((t, i) => <span key={i}>{t}</span>)}</span></p>
}

// the panel's kicker (the question it answers) with the language switch beside it, small, above the city's name. CSS
// shows the switch only where the bar has none: on a phone, where the panel is the bottom sheet (Elena, 5 Oct 2026), and
// from 861 to 1 019 px, where the bar has no room for it. The same LanguageSwitcher as the site's, so it keeps the view
export function PanelKicker({ children }: { children: ReactNode }) {
  return (
    <div className="panel-kicker">
      <p className="label">{children}</p>
      <LanguageSwitcher className="lang--sheet" />
    </div>
  )
}
