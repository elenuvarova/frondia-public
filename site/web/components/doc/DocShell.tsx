// The document pages' styles (dossier, commune, data, register — plan 3): imported here, not in the
// root layout, so dossier.css's `@media print` rules (a `:root`/`body` reset and hiding
// `.nav`/`.footer`) only ship to pages that render DocShell. React 19 keeps a stylesheet once
// inserted, so after a client-side move from here to the landing the rules stay in the document:
// each is scoped to `main.doc` (`:root:has(main.doc)`, `.doc …`), and prints nothing away from it.
// The four are still scoped on screen by page classes (`.doc`, `.data-…`, `.reg-…`), so the import
// order among themselves doesn't matter.
import '@/styles/dossier.css'
import '@/styles/commune.css'
import '@/styles/data.css'
import '@/styles/register.css'
import type { ReactNode } from 'react'
import { Footer } from '@/components/Footer'
import { Nav } from '@/components/Nav'

// The document pages' shell (dossier, commune, data, register): the same Nav and Footer as every
// other page, the body between them a `.doc` column (styles/dossier.css sets its width and rhythm).
// No `home` override: Footer's own default (`localePath(loc, '/')`) leads home in the page's
// language, same as every other page's shell. A page may add its own class to the column (the
// register's `.reg`, which its styles are scoped under), as the old pages did on <main>.
export async function DocShell({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <>
      <Nav />
      <main className={className ? `doc wrap ${className}` : 'doc wrap'} id="main">{children}</main>
      <Footer />
    </>
  )
}
