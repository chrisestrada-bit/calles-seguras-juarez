import { useEffect, useState, type FormEvent } from 'react';
import { useAuth } from '../context/AuthContext';
import { api, ApiError } from '../services/api';
import type {
  CandidatoCercano, ColoniasResponse, CrearReporteRequest, GeocodingResponse, GeocodingResultado,
  NivelAgua, ReportePublico, TipoDano, Ubicacion,
} from '../types/api';

const TIPOS: TipoDano[] = ['Bache', 'Alcantarilla sin tapa', 'Encharcamiento'];
const LIMITES = { latitudMin: 31.45, latitudMax: 31.80, longitudMin: -106.65, longitudMax: -106.25 };
const enJuarez = ({ latitud, longitud }: Ubicacion) => latitud >= LIMITES.latitudMin && latitud <= LIMITES.latitudMax && longitud >= LIMITES.longitudMin && longitud <= LIMITES.longitudMax;

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
  const [colonias, setColonias] = useState<ColoniasResponse['datos']>([]);
  const [ubicacionEstado, setUbicacionEstado] = useState('');
  const [cargandoUbicacion, setCargandoUbicacion] = useState(false);
  const [candidatos, setCandidatos] = useState<CandidatoCercano[]>([]);
  const [radio, setRadio] = useState<number | null>(null);
  const [revisandoDuplicados, setRevisandoDuplicados] = useState(false);
  const [forzarNuevo, setForzarNuevo] = useState(false);
  const [detalle, setDetalle] = useState({ tamano: '', profundidad: '', carril_afectado: '', esta_senalizado: '', nivel_agua: '', hay_riesgo_personas_vehiculos: '', referencia: '', descripcion: '' });
  const [error, setError] = useState('');
  const mostrarError = (e: unknown) => setError(e instanceof ApiError ? e.message : 'No fue posible completar la solicitud. Intenta de nuevo.');
  const [exito, setExito] = useState<ReportePublico | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    api.get<ColoniasResponse>('/api/v1/catalogos/colonias?pagina=1&por_pagina=100').then((respuesta) => setColonias(respuesta.datos)).catch(() => setUbicacionEstado('No pudimos cargar el catálogo de colonias; podrás intentarlo de nuevo al recargar.'));
  }, []);

  useEffect(() => {
    setCandidatos([]); setRadio(null); setForzarNuevo(false); setError('');
    if (!ubicacion) return;
    let activo = true;
    setRevisandoDuplicados(true);
    api.get<{ radio_metros: number; candidatos: CandidatoCercano[] }>(`/api/v1/reportes/cercanos?latitud=${ubicacion.latitud}&longitud=${ubicacion.longitud}&tipo_dano=${encodeURIComponent(tipo)}`)
      .then((respuesta) => { if (activo) { setCandidatos(respuesta.candidatos); setRadio(respuesta.radio_metros); } })
      .catch((e) => { if (activo) setError(e instanceof ApiError && e.codigo === 'FUERA_DE_JUAREZ' ? e.message : 'No pudimos revisar reportes cercanos.'); })
      .finally(() => { if (activo) setRevisandoDuplicados(false); });
    return () => { activo = false; };
  }, [ubicacion, tipo]);

  if (!autenticado) return <main className="report-page"><section className="auth-card"><h1>Reportar un daño</h1><p>Inicia sesión para registrar un reporte y darle seguimiento.</p><a className="button" href="/login">Iniciar sesión</a></section></main>;

  const seleccionarUbicacion = (resultado: GeocodingResultado) => {
    setUbicacion(resultado.ubicacion); setCalle(resultado.calle ?? '');
    if (resultado.colonia_sugerida) setColoniaId(String(resultado.colonia_sugerida.id));
    setResultados([]); setUbicacionEstado(resultado.precision === 'aproximada' ? 'La ubicación es aproximada. Confirma la colonia y ajusta la dirección si es necesario.' : 'Ubicación seleccionada.');
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
      if (!enJuarez(punto)) { setUbicacion(null); setUbicacionEstado('La ubicación está fuera de los límites de Ciudad Juárez, Chihuahua. Selecciona un punto dentro del municipio.'); return; }
      setUbicacion(punto); setCalle(''); setUbicacionEstado('Ubicación GPS seleccionada. Elige la colonia correspondiente.');
    }, () => setUbicacionEstado('No pudimos obtener tu ubicación. Revisa el permiso del navegador e intenta de nuevo.'));
  };

  const cambiarTipo = (nuevo: TipoDano) => { setTipo(nuevo); setUbicacion(null); setResultados([]); setUbicacionEstado('Selecciona nuevamente la ubicación para revisar duplicados.'); };
  const cambiarDetalle = (campo: keyof typeof detalle, valor: string) => setDetalle((actual) => ({ ...actual, [campo]: valor }));

  const confirmar = async (candidato: CandidatoCercano) => {
    setError('');
    try { await api.post(`/api/v1/reportes/${encodeURIComponent(candidato.folio)}/confirmaciones`, { tipo: tipo === 'Encharcamiento' ? 'sigue_ahi' : 'confirmacion_dano' }); setExito({ folio: candidato.folio } as ReportePublico); }
    catch (e) { mostrarError(e); }
  };

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault(); setError(''); setExito(null);
    if (!ubicacion || !enJuarez(ubicacion)) { setError('Selecciona una ubicación dentro de los límites de Ciudad Juárez.'); return; }
    if (!coloniaId) { setError('Selecciona la colonia del reporte.'); return; }
    const base = { tipo_dano: tipo, ...ubicacion, colonia_id: Number(coloniaId), calle: calle.trim(), referencia: detalle.referencia.trim() || undefined, descripcion: detalle.descripcion.trim() || undefined, forzar_nuevo: forzarNuevo };
    let payload: CrearReporteRequest;
    if (tipo === 'Bache') payload = { ...base, tipo_dano: 'Bache', tamano: detalle.tamano as 'chico' | 'mediano' | 'grande', profundidad: detalle.profundidad as never, carril_afectado: detalle.carril_afectado as never };
    else if (tipo === 'Alcantarilla sin tapa') payload = { ...base, tipo_dano: 'Alcantarilla sin tapa', esta_senalizado: detalle.esta_senalizado === 'si' };
    else payload = { ...base, tipo_dano: 'Encharcamiento', nivel_agua: detalle.nivel_agua as NivelAgua, ...(detalle.nivel_agua === 'intransitable' ? { hay_riesgo_personas_vehiculos: detalle.hay_riesgo_personas_vehiculos === 'si' } : {}) };
    setEnviando(true);
    try { setExito(await api.post<ReportePublico>('/api/v1/reportes', payload)); } catch (e) { mostrarError(e); } finally { setEnviando(false); }
  };

  const hayDuplicados = candidatos.length > 0 && !forzarNuevo;
  return <main className="report-page"><section className="report-intro"><p className="eyebrow">HU-02 · HU-03</p><h1>Reportar un daño</h1><p>Ayúdanos a identificar baches, alcantarillas sin tapa y encharcamientos en Ciudad Juárez.</p></section>
    {error && <div className="form-error" role="alert"><ErrorApiTexto error={error} /></div>}
    {exito ? <section className="form-success" aria-live="polite"><h2>Reporte registrado</h2><p>Tu folio es <strong>{exito.folio}</strong>. Gracias por ayudar a cuidar nuestras calles.</p><a className="button" href={`/reportes/${encodeURIComponent(exito.folio)}`}>Ver reporte</a></section> : <>
      <section className="report-section" aria-labelledby="tipo-titulo"><h2 id="tipo-titulo">1. ¿Qué observaste?</h2><div className="type-options">{TIPOS.map((opcion) => <label className={`type-option${tipo === opcion ? ' type-option--selected' : ''}`} key={opcion}><input type="radio" name="tipo_dano" checked={tipo === opcion} onChange={() => cambiarTipo(opcion)} /><span>{opcion}</span>{opcion === 'Alcantarilla sin tapa' && <small>Severidad Alta fija</small>}</label>)}</div></section>
      <section className="report-section" aria-labelledby="ubicacion-titulo"><h2 id="ubicacion-titulo">2. ¿Dónde está?</h2><form className="location-search" onSubmit={buscarDireccion}><label htmlFor="direccion">Buscar por dirección, calle o cruce</label><div className="inline-form"><input id="direccion" value={consulta} onChange={(e) => setConsulta(e.target.value)} placeholder="Ej. Tecnológico y Ejército Nacional" /><button className="button" disabled={cargandoUbicacion}>{cargandoUbicacion ? 'Buscando…' : 'Buscar'}</button></div></form><button className="button button--secondary" type="button" onClick={usarGps}>Usar mi ubicación GPS</button>{ubicacion && <p className="location-readout" role="status">Punto: {ubicacion.latitud.toFixed(6)}, {ubicacion.longitud.toFixed(6)}. {ubicacionEstado}</p>}{ubicacionEstado && !ubicacion && <p className="field-help" role="status">{ubicacionEstado}</p>}{resultados.length > 0 && <ul className="search-results" aria-label="Resultados de dirección">{resultados.map((resultado) => <li key={`${resultado.etiqueta}-${resultado.ubicacion.latitud}`}><button type="button" onClick={() => seleccionarUbicacion(resultado)}><strong>{resultado.etiqueta}</strong><span>{resultado.precision}</span></button></li>)}</ul>}<label htmlFor="colonia">Colonia <span aria-hidden="true">*</span></label><select id="colonia" value={coloniaId} onChange={(e) => setColoniaId(e.target.value)} required><option value="">Selecciona la colonia</option>{colonias.map((colonia) => <option key={colonia.id} value={colonia.id}>{colonia.nombre}</option>)}</select><label htmlFor="calle">Calle</label><input id="calle" value={calle} onChange={(e) => setCalle(e.target.value)} minLength={3} maxLength={150} required placeholder="Ej. Avenida Tecnológico" />{revisandoDuplicados && <p className="field-help" role="status">Revisando reportes cercanos…</p>}{!revisandoDuplicados && ubicacion && candidatos.length === 0 && <p className="form-success" role="status">No encontramos reportes abiertos o vigentes en el radio correspondiente.</p>}{candidatos.length > 0 && <div className="duplicate-box" role="alert"><h3>Encontramos un reporte cercano</h3><p>Hay un reporte a menos de {radio} metros. Puedes confirmarlo o indicar que el daño es distinto.</p>{candidatos.map((candidato) => <article className="duplicate-card" key={candidato.folio}><div><strong>{candidato.folio}</strong><span>{candidato.calle} · {candidato.distancia_metros.toFixed(1)} m</span></div>{candidato.es_mio ? <p className="field-help">Este reporte es tuyo y no puedes confirmarlo.</p> : candidato.ya_confirmado_por_mi ? <p className="field-help">Ya confirmaste este reporte.</p> : <button className="button button--secondary" type="button" onClick={() => void confirmar(candidato)}>Confirmar existente</button>}</article>)}{!forzarNuevo && <button className="button" type="button" onClick={() => setForzarNuevo(true)}>Es un daño distinto, crear reporte nuevo</button>}{forzarNuevo && <p className="field-help">Crearás un reporte nuevo y quedará registrado como daño distinto.</p>}</div>}</section>
      <form onSubmit={enviar}><fieldset className="report-section" disabled={!ubicacion || revisandoDuplicados || hayDuplicados}><legend>3. Detalles del reporte</legend><p className="field-help">No escribas datos personales en la descripción.</p>{tipo === 'Bache' && <div className="field-grid"><label htmlFor="tamano">Tamaño<select id="tamano" value={detalle.tamano} onChange={(e) => cambiarDetalle('tamano', e.target.value)} required><option value="">Selecciona</option><option>chico</option><option>mediano</option><option>grande</option></select></label><label htmlFor="profundidad">Profundidad<select id="profundidad" value={detalle.profundidad} onChange={(e) => cambiarDetalle('profundidad', e.target.value)} required><option value="">Selecciona</option><option>menos de 5 cm</option><option>5 a 10 cm</option><option>más de 10 cm</option></select></label><label htmlFor="carril_afectado">Carril afectado<select id="carril_afectado" value={detalle.carril_afectado} onChange={(e) => cambiarDetalle('carril_afectado', e.target.value)} required><option value="">Selecciona</option><option>carril derecho</option><option>carril central</option><option>carril izquierdo</option><option>varios carriles</option><option>acotamiento</option></select></label></div>}{tipo === 'Alcantarilla sin tapa' && <label className="radio-question">¿Está señalizada?<span className="radio-options"><label><input type="radio" name="esta_senalizado" value="si" checked={detalle.esta_senalizado === 'si'} onChange={(e) => cambiarDetalle('esta_senalizado', e.target.value)} required /> Sí</label><label><input type="radio" name="esta_senalizado" value="no" checked={detalle.esta_senalizado === 'no'} onChange={(e) => cambiarDetalle('esta_senalizado', e.target.value)} /> No</label></span></label>}{tipo === 'Encharcamiento' && <><label htmlFor="nivel_agua">Nivel del agua<select id="nivel_agua" value={detalle.nivel_agua} onChange={(e) => cambiarDetalle('nivel_agua', e.target.value)} required><option value="">Selecciona</option><option>a un lado de la calle</option><option>cubre un carril</option><option>a media llanta</option><option>intransitable</option></select></label>{detalle.nivel_agua === 'intransitable' && <label className="radio-question">¿Hay riesgo para personas o vehículos?<span className="radio-options"><label><input type="radio" name="riesgo" value="si" checked={detalle.hay_riesgo_personas_vehiculos === 'si'} onChange={(e) => cambiarDetalle('hay_riesgo_personas_vehiculos', e.target.value)} required /> Sí</label><label><input type="radio" name="riesgo" value="no" checked={detalle.hay_riesgo_personas_vehiculos === 'no'} onChange={(e) => cambiarDetalle('hay_riesgo_personas_vehiculos', e.target.value)} /> No</label></span></label>}</>}<label htmlFor="referencia">Referencia <span className="field-help">(opcional)</span></label><input id="referencia" value={detalle.referencia} onChange={(e) => cambiarDetalle('referencia', e.target.value)} maxLength={200} placeholder="Ej. frente a la escuela" /><label htmlFor="descripcion">Descripción <span className="field-help">(opcional, máximo 500 caracteres)</span></label><textarea id="descripcion" value={detalle.descripcion} onChange={(e) => cambiarDetalle('descripcion', e.target.value)} maxLength={500} rows={4} placeholder="Describe lo que observaste, sin datos personales." /><p className="character-count">{detalle.descripcion.length}/500</p><button className="button button--full" disabled={enviando}>{enviando ? 'Enviando reporte…' : 'Enviar reporte'}</button></fieldset></form>
    </>}</main>;
}
