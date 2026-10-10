// The city's file starts downloading with the HTML: a nonced inline script in the page (earlyFetchScript, written by
// app/(atlas)/[locale]/atlas/page.tsx) begins the fetch and leaves its promise on window, and the first read
// (components/atlas/useJSON.ts load) adopts it.
// It replaced <link rel="preload" as="fetch">, which WebKit never hands to fetch(): Safari downloaded the city twice
// (re-check 1, 3 Oct). The script holds the same read as `load`, written as an ES5 string.
export const EARLY = '__frondiaEarly'
export function earlyFetchScript(url: string): string {
  const u = JSON.stringify(url).replace(/</g, '\\u003c')
  return `(function(){var u=${u},w=window,m=w.${EARLY}||(w.${EARLY}={}),p=fetch(u).then(function(r){if(!r.ok)throw new Error(u+": "+r.status);return r.json()});p.catch(function(){});m[u]=p})()`
}
