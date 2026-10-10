import type { MetadataRoute } from 'next'
import { siteUrl } from '@/lib/site'

// rendered per request: SITE_URL is read from the running container, not frozen at build time
export const dynamic = 'force-dynamic'

export default function robots(): MetadataRoute.Robots {
  const site = siteUrl()
  return { rules: { userAgent: '*', allow: '/' }, sitemap: `${site}/sitemap.xml` }
}
