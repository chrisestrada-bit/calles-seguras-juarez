import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { filtrarColonias } from '../services/catalogos'
import type { Colonia } from '../types/api'
import { RecurrentBadge } from './ui'

describe('<RecurrentBadge /> (HU-03.4)', () => {
  it('muestra el texto «Punto recurrente» (no sólo color) y los días para lectores de pantalla', () => {
    render(<RecurrentBadge dias={4} />)
    expect(screen.getByText(/punto recurrente/i)).toBeInTheDocument()
    expect(screen.getByText(/4 días distintos este año/i)).toBeInTheDocument()
    expect(screen.getByTitle(/4 días distintos este año/i)).toBeInTheDocument()
  })

  it('funciona sin conteo de días', () => {
    render(<RecurrentBadge />)
    expect(screen.getByText(/punto recurrente/i)).toBeInTheDocument()
  })
})

const colonia = (id: number, nombre: string, cp: string | undefined): Colonia => ({ id, nombre, codigo_postal: cp, sector: { id: 1, nombre: 'Centro' }, centro: { latitud: 31.7, longitud: -106.4 } })
const catalogo = [colonia(1, 'Álamos', '32310'), colonia(2, 'Pronaf', '32315'), colonia(3, 'Partido Escobedo', '32330'), colonia(4, 'Sin CP', undefined)]

describe('filtrarColonias (buscador de colonias de interés y resumen)', () => {
  it('no busca con menos de 2 caracteres', () => {
    expect(filtrarColonias(catalogo, 'a')).toEqual([])
    expect(filtrarColonias(catalogo, '   ')).toEqual([])
  })

  it('ignora acentos y mayúsculas', () => {
    expect(filtrarColonias(catalogo, 'ALAMOS').map((c) => c.id)).toEqual([1])
    expect(filtrarColonias(catalogo, 'escobedo').map((c) => c.id)).toEqual([3])
  })

  it('busca por prefijo de código postal', () => {
    expect(filtrarColonias(catalogo, '3231').map((c) => c.id)).toEqual([1, 2])
    expect(filtrarColonias(catalogo, '32330').map((c) => c.id)).toEqual([3])
  })

  it('respeta el límite de resultados', () => {
    expect(filtrarColonias(catalogo, '32', 2)).toHaveLength(2)
  })
})
