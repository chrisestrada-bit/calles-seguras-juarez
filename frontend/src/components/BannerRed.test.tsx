import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../context/authContexto'
import { api, ApiError } from '../services/api'
import { cargarCola, encolar } from '../services/colaOffline'
import type { CrearReporteRequest } from '../types/api'
import { BannerRed } from './BannerRed'

vi.mock('../services/api', async (original) => ({ ...(await original<typeof import('../services/api')>()), api: { post: vi.fn() } }))

const BACHE: CrearReporteRequest = {
  tipo_dano: 'Bache', latitud: 31.7, longitud: -106.4, colonia_id: 1, calle: 'Calle Sin Conexión',
  tamano: 'chico', profundidad: 'menos de 5 cm', carril_afectado: 'acotamiento', forzar_nuevo: false,
}
const sesion: AuthContextValue = {
  usuario: { id: 'u-1', nombre: 'Ana', rol: 'ciudadano' }, token: 't', rolActivo: 'ciudadano', autenticado: true,
  iniciarSesion: () => undefined, renovarSesion: async () => undefined, cerrarSesion: async () => undefined, cambiarRolActivo: () => undefined,
}
const pintar = () => render(<AuthContext.Provider value={sesion}><BannerRed /></AuthContext.Provider>)
const sinRed = (valor: boolean) => Object.defineProperty(navigator, 'onLine', { configurable: true, value: !valor })

beforeEach(() => {
  vi.mocked(api.post).mockReset()
  cargarCola(null)
})

describe('<BannerRed /> (HU-08.4)', () => {
  it('no muestra nada con red y sin borradores', () => {
    const { container } = pintar()
    expect(container).toBeEmptyDOMElement()
  })

  it('sin conexión avisa «Sin conexión» y cuántos reportes quedaron guardados para enviar', () => {
    sinRed(true)
    encolar('u-1', BACHE, 'a1b2c3d4-0000-4000-8000-000000000001')
    pintar()
    expect(screen.getByText('Sin conexión')).toBeInTheDocument()
    expect(screen.getByText(/1 reporte\(s\) guardado\(s\) para enviar/i)).toBeInTheDocument()
  })

  it('al volver la red envía solo, muestra «Enviando» y luego el folio sin duplicar', async () => {
    sinRed(true)
    encolar('u-1', BACHE, 'a1b2c3d4-0000-4000-8000-000000000002')
    let resolver: (v: { folio: string }) => void = () => undefined
    vi.mocked(api.post).mockReturnValue(new Promise((r) => { resolver = r as typeof resolver }))
    pintar()
    expect(screen.getByText('Sin conexión')).toBeInTheDocument()
    await act(async () => { sinRed(false); window.dispatchEvent(new Event('online')) })
    expect(await screen.findByText('Enviando')).toBeInTheDocument()
    expect(api.post).toHaveBeenCalledTimes(1)
    await act(async () => { resolver({ folio: 'BCH-2026-000900' }) })
    expect(await screen.findByText('Enviado')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /BCH-2026-000900/ })).toHaveAttribute('href', '/reportes/BCH-2026-000900')
    expect(api.post).toHaveBeenCalledTimes(1)
  })

  it('un rechazo del servidor muestra «No se pudo enviar», conserva el borrador y permite reintentar o descartar', async () => {
    const user = userEvent.setup()
    encolar('u-1', BACHE, 'a1b2c3d4-0000-4000-8000-000000000003')
    vi.mocked(api.post).mockRejectedValueOnce(new ApiError(422, 'La ubicación está fuera de los límites de Ciudad Juárez, Chihuahua.'))
    pintar()
    const alerta = await screen.findByRole('alert')
    expect(alerta).toHaveTextContent('No se pudo enviar')
    await user.click(screen.getByRole('button', { name: /ver reportes \(1\)/i }))
    expect(screen.getByText(/Calle Sin Conexión/)).toBeInTheDocument()
    expect(screen.getByText(/fuera de los límites de Ciudad Juárez/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /descartar/i }))
    expect(screen.queryByText(/Calle Sin Conexión/)).not.toBeInTheDocument()
  })

  it('un posible duplicado ofrece «Enviar como daño distinto» y el folio cercano', async () => {
    const user = userEvent.setup()
    encolar('u-1', BACHE, 'a1b2c3d4-0000-4000-8000-000000000004')
    vi.mocked(api.post).mockRejectedValueOnce(new ApiError(409, 'Ya existe un reporte', { codigo: 'POSIBLE_DUPLICADO', mensaje: 'x', detalles: [{ folio: 'BCH-2026-000123', mensaje: 'cerca' }] }))
    pintar()
    await user.click(await screen.findByRole('button', { name: /ver reportes \(1\)/i }))
    expect(screen.getByRole('button', { name: /enviar como daño distinto/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /BCH-2026-000123/ })).toBeInTheDocument()
  })
})
