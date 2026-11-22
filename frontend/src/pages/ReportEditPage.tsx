import { useState, type FormEvent } from 'react';
import { useAuth } from '../context/useAuth';
import { api, ApiError } from '../services/api';
import { agruparPorSector, cargarColonias, etiquetaColonia } from '../services/catalogos';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { Icon } from '../components/Icon';
import { BlockSkeleton, EmptyState, TypeBadge } from '../components/ui';
import type { CarrilAfectado, Colonia, EditarReporteRequest, Profundidad, ReportePublico, Tamano } from '../types/api';

const TAMANOS: Tamano[] = ['chico', 'mediano', 'grande'];
const PROFUNDIDADES: Profundidad[] = ['menos de 5 cm', '5 a 10 cm', 'más de 10 cm'];
const CARRILES: CarrilAfectado[] = ['carril derecho', 'carril central', 'carril izquierdo', 'varios carriles', 'acotamiento'];
const cargarCatalogo = () => cargarColonias();

function Aviso({ titulo, children }: { titulo: string; children: string }) {
  return <main className="report-page"><EmptyState art="inbox" title={titulo} action={<a className="button button--primary" href="/mis-reportes"><Icon name="arrowLeft" size={18} />Volver a mis reportes</a>}>{children}</EmptyState></main>;
}

function FormularioEdicion({ reporte, colonias }: { reporte: ReportePublico; colonias: Colonia[] }) {
  const detalle = reporte.detalle;
  const [coloniaId, setColoniaId] = useState(String(reporte.colonia.id));
  const [calle, setCalle] = useState(reporte.calle);
  const [referencia, setReferencia] = useState(reporte.referencia ?? '');
  const [descripcion, setDescripcion] = useState(reporte.descripcion ?? '');
  const [tamano, setTamano] = useState('tamano' in detalle ? detalle.tamano : '');
  const [profundidad, setProfundidad] = useState('profundidad' in detalle ? detalle.profundidad : '');
  const [carril, setCarril] = useState('carril_afectado' in detalle ? detalle.carril_afectado : '');
  const [senalizado, setSenalizado] = useState('esta_senalizado' in detalle ? (detalle.esta_senalizado ? 'si' : 'no') : '');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState('');
  const [guardado, setGuardado] = useState(false);

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault(); setError(''); setGuardado(false);
    if (calle.trim().length < 3) { setError('La calle debe tener al menos 3 caracteres.'); return; }
    const cambios: EditarReporteRequest = { colonia_id: Number(coloniaId), calle: calle.trim(), referencia: referencia.trim() || null, descripcion: descripcion.trim() || null };
    if (reporte.tipo_dano === 'Bache') Object.assign(cambios, { tamano, profundidad, carril_afectado: carril });
    if (reporte.tipo_dano === 'Alcantarilla sin tapa') cambios.esta_senalizado = senalizado === 'si';
    setEnviando(true);
    try { await api.patch<ReportePublico>(`/api/v1/reportes/${encodeURIComponent(reporte.folio)}`, cambios); setGuardado(true); }
    catch (e) { setError(e instanceof ApiError ? e.message : 'No fue posible guardar los cambios.'); }
    finally { setEnviando(false); }
  };

  return (
    <main className="report-page">
      <a className="back-link" href="/mis-reportes"><Icon name="arrowLeft" size={16} />Volver a mis reportes</a>
      <section className="report-intro"><h1>Editar reporte <span className="tabular">{reporte.folio}</span></h1><p>Puedes corregir tu reporte mientras está sin validar. El folio, el tipo de daño, la ubicación y la fecha original no cambian.</p></section>
      {error && <div className="form-error" role="alert">{error}</div>}
      {guardado && <div className="form-success" role="status">Cambios guardados. <a href={`/reportes/${encodeURIComponent(reporte.folio)}`}>Ver reporte</a></div>}
      <form onSubmit={enviar}>
        <fieldset className="report-section" disabled={enviando}>
          <legend>Datos del reporte</legend>
          <p><TypeBadge tipo={reporte.tipo_dano} /></p>
          <p className="location-readout"><Icon name="pin" size={18} /><span>Punto: {reporte.ubicacion.latitud.toFixed(6)}, {reporte.ubicacion.longitud.toFixed(6)} (no se puede cambiar).</span></p>
          <label htmlFor="colonia-edicion">Colonia <span aria-hidden="true">*</span></label>
          <select id="colonia-edicion" value={coloniaId} onChange={(e) => setColoniaId(e.target.value)} required>
            {!colonias.some((c) => String(c.id) === coloniaId) && <option value={coloniaId}>{reporte.colonia.nombre}</option>}
            {agruparPorSector(colonias).map(([sector, lista]) => <optgroup key={sector} label={sector}>{lista.map((c) => <option key={c.id} value={c.id}>{etiquetaColonia(c)}</option>)}</optgroup>)}
          </select>
          <label htmlFor="calle-edicion">Calle <span aria-hidden="true">*</span></label>
          <input id="calle-edicion" value={calle} onChange={(e) => setCalle(e.target.value)} minLength={3} maxLength={150} required />
          {reporte.tipo_dano === 'Bache' && <div className="field-grid">
            <label htmlFor="tamano-edicion">Tamaño<select id="tamano-edicion" value={tamano} onChange={(e) => setTamano(e.target.value as Tamano)} required>{TAMANOS.map((t) => <option key={t}>{t}</option>)}</select></label>
            <label htmlFor="profundidad-edicion">Profundidad<select id="profundidad-edicion" value={profundidad} onChange={(e) => setProfundidad(e.target.value as Profundidad)} required>{PROFUNDIDADES.map((t) => <option key={t}>{t}</option>)}</select></label>
            <label htmlFor="carril-edicion">Carril afectado<select id="carril-edicion" value={carril} onChange={(e) => setCarril(e.target.value as CarrilAfectado)} required>{CARRILES.map((t) => <option key={t}>{t}</option>)}</select></label>
          </div>}
          {reporte.tipo_dano === 'Alcantarilla sin tapa' && <div className="radio-question" role="radiogroup" aria-labelledby="senalizado-edicion-titulo"><span id="senalizado-edicion-titulo">¿Está señalizada?</span><span className="radio-options"><label><input type="radio" name="senalizado-edicion" value="si" checked={senalizado === 'si'} onChange={(e) => setSenalizado(e.target.value)} required /> Sí</label><label><input type="radio" name="senalizado-edicion" value="no" checked={senalizado === 'no'} onChange={(e) => setSenalizado(e.target.value)} /> No</label></span></div>}
          <label htmlFor="referencia-edicion">Referencia <span className="field-help">(opcional)</span></label>
          <input id="referencia-edicion" value={referencia} onChange={(e) => setReferencia(e.target.value)} maxLength={200} />
          <label htmlFor="descripcion-edicion">Descripción <span className="field-help">(opcional, máximo 500 caracteres)</span></label>
          <textarea id="descripcion-edicion" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} maxLength={500} rows={4} aria-describedby="descripcion-edicion-conteo" />
          <p id="descripcion-edicion-conteo" className="character-count">{descripcion.length}/500</p>
          <button className="button button--primary button--full button--lg" type="submit">{enviando ? 'Guardando…' : 'Guardar cambios'}</button>
        </fieldset>
      </form>
    </main>
  );
}

