import { useState, type FormEvent, type ReactNode } from 'react';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { api, ApiError } from '../services/api';
import { ErrorMessage, Guard, PageIntro } from '../components/AdminShared';
import { Icon } from '../components/Icon';
import { EmptyState, Notice, StatusBadge, TableSkeleton, TypeBadge } from '../components/ui';
import { fechaCalendario } from '../utils/formato';
import type { Cuadrilla, CuadrillaDetalle, RespuestaPaginada, UsuarioAdmin } from '../types/api';

const HOY = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Ciudad_Juarez' });
const error = (e: unknown, texto: string) => (e instanceof ApiError ? e.message : texto);

/** HU-05.4: gestión de cuadrillas. Con `?id=` muestra el detalle (baches asignados, enlaces y asignación). */
export function CuadrillasPage() {
  const id = Number(new URLSearchParams(window.location.search).get('id')) || null;
  return <Guard roles={['coordinador']}>{id ? <DetalleCuadrilla id={id} /> : <ListaCuadrillas />}</Guard>;
}

function ListaCuadrillas() {
  const [recarga, setRecarga] = useState(0);
  const [aviso, setAviso] = useState('');
  const [fallo, setFallo] = useState('');
  const [form, setForm] = useState({ nombre: '', responsable: '', telefono_contacto: '' });
  const consulta = useCargaDatos<{ datos: Cuadrilla[] }>(`/api/v1/cuadrillas#${recarga}`, obtenerJson, 'No pudimos cargar las cuadrillas.');

  const crear = async (e: FormEvent) => {
    e.preventDefault(); setFallo(''); setAviso('');
    try { await api.post('/api/v1/cuadrillas', form); setAviso(`Se creó la cuadrilla ${form.nombre}.`); setForm({ nombre: '', responsable: '', telefono_contacto: '' }); setRecarga((n) => n + 1); }
    catch (err) { setFallo(error(err, 'No pudimos crear la cuadrilla.')); }
  };

  return (
    <main className="admin-page">
      <PageIntro title="Cuadrillas">Asigna baches validados a una cuadrilla con fecha programada y consulta su avance.</PageIntro>
      {aviso && <Notice tone="success">{aviso}</Notice>}
      <form className="panel admin-form" onSubmit={crear} aria-labelledby="nueva-cuadrilla">
        <h2 id="nueva-cuadrilla">Nueva cuadrilla</h2>
        {fallo && <ErrorMessage message={fallo} />}
        <label htmlFor="cu-nombre">Nombre</label><input id="cu-nombre" required minLength={3} maxLength={120} value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
        <label htmlFor="cu-resp">Responsable</label><input id="cu-resp" required minLength={3} maxLength={120} value={form.responsable} onChange={(e) => setForm({ ...form, responsable: e.target.value })} />
        <label htmlFor="cu-tel">Teléfono de contacto</label><input id="cu-tel" required inputMode="tel" pattern="[0-9 +()\-]{7,20}" value={form.telefono_contacto} onChange={(e) => setForm({ ...form, telefono_contacto: e.target.value })} />
        <button className="button button--primary" type="submit"><Icon name="plus" size={18} />Crear cuadrilla</button>
      </form>
      {consulta.estado === 'cargando' && <TableSkeleton label="Cargando cuadrillas…" />}
      {consulta.estado === 'error' && <ErrorMessage message={consulta.error} />}
      {consulta.estado === 'listo' && consulta.datos?.datos.length === 0 && <EmptyState art="inbox" title="Sin cuadrillas">Crea la primera cuadrilla para comenzar a programar reparaciones.</EmptyState>}
      {consulta.estado === 'listo' && !!consulta.datos?.datos.length && (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <caption className="visually-hidden">Cuadrillas registradas</caption>
            <thead><tr><th scope="col">Cuadrilla</th><th scope="col">Responsable</th><th scope="col">Estado</th><th scope="col">Pendientes</th></tr></thead>
            <tbody>
              {consulta.datos.datos.map((c) => (
                <tr key={c.id}>
                  <th scope="row"><a href={`/cuadrillas?id=${c.id}`}>{c.nombre}</a></th>
                  <td>{c.responsable}<div className="cell-sub"><small>{c.telefono_contacto}</small></div></td>
                  <td><span className={`chip${c.activa ? '' : ' chip--inactive'}`}><Icon name={c.activa ? 'checkCircle' : 'ban'} size={14} />{c.activa ? 'Activa' : 'Desactivada'}</span></td>
                  <td className="tabular">{c.pendientes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

const cargarEnlaces = (clave: string) => api.get<RespuestaPaginada<UsuarioAdmin>>(clave).then((r) => r.datos);

function DetalleCuadrilla({ id }: { id: number }) {
  const [recarga, setRecarga] = useState(0);
  const [aviso, setAviso] = useState<{ tono: 'success' | 'error'; texto: string } | null>(null);
  const [asignacion, setAsignacion] = useState({ folio: '', fecha_programada: HOY });
  const [enlaceId, setEnlaceId] = useState('');
  const consulta = useCargaDatos<CuadrillaDetalle>(`/api/v1/cuadrillas/${id}#${recarga}`, obtenerJson, 'No pudimos cargar la cuadrilla.');
  const enlaces = useCargaDatos('/api/v1/admin/usuarios?rol=enlace_municipal&activo=true&por_pagina=100', cargarEnlaces, 'No pudimos cargar las cuentas de enlace.');
  const c = consulta.datos;

  const ejecutar = async (accion: () => Promise<unknown>, exito: string, fallo: string) => {
    setAviso(null);
    try { await accion(); setAviso({ tono: 'success', texto: exito }); setRecarga((n) => n + 1); }
    catch (e) { setAviso({ tono: 'error', texto: error(e, fallo) }); }
  };
  const asignar = (e: FormEvent) => { e.preventDefault(); const folio = asignacion.folio.trim().toUpperCase(); void ejecutar(() => api.post(`/api/v1/cuadrillas/${id}/asignaciones`, { ...asignacion, folio }), `El bache ${folio} quedó programado para el ${fechaCalendario(asignacion.fecha_programada)}.`, 'No pudimos asignar el bache.'); };

  if (consulta.estado === 'cargando') return <main className="admin-page"><TableSkeleton label="Cargando cuadrilla…" /></main>;
  if (consulta.estado === 'error' || !c) return <main className="admin-page"><ErrorMessage message={consulta.error} /><a className="back-link" href="/cuadrillas"><Icon name="arrowLeft" size={16} />Volver a cuadrillas</a></main>;
  const activos = c.baches.filter((b) => b.asignacion_activa);
  const historial = c.baches.filter((b) => !b.asignacion_activa);

  return (
    <main className="admin-page">
      <a className="back-link" href="/cuadrillas"><Icon name="arrowLeft" size={16} />Volver a cuadrillas</a>
      <PageIntro title={c.nombre} actions={<>
        <button className="button button--secondary button--sm" type="button" onClick={() => void ejecutar(() => api.patch(`/api/v1/cuadrillas/${id}`, { activa: !c.activa }), c.activa ? 'Cuadrilla desactivada.' : 'Cuadrilla activada.', 'No pudimos cambiar el estado.')}><Icon name={c.activa ? 'ban' : 'checkCircle'} size={16} />{c.activa ? 'Desactivar' : 'Activar'}</button>
        <button className="button button--quiet button--sm" type="button" onClick={() => void ejecutar(async () => { await api.delete(`/api/v1/cuadrillas/${id}`); window.location.assign('/cuadrillas'); }, 'Cuadrilla eliminada.', 'No pudimos eliminar la cuadrilla.')}><Icon name="trash" size={16} />Eliminar</button>
      </>}>{c.responsable} · {c.telefono_contacto} · {c.activa ? 'Activa' : 'Desactivada'} · {c.pendientes} pendiente(s)</PageIntro>
      {aviso && <Notice tone={aviso.tono} live={aviso.tono === 'error' ? 'alert' : 'status'}>{aviso.texto}</Notice>}

      <form className="panel admin-form" onSubmit={asignar} aria-labelledby="asignar-titulo">
        <h2 id="asignar-titulo">Asignar bache validado</h2>
        <label htmlFor="as-folio">Folio del bache</label><input id="as-folio" required pattern="(BCH|bch)-[0-9]{4}-[0-9]{6}" value={asignacion.folio} onChange={(e) => setAsignacion({ ...asignacion, folio: e.target.value })} placeholder="BCH-2026-000418" />
        <label htmlFor="as-fecha">Fecha programada</label><input id="as-fecha" type="date" required min={HOY} value={asignacion.fecha_programada} onChange={(e) => setAsignacion({ ...asignacion, fecha_programada: e.target.value })} />
        <button className="button button--primary" type="submit" disabled={!c.activa}><Icon name="calendar" size={18} />Asignar y programar</button>
        {!c.activa && <p className="field-help">Activa la cuadrilla para asignarle trabajo.</p>}
      </form>

      <section className="panel" aria-labelledby="enlaces-titulo">
        <h2 id="enlaces-titulo"><Icon name="users" size={20} />Enlaces municipales</h2>
        {c.enlaces.length === 0 ? <p className="field-help">Ningún enlace municipal está vinculado.</p> : (
          <ul className="chip-list">{c.enlaces.map((u) => <li className={`chip${u.activo ? '' : ' chip--inactive'}`} key={u.id}><Icon name="user" size={14} />{u.nombre}{!u.activo && ' (suspendida)'}<button className="link-button" type="button" onClick={() => void ejecutar(() => api.delete(`/api/v1/cuadrillas/${id}/enlaces/${u.id}`), 'Enlace desvinculado.', 'No pudimos desvincular.')}>Desvincular</button></li>)}</ul>
        )}
        <form className="inline-form" onSubmit={(e) => { e.preventDefault(); if (enlaceId) void ejecutar(() => api.post(`/api/v1/cuadrillas/${id}/enlaces`, { usuario_id: enlaceId }), 'Enlace vinculado.', 'No pudimos vincular el enlace.'); }}>
          <label htmlFor="en-sel" className="visually-hidden">Cuenta de enlace municipal</label>
          <select id="en-sel" value={enlaceId} onChange={(e) => setEnlaceId(e.target.value)} disabled={enlaces.estado !== 'listo'}>
            <option value="">{enlaces.estado === 'cargando' ? 'Cargando cuentas…' : 'Elige una cuenta de enlace'}</option>
            {(enlaces.datos ?? []).filter((u) => !c.enlaces.some((e) => e.id === u.id)).map((u) => <option key={u.id} value={u.id}>{u.nombre}</option>)}
          </select>
          <button className="button button--secondary" type="submit" disabled={!enlaceId}>Vincular</button>
        </form>
      </section>

      <section aria-labelledby="baches-titulo">
        <h2 id="baches-titulo">Baches asignados</h2>
        {activos.length === 0 ? <EmptyState art="road" title="Sin baches asignados">Asigna un bache validado con el formulario de arriba.</EmptyState> : <TablaBaches baches={activos} />}
        {historial.length > 0 && <details className="map-list"><summary>Historial de reasignaciones ({historial.length})</summary><TablaBaches baches={historial} /></details>}
      </section>
    </main>
  );
}

export function TablaBaches({ baches, acciones }: { baches: CuadrillaDetalle['baches']; acciones?: (b: CuadrillaDetalle['baches'][number]) => ReactNode }) {
  return (
    <div className="admin-table-wrap">
      <table className="admin-table">
        <caption className="visually-hidden">Baches asignados</caption>
        <thead><tr><th scope="col">Folio</th><th scope="col">Ubicación</th><th scope="col">Estado</th><th scope="col">Fecha programada</th>{acciones && <th scope="col">Avance</th>}</tr></thead>
        <tbody>
          {baches.map((b) => (
            <tr key={b.asignacion_id}>
              <th scope="row"><a className="tabular" href={`/reportes/${b.folio}`}>{b.folio}</a><div className="cell-sub"><TypeBadge tipo={b.tipo_dano} /></div></th>
              <td><div className="cell-main">{b.calle}</div><small>{b.colonia.nombre}{b.referencia ? ` · ${b.referencia}` : ''}</small></td>
              <td><StatusBadge estado={b.estado} />{b.fecha_reparacion && <div className="cell-sub"><small>Reparado el {fechaCalendario(b.fecha_reparacion)}</small></div>}</td>
              <td className="tabular">{fechaCalendario(b.fecha_programada)}<div className="cell-sub"><small>{b.cuadrilla}</small></div></td>
              {acciones && <td>{acciones(b)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
