import type { ReactNode } from 'react';
import { Icon, type IconName } from './Icon';
import type { Severidad, TipoDano } from '../types/api';
import type { Tono } from '../utils/formato';

/* ——— Tipo de daño ——— */
const TIPO: Record<TipoDano, { icon: IconName; tone: Tono; corto: string }> = {
  Bache: { icon: 'pothole', tone: 'road', corto: 'Bache' },
  'Alcantarilla sin tapa': { icon: 'manhole', tone: 'manhole', corto: 'Alcantarilla sin tapa' },
  Encharcamiento: { icon: 'water', tone: 'water', corto: 'Encharcamiento' },
};

/** Glifos duotono propios para cada tipo de daño (retícula 24, tinta + relleno tenue). */
export function TypeGlyph({ tipo, size = 24 }: { tipo: TipoDano; size?: number }) {
  const t = (TIPO[tipo] ?? TIPO.Bache).tone;
  return (
    <svg className={`glyph glyph--${t}`} width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      {t === 'road' && <>
        <path className="glyph__fill" d="M2.5 19 6.2 8h11.6l3.7 11Z" />
        <path className="glyph__line" d="M2.5 19 6.2 8h11.6l3.7 11Z" />
        <path className="glyph__ink" d="M7.6 15.4c.5-1.7 2.3-2.7 4.4-2.7s3.9 1 4.4 2.7c-.4 1.4-2.2 2.2-4.4 2.2s-4-.8-4.4-2.2Z" />
        <path className="glyph__line" d="m16.8 13.5 2-1.4M7.2 13.6l-1.8-1M12.3 12.7l.5-1.9" />
        <path className="glyph__lane" d="M12 8.6v1.4" />
      </>}
      {t === 'manhole' && <>
        <ellipse className="glyph__fill" cx="11" cy="16.5" rx="8.8" ry="4" />
        <ellipse className="glyph__line" cx="11" cy="16.5" rx="8.8" ry="4" />
        <ellipse className="glyph__ink" cx="11" cy="16.6" rx="5.6" ry="2.3" />
        <g transform="rotate(-18 16.5 6.6)">
          <ellipse className="glyph__fill glyph__fill--solid" cx="16.5" cy="6.6" rx="5" ry="2.2" />
          <ellipse className="glyph__line" cx="16.5" cy="6.6" rx="5" ry="2.2" />
          <path className="glyph__line glyph__line--thin" d="M13.2 6.6h6.6M14 5.4h5M14 7.8h5" />
        </g>
      </>}
      {t === 'water' && <>
        <path className="glyph__fill" d="M3 16.5c0-1.9 3.2-3.1 6.4-2.8 1.7.2 2.6-.6 4.6-.6 3.6 0 7 1.4 7 3.5 0 2.2-4.2 3.4-9 3.4s-9-1.4-9-3.5Z" />
        <path className="glyph__line" d="M3 16.5c0-1.9 3.2-3.1 6.4-2.8 1.7.2 2.6-.6 4.6-.6 3.6 0 7 1.4 7 3.5 0 2.2-4.2 3.4-9 3.4s-9-1.4-9-3.5Z" />
        <path className="glyph__line glyph__line--thin" d="M7.5 16.8c1.4.6 2.8.6 4.2 0s2.8-.6 4.2 0" />
        <path className="glyph__ink" d="M12 2.8s-3.2 3.6-3.2 5.8a3.2 3.2 0 0 0 6.4 0c0-2.2-3.2-5.8-3.2-5.8Z" />
      </>}
    </svg>
  );
}

export function TypeBadge({ tipo }: { tipo: TipoDano }) {
  const t = TIPO[tipo] ?? TIPO.Bache;
  return <span className={`type-badge type-badge--${t.tone}`}><span className="type-badge__tile"><TypeGlyph tipo={tipo} size={22} /></span>{t.corto}</span>;
}


/* ——— Estado del reporte ——— */
const ESTADO: Record<string, { icon: IconName; tone: string }> = {
  Recibido: { icon: 'inbox', tone: 'pending' },
  'Sin validar': { icon: 'inbox', tone: 'pending' },
  Validado: { icon: 'checkCircle', tone: 'info' },
  Programado: { icon: 'calendar', tone: 'info' },
  'En reparación': { icon: 'wrench', tone: 'progress' },
  Reparado: { icon: 'check', tone: 'success' },
  Rechazado: { icon: 'xCircle', tone: 'danger' },
  Activo: { icon: 'water', tone: 'water' },
  Histórico: { icon: 'history', tone: 'neutral' },
};

