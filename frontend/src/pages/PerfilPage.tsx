import { useState } from 'react';
import { useAuth } from '../context/useAuth';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { api, ApiError } from '../services/api';
import { BuscadorColonia } from '../components/BuscadorColonia';
import { Guard, PageIntro } from '../components/AdminShared';
import { Icon } from '../components/Icon';
import { BlockSkeleton, EmptyState, Notice } from '../components/ui';
import type { Colonia, ListaFavoritas } from '../types/api';

/** HU-01.4: elegir mis colonias de interés. La consulta pública las prioriza bajo «Tus colonias». */
export function PerfilPage() {
  const { usuario } = useAuth();
  const [recarga, setRecarga] = useState(0);
  const [aviso, setAviso] = useState<{ tono: 'success' | 'error'; texto: string } | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const favoritas = useCargaDatos<ListaFavoritas>(usuario ? `/api/v1/perfil/colonias-favoritas#${recarga}` : null, obtenerJson, 'No pudimos cargar tus colonias.');
  const lista = favoritas.datos?.datos ?? [];

  const agregar = async (c: Colonia) => {
    setOcupado(true); setAviso(null);
    try { await api.post('/api/v1/perfil/colonias-favoritas', { colonia_id: c.id }); setAviso({ tono: 'success', texto: `Guardamos ${c.nombre} en tus colonias.` }); setRecarga((n) => n + 1); }
    catch (e) { setAviso({ tono: 'error', texto: e instanceof ApiError ? e.message : 'No pudimos guardar la colonia.' }); }
    finally { setOcupado(false); }
  };
  const quitar = async (id: number, nombre: string) => {
    setOcupado(true); setAviso(null);
    try { await api.delete(`/api/v1/perfil/colonias-favoritas/${id}`); setAviso({ tono: 'success', texto: `Quitamos ${nombre} de tus colonias.` }); setRecarga((n) => n + 1); }
    catch (e) { setAviso({ tono: 'error', texto: e instanceof ApiError ? e.message : 'No pudimos quitar la colonia.' }); }
    finally { setOcupado(false); }
  };

  return (
    <Guard roles={['ciudadano', 'moderador', 'coordinador']}>
      <main className="admin-page">
        <PageIntro title="Mi perfil">Elige tus colonias de interés: en la consulta de reportes verás primero los de «Tus colonias», sin ocultar el resto de la ciudad.</PageIntro>
        {aviso && <Notice tone={aviso.tono} live={aviso.tono === 'error' ? 'alert' : 'status'}>{aviso.texto}</Notice>}
        <section className="panel" aria-labelledby="mis-colonias-titulo">
          <h2 id="mis-colonias-titulo"><Icon name="star" size={20} />Tus colonias {favoritas.datos && <small className="tabular">({lista.length}/{favoritas.datos.maximo})</small>}</h2>
          {favoritas.estado === 'cargando' && <BlockSkeleton label="Cargando tus colonias…" lines={2} />}
          {favoritas.estado === 'error' && <div className="form-error" role="alert">{favoritas.error}</div>}
          {favoritas.estado === 'listo' && lista.length === 0 && <EmptyState art="map" title="Aún no eliges colonias">Busca tu colonia, la de tu trabajo o la de la escuela y agrégala.</EmptyState>}
          {lista.length > 0 && (
            <ul className="chip-list">
              {lista.map((f) => (
                <li key={f.colonia.id} className={`chip${f.activa ? '' : ' chip--inactive'}`}>
                  <Icon name={f.activa ? 'pin' : 'ban'} size={16} />
                  <span>{f.colonia.nombre}{f.codigo_postal ? ` (C.P. ${f.codigo_postal})` : ''} · {f.sector.nombre}</span>
                  {!f.activa && <span className="chip__note">Colonia desactivada: se conserva, pero ya no recibe reportes nuevos.</span>}
                  <button type="button" className="link-button" onClick={() => void quitar(f.colonia.id, f.colonia.nombre)} disabled={ocupado} aria-label={`Quitar ${f.colonia.nombre}`}>Quitar</button>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section className="panel" aria-labelledby="agregar-colonia-titulo">
          <h2 id="agregar-colonia-titulo"><Icon name="plus" size={20} />Agregar colonia</h2>
          <BuscadorColonia etiqueta="Buscar colonia activa" onElegir={(c) => void agregar(c)} excluir={lista.map((f) => f.colonia.id)} />
        </section>
      </main>
    </Guard>
  );
}
