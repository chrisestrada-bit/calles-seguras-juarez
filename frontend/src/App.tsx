import { useAuth } from './context/AuthContext';
import './styles/global.css';

function App() {
  const { usuario, rolActivo, autenticado, cerrarSesion } = useAuth();
  return (
    <main className="contenedor">
      <header><h1>Calles Seguras Juárez</h1><p>Reporta daños y consulta el estado de las calles de Ciudad Juárez.</p></header>
      <section aria-labelledby="sesion-titulo"><h2 id="sesion-titulo">Sesión</h2>
        {autenticado ? <><p>Hola, {usuario?.nombre}. Rol activo: {rolActivo}.</p><button type="button" onClick={() => void cerrarSesion()}>Cerrar sesión</button></> : <p>Consulta reportes públicos o inicia sesión para participar.</p>}
      </section>
    </main>
  )
}

export default App
