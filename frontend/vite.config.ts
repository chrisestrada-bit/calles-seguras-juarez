import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Pruebas de componentes y lógica (Vitest + Testing Library). Los flujos de extremo a extremo viven en e2e/ (Playwright).
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    css: false,
    restoreMocks: true,
    reporters: process.env.CI ? ['default', 'junit'] : ['default'],
    outputFile: { junit: './test-results/vitest-junit.xml' },
  },
})
