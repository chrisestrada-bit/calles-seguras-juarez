import { expect, type Page, type BrowserContext } from '@playwright/test'

export const API = `http://localhost:${process.env.E2E_API_PORT ?? '18000'}`
export const CLAVE = 'Prueba2026e2e'
/** Contraseña de las cuentas sembradas (db/seed.py); en CI la fija el flujo con SEED_PASSWORD. */
export const CLAVE_SEMILLA = (() => {
  const clave = process.env.SEED_PASSWORD
  if (!clave) throw new Error('Define SEED_PASSWORD (la misma con la que corriste db/seed.py) para ejecutar las pruebas E2E.')
  return clave
})()
export const TOKEN_KEY = 'calles-seguras.access-token'

export function correoUnico(prefijo = 'e2e'): string {
  return `${prefijo}-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}@ejemplo.mx`
}

/** PNG válido mínimo (1×1) para pruebas de carga de fotografías. */
export const PNG_1X1 = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==',
  'base64',
)

/** Punto único (cada ejecución) dentro de Ciudad Juárez: evita avisos de duplicado con reportes de otras corridas. */
export function puntoAleatorio(): { latitude: number; longitude: number } {
  return { latitude: 31.46 + Math.random() * 0.3, longitude: -106.62 + Math.random() * 0.34 }
}

export async function registrar(page: Page, correo: string, nombre = 'Persona E2E'): Promise<void> {
  await page.goto('/registro')
  await page.getByLabel('Nombre completo').fill(nombre)
  await page.getByLabel('Correo electrónico').fill(correo)
  await page.getByLabel('Contraseña', { exact: true }).fill(CLAVE)
  await page.getByRole('checkbox', { name: /aviso de privacidad/i }).check()
  await page.getByRole('button', { name: 'Crear cuenta' }).click()
  await expect(page.getByText(/cuenta creada para/i)).toBeVisible()
}

export async function iniciarSesion(page: Page, correo: string, contrasena = CLAVE): Promise<void> {
  await page.goto('/login')
  await page.getByLabel('Correo electrónico').fill(correo)
  await page.getByLabel('Contraseña', { exact: true }).fill(contrasena)
  await page.getByRole('button', { name: 'Iniciar sesión' }).click()
  await page.waitForURL((url) => url.pathname === '/')
  await expect(page.getByRole('button', { name: /cerrar sesión/i })).toBeVisible()
}

/** Cuenta ciudadana nueva con sesión iniciada. */
export async function ciudadanoNuevo(page: Page): Promise<string> {
  const correo = correoUnico()
  await registrar(page, correo)
  await iniciarSesion(page, correo)
  return correo
}

export const tokenDe = (page: Page): Promise<string> =>
  page.evaluate((k) => localStorage.getItem(k) ?? '', TOKEN_KEY)

/** Los mosaicos de OpenStreetMap se sustituyen por un PNG local: la prueba no depende de internet. */
export async function sinMosaicosExternos(context: BrowserContext): Promise<void> {
  await context.route('**/tile.openstreetmap.org/**', (ruta) =>
    ruta.fulfill({ status: 200, contentType: 'image/png', body: PNG_1X1 }),
  )
}
