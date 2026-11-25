import { lazy, Suspense, useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { api, ApiError, descargarArchivo } from '../services/api';
import { useAuth } from '../context/useAuth';
import { agruparPorSector, cargarColonias, etiquetaColonia, filtrarColonias } from '../services/catalogos';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { useEncharcamientosEnVivo } from '../hooks/useEncharcamientosEnVivo';
import { guardarConsulta, leerConsulta, useEnLinea } from '../services/offline';
import { fusionarEnVivo, PATRON_FOLIO, SIN_FILTROS, type FiltrosLista as Filtros } from '../utils/enVivo';
import { fechaHora } from '../utils/formato';
import { ReportCard } from '../components/ReportCard';
import { Pagination } from '../components/AdminShared';
import { Icon } from '../components/Icon';
import { EmptyState, ReportGridSkeleton, TypeGlyph } from '../components/ui';
import { AlertaPrioritaria } from '../components/AlertaPrioritaria';
import { TableroPortada } from '../components/TableroPortada';
import { EncharcamientosVigentes } from '../components/EncharcamientosVigentes';
import { vigentesOrdenados } from '../utils/vigencia';
import { BuscadorCalle, type CalleSugerida } from '../components/BuscadorCalle';
import type { Colonia, ReporteResumenPublico, ReportePublico, RespuestaPaginada, TipoDano, EstadoReporte } from '../types/api';

const MapaReportes = lazy(() => import('../components/MapaReportes').then((m) => ({ default: m.MapaReportes })));

const tipos: TipoDano[] = ['Bache', 'Alcantarilla sin tapa', 'Encharcamiento'];
const estados: EstadoReporte[] = ['Recibido', 'Validado', 'Programado', 'En reparación', 'Reparado', 'Activo', 'Histórico'];

/** Filtros de HU-04.2 como query string: los comparten la lista, el mapa y la exportación (HU-04.5, HU-07.3). */
function paramsFiltros(f: Filtros): URLSearchParams {
  const params = new URLSearchParams();
  if (f.busqueda.trim().length >= 3 && !PATRON_FOLIO.test(f.busqueda.trim())) params.set('calle', f.busqueda.trim());
  if (f.tipo) params.set('tipo_dano', f.tipo);
  if (f.estado) params.set('estado', f.estado);
  if (f.colonia) params.set('colonia_id', f.colonia);
  if (f.desde) params.set('desde', f.desde);
  if (f.hasta) params.set('hasta', f.hasta);
  return params;
}

/** Clave de la consulta: un folio exacto o la URL de la lista con todos los filtros combinados (HU-04.2). */
function claveDeConsulta(f: Filtros, pagina: number): string {
  const folio = f.busqueda.trim().match(PATRON_FOLIO)?.[0];
  if (folio) return `folio:${folio.toUpperCase()}`;
  const params = new URLSearchParams({ pagina: String(pagina), por_pagina: '20' });
  if (f.busqueda.trim().length >= 3) params.set('calle', f.busqueda.trim());
  if (f.tipo) params.set('tipo_dano', f.tipo);
  if (f.estado) params.set('estado', f.estado);
  if (f.colonia) params.set('colonia_id', f.colonia);
  if (f.desde) params.set('desde', f.desde);
  if (f.hasta) params.set('hasta', f.hasta);
  return `/api/v1/reportes?${params}`;
}

type RespuestaConsulta = RespuestaPaginada<ReporteResumenPublico> & { sincronizado_en?: string };

/** Consulta pública con respaldo local: sin conexión muestra la última consulta guardada y su fecha de sincronización (HU-08.4). */
async function cargarReportes(claveConRecarga: string): Promise<RespuestaConsulta> {
  const clave = claveConRecarga.split('#')[0];
  try {
    const datos = await consultar(clave);
    guardarConsulta(clave, datos);
    return datos;
  } catch (e) {
    const guardado = e instanceof ApiError && e.status === 0 ? leerConsulta<RespuestaPaginada<ReporteResumenPublico>>(clave) : null;
    if (guardado) return { ...guardado.datos, sincronizado_en: guardado.sincronizado_en };
    throw e;
  }
}

async function consultar(clave: string): Promise<RespuestaPaginada<ReporteResumenPublico>> {
  if (!clave.startsWith('folio:')) return api.get<RespuestaPaginada<ReporteResumenPublico>>(clave);
  const d = await api.get<ReportePublico>(`/api/v1/reportes/${clave.slice('folio:'.length)}`);
  const nivel = 'nivel_agua' in d.detalle ? d.detalle.nivel_agua : null;
  return {
    datos: [{ folio: d.folio, tipo_dano: d.tipo_dano, estado: d.estado, etiqueta_publica: d.etiqueta_publica, severidad: d.severidad, ubicacion: d.ubicacion, calle: d.calle, colonia: d.colonia, created_at: d.created_at, longevidad_dias: d.longevidad_dias, vigencia: d.vigencia, nivel_agua: nivel }],
    paginacion: { pagina: 1, por_pagina: 1, total: 1, total_paginas: 1 },
  };
}

const cargarCatalogo = () => cargarColonias();

/** HU-03.2: encharcamientos activos para la portada (se mezclan con los eventos en vivo de HU-08.3). */
const RUTA_VIGENTES = '/api/v1/reportes?tipo_dano=Encharcamiento&estado=Activo&por_pagina=50&orden=recientes';
const FILTRO_VIGENTES: Filtros = { ...SIN_FILTROS, tipo: 'Encharcamiento', estado: 'Activo' };

export function PublicHomePage() {
  // /?colonia=ID (enlace desde /resumen-colonia) abre la consulta ya filtrada.
  const coloniaUrl = new URLSearchParams(window.location.search).get('colonia') ?? '';
  const [borrador, setBorrador] = useState<Filtros>({ ...SIN_FILTROS, colonia: coloniaUrl }); // lo que se está escribiendo
  const [aplicados, setAplicados] = useState<Filtros>({ ...SIN_FILTROS, colonia: coloniaUrl }); // lo que se consultó
  const [pagina, setPagina] = useState(1);
  const [vista, setVista] = useState<'lista' | 'mapa'>('lista');
  const [exportando, setExportando] = useState<'csv' | 'xml' | null>(null);
  const [errorExportar, setErrorExportar] = useState('');
  const { usuario, autenticado } = useAuth();
  const puedeExportar = usuario?.rol === 'moderador' || usuario?.rol === 'coordinador';
  const { reconexiones } = useEnLinea();
  const enVivo = useEncharcamientosEnVivo(true);
  const consulta = useCargaDatos(`${claveDeConsulta(aplicados, pagina)}#${reconexiones}`, cargarReportes, 'No fue posible cargar los reportes.');
  const catalogo = useCargaDatos('colonias', cargarCatalogo, 'No pudimos cargar las colonias.');
  const base = consulta.datos?.datos;
  // HU-08.3: los eventos en vivo se mezclan sin duplicar folios y respetando los filtros activos.
  const reportes = useMemo(() => fusionarEnVivo(base ?? [], enVivo.vivos, aplicados, pagina === 1, 20), [base, enVivo.vivos, aplicados, pagina]);
  const totalPaginas = consulta.datos?.paginacion.total_paginas || 1;
  const cargando = consulta.estado === 'cargando';
  const error = consulta.estado === 'error' ? consulta.error : '';
  const hayFiltros = Object.values(aplicados).some((valor) => valor.trim() !== '');
  const hayBorrador = Object.values(borrador).some((valor) => valor.trim() !== '');
  // Portada: reporte seleccionado (mapa ↔ encharcamientos), reloj para la vigencia de 6 h y encharcamientos vigentes.
  const [seleccionado, setSeleccionado] = useState<string | null>(null);
  const [ahora, setAhora] = useState(() => Date.now());
  useEffect(() => { const reloj = window.setInterval(() => setAhora(Date.now()), 60_000); return () => window.clearInterval(reloj); }, []);
  const [intentoVigentes, setIntentoVigentes] = useState(0);
  const encharcamientos = useCargaDatos<RespuestaPaginada<ReporteResumenPublico>>(`${RUTA_VIGENTES}#${reconexiones}-${intentoVigentes}`, obtenerJson, 'No fue posible cargar los encharcamientos vigentes.');
  const vigentes = useMemo(() => vigentesOrdenados(fusionarEnVivo(encharcamientos.datos?.datos ?? [], enVivo.vivos, FILTRO_VIGENTES, true), ahora), [encharcamientos.datos, enVivo.vivos, ahora]);
  const estadoVigentes = encharcamientos.estado === 'error' ? 'error' : encharcamientos.estado === 'listo' ? 'listo' : 'cargando';

  const aplicar = (siguientes: Filtros) => { setAplicados(siguientes); setPagina(1); };

  // Búsqueda en vivo (HU-04.2): al escribir se consulta sola con debounce de 450 ms para no saturar la API.
  // Sólo textos que la API entiende: vacío, folio exacto o calle de 3+ letras (un número suelto es un C.P. y va a las sugerencias).
  const textoBuscado = borrador.busqueda.trim();
  useEffect(() => {
    if (textoBuscado === aplicados.busqueda.trim()) return;
    const valida = textoBuscado === '' || PATRON_FOLIO.test(textoBuscado) || (textoBuscado.length >= 3 && !/^\d+$/.test(textoBuscado));
    if (!valida) return;
    const espera = window.setTimeout(() => { setAplicados((actual) => ({ ...actual, busqueda: textoBuscado })); setPagina(1); }, 450);
    return () => window.clearTimeout(espera);
  }, [textoBuscado, aplicados.busqueda]);

  const colonias = useMemo(() => catalogo.datos ?? [], [catalogo.datos]);
  // Calles con reportes que coinciden con lo escrito (de la consulta en vivo ya resuelta).
  const callesSugeridas = useMemo<CalleSugerida[]>(() => {
    if (textoBuscado.length < 3 || aplicados.busqueda.trim().toLowerCase() !== textoBuscado.toLowerCase()) return [];
    const vistas = new Set<string>();
    return (base ?? []).filter((r) => { const clave = `${r.calle}|${r.colonia.nombre}`; if (vistas.has(clave)) return false; vistas.add(clave); return true; })
      .map((r) => ({ calle: r.calle, colonia: r.colonia.nombre }));
  }, [base, textoBuscado, aplicados.busqueda]);
  // Sin resultados: si lo buscado es una colonia o un C.P., se proponen como filtro.
  const coloniasSinResultados = useMemo(() => (aplicados.busqueda.trim() ? filtrarColonias(colonias, aplicados.busqueda, 4) : []), [colonias, aplicados.busqueda]);
  const irAResultados = () => document.getElementById('reportes-titulo')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
  /** Elegir una colonia (por nombre o C.P.) aplica el filtro real de colonia y limpia el texto. */
  const elegirColonia = useCallback((c: Colonia) => {
    const siguientes = { ...borrador, busqueda: '', colonia: String(c.id) };
    setBorrador(siguientes); setAplicados(siguientes); setPagina(1); irAResultados();
  }, [borrador]);
  const elegirCalle = useCallback((calle: string) => {
    const siguientes = { ...borrador, busqueda: calle };
    setBorrador(siguientes); setAplicados(siguientes); setPagina(1); irAResultados();
  }, [borrador]);
  /** Listas y fechas filtran al cambiar (con la calle escrita); la calle o el folio, al pulsar «Buscar». */
  const cambiar = (campo: keyof Filtros, valor: string) => {
    setBorrador((actual) => ({ ...actual, [campo]: valor }));
    if (campo !== 'busqueda') aplicar({ ...borrador, [campo]: valor });
  };
  const exportar = async (formato: 'csv' | 'xml') => {
    setExportando(formato); setErrorExportar('');
    try { await descargarArchivo(`/api/v1/reportes/exportar/${formato}?${paramsFiltros(aplicados)}`, `reportes.${formato}`); }
    catch (e) { setErrorExportar(e instanceof ApiError ? e.message : 'No fue posible exportar los reportes.'); }
    finally { setExportando(null); }
  };
  const buscar = (evento: FormEvent) => { evento.preventDefault(); aplicar(borrador); };
  /** Buscador de la portada: aplica la misma búsqueda de calle/folio (HU-04.2) y lleva a los resultados. */
  const consultarCalle = useCallback(() => {
    // Un C.P. de 5 dígitos con una sola colonia se resuelve como filtro de colonia; si hay varias, se eligen en las sugerencias.
    if (/^\d{5}$/.test(textoBuscado)) {
      const conCp = colonias.filter((c) => c.codigo_postal === textoBuscado);
      if (conCp.length === 1) { elegirColonia(conCp[0]); return; }
      if (conCp.length > 1) return;
    }
    setAplicados(borrador); setPagina(1);
    irAResultados();
  }, [textoBuscado, colonias, elegirColonia, borrador]);
  const limpiar = () => { setBorrador(SIN_FILTROS); aplicar(SIN_FILTROS); };

  return (
    <main className="public-page">
      <section className="portada" aria-labelledby="portada-titulo">
        <div className="portada__texto">
          <h1 id="portada-titulo" className="reveal">Antes de salir, <em>lee la calle.</em></h1>
          <p className="portada__entrada reveal reveal--2">Baches, alcantarillas sin tapa y encharcamientos reportados por vecinos de Ciudad Juárez, con su estado de reparación al minuto. Nunca mostramos datos de quien reporta.</p>

          <BuscadorCalle valor={borrador.busqueda} onCambiar={(texto) => cambiar('busqueda', texto)} onEnviar={consultarCalle} colonias={colonias} calles={callesSugeridas} onElegirColonia={elegirColonia} onElegirCalle={elegirCalle} />

          <AlertaPrioritaria vigentes={vigentes} estado={estadoVigentes} ahora={ahora} onSeleccionar={setSeleccionado} />
        </div>

        <TableroPortada filtros={paramsFiltros(aplicados).toString()} filtrosLista={aplicados} vivos={enVivo.vivos} seleccionado={seleccionado} onSeleccionar={setSeleccionado} />
      </section>

      <EncharcamientosVigentes vigentes={vigentes} estado={estadoVigentes} error={encharcamientos.error} autenticado={autenticado} ahora={ahora} seleccionado={seleccionado} onSeleccionar={setSeleccionado} onReintentar={() => setIntentoVigentes((n) => n + 1)} />

      <section className="reports-section" aria-labelledby="reportes-titulo">
        <div className="section-heading">
          <div>
            <h2 id="reportes-titulo">Reportes recientes</h2>
            <p className="section-heading__sub">Busca por calle o folio y combina filtros de tipo, estado, colonia y fechas.</p>
          </div>
          <ul className="legend" aria-label="Simbología">
            <li className="legend__item legend__item--road"><TypeGlyph tipo="Bache" size={18} />Bache</li>
            <li className="legend__item legend__item--manhole"><TypeGlyph tipo="Alcantarilla sin tapa" size={18} />Alcantarilla</li>
            <li className="legend__item legend__item--water"><TypeGlyph tipo="Encharcamiento" size={18} />Encharcamiento</li>
          </ul>
        </div>

        <section className="filter-bar" aria-labelledby="filtros-titulo">
          <h3 id="filtros-titulo" className="visually-hidden">Buscar reportes</h3>
          <form className="filters" onSubmit={buscar}>
            <div className="field field--search">
              <label htmlFor="busqueda">Calle o folio</label>
              <div className="input-icon"><Icon name="search" size={18} /><input id="busqueda" placeholder="Ej. Tecnológico o BCH-2026-000418" value={borrador.busqueda} onChange={(e) => cambiar('busqueda', e.target.value)} aria-describedby="busqueda-ayuda" /></div>
              <p id="busqueda-ayuda" className="visually-hidden">Escribe al menos 3 letras de la calle, o el folio completo.</p>
            </div>
            <div className="field">
              <label htmlFor="tipo">Tipo de daño</label>
              <select id="tipo" value={borrador.tipo} onChange={(e) => cambiar('tipo', e.target.value)}><option value="">Todos</option>{tipos.map((t) => <option key={t}>{t}</option>)}</select>
            </div>
            <div className="field">
              <label htmlFor="estado">Estado</label>
              <select id="estado" value={borrador.estado} onChange={(e) => cambiar('estado', e.target.value)}><option value="">Todos</option>{estados.map((e) => <option key={e}>{e}</option>)}</select>
            </div>
            <button className="button button--primary" type="submit"><Icon name="search" size={18} />Buscar</button>
            <div className="field">
              <label htmlFor="colonia-filtro">Colonia</label>
              <select id="colonia-filtro" value={borrador.colonia} onChange={(e) => cambiar('colonia', e.target.value)} disabled={catalogo.estado !== 'listo'} aria-describedby={catalogo.estado === 'error' ? 'colonia-filtro-error' : undefined}>
                <option value="">{catalogo.estado === 'cargando' ? 'Cargando colonias…' : 'Todas'}</option>
                {agruparPorSector(catalogo.datos ?? []).map(([sector, lista]) => <optgroup key={sector} label={sector}>{lista.map((c) => <option key={c.id} value={c.id}>{etiquetaColonia(c)}</option>)}</optgroup>)}
              </select>
              {catalogo.estado === 'error' && <p id="colonia-filtro-error" className="field-help">{catalogo.error}</p>}
            </div>
            <div className="field">
              <label htmlFor="desde">Desde</label>
              <input id="desde" type="date" value={borrador.desde} max={borrador.hasta || undefined} onChange={(e) => cambiar('desde', e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="hasta">Hasta</label>
              <input id="hasta" type="date" value={borrador.hasta} min={borrador.desde || undefined} onChange={(e) => cambiar('hasta', e.target.value)} />
            </div>
            <button className="button button--secondary" type="button" onClick={limpiar} disabled={!hayFiltros && !hayBorrador}><Icon name="close" size={18} />Limpiar filtros</button>
          </form>
        </section>

        <p className={`live-status live-status--${enVivo.estado}`} role="status"><span className="live-status__dot" aria-hidden="true" /><Icon name={enVivo.estado === 'en_vivo' ? 'rain' : 'clock'} size={16} />{enVivo.estado === 'en_vivo' ? 'En vivo' : enVivo.estado === 'reconectando' ? 'Reconectando' : 'Conectando'}<span className="live-status__hint"> · encharcamientos nuevos sin recargar la página</span></p>
        {consulta.datos?.sincronizado_en && <div className="notice notice--warning" role="status"><Icon name="alert" size={20} /><div><strong>Sin conexión.</strong> Estás viendo la última consulta guardada el {fechaHora(consulta.datos.sincronizado_en)}. Se actualizará al volver la red.</div></div>}
        <div className="view-toolbar">
          <div className="view-toggle" role="group" aria-label="Forma de ver los reportes">
            <button type="button" className={`button button--sm ${vista === 'lista' ? '' : 'button--secondary'}`} aria-pressed={vista === 'lista'} onClick={() => setVista('lista')}><Icon name="list" size={18} />Lista</button>
            <button type="button" className={`button button--sm ${vista === 'mapa' ? '' : 'button--secondary'}`} aria-pressed={vista === 'mapa'} onClick={() => setVista('mapa')}><Icon name="map" size={18} />Mapa</button>
          </div>
          {puedeExportar && (
            <div className="export-actions" role="group" aria-label="Exportar los reportes filtrados">
              <button type="button" className="button button--secondary button--sm" disabled={exportando !== null} onClick={() => void exportar('csv')}><Icon name="download" size={18} />{exportando === 'csv' ? 'Exportando…' : 'Exportar CSV'}</button>
              <button type="button" className="button button--secondary button--sm" disabled={exportando !== null} onClick={() => void exportar('xml')}><Icon name="download" size={18} />{exportando === 'xml' ? 'Exportando…' : 'Exportar XML'}</button>
            </div>
          )}
        </div>
        {errorExportar && <div className="form-error" role="alert">{errorExportar}</div>}

        {vista === 'mapa' ? <Suspense fallback={<div className="map-state" role="status"><span className="spinner" aria-hidden="true" />Cargando mapa…</div>}><MapaReportes filtros={paramsFiltros(aplicados).toString()} onVerLista={() => setVista('lista')} vivos={enVivo.vivos} filtrosLista={aplicados} /></Suspense> : <>
        {cargando ? <ReportGridSkeleton count={6} /> : error ? <div className="form-error" role="alert">{error}</div> : reportes.length === 0
          ? <EmptyState art="search" title="No hay reportes que coincidan con tus filtros" action={<>
              {coloniasSinResultados.length > 0 && (
                <div className="sugerencias-vacio">
                  <p>¿Buscabas una colonia? Filtra por ella:</p>
                  <ul>{coloniasSinResultados.map((c) => <li key={c.id}><button className="pill" type="button" onClick={() => elegirColonia(c)}><Icon name="pin" size={16} />{etiquetaColonia(c)}</button></li>)}</ul>
                </div>
              )}
              <a className="button button--primary" href="/reportar"><Icon name="plus" size={18} />Reportar un daño</a>
            </>}>{hayFiltros ? 'Prueba con otra calle, otra colonia u otras fechas, o usa «Limpiar filtros».' : 'Aún no hay reportes públicos. Sé la primera persona en reportar un daño.'}</EmptyState>
          : <ListaConTusColonias reportes={reportes} />}
        <Pagination page={pagina} total={totalPaginas} onChange={setPagina} label="Paginación de reportes" />
        </>}
      </section>
    </main>
  );
}

/** HU-01.4: con colonias de interés, primero «Tus colonias» y después el resto de la ciudad (nada se oculta). */
function ListaConTusColonias({ reportes }: { reportes: ReporteResumenPublico[] }) {
  const tuyas = reportes.filter((r) => r.en_tus_colonias);
  if (tuyas.length === 0 || tuyas.length === reportes.length && !reportes.some((r) => r.en_tus_colonias === false)) {
    return <div className="report-grid">{reportes.map((r) => <ReportCard key={r.folio} reporte={r} />)}</div>;
  }
  const resto = reportes.filter((r) => !r.en_tus_colonias);
  return (
    <>
      <section aria-labelledby="tus-colonias-titulo" className="tus-colonias">
        <div className="tus-colonias__head">
          <h3 id="tus-colonias-titulo"><Icon name="star" size={18} />Tus colonias</h3>
          {resto.length > 0 && <a className="link-button" href="#resto-titulo">Ver el resto de la ciudad ({resto.length})</a>}
          <a className="link-button" href="/perfil">Editar mis colonias</a>
        </div>
        <div className="report-grid">{tuyas.map((r) => <ReportCard key={r.folio} reporte={r} />)}</div>
      </section>
      {resto.length > 0 && (
        <section aria-labelledby="resto-titulo">
          <h3 id="resto-titulo" className="tus-colonias__resto">Resto de la ciudad</h3>
          <div className="report-grid">{resto.map((r) => <ReportCard key={r.folio} reporte={r} />)}</div>
        </section>
      )}
    </>
  );
}
