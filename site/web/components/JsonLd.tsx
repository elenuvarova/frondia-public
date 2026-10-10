// A server component: one <script type="application/ld+json"> tag. `data` is a plain object the
// caller built (lib/seo.ts) — never raw HTML — but a string inside it could still hold "</script>"
// (a description from the catalogue, later a dataset title), which would end the tag early. Every
// "<" is written as its JSON escape <: the same JSON to a parser, never a tag to the browser.
export function jsonLdText(data: unknown): string {
  return JSON.stringify(data).replace(/</g, '\\u003c')
}

export function JsonLd({ data, nonce }: { data: unknown; nonce?: string }) {
  return (
    // eslint-disable-next-line react/no-danger
    <script type="application/ld+json" nonce={nonce} dangerouslySetInnerHTML={{ __html: jsonLdText(data) }} />
  )
}
