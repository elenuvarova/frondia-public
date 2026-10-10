// Apple's own touch-icon size (180): the same wordmark as app/icon.tsx, one call.
import type { ImageResponse } from 'next/og'
import { wordmarkIcon } from '@/lib/og'

export const runtime = 'nodejs'
export const size = { width: 180, height: 180 }
export const contentType = 'image/png'

export default async function AppleIcon(): Promise<ImageResponse> {
  return wordmarkIcon(180)
}
