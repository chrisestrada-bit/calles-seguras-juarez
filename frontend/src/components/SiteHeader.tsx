import { useAuth } from '../context/AuthContext';

export function SiteHeader() {
  const { usuario, autenticado, cerrarSesion } = useAuth();
  const rol = usuario?.rol;
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <a className="brand" href="/" aria-label="Calles Seguras Juárez, inicio"><span aria-hidden="true">🛣️</span> Calles Seguras Juárez</a>
        <nav aria-label="Navegación principal">
          <ul className="nav-list">
            <li><a href="/">Reportes públicos</a></li>
            <li><a href="/mi-zona">Mi zona</a></li>
            {autenticado && <li><a href="/reportar">Reportar daño</a></li>}
            {autenticado && <li><a href="/mis-reportes">Mis reportes</a></li>}
            {(rol === 'moderador' || rol === 'coordinador') && <li><a href="/moderacion">Moderación</a></li>}
            {rol === 'coordinador' && <><li><a href="/coordinacion">Coordinación</a></li><li><a href="/admin/colonias">Colonias</a></li><li><a href="/admin/usuarios">Usuarios</a></li><li><a href="/dashboard">Dashboard</a></li><li><a href="/auditoria">Auditoría</a></li></>}
            {rol === 'moderador' && <li><a href="/dashboard">Dashboard</a></li>}
          </ul>
        </nav>
        <div className="session-actions">
          {autenticado ? <><span className="session-user">{usuario?.nombre} ({rol})</span><button className="button button--quiet" type="button" onClick={() => void cerrarSesion()}>Cerrar sesión</button></> : <><a className="button button--quiet" href="/login">Iniciar sesión</a><a className="button" href="/registro">Registrarme</a></>}
        </div>
      </div>
    </header>
  );
}
