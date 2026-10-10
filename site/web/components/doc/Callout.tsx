import type { ReactNode } from 'react'

// A note inside a document (Notion's callout): a bold lead sentence running into the body, no
// border on screen — a rule above and below on paper (styles/dossier.css's @media print). Markup
// 1:1 with Dossier.jsx's Callout. `tone="warn"` is the only tone the dossier uses today
// (.doc-callout--warn); an empty tone renders the plain callout.
export function Callout({
  lead,
  children,
  tone = '',
}: {
  lead: ReactNode
  children?: ReactNode
  tone?: string
}) {
  return (
    <div className={`doc-callout${tone ? ` doc-callout--${tone}` : ''}`}>
      <p><strong>{lead}</strong> {children}</p>
    </div>
  )
}
