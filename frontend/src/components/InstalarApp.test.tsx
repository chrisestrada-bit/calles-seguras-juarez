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

/** En la app la cabecera y el pie conviven: el botón superior es «Instalar app» y el del pie, «Instalar aplicación». */
const montar = () => render(<><InstalarApp /><SeccionInstalacion /></>)
const superior = () => screen.getByRole('button', { name: 'Instalar app' })
const apartado = () => screen.getByRole('region', { name: /en tu dispositivo/i })

describe('Instalar aplicación (HU-08.4)', () => {
  it('sin aviso del navegador el botón superior existe y lleva a la guía del pie', async () => {
    const user = userEvent.setup()
    const desplazar = vi.fn()
    montar()
    apartado().scrollIntoView = desplazar
    expect(apartado()).toHaveAttribute('id', 'instalar-app')
    expect(screen.queryByRole('button', { name: 'Instalar aplicación' })).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('todavía no ofrece la instalación automática')
    await user.click(superior())
    expect(apartado()).toHaveFocus()
    expect(desplazar).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' })
  })

  it('con beforeinstallprompt el botón superior abre el diálogo y, si se rechaza, vuelve a llevar a la guía', async () => {
    const user = userEvent.setup()
    montar()
    const { prompt, evento } = ofrecer('dismissed')
    expect(evento.defaultPrevented).toBe(true)
    await user.click(superior())
    expect(prompt).toHaveBeenCalledTimes(1)
    expect(apartado()).not.toHaveFocus()
    expect(screen.getByRole('status')).toHaveTextContent('todavía no ofrece')
    await user.click(superior())
    expect(prompt).toHaveBeenCalledTimes(1)
    expect(apartado()).toHaveFocus()
  })

  it('conserva el aviso recibido antes de montar; ya instalada, el botón superior sigue y muestra el estado', async () => {
    const user = userEvent.setup()
    const { prompt } = ofrecer('accepted')
    montar()
    await user.click(within(apartado()).getByRole('button', { name: 'Instalar aplicación' }))
    expect(screen.getByRole('status')).toHaveTextContent('ya está instalada')
    expect(screen.queryByRole('button', { name: 'Instalar aplicación' })).not.toBeInTheDocument()
    await user.click(superior())
    expect(prompt).toHaveBeenCalledTimes(1)
    expect(apartado()).toHaveFocus()
  })
})
