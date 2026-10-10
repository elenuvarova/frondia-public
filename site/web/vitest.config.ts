import path from 'node:path'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  // one React for next-intl and use-intl (kept from the time the Vite apps hoisted React 18; harmless with one workspace)
  resolve: { alias: { '@': path.resolve(__dirname), 'server-only': path.resolve(__dirname, 'tests/empty.ts') }, dedupe: ['react', 'react-dom'] },
  test: { include: ['tests/**/*.test.ts'], environment: 'node', root: __dirname, server: { deps: { inline: ['next-intl', 'use-intl'] } } },
})
