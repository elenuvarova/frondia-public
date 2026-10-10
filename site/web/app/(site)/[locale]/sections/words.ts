// Small counts are written as words ("Sixteen places grew"); the words come from the catalogue
// (landing.words), so each language spells its own.
export const inWords = (words: string[], k: number): string => words[k] ?? String(k)

// the background photographs: generated, a lilac bush panned sideways (docs/design/imagery) —
// the rustle as a picture; the measured field stays below, on the maps
export const LILAC = { src: 'photo/lilac-wind.webp', w: 2400, h: 1350 }
export const LILAC_PHONE = { src: 'photo/lilac-wind-phone.webp', w: 1080, h: 1920 }
export const LILAC_BAND = { src: 'photo/lilac-wind-band.webp', w: 2400, h: 1030 }
