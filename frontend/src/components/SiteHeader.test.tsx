import { render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../context/authContexto'
import { SiteHeader } from './SiteHeader'

const visitante: AuthContextValue = {
  usuario: null, token: null, rolActivo: 'visitante', autenticado: false,
  iniciarSesion: vi.fn(), renovarSesion: vi.fn(), cerrarSesion: vi.fn(), cambiarRolActivo: vi.fn(),
}
const enlace: AuthContextValue = { ...visitante, autenticado: true, rolActivo: 'enlace_municipal', usuario: { id: '1', nombre: 'Persona Enlace', rol: 'enlace_municipal' } as AuthContextValue['usuario'] }

describe('<SiteHeader /> (HU-08.4)', () => {
  it.each([['visitante', visitante], ['con sesión', enlace]])('%s: «Instalar app» aparece junto a la marca sin esperar al navegador', (_, sesion) => {
    render(<AuthContext.Provider value={sesion}><SiteHeader /></AuthContext.Provider>)
    const marca = screen.getByRole('link', { name: 'Calles Seguras Juárez, inicio' }).parentElement as HTMLElement
    expect(within(marca).getByRole('button', { name: 'Instalar app' })).toBeInTheDocument()
  })
})
