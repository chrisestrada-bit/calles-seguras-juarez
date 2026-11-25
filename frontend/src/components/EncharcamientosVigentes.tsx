import { useState } from 'react';
import { api, mensajeDeError } from '../services/api';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { Icon } from './Icon';
import { EmptyState } from './ui';
import { DESMENTIDOS_PARA_HISTORICO, esIntransitable, horaLocal, indiceNivel, restante, textoNivel } from '../utils/vigencia';
import type { ConfirmacionResponse, EstadoReporte, ReportePublico, ReporteResumenPublico, Vigencia } from '../types/api';

interface Props {
  vigentes: ReporteResumenPublico[];
  estado: 'cargando' | 'listo' | 'error';
  error: string;
  autenticado: boolean;
  ahora: number;
  seleccionado: string | null;
  onSeleccionar: (folio: string) => void;
  /** Vuelve a consultar la lista si la carga falló. */
  onReintentar?: () => void;
}

/**
 * HU-03.2 / HU-03.3: encharcamientos vigentes con su vigencia de 6 h y los votos «Sigue ahí» / «Ya no hay agua».
 * Los votos usan el mismo endpoint que el detalle (POST /reportes/{folio}/confirmaciones) y se ocultan
 * a quien creó el reporte (es_mio, sólo disponible en el detalle autenticado). Sin sesión los botones se ven
 * con sus contadores públicos y llevan a iniciar sesión (votar requiere cuenta, RN-06).
 */
export function EncharcamientosVigentes({ vigentes, estado, error, autenticado, ahora, seleccionado, onSeleccionar, onReintentar }: Props) {
  return (
    <section className="agua-vigente" aria-labelledby="agua-titulo">
      <div className="agua-vigente__cabeza">
        <h2 id="agua-titulo">Encharcamientos <em>vigentes</em></h2>
        <p>Cada «Sigue ahí» reinicia las 6 horas de vigencia. Con {DESMENTIDOS_PARA_HISTORICO} «Ya no hay agua» de personas distintas pasa a histórico.</p>
      </div>
      {estado === 'cargando' && <div className="agua-vigente__estado" role="status"><span className="spinner" aria-hidden="true" />Cargando encharcamientos vigentes…</div>}
      {estado === 'error' && (
        <div className="agua-vigente__error" role="alert">
          <Icon name="alert" size={20} />
          <div>
            <strong>No pudimos cargar los encharcamientos vigentes.</strong>
            <p>{error} Si el problema sigue, consulta el mapa o la lista de reportes más abajo.</p>
          </div>
          {onReintentar && <button className="button button--secondary button--sm" type="button" onClick={onReintentar}><Icon name="history" size={16} />Reintentar</button>}
        </div>
      )}
      {estado === 'listo' && vigentes.length === 0 && (
        <EmptyState art="road" title="Sin encharcamientos vigentes">Ahora mismo nadie ha reportado agua en las calles. Si ves un encharcamiento, repórtalo para avisar a los demás.</EmptyState>
      )}
      {estado === 'listo' && vigentes.length > 0 && (
        <ol className="agua-lista">
          {vigentes.map((r) => <FilaEncharcamiento key={r.folio} reporte={r} autenticado={autenticado} ahora={ahora} activo={seleccionado === r.folio} onSeleccionar={onSeleccionar} />)}
        </ol>
      )}
    </section>
  );
}

