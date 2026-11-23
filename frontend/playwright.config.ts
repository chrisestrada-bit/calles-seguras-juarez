import { defineConfig, devices } from '@playwright/test'

/**
 * Pruebas de extremo a extremo (Playwright). Levantan la API real (FastAPI + PostgreSQL ya migrada y sembrada)
 * y el frontend de Vite, y recorren la aplicación como lo haría una persona.
 *
 * Variables (todas opcionales):
 *  - E2E_API_PORT / E2E_WEB_PORT: puertos de la API (18000) y del frontend (4173). La API NO usa el 8000 por
 *    omisión: ahí suele correr el backend de `docker compose`, y reutilizarlo escribía datos de prueba en la base
 *    de desarrollo (auditoría final, M9).
 *  - DATABASE_URL, JWT_SECRET_KEY, SEED_PASSWORD: los mismos que usa el backend (ver .env.example).
 *  - E2E_SKIP_WEBSERVER=1: no arranca servidores (ya están corriendo).
 */
const apiPort = process.env.E2E_API_PORT ?? '18000'
const webPort = process.env.E2E_WEB_PORT ?? '4173'
const apiUrl = `http://localhost:${apiPort}`
const webUrl = `http://localhost:${webPort}`

export default defineConfig({
  testDir: './e2e',
  outputDir: './test-results/e2e',
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: false, // comparten la misma base de datos; el orden fijo evita choques con los límites por usuario
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI
    ? [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }], ['junit', { outputFile: 'test-results/playwright-junit.xml' }]]
    : [['list'], ['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    baseURL: webUrl,
    locale: 'es-MX',
    timezoneId: 'America/Ciudad_Juarez',
    // Evidencia de fallos: captura, traza (se abre con `npx playwright show-trace`) y video.
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'escritorio', use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } } },
    // 360 px: ancho mínimo exigido por el proyecto (RNF). Sólo los flujos que no dependen del tamaño.
    { name: 'movil-360', use: { ...devices['Pixel 5'], viewport: { width: 360, height: 740 } }, grep: /@movil/ },
  ],
  webServer: process.env.E2E_SKIP_WEBSERVER
    ? undefined
    : [
        {
          command: `python -m uvicorn app.main:app --host 127.0.0.1 --port ${apiPort}`,
          cwd: '../backend',
          url: `${apiUrl}/salud`,
          reuseExistingServer: !process.env.CI,
          timeout: 60_000,
          env: {
            FRONTEND_URL: webUrl, ROUTING_API_URL: '', GEOCODING_API_KEY: '', UPLOADS_DIR: process.env.UPLOADS_DIR ?? './.uploads_e2e',
            // Todas las pruebas llegan desde 127.0.0.1: se elevan los límites anti-abuso por IP (registro y login).
            LIMITE_REGISTROS_POR_HORA_IP: '100000', LIMITE_LOGIN_FALLIDOS_POR_IP: '100000',
          },
        },
        {
          command: `npm run dev -- --host 127.0.0.1 --port ${webPort} --strictPort`,
          url: webUrl,
          reuseExistingServer: !process.env.CI,
          timeout: 60_000,
          env: { VITE_API_BASE_URL: apiUrl },
        },
      ],
})