export function ReportEditPage({ folio }: { folio: string }) {
  const { autenticado } = useAuth();
  const reporte = useCargaDatos<ReportePublico>(autenticado ? `/api/v1/reportes/${encodeURIComponent(folio)}` : null, obtenerJson, 'No encontramos ese reporte.');
  const catalogo = useCargaDatos(autenticado ? 'colonias' : null, cargarCatalogo, 'No pudimos cargar las colonias.');

  if (!autenticado) return <main className="report-page"><section className="auth-card auth-card--center"><span className="auth-card__icon"><Icon name="edit" size={28} /></span><h1>Editar reporte</h1><p>Inicia sesión para editar tus reportes.</p><a className="button button--primary" href="/login">Iniciar sesión</a></section></main>;
  if (reporte.estado === 'cargando' || catalogo.estado === 'cargando') return <main className="report-page"><div className="report-section"><BlockSkeleton label="Cargando reporte…" lines={5} /></div></main>;
  if (reporte.estado === 'error' || !reporte.datos) return <Aviso titulo="Reporte no disponible">{reporte.error || 'No encontramos ese reporte.'}</Aviso>;
  if (!reporte.datos.es_mio) return <Aviso titulo="No puedes editar este reporte">Sólo la persona que creó un reporte puede editarlo.</Aviso>;
  if (reporte.datos.estado !== 'Recibido') return <Aviso titulo="Este reporte ya no se puede editar">La edición sólo está disponible mientras el reporte está sin validar (estado Recibido). Los reportes se conservan por trazabilidad.</Aviso>;
  return <FormularioEdicion key={folio} reporte={reporte.datos} colonias={catalogo.datos ?? []} />;
}
