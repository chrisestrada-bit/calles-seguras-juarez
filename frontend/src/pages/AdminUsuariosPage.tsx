import { useEffect, useState, type FormEvent } from 'react';
import { api, ApiError } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ErrorMessage, Guard, Pagination } from '../components/AdminShared';
import type { CambiarEstadoResponse, CambiarRolResponse, RespuestaPaginada, Rol, UsuarioAdmin } from '../types/api';

const POR_PAGINA = 20;
const ROLES: Array<Exclude<Rol, 'visitante'>> = ['ciudadano', 'moderador', 'coordinador'];
const consulta = (valores: Record<string, string | number>) => Object.entries(valores).filter(([, v]) => v !== '').map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join('&');
const fecha = (valor: string) => new Date(valor).toLocaleString('es-MX', { dateStyle: 'medium', timeZone: 'America/Ciudad_Juarez' });

export function AdminUsuariosPage() {
  const { usuario } = useAuth();
  const [filas, setFilas] = useState<UsuarioAdmin[]>([]);
  const [busqueda, setBusqueda] = useState('');
  const [q, setQ] = useState('');
  const [rol, setRol] = useState('');
  const [activo, setActivo] = useState('');
  const [pagina, setPagina] = useState(1);
  const [total, setTotal] = useState(1);
  const [estado, setEstado] = useState<'cargando' | 'listo' | 'error'>('cargando');
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [errorAccion, setErrorAccion] = useState('');
  const [ocupado, setOcupado] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    setEstado('cargando');
    api.get<RespuestaPaginada<UsuarioAdmin>>(`/api/v1/admin/usuarios?${consulta({ q, rol, activo, pagina, por_pagina: POR_PAGINA })}`)
      .then((r) => {
        if (!vigente) return;
        setFilas(r.datos);
        setTotal(r.paginacion.total_paginas || 1);
        setEstado('listo');
      })
      .catch((e) => {
        if (!vigente) return;
        setError(e instanceof ApiError ? e.message : 'No fue posible cargar los usuarios.');
        setEstado('error');
      });
    return () => { vigente = false; };
  }, [q, rol, activo, pagina]);

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
        <header className="admin-intro">
          <p className="eyebrow">Seguridad · coordinación</p>
          <h1>Usuarios y roles</h1>
          <p>Consulta cuentas, cambia roles y suspende o reactiva usuarios. Esta vista es privada.</p>
        </header>
        <section className="filters-section" aria-labelledby="usuarios-filtros">
          <h2 id="usuarios-filtros">Buscar usuarios</h2>
          <form className="filters" onSubmit={buscar}>
            <label htmlFor="usuarios-q">Nombre o correo (mínimo 2 caracteres)</label>
            <input id="usuarios-q" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
            <label htmlFor="usuarios-rol">Rol</label>
            <select id="usuarios-rol" value={rol} onChange={(e) => { setRol(e.target.value); setPagina(1); }}>
              <option value="">Todos</option>
              {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
            <label htmlFor="usuarios-estado">Estado</label>
            <select id="usuarios-estado" value={activo} onChange={(e) => { setActivo(e.target.value); setPagina(1); }}>
              <option value="">Todos</option>
              <option value="true">Activos</option>
              <option value="false">Suspendidos</option>
            </select>
            <button className="button" type="submit">Buscar</button>
          </form>
        </section>
        {mensaje && <div className="form-success" role="status">{mensaje}</div>}
        {errorAccion && <ErrorMessage message={errorAccion} />}
        {estado === 'cargando' && <p className="state-message" role="status">Cargando usuarios…</p>}
        {estado === 'error' && <ErrorMessage message={error} />}
        {estado === 'listo' && filas.length === 0 && <p className="state-message">No hay usuarios que coincidan con los filtros.</p>}
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
                        <td>{u.activo ? '✔ Activo' : '⛔ Suspendido'}</td>
                        <td>{fecha(u.created_at)}</td>
                        <td><button className="button" type="button" disabled={ocupado === u.id || esYo} onClick={() => void alternarEstado(u)}>{u.activo ? 'Suspender' : 'Reactivar'}<span className="visually-hidden"> a {u.nombre}</span></button></td>
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
