import { act, render } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../services/api'
import { AuthProvider } from './AuthContext'

vi.mock('../services/api', async (original) => ({ ...(await original<typeof import('../services/api')>()), api: { post: vi.fn() } }))

const RESPUESTA = { access_token: 'token-nuevo', token_type: 'bearer', expira_en_segundos: 1800, usuario: { id: 'u-1', nombre: 'Ana', rol: 'ciudadano' } }
const llamadasRenovar = () => vi.mocked(api.post).mock.calls.filter(([ruta]) => ruta === '/api/v1/auth/renovar').length

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date', 'setTimeout', 'clearTimeout'] })
  vi.setSystemTime(new Date('2026-11-22T12:00:00-07:00'))
  vi.mocked(api.post).mockReset()
  vi.mocked(api.post).mockResolvedValue(RESPUESTA)
  localStorage.setItem('calles-seguras.access-token', 'token-guardado')
  localStorage.setItem('calles-seguras.usuario', JSON.stringify(RESPUESTA.usuario))
})

afterEach(() => {
  vi.useRealTimers()
})

describe('<AuthProvider /> sesión deslizante (auditoría final, M4)', () => {
  it('renueva el token con la actividad, como máximo una vez cada 10 minutos', async () => {
    render(<AuthProvider><p>contenido</p></AuthProvider>)
    await act(async () => { await Promise.resolve() })
    expect(llamadasRenovar()).toBe(1) // token recuperado de localStorage: se renueva al primer uso
    expect(localStorage.getItem('calles-seguras.access-token')).toBe('token-nuevo')

    await act(async () => { window.dispatchEvent(new Event('keydown')) })
    expect(llamadasRenovar()).toBe(1) // actividad reciente: no se vuelve a pedir

    vi.setSystemTime(new Date('2026-11-22T12:11:00-07:00'))
    await act(async () => { window.dispatchEvent(new Event('mousedown')); await Promise.resolve() })
    expect(llamadasRenovar()).toBe(2) // 11 min después, con actividad, se renueva antes de que venza a los 30
  })

  it('sin actividad no renueva: la sesión vence por inactividad', async () => {
    render(<AuthProvider><p>contenido</p></AuthProvider>)
    await act(async () => { await Promise.resolve() })
    vi.setSystemTime(new Date('2026-11-22T12:20:00-07:00'))
    expect(llamadasRenovar()).toBe(1)
  })
})
