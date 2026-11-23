import { useState, type FormEvent } from 'react';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { api, ApiError } from '../services/api';
import { ErrorMessage, Guard, PageIntro } from '../components/AdminShared';
import { Icon } from '../components/Icon';
import { Notice, TableSkeleton } from '../components/ui';
import type { MotivoRechazo, TipoDanoAdmin } from '../types/api';

type Aviso = { tono: 'success' | 'error'; texto: string } | null;

/** HU-06.3: tipos de daño y motivos de rechazo. Nada se borra: se desactiva y los históricos conservan su texto. */
export function AdminCatalogosPage() {
  const [recarga, setRecarga] = useState(0);
  const [aviso, setAviso] = useState<Aviso>(null);
  const [nuevo, setNuevo] = useState({ nombre: '', descripcion: '' });
  const tipos = useCargaDatos<{ datos: TipoDanoAdmin[] }>(`/api/v1/admin/catalogos/tipos-dano#${recarga}`, obtenerJson, 'No pudimos cargar los tipos de daño.');
  const motivos = useCargaDatos<{ datos: MotivoRechazo[] }>(`/api/v1/admin/catalogos/motivos-rechazo#${recarga}`, obtenerJson, 'No pudimos cargar los motivos.');

  const guardar = async (accion: () => Promise<unknown>, exito: string) => {
    setAviso(null);
    try { await accion(); setAviso({ tono: 'success', texto: exito }); setRecarga((n) => n + 1); }
    catch (e) { setAviso({ tono: 'error', texto: e instanceof ApiError ? e.message : 'No pudimos guardar el cambio.' }); }
  };
  const crearMotivo = (e: FormEvent) => {
    e.preventDefault();
    void guardar(async () => { await api.post('/api/v1/admin/catalogos/motivos-rechazo', { nombre: nuevo.nombre.trim(), descripcion: nuevo.descripcion.trim() || null }); setNuevo({ nombre: '', descripcion: '' }); }, 'Motivo creado.');
  };

  return (
    <Guard roles={['coordinador']}>
      <main className="admin-page">
        <PageIntro title="Catálogos">Activa o desactiva los tipos de daño disponibles para reportar y administra los motivos con los que moderación rechaza reportes.</PageIntro>
        {aviso && <Notice tone={aviso.tono} live={aviso.tono === 'error' ? 'alert' : 'status'}>{aviso.texto}</Notice>}

        <section aria-labelledby="tipos-titulo">
          <h2 id="tipos-titulo"><Icon name="tag" size={20} />Tipos de daño</h2>
          <p className="field-help">Un tipo desactivado deja de aparecer en el formulario y el servidor rechaza reportes nuevos de ese tipo. Los reportes existentes no cambian.</p>
          {tipos.estado === 'cargando' && <TableSkeleton label="Cargando tipos…" />}
          {tipos.estado === 'error' && <ErrorMessage message={tipos.error} />}
          {tipos.datos && <FilasCatalogo filas={tipos.datos.datos.map((t) => ({ ...t, etiqueta: t.clave }))} onGuardar={(id, cambio) => guardar(() => api.patch(`/api/v1/admin/catalogos/tipos-dano/${id}`, cambio), 'Tipo de daño actualizado.')} />}
        </section>

        <section aria-labelledby="motivos-titulo">
          <h2 id="motivos-titulo"><Icon name="xCircle" size={20} />Motivos de rechazo</h2>
          <form className="panel admin-form" onSubmit={crearMotivo}>
            <h3>Nuevo motivo</h3>
            <label htmlFor="mo-nombre">Nombre</label><input id="mo-nombre" required minLength={3} maxLength={120} value={nuevo.nombre} onChange={(e) => setNuevo({ ...nuevo, nombre: e.target.value })} />
            <label htmlFor="mo-desc">Descripción (opcional)</label><input id="mo-desc" maxLength={300} value={nuevo.descripcion} onChange={(e) => setNuevo({ ...nuevo, descripcion: e.target.value })} />
            <button className="button button--primary" type="submit"><Icon name="plus" size={18} />Agregar motivo</button>
          </form>
          {motivos.estado === 'cargando' && <TableSkeleton label="Cargando motivos…" />}
          {motivos.estado === 'error' && <ErrorMessage message={motivos.error} />}
          {motivos.datos && <FilasCatalogo filas={motivos.datos.datos.map((m) => ({ ...m, etiqueta: null }))} onGuardar={(id, cambio) => guardar(() => api.patch(`/api/v1/admin/catalogos/motivos-rechazo/${id}`, cambio), 'Motivo actualizado.')} />}
        </section>
      </main>
    </Guard>
  );
}

type Fila = { id: number; nombre: string; descripcion: string | null; activo: boolean; etiqueta: string | null };

function FilasCatalogo({ filas, onGuardar }: { filas: Fila[]; onGuardar: (id: number, cambio: Partial<Fila>) => Promise<void> }) {
  return (
    <div className="admin-table-wrap">
      <table className="admin-table">
        <thead><tr><th scope="col">Nombre visible</th><th scope="col">Descripción</th><th scope="col">Estado</th><th scope="col">Acciones</th></tr></thead>
        <tbody>{filas.map((f) => <FilaEditable key={`${f.id}-${f.nombre}-${f.activo}`} fila={f} onGuardar={onGuardar} />)}</tbody>
      </table>
    </div>
  );
}

function FilaEditable({ fila, onGuardar }: { fila: Fila; onGuardar: (id: number, cambio: Partial<Fila>) => Promise<void> }) {
  const [nombre, setNombre] = useState(fila.nombre);
  const [descripcion, setDescripcion] = useState(fila.descripcion ?? '');
  const cambiado = nombre.trim() !== fila.nombre || descripcion.trim() !== (fila.descripcion ?? '');
  return (
    <tr>
      <th scope="row">
        <label className="visually-hidden" htmlFor={`n-${fila.id}-${fila.etiqueta ?? 'm'}`}>Nombre</label>
        <input id={`n-${fila.id}-${fila.etiqueta ?? 'm'}`} value={nombre} minLength={3} onChange={(e) => setNombre(e.target.value)} />
        {fila.etiqueta && <div className="cell-sub"><small>Tipo base: {fila.etiqueta}</small></div>}
      </th>
      <td><label className="visually-hidden" htmlFor={`d-${fila.id}-${fila.etiqueta ?? 'm'}`}>Descripción</label><input id={`d-${fila.id}-${fila.etiqueta ?? 'm'}`} value={descripcion} maxLength={300} onChange={(e) => setDescripcion(e.target.value)} /></td>
      <td><span className={`chip${fila.activo ? '' : ' chip--inactive'}`}><Icon name={fila.activo ? 'checkCircle' : 'ban'} size={14} />{fila.activo ? 'Activo' : 'Desactivado'}</span></td>
      <td className="cell-actions">
        <button className="button button--secondary button--sm" type="button" disabled={!cambiado || nombre.trim().length < 3} onClick={() => void onGuardar(fila.id, { nombre: nombre.trim(), descripcion: descripcion.trim() || null })}>Guardar</button>
        <button className="button button--quiet button--sm" type="button" onClick={() => void onGuardar(fila.id, { activo: !fila.activo })}>{fila.activo ? 'Desactivar' : 'Activar'}</button>
      </td>
    </tr>
  );
}
