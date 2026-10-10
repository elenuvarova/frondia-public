import { readFileSync } from 'node:fs'
import path from 'node:path'
import { expect, test } from 'vitest'

// re-check 4: what goes into the image and what it is built from. The build context is site/ (web/Dockerfile).
const SITE = path.resolve(__dirname, '../..')
const dockerfile = readFileSync(path.join(SITE, 'web/Dockerfile'), 'utf8')
const ignore = readFileSync(path.join(SITE, '.dockerignore'), 'utf8').split('\n').map((l) => l.trim()).filter((l) => l && !l.startsWith('#'))

test('.dockerignore keeps env files, git, the agents’ notes, host installs and Next caches out of the build context', () => {
  for (const p of ['**/.env', '**/.env.*', '**/.git', '**/.superpowers', '**/node_modules', '**/.next']) expect(ignore, p).toContain(p)
})

test('both stages build from one pinned release with its digest, and the server runs as a non-root user', () => {
  const arg = dockerfile.match(/^ARG NODE_IMAGE=(\S+)$/m)?.[1]
  expect(arg).toMatch(/^node:\d+\.\d+\.\d+-alpine\d+\.\d+@sha256:[0-9a-f]{64}$/)
  const froms = [...dockerfile.matchAll(/^FROM (\S+)/gm)].map((m) => m[1])
  expect(froms).toEqual(['${NODE_IMAGE}', '${NODE_IMAGE}'])
  const final = dockerfile.slice(dockerfile.lastIndexOf('\nFROM '))
  expect(final).toMatch(/^USER node$/m)
  expect(final).toMatch(/HOSTNAME=0\.0\.0\.0/)
  expect(final).toMatch(/HEALTHCHECK[\s\S]*\/health/)
})

test('the preview languages never reach the image: the variable is set only for a local build', () => {
  expect(dockerfile).not.toContain('PREVIEW_LOCALES')
})

test('the image is built from the web workspace alone: no Vite app or shared package left (plan 6)', () => {
  expect(dockerfile).not.toMatch(/apps\/(landing|atlas)|packages\/shared/)
  const pkg = JSON.parse(readFileSync(path.join(SITE, 'package.json'), 'utf8'))
  expect(pkg.workspaces).toEqual(['web'])
})
