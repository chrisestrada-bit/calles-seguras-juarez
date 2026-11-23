import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { filtrarArchivos, MAX_BYTES_FOTO } from '../services/fotos'
import { FotoPicker } from './FotoPicker'

/** Crea un File con el tamaño exacto pedido sin reservar la memoria real. */
function archivo(nombre: string, tipo: string, bytes = 1024): File {
  const f = new File(['x'], nombre, { type: tipo })
  Object.defineProperty(f, 'size', { value: bytes })
  return f
}

function Contenedor({ inicial = [] as File[] }) {
  const [archivos, setArchivos] = useState(inicial)
  return <FotoPicker archivos={archivos} onChange={setArchivos} />
}

beforeEach(() => {
  URL.createObjectURL = vi.fn(() => 'blob:prueba')
  URL.revokeObjectURL = vi.fn()
})

describe('filtrarArchivos (HU-02.4)', () => {
  it('acepta JPG y PNG y separa los errores por categoría', () => {
    const { aceptados, errores } = filtrarArchivos([], [
      archivo('a.jpg', 'image/jpeg'),
      archivo('b.png', 'image/png'),
      archivo('c.gif', 'image/gif'),
      archivo('grande.png', 'image/png', MAX_BYTES_FOTO + 1),
    ])
    expect(aceptados.map((f) => f.name)).toEqual(['a.jpg', 'b.png'])
    expect(errores.formato).toEqual(['c.gif'])
    expect(errores.tamano).toEqual(['grande.png'])
    expect(errores.limite).toEqual([])
  })

  it('acepta exactamente 5 MB y rechaza 5 MB + 1 byte', () => {
    const justo = filtrarArchivos([], [archivo('justo.png', 'image/png', MAX_BYTES_FOTO)])
    expect(justo.aceptados).toHaveLength(1)
    const pasado = filtrarArchivos([], [archivo('pasado.png', 'image/png', MAX_BYTES_FOTO + 1)])
    expect(pasado.aceptados).toHaveLength(0)
    expect(pasado.errores.tamano).toEqual(['pasado.png'])
  })

  it('no pasa de 3 imágenes', () => {
    const { aceptados, errores } = filtrarArchivos(
      [archivo('1.jpg', 'image/jpeg'), archivo('2.jpg', 'image/jpeg')],
      [archivo('3.jpg', 'image/jpeg'), archivo('4.jpg', 'image/jpeg')],
    )
    expect(aceptados).toHaveLength(3)
    expect(errores.limite).toEqual(['4.jpg'])
  })
})

describe('<FotoPicker />', () => {
  it('muestra el contador 0/3 y no hay vista previa al inicio', () => {
    render(<Contenedor />)
    expect(screen.getByText('0/3')).toBeInTheDocument()
    expect(screen.queryByRole('list', { name: /fotografías seleccionadas/i })).not.toBeInTheDocument()
  })

  it('agrega fotos con vista previa, nombre y tamaño, y permite quitarlas', async () => {
    const user = userEvent.setup()
    render(<Contenedor />)
    const entrada = screen.getByLabelText(/agregar fotografías/i)
    await user.upload(entrada, [archivo('baches.jpg', 'image/jpeg', 2048), archivo('calle.png', 'image/png', 3 * 1024 * 1024)])
    expect(screen.getByText('2/3')).toBeInTheDocument()
    expect(screen.getByText('baches.jpg')).toBeInTheDocument()
    expect(screen.getByText('2 KB')).toBeInTheDocument()
    expect(screen.getByText('3.0 MB')).toBeInTheDocument()
    expect(screen.getByAltText(/vista previa de baches\.jpg/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /quitar baches\.jpg/i }))
    expect(screen.getByText('1/3')).toBeInTheDocument()
    expect(screen.queryByText('baches.jpg')).not.toBeInTheDocument()
  })

  it('muestra mensajes de error separados para formato, tamaño y límite', async () => {
    const user = userEvent.setup({ applyAccept: false })
    render(<Contenedor inicial={[archivo('1.jpg', 'image/jpeg'), archivo('2.jpg', 'image/jpeg')]} />)
    const entrada = screen.getByLabelText(/agregar fotografías/i)
    await user.upload(entrada, [
      archivo('documento.pdf', 'application/pdf'),
      archivo('enorme.png', 'image/png', MAX_BYTES_FOTO + 1),
      archivo('3.jpg', 'image/jpeg'),
      archivo('4.jpg', 'image/jpeg'),
    ])
    const alertas = screen.getAllByRole('alert').map((a) => a.textContent ?? '')
    expect(alertas).toHaveLength(3)
    expect(alertas.some((t) => /formato no permitido.*documento\.pdf/i.test(t))).toBe(true)
    expect(alertas.some((t) => /5 MB.*enorme\.png/i.test(t))).toBe(true)
    expect(alertas.some((t) => /límite de 3.*4\.jpg/i.test(t))).toBe(true)
    expect(screen.getByText('3/3')).toBeInTheDocument()
  })
})
