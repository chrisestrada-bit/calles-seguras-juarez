import { useEffect, useState } from 'react';
import { ApiError, api, obtenerBlob } from '../services/api';
import { Icon } from './Icon';
import type { ListaFotosResponse } from '../types/api';

type Estado = { tipo: 'cargando' } | { tipo: 'listo'; fotos: Array<{ id: string; nombre: string; url: string }> } | { tipo: 'privada' } | { tipo: 'error' };

/** HU-02.4: galería de fotos. Mientras el reporte está «Recibido» sólo la ve su autor o moderación (el servidor responde 403). */
export function FotosReporte({ folio }: { folio: string }) {
  const [estado, setEstado] = useState<Estado>({ tipo: 'cargando' });

  useEffect(() => {
    let activo = true;
    const urls: string[] = [];
    (async () => {
      try {
        const lista = await api.get<ListaFotosResponse>(`/api/v1/reportes/${encodeURIComponent(folio)}/fotos`);
        // Las imágenes se piden con fetch para enviar la sesión; un <img src> no podría autenticarse.
        const fotos = await Promise.all(lista.datos.map(async (f) => {
          const url = URL.createObjectURL(await obtenerBlob(f.url));
          urls.push(url);
          return { id: f.id, nombre: f.nombre_original, url };
        }));
        if (activo) setEstado({ tipo: 'listo', fotos });
      } catch (e) {
        if (activo) setEstado(e instanceof ApiError && e.status === 403 ? { tipo: 'privada' } : { tipo: 'error' });
      }
    })();
    return () => { activo = false; urls.forEach((u) => URL.revokeObjectURL(u)); };
  }, [folio]);

  return (
    <section className="detail-card__photos" aria-labelledby="fotos-titulo">
      <h2 id="fotos-titulo"><Icon name="camera" size={20} />Fotografías</h2>
      {estado.tipo === 'cargando' && <p className="field-help" role="status">Cargando fotografías…</p>}
      {estado.tipo === 'error' && <p className="form-error" role="alert">No pudimos cargar las fotografías. Intenta de nuevo más tarde.</p>}
      {estado.tipo === 'privada' && <p className="field-help" role="status"><Icon name="shield" size={16} />Las fotografías se publican cuando moderación valida el reporte.</p>}
      {estado.tipo === 'listo' && estado.fotos.length === 0 && <p className="field-help">Este reporte no tiene fotografías.</p>}
      {estado.tipo === 'listo' && estado.fotos.length > 0 && (
        <ul className="photo-gallery">
          {estado.fotos.map((f, i) => <li key={f.id}><a href={f.url} target="_blank" rel="noreferrer"><img src={f.url} alt={`Fotografía ${i + 1} del reporte ${folio}`} loading="lazy" /></a></li>)}
        </ul>
      )}
    </section>
  );
}
