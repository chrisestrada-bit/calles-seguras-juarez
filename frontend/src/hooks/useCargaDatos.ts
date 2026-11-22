import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../services/api';

export type EstadoCarga = 'inactivo' | 'cargando' | 'listo' | 'error';

interface Resultado<T> { clave: string; datos?: T; error?: string }

/**
 * Carga datos de la API para una `clave` (p. ej. la URL con sus filtros).
 *
 * El estado de carga se deriva comparando la clave pedida con la de la última respuesta, así el efecto sólo
 * actualiza el estado desde callbacks asíncronos (sin renders en cascada) y una respuesta tardía de una
 * consulta anterior nunca sustituye a la vigente. `cargar` debe ser estable (definida fuera del componente).
 * Con `clave = null` no se consulta nada.
 */
export function useCargaDatos<T>(clave: string | null, cargar: (clave: string) => Promise<T>, mensajeError = 'No fue posible cargar la información.') {
  const [resultado, setResultado] = useState<Resultado<T> | null>(null);

  useEffect(() => {
    if (clave === null) return;
    let activo = true;
    cargar(clave)
      .then((datos) => { if (activo) setResultado({ clave, datos }); })
      .catch((e: unknown) => { if (activo) setResultado({ clave, error: e instanceof ApiError ? e.message : mensajeError }); });
    return () => { activo = false; };
  }, [clave, cargar, mensajeError]);

  const vigente = resultado !== null && resultado.clave === clave ? resultado : null;
  const estado: EstadoCarga = clave === null ? 'inactivo' : vigente === null ? 'cargando' : vigente.error !== undefined ? 'error' : 'listo';

  /** Ajusta localmente los datos vigentes (p. ej. tras cambiar el rol de una fila) sin volver a consultar. */
  const actualizar = useCallback((cambio: (datos: T) => T) => {
    setResultado((actual) => (actual?.datos !== undefined ? { ...actual, datos: cambio(actual.datos) } : actual));
  }, []);

  return { estado, datos: vigente?.datos, error: vigente?.error ?? '', actualizar };
}

/** Cargador estándar: la clave es la ruta de la API; un sufijo `#n` sólo fuerza a recargar. */
export function obtenerJson<T>(clave: string): Promise<T> {
  return api.get<T>(clave.split('#')[0]);
}
