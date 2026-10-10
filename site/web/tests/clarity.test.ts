import { expect, test } from 'vitest'
import { cookieDomains } from '@/components/Clarity'

test('Clarity cookies are cleared on the host and its parent domain, whatever the host', () => {
  expect(cookieDomains('frondia.eu')).toEqual(['.frondia.eu'])
  expect(cookieDomains('www.frondia.eu')).toEqual(['.www.frondia.eu', '.frondia.eu'])
  expect(cookieDomains('preview.example.org')).toEqual(['.preview.example.org', '.example.org'])
})

test('no domain attribute for localhost or an IP address (host-only cookies there)', () => {
  expect(cookieDomains('localhost')).toEqual([])
  expect(cookieDomains('127.0.0.1')).toEqual([])
  expect(cookieDomains('::1')).toEqual([])
})
