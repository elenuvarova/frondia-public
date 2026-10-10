'use client'

// The dossier's one interactive control: the browser's own print dialog (A4, styles/dossier.css's
// @media print). The label comes from the server already tied, so this stays a button and no more.
export function PrintButton({ label }: { label: string }) {
  return <button type="button" className="pill pill--ink pill--sm" onClick={() => window.print()}>{label}</button>
}
