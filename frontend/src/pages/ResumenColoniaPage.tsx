import { useState } from 'react';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { BuscadorColonia } from '../components/BuscadorColonia';
import { PageIntro } from '../components/AdminShared';
import { Icon } from '../components/Icon';
import { BlockSkeleton, EmptyState } from '../components/ui';
import { fechaHora } from '../utils/formato';
import type { Colonia, ResumenColonia } from '../types/api';

const inicial = () => Number(new URLSearchParams(window.location.search).get('colonia')) || null;

/** HU-07.2: resumen público por colonia, con las mismas tarjetas métricas que /tablero. Sin datos personales. */
export function ResumenColoniaPage() {
  const [coloniaId, setColoniaId] = useState<number | null>(inicial);
  const consulta = useCargaDatos<ResumenColonia>(coloniaId ? `/api/v1/publico/colonias/${coloniaId}/resumen` : null, obtenerJson, 'No pudimos cargar el resumen de la colonia.');
  const elegir = (c: Colonia) => { setColoniaId(c.id); window.history.replaceState(null, '', `/resumen-colonia?colonia=${c.id}`); };
  const r = consulta.datos;
  const promedio = r?.tiempo_promedio_reparacion_dias;

  return (
    <main className="admin-page">
      <PageIntro title="Resumen por colonia">Consulta cuántos reportes siguen abiertos en una colonia, cuántos se repararon y cuánto tarda en promedio una reparación.</PageIntro>
      <section className="panel"><BuscadorColonia etiqueta="Colonia o código postal" onElegir={elegir} /></section>
      {coloniaId === null && <EmptyState art="map" title="Elige una colonia">Busca por nombre o código postal para ver su resumen.</EmptyState>}
      {consulta.estado === 'cargando' && <div className="kpi-grid">{[0, 1, 2, 3].map((i) => <div className="kpi-card" key={i}><BlockSkeleton label="Cargando resumen…" lines={1} /></div>)}</div>}
      {consulta.estado === 'error' && <div className="form-error" role="alert">{consulta.error}</div>}
      {consulta.estado === 'listo' && r && (
        <section aria-labelledby="resumen-titulo">
          <h2 id="resumen-titulo">{r.colonia.nombre} <small>· {r.sector.nombre}{r.codigo_postal ? ` · C.P. ${r.codigo_postal}` : ''}</small></h2>
          {!r.activa && <p className="field-help"><Icon name="info" size={16} />Esta colonia está desactivada en el catálogo; se muestra su historial.</p>}
          {r.abiertos === 0 && r.reparados === 0 && r.encharcamientos_activos === 0 && <p className="field-help" role="status">Esta colonia aún no tiene reportes.</p>}
          <div className="kpi-grid" aria-label="Métricas de la colonia">
            <article className="kpi-card kpi-card--road"><span className="kpi-card__label"><Icon name="inbox" size={18} />Reportes abiertos</span><strong className="tabular">{r.abiertos}</strong><span className="field-help">Sin validar {r.abiertos_por_estado['Recibido'] ?? 0} · Validados {r.abiertos_por_estado['Validado'] ?? 0} · Programados {r.abiertos_por_estado['Programado'] ?? 0} · En reparación {r.abiertos_por_estado['En reparación'] ?? 0}</span></article>
            <article className="kpi-card kpi-card--success"><span className="kpi-card__label"><Icon name="check" size={18} />Reparados</span><strong className="tabular">{r.reparados}</strong></article>
            <article className="kpi-card"><span className="kpi-card__label"><Icon name="clock" size={18} />Tiempo promedio de reparación</span><strong className="tabular">{promedio === null ? 'Sin datos' : <>{promedio}<small> {promedio === 1 ? 'día' : 'días'}</small></>}</strong></article>
            <article className="kpi-card kpi-card--water"><span className="kpi-card__label"><Icon name="water" size={18} />Encharcamientos vigentes</span><strong className="tabular">{r.encharcamientos_activos}</strong></article>
          </div>
          <dl className="criterios-list">
            <div><dt>Qué cuenta como abierto</dt><dd>{r.criterios.abiertos}</dd></div>
            <div><dt>Cómo se calcula el promedio</dt><dd>{r.criterios.tiempo_promedio_reparacion}</dd></div>
            <div><dt>Actualizado</dt><dd>{fechaHora(r.actualizado_en)}</dd></div>
          </dl>
          <a className="button button--secondary" href={`/?colonia=${r.colonia.id}`}><Icon name="layers" size={18} />Ver reportes de esta colonia</a>
        </section>
      )}
    </main>
  );
}
