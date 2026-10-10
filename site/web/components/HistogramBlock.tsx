'use client'
import { useEffect, useState } from 'react'
import { NullHistogram, type Hist } from '@/components/NullHistogram'
import { int, signed } from '@/lib/format'
import { useT } from '@/lib/t-client'
import { plain } from '@/lib/typography'

function useMedia(q: string): boolean {
  // the server and the first client paint render wide; the effect corrects a phone once mounted
  const [on, setOn] = useState(false)
  useEffect(() => {
    const m = window.matchMedia(q), f = () => setOn(m.matches)
    f()
    m.addEventListener('change', f)
    return () => m.removeEventListener('change', f)
  }, [q])
  return on
}

interface HistogramBlockProps {
  hist: Hist
  thr: number
  city: string
  comparable: number
  mean: number
  marker?: number
}

// (3) the null distribution with its switch: effects against matched places, or change against its own past
export function HistogramBlock({ hist, thr, city, comparable, mean, marker }: HistogramBlockProps) {
  const { t, loc } = useT('landing')
  const [mode, setMode] = useState<'raw' | 'effect'>('effect')
  const narrow = useMedia('(max-width: 720px)')
  const n = int(comparable, loc)
  return (
    <div className="hist-block reveal">
      <div className="hist-head">
        <p className="label">{t(mode === 'effect' ? 'threshold.hist.effect' : 'threshold.hist.raw', { city, n })}</p>
        <div className="seg" role="group" aria-label={plain(t('threshold.hist.group'))}>
          <button type="button" aria-pressed={mode === 'raw'} onClick={() => setMode('raw')}>{t('threshold.hist.rawButton')}</button>
          <button type="button" aria-pressed={mode === 'effect'} onClick={() => setMode('effect')}>{t('threshold.hist.effectButton')}</button>
        </div>
      </div>
      <NullHistogram hist={hist} thr={thr} mode={mode} height={narrow ? 240 : 300} width={narrow ? 400 : 1200} loc={loc}
                     marker={marker == null ? undefined : { value: marker, label: t('threshold.hist.marker') }} />
      <p className="small hist-note">
        {mode === 'effect' ? t('threshold.hist.effectNote', { mean: signed(mean, 4, loc) }) : t('threshold.hist.rawNote')}
      </p>
    </div>
  )
}
