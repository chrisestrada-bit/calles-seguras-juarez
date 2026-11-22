import { useAuth } from '../context/useAuth';
import { obtenerJson, useCargaDatos } from '../hooks/useCargaDatos';
import { Icon } from '../components/Icon';
import { BlockSkeleton, EmptyState } from '../components/ui';
import { fechaHora } from '../utils/formato';
import type { PuntosRecurrentesResponse } from '../types/api';

/** HU-03.4: vista del Coordinador con los puntos de inundación recurrente del año en curso. */
export function PuntosRecurrentesPage() {
  const { usuario } = useAuth();
  const esCoordinador = usuario?.rol === 'coordinador';
  const consulta = useCargaDatos<PuntosRecurrentesResponse>(esCoordinador ? '/api/v1/indicadores/puntos-recurrentes' : null, obtenerJson, 'No fue posible cargar los puntos recurrentes.');

  if (!esCoordinador) {
    return <main className="admin-page"><EmptyState art="inbox" title="Acceso restringido" action={<a className="button button--primary" href="/">Volver al inicio</a>}>Esta vista es sólo para coordinación.</EmptyState></main>;
  }
  const datos = consulta.datos;
  return (
    <main className="admin-page">
      <header className="admin-head">
        <h1>Puntos de inundación recurrente</h1>
        <p>Encharcamientos a menos de {datos?.radio_metros ?? 50} m entre sí con al menos {datos?.minimo_dias ?? 3} días distintos en {datos?.anio ?? 'el año en curso'} (hora de Ciudad Juárez). Varios reportes el mismo día cuentan como un solo día.</p>
      </header>
      {consulta.estado === 'cargando' && <BlockSkeleton label="Cargando puntos recurrentes…" lines={5} />}
      {consulta.estado === 'error' && <div className="form-error" role="alert">{consulta.error}</div>}
      {consulta.estado === 'listo' && datos && datos.datos.length === 0 && (
        <EmptyState art="map" title="Sin puntos recurrentes este año">Ningún punto acumula {datos.minimo_dias} días distintos de encharcamientos en {datos.anio}.</EmptyState>
      )}
      {consulta.estado === 'listo' && datos && datos.datos.length > 0 && (
        <div className="table-wrap">
          <table className="data-table">
            <caption className="visually-hidden">Puntos recurrentes de inundación en {datos.anio}</caption>
            <thead><tr><th scope="col">Ubicación</th><th scope="col">Colonia</th><th scope="col">Días distintos</th><th scope="col">Reportes</th><th scope="col">Última ocurrencia</th></tr></thead>
            <tbody>
              {datos.datos.map((p) => (
                <tr key={p.folios[0]}>
                  <th scope="row"><Icon name="pin" size={16} />{p.calle}<span className="table-sub">{p.ubicacion.latitud.toFixed(5)}, {p.ubicacion.longitud.toFixed(5)}</span></th>
                  <td>{p.colonia.nombre}</td>
                  <td><span className="badge-recurrente"><Icon name="repeat" size={14} /><span className="tabular">{p.dias_distintos_anio}</span> días</span></td>
                  <td className="tabular">{p.total_reportes}</td>
                  <td><time dateTime={p.ultima_ocurrencia}>{fechaHora(p.ultima_ocurrencia)}</time>{' '}<a href={`/reportes/${p.folios[0]}`}>Ver {p.folios[0]}</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
