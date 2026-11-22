import { createContext } from 'react';
import type { LoginResponse, Rol, UsuarioResumen } from '../types/api';

export interface AuthContextValue {
  usuario: UsuarioResumen | null;
  token: string | null;
  rolActivo: Rol;
  autenticado: boolean;
  iniciarSesion: (respuesta: LoginResponse) => void;
  renovarSesion: () => Promise<void>;
  cerrarSesion: () => Promise<void>;
  cambiarRolActivo: (rol: Rol) => void;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