export function StatusBadge({ estado, etiqueta, size = 'md' }: { estado: string; etiqueta?: string | null; size?: 'md' | 'lg' }) {
  const texto = etiqueta ?? estado;
  const e = ESTADO[texto] ?? ESTADO[estado] ?? { icon: 'info' as IconName, tone: 'neutral' };
  return <span className={`status-badge status-badge--${e.tone}${size === 'lg' ? ' status-badge--lg' : ''}`}><Icon name={e.icon} size={size === 'lg' ? 18 : 15} />{texto}</span>;
}

/* ——— Severidad (texto + medidor de barras, nunca sólo color) ——— */
const NIVEL: Record<string, number> = { Baja: 1, Media: 2, Alta: 3 };

export function SeverityBadge({ severidad, intransitable = false }: { severidad: Severidad | string; intransitable?: boolean }) {
  if (intransitable) return <span className="severity severity--critical"><Icon name="ban" size={16} />Intransitable</span>;
  const nivel = NIVEL[severidad] ?? 1;
  return (
    <span className={`severity severity--${nivel}`}>
      <svg className="severity__meter" width="16" height="14" viewBox="0 0 16 14" aria-hidden="true" focusable="false">
        {[0, 1, 2].map((i) => <rect key={i} x={i * 6} y={9 - i * 4} width="4" height={5 + i * 4} rx="1" className={i < nivel ? 'on' : 'off'} />)}
      </svg>
      Severidad {String(severidad).toLowerCase()}
    </span>
  );
}

/* ——— Aviso en línea ——— */
const AVISO: Record<'info' | 'success' | 'warning' | 'error', IconName> = { info: 'info', success: 'checkCircle', warning: 'alert', error: 'alert' };
export function Notice({ tone = 'info', children, live = 'status' }: { tone?: keyof typeof AVISO; children: ReactNode; live?: 'status' | 'alert' }) {
  return <div className={`notice notice--${tone}`} role={live}><Icon name={AVISO[tone]} size={20} /><div>{children}</div></div>;
}

/* ——— Estado vacío ilustrado ——— */
type Ilustracion = 'road' | 'search' | 'inbox' | 'map';
function Illustration({ kind }: { kind: Ilustracion }) {
  return (
    <svg className={`empty-state__art art--${kind}`} width="200" height="140" viewBox="0 0 200 140" aria-hidden="true" focusable="false">
      <defs>
        <radialGradient id={`art-halo-${kind}`} cx="50%" cy="55%" r="55%"><stop offset="0" stopColor="#dfe6ff" className="art-halo-stop" /><stop offset="1" stopColor="#dfe6ff" stopOpacity="0" className="art-halo-stop" /></radialGradient>
      </defs>
      <ellipse cx="100" cy="74" rx="96" ry="64" fill={`url(#art-halo-${kind})`} />
      <ellipse cx="100" cy="126" rx="64" ry="6" className="art-ground" />
      {kind === 'road' && <>
        <path d="M70 124 92 30h16l22 94Z" className="art-surface" />
        <path d="M100 38v10M100 58v14M100 84v18M100 112v10" className="art-lane" />
        <g><circle cx="146" cy="46" r="18" className="art-badge" /><path d="m138 46 6 6 10-11" className="art-badge-mark" /></g>
        <circle cx="56" cy="62" r="4" className="art-dot art-dot--road" /><circle cx="150" cy="96" r="3.5" className="art-dot art-dot--water" />
      </>}
      {kind === 'search' && <>
        <rect x="40" y="26" width="104" height="80" rx="14" className="art-surface" />
        <path d="M40 58h104M40 84h104M76 26v80M112 26v80" className="art-grid" />
        <path d="M48 98c22-6 30-34 56-40s30-20 34-26" className="art-route" />
        <g><circle cx="138" cy="84" r="20" className="art-lens" /><circle cx="138" cy="84" r="12" className="art-lens-ring" /><path d="m152 98 14 14" className="art-lens-handle" /></g>
      </>}
      {kind === 'inbox' && <>
        <rect x="62" y="22" width="76" height="40" rx="9" className="art-card art-card--back" />
        <rect x="54" y="34" width="92" height="40" rx="9" className="art-card" />
        <path d="M66 48h40M66 58h26" className="art-lane art-lane--soft" />
        <path d="M40 76 52 52h96l12 24v30a10 10 0 0 1-10 10H50a10 10 0 0 1-10-10Z" className="art-surface" />
        <path d="M40 76h30a30 18 0 0 0 60 0h30" className="art-grid art-grid--strong" />
        <g><circle cx="156" cy="30" r="14" className="art-badge" /><path d="m150 30 4.5 4.5 8-8.5" className="art-badge-mark" /></g>
      </>}
      {kind === 'map' && <>
        <circle cx="100" cy="74" r="50" className="art-ring" /><circle cx="100" cy="74" r="32" className="art-ring" /><circle cx="100" cy="74" r="14" className="art-ring" />
        <path d="M100 74 136 38A50 50 0 0 1 150 74Z" className="art-sweep" />
        <g><path d="M100 82s-14-11.5-14-23a14 14 0 0 1 28 0c0 11.5-14 23-14 23Z" className="art-pin" /><circle cx="100" cy="59" r="5" className="art-pin-core" /></g>
        <g><circle cx="146" cy="104" r="14" className="art-badge" /><path d="m140 104 4.5 4.5 8-8.5" className="art-badge-mark" /></g>
      </>}
    </svg>
  );
}

