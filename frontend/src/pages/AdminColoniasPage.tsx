import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { api, ApiError } from '../services/api';
import { ErrorMessage, Guard, Pagination } from '../components/AdminShared';
import type { Colonia, ColoniaRequest, ColoniaUpdate, RespuestaPaginada, SectorAdmin } from '../types/api';

const POR_PAGINA = 20;
type ColoniaFila = Colonia & { activo: boolean };
type Formulario = { sector_id: string; nombre: string; codigo_postal: string; latitud_centro: string; longitud_centro: string };
const vacio: Formulario = { sector_id: '', nombre: '', codigo_postal: '', latitud_centro: '', longitud_centro: '' };
const consulta = (valores: Record<string, string | number>) => Object.entries(valores).filter(([, v]) => v !== '').map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join('&');

function ColoniaForm({ sectores, editando, onCancel, onSaved }: { sectores: SectorAdmin[]; editando: ColoniaFila | null; onCancel: () => void; onSaved: (colonia: ColoniaFila, esNueva: boolean) => void }) {
  const [valores, setValores] = useState<Formulario>(editando ? { sector_id: String(editando.sector.id), nombre: editando.nombre, codigo_postal: editando.codigo_postal ?? '', latitud_centro: String(editando.centro.latitud), longitud_centro: String(editando.centro.longitud) } : vacio);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState('');
  const cambiar = (campo: keyof Formulario, valor: string) => setValores((actual) => ({ ...actual, [campo]: valor }));

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault();
    setError('');
    const lat = Number(valores.latitud_centro);
    const lng = Number(valores.longitud_centro);
    if (!Number.isFinite(lat) || !Number.isFinite(lng) || lat < 31.45 || lat > 31.8 || lng < -106.65 || lng > -106.25) {
      setError('El centro de la colonia debe estar dentro de Ciudad Juárez (latitud 31.45 a 31.80, longitud -106.65 a -106.25).');
      return;
    }
    if (valores.codigo_postal && !/^32\d{3}$/.test(valores.codigo_postal)) {
      setError('El código postal debe tener 5 dígitos y comenzar con 32.');
      return;
    }
    const cuerpo: ColoniaRequest | ColoniaUpdate = { sector_id: Number(valores.sector_id), nombre: valores.nombre.trim(), latitud_centro: lat, longitud_centro: lng, ...(valores.codigo_postal ? { codigo_postal: valores.codigo_postal } : {}) };
    setOcupado(true);
    try {
      const guardada = editando
        ? await api.patch<ColoniaFila>(`/api/v1/admin/colonias/${editando.id}`, cuerpo)
        : await api.post<ColoniaFila>('/api/v1/admin/colonias', cuerpo);
      onSaved(guardada, !editando);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'No fue posible guardar la colonia.');
    } finally {
      setOcupado(false);
    }
  };

  return (
    <form className="detail-card admin-form" onSubmit={enviar} aria-labelledby="colonia-form-titulo">
      <h2 id="colonia-form-titulo">{editando ? `Editar colonia: ${editando.nombre}` : 'Nueva colonia'}</h2>
      {error && <ErrorMessage message={error} />}
      <label htmlFor="col-nombre">Nombre</label>
      <input id="col-nombre" required minLength={2} maxLength={120} value={valores.nombre} onChange={(e) => cambiar('nombre', e.target.value)} />
      <label htmlFor="col-sector">Sector</label>
      <select id="col-sector" required value={valores.sector_id} onChange={(e) => cambiar('sector_id', e.target.value)}>
        <option value="">Selecciona un sector</option>
        {sectores.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
      </select>
      <label htmlFor="col-cp">Código postal (opcional)</label>
      <input id="col-cp" inputMode="numeric" pattern="32[0-9]{3}" maxLength={5} value={valores.codigo_postal} onChange={(e) => cambiar('codigo_postal', e.target.value)} />
      <label htmlFor="col-lat">Latitud del centro</label>
      <input id="col-lat" required inputMode="decimal" value={valores.latitud_centro} onChange={(e) => cambiar('latitud_centro', e.target.value)} />
      <label htmlFor="col-lng">Longitud del centro</label>
      <input id="col-lng" required inputMode="decimal" value={valores.longitud_centro} onChange={(e) => cambiar('longitud_centro', e.target.value)} />
      <div className="confirmation-actions">
        <button className="button" type="submit" disabled={ocupado}>{ocupado ? 'Guardando…' : 'Guardar'}</button>
        <button className="button button--secondary" type="button" onClick={onCancel} disabled={ocupado}>Cancelar</button>
      </div>
    </form>
  );
}

