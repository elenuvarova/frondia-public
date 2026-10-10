import type { ReactNode } from 'react'

// A document section (dossier/commune/data/register): an eyebrow and a heading that travel together
// — on paper neither is left at the foot of a page — over whatever body the page hands it. Markup
// 1:1 with the Section in site/apps/landing/src/pages/Dossier.jsx; styled by styles/dossier.css
// (.doc-sec, .doc-sec--wide, .doc-sec-head, .doc-h2), shared by all four document pages.
export function Section({
  id,
  eyebrow,
  title,
  children,
  wide = false,
}: {
  id: string
  eyebrow: ReactNode
  title: ReactNode
  children?: ReactNode
  wide?: boolean
}) {
  return (
    <section className={`doc-sec${wide ? ' doc-sec--wide' : ''}`} aria-labelledby={`${id}-h`} id={id}>
      <header className="doc-sec-head">
        <p className="label">{eyebrow}</p>
        <h2 id={`${id}-h`} className="doc-h2">{title}</h2>
      </header>
      {children}
    </section>
  )
}
