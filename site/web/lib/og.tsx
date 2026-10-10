// The one drawing the tab icons and the og card share: an instrument (a font read straight off
// disk — Satori, next/og's renderer, reads WOFF/TTF/OTF, never WOFF2, so a plain .woff is read
// directly, not the *.css that ships to the browser) and the brand's own palette.
// The two faces are copied into assets/fonts (from @fontsource, OFL) rather than read via
// require.resolve('@fontsource/...'): both webpack and Turbopack trace a require.resolve() call
// as an import and then try to parse the binary .woff as a JS module ("Module parse failed" /
// "Unknown module type") — a plain fs path under this app's own root never enters that graph, the
// same reason Next's own next/og docs read a local font file with plain path.join(process.cwd(), …).
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { ImageResponse } from 'next/og'

export const NIGHT = '#0F4E37'
export const CREAM = '#F2EADE'
export const INK = '#1D1D1B'

async function readFontBuffer(fileName: string): Promise<ArrayBuffer> {
  const buf = await readFile(path.join(process.cwd(), 'assets/fonts', fileName))
  return buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength) as ArrayBuffer
}

export const instrumentSerif = (): Promise<ArrayBuffer> => readFontBuffer('instrument-serif-400.woff')
export const fragmentMono = (): Promise<ArrayBuffer> => readFontBuffer('fragment-mono-400.woff')

// the pre-cropped 1200×630 JPEG (public/photo/lilac-wind-og.jpg, made from lilac-wind.webp — Satori
// does not read WebP); this app's own public folder, so process.cwd() (the running workspace) is right
export async function ogPhoto(): Promise<string> {
  const file = await readFile(path.join(process.cwd(), 'public/photo/lilac-wind-og.jpg'))
  return `data:image/jpeg;base64,${file.toString('base64')}`
}

/** The wordmark, the one shape the tab icons draw: an "f" in Instrument Serif, cream on night.
 *  Shared by app/icon.tsx and app/apple-icon.tsx so each is a one-line call at its own size. */
export async function wordmarkIcon(size: number): Promise<ImageResponse> {
  const serif = await instrumentSerif()
  return new ImageResponse(
    (
      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: NIGHT }}>
        <span style={{ fontFamily: 'Instrument Serif', fontSize: Math.round(size * 0.62), color: CREAM, lineHeight: 1 }}>f</span>
      </div>
    ),
    { width: size, height: size, fonts: [{ name: 'Instrument Serif', data: serif, style: 'normal', weight: 400 }] },
  )
}

/** The og card: the lilac photo full-bleed, the wordmark top-left of the frame, a cream card
 *  centred with the kicker (mono) and the title (serif). Called once per published language —
 *  app/og/[file]/route.ts passes each string already in that language and re-encodes it as JPEG. */
export async function ogCard({ kicker, title, photo }: { kicker: string; title: string; photo: string }): Promise<ImageResponse> {
  const [serif, mono] = await Promise.all([instrumentSerif(), fragmentMono()])
  return new ImageResponse(
    (
      <div style={{ width: '100%', height: '100%', display: 'flex', position: 'relative', background: NIGHT }}>
        {/* Satori doesn't resolve the `inset` shorthand — top/right/bottom/left, spelled out */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={photo} width={1200} height={630} style={{ position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
        {/* a cream chip, ink text — the card's own colours, so the mark holds up over the photo
            instead of nearly vanishing (cream text had barely any contrast on the lighter greens) */}
        <div style={{ position: 'absolute', top: 32, left: 32, display: 'flex', alignItems: 'center', background: CREAM, color: INK, fontFamily: 'Instrument Serif', fontSize: 28, lineHeight: 1, padding: '10px 22px', borderRadius: 14 }}>
          frondia
        </div>
        <div style={{ position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18, background: CREAM, color: INK, padding: '40px 64px', borderRadius: 24, maxWidth: 840 }}>
            <div style={{ display: 'flex', fontFamily: 'Fragment Mono', fontSize: 20, letterSpacing: '0.02em' }}>{kicker}</div>
            <div style={{ display: 'flex', fontFamily: 'Instrument Serif', fontSize: 84, lineHeight: 1, textAlign: 'center' }}>{title}</div>
          </div>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
      fonts: [
        { name: 'Instrument Serif', data: serif, style: 'normal', weight: 400 },
        { name: 'Fragment Mono', data: mono, style: 'normal', weight: 400 },
      ],
    },
  )
}
