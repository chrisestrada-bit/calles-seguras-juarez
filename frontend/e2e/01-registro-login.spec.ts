import { expect, test } from '@playwright/test'
import { CLAVE, correoUnico, iniciarSesion, registrar, TOKEN_KEY } from './ayudas'

test.describe('Registro e inicio de sesión', () => {
  test('una persona se registra, inicia sesión y cierra sesión', async ({ page }) => {
    const correo = correoUnico()
    await registrar(page, correo, 'Ana López E2E')
    await iniciarSesion(page, correo)

    // La sesión se refleja en el encabezado y el token se guarda para las llamadas a la API.
    await expect(page.locator('.session-user__name')).toHaveText('Ana López E2E')
    await expect(page.locator('.session-user__role')).toHaveText('Ciudadano')
    expect(await page.evaluate((k) => Boolean(localStorage.getItem(k)), TOKEN_KEY)).toBe(true)

    await page.getByRole('button', { name: /cerrar sesión/i }).click()
    await page.waitForURL('**/login')
    expect(await page.evaluate((k) => localStorage.getItem(k), TOKEN_KEY)).toBeNull()
  })

  test('rechaza una contraseña sin números y exige aceptar el aviso de privacidad', async ({ page }) => {
    await page.goto('/registro')
    await page.getByLabel('Nombre completo').fill('Persona E2E')
    await page.getByLabel('Correo electrónico').fill(correoUnico())
    await page.getByLabel('Contraseña', { exact: true }).fill('soloLetras')
    await page.getByRole('button', { name: 'Crear cuenta' }).click()
    await expect(page.getByRole('alert')).toContainText('al menos 8 caracteres e incluir letras y números')

    await page.getByLabel('Contraseña', { exact: true }).fill(CLAVE)
    await page.getByRole('button', { name: 'Crear cuenta' }).click()
    await expect(page.getByRole('alert')).toContainText('aviso de privacidad')
  })

  test('un correo repetido o una contraseña incorrecta muestran un error claro', async ({ page }) => {
    const correo = correoUnico()
    await registrar(page, correo)
    await page.goto('/registro')
    await page.getByLabel('Nombre completo').fill('Otra Persona')
    await page.getByLabel('Correo electrónico').fill(correo)
    await page.getByLabel('Contraseña', { exact: true }).fill(CLAVE)
    await page.getByRole('checkbox', { name: /aviso de privacidad/i }).check()
    await page.getByRole('button', { name: 'Crear cuenta' }).click()
    await expect(page.getByRole('alert')).toBeVisible()

    await page.goto('/login')
    await page.getByLabel('Correo electrónico').fill(correo)
    await page.getByLabel('Contraseña', { exact: true }).fill('Incorrecta123')
    await page.getByRole('button', { name: 'Iniciar sesión' }).click()
    await expect(page.getByRole('alert')).toContainText('Correo o contraseña incorrectos')
    await expect(page).toHaveURL(/\/login$/)
  })

  test('@movil el formulario de inicio de sesión cabe en 360 px sin desplazamiento horizontal', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByRole('button', { name: 'Iniciar sesión' })).toBeVisible()
    const sobra = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    expect(sobra).toBeLessThanOrEqual(0)
  })
})