export function AdminColoniasPage() {
  const [sectores, setSectores] = useState<SectorAdmin[]>([]);
  const [filas, setFilas] = useState<ColoniaFila[]>([]);
  const [busqueda, setBusqueda] = useState('');
  const [q, setQ] = useState('');
  const [sector, setSector] = useState('');
  const [pagina, setPagina] = useState(1);
  const [total, setTotal] = useState(1);
  const [estado, setEstado] = useState<'cargando' | 'listo' | 'error'>('cargando');
  const [error, setError] = useState('');
  const [formulario, setFormulario] = useState<{ editando: ColoniaFila | null } | null>(null);
  const [mensaje, setMensaje] = useState('');
  const [errorAccion, setErrorAccion] = useState('');
  const [cambiando, setCambiando] = useState<number | null>(null);
  const [recarga, setRecarga] = useState(0);

  useEffect(() => {
    let activo = true;
    api.get<{ datos: SectorAdmin[] }>('/api/v1/catalogos/sectores').then((r) => { if (activo) setSectores(r.datos); }).catch(() => undefined);
    return () => { activo = false; };
  }, []);

  useEffect(() => {
    let activo = true;
    setEstado('cargando');
    // El contrato no define GET /admin/colonias; se lista el catálogo público, que sólo devuelve colonias activas.
    api.get<RespuestaPaginada<ColoniaFila>>(`/api/v1/catalogos/colonias?${consulta({ q, sector_id: sector, pagina, por_pagina: POR_PAGINA })}`)
      .then((r) => {
        if (!activo) return;
        setFilas(r.datos.map((c) => ({ ...c, activo: c.activo ?? true })));
        setTotal(r.paginacion.total_paginas || 1);
        setEstado('listo');
      })
      .catch((e) => {
        if (!activo) return;
        setError(e instanceof ApiError ? e.message : 'No fue posible cargar las colonias.');
        setEstado('error');
      });
    return () => { activo = false; };
  }, [q, sector, pagina, recarga]);

  const buscar = (evento: FormEvent) => {
    evento.preventDefault();
    setPagina(1);
    setQ(busqueda.trim().length >= 2 ? busqueda.trim() : '');
  };
  const alGuardar = useCallback((colonia: ColoniaFila, esNueva: boolean) => {
    setFormulario(null);
    setMensaje(esNueva ? `Colonia «${colonia.nombre}» creada.` : `Colonia «${colonia.nombre}» actualizada.`);
    setRecarga((n) => n + 1);
  }, []);
  const alternar = async (colonia: ColoniaFila) => {
    setCambiando(colonia.id);
    setErrorAccion('');
    setMensaje('');
    try {
      const nueva = await api.patch<ColoniaFila>(`/api/v1/admin/colonias/${colonia.id}`, { activo: !colonia.activo });
      setFilas((actual) => actual.map((c) => (c.id === colonia.id ? { ...c, activo: nueva.activo } : c)));
      setMensaje(`Colonia «${colonia.nombre}» ${nueva.activo ? 'reactivada' : 'desactivada'}. Sus reportes históricos se conservan.`);
    } catch (e) {
      setErrorAccion(e instanceof ApiError ? e.message : 'No fue posible cambiar el estado de la colonia.');
    } finally {
      setCambiando(null);
    }
  };

  return (
    <Guard roles={['coordinador']}>
      <main className="admin-page">
        <header className="admin-intro">
          <p className="eyebrow">Catálogos · coordinación</p>
          <h1>Administración de colonias</h1>
          <p>Crea, edita y desactiva colonias. Las colonias no se eliminan para conservar la integridad de los reportes históricos.</p>
        </header>
        <section className="filters-section" aria-labelledby="colonias-filtros">
          <h2 id="colonias-filtros">Buscar colonias</h2>
          <form className="filters" onSubmit={buscar}>
            <label htmlFor="colonias-q">Nombre (mínimo 2 caracteres)</label>
            <input id="colonias-q" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
            <label htmlFor="colonias-sector">Sector</label>
            <select id="colonias-sector" value={sector} onChange={(e) => { setSector(e.target.value); setPagina(1); }}>
              <option value="">Todos los sectores</option>
              {sectores.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
            </select>
            <button className="button" type="submit">Buscar</button>
          </form>
          <button className="button button--secondary" type="button" onClick={() => setFormulario({ editando: null })}>Nueva colonia</button>
        </section>
        {formulario && <ColoniaForm key={formulario.editando?.id ?? 'nueva'} sectores={sectores} editando={formulario.editando} onCancel={() => setFormulario(null)} onSaved={alGuardar} />}
        {mensaje && <div className="form-success" role="status">{mensaje}</div>}
        {errorAccion && <ErrorMessage message={errorAccion} />}
        {estado === 'cargando' && <p className="state-message" role="status">Cargando colonias…</p>}
        {estado === 'error' && <ErrorMessage message={error} />}
        {estado === 'listo' && filas.length === 0 && <p className="state-message">No hay colonias que coincidan con la búsqueda.</p>}
        {estado === 'listo' && filas.length > 0 && (
          <>
            <div className="admin-table-wrap">
              <table className="admin-table">
                <caption className="visually-hidden">Catálogo de colonias</caption>
                <thead><tr><th scope="col">Colonia</th><th scope="col">Sector</th><th scope="col">C. P.</th><th scope="col">Estado</th><th scope="col">Acciones</th></tr></thead>
                <tbody>
                  {filas.map((c) => (
                    <tr key={c.id}>
                      <th scope="row">{c.nombre}</th>
                      <td>{c.sector.nombre}</td>
                      <td>{c.codigo_postal ?? '—'}</td>
                      <td>{c.activo ? '✔ Activa' : '⛔ Inactiva'}</td>
                      <td>
                        <div className="confirmation-actions">
                          <button className="button button--secondary" type="button" onClick={() => setFormulario({ editando: c })}>Editar<span className="visually-hidden"> {c.nombre}</span></button>
                          <button className="button" type="button" disabled={cambiando === c.id} onClick={() => void alternar(c)}>{c.activo ? 'Desactivar' : 'Reactivar'}<span className="visually-hidden"> {c.nombre}</span></button>
                        </div>
                      </td>
                    </tr>
                  ))}
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
