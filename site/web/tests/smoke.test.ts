import { existsSync, realpathSync } from 'node:fs'
import path from 'node:path'
import { expect, test } from 'vitest'

test('public is the pipeline folder, reached through the symlink', () => {
  const pub = path.resolve(__dirname, '../public')
  expect(realpathSync(pub)).toBe(path.resolve(__dirname, '../../public'))
  expect(existsSync(path.join(pub, 'data/facts.json'))).toBe(true)
})
