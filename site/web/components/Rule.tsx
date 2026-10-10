import type { ReactNode } from 'react'

export function Rule({ n, children, right }: { n: number | string; children: ReactNode; right?: ReactNode }) {
  return (
    <div className="label-rule label reveal">
      <span>({n})</span><i /><span>{children}</span>{right && <><i /><span>{right}</span></>}
    </div>
  )
}
