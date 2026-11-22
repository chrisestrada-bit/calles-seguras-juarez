import { useEffect, useState, type FormEvent } from 'react';
import { api, ApiError } from '../services/api';
import { ReportCard } from '../components/ReportCard';
import { ZoneSection } from '../components/ZoneSection';
import { Pagination } from '../components/AdminShared';
import { Icon } from '../components/Icon';
import { EmptyState, ReportGridSkeleton, TypeGlyph } from '../components/ui';
import { HeroMap } from '../components/HeroMap';
import type { ReporteResumenPublico, ReportePublico, RespuestaPaginada, TipoDano, EstadoReporte } from '../types/api';

const tipos: TipoDano[] = ['Bache', 'Alcantarilla sin tapa', 'Encharcamiento'];
const estados: EstadoReporte[] = ['Recibido', 'Validado', 'Programado', 'En reparación', 'Reparado', 'Activo', 'Histórico'];

export function PublicHomePage() {
  const [reportes, setReportes] = useState<ReporteResumenPublico[]>([]); const [busqueda, setBusqueda] = useState(''); const [tipo, setTipo] = useState(''); const [estado, setEstado] = useState(''); const [pagina, setPagina] = useState(1); const [totalPaginas, setTotalPaginas] = useState(1); const [cargando, setCargando] = useState(true); const [error, setError] = useState('');
  const cargar = async (evento?: FormEvent) => { evento?.preventDefault(); setCargando(true); setError(''); try { const folio = busqueda.trim().match(/^(BCH|ENC)-\d{4}-\d{6}$/i)?.[0]; if (folio) { const detalle = await api.get<ReportePublico>(`/api/v1/reportes/${folio}`); setReportes([{ folio: detalle.folio, tipo_dano: detalle.tipo_dano, estado: detalle.estado, etiqueta_publica: detalle.etiqueta_publica, severidad: detalle.severidad, ubicacion: detalle.ubicacion, calle: detalle.calle, colonia: detalle.colonia, created_at: detalle.created_at, longevidad_dias: detalle.longevidad_dias, vigencia: detalle.vigencia }]); setTotalPaginas(1); return; } const params = new URLSearchParams({ pagina: String(pagina), por_pagina: '20' }); if (busqueda.trim()) params.set('calle', busqueda.trim()); if (tipo) params.set('tipo_dano', tipo); if (estado) params.set('estado', estado); const respuesta = await api.get<RespuestaPaginada<ReporteResumenPublico>>(`/api/v1/reportes?${params}`); setReportes(respuesta.datos); setTotalPaginas(respuesta.paginacion.total_paginas || 1); } catch (e) { setError(e instanceof ApiError ? e.message : 'No fue posible cargar los reportes.'); } finally { setCargando(false); } };
  useEffect(() => { void cargar(); }, [pagina, tipo, estado]);
  const buscar = (evento: FormEvent) => { evento.preventDefault(); setPagina(1); void cargar(evento); };
  const filtrados = busqueda.trim() ? reportes.filter((r) => `${r.folio} ${r.calle}`.toLocaleLowerCase().includes(busqueda.toLocaleLowerCase())) : reportes;
  const hayFiltros = Boolean(busqueda.trim() || tipo || estado);

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
            <p className="section-heading__sub">Busca por calle o folio y filtra por tipo o estado.</p>
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
              <div className="input-icon"><Icon name="search" size={18} /><input id="busqueda" placeholder="Ej. Tecnológico o BCH-2026-000418" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} /></div>
            </div>
            <div className="field">
              <label htmlFor="tipo">Tipo de daño</label>
              <select id="tipo" value={tipo} onChange={(e) => { setTipo(e.target.value); setPagina(1); }}><option value="">Todos</option>{tipos.map((t) => <option key={t}>{t}</option>)}</select>
            </div>
            <div className="field">
              <label htmlFor="estado">Estado</label>
              <select id="estado" value={estado} onChange={(e) => { setEstado(e.target.value); setPagina(1); }}><option value="">Todos</option>{estados.map((e) => <option key={e}>{e}</option>)}</select>
            </div>
            <button className="button button--primary" type="submit"><Icon name="search" size={18} />Buscar</button>
          </form>
        </section>

        {cargando ? <ReportGridSkeleton count={6} /> : error ? <div className="form-error" role="alert">{error}</div> : filtrados.length === 0
          ? <EmptyState art="search" title="No hay reportes que coincidan con tus filtros" action={<a className="button button--primary" href="/reportar"><Icon name="plus" size={18} />Reportar un daño</a>}>{hayFiltros ? 'Prueba con otra calle, otro tipo de daño o quita el filtro de estado.' : 'Aún no hay reportes públicos. Sé la primera persona en reportar un daño.'}</EmptyState>
          : <div className="report-grid">{filtrados.map((r) => <ReportCard key={r.folio} reporte={r} />)}</div>}
        <Pagination page={pagina} total={totalPaginas} onChange={setPagina} label="Paginación de reportes" />
      </section>
    </main>
  );
}
