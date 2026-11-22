import { useState, type FormEvent } from 'react';
import { useAuth } from '../context/useAuth';
import { api, ApiError } from '../services/api';
import { agruparPorSector, cargarColonias, etiquetaColonia } from '../services/catalogos';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import type {
  CandidatoCercano, CercanosResponse, CrearReporteRequest, GeocodingInversaResponse, GeocodingResponse, GeocodingResultado,
  NivelAgua, ReportePublico, TipoDano, Ubicacion,
} from '../types/api';
import { Icon } from '../components/Icon';
import { TypeGlyph } from '../components/ui';
import { FotoPicker } from '../components/FotoPicker';
import { subirFotos } from '../services/fotos';

const TIPO_TONO: Record<TipoDano, string> = { Bache: 'road', 'Alcantarilla sin tapa': 'manhole', Encharcamiento: 'water' };
const TIPO_AYUDA: Record<TipoDano, string> = { Bache: 'Hoyo o hundimiento en el pavimento', 'Alcantarilla sin tapa': 'Severidad Alta fija', Encharcamiento: 'Agua acumulada en la calle' };

const TIPOS: TipoDano[] = ['Bache', 'Alcantarilla sin tapa', 'Encharcamiento'];
const LIMITES = { latitudMin: 31.45, latitudMax: 31.80, longitudMin: -106.65, longitudMax: -106.25 };
const enJuarez = ({ latitud, longitud }: Ubicacion) => latitud >= LIMITES.latitudMin && latitud <= LIMITES.latitudMax && longitud >= LIMITES.longitudMin && longitud <= LIMITES.longitudMax;

const cargarCatalogo = () => cargarColonias();

function ErrorApiTexto({ error }: { error: unknown }) {
  return <>{error instanceof ApiError ? error.message : 'No fue posible completar la solicitud. Intenta de nuevo.'}</>;
}

