'use client'
import { useEffect, useState } from 'react'
import { useRouter } from '@/i18n/navigation'
import type { CityKey } from '@/lib/cities'
import { plain } from '@/lib/typography'

/* The city on the data page, as the atlas picks it: a pill over a native select (Sweatpals, DoorDash),
   1:1 with the select in site/apps/landing/src/pages/Data.jsx. Choosing a city replaces the address
   (/data?city=…, through next-intl's router, so the language prefix stays) without moving the page,
   and the server sends that city's layers. The select shows the choice at once, not only when the
   new page arrives. Its words come from the server (the page's own catalogue), as props: the browser
   is sent only the few words the layout picks (lib/client-messages.ts). */
export function CitySelect({ city, label, options }: { city: CityKey; label: string; options: { key: CityKey; name: string }[] }) {
  const router = useRouter()
  const [value, setValue] = useState<CityKey>(city)
  useEffect(() => { setValue(city) }, [city])
  return (
    <label className="city-pick">
      <span className="sr-only">{label}</span>
      <select value={value} onChange={(e) => {
        const next = e.target.value as CityKey
        setValue(next)
        router.replace(`/data?city=${next}`, { scroll: false })
      }}>
        {/* an option never wraps: its soft hyphens (Ant\u00ADwer\u00ADpen) would only reach the screen reader */}
        {options.map((o) => <option key={o.key} value={o.key}>{plain(o.name)}</option>)}
      </select>
      <span className="city-pick-mark" aria-hidden="true" />
    </label>
  )
}
