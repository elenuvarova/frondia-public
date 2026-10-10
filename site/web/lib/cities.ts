// The five cities, in the order the site lists them everywhere (CITY_NAMES in
// site/packages/shared/content/en.js). cityOf mirrors that file's own cityOf: anything that is not
// one of the five keys — missing, misspelled, a stray query value — resolves to 'brussels', not an
// error, because every document page opens with a city even when the address is wrong.
export const CITIES = ['brussels', 'antwerp', 'ghent', 'liege', 'charleroi'] as const
export type CityKey = (typeof CITIES)[number]

const isCityKey = (x: string): x is CityKey => (CITIES as readonly string[]).includes(x)

export function cityOf(key: string | null | undefined): CityKey {
  return key != null && isCityKey(key) ? key : 'brussels'
}
