import { useState, type FormEvent } from 'react';
import { api, ApiError } from '../services/api';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { fechaDeInstante } from '../utils/formato';
import { useAuth } from '../context/useAuth';
import { ErrorMessage, Guard, PageIntro, Pagination } from '../components/AdminShared';
import { Icon } from '../components/Icon';
import { EmptyState, TableSkeleton } from '../components/ui';
import type { CambiarEstadoResponse, CambiarRolResponse, RespuestaPaginada, Rol, UsuarioAdmin } from '../types/api';

const POR_PAGINA = 20;
const ROLES: Array<Exclude<Rol, 'visitante'>> = ['ciudadano', 'moderador', 'coordinador', 'enlace_municipal'];
const consulta = (valores: Record<string, string | number>) => Object.entries(valores).filter(([, v]) => v !== '').map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join('&');
const fecha = fechaDeInstante; // RN-02

export function AdminUsuariosPage() {
  const { usuario } = useAuth();
  const [busqueda, setBusqueda] = useState('');
  const [q, setQ] = useState('');
  const [rol, setRol] = useState('');
  const [activo, setActivo] = useState('');
  const [pagina, setPagina] = useState(1);
  const [mensaje, setMensaje] = useState('');
  const [errorAccion, setErrorAccion] = useState('');
  const [ocupado, setOcupado] = useState<string | null>(null);

  const consultaUsuarios = useCargaDatos<RespuestaPaginada<UsuarioAdmin>>(
    `/api/v1/admin/usuarios?${consulta({ q, rol, activo, pagina, por_pagina: POR_PAGINA })}`,
    obtenerJson,
    'No fue posible cargar los usuarios.',
  );
  const { estado, error, actualizar } = consultaUsuarios;
  const filas = consultaUsuarios.datos?.datos ?? [];
  const total = consultaUsuarios.datos?.paginacion.total_paginas || 1;
  const setFilas = (cambio: (actual: UsuarioAdmin[]) => UsuarioAdmin[]) => actualizar((d) => ({ ...d, datos: cambio(d.datos) }));

  const buscar = (evento: FormEvent) => {
    evento.preventDefault();
    setPagina(1);
    setQ(busqueda.trim().length >= 2 ? busqueda.trim() : '');
  };
  const cambiarRol = async (u: UsuarioAdmin, nuevo: string) => {
    if (nuevo === u.rol) return;
    setOcupado(u.id);
    setErrorAccion('');
    setMensaje('');
    try {
      const r = await api.patch<CambiarRolResponse>(`/api/v1/admin/usuarios/${u.id}/rol`, { rol: nuevo });
      setFilas((actual) => actual.map((x) => (x.id === u.id ? { ...x, rol: r.rol } : x)));
      setMensaje(`${u.nombre}: ${r.mensaje}`);
    } catch (e) {
      setErrorAccion(e instanceof ApiError ? e.message : 'No fue posible cambiar el rol.');
    } finally {
      setOcupado(null);
    }
  };
  const alternarEstado = async (u: UsuarioAdmin) => {
    setOcupado(u.id);
    setErrorAccion('');
    setMensaje('');
    try {
      const r = await api.patch<CambiarEstadoResponse>(`/api/v1/admin/usuarios/${u.id}/estado`, { activo: !u.activo });
      setFilas((actual) => actual.map((x) => (x.id === u.id ? { ...x, activo: r.activo } : x)));
      setMensaje(`${u.nombre}: ${r.mensaje}`);
    } catch (e) {
      setErrorAccion(e instanceof ApiError ? e.message : 'No fue posible cambiar el estado de la cuenta.');
    } finally {
      setOcupado(null);
    }
  };

  return (
    <Guard roles={['coordinador']}>
      <main className="admin-page">
        <PageIntro title="Usuarios y roles">Consulta cuentas, cambia roles y suspende o reactiva usuarios. Esta vista es privada.</PageIntro>
        <section className="filter-bar" aria-labelledby="usuarios-filtros">
          <h2 id="usuarios-filtros" className="visually-hidden">Buscar usuarios</h2>
          <form className="filters" onSubmit={buscar}>
            <div className="field field--search">
              <label htmlFor="usuarios-q">Nombre o correo (mínimo 2 caracteres)</label>
              <div className="input-icon"><Icon name="search" size={18} /><input id="usuarios-q" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} /></div>
            </div>
            <div className="field">
              <label htmlFor="usuarios-rol">Rol</label>
              <select id="usuarios-rol" value={rol} onChange={(e) => { setRol(e.target.value); setPagina(1); }}>
                <option value="">Todos</option>
                {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <div className="field">
              <label htmlFor="usuarios-estado">Estado</label>
              <select id="usuarios-estado" value={activo} onChange={(e) => { setActivo(e.target.value); setPagina(1); }}>
                <option value="">Todos</option>
                <option value="true">Activos</option>
                <option value="false">Suspendidos</option>
              </select>
            </div>
            <button className="button button--primary" type="submit"><Icon name="search" size={18} />Buscar</button>
          </form>
        </section>
        {mensaje && <div className="form-success" role="status">{mensaje}</div>}
        {errorAccion && <ErrorMessage message={errorAccion} />}
        {estado === 'cargando' && <TableSkeleton label="Cargando usuarios…" />}
        {estado === 'error' && <ErrorMessage message={error} />}
        {estado === 'listo' && filas.length === 0 && <EmptyState art="search" title="Sin coincidencias">No hay usuarios que coincidan con los filtros.</EmptyState>}
        {estado === 'listo' && filas.length > 0 && (
          <>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <caption className="visually-hidden">Usuarios registrados</caption>
                <thead><tr><th scope="col">Usuario</th><th scope="col">Rol</th><th scope="col">Estado</th><th scope="col">Alta</th><th scope="col">Acciones</th></tr></thead>
                <tbody>
                  {filas.map((u) => {
                    const esYo = u.id === usuario?.id;
                    return (
                      <tr key={u.id}>
                        <th scope="row">{u.nombre}<br /><small>{u.correo}{esYo ? ' (tú)' : ''}</small></th>
                        <td>
                          <label className="visually-hidden" htmlFor={`rol-${u.id}`}>Rol de {u.nombre}</label>
                          <select id={`rol-${u.id}`} value={u.rol} disabled={ocupado === u.id || esYo} onChange={(e) => void cambiarRol(u, e.target.value)}>
                            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                          </select>
                        </td>
                        <td>{u.activo ? <span className="status-badge status-badge--success"><Icon name="checkCircle" size={15} />Activo</span> : <span className="status-badge status-badge--danger"><Icon name="ban" size={15} />Suspendido</span>}</td>
                        <td className="tabular">{fecha(u.created_at)}</td>
                        <td><button className={`button button--sm ${u.activo ? 'button--quiet' : 'button--primary'}`} type="button" disabled={ocupado === u.id || esYo} onClick={() => void alternarEstado(u)}>{u.activo ? 'Suspender' : 'Reactivar'}<span className="visually-hidden"> a {u.nombre}</span></button></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <Pagination page={pagina} total={total} onChange={setPagina} />
          </>
        )}
      </main>
    </Guard>
  );
}
