import { useState, type FormEvent } from 'react';
import { api, ApiError } from '../services/api';
import { AuthArt } from '../components/ui';
import { useAuth } from '../context/useAuth';
import type { LoginResponse } from '../types/api';

export function LoginPage() {
  const { iniciarSesion } = useAuth();
  const [correo, setCorreo] = useState(''); const [contrasena, setContrasena] = useState(''); const [error, setError] = useState(''); const [cargando, setCargando] = useState(false);
  const enviar = async (evento: FormEvent) => { evento.preventDefault(); setError(''); setCargando(true); try { const respuesta = await api.post<LoginResponse>('/api/v1/auth/login', { correo, contrasena }); iniciarSesion(respuesta); window.location.assign('/'); } catch (e) { setError(e instanceof ApiError && e.status === 429 ? e.message : 'Correo o contraseña incorrectos.'); } finally { setCargando(false); } };
  return <main className="auth-page"><section className="auth-card" aria-labelledby="login-titulo"><AuthArt /><h1 id="login-titulo">Iniciar sesión</h1><p>Consulta tus reportes y participa en tu comunidad.</p>{error && <div className="form-error" role="alert">{error}</div>}<form onSubmit={enviar} noValidate><label htmlFor="correo">Correo electrónico</label><input id="correo" type="email" autoComplete="email" value={correo} onChange={(e) => setCorreo(e.target.value)} required /><label htmlFor="contrasena">Contraseña</label><input id="contrasena" type="password" autoComplete="current-password" value={contrasena} onChange={(e) => setContrasena(e.target.value)} required /><button className="button button--primary button--full button--lg" disabled={cargando}>{cargando ? 'Iniciando sesión…' : 'Iniciar sesión'}</button></form><p className="auth-footer">¿No tienes cuenta? <a href="/registro">Regístrate</a></p></section></main>;
}
