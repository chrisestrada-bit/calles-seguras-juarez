import type { ReactNode } from 'react';
import { useAuth } from '../context/AuthContext';

export function Guard({ roles, children }: { roles: string[]; children: ReactNode }) {
  const { autenticado, usuario } = useAuth();
  if (!autenticado) return <main className="admin-page"><section className="auth-card"><h1>Acceso restringido</h1><p>Inicia sesión para acceder a esta vista administrativa.</p><a className="button" href="/login">Iniciar sesión</a></section></main>;
  if (!usuario || !roles.includes(usuario.rol)) return <main className="admin-page"><div className="form-error" role="alert">Tu rol no tiene permiso para consultar esta vista.</div><a href="/">Volver a reportes</a></main>;
  return <>{children}</>;
}
export function ErrorMessage({ message }: { message: string }) { return <div className="form-error" role="alert">{message}</div>; }
export function Pagination({ page, total, onChange }: { page: number; total: number; onChange: (value: number) => void }) { return <nav className="pagination" aria-label="Paginación"><button type="button" disabled={page <= 1} onClick={() => onChange(page - 1)}>Anterior</button><span>Página {page} de {total || 1}</span><button type="button" disabled={page >= total} onClick={() => onChange(page + 1)}>Siguiente</button></nav>; }
