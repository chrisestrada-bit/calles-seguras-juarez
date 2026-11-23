import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { EncharcamientoEnTrayecto, Ubicacion } from '../types/api';
import { ATRIBUCION, CENTRO_JUAREZ, LIMITES, TILES_URL } from './mapaUtils';

interface Props {
  origen: Ubicacion | null;
  destino: Ubicacion | null;
  ruta: Array<[number, number]>;
  encharcamientos: EncharcamientoEnTrayecto[];
  onClic: (punto: Ubicacion) => void;
}

// `texto` es siempre una letra fija ('A', 'B', 'E', '!'): nunca datos escritos por la ciudadanía.
const marca = (texto: string, tono: string) =>
  L.divIcon({ html: `<span class="map-pin map-pin--${tono}" aria-hidden="true"><b>${texto}</b></span>`, className: 'map-pin-wrap', iconSize: [44, 30], iconAnchor: [22, 15] });

/** Contenido del globo con textContent: la calle la escribió un ciudadano y no debe interpretarse como HTML. */
function globo(folio: string, texto: string): HTMLElement {
  const div = document.createElement('div');
  const fuerte = document.createElement('strong');
  fuerte.textContent = folio;
  div.append(fuerte, document.createElement('br'), document.createTextNode(texto));
  return div;
}

/** HU-04.6: mapa del trayecto. Clic: primero origen (A), luego destino (B). La lista de resultados es la alternativa accesible. */
export function TrayectoMapa({ origen, destino, ruta, encharcamientos, onClic }: Props) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<L.Map | null>(null);
  const capa = useRef<L.LayerGroup | null>(null);
  const alClic = useRef(onClic);
  useEffect(() => { alClic.current = onClic; });

  useEffect(() => {
    if (!contenedor.current) return;
    const m = L.map(contenedor.current, { center: CENTRO_JUAREZ, zoom: 12, minZoom: 10, maxBounds: LIMITES });
    L.tileLayer(TILES_URL, { attribution: ATRIBUCION, maxZoom: 19 }).addTo(m);
    m.on('click', (e: L.LeafletMouseEvent) => alClic.current({ latitud: Number(e.latlng.lat.toFixed(6)), longitud: Number(e.latlng.lng.toFixed(6)) }));
    capa.current = L.layerGroup().addTo(m);
    mapa.current = m;
    return () => { m.remove(); mapa.current = null; capa.current = null; };
  }, []);

  useEffect(() => {
    const grupo = capa.current;
    if (!grupo || !mapa.current) return;
    grupo.clearLayers();
    if (origen) L.marker([origen.latitud, origen.longitud], { icon: marca('A', 'road'), title: 'Origen', alt: 'Origen' }).addTo(grupo);
    if (destino) L.marker([destino.latitud, destino.longitud], { icon: marca('B', 'road'), title: 'Destino', alt: 'Destino' }).addTo(grupo);
    if (ruta.length > 1) {
      const linea = L.polyline(ruta, { color: '#2446d8', weight: 5, opacity: 0.85 }).addTo(grupo);
      mapa.current.fitBounds(linea.getBounds().pad(0.2));
    }
    for (const e of encharcamientos) {
      const texto = `${e.es_intransitable ? 'Intransitable' : `Encharcamiento: ${e.nivel_agua}`} a ${Math.round(e.distancia_metros)} m del trayecto, ${e.calle}`;
      L.marker([e.ubicacion.latitud, e.ubicacion.longitud], { icon: marca(e.es_intransitable ? '!' : 'E', e.es_intransitable ? 'manhole' : 'water'), title: texto, alt: texto, keyboard: true })
        .bindPopup(globo(e.folio, texto))
        .addTo(grupo);
    }
  }, [origen, destino, ruta, encharcamientos]);

  return <div ref={contenedor} className="report-map" role="region" aria-label="Mapa del trayecto. Haz clic para marcar el origen y luego el destino. Los resultados también aparecen como lista." />;
}
