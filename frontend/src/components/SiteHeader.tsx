import { useState } from 'react';
import { useAuth } from '../context/useAuth';
import { Icon, type IconName } from './Icon';
import { ThemeToggle } from './ThemeToggle';
import { CampanaNotificaciones } from './CampanaNotificaciones';
import { InstalarApp } from './InstalarApp';

type Enlace = { href: string; texto: string; icon: IconName };

const ROL_TEXTO: Record<string, string> = { ciudadano: 'Ciudadano', moderador: 'Moderador', coordinador: 'Coordinador', enlace_municipal: 'Enlace municipal' };

function actual(href: string) {
  const path = window.location.pathname;
  if (href === '/') return path === '/' || path.startsWith('/reportes/') ? 'page' : undefined;
  return path === href || (href === '/dashboard' && path === '/tablero') ? 'page' : undefined;
}

function Marca() {
  return (
    <a className="brand" href="/" aria-label="Calles Seguras Juárez, inicio">
      <span className="brand__mark" aria-hidden="true">
        <svg width="36" height="36" viewBox="0 0 36 36" focusable="false">
          <defs>
            <linearGradient id="brand-noche" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#1c2f63" /><stop offset="1" stopColor="#070d1a" /></linearGradient>
            <linearGradient id="brand-ruta" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stopColor="#7d95ff" /><stop offset="1" stopColor="#22c4e6" /></linearGradient>
          </defs>
          <rect width="36" height="36" rx="10" fill="url(#brand-noche)" />
          <path d="M4 26c6-1 9-6 14-7s9 2 14-3" className="brand__route" stroke="url(#brand-ruta)" />
          <path d="M9 4c1 8 6 11 9 15s3 9 2 13" className="brand__street" />
          <circle cx="18" cy="19" r="4.2" className="brand__node" />
          <circle cx="18" cy="19" r="1.6" className="brand__node-core" />
        </svg>
      </span>
      <span className="brand__text">Calles Seguras <span>Juárez</span></span>
    </a>
  );
}

export function SiteHeader() {
  const { usuario, autenticado, cerrarSesion } = useAuth();
  const [abierto, setAbierto] = useState(false);
  const rol = usuario?.rol;

  const publicos: Enlace[] = [
    { href: '/', texto: 'Reportes públicos', icon: 'layers' },
    { href: '/mi-zona', texto: 'Mi zona', icon: 'locate' },
    { href: '/trayecto', texto: 'Mi trayecto', icon: 'route' },
    { href: '/resumen-colonia', texto: 'Por colonia', icon: 'chart' },
    ...(autenticado && rol !== 'enlace_municipal' ? [{ href: '/mis-reportes', texto: 'Mis reportes', icon: 'inbox' as IconName }, { href: '/perfil', texto: 'Mi perfil', icon: 'star' as IconName }] : []),
  ];
  const gestion: Enlace[] = [
    ...(rol === 'moderador' || rol === 'coordinador' ? [{ href: '/moderacion', texto: 'Moderación', icon: 'shield' as IconName }] : []),
    ...(rol === 'coordinador' ? [
      { href: '/coordinacion', texto: 'Coordinación', icon: 'wrench' as IconName },
      { href: '/cuadrillas', texto: 'Cuadrillas', icon: 'users' as IconName },
      { href: '/admin/catalogos', texto: 'Catálogos', icon: 'tag' as IconName },
      { href: '/puntos-recurrentes', texto: 'Puntos recurrentes', icon: 'repeat' as IconName },
      { href: '/admin/colonias', texto: 'Colonias', icon: 'pin' as IconName },
      { href: '/admin/usuarios', texto: 'Usuarios', icon: 'user' as IconName },
    ] : []),
    ...(rol === 'moderador' || rol === 'coordinador' ? [{ href: '/dashboard', texto: 'Dashboard', icon: 'chart' as IconName }] : []),
    ...(rol === 'coordinador' ? [{ href: '/auditoria', texto: 'Auditoría', icon: 'history' as IconName }] : []),
    ...(rol === 'enlace_municipal' ? [{ href: '/enlace', texto: 'Mis cuadrillas', icon: 'wrench' as IconName }] : []),
  ];

  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Marca />
        <InstalarApp />
        {autenticado && rol !== 'enlace_municipal' && <CampanaNotificaciones />}
        <ThemeToggle />
        <button className="menu-toggle" type="button" aria-expanded={abierto} aria-controls="menu-principal" onClick={() => setAbierto((v) => !v)}>
          <Icon name={abierto ? 'close' : 'menu'} size={22} /><span>{abierto ? 'Cerrar' : 'Menú'}</span>
        </button>
        <div id="menu-principal" className={`site-header__menu${abierto ? ' is-open' : ''}`}>
          <nav aria-label="Navegación principal">
            <ul className="nav-list">
              {publicos.map((e) => <li key={e.href}><a href={e.href} aria-current={actual(e.href)}><Icon name={e.icon} size={18} />{e.texto}</a></li>)}
            </ul>
          </nav>
          <div className="session-actions">
            {autenticado && rol !== 'enlace_municipal' && <a className="button button--primary" href="/reportar" aria-current={actual('/reportar')}><Icon name="plus" size={18} />Reportar daño</a>}
            {autenticado ? (
              <>
                <span className="session-user"><span className="session-user__avatar" aria-hidden="true">{usuario?.nombre?.trim().charAt(0).toUpperCase() || '·'}</span><span className="session-user__meta"><span className="session-user__name">{usuario?.nombre}</span><span className="session-user__role">{ROL_TEXTO[rol ?? ''] ?? rol}</span></span></span>
                <button className="button button--quiet button--sm" type="button" onClick={() => void cerrarSesion()}><Icon name="logout" size={18} />Cerrar sesión</button>
              </>
            ) : (
              <><a className="button button--quiet" href="/login">Iniciar sesión</a><a className="button button--primary" href="/registro">Registrarme</a></>
            )}
          </div>
        </div>
      </div>
      {gestion.length > 0 && (
        <nav className="staff-bar" aria-label="Herramientas de gestión">
          <ul className="staff-bar__list">
            <li className="staff-bar__label" aria-hidden="true">Gestión</li>
            {gestion.map((e) => <li key={e.href}><a href={e.href} aria-current={actual(e.href)}><Icon name={e.icon} size={16} />{e.texto}</a></li>)}
          </ul>
        </nav>
      )}
    </header>
  );
}
