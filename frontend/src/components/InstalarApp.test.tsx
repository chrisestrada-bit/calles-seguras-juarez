import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { InstalarApp, SeccionInstalacion } from './InstalarApp'

/** El estado vive en el módulo (como en el navegador), así que las pruebas siguen el ciclo en orden. */
const ofrecer = (outcome: 'accepted' | 'dismissed') => {
  const prompt = vi.fn().mockResolvedValue(undefined)
  const evento = Object.assign(new Event('beforeinstallprompt', { cancelable: true }), { prompt, userChoice: Promise.resolve({ outcome }) })
  act(() => { window.dispatchEvent(evento) })
  return { prompt, evento }
}

describe('Instalar aplicación (HU-08.4)', () => {
  it('sin aviso del navegador no hay botón y el pie explica cómo instalar a mano', () => {
    render(<><InstalarApp /><SeccionInstalacion /></>)
    expect(screen.queryByRole('button', { name: 'Instalar aplicación' })).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('todavía no ofrece la instalación automática')
  })

  it('con beforeinstallprompt muestra el botón, abre el diálogo y tras rechazarlo vuelve a las instrucciones', async () => {
    const user = userEvent.setup()
    render(<><InstalarApp /><SeccionInstalacion /></>)
    const { prompt, evento } = ofrecer('dismissed')
    expect(evento.defaultPrevented).toBe(true)
    expect(screen.getAllByRole('button', { name: 'Instalar aplicación' })).toHaveLength(2)
    await user.click(screen.getAllByRole('button', { name: 'Instalar aplicación' })[0])
    expect(prompt).toHaveBeenCalledTimes(1)
    expect(screen.queryByRole('button', { name: 'Instalar aplicación' })).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('todavía no ofrece')
  })

  it('conserva el aviso recibido antes de montar y al aceptar indica que ya está instalada', async () => {
    const user = userEvent.setup()
    ofrecer('accepted')
    render(<SeccionInstalacion />)
    const seccion = screen.getByRole('region', { name: /en tu dispositivo/i })
    await user.click(within(seccion).getByRole('button', { name: 'Instalar aplicación' }))
    expect(screen.getByRole('status')).toHaveTextContent('ya está instalada')
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
