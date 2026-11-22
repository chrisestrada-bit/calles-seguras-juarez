import type { ReactNode } from 'react';
import { useAuth } from '../context/useAuth';
import { Icon } from './Icon';

export function Guard({ roles, children }: { roles: string[]; children: ReactNode }) {
  const { autenticado, usuario } = useAuth();
  if (!autenticado) return <main className="admin-page"><section className="auth-card auth-card--center"><span className="auth-card__icon"><Icon name="shield" size={28} /></span><h1>Acceso restringido</h1><p>Inicia sesión para acceder a esta vista administrativa.</p><a className="button button--primary" href="/login">Iniciar sesión</a></section></main>;
  if (!usuario || !roles.includes(usuario.rol)) return <main className="admin-page"><div className="form-error" role="alert">Tu rol no tiene permiso para consultar esta vista.</div><a className="back-link" href="/"><Icon name="arrowLeft" size={16} />Volver a reportes</a></main>;
  return <>{children}</>;
}

export function ErrorMessage({ message }: { message: string }) { return <div className="form-error" role="alert">{message}</div>; }

export function Pagination({ page, total, onChange, label = 'Paginación' }: { page: number; total: number; onChange: (value: number) => void; label?: string }) {
  return (
    <nav className="pagination" aria-label={label}>
      <button type="button" disabled={page <= 1} onClick={() => onChange(page - 1)}><Icon name="chevronLeft" size={18} />Anterior</button>
      <span className="pagination__status">Página <strong className="tabular">{page}</strong> de <span className="tabular">{total || 1}</span></span>
      <button type="button" disabled={page >= total} onClick={() => onChange(page + 1)}>Siguiente<Icon name="chevronRight" size={18} /></button>
    </nav>
  );
}

export function PageIntro({ title, children, actions }: { title: string; children?: ReactNode; actions?: ReactNode }) {
  return (
    <header className="page-intro">
      <div><h1>{title}</h1>{children && <p>{children}</p>}</div>
      {actions && <div className="page-intro__actions">{actions}</div>}
    </header>
  );
}
