'use client'
import { clearChoice, openConsent, safeStorage } from '@/lib/consent'

// A no-op fallback so the choice still gets cleared (dispatching `frondia:consent` with null) even if
// localStorage itself is unreachable — matches the fallback ConsentBanner uses for saveChoice.
const NOOP_STORAGE: Pick<Storage, 'removeItem'> = { removeItem() {} }

// The /privacy page's only interactive control: withdraws any saved choice and reopens the banner in
// this tab (openConsent → ConsentBanner listens via onOpenConsent), so a visitor can decide again.
export function ConsentReset({ label }: { label: string }) {
  return (
    <button
      type="button"
      className="pill pill--ghost"
      onClick={() => {
        clearChoice(safeStorage() ?? NOOP_STORAGE)
        openConsent()
      }}
    >
      {label}
    </button>
  )
}
