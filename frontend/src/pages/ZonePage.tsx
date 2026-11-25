import { ZoneSection } from '../components/ZoneSection';

export function ZonePage() {
  // El radar de 1 km (HU-04.3) vive aquí; «Mi zona» en la cabecera y en la portada llevan a esta vista.
  return <main className="public-page"><h1 className="visually-hidden">Mi zona</h1><ZoneSection /></main>;
}
