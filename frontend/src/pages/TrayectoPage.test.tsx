import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError } from '../services/api'
import type { TrayectoResponse } from '../types/api'
import { TrayectoPage } from './TrayectoPage'

vi.mock('../services/api', async (original) => ({ ...(await original<typeof import('../services/api')>()), api: { get: vi.fn() } }))
// Leaflet necesita un navegador real: aquí sólo importa la lógica de la página.
vi.mock('../components/TrayectoMapa', () => ({ TrayectoMapa: () => <div data-testid="mapa-trayecto" /> }))

const VACIO = 'No hay encharcamientos reportados cerca del trayecto'
const geocoding = (etiqueta: string, lat: number) => ({ fuente: 'catalogo_local', degradado: false, atribucion: null, mensaje: null, datos: [{ etiqueta, calle: null, precision: 'colonia', colonia_sugerida: null, ubicacion: { latitud: lat, longitud: -106.4 } }] })
const trayecto = (extra: Partial<TrayectoResponse>): TrayectoResponse => ({
  origen: { latitud: 31.7, longitud: -106.4 }, destino: { latitud: 31.71, longitud: -106.4 }, radio_metros: 100,
  ruta: { fuente: 'osrm', degradado: false, mensaje: null, distancia_metros: 1200, duracion_segundos: 180, puntos: [[31.7, -106.4], [31.71, -106.4]] },
  total: 0, datos: [], mensaje: VACIO, ...extra,
})

async function elegirPuntos(user: ReturnType<typeof userEvent.setup>) {
  const campos = screen.getAllByLabelText(/dirección, cruce o colonia/i)
  const botones = screen.getAllByRole('button', { name: /^buscar$/i })
  await user.type(campos[0], 'Pronaf')
  await user.click(botones[0])
  await user.click(await screen.findByRole('option', { name: /origen pronaf/i }))
  await user.type(campos[1], 'Centro')
  await user.click(botones[1])
  await user.click(await screen.findByRole('option', { name: /destino centro/i }))
}

beforeEach(() => {
  vi.mocked(api.get).mockReset()
  vi.mocked(api.get).mockImplementation((ruta: string) => {
    if (ruta.includes('/geocoding/buscar')) return Promise.resolve(ruta.includes('Pronaf') ? geocoding('Origen Pronaf', 31.7) : geocoding('Destino Centro', 31.71))
    return Promise.reject(new Error(`ruta inesperada ${ruta}`))
  })
})

describe('<TrayectoPage /> (HU-04.6)', () => {
  it('sugiere direcciones al escribir y se elige con teclado', async () => {
    const user = userEvent.setup()
    render(<TrayectoPage />)
    await user.type(screen.getAllByRole('combobox')[0], 'Pronaf')
    expect(await screen.findByRole('option', { name: /origen pronaf/i })).toBeInTheDocument()
    expect(vi.mocked(api.get).mock.calls.length).toBe(1)
    await user.keyboard('{ArrowDown}{Enter}')
    expect(await screen.findByText(/origen pronaf \(31\.70000/i)).toBeInTheDocument()
    expect(screen.queryByRole('option')).not.toBeInTheDocument()
  })

  it('no consulta con menos de 3 caracteres', async () => {
    const user = userEvent.setup()
    render(<TrayectoPage />)
    await user.type(screen.getAllByRole('combobox')[0], 'Pr')
    await new Promise((r) => setTimeout(r, 450))
    expect(api.get).not.toHaveBeenCalled()
  })

  it('pide origen y destino antes de revisar', async () => {
    const user = userEvent.setup()
    render(<TrayectoPage />)
    await user.click(screen.getByRole('button', { name: /revisar trayecto/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/elige el origen y el destino/i)
  })

  it('con el trayecto limpio muestra el estado vacío explícito', async () => {
    const user = userEvent.setup()
    render(<TrayectoPage />)
    await elegirPuntos(user)
    vi.mocked(api.get).mockImplementation((ruta: string) => (ruta.includes('/trayecto/revisar') ? Promise.resolve(trayecto({})) : Promise.reject(new Error(ruta))))
    await user.click(screen.getByRole('button', { name: /revisar trayecto/i }))
    expect(await screen.findByText(VACIO)).toBeInTheDocument()
    const llamada = vi.mocked(api.get).mock.calls.at(-1)?.[0] as string
    expect(llamada).toContain('origen_latitud=31.7')
    expect(llamada).toContain('destino_latitud=31.71')
  })

  it('lista los encharcamientos cercanos con los intransitables primero y avisa si la ruta es una línea recta', async () => {
    const user = userEvent.setup()
    render(<TrayectoPage />)
    await elegirPuntos(user)
    const respuesta = trayecto({
      total: 2, mensaje: null,
      ruta: { fuente: 'linea_recta', degradado: true, mensaje: 'El servicio de rutas no respondió; se revisó la línea recta entre origen y destino.', distancia_metros: 1100, duracion_segundos: null, puntos: [[31.7, -106.4], [31.71, -106.4]] },
      datos: [
        { folio: 'ENC-2026-000050', calle: 'Av. Juárez', colonia: { id: 1, nombre: 'Centro' }, ubicacion: { latitud: 31.705, longitud: -106.4 }, nivel_agua: 'intransitable', es_intransitable: true, hay_riesgo_personas_vehiculos: true, distancia_metros: 80, vigente_hasta: '2026-11-22T20:00:00-07:00' },
        { folio: 'ENC-2026-000051', calle: 'Av. Tecnológico', colonia: { id: 2, nombre: 'Pronaf' }, ubicacion: { latitud: 31.706, longitud: -106.4 }, nivel_agua: 'a media llanta', es_intransitable: false, hay_riesgo_personas_vehiculos: null, distancia_metros: 20, vigente_hasta: '2026-11-22T20:00:00-07:00' },
      ],
    })
    vi.mocked(api.get).mockImplementation((ruta: string) => (ruta.includes('/trayecto/revisar') ? Promise.resolve(respuesta) : Promise.reject(new Error(ruta))))
    await user.click(screen.getByRole('button', { name: /revisar trayecto/i }))
    const items = await screen.findAllByRole('listitem')
    const textos = items.map((li) => li.textContent ?? '')
    const iCritico = textos.findIndex((t) => t.includes('ENC-2026-000050'))
    const iNormal = textos.findIndex((t) => t.includes('ENC-2026-000051'))
    expect(iCritico).toBeGreaterThanOrEqual(0)
    expect(iCritico).toBeLessThan(iNormal)
    expect(within(items[iCritico]).getByText('Intransitable')).toBeInTheDocument()
    expect(within(items[iCritico]).getByText(/riesgo para personas o vehículos/i)).toBeInTheDocument()
    expect(screen.getByText(/línea recta entre origen y destino/i)).toBeInTheDocument()
    expect(screen.queryByText(VACIO)).not.toBeInTheDocument()
  })

  it('muestra el mensaje del servidor si un punto está fuera de Ciudad Juárez', async () => {
    const user = userEvent.setup()
    render(<TrayectoPage />)
    await elegirPuntos(user)
    vi.mocked(api.get).mockImplementation((ruta: string) => (ruta.includes('/trayecto/revisar')
      ? Promise.reject(new ApiError(422, 'La ubicación está fuera de los límites de Ciudad Juárez, Chihuahua. Selecciona un punto dentro del municipio.'))
      : Promise.reject(new Error(ruta))))
    await user.click(screen.getByRole('button', { name: /revisar trayecto/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/fuera de los límites de Ciudad Juárez/i)
  })
})
