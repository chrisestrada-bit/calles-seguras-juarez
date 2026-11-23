import { useId, useMemo, useState } from 'react';
import { cargarColonias, etiquetaColonia, filtrarColonias } from '../services/catalogos';
import { useCargaDatos } from '../hooks/useCargaDatos';
import type { Colonia } from '../types/api';
import { Icon } from './Icon';

const cargar = () => cargarColonias();

/** Búsqueda accesible de colonias activas por nombre o código postal (lista de botones navegable con Tab). */
export function BuscadorColonia({ etiqueta, onElegir, excluir = [] }: { etiqueta: string; onElegir: (c: Colonia) => void; excluir?: number[] }) {
  const id = useId();
  const [texto, setTexto] = useState('');
  const catalogo = useCargaDatos('colonias', cargar, 'No pudimos cargar el catálogo de colonias.');
  const resultados = useMemo(() => filtrarColonias((catalogo.datos ?? []).filter((c) => !excluir.includes(c.id)), texto), [catalogo.datos, texto, excluir]);
  const buscando = texto.trim().length >= 2;

  return (
    <div className="colonia-search">
      <label htmlFor={id}>{etiqueta}</label>
      <div className="input-icon"><Icon name="search" size={18} /><input id={id} value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Nombre de la colonia o código postal" autoComplete="off" aria-describedby={`${id}-estado`} /></div>
      <p id={`${id}-estado`} className="field-help" role="status">
        {catalogo.estado === 'cargando' ? 'Cargando colonias…' : catalogo.estado === 'error' ? catalogo.error : buscando ? `${resultados.length} resultado(s)` : 'Escribe al menos 2 letras o los primeros dígitos del código postal.'}
      </p>
      {buscando && resultados.length > 0 && (
        <ul className="search-results" aria-label="Colonias encontradas">
          {resultados.map((c) => <li key={c.id}><button type="button" onClick={() => { onElegir(c); setTexto(''); }}><Icon name="pin" size={18} /><strong>{etiquetaColonia(c)}</strong><span>{c.sector.nombre}</span></button></li>)}
        </ul>
      )}
    </div>
  );
}
