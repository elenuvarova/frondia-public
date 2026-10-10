// The tab icon: 192 (Android/PWA minimum) and 512 (its maskable/splash size), drawn once by
// lib/og.tsx's wordmarkIcon. Two sizes → /icon/0 (192) and /icon/1 (512), read by manifest.ts.
import type { ImageResponse } from 'next/og'
import { wordmarkIcon } from '@/lib/og'

export const runtime = 'nodejs'
export const contentType = 'image/png'

export function generateImageMetadata() {
  return [
    { id: 0, size: { width: 192, height: 192 }, contentType: 'image/png' },
    { id: 1, size: { width: 512, height: 512 }, contentType: 'image/png' },
  ]
}

export default async function Icon({ id }: { id: Promise<string | number> }): Promise<ImageResponse> {
  // the id comes back through the URL segment (/icon/0, /icon/1), so it reads back as the string
  // "1" even though generateImageMetadata returned the number 1 — compare as a string
  const size = String(await id) === '1' ? 512 : 192
  return wordmarkIcon(size)
}
