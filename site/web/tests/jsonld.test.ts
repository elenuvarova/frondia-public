import { expect, test } from 'vitest'
import { jsonLdText } from '@/components/JsonLd'

test('JSON-LD text cannot close its own script tag', () => {
  const data = { description: 'a </script><script>alert(1)</script> b' }
  const text = jsonLdText(data)
  expect(text).not.toContain('<')
  expect(JSON.parse(text)).toEqual(data)
})
