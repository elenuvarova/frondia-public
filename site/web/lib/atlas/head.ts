import type { TValues } from '@/lib/icu'

// what the head reads of a view: the server's AtlasResolved, or the atlas's own state on the client
export interface HeadView {
  state: { city: string; q: string; obj: string }
  lens: string
  caseSlug: string | null
  sector: { name: string; place: string } | null   // already in the page's language (lib/names.ts): '' is no name
}

// The words of a view's head: for a link opened afresh (lib/seo.ts, the server's <title>), and since re-check 2 for every
// view the atlas shows, which sets document.title with them (WCAG 2.4.2: a page that kept "Atlas · Brussels" while it
// showed Ghent named the wrong page; the plan's A3 had left the title alone on clicks). An audit of this city names its
// place; else a sector with a name, its name (five Brussels sectors have none, and Liège's 62063L0AP is "None": they fall
// through); else the question's lens or object; else the city alone. `t` reads atlas, `tc` common, `tl` landing.
type Tr = (key: string, values?: TValues) => string
export function atlasHeadWords(r: HeadView, t: Tr, tc: Tr, tl: Tr): { title: string; description: string } {
  const city = tc(`cities.${r.state.city}`)
  if (r.caseSlug) {
    return { title: t('meta.titleCase', { place: tl(`cases.${r.caseSlug}.place`) }), description: tl(`cases.${r.caseSlug}.story`) }
  }
  if (r.sector?.name) {
    const { name, place } = r.sector
    return { title: t('meta.titleView', { view: name, city }), description: t('meta.sectorDescription', { name, commune: place, city }) }
  }
  const description = t('meta.description')
  if (r.state.q === 'need') return { title: t('meta.titleView', { view: t(`need.lenses.${r.lens}.title`), city }), description }
  if (r.state.q === 'place') return { title: t('meta.titleView', { view: tc(`objects.many.${r.state.obj}`), city }), description }
  return { title: t('meta.title', { city }), description }
}