function FilaEncharcamiento({ reporte, autenticado, ahora, activo, onSeleccionar }: { reporte: ReporteResumenPublico; autenticado: boolean; ahora: number; activo: boolean; onSeleccionar: (folio: string) => void }) {
  // HU-03.3: sólo con sesión se pide el detalle para saber si el reporte es propio.
  const detalle = useCargaDatos<ReportePublico>(autenticado ? `/api/v1/reportes/${encodeURIComponent(reporte.folio)}` : null, obtenerJson, 'No pudimos comprobar si puedes confirmar este reporte.');
  const [local, setLocal] = useState<{ vigencia: Vigencia; estado: EstadoReporte } | null>(null);
  const [enviando, setEnviando] = useState<'sigue_ahi' | 'ya_no_hay_agua' | null>(null);
  const [aviso, setAviso] = useState<{ tipo: 'ok' | 'error'; texto: string } | null>(null);

  const vigencia = local?.vigencia ?? reporte.vigencia;
  const estadoActual = local?.estado ?? reporte.estado;
  const tiempo = restante(vigencia, ahora);
  const nivel = indiceNivel(reporte.nivel_agua);
  const grave = esIntransitable(reporte);
  const historico = estadoActual !== 'Activo';
  const esMio = detalle.datos?.es_mio === true;

  const votar = async (tipo: 'sigue_ahi' | 'ya_no_hay_agua') => {
    setEnviando(tipo); setAviso(null);
    try {
      const r = await api.post<ConfirmacionResponse>(`/api/v1/reportes/${encodeURIComponent(reporte.folio)}/confirmaciones`, { tipo });
      setLocal({ vigencia: r.vigencia, estado: r.estado_reporte });
      setAviso({ tipo: 'ok', texto: r.mensaje });
    } catch (e) {
      setAviso({ tipo: 'error', texto: mensajeDeError(e, 'No fue posible registrar tu confirmación. Intenta de nuevo.') });
    } finally { setEnviando(null); }
  };

  return (
    <li className={`agua-fila${activo ? ' is-activo' : ''}${grave ? ' is-grave' : ''}${historico ? ' is-historico' : ''}`}>
      <button type="button" className="agua-fila__lugar" onClick={() => onSeleccionar(reporte.folio)} aria-pressed={activo}>
        <span className="tabular agua-fila__folio">{reporte.folio}</span>
        <span className="agua-fila__calle">{reporte.calle}</span>
        <span className="agua-fila__meta">{reporte.colonia.nombre} · reportado {horaLocal(reporte.created_at)}</span>
      </button>

      <div className="agua-nivel">
        <span className="agua-nivel__barras" aria-hidden="true">{[0, 1, 2, 3].map((i) => <i key={i} className={i <= nivel ? 'on' : undefined} />)}</span>
        <span className="agua-nivel__texto">{grave && <Icon name="alert" size={14} />}{textoNivel(reporte.nivel_agua)}</span>
      </div>

      <div className="agua-vigencia">
        {historico ? <span className="agua-vigencia__texto">Pasó a histórico</span> : tiempo && <>
          <span className="agua-vigencia__barra" role="img" aria-label={`Quedan ${tiempo.texto} de 6 horas de vigencia`}><i style={{ inlineSize: `${tiempo.fraccion * 100}%` }} /></span>
          <span className="tabular agua-vigencia__texto">{tiempo.texto} · vence {tiempo.vence}</span>
        </>}
      </div>

      <div className="agua-acciones">
        {historico ? null : !autenticado ? (
          <div className="agua-votos" role="group" aria-label={`¿Sigue el agua en ${reporte.calle}? Inicia sesión para confirmar`}>
            <a className="agua-voto" href="/login" aria-describedby={`login-${reporte.folio}`}>
              <Icon name="water" size={16} />Sigue ahí{vigencia && <span className="tabular">{vigencia.sigue_ahi}</span>}
            </a>
            <a className="agua-voto" href="/login" aria-describedby={`login-${reporte.folio}`}>
              <Icon name="sun" size={16} />Ya no hay agua{vigencia && <span className="tabular">({vigencia.ya_no_hay_agua}/{DESMENTIDOS_PARA_HISTORICO})</span>}
            </a>
            <span id={`login-${reporte.folio}`} className="agua-acciones__nota">Inicia sesión para confirmar</span>
          </div>
        ) : esMio ? (
          <span className="agua-acciones__nota">Es tu reporte: no puedes confirmarlo</span>
        ) : (
          <div className="agua-votos" role="group" aria-label={`¿Sigue el agua en ${reporte.calle}?`}>
            <button type="button" className="agua-voto" disabled={enviando !== null || detalle.estado === 'cargando'} onClick={() => void votar('sigue_ahi')}>
              <Icon name="water" size={16} />{enviando === 'sigue_ahi' ? 'Enviando…' : 'Sigue ahí'}{vigencia && <span className="tabular">{vigencia.sigue_ahi}</span>}
            </button>
            <button type="button" className="agua-voto" disabled={enviando !== null || detalle.estado === 'cargando'} onClick={() => void votar('ya_no_hay_agua')}>
              <Icon name="sun" size={16} />{enviando === 'ya_no_hay_agua' ? 'Enviando…' : 'Ya no hay agua'}{vigencia && <span className="tabular">({vigencia.ya_no_hay_agua}/{DESMENTIDOS_PARA_HISTORICO})</span>}
            </button>
          </div>
        )}
        <a className="agua-acciones__detalle" href={`/reportes/${encodeURIComponent(reporte.folio)}`}>Ver detalle<span className="visually-hidden"> de {reporte.folio}</span></a>
        {aviso && <p className={aviso.tipo === 'ok' ? 'agua-aviso' : 'agua-aviso agua-aviso--error'} role={aviso.tipo === 'ok' ? 'status' : 'alert'}>{aviso.texto}</p>}
      </div>
    </li>
  );
}
