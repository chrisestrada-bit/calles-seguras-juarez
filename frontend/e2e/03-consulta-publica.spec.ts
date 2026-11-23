import { expect, test } from '@playwright/test'
import { API, sinMosaicosExternos } from './ayudas'

test.describe('Consulta pública', () => {
  test.beforeEach(async ({ context }) => {
    await sinMosaicosExternos(context)
  })

  test('los filtros llegan a la API, se pueden combinar y limpiar', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Reportes recientes' })).toBeVisible()
    await expect(page.locator('.report-card').first()).toBeVisible()

    const porTipo = page.waitForResponse((r) => r.url().includes('/api/v1/reportes?') && r.url().includes('tipo_dano=Encharcamiento'))
    await page.getByLabel('Tipo de daño').selectOption('Encharcamiento')
    expect((await porTipo).status()).toBe(200)
    await expect(page.locator('.report-card .type-badge').first()).toContainText('Encharcamiento')
    // Todas las tarjetas visibles son del tipo filtrado (la aserción reintenta hasta que termina de pintar).
    await expect(page.locator('.report-card .type-badge', { hasNotText: 'Encharcamiento' })).toHaveCount(0)

    const porEstado = page.waitForRequest((r) => r.url().includes('estado=Activo') && r.url().includes('tipo_dano=Encharcamiento'))
    await page.getByLabel('Estado', { exact: true }).selectOption('Activo')
    await porEstado

    await page.getByRole('button', { name: /limpiar filtros/i }).click()
    await expect(page.getByLabel('Tipo de daño')).toHaveValue('')
    await expect(page.getByLabel('Estado', { exact: true })).toHaveValue('')
  })

  test('una búsqueda sin coincidencias muestra el estado vacío', async ({ page }) => {
    await page.goto('/')
    await page.getByLabel('Calle o folio').fill('zzzcalleinexistente')
    await page.getByRole('button', { name: 'Buscar', exact: true }).click()
    await expect(page.getByText('No hay reportes que coincidan con tus filtros')).toBeVisible()
  })

  test('el mapa muestra los reportes con la leyenda y mantiene una lista accesible', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('button', { name: 'Mapa', exact: true }).click()
    await expect(page.getByRole('region', { name: /mapa interactivo de reportes/i })).toBeVisible()
    await expect(page.getByRole('list', { name: 'Simbología del mapa' })).toBeVisible()
    await expect(page.locator('.leaflet-marker-icon').first()).toBeVisible()
    // El mapa no pide la ubicación hasta que la persona lo solicita.
    await expect(page.getByText(/tu navegador te pedirá permiso/i)).toHaveCount(0)
    await expect(page.getByRole('button', { name: /centrar en mi ubicación/i })).toBeVisible()

    const lista = page.locator('details.map-list')
    await lista.locator('summary').click()
    await expect(lista.getByRole('link').first()).toHaveAttribute('href', /\/reportes\/(BCH|ENC)-/)
    await expect(page.locator('.leaflet-control-attribution')).toContainText('OpenStreetMap')
  })

  test('los filtros activos también se aplican al mapa', async ({ page }) => {
    await page.goto('/')
    const mapa = page.waitForRequest((r) => r.url().includes('/api/v1/reportes/mapa') && r.url().includes('tipo_dano=Bache'))
    await page.getByLabel('Tipo de daño').selectOption('Bache')
    await page.getByRole('button', { name: 'Mapa', exact: true }).click()
    await mapa
  })

  test('el detalle de un reporte público muestra su historial y nunca datos personales', async ({ page, request }) => {
    const lista = await request.get(`${API}/api/v1/reportes?por_pagina=1`)
    const folio = (await lista.json()).datos[0].folio as string
    await page.goto(`/reportes/${folio}`)
    await expect(page.getByRole('heading', { name: 'Historial del reporte' })).toBeVisible()
    await expect(page.getByText(folio).first()).toBeVisible()
    const cuerpo = await (await request.get(`${API}/api/v1/reportes/${folio}`)).text()
    expect(cuerpo).not.toMatch(/correo|"usuario|autor_id|password/i)
  })

  test('revisar mi trayecto: origen, destino y resultado (o estado vacío explícito)', async ({ page, request }) => {
    const colonias = (await (await request.get(`${API}/api/v1/catalogos/colonias?por_pagina=2`)).json()).datos as Array<{ nombre: string }>
    await page.goto('/trayecto')
    await expect(page.getByRole('heading', { name: 'Revisar mi trayecto' })).toBeVisible()

    const buscar = async (indice: number, texto: string) => {
      const [campo] = await page.getByLabel(/dirección, cruce o colonia/i).all().then((l) => [l[indice]])
      await campo.fill(texto)
      await page.getByRole('button', { name: 'Buscar', exact: true }).nth(indice).click()
      await page.locator('.search-results button').first().click()
    }
    await buscar(0, colonias[0].nombre)
    await buscar(1, colonias[1].nombre)
    await expect(page.locator('.location-readout')).toHaveCount(2)

    const respuesta = page.waitForResponse((r) => r.url().includes('/api/v1/trayecto/revisar'))
    await page.getByRole('button', { name: /revisar trayecto/i }).click()
    expect((await respuesta).status()).toBe(200)
    await expect(page.getByRole('heading', { name: 'Resultados' })).toBeVisible()
    const hayLista = await page.locator('.trayecto-lista li').count()
    if (hayLista === 0) await expect(page.getByText('No hay encharcamientos reportados cerca del trayecto')).toBeVisible()
    else await expect(page.locator('.trayecto-lista li').first()).toContainText(/del trayecto/i)
  })

  test('@movil la consulta pública y su barra de vista caben en 360 px', async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('button', { name: 'Mapa', exact: true })).toBeVisible()
    const sobra = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    expect(sobra).toBeLessThanOrEqual(1)
  })
})
