import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, ApiError } from '../services/api';
import type { FusionResponse } from '../types/api';
import { Icon } from './Icon';

const PATRON = /^(BCH|ENC)-\d{4}-\d{6}$/;

/** HU-05.3: fusión con confirmación previa que identifica el folio principal y el secundario. */
export function FusionarDialog({ folioSecundario, onDone }: { folioSecundario: string; onDone: (r: FusionResponse) => void }) {
  const dialogo = useRef<HTMLDialogElement>(null);
  const [principal, setPrincipal] = useState('');
  const [paso, setPaso] = useState<'captura' | 'confirmar'>('captura');
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);

  useEffect(() => { if (paso === 'confirmar') dialogo.current?.querySelector<HTMLButtonElement>('[data-confirmar]')?.focus(); }, [paso]);

  const abrir = () => { setPrincipal(''); setPaso('captura'); setError(''); dialogo.current?.showModal(); };
  const cerrar = () => dialogo.current?.close();
  const revisar = (e: FormEvent) => {
    e.preventDefault();
    const folio = principal.trim().toUpperCase();
    if (!PATRON.test(folio)) { setError('Escribe un folio válido, por ejemplo BCH-2026-000418.'); return; }
    if (folio === folioSecundario) { setError('El folio principal debe ser distinto del reporte duplicado.'); return; }
    setPrincipal(folio); setError(''); setPaso('confirmar');
  };
  const fusionar = async () => {
    setOcupado(true); setError('');
    try {
      const r = await api.post<FusionResponse>('/api/v1/moderacion/reportes/fusionar', { folio_principal: principal, folio_secundario: folioSecundario });
      cerrar(); onDone(r);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'No fue posible fusionar los reportes.'); setPaso('captura');
    } finally { setOcupado(false); }
  };

  return (
    <>
      <button className="button button--quiet button--sm" type="button" onClick={abrir}><Icon name="merge" size={16} />Fusionar como duplicado</button>
      <dialog ref={dialogo} className="modal" aria-labelledby={`fusion-${folioSecundario}`}>
        <h2 id={`fusion-${folioSecundario}`}>Fusionar reporte duplicado</h2>
        {paso === 'captura' ? (
          <form onSubmit={revisar}>
            <p>El reporte <strong className="tabular">{folioSecundario}</strong> se marcará como «Rechazado» por duplicado y sus confirmaciones se sumarán al reporte principal.</p>
            <label htmlFor={`principal-${folioSecundario}`}>Folio del reporte principal</label>
            <input id={`principal-${folioSecundario}`} value={principal} onChange={(e) => setPrincipal(e.target.value)} placeholder="BCH-2026-000418" autoComplete="off" required />
            {error && <p className="form-error" role="alert">{error}</p>}
            <div className="modal__actions">
              <button className="button button--secondary" type="button" onClick={cerrar}>Cancelar</button>
              <button className="button button--primary" type="submit">Revisar fusión</button>
            </div>
          </form>
        ) : (
          <div>
            <dl className="modal__resumen">
              <div><dt>Reporte principal (se conserva abierto)</dt><dd className="tabular">{principal}</dd></div>
              <div><dt>Reporte duplicado (pasará a «Rechazado»)</dt><dd className="tabular">{folioSecundario}</dd></div>
            </dl>
            <p className="field-help">La acción queda en el historial y no se puede deshacer. El duplicado conserva su folio y mostrará un enlace al principal.</p>
            {error && <p className="form-error" role="alert">{error}</p>}
            <div className="modal__actions">
              <button className="button button--secondary" type="button" onClick={() => setPaso('captura')} disabled={ocupado}>Volver</button>
              <button className="button button--danger" type="button" data-confirmar onClick={() => void fusionar()} disabled={ocupado}>{ocupado ? 'Fusionando…' : 'Confirmar fusión'}</button>
            </div>
          </div>
        )}
      </dialog>
    </>
  );
}
