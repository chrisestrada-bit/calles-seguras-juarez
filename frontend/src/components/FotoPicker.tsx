import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { Icon } from './Icon';
import {
  filtrarArchivos, formatoTamano, MAX_BYTES_FOTO, MAX_FOTOS, SIN_ERRORES_FOTOS, type ErroresFotos,
} from '../services/fotos';

interface Props {
  archivos: File[];
  onChange: (archivos: File[]) => void;
  disabled?: boolean;
}

/** HU-02.4: selector de hasta 3 fotos JPG/PNG (5 MB c/u) con contador, vista previa y errores separados. */
export function FotoPicker({ archivos, onChange, disabled }: Props) {
  const id = useId();
  const entrada = useRef<HTMLInputElement>(null);
  const [errores, setErrores] = useState<ErroresFotos>(SIN_ERRORES_FOTOS);
  const vistas = useMemo(() => archivos.map((archivo) => URL.createObjectURL(archivo)), [archivos]);
  useEffect(() => () => vistas.forEach((url) => URL.revokeObjectURL(url)), [vistas]);

  const elegir = (lista: FileList | null) => {
    const { aceptados, errores: nuevos } = filtrarArchivos(archivos, Array.from(lista ?? []));
    setErrores(nuevos);
    onChange(aceptados);
    if (entrada.current) entrada.current.value = ''; // permite volver a elegir el mismo archivo
  };
  const quitar = (indice: number) => { setErrores(SIN_ERRORES_FOTOS); onChange(archivos.filter((_, i) => i !== indice)); };
  const lleno = archivos.length >= MAX_FOTOS;

  return (
    <div className="photo-picker">
      <div className="photo-picker__head">
        <label htmlFor={id} className={`button button--secondary button--sm${lleno || disabled ? ' is-disabled' : ''}`}>
          <Icon name="camera" size={18} />Agregar fotografías
        </label>
        <input
          ref={entrada} id={id} className="visually-hidden" type="file" multiple accept="image/jpeg,image/png"
          disabled={disabled || lleno} onChange={(e) => elegir(e.target.files)} aria-describedby={`${id}-ayuda`}
        />
        <p className="photo-picker__count" aria-live="polite"><strong>{archivos.length}/{MAX_FOTOS}</strong> fotografías</p>
      </div>
      <p id={`${id}-ayuda`} className="field-help">Opcional. Hasta {MAX_FOTOS} imágenes JPG o PNG de máximo {MAX_BYTES_FOTO / (1024 * 1024)} MB cada una. No incluyas rostros ni placas si puedes evitarlo.</p>

      {errores.formato.length > 0 && <p className="form-error" role="alert"><Icon name="alert" size={16} />Formato no permitido (sólo JPG o PNG): {errores.formato.join(', ')}.</p>}
      {errores.tamano.length > 0 && <p className="form-error" role="alert"><Icon name="alert" size={16} />Supera el tamaño máximo de 5 MB: {errores.tamano.join(', ')}.</p>}
      {errores.limite.length > 0 && <p className="form-error" role="alert"><Icon name="alert" size={16} />Límite de {MAX_FOTOS} imágenes alcanzado. No se agregó: {errores.limite.join(', ')}.</p>}

      {archivos.length > 0 && (
        <ul className="photo-picker__list" aria-label="Fotografías seleccionadas">
          {archivos.map((archivo, i) => (
            <li className="photo-picker__item" key={`${archivo.name}-${archivo.size}-${i}`}>
              <img src={vistas[i]} alt={`Vista previa de ${archivo.name}`} width={96} height={72} />
              <div><strong>{archivo.name}</strong><span>{formatoTamano(archivo.size)}</span></div>
              <button className="button button--quiet button--sm" type="button" onClick={() => quitar(i)} disabled={disabled} aria-label={`Quitar ${archivo.name}`}>
                <Icon name="close" size={16} />Quitar
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
