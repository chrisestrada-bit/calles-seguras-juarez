import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import type { Colonia } from '../types/api'
import { BuscadorCalle, type CalleSugerida } from './BuscadorCalle'

const colonia = (id: number, nombre: string, cp: string): Colonia => ({ id, nombre, codigo_postal: cp, sector: { id: 1, nombre: 'Centro' }, centro: { latitud: 31.7, longitud: -106.4 } })
const COLONIAS = [colonia(1, 'Partido Romero', '32030'), colonia(2, 'Partido Iglesias', '32528'), colonia(3, 'Centro', '32000')]

function Prueba({ calles = [] as CalleSugerida[], ...espias }: { calles?: CalleSugerida[]; onEnviar?: () => void; onElegirColonia?: (c: Colonia) => void; onElegirCalle?: (c: string) => void }) {
  const [valor, setValor] = useState('')
  return <BuscadorCalle valor={valor} onCambiar={setValor} onEnviar={espias.onEnviar ?? vi.fn()} colonias={COLONIAS} calles={calles} onElegirColonia={espias.onElegirColonia ?? vi.fn()} onElegirCalle={espias.onElegirCalle ?? vi.fn()} />
}

describe('<BuscadorCalle /> (HU-04.2 búsqueda en vivo con sugerencias)', () => {
  it('sugiere colonias por nombre sin acentos mientras se escribe', async () => {
    const user = userEvent.setup()
    render(<Prueba />)
    await user.type(screen.getByRole('combobox', { name: /por qué calle/i }), 'partido')
    const opciones = screen.getAllByRole('option')
    expect(opciones.map((o) => o.textContent)).toEqual(expect.arrayContaining([expect.stringContaining('Partido Romero (C.P. 32030)'), expect.stringContaining('Partido Iglesias (C.P. 32528)')]))
    expect(screen.getByRole('status')).toHaveTextContent('2 sugerencias')
  })

  it('sugiere colonias por código postal 32xxx y se eligen con teclado', async () => {
    const user = userEvent.setup()
    const onElegirColonia = vi.fn()
    render(<Prueba onElegirColonia={onElegirColonia} />)
    const campo = screen.getByRole('combobox', { name: /por qué calle/i })
    await user.type(campo, '3203')
    expect(screen.getAllByRole('option')).toHaveLength(1)
    await user.keyboard('{ArrowDown}')
    expect(campo).toHaveAttribute('aria-activedescendant', screen.getByRole('option').id)
    await user.keyboard('{Enter}')
    expect(onElegirColonia).toHaveBeenCalledWith(COLONIAS[0])
  })

  it('ofrece el folio exacto y las calles con reportes que coinciden', async () => {
    const user = userEvent.setup()
    const onElegirCalle = vi.fn()
    const { rerender } = render(<Prueba />)
    await user.type(screen.getByRole('combobox'), 'enc-2026-000162')
    expect(screen.getByRole('option', { name: /ENC-2026-000162/ })).toBeInTheDocument()
    rerender(<Prueba calles={[{ calle: 'Av. Tecnológico', colonia: 'Pronaf' }]} onElegirCalle={onElegirCalle} />)
    await user.clear(screen.getByRole('combobox'))
    await user.type(screen.getByRole('combobox'), 'tecno')
    await user.click(screen.getByRole('option', { name: /Av\. Tecnológico/ }))
    expect(onElegirCalle).toHaveBeenCalledWith('Av. Tecnológico')
  })

  it('Enter sin opción activa y el botón «Consultar» envían la búsqueda; Esc cierra las sugerencias', async () => {
    const user = userEvent.setup()
    const onEnviar = vi.fn()
    render(<Prueba onEnviar={onEnviar} />)
    const campo = screen.getByRole('combobox')
    await user.type(campo, 'partido')
    expect(campo).toHaveAttribute('aria-expanded', 'true')
    await user.keyboard('{Escape}')
    expect(campo).toHaveAttribute('aria-expanded', 'false')
    await user.keyboard('{Enter}')
    await user.click(screen.getByRole('button', { name: 'Consultar' }))
    expect(onEnviar).toHaveBeenCalledTimes(2)
  })
})
