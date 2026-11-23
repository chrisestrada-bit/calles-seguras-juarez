import { useState, type FormEvent } from 'react';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { api, ApiError } from '../services/api';
import { ErrorMessage, Guard, PageIntro } from '../components/AdminShared';
import { Icon } from '../components/Icon';
import { EmptyState, Notice, TableSkeleton } from '../components/ui';
import { TablaBaches } from './CuadrillasPage';
import type { AvanceResponse, BacheAsignado, MisAsignaciones } from '../types/api';

const HOY = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Ciudad_Juarez' });

/** HU-05.5: vista operativa del enlace municipal. Sólo ve y avanza baches de sus cuadrillas (el servidor lo garantiza). */
export function EnlacePage() {
  const [recarga, setRecarga] = useState(0);
  const [reparados, setReparados] = useState(false);
  const [aviso, setAviso] = useState<{ tono: 'success' | 'error'; texto: string } | null>(null);
  const consulta = useCargaDatos<MisAsignaciones>(`/api/v1/enlace/reportes?incluir_reparados=${reparados}#${recarga}`, obtenerJson, 'No pudimos cargar tus baches asignados.');
  const d = consulta.datos;

  return (
    <Guard roles={['enlace_municipal']}>
      <main className="admin-page">
        <PageIntro title="Mis cuadrillas">Reporta el avance de los baches asignados a tus cuadrillas: «Programado → En reparación → Reparado».</PageIntro>
        {aviso && <Notice tone={aviso.tono} live={aviso.tono === 'error' ? 'alert' : 'status'}>{aviso.texto}</Notice>}
        {d && <p className="field-help"><Icon name="users" size={16} />Cuadrillas: {d.cuadrillas.length ? d.cuadrillas.map((c) => `${c.nombre}${c.activa ? '' : ' (desactivada)'}`).join(', ') : 'ninguna vinculada; pide a coordinación que te asigne.'}</p>}
        <label className="checkbox-row"><input type="checkbox" checked={reparados} onChange={(e) => setReparados(e.target.checked)} /> Mostrar también los reparados</label>
        {consulta.estado === 'cargando' && <TableSkeleton label="Cargando baches…" />}
        {consulta.estado === 'error' && <ErrorMessage message={consulta.error} />}
        {consulta.estado === 'listo' && d && d.datos.length === 0 && <EmptyState art="road" title="Sin baches pendientes">Cuando coordinación programe un bache para tus cuadrillas aparecerá aquí.</EmptyState>}
        {consulta.estado === 'listo' && d && d.datos.length > 0 && (
          <TablaBaches baches={d.datos} acciones={(b) => <Avance bache={b} onHecho={(r) => { setAviso({ tono: 'success', texto: r.mensaje }); setRecarga((n) => n + 1); }} onError={(t) => setAviso({ tono: 'error', texto: t })} />} />
        )}
      </main>
    </Guard>
  );
}

function Avance({ bache, onHecho, onError }: { bache: BacheAsignado; onHecho: (r: AvanceResponse) => void; onError: (t: string) => void }) {
  const [fecha, setFecha] = useState(HOY);
  const [ocupado, setOcupado] = useState(false);
  const siguiente = bache.transiciones_disponibles.find((e) => e === 'En reparación' || e === 'Reparado');
  if (!siguiente) return <small className="field-help">Sin acciones</small>;
  const enviar = async (e: FormEvent) => {
    e.preventDefault(); setOcupado(true);
    try { onHecho(await api.post<AvanceResponse>(`/api/v1/enlace/reportes/${bache.folio}/avance`, { estado_nuevo: siguiente, ...(siguiente === 'Reparado' ? { fecha_reparacion: fecha } : {}) })); }
    catch (err) { onError(err instanceof ApiError ? err.message : 'No pudimos registrar el avance.'); }
    finally { setOcupado(false); }
  };
  return (
    <form className="admin-action" onSubmit={enviar}>
      {siguiente === 'Reparado' && <label>Fecha de reparación<input type="date" required max={HOY} value={fecha} onChange={(e) => setFecha(e.target.value)} /></label>}
      <button className="button button--primary button--sm" type="submit" disabled={ocupado}><Icon name={siguiente === 'Reparado' ? 'check' : 'wrench'} size={16} />{ocupado ? 'Guardando…' : `Marcar «${siguiente}»`}</button>
    </form>
  );
}
