import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError } from '../services/api'
import type { ReportePublico, ReporteResumenPublico } from '../types/api'
import { EncharcamientosVigentes } from './EncharcamientosVigentes'

vi.mock('../services/api', async (original) => ({ ...(await original<typeof import('../services/api')>()), api: { get: vi.fn(), post: vi.fn() } }))

const AHORA = Date.parse('2026-11-25T21:32:00Z')
const encharcamiento = (extra: Partial<ReporteResumenPublico> = {}): ReporteResumenPublico => ({
  folio: 'ENC-2026-000318', tipo_dano: 'Encharcamiento', estado: 'Activo', etiqueta_publica: null, severidad: 'Alta',
  ubicacion: { latitud: 31.707, longitud: -106.431 }, calle: 'Av. Tecnológico', colonia: { id: 1, nombre: 'Partido Iglesias' },
  created_at: '2026-11-25T18:10:00Z', longevidad_dias: 0, nivel_agua: 'intransitable',
  vigencia: { vigente_hasta: '2026-11-26T02:05:00Z', sigue_ahi: 9, ya_no_hay_agua: 1 }, ...extra,
})
const detalle = (esMio: boolean) => ({ ...encharcamiento(), es_mio: esMio }) as unknown as ReportePublico

function mostrar(autenticado: boolean, vigentes = [encharcamiento()]) {
  return render(<EncharcamientosVigentes vigentes={vigentes} estado="listo" error="" autenticado={autenticado} ahora={AHORA} seleccionado={null} onSeleccionar={() => undefined} />)
}

beforeEach(() => {
  vi.mocked(api.get).mockReset()
  vi.mocked(api.post).mockReset()
})

describe('<EncharcamientosVigentes /> (HU-03.2, HU-03.3)', () => {
  it('muestra folio, nivel, vigencia restante y explica la regla de 6 h', () => {
    mostrar(false)
    expect(screen.getByText('ENC-2026-000318')).toBeInTheDocument()
    expect(screen.getByText('Intransitable')).toBeInTheDocument()
    expect(screen.getByText(/4 h 33 min · vence/)).toBeInTheDocument()
    expect(screen.getByText(/reinicia las 6 horas de vigencia/)).toBeInTheDocument()
  })

  it('sin sesión no muestra votos: invita a iniciar sesión', () => {
    mostrar(false)
    expect(screen.queryByRole('button', { name: /sigue ahí/i })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Inicia sesión para confirmar' })).toHaveAttribute('href', '/login')
    expect(api.get).not.toHaveBeenCalled()
  })

  it('oculta los votos a quien creó el reporte (HU-03.3)', async () => {
    vi.mocked(api.get).mockResolvedValue(detalle(true))
    mostrar(true)
    expect(await screen.findByText('Es tu reporte: no puedes confirmarlo')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /sigue ahí/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /ya no hay agua/i })).not.toBeInTheDocument()
  })

  it('registra «Ya no hay agua» con el endpoint real y actualiza el contador n/3', async () => {
    const user = userEvent.setup()
    vi.mocked(api.get).mockResolvedValue(detalle(false))
    vi.mocked(api.post).mockResolvedValue({ folio: 'ENC-2026-000318', tipo: 'ya_no_hay_agua', estado_reporte: 'Activo', vigencia: { vigente_hasta: '2026-11-26T02:05:00Z', sigue_ahi: 9, ya_no_hay_agua: 2 }, mensaje: 'Gracias, registramos tu confirmación.' })
    mostrar(true)
    const grupo = await screen.findByRole('group', { name: /sigue el agua en av\. tecnológico/i })
    await vi.waitFor(() => expect(within(grupo).getByRole('button', { name: /ya no hay agua/i })).toBeEnabled())
    expect(within(grupo).getByRole('button', { name: /ya no hay agua/i })).toHaveTextContent('(1/3)')
    await user.click(within(grupo).getByRole('button', { name: /ya no hay agua/i }))
    expect(api.post).toHaveBeenCalledWith('/api/v1/reportes/ENC-2026-000318/confirmaciones', { tipo: 'ya_no_hay_agua' })
    expect(await screen.findByRole('status')).toHaveTextContent('Gracias, registramos tu confirmación.')
    expect(within(grupo).getByRole('button', { name: /ya no hay agua/i })).toHaveTextContent('(2/3)')
  })

  it('muestra el mensaje del servidor si el voto se rechaza (p. ej. 429)', async () => {
    const user = userEvent.setup()
    vi.mocked(api.get).mockResolvedValue(detalle(false))
    vi.mocked(api.post).mockRejectedValue(new ApiError(429, 'Demasiadas solicitudes. Intenta de nuevo en 1 minuto.'))
    mostrar(true)
    const boton = await screen.findByRole('button', { name: /sigue ahí/i })
    await vi.waitFor(() => expect(boton).toBeEnabled())
    await user.click(boton)
    expect(await screen.findByRole('alert')).toHaveTextContent('Demasiadas solicitudes')
  })

  it('con 3 «Ya no hay agua» la fila pasa a histórico y deja de ofrecer votos', async () => {
    const user = userEvent.setup()
    vi.mocked(api.get).mockResolvedValue(detalle(false))
    vi.mocked(api.post).mockResolvedValue({ folio: 'ENC-2026-000318', tipo: 'ya_no_hay_agua', estado_reporte: 'Histórico', vigencia: { vigente_hasta: '2026-11-26T02:05:00Z', sigue_ahi: 9, ya_no_hay_agua: 3 }, mensaje: 'El encharcamiento pasó a histórico.' })
    mostrar(true)
    const boton = await screen.findByRole('button', { name: /ya no hay agua/i })
    await vi.waitFor(() => expect(boton).toBeEnabled())
    await user.click(boton)
    expect(await screen.findByText('Pasó a histórico')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /sigue ahí/i })).not.toBeInTheDocument()
  })

  it('estado vacío cuando no hay encharcamientos vigentes', () => {
    mostrar(false, [])
    expect(screen.getByText('Sin encharcamientos vigentes')).toBeInTheDocument()
  })
})
