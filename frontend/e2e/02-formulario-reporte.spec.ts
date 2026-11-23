import { expect, test, type Page } from '@playwright/test'
import { ciudadanoNuevo, PNG_1X1, puntoAleatorio } from './ayudas'

/** Fija la ubicación con el GPS simulado (un punto único por ejecución) y espera la revisión de duplicados. */
async function fijarUbicacion(page: Page) {
  await page.context().grantPermissions(['geolocation'])
  await page.context().setGeolocation(puntoAleatorio())
  await page.getByRole('button', { name: /usar mi ubicación gps/i }).click()
  await expect(page.getByText(/punto: 31\./i)).toBeVisible()
  await expect(page.getByText(/no encontramos reportes abiertos o vigentes/i)).toBeVisible()
}

const subir = (page: Page, archivos: Array<{ name: string; mimeType: string; buffer: Buffer }>) =>
  page.getByLabel(/agregar fotografías/i).setInputFiles(archivos)

test.describe('Formulario dinámico de reporte', () => {
  test.beforeEach(async ({ page }) => {
    await ciudadanoNuevo(page)
    await page.goto('/reportar')
  })

  test('los campos cambian según el tipo de daño y los condicionales aparecen sólo cuando corresponden', async ({ page }) => {
    await fijarUbicacion(page)

    // Bache: tamaño, profundidad y carril afectado.
    await expect(page.getByLabel('Tamaño')).toBeVisible()
    await expect(page.getByLabel('Profundidad')).toBeVisible()
    await expect(page.getByLabel('Carril afectado')).toBeVisible()

    // Alcantarilla sin tapa: pregunta si está señalizada (la severidad Alta la fija el servidor).
    await page.locator('label.type-option', { hasText: 'Alcantarilla sin tapa' }).click()
    await fijarUbicacion(page)
    await expect(page.getByText('¿Está señalizada?')).toBeVisible()
    await expect(page.getByLabel('Tamaño')).toHaveCount(0)

    // Encharcamiento: el riesgo sólo se pregunta si el agua es intransitable.
    await page.locator('label.type-option', { hasText: 'Encharcamiento' }).click()
    await fijarUbicacion(page)
    await expect(page.getByLabel('Nivel del agua')).toBeVisible()
    await expect(page.getByText('¿Hay riesgo para personas o vehículos?')).toHaveCount(0)
    await page.getByLabel('Nivel del agua').selectOption('intransitable')
    await expect(page.getByText('¿Hay riesgo para personas o vehículos?')).toBeVisible()
    await page.getByLabel('Nivel del agua').selectOption('a media llanta')
    await expect(page.getByText('¿Hay riesgo para personas o vehículos?')).toHaveCount(0)
  })

  test('la descripción se limita a 500 caracteres y los campos obligatorios impiden enviar', async ({ page }) => {
    await fijarUbicacion(page)
    await page.getByLabel(/^descripción/i).fill('a'.repeat(520))
    await expect(page.getByLabel(/^descripción/i)).toHaveValue('a'.repeat(500))
    await expect(page.getByText('500/500')).toBeVisible()

    await page.getByRole('button', { name: 'Enviar reporte' }).click()
    // El navegador bloquea el envío: seguimos en el formulario y no hay folio.
    await expect(page.getByRole('heading', { name: 'Reporte registrado' })).toHaveCount(0)
    await expect(page.getByLabel('Tamaño')).toBeVisible()
  })

  test('las fotografías se validan: formato, tamaño (5 MB), límite de 3, contador y quitar', async ({ page }) => {
    await fijarUbicacion(page)
    await expect(page.getByText('0/3')).toBeVisible()

    await subir(page, [
      { name: 'documento.txt', mimeType: 'text/plain', buffer: Buffer.from('no soy imagen') },
      { name: 'enorme.png', mimeType: 'image/png', buffer: Buffer.alloc(5 * 1024 * 1024 + 1) },
    ])
    await expect(page.getByRole('alert').filter({ hasText: /formato no permitido/i })).toContainText('documento.txt')
    await expect(page.getByRole('alert').filter({ hasText: /5 MB/i })).toContainText('enorme.png')
    await expect(page.getByText('0/3')).toBeVisible()

    await subir(page, [1, 2, 3, 4].map((n) => ({ name: `foto-${n}.png`, mimeType: 'image/png', buffer: PNG_1X1 })))
    await expect(page.getByText('3/3')).toBeVisible()
    await expect(page.getByRole('alert').filter({ hasText: /límite de 3/i })).toContainText('foto-4.png')
    await expect(page.getByAltText(/vista previa de foto-1\.png/i)).toBeVisible()

    await page.getByRole('button', { name: /quitar foto-1\.png/i }).click()
    await expect(page.getByText('2/3')).toBeVisible()
  })

  test('se crea un bache con una fotografía y la persona la ve en el detalle de su reporte', async ({ page }) => {
    await fijarUbicacion(page)
    await page.locator('#colonia').selectOption({ index: 1 })
    await page.getByLabel('Calle', { exact: true }).fill('Calle de prueba E2E')
    await page.getByLabel('Tamaño').selectOption('mediano')
    await page.getByLabel('Profundidad').selectOption('5 a 10 cm')
    await page.getByLabel('Carril afectado').selectOption('carril derecho')
    await subir(page, [{ name: 'evidencia.png', mimeType: 'image/png', buffer: PNG_1X1 }])
    await page.getByRole('button', { name: 'Enviar reporte' }).click()

    await expect(page.getByRole('heading', { name: 'Reporte registrado' })).toBeVisible()
    const folio = (await page.getByText(/BCH-\d{4}-\d{6}/).first().textContent())?.match(/BCH-\d{4}-\d{6}/)?.[0]
    expect(folio).toBeTruthy()

    await page.getByRole('link', { name: /ver reporte/i }).click()
    await expect(page.getByRole('heading', { name: 'Fotografías' })).toBeVisible()
    await expect(page.getByAltText(new RegExp(`fotografía 1 del reporte ${folio}`, 'i'))).toBeVisible()
    await expect(page.getByText('Sin validar')).toBeVisible()
  })
})
