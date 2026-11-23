import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { LoginResponse, Rol, UsuarioResumen } from '../types/api';
import { AuthContext } from './authContexto';
import { api, configurarSesionExpirada, eliminarToken, guardarToken, obtenerToken } from '../services/api';
import { limpiarCachesSensibles } from '../services/offline';

const USUARIO_KEY = 'calles-seguras.usuario';
const INACTIVIDAD_MS = 30 * 60 * 1000;
/**
 * El JWT vence 30 min después de emitirse. Para que la expiración sea por INACTIVIDAD (no absoluta), con
 * actividad del usuario se renueva cuando ya pasaron 10 min desde la última emisión (auditoría final, M4).
 */
const RENOVAR_TRAS_MS = 10 * 60 * 1000;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState(obtenerToken);
  const [usuario, setUsuario] = useState<UsuarioResumen | null>(() => {
    const guardado = localStorage.getItem(USUARIO_KEY);
    return guardado ? JSON.parse(guardado) as UsuarioResumen : null;
  });
  // 0 = token de origen desconocido (p. ej. recuperado de localStorage al recargar): se renueva con la primera actividad.
  const ultimaRenovacion = useRef(0);
  const renovando = useRef(false);
  const [rolActivo, setRolActivo] = useState<Rol>(() => usuario?.rol ?? 'visitante');

  const cerrarSesionLocal = useCallback(() => {
    eliminarToken();
    limpiarCachesSensibles(); // HU-08.4: nada de lo consultado queda en caché al cerrar sesión
    localStorage.removeItem(USUARIO_KEY);
    setToken(null);
    setUsuario(null);
    setRolActivo('visitante');
    window.location.assign('/login');
  }, []);

  const iniciarSesion = useCallback((respuesta: LoginResponse) => {
    ultimaRenovacion.current = Date.now();
    guardarToken(respuesta.access_token);
    localStorage.setItem(USUARIO_KEY, JSON.stringify(respuesta.usuario));
    setToken(respuesta.access_token);
    setUsuario(respuesta.usuario);
    setRolActivo(respuesta.usuario.rol);
  }, []);

  const renovarSesion = useCallback(async () => {
    const respuesta = await api.post<LoginResponse>('/api/v1/auth/renovar');
    iniciarSesion(respuesta);
  }, [iniciarSesion]);

  const cerrarSesion = useCallback(async () => {
    try {
      if (obtenerToken()) await api.post<void>('/api/v1/auth/cerrar-sesion');
    } finally {
      cerrarSesionLocal();
    }
  }, [cerrarSesionLocal]);

  const cambiarRolActivo = useCallback((rol: Rol) => {
    if (rol === 'visitante' || usuario?.rol === rol) setRolActivo(rol);
  }, [usuario?.rol]);

  useEffect(() => {
    configurarSesionExpirada(cerrarSesionLocal);
    return () => configurarSesionExpirada(() => undefined);
  }, [cerrarSesionLocal]);

  useEffect(() => {
    if (!token) return;
    let temporizador: number;
    const reiniciarInactividad = () => {
      window.clearTimeout(temporizador);
      temporizador = window.setTimeout(cerrarSesionLocal, INACTIVIDAD_MS);
      if (!renovando.current && Date.now() - ultimaRenovacion.current >= RENOVAR_TRAS_MS) {
        renovando.current = true;
        renovarSesion()
          .then(() => { ultimaRenovacion.current = Date.now(); })
          .catch(() => undefined) // un 401 ya cierra la sesión desde services/api; un fallo de red se reintenta luego
          .finally(() => { renovando.current = false; });
      }
    };
    const eventos: Array<keyof WindowEventMap> = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'];
    eventos.forEach((evento) => window.addEventListener(evento, reiniciarInactividad));
    reiniciarInactividad();
    return () => {
      window.clearTimeout(temporizador);
      eventos.forEach((evento) => window.removeEventListener(evento, reiniciarInactividad));
    };
  }, [token, cerrarSesionLocal, renovarSesion]);

  const value = useMemo(() => ({ usuario, token, rolActivo, autenticado: Boolean(token && usuario), iniciarSesion, renovarSesion, cerrarSesion, cambiarRolActivo }), [usuario, token, rolActivo, iniciarSesion, renovarSesion, cerrarSesion, cambiarRolActivo]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
