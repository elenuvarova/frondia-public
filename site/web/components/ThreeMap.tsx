'use client'
import { useCallback, type ReactNode } from 'react'
import { needFill } from '@/lib/lenses'
import type { City, Sector } from '@/lib/types'
import { FIELD_UNDER_DATA, SectorMap } from './SectorMap'

/* The landing's three mini-maps, from the atlas's own component and data: the product shown as
   itself. Client-side because two of them colour sectors with a function, and a function cannot
   travel from a server component to a client one. */
export function ThreeMap({ city, kind, label, children }: {
  city: City
  kind: 'need' | 'place' | 'change'
  label: string
  children?: ReactNode
}) {
  const need = useCallback((s: Sector) => needFill(s, 'services', { scenario: 'family' }), [])
  const none = useCallback(() => null, [])
  if (kind === 'need') return <SectorMap city={city} field={false} fill={need} label={label} />
  if (kind === 'place') {
    return (
      <SectorMap city={city} fill={none} fieldOpacity={FIELD_UNDER_DATA} stroke="rgba(29,29,27,.1)" label={label}>
        {children}
      </SectorMap>
    )
  }
  return <SectorMap city={city} mode="effect" label={label} />
}
