import { describe, expect, it } from 'vitest';
import { ApiError, erroresPorCampo, mensajeDeError, textoEspera } from './api';

describe('mensajes de error de la API', () => {
  it('429 con Retry-After incluye el tiempo de espera', () => {
    const e = new ApiError(429, 'Alcanzaste el máximo de 10 reportes por hora.', undefined, 1500);
    expect(mensajeDeError(e)).toContain('25 minutos');
  });
  it('error ajeno a la API usa el mensaje genérico', () => {
    expect(mensajeDeError(new Error('x'))).toBe('No fue posible completar la solicitud. Intenta de nuevo.');
  });
  it('422 expone mensajes por campo', () => {
    const e = new ApiError(422, 'Revisa', { codigo: 'VALIDACION', mensaje: 'Revisa', detalles: [{ campo: 'calle', mensaje: 'Obligatoria' }] });
    expect(erroresPorCampo(e)).toEqual({ calle: 'Obligatoria' });
  });
  it('textoEspera singular y plural', () => {
    expect(textoEspera(1)).toBe('1 segundo');
    expect(textoEspera(30)).toBe('30 segundos');
  });
});
