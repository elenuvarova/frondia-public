import type { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Frondia',
    short_name: 'Frondia',
    start_url: '/',
    display: 'browser',
    background_color: '#F2EADE',
    theme_color: '#F3F0E7',
    icons: [
      { src: '/icon/0', sizes: '192x192', type: 'image/png' },
      { src: '/icon/1', sizes: '512x512', type: 'image/png' },
    ],
  }
}
