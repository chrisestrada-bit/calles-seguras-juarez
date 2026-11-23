import { renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { CrearReporteRequest } from '../types/api'
import { api, ApiError } from './api'
import {
  cargarCola, descartar, encolar, enviarComoDistinto, reintentar, sincronizar, useColaOffline, type Borrador,
} from './colaOffline'

vi.mock('./api', async (original) => ({ ...(await original<typeof import('./api')>()), api: { post: vi.fn() } }))

const USUARIO = 'usuario-1'
const CLAVE = '5b2f7e1c-0a54-4c53-9e0f-a8a1d3a8c001'
const BACHE: CrearReporteRequest = {
  tipo_dano: 'Bache', latitud: 31.7, longitud: -106.4, colonia_id: 1, calle: 'Av. Tecnológico',
  tamano: 'grande', profundidad: 'más de 10 cm', carril_afectado: 'carril derecho', forzar_nuevo: false,
}
const post = () => vi.mocked(api.post)
const guardada = (): Borrador[] => JSON.parse(localStorage.getItem(`csj.cola.${USUARIO}`) ?? '[]') as Borrador[]

beforeEach(() => {
  post().mockReset()
  cargarCola(null)
  localStorage.clear()
  cargarCola(USUARIO)
})

describe('cola de envío sin conexión (HU-08.4)', () => {
  it('guarda el borrador con su idempotency_key, por persona', () => {
    encolar(USUARIO, BACHE, CLAVE)
    expect(guardada()).toHaveLength(1)
    expect(guardada()[0]).toMatchObject({ id: CLAVE, estado: 'pendiente', payload: { idempotency_key: CLAVE, calle: 'Av. Tecnológico' } })
    expect(localStorage.getItem('csj.cola.otra-persona')).toBeNull()
  })

  it('encolar la misma llave dos veces no duplica el borrador', () => {
    encolar(USUARIO, BACHE, CLAVE)
    encolar(USUARIO, BACHE, CLAVE)
    expect(guardada()).toHaveLength(1)
  })

  it('envía con la misma llave, retira el borrador y avisa el folio', async () => {
    encolar(USUARIO, BACHE, CLAVE)
    post().mockResolvedValueOnce({ folio: 'BCH-2026-000777' })
    const { result } = renderHook(() => useColaOffline())
    await sincronizar(USUARIO)
    expect(post()).toHaveBeenCalledWith('/api/v1/reportes', expect.objectContaining({ idempotency_key: CLAVE }))
    expect(guardada()).toEqual([])
    expect(result.current.ultimosFolios).toEqual(['BCH-2026-000777'])
  })

  it('si se cae la red conserva el borrador y reintenta con la MISMA llave (nunca duplica el folio)', async () => {
    encolar(USUARIO, BACHE, CLAVE)
    post().mockRejectedValueOnce(new ApiError(0, 'sin conexión')).mockResolvedValueOnce({ folio: 'BCH-2026-000778' })
    await sincronizar(USUARIO)
    expect(guardada()[0].estado).toBe('pendiente')
    await sincronizar(USUARIO)
    expect(guardada()).toEqual([])
    const llaves = post().mock.calls.map(([, cuerpo]) => (cuerpo as { idempotency_key: string }).idempotency_key)
    expect(llaves).toEqual([CLAVE, CLAVE])
  })

  it('un posible duplicado se conserva como conflicto con los folios cercanos; «enviar como distinto» lo reenvía', async () => {
    encolar(USUARIO, BACHE, CLAVE)
    post().mockRejectedValueOnce(new ApiError(409, 'Ya existe un reporte', { codigo: 'POSIBLE_DUPLICADO', mensaje: 'Ya existe un reporte', detalles: [{ folio: 'BCH-2026-000100', mensaje: 'cerca' }] }))
    await sincronizar(USUARIO)
    expect(guardada()[0]).toMatchObject({ estado: 'conflicto', candidatos: ['BCH-2026-000100'] })
    enviarComoDistinto(USUARIO, CLAVE)
    expect(guardada()[0]).toMatchObject({ estado: 'pendiente', id: CLAVE, payload: { forzar_nuevo: true, idempotency_key: CLAVE } })
    post().mockResolvedValueOnce({ folio: 'BCH-2026-000779' })
    await sincronizar(USUARIO)
    expect(guardada()).toEqual([])
  })

  it('un rechazo del servidor (territorio/validación) conserva el borrador con el motivo', async () => {
    encolar(USUARIO, BACHE, CLAVE)
    post().mockRejectedValueOnce(new ApiError(422, 'La ubicación está fuera de los límites de Ciudad Juárez, Chihuahua.', { codigo: 'FUERA_DE_JUAREZ', mensaje: 'fuera', detalles: [] }))
    await sincronizar(USUARIO)
    expect(guardada()[0]).toMatchObject({ estado: 'error', mensaje: expect.stringContaining('fuera de los límites') })
    reintentar(USUARIO, CLAVE)
    expect(guardada()[0].estado).toBe('pendiente')
    descartar(USUARIO, CLAVE)
    expect(guardada()).toEqual([])
  })

  it('sin sesión válida (401) o con tope por hora (429) el borrador se conserva pendiente', async () => {
    encolar(USUARIO, BACHE, CLAVE)
    post().mockRejectedValueOnce(new ApiError(401, 'sesión expirada'))
    await sincronizar(USUARIO)
    expect(guardada()[0].estado).toBe('pendiente')
    post().mockRejectedValueOnce(new ApiError(429, 'límite'))
    await sincronizar(USUARIO)
    expect(guardada()[0]).toMatchObject({ estado: 'pendiente', mensaje: expect.stringContaining('10 reportes por hora') })
  })

  it('sin conexión del navegador no intenta enviar', async () => {
    encolar(USUARIO, BACHE, CLAVE)
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: false })
    await sincronizar(USUARIO)
    expect(post()).not.toHaveBeenCalled()
    expect(guardada()[0].estado).toBe('pendiente')
  })
})
