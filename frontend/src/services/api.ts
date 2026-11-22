import type { ErrorApi, RespuestaError } from '../types/api';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');
const TOKEN_KEY = 'calles-seguras.access-token';

export class ApiError extends Error {
  readonly status: number;
  readonly codigo?: string;
  readonly detalles: ErrorApi['detalles'];
  readonly retryAfter?: number;

  constructor(status: number, mensaje: string, error?: ErrorApi, retryAfter?: number) {
    super(mensaje);
    this.name = 'ApiError';
    this.status = status;
    this.codigo = error?.codigo;
    this.detalles = error?.detalles ?? [];
    this.retryAfter = retryAfter;
  }
}

let onUnauthorized: (() => void) | undefined;

export function configurarSesionExpirada(callback: () => void): void {
  onUnauthorized = callback;
}

export function obtenerToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function guardarToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function eliminarToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

function mensajePorEstado(status: number, fallback: string): string {
  switch (status) {
    case 403: return 'Tu rol no tiene permiso para realizar esta acción.';
    case 422: return 'Revisa los datos marcados antes de continuar.';
    case 429: return 'Hiciste demasiadas solicitudes en poco tiempo. Espera unos segundos e intenta de nuevo.';
    default: return fallback;
  }
}

async function leerError(response: Response): Promise<ErrorApi | undefined> {
  try {
    const body = await response.json() as RespuestaError;
    return body.error;
  } catch {
    return undefined;
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');

  const token = obtenerToken();
  const hayTokenPrevio = Boolean(token);
  if (token) headers.set('Authorization', `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, 'No fue posible conectar con el servidor. Revisa tu conexión e intenta de nuevo.');
  }

  if (response.ok) {
    if (response.status === 204) return undefined as T;
    return await response.json() as T;
  }

  const error = await leerError(response);
  const esRutaDeAcceso = /\/auth\/(login|registro)(\?|$)/.test(path);
  if (response.status === 401 && hayTokenPrevio && !esRutaDeAcceso) {
    eliminarToken();
    onUnauthorized?.();
  }

  const fallback = response.status === 401
    ? 'Tu sesión expiró. Inicia sesión nuevamente.'
    : 'Ocurrió un error al procesar la solicitud.';
  const retryAfter = Number(response.headers.get('Retry-After')) || undefined;
  throw new ApiError(response.status, error?.mensaje ?? mensajePorEstado(response.status, fallback), error, retryAfter);
}

export const api = {
  get: <T>(path: string, init?: RequestInit) => apiFetch<T>(path, { ...init, method: 'GET' }),
  post: <T>(path: string, body?: unknown, init?: RequestInit) => apiFetch<T>(path, { ...init, method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown, init?: RequestInit) => apiFetch<T>(path, { ...init, method: 'PATCH', body: JSON.stringify(body) }),
};

export { TOKEN_KEY };