export function ReportCreatePage() {
  const { autenticado } = useAuth();
  const [tipo, setTipo] = useState<TipoDano>('Bache');
  const [consulta, setConsulta] = useState('');
  const [resultados, setResultados] = useState<GeocodingResultado[]>([]);
  const [ubicacion, setUbicacion] = useState<Ubicacion | null>(null);
  const [calle, setCalle] = useState('');
  const [coloniaId, setColoniaId] = useState('');
  const [ubicacionEstado, setUbicacionEstado] = useState('');
  const [cargandoUbicacion, setCargandoUbicacion] = useState(false);
  const [forzarNuevo, setForzarNuevo] = useState(false);
  const [detalle, setDetalle] = useState({ tamano: '', profundidad: '', carril_afectado: '', esta_senalizado: '', nivel_agua: '', hay_riesgo_personas_vehiculos: '', referencia: '', descripcion: '' });
  const [error, setError] = useState('');
  const mostrarError = (e: unknown) => setError(e instanceof ApiError ? e.message : 'No fue posible completar la solicitud. Intenta de nuevo.');
  const [exito, setExito] = useState<ReportePublico | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [fotos, setFotos] = useState<File[]>([]); // HU-02.4: se suben justo después de crear o confirmar
  const [avisoFotos, setAvisoFotos] = useState('');

  const catalogo = useCargaDatos(autenticado ? 'colonias' : null, cargarCatalogo, 'No pudimos cargar el catálogo de colonias; recarga la página para intentarlo de nuevo.');
  const colonias = catalogo.datos ?? [];
  // HU-02.3 / HU-03.1: al elegir punto o tipo se revisan duplicados en 30 m (pavimento) o 50 m (encharcamiento).
  const cercanos = useCargaDatos<CercanosResponse>(
    autenticado && ubicacion ? `/api/v1/reportes/cercanos?latitud=${ubicacion.latitud}&longitud=${ubicacion.longitud}&tipo_dano=${encodeURIComponent(tipo)}` : null,
    obtenerJson,
    'No pudimos revisar reportes cercanos.',
  );
  const candidatos: CandidatoCercano[] = cercanos.datos?.candidatos ?? [];
  const radio = cercanos.datos?.radio_metros ?? null;
  const revisandoDuplicados = cercanos.estado === 'cargando';

  /** Cambiar de punto reinicia la decisión sobre duplicados y los errores del envío anterior. */
  const fijarUbicacion = (punto: Ubicacion | null) => { setUbicacion(punto); setForzarNuevo(false); setError(''); };

  if (!autenticado) return <main className="report-page"><section className="auth-card auth-card--center"><span className="auth-card__icon"><Icon name="plus" size={28} /></span><h1>Reportar un daño</h1><p>Inicia sesión para registrar un reporte y darle seguimiento.</p><a className="button button--primary" href="/login">Iniciar sesión</a></section></main>;

  const seleccionarUbicacion = (resultado: GeocodingResultado) => {
    fijarUbicacion(resultado.ubicacion); setCalle(resultado.calle ?? '');
    if (resultado.colonia_sugerida) setColoniaId(String(resultado.colonia_sugerida.id));
    const aproximada = resultado.precision === 'aproximada' || resultado.precision === 'colonia';
    setResultados([]); setUbicacionEstado(aproximada ? 'El punto es el centro aproximado de la colonia. Escribe la calle y, si estás en el lugar del daño, usa tu ubicación GPS para mayor precisión.' : 'Ubicación seleccionada.');
  };

  const buscarDireccion = async (evento: FormEvent) => {
    evento.preventDefault(); setError(''); setUbicacionEstado('');
    if (consulta.trim().length < 3) { setUbicacionEstado('Escribe al menos 3 caracteres para buscar una dirección.'); return; }
    setCargandoUbicacion(true);
    try { const respuesta = await api.get<GeocodingResponse>(`/api/v1/geocoding/buscar?q=${encodeURIComponent(consulta.trim())}&limite=5`); setResultados(respuesta.datos); if (!respuesta.datos.length) setUbicacionEstado(respuesta.mensaje ?? 'No encontramos una dirección dentro de Ciudad Juárez.'); } catch (e) { mostrarError(e); } finally { setCargandoUbicacion(false); }
  };

  const usarGps = () => {
    setError(''); setUbicacionEstado('Solicitando tu ubicación…');
    if (!navigator.geolocation) { setUbicacionEstado('Tu navegador no permite obtener la ubicación. Usa la búsqueda por dirección.'); return; }
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      const punto = { latitud: coords.latitude, longitud: coords.longitude };
      if (!enJuarez(punto)) { fijarUbicacion(null); setUbicacionEstado('La ubicación está fuera de los límites de Ciudad Juárez, Chihuahua. Selecciona un punto dentro del municipio.'); return; }
      fijarUbicacion(punto); setCalle(''); setUbicacionEstado('Ubicación GPS seleccionada. Buscando la calle y la colonia…');
      // Geocodificación inversa (RN-01): sugiere calle y colonia para el punto del GPS.
      api.get<GeocodingInversaResponse>(`/api/v1/geocoding/inversa?latitud=${punto.latitud}&longitud=${punto.longitud}`)
        .then((r) => {
          if (r.calle) setCalle(r.calle);
          if (r.colonia_sugerida) setColoniaId(String(r.colonia_sugerida.id));
          setUbicacionEstado(r.colonia_sugerida ? `Ubicación GPS seleccionada. Colonia sugerida: ${r.colonia_sugerida.nombre}. Confírmala${r.calle ? '' : ' y escribe la calle'}.` : 'Ubicación GPS seleccionada. Elige la colonia correspondiente.');
        })
        .catch(() => setUbicacionEstado('Ubicación GPS seleccionada. Elige la colonia correspondiente.'));
    }, () => setUbicacionEstado('No pudimos obtener tu ubicación. Revisa el permiso del navegador e intenta de nuevo.'));
  };

  const cambiarTipo = (nuevo: TipoDano) => { setTipo(nuevo); fijarUbicacion(null); setResultados([]); setUbicacionEstado('Selecciona nuevamente la ubicación para revisar duplicados.'); };
  const cambiarDetalle = (campo: keyof typeof detalle, valor: string) => setDetalle((actual) => ({ ...actual, [campo]: valor }));

  /** El reporte (o la confirmación) ya quedó guardado: si alguna foto falla se avisa, pero nunca se pierde el reporte. */
  const adjuntarFotos = async (folio: string) => {
    if (fotos.length === 0) return;
    try {
      const r = await subirFotos(folio, fotos);
      setAvisoFotos(r.rechazadas.length ? `${r.mensaje} ${r.rechazadas.map((x) => `${x.nombre}: ${x.motivo}`).join(' ')}` : r.mensaje);
    } catch (e) {
      setAvisoFotos(`Tu reporte se guardó, pero no pudimos adjuntar las fotografías: ${e instanceof ApiError ? e.message : 'intenta de nuevo desde el detalle del reporte.'}`);
    }
  };

  const confirmar = async (candidato: CandidatoCercano) => {
    setError(''); setAvisoFotos('');
    try {
      await api.post(`/api/v1/reportes/${encodeURIComponent(candidato.folio)}/confirmaciones`, { tipo: tipo === 'Encharcamiento' ? 'sigue_ahi' : 'confirmacion_dano' });
      await adjuntarFotos(candidato.folio);
      setExito({ folio: candidato.folio } as ReportePublico);
    } catch (e) { mostrarError(e); }
  };

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault(); setError(''); setExito(null); setAvisoFotos('');
    if (!ubicacion || !enJuarez(ubicacion)) { setError('Selecciona una ubicación dentro de los límites de Ciudad Juárez.'); return; }
    if (!coloniaId) { setError('Selecciona la colonia del reporte.'); return; }
    const base = { tipo_dano: tipo, ...ubicacion, colonia_id: Number(coloniaId), calle: calle.trim(), referencia: detalle.referencia.trim() || undefined, descripcion: detalle.descripcion.trim() || undefined, forzar_nuevo: forzarNuevo };
    let payload: CrearReporteRequest;
    if (tipo === 'Bache') payload = { ...base, tipo_dano: 'Bache', tamano: detalle.tamano as 'chico' | 'mediano' | 'grande', profundidad: detalle.profundidad as never, carril_afectado: detalle.carril_afectado as never };
    else if (tipo === 'Alcantarilla sin tapa') payload = { ...base, tipo_dano: 'Alcantarilla sin tapa', esta_senalizado: detalle.esta_senalizado === 'si' };
    else payload = { ...base, tipo_dano: 'Encharcamiento', nivel_agua: detalle.nivel_agua as NivelAgua, ...(detalle.nivel_agua === 'intransitable' ? { hay_riesgo_personas_vehiculos: detalle.hay_riesgo_personas_vehiculos === 'si' } : {}) };
    setEnviando(true);
    try { const creado = await api.post<ReportePublico>('/api/v1/reportes', payload); await adjuntarFotos(creado.folio); setExito(creado); } catch (e) { mostrarError(e); } finally { setEnviando(false); }
  };

  const hayDuplicados = candidatos.length > 0 && !forzarNuevo;
  return <main className="report-page"><section className="report-intro"><h1>Reportar un daño</h1><p>Ayúdanos a identificar baches, alcantarillas sin tapa y encharcamientos en Ciudad Juárez.</p></section>
    {error && <div className="form-error" role="alert"><ErrorApiTexto error={error} /></div>}
    {exito ? <section className="success-panel" aria-live="polite"><span className="success-panel__icon"><Icon name="checkCircle" size={32} /></span><h2>Reporte registrado</h2><p>Tu folio es <strong>{exito.folio}</strong>. Gracias por ayudar a cuidar nuestras calles.</p>{avisoFotos && <p className="field-help" role="status"><Icon name="camera" size={16} />{avisoFotos}</p>}<a className="button button--primary" href={`/reportes/${encodeURIComponent(exito.folio)}`}>Ver reporte<Icon name="arrowRight" size={18} /></a></section> : <>
      <section className="report-section" aria-labelledby="tipo-titulo"><h2 id="tipo-titulo">1. ¿Qué observaste?</h2><div className="type-options">{TIPOS.map((opcion) => <label className={`type-option${tipo === opcion ? ' type-option--selected' : ''}`} key={opcion}><input type="radio" name="tipo_dano" checked={tipo === opcion} onChange={() => cambiarTipo(opcion)} /><span className={`type-option__icon type-option__icon--${TIPO_TONO[opcion]}`}><TypeGlyph tipo={opcion} size={30} /></span><span className="type-option__text"><span>{opcion}</span><small>{TIPO_AYUDA[opcion]}</small></span></label>)}</div></section>
      <section className="report-section" aria-labelledby="ubicacion-titulo"><h2 id="ubicacion-titulo">2. ¿Dónde está?</h2><form className="location-search" onSubmit={buscarDireccion}><label htmlFor="direccion">Buscar por dirección, calle, cruce o código postal</label><div className="inline-form"><div className="input-icon"><Icon name="search" size={18} /><input id="direccion" value={consulta} onChange={(e) => setConsulta(e.target.value)} placeholder="Ej. Tecnológico y Ejército Nacional o 32310" /></div><button className="button button--primary" disabled={cargandoUbicacion}>{cargandoUbicacion ? 'Buscando…' : 'Buscar'}</button></div></form><button className="button button--secondary" type="button" onClick={usarGps}><Icon name="locate" size={18} />Usar mi ubicación GPS</button>{ubicacion && <p className="location-readout" role="status"><Icon name="pin" size={18} /><span>Punto: {ubicacion.latitud.toFixed(6)}, {ubicacion.longitud.toFixed(6)}. {ubicacionEstado}</span></p>}{ubicacionEstado && !ubicacion && <p className="field-help" role="status">{ubicacionEstado}</p>}{resultados.length > 0 && <ul className="search-results" aria-label="Resultados de dirección">{resultados.map((resultado) => <li key={`${resultado.etiqueta}-${resultado.ubicacion.latitud}`}><button type="button" onClick={() => seleccionarUbicacion(resultado)}><Icon name="pin" size={18} /><strong>{resultado.etiqueta}</strong><span>{resultado.precision}</span></button></li>)}</ul>}<label htmlFor="colonia">Colonia <span aria-hidden="true">*</span></label><select id="colonia" value={coloniaId} onChange={(e) => setColoniaId(e.target.value)} required aria-describedby={catalogo.estado === 'error' ? 'colonia-error' : undefined}><option value="">{catalogo.estado === 'cargando' ? 'Cargando colonias…' : 'Selecciona la colonia'}</option>{agruparPorSector(colonias).map(([sector, lista]) => <optgroup key={sector} label={sector}>{lista.map((colonia) => <option key={colonia.id} value={colonia.id}>{etiquetaColonia(colonia)}</option>)}</optgroup>)}</select>{catalogo.estado === 'error' && <p id="colonia-error" className="field-help" role="alert">{catalogo.error}</p>}<label htmlFor="calle">Calle</label><input id="calle" value={calle} onChange={(e) => setCalle(e.target.value)} minLength={3} maxLength={150} required placeholder="Ej. Avenida Tecnológico" />{revisandoDuplicados && <p className="field-help" role="status">Revisando reportes cercanos…</p>}{cercanos.estado === 'error' && <p className="form-error" role="alert">{cercanos.error}</p>}{cercanos.estado === 'listo' && candidatos.length === 0 && <p className="form-success" role="status">No encontramos reportes abiertos o vigentes en el radio correspondiente.</p>}{candidatos.length > 0 && <div className="duplicate-box" role="alert"><h3><Icon name="alert" size={20} />Encontramos un reporte cercano</h3><p>Hay un reporte a menos de {radio} metros. Puedes confirmarlo o indicar que el daño es distinto.</p>{candidatos.map((candidato) => <article className="duplicate-card" key={candidato.folio}><div><strong>{candidato.folio}</strong><span>{candidato.calle} · {candidato.distancia_metros.toFixed(1)} m</span></div>{candidato.es_mio ? <p className="field-help">Este reporte es tuyo y no puedes confirmarlo.</p> : candidato.ya_confirmado_por_mi ? <p className="field-help">Ya confirmaste este reporte.</p> : <button className="button button--secondary" type="button" onClick={() => void confirmar(candidato)}>Confirmar existente</button>}</article>)}{!forzarNuevo && <div className="duplicate-box__photos"><h4>Si confirmas, puedes adjuntar fotografías</h4><FotoPicker archivos={fotos} onChange={setFotos} /></div>}{!forzarNuevo && <button className="button button--quiet" type="button" onClick={() => setForzarNuevo(true)}>Es un daño distinto, crear reporte nuevo</button>}{forzarNuevo && <p className="field-help">Crearás un reporte nuevo y quedará registrado como daño distinto.</p>}</div>}</section>
      <form onSubmit={enviar}><fieldset className="report-section" disabled={!ubicacion || revisandoDuplicados || hayDuplicados}><legend>3. Detalles del reporte</legend><p className="field-help">No escribas datos personales en la descripción.</p>{tipo === 'Bache' && <div className="field-grid"><label htmlFor="tamano">Tamaño<select id="tamano" value={detalle.tamano} onChange={(e) => cambiarDetalle('tamano', e.target.value)} required><option value="">Selecciona</option><option>chico</option><option>mediano</option><option>grande</option></select></label><label htmlFor="profundidad">Profundidad<select id="profundidad" value={detalle.profundidad} onChange={(e) => cambiarDetalle('profundidad', e.target.value)} required><option value="">Selecciona</option><option>menos de 5 cm</option><option>5 a 10 cm</option><option>más de 10 cm</option></select></label><label htmlFor="carril_afectado">Carril afectado<select id="carril_afectado" value={detalle.carril_afectado} onChange={(e) => cambiarDetalle('carril_afectado', e.target.value)} required><option value="">Selecciona</option><option>carril derecho</option><option>carril central</option><option>carril izquierdo</option><option>varios carriles</option><option>acotamiento</option></select></label></div>}{tipo === 'Alcantarilla sin tapa' && <label className="radio-question">¿Está señalizada?<span className="radio-options"><label><input type="radio" name="esta_senalizado" value="si" checked={detalle.esta_senalizado === 'si'} onChange={(e) => cambiarDetalle('esta_senalizado', e.target.value)} required /> Sí</label><label><input type="radio" name="esta_senalizado" value="no" checked={detalle.esta_senalizado === 'no'} onChange={(e) => cambiarDetalle('esta_senalizado', e.target.value)} /> No</label></span></label>}{tipo === 'Encharcamiento' && <><label htmlFor="nivel_agua">Nivel del agua<select id="nivel_agua" value={detalle.nivel_agua} onChange={(e) => cambiarDetalle('nivel_agua', e.target.value)} required><option value="">Selecciona</option><option>a un lado de la calle</option><option>cubre un carril</option><option>a media llanta</option><option>intransitable</option></select></label>{detalle.nivel_agua === 'intransitable' && <label className="radio-question">¿Hay riesgo para personas o vehículos?<span className="radio-options"><label><input type="radio" name="riesgo" value="si" checked={detalle.hay_riesgo_personas_vehiculos === 'si'} onChange={(e) => cambiarDetalle('hay_riesgo_personas_vehiculos', e.target.value)} required /> Sí</label><label><input type="radio" name="riesgo" value="no" checked={detalle.hay_riesgo_personas_vehiculos === 'no'} onChange={(e) => cambiarDetalle('hay_riesgo_personas_vehiculos', e.target.value)} /> No</label></span></label>}</>}<label htmlFor="referencia">Referencia <span className="field-help">(opcional)</span></label><input id="referencia" value={detalle.referencia} onChange={(e) => cambiarDetalle('referencia', e.target.value)} maxLength={200} placeholder="Ej. frente a la escuela" /><label htmlFor="descripcion">Descripción <span className="field-help">(opcional, máximo 500 caracteres)</span></label><textarea id="descripcion" value={detalle.descripcion} onChange={(e) => cambiarDetalle('descripcion', e.target.value)} maxLength={500} rows={4} placeholder="Describe lo que observaste, sin datos personales." /><p className="character-count">{detalle.descripcion.length}/500</p>{!hayDuplicados && <FotoPicker archivos={fotos} onChange={setFotos} disabled={enviando} />}<button className="button button--primary button--full button--lg" disabled={enviando}>{enviando ? 'Enviando reporte…' : 'Enviar reporte'}</button></fieldset></form>
    </>}</main>;
}
