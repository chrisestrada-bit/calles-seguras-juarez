import { lazy, Suspense, useMemo, useState } from 'react';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { Icon } from './Icon';
import { StatusBadge, TypeBadge, TypeGlyph } from './ui';
import { fusionarEnVivo, type FiltrosLista, type Vivos } from '../utils/enVivo';
import { horaLocal } from '../utils/vigencia';
import type { EstadoPavimento, IndicadoresResumen, MapaResponse, TipoDano } from '../types/api';

// Leaflet se descarga aparte (chunk propio) para no bloquear el primer pintado de la portada.
const ReportMap = lazy(() => import('./ReportMap').then((m) => ({ default: m.ReportMap })));

const CAPAS: { tipo: TipoDano; texto: string; tono: string }[] = [
  { tipo: 'Bache', texto: 'Baches', tono: 'road' },
  { tipo: 'Encharcamiento', texto: 'Encharcamientos', tono: 'water' },
  { tipo: 'Alcantarilla sin tapa', texto: 'Alcantarillas sin tapa', tono: 'manhole' },
];
const ABIERTOS: EstadoPavimento[] = ['Recibido', 'Validado', 'Programado', 'En reparación'];

interface Props {
  /** Mismos filtros de la lista (HU-04.2) como query string: el mapa de la portada refleja la consulta activa. */
  filtros: string;
  filtrosLista: FiltrosLista;
  vivos: Vivos;
  seleccionado: string | null;
  onSeleccionar: (folio: string) => void;
}

/** Tablero de la portada: mapa con capas ocultables, reporte seleccionado e indicadores públicos. Sin datos personales (RN-04). */
export function TableroPortada({ filtros, filtrosLista, vivos, seleccionado, onSeleccionar }: Props) {
  const mapa = useCargaDatos<MapaResponse>(`/api/v1/reportes/mapa?${filtros}`, obtenerJson, 'No fue posible cargar el mapa de reportes.');
  const indicadores = useCargaDatos<IndicadoresResumen>('/api/v1/indicadores/resumen', obtenerJson, 'No fue posible cargar los indicadores.');
  const [capas, setCapas] = useState<Record<TipoDano, boolean>>({ Bache: true, Encharcamiento: true, 'Alcantarilla sin tapa': true });
  const [mapaCaido, setMapaCaido] = useState(false);

  const todos = useMemo(() => fusionarEnVivo(mapa.datos?.datos ?? [], vivos, filtrosLista, true), [mapa.datos, vivos, filtrosLista]);
  const visibles = useMemo(() => todos.filter((m) => capas[m.tipo_dano]), [todos, capas]);
  const elegido = visibles.find((m) => m.folio === seleccionado) ?? visibles.find((m) => m.nivel_agua === 'intransitable') ?? visibles[0] ?? null;

  const ind = indicadores.datos;
  const abiertos = ind ? ABIERTOS.reduce((suma, e) => suma + (ind.pavimento.por_estado[e] ?? 0), 0) : null;
  const valor = (n: number | null | undefined) => (indicadores.estado === 'listo' && n !== null && n !== undefined ? String(n) : '—');

  return (
    <div className="tablero">
      <div className="tablero__barra">
        <fieldset className="capas">
          <legend className="visually-hidden">Capas visibles en el mapa de la portada</legend>
          {CAPAS.map((c) => (
            <label key={c.tipo} className={`capa capa--${c.tono}`}>
              <input type="checkbox" checked={capas[c.tipo]} onChange={() => setCapas((a) => ({ ...a, [c.tipo]: !a[c.tipo] }))} />
              <TypeGlyph tipo={c.tipo} size={18} />{c.texto}
            </label>
          ))}
        </fieldset>
        {elegido && <span className="tabular tablero__coords" aria-label={`Coordenadas del reporte seleccionado: ${elegido.ubicacion.latitud.toFixed(4)} norte, ${Math.abs(elegido.ubicacion.longitud).toFixed(4)} oeste`}>{elegido.ubicacion.latitud.toFixed(4)}° N · {Math.abs(elegido.ubicacion.longitud).toFixed(4)}° O</span>}
      </div>

      <div className="tablero__mapa">
        {mapa.estado === 'cargando' && <div className="tablero__estado" role="status"><span className="spinner" aria-hidden="true" />Cargando mapa…</div>}
        {mapa.estado === 'error' && <div className="tablero__estado tablero__estado--error" role="alert"><Icon name="alert" size={18} />{mapa.error}</div>}
        {mapa.estado === 'listo' && todos.length === 0 && <div className="tablero__estado" role="status"><Icon name="info" size={18} />No hay reportes en el mapa con la consulta actual.</div>}
        {mapa.estado === 'listo' && todos.length > 0 && visibles.length === 0 && <div className="tablero__estado" role="status"><Icon name="layers" size={18} />Activa al menos una capa para ver reportes.</div>}
        {mapaCaido && <div className="tablero__estado tablero__estado--error" role="alert"><Icon name="alert" size={18} />No pudimos cargar los mosaicos del mapa. Los mismos reportes están en la lista de abajo.</div>}
        {mapa.estado === 'listo' && visibles.length > 0 && !mapaCaido && (
          <Suspense fallback={<div className="tablero__estado" role="status"><span className="spinner" aria-hidden="true" />Cargando mapa…</div>}>
            <ReportMap marcadores={visibles} seleccionado={elegido?.folio ?? null} onSeleccionar={onSeleccionar} miUbicacion={null} onFalloMapa={() => setMapaCaido(true)} etiqueta="Mapa de la portada con los reportes de la consulta actual. Los mismos reportes están en la lista de reportes recientes." />
          </Suspense>
        )}
      </div>

      <div className="tablero__foco" aria-live="polite">
        {elegido ? (
          <>
            <TypeBadge tipo={elegido.tipo_dano} />
            <div className="tablero__foco-texto">
              <p className="tablero__foco-calle">{elegido.calle}</p>
              <p className="tablero__foco-meta"><span className="tabular">{elegido.folio}</span> · {elegido.colonia.nombre} · {horaLocal(elegido.created_at)} h</p>
            </div>
            <StatusBadge estado={elegido.estado} etiqueta={elegido.etiqueta_publica} />
            <a className="tablero__foco-link" href={`/reportes/${encodeURIComponent(elegido.folio)}`}>Ver detalle<span className="visually-hidden"> de {elegido.folio}</span><Icon name="arrowRight" size={16} /></a>
          </>
        ) : <p className="tablero__foco-meta">Selecciona un punto del mapa o un encharcamiento para ver su resumen.</p>}
      </div>

      <dl className="kpis" aria-describedby={indicadores.estado === 'error' ? 'kpis-error' : undefined}>
        <div><dt>Daños abiertos</dt><dd className="tabular">{valor(abiertos)}</dd></div>
        <div><dt>Sin validar</dt><dd className="tabular">{valor(ind?.pavimento.por_estado.Recibido)}</dd></div>
        <div><dt>Encharcamientos vigentes</dt><dd className="tabular kpis__agua">{valor(ind?.encharcamientos.activos)}</dd></div>
        <div><dt>Longevidad promedio</dt><dd className="tabular">{valor(ind ? Math.round(ind.pavimento.longevidad_promedio_abiertos_dias) : null)}<small> días</small></dd></div>
      </dl>
      {indicadores.estado === 'error' && <p id="kpis-error" className="kpis__error" role="status">{indicadores.error}</p>}
    </div>
  );
}
