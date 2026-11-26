import { act, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { detectarPlataforma } from '../hooks/useInstalacion'
import { InstalarApp, SeccionInstalacion } from './InstalarApp'

/** El estado vive en el módulo (como en el navegador), así que las pruebas siguen el ciclo en orden. */
const ofrecer = (outcome: 'accepted' | 'dismissed') => {
  const prompt = vi.fn().mockResolvedValue(undefined)
  const evento = Object.assign(new Event('beforeinstallprompt', { cancelable: true }), { prompt, userChoice: Promise.resolve({ outcome }) })
  act(() => { window.dispatchEvent(evento) })
  return { prompt, evento }
}

const montar = () => render(<><header><InstalarApp /></header><SeccionInstalacion /></>)
const cabecera = () => within(screen.getByRole('banner')).getByRole('button')
const apartado = () => screen.getByRole('region', { name: /en tu dispositivo/i })
const enPie = (name: string) => within(apartado()).queryByRole('button', { name })

describe('Instalar aplicación (HU-08.4)', () => {
  it('sin beforeinstallprompt el pie ofrece un botón que muestra y oculta los pasos', async () => {
    const user = userEvent.setup()
    montar()
    expect(apartado()).toHaveAttribute('id', 'instalar-app')
    expect(enPie('Instalar aplicación')).not.toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('no ofrece en este momento')
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
    const boton = enPie('Cómo instalar la app') as HTMLElement
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    await user.click(boton)
    expect(boton).toHaveAttribute('aria-expanded', 'true')
    expect(within(screen.getByRole('list')).getAllByRole('listitem').length).toBeGreaterThan(1)
    await user.click(boton)
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  it('sin beforeinstallprompt el botón superior abre los pasos y lleva al apartado', async () => {
    const user = userEvent.setup()
    const desplazar = vi.fn()
    montar()
    apartado().scrollIntoView = desplazar
    expect(cabecera()).toHaveAccessibleName('Cómo instalar la app')
    await user.click(cabecera())
    expect(screen.getByRole('list')).toBeInTheDocument()
    expect(apartado()).toHaveFocus()
    expect(desplazar).toHaveBeenCalledWith({ behavior: 'smooth', block: 'center' })
  })

  it('con beforeinstallprompt el botón superior abre el diálogo y, si se rechaza, vuelve a la guía', async () => {
    const user = userEvent.setup()
    montar()
    const { prompt, evento } = ofrecer('dismissed')
    expect(evento.defaultPrevented).toBe(true)
    expect(cabecera()).toHaveAccessibleName('Instalar app')
    await user.click(cabecera())
    expect(prompt).toHaveBeenCalledTimes(1)
    expect(apartado()).not.toHaveFocus()
    expect(cabecera()).toHaveAccessibleName('Cómo instalar la app')
    await user.click(cabecera())
    expect(prompt).toHaveBeenCalledTimes(1)
    expect(apartado()).toHaveFocus()
  })

  it('conserva el aviso recibido antes de montar; ya instalada (appinstalled) muestra el estado sin guía', async () => {
    const user = userEvent.setup()
    const { prompt } = ofrecer('accepted')
    montar()
    await user.click(enPie('Instalar aplicación') as HTMLElement)
    expect(screen.getByRole('status')).toHaveTextContent('ya está instalada')
    expect(within(apartado()).queryByRole('button')).not.toBeInTheDocument()
    await user.click(cabecera())
    expect(prompt).toHaveBeenCalledTimes(1)
    expect(apartado()).toHaveFocus()
  })

  it('abierta en modo standalone muestra que ya está instalada y no ofrece pasos', async () => {
    vi.resetModules()
    vi.stubGlobal('matchMedia', (query: string) => ({ matches: query === '(display-mode: standalone)', addEventListener: () => {} }))
    const { SeccionInstalacion: Seccion } = await import('./InstalarApp')
    render(<Seccion />)
    expect(screen.getByRole('status')).toHaveTextContent('ya está instalada')
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
    vi.unstubAllGlobals()
  })
})

describe('detectarPlataforma', () => {
  it.each([
    ['ios', 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1', 5],
    ['ios', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.0 Safari/605.1.15', 5],
    ['escritorio-safari', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.0 Safari/605.1.15', 0],
    ['android', 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/130.0 Mobile Safari/537.36', 5],
    ['android-edge', 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/130.0 Mobile Safari/537.36 EdgA/130.0', 5],
    ['android-samsung', 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 SamsungBrowser/26.0 Chrome/122.0 Mobile Safari/537.36', 5],
    ['android-firefox', 'Mozilla/5.0 (Android 14; Mobile; rv:130.0) Gecko/130.0 Firefox/130.0', 5],
    ['escritorio-firefox', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0', 0],
    ['escritorio', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36', 0],
  ])('%s', (esperada, agente, puntos) => {
    expect(detectarPlataforma(agente, puntos)).toBe(esperada)
  })
})
