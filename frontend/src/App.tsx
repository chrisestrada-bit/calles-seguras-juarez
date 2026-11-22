import { useAuth } from './context/AuthContext';
import { SiteHeader } from './components/SiteHeader';
import { RainBanner } from './components/RainBanner';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { PublicHomePage } from './pages/PublicHomePage';
import { ReportDetailPage } from './pages/ReportDetailPage';

function App() {
  useAuth();
  const path = window.location.pathname;
  const contenido = path === '/login' ? <LoginPage /> : path === '/registro' ? <RegisterPage /> : path.startsWith('/reportes/') ? <ReportDetailPage folio={decodeURIComponent(path.split('/')[2] ?? '')} /> : <PublicHomePage />;
  return (
    <><SiteHeader /><RainBanner />{contenido}<footer className="site-footer"><p>Calles Seguras Juárez · Información pública para una movilidad más segura.</p></footer></>
  )
}

export default App
