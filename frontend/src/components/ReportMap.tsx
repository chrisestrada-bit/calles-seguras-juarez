import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import type { MarcadorMapa, Ubicacion } from '../types/api';
import { colorDeToken } from '../hooks/useTema';
import { ATRIBUCION, CENTRO_JUAREZ, ERRORES_PARA_FALLAR, LIMITES, TILES_URL, descripcionMarcador, iconoDe } from './mapaUtils';

interface Props {
  marcadores: MarcadorMapa[];
  seleccionado: string | null;
  onSeleccionar: (folio: string) => void;
  /** Ubicación del usuario (sólo tras pulsar «Centrar en mi ubicación»). */
  miUbicacion: Ubicacion | null;
  onFalloMapa: () => void;
  /** Nombre accesible de la región (cada mapa de la página debe tener uno distinto). */
  etiqueta?: string;
  /** Al cambiar esta clave (p. ej. los filtros) el mapa se reencuadra; las actualizaciones en vivo no mueven la vista. */
  claveEncuadre?: string;
}

const ETIQUETA_PREDETERMINADA = 'Mapa interactivo de reportes en Ciudad Juárez. Los mismos reportes están disponibles como lista debajo del mapa.';

export function ReportMap({ marcadores, seleccionado, onSeleccionar, miUbicacion, onFalloMapa, etiqueta = ETIQUETA_PREDETERMINADA, claveEncuadre = '' }: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<L.Map | null>(null);
  const grupo = useRef<L.MarkerClusterGroup | null>(null);
  const yo = useRef<L.CircleMarker | null>(null);
  const porFolio = useRef(new Map<string, { marker: L.Marker; datos: MarcadorMapa }>());
  // Último encuadre aplicado: sólo se vuelve a encuadrar si cambia la clave (filtros), no con cada evento en vivo.
  const encuadre = useRef<string | null>(null);
  // Los callbacks vigentes se leen desde refs para no recrear el mapa en cada render.
  const alSeleccionar = useRef(onSeleccionar);
  const alFallar = useRef(onFalloMapa);
  // La selección vigente también se lee al regenerar íconos (actualizaciones en vivo) para no perder el resaltado.
  const elegido = useRef(seleccionado);
  useEffect(() => { alSeleccionar.current = onSeleccionar; alFallar.current = onFalloMapa; elegido.current = seleccionado; });

  useEffect(() => {
    if (!contenedor.current) return;
    const instancia = L.map(contenedor.current, { center: CENTRO_JUAREZ, zoom: 11, minZoom: 10, maxBounds: LIMITES, maxBoundsViscosity: 0.8 });
    let errores = 0;
    let avisado = false;
    const capa = L.tileLayer(TILES_URL, { attribution: ATRIBUCION, maxZoom: 19 }).addTo(instancia);
    capa.on('tileload', () => { errores = 0; });
    capa.on('tileerror', () => {
      errores += 1;
      if (errores >= ERRORES_PARA_FALLAR && !avisado) { avisado = true; alFallar.current(); }
    });
    const cluster = L.markerClusterGroup({ showCoverageOnHover: false, maxClusterRadius: 48, spiderfyOnMaxZoom: true });
    instancia.addLayer(cluster);
    mapa.current = instancia;
    grupo.current = cluster;
    const registro = porFolio.current;
    return () => { instancia.remove(); mapa.current = null; grupo.current = null; yo.current = null; registro.clear(); encuadre.current = null; };
  }, []);

  useEffect(() => {
    const cluster = grupo.current;
    if (!cluster) return;
    cluster.clearLayers();
    porFolio.current.clear();
    const marcas = marcadores.map((m) => {
      const marker = L.marker([m.ubicacion.latitud, m.ubicacion.longitud], {
        icon: iconoDe(m, m.folio === elegido.current), title: descripcionMarcador(m), alt: descripcionMarcador(m), keyboard: true, riseOnHover: true,
      });
      marker.on('click', () => alSeleccionar.current(m.folio));
      marker.on('keypress', (e) => { if ((e.originalEvent as KeyboardEvent).key === 'Enter') alSeleccionar.current(m.folio); });
      porFolio.current.set(m.folio, { marker, datos: m });
      return marker;
    });
    // Encuadre ANTES de agrupar y con límites calculados de las coordenadas: mover el mapa justo después de
    // addLayers dispara los manejadores de zoom de markercluster a medio agrupar y, con cientos de puntos,
    // rompe con «Cannot use 'in' operator to search for '_leaflet_id' in undefined».
    if (marcas.length > 0 && mapa.current && encuadre.current !== claveEncuadre) {
      encuadre.current = claveEncuadre;
      const limites = L.latLngBounds(marcadores.map((m) => [m.ubicacion.latitud, m.ubicacion.longitud] as L.LatLngTuple));
      mapa.current.fitBounds(limites.pad(0.15), { maxZoom: 15, animate: false });
    }
    cluster.addLayers(marcas);
  }, [marcadores, claveEncuadre]);

  useEffect(() => {
    porFolio.current.forEach(({ marker, datos }, folio) => marker.setIcon(iconoDe(datos, folio === seleccionado)));
    const actual = seleccionado ? porFolio.current.get(seleccionado) : undefined;
    if (actual && mapa.current && grupo.current) grupo.current.zoomToShowLayer(actual.marker, () => mapa.current?.panTo(actual.marker.getLatLng()));
  }, [seleccionado]);

  useEffect(() => {
    if (!mapa.current || !miUbicacion) return;
    const punto: L.LatLngExpression = [miUbicacion.latitud, miUbicacion.longitud];
    yo.current?.remove();
    // Colores de la identidad activa (Leaflet no lee variables CSS directamente).
    yo.current = L.circleMarker(punto, { radius: 9, color: colorDeToken('--surface', '#ffffff'), weight: 3, fillColor: colorDeToken('--route-700', '#3f6212'), fillOpacity: 1 }).bindTooltip('Tu ubicación').addTo(mapa.current);
    mapa.current.flyTo(punto, 15);
  }, [miUbicacion]);

  return <div ref={contenedor} className="report-map" role="region" aria-label={etiqueta} />;
}
