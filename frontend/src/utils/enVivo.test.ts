import { describe, expect, it } from 'vitest'
import type { ReporteResumenPublico } from '../types/api'
import { coincideConFiltros, fusionarEnVivo, SIN_FILTROS, type FiltrosLista, type Vivos } from './enVivo'

function enc(folio: string, extra: Partial<ReporteResumenPublico> = {}): ReporteResumenPublico {
  return {
    folio, tipo_dano: 'Encharcamiento', estado: 'Activo', etiqueta_publica: 'Activo', severidad: 'Media',
    ubicacion: { latitud: 31.7, longitud: -106.4 }, calle: 'Av. de las Torres', colonia: { id: 5, nombre: 'Centro' },
    created_at: '2026-11-22T10:00:00-07:00', longevidad_dias: null, vigencia: null, nivel_agua: 'cubre un carril', ...extra,
  }
}

const filtros = (cambios: Partial<FiltrosLista> = {}): FiltrosLista => ({ ...SIN_FILTROS, ...cambios })

describe('coincideConFiltros (filtros de consulta)', () => {
  it('sin filtros acepta cualquier encharcamiento y rechaza el pavimento', () => {
    expect(coincideConFiltros(enc('ENC-2026-000001'), filtros())).toBe(true)
    expect(coincideConFiltros(enc('BCH-2026-000001', { tipo_dano: 'Bache' }), filtros())).toBe(false)
  })

  it('respeta estado, colonia, calle y rango de fechas (en hora de Ciudad Juárez)', () => {
    const r = enc('ENC-2026-000002')
    expect(coincideConFiltros(r, filtros({ estado: 'Histórico' }))).toBe(false)
    expect(coincideConFiltros(r, filtros({ colonia: '5' }))).toBe(true)
    expect(coincideConFiltros(r, filtros({ colonia: '6' }))).toBe(false)
    expect(coincideConFiltros(r, filtros({ busqueda: 'torres' }))).toBe(true)
    expect(coincideConFiltros(r, filtros({ busqueda: 'tecnologico' }))).toBe(false)
    expect(coincideConFiltros(r, filtros({ busqueda: 'ab' }))).toBe(true) // menos de 3 letras: no filtra
    expect(coincideConFiltros(r, filtros({ desde: '2026-11-22', hasta: '2026-11-22' }))).toBe(true)
    expect(coincideConFiltros(r, filtros({ desde: '2026-11-23' }))).toBe(false)
    expect(coincideConFiltros(r, filtros({ hasta: '2026-11-21' }))).toBe(false)
  })

  it('una búsqueda por folio sólo acepta ese folio', () => {
    const r = enc('ENC-2026-000003')
    expect(coincideConFiltros(r, filtros({ busqueda: 'enc-2026-000003' }))).toBe(true)
    expect(coincideConFiltros(r, filtros({ busqueda: 'ENC-2026-000004' }))).toBe(false)
  })
})

describe('fusionarEnVivo (HU-08.3: sin duplicar y sin borrar filtros)', () => {
  const base = [enc('ENC-2026-000010', { created_at: '2026-11-22T09:00:00-07:00' }), enc('ENC-2026-000011', { created_at: '2026-11-22T08:00:00-07:00' })]

  it('inserta los nuevos al inicio y nunca duplica un folio', () => {
    const vivos: Vivos = { 'ENC-2026-000012': enc('ENC-2026-000012', { created_at: '2026-11-22T11:00:00-07:00' }), 'ENC-2026-000010': enc('ENC-2026-000010') }
    const r = fusionarEnVivo(base, vivos, filtros(), true)
    expect(r.map((x) => x.folio)).toEqual(['ENC-2026-000012', 'ENC-2026-000010', 'ENC-2026-000011'])
    expect(new Set(r.map((x) => x.folio)).size).toBe(r.length)
  })

  it('el mismo evento aplicado dos veces da el mismo resultado', () => {
    const vivos: Vivos = { 'ENC-2026-000012': enc('ENC-2026-000012') }
    const una = fusionarEnVivo(base, vivos, filtros(), true)
    const dos = fusionarEnVivo(una, vivos, filtros(), true)
    expect(dos.map((x) => x.folio)).toEqual(una.map((x) => x.folio))
  })

  it('actualiza un folio existente (p. ej. pasa a Histórico) sin cambiar su posición', () => {
    const vivos: Vivos = { 'ENC-2026-000010': enc('ENC-2026-000010', { estado: 'Histórico' }) }
    const r = fusionarEnVivo(base, vivos, filtros(), true)
    expect(r[0]).toMatchObject({ folio: 'ENC-2026-000010', estado: 'Histórico' })
  })

  it('retira los rechazados (null) y los que dejan de cumplir el filtro activo', () => {
    const retirado: Vivos = { 'ENC-2026-000010': null }
    expect(fusionarEnVivo(base, retirado, filtros(), true).map((x) => x.folio)).toEqual(['ENC-2026-000011'])
    const vivos: Vivos = { 'ENC-2026-000011': enc('ENC-2026-000011', { estado: 'Histórico' }) }
    expect(fusionarEnVivo(base, vivos, filtros({ estado: 'Activo' }), true).map((x) => x.folio)).toEqual(['ENC-2026-000010'])
  })

  it('no inserta eventos que no cumplen los filtros activos', () => {
    const vivos: Vivos = { 'ENC-2026-000020': enc('ENC-2026-000020', { colonia: { id: 9, nombre: 'Otra' } }) }
    expect(fusionarEnVivo(base, vivos, filtros({ colonia: '5' }), true)).toHaveLength(2)
  })

  it('fuera de la primera página sólo actualiza o retira, no inserta', () => {
    const vivos: Vivos = { 'ENC-2026-000020': enc('ENC-2026-000020') }
    expect(fusionarEnVivo(base, vivos, filtros(), false)).toHaveLength(2)
  })

  it('con la página llena no inserta reportes más viejos que el último visible (sondeo)', () => {
    const llena = Array.from({ length: 3 }, (_, i) => enc(`ENC-2026-0001${i}0`, { created_at: `2026-11-22T1${i}:00:00-07:00` })).reverse()
    const viejo: Vivos = { 'ENC-2026-000999': enc('ENC-2026-000999', { created_at: '2026-01-01T10:00:00-07:00' }) }
    expect(fusionarEnVivo(llena, viejo, filtros(), true, 3)).toHaveLength(3)
    const nuevo: Vivos = { 'ENC-2026-000998': enc('ENC-2026-000998', { created_at: '2026-11-22T20:00:00-07:00' }) }
    const r = fusionarEnVivo(llena, nuevo, filtros(), true, 3)
    expect(r).toHaveLength(3)
    expect(r[0].folio).toBe('ENC-2026-000998')
  })
})
