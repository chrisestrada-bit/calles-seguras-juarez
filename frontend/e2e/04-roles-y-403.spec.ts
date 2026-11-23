import { expect, test } from '@playwright/test'
import { API, ciudadanoNuevo, CLAVE_SEMILLA, iniciarSesion, tokenDe } from './ayudas'

const conToken = (token: string) => ({ headers: { Authorization: `Bearer ${token}` } })

test.describe('Acciones protegidas por rol y respuestas 403', () => {
  test('un ciudadano no ve las vistas de gestión y la API responde 403', async ({ page, request }) => {
    await ciudadanoNuevo(page)
    // El encabezado no ofrece herramientas de gestión a este rol.
    await expect(page.getByRole('navigation', { name: 'Herramientas de gestión' })).toHaveCount(0)

    for (const ruta of ['/moderacion', '/coordinacion', '/cuadrillas', '/admin/catalogos', '/enlace']) {
      await page.goto(ruta)
      await expect(page.getByText('Tu rol no tiene permiso para consultar esta vista.')).toBeVisible()
    }

    const token = await tokenDe(page)
    for (const [metodo, ruta] of [
      ['GET', '/api/v1/moderacion/reportes'],
      ['GET', '/api/v1/cuadrillas'],
      ['GET', '/api/v1/admin/usuarios'],
      ['GET', '/api/v1/indicadores/puntos-recurrentes'],
      ['GET', '/api/v1/reportes/exportar/csv'],
      ['GET', '/api/v1/enlace/reportes'],
    ] as const) {
      const r = await request.fetch(`${API}${ruta}`, { method: metodo, ...conToken(token) })
      expect(r.status(), `${metodo} ${ruta}`).toBe(403)
    }
    expect((await request.get(`${API}/api/v1/moderacion/reportes`)).status()).toBe(401) // sin sesión
  })

  test('el 403 queda visible en la red cuando el navegador llama a una ruta sin permiso', async ({ page }) => {
    await ciudadanoNuevo(page)
    const token = await tokenDe(page)
    const enRed = page.waitForResponse((r) => r.url().includes('/api/v1/moderacion/reportes'))
    const desdeLaPagina = await page.evaluate(async ([base, t]) => {
      const r = await fetch(`${base}/api/v1/moderacion/reportes`, { headers: { Authorization: `Bearer ${t}` } })
      return { status: r.status, cuerpo: (await r.json()) as { error: { codigo: string } } }
    }, [API, token])
    expect((await enRed).status()).toBe(403) // visible en la red del navegador
    expect(desdeLaPagina.status).toBe(403)
    expect(desdeLaPagina.cuerpo.error.codigo).toBe('ROL_NO_AUTORIZADO')
  })

  test('moderación ve su panel, pero asignar cuadrillas (coordinación) le devuelve 403', async ({ page, request }) => {
    await iniciarSesion(page, 'moderador@ejemplo.mx', CLAVE_SEMILLA)
    await expect(page.getByRole('navigation', { name: 'Herramientas de gestión' })).toBeVisible()
    const erroresDeConsola: string[] = []
    page.on('console', (m) => { if (m.type() === 'error') erroresDeConsola.push(m.text()) })
    await page.goto('/moderacion')
    await expect(page.getByRole('heading', { name: 'Panel de moderación' })).toBeVisible()
    await expect(page.getByRole('table', { name: /cola administrativa/i })).toBeVisible() // ya hay filas con su botón «Fusionar»
    await expect(page.getByRole('button', { name: /fusionar como duplicado/i }).first()).toBeVisible()
    // Regresión: el modal de fusión no debe anidarse dentro del formulario de transición (<form> dentro de <form>).
    // React 19 lo reporta como «<form> cannot be a descendant of <form>» (versiones anteriores: validateDOMNesting).
    expect(erroresDeConsola.filter((t) => /descendant|nested|validateDOMNesting|cannot contain/i.test(t))).toEqual([])
    await expect(page.getByRole('table', { name: /cola administrativa/i }).or(page.getByText(/no hay reportes|sin transiciones/i)).first()).toBeVisible()

    await page.goto('/cuadrillas')
    await expect(page.getByText('Tu rol no tiene permiso para consultar esta vista.')).toBeVisible()
    const token = await tokenDe(page)
    expect((await request.get(`${API}/api/v1/cuadrillas`, conToken(token))).status()).toBe(403)
    const asignar = await request.post(`${API}/api/v1/cuadrillas/1/asignaciones`, { ...conToken(token), data: { folio: 'BCH-2026-000001', fecha_programada: '2099-01-01' } })
    expect(asignar.status()).toBe(403)
  })

  test('coordinación administra cuadrillas y catálogos', async ({ page }) => {
    await iniciarSesion(page, 'coordinador@ejemplo.mx', CLAVE_SEMILLA)
    await page.goto('/cuadrillas')
    await expect(page.getByRole('heading', { name: 'Cuadrillas', exact: true })).toBeVisible()
    await expect(page.getByRole('link', { name: /cuadrilla norte/i })).toBeVisible()
    await page.getByRole('link', { name: /cuadrilla norte/i }).click()
    await expect(page.getByRole('heading', { name: 'Asignar bache validado' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Enlaces municipales' })).toBeVisible()

    await page.goto('/admin/catalogos')
    await expect(page.getByRole('heading', { name: 'Motivos de rechazo' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Tipos de daño' })).toBeVisible()
  })

  test('el enlace municipal sólo ve sus cuadrillas y todo lo ajeno responde 403', async ({ page, request }) => {
    await iniciarSesion(page, 'enlace@ejemplo.mx', CLAVE_SEMILLA)
    await expect(page.locator('.session-user__role')).toHaveText('Enlace municipal')
    await page.goto('/enlace')
    await expect(page.getByRole('heading', { name: 'Mis cuadrillas' })).toBeVisible()
    await expect(page.getByText(/cuadrilla norte/i).first()).toBeVisible()
    await expect(page.getByText(/cuadrilla centro/i)).toHaveCount(0) // no está vinculada a su cuenta

    const token = await tokenDe(page)
    const propios = await (await request.get(`${API}/api/v1/enlace/reportes`, conToken(token))).json()
    expect(propios.cuadrillas.map((c: { nombre: string }) => c.nombre).join()).not.toContain('Centro')

    for (const ruta of ['/api/v1/moderacion/reportes', '/api/v1/cuadrillas', '/api/v1/admin/usuarios', '/api/v1/notificaciones']) {
      expect((await request.get(`${API}${ruta}`, conToken(token))).status(), ruta).toBe(403)
    }
    // Un bache ajeno (o inexistente) recibe la misma respuesta: no se revela trabajo de otras cuadrillas.
    const ajeno = await request.get(`${API}/api/v1/enlace/reportes/BCH-2099-999999`, conToken(token))
    expect(ajeno.status()).toBe(403)
    expect((await ajeno.json()).error.codigo).toBe('REPORTE_AJENO')
    const avance = await request.post(`${API}/api/v1/enlace/reportes/BCH-2099-999999/avance`, { ...conToken(token), data: { estado_nuevo: 'En reparación' } })
    expect(avance.status()).toBe(403)
  })
})
