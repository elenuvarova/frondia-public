// A page that must not move: a capture or a comparison (?clean) or a reader who asked for reduced
// motion. Read on the client after mount (the server cannot know either), so the first paint is the
// moving version and the effect settles it — the same moment the old site decided it.
export function stillFromPage(): boolean {
  if (typeof window === 'undefined') return false
  return new URLSearchParams(window.location.search).has('clean')
    || window.matchMedia('(prefers-reduced-motion: reduce)').matches
}