export function EmptyState({ title, children, action, art = 'road' }: { title: string; children?: ReactNode; action?: ReactNode; art?: Ilustracion }) {
  return (
    <div className="empty-state">
      <Illustration kind={art} />
      <h3 className="empty-state__title">{title}</h3>
      {children && <p className="empty-state__text">{children}</p>}
      {action && <div className="empty-state__action">{action}</div>}
    </div>
  );
}

/* ——— Esqueletos de carga ——— */
export function ReportGridSkeleton({ count = 6, label = 'Cargando reportes…' }: { count?: number; label?: string }) {
  return (
    <div className="report-grid" role="status" aria-live="polite">
      <span className="visually-hidden">{label}</span>
      {Array.from({ length: count }, (_, i) => (
        <div className="report-card report-card--skeleton" key={i} aria-hidden="true">
          <div className="skeleton-row"><span className="skeleton-row__lead"><span className="skeleton skeleton--tile" /><span className="skeleton skeleton--pill" /></span><span className="skeleton skeleton--pill skeleton--short" /></div>
          <span className="skeleton skeleton--title" /><span className="skeleton skeleton--text" />
          <div className="skeleton-row skeleton-row--foot"><span className="skeleton skeleton--text skeleton--short" /><span className="skeleton skeleton--text skeleton--short" /></div>
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5, label = 'Cargando…' }: { rows?: number; label?: string }) {
  return (
    <div className="table-skeleton" role="status" aria-live="polite">
      <span className="visually-hidden">{label}</span>
      <span className="skeleton skeleton--bar" aria-hidden="true" />
      {Array.from({ length: rows }, (_, i) => (
        <div className="table-skeleton__row" key={i} aria-hidden="true">
          <span className="skeleton skeleton--text" /><span className="skeleton skeleton--text" /><span className="skeleton skeleton--text skeleton--short" /><span className="skeleton skeleton--pill" />
        </div>
      ))}
    </div>
  );
}

export function BlockSkeleton({ label = 'Cargando…', lines = 3 }: { label?: string; lines?: number }) {
  return (
    <div className="block-skeleton" role="status" aria-live="polite">
      <span className="visually-hidden">{label}</span>
      <div className="skeleton-row" aria-hidden="true"><span className="skeleton skeleton--pill" /><span className="skeleton skeleton--pill skeleton--short" /></div>
      <span className="skeleton skeleton--heading" aria-hidden="true" />
      {Array.from({ length: lines }, (_, i) => <span className="skeleton skeleton--text" key={i} aria-hidden="true" />)}
    </div>
  );
}

/* ——— Sello ilustrado para tarjetas de cuenta (decorativo) ——— */
export function AuthArt() {
  return (
    <svg className="auth-art" width="64" height="64" viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      <rect width="64" height="64" rx="18" className="auth-art__tile" />
      <path d="M8 46c10-2 16-12 26-13s16 4 24-5" className="auth-art__route" />
      <path d="M18 6c2 14 10 20 15 27s5 16 3 25" className="auth-art__street" />
      <circle cx="34" cy="33" r="12" className="auth-art__ring" />
      <circle cx="34" cy="33" r="5" className="auth-art__node" />
    </svg>
  );
}
