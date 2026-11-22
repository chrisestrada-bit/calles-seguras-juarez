import { useState, type FormEvent } from 'react';
import { api } from '../services/api';
import { agruparPorSector, cargarColonias, etiquetaColonia } from '../services/catalogos';
import { useCargaDatos } from '../hooks/useCargaDatos';
import { ReportCard } from '../components/ReportCard';
import { ZoneSection } from '../components/ZoneSection';
import { Pagination } from '../components/AdminShared';
import { Icon } from '../components/Icon';
import { EmptyState, ReportGridSkeleton, TypeGlyph } from '../components/ui';
import { HeroMap } from '../components/HeroMap';
import type { ReporteResumenPublico, ReportePublico, RespuestaPaginada, TipoDano, EstadoReporte } from '../types/api';

const tipos: TipoDano[] = ['Bache', 'Alcantarilla sin tapa', 'Encharcamiento'];
const estados: EstadoReporte[] = ['Recibido', 'Validado', 'Programado', 'En reparación', 'Reparado', 'Activo', 'Histórico'];
const PATRON_FOLIO = /^(BCH|ENC)-\d{4}-\d{6}$/i;
const SIN_FILTROS = { busqueda: '', tipo: '', estado: '', colonia: '', desde: '', hasta: '' };
type Filtros = typeof SIN_FILTROS;

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

async function cargarReportes(clave: string): Promise<RespuestaPaginada<ReporteResumenPublico>> {
  if (!clave.startsWith('folio:')) return api.get<RespuestaPaginada<ReporteResumenPublico>>(clave);
  const d = await api.get<ReportePublico>(`/api/v1/reportes/${clave.slice('folio:'.length)}`);
  const nivel = 'nivel_agua' in d.detalle ? d.detalle.nivel_agua : null;
  return {
    datos: [{ folio: d.folio, tipo_dano: d.tipo_dano, estado: d.estado, etiqueta_publica: d.etiqueta_publica, severidad: d.severidad, ubicacion: d.ubicacion, calle: d.calle, colonia: d.colonia, created_at: d.created_at, longevidad_dias: d.longevidad_dias, vigencia: d.vigencia, nivel_agua: nivel }],
    paginacion: { pagina: 1, por_pagina: 1, total: 1, total_paginas: 1 },
  };
}

const cargarCatalogo = () => cargarColonias();

export function PublicHomePage() {
  const [borrador, setBorrador] = useState<Filtros>(SIN_FILTROS); // lo que se está escribiendo
  const [aplicados, setAplicados] = useState<Filtros>(SIN_FILTROS); // lo que se consultó
  const [pagina, setPagina] = useState(1);
  const consulta = useCargaDatos(claveDeConsulta(aplicados, pagina), cargarReportes, 'No fue posible cargar los reportes.');
  const catalogo = useCargaDatos('colonias', cargarCatalogo, 'No pudimos cargar las colonias.');
  const reportes = consulta.datos?.datos ?? [];
  const totalPaginas = consulta.datos?.paginacion.total_paginas || 1;
  const cargando = consulta.estado === 'cargando';
  const error = consulta.estado === 'error' ? consulta.error : '';
  const hayFiltros = Object.values(aplicados).some((valor) => valor.trim() !== '');
  const hayBorrador = Object.values(borrador).some((valor) => valor.trim() !== '');

  const aplicar = (siguientes: Filtros) => { setAplicados(siguientes); setPagina(1); };
  /** Listas y fechas filtran al cambiar (con la calle escrita); la calle o el folio, al pulsar «Buscar». */
  const cambiar = (campo: keyof Filtros, valor: string) => {
    setBorrador((actual) => ({ ...actual, [campo]: valor }));
    if (campo !== 'busqueda') aplicar({ ...borrador, [campo]: valor });
  };
  const buscar = (evento: FormEvent) => { evento.preventDefault(); aplicar(borrador); };
  const limpiar = () => { setBorrador(SIN_FILTROS); aplicar(SIN_FILTROS); };

  return (
    <main className="public-page">
      <section className="hero" aria-labelledby="hero-titulo">
        <HeroMap />
        <div className="hero__content">
          <h1 id="hero-titulo" className="reveal">Consulta y reporta el estado de tus calles</h1>
          <p className="hero__lead reveal reveal--2">Encuentra baches y encharcamientos antes de salir. La información pública nunca muestra datos del autor.</p>
          <p className="hero__place reveal reveal--3"><span className="hero__live" aria-hidden="true" />Ciudad Juárez, Chihuahua</p>
          <div className="hero__actions reveal reveal--4">
            <a className="button button--accent button--lg" href="#zona-titulo"><Icon name="locate" size={20} />Revisar mi zona</a>
            <a className="button button--ghost-light button--lg" href="/reportar"><Icon name="plus" size={20} />Reportar un daño</a>
          </div>
        </div>
        <p className="hero__map-note">Mapa ilustrativo de Ciudad Juárez</p>
        <ul className="hero__legend reveal reveal--4" aria-label="Qué puedes reportar">
          <li className="hero__chip hero__chip--road"><TypeGlyph tipo="Bache" size={20} />Bache</li>
          <li className="hero__chip hero__chip--manhole"><TypeGlyph tipo="Alcantarilla sin tapa" size={20} />Alcantarilla sin tapa</li>
          <li className="hero__chip hero__chip--water"><TypeGlyph tipo="Encharcamiento" size={20} />Encharcamiento</li>
        </ul>
      </section>

      <ZoneSection />

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

        {cargando ? <ReportGridSkeleton count={6} /> : error ? <div className="form-error" role="alert">{error}</div> : reportes.length === 0
          ? <EmptyState art="search" title="No hay reportes que coincidan con tus filtros" action={<a className="button button--primary" href="/reportar"><Icon name="plus" size={18} />Reportar un daño</a>}>{hayFiltros ? 'Prueba con otra calle, otra colonia u otras fechas, o usa «Limpiar filtros».' : 'Aún no hay reportes públicos. Sé la primera persona en reportar un daño.'}</EmptyState>
          : <div className="report-grid">{reportes.map((r) => <ReportCard key={r.folio} reporte={r} />)}</div>}
        <Pagination page={pagina} total={totalPaginas} onChange={setPagina} label="Paginación de reportes" />
      </section>
    </main>
  );
}
