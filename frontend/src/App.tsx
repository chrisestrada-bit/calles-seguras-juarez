import { useAuth } from './context/AuthContext';
import { SiteHeader } from './components/SiteHeader';
import { Icon } from './components/Icon';
import { RainBanner } from './components/RainBanner';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { PublicHomePage } from './pages/PublicHomePage';
import { ReportDetailPage } from './pages/ReportDetailPage';
import { ReportCreatePage } from './pages/ReportCreatePage';
import { ZonePage } from './pages/ZonePage';
import { AdminColoniasPage } from './pages/AdminColoniasPage';
import { AdminUsuariosPage } from './pages/AdminUsuariosPage';
import { MyReportsPage } from './pages/MyReportsPage';
import { AuditPage, CoordinationPage, DashboardPage, ModerationPage } from './pages/AdminPages';

function App() {
  useAuth();
  const path = window.location.pathname;
  const contenido = path === '/login' ? <LoginPage /> : path === '/registro' ? <RegisterPage /> : path === '/reportar' ? <ReportCreatePage /> : path === '/mis-reportes' ? <MyReportsPage /> : path === '/moderacion' ? <ModerationPage /> : path === '/coordinacion' ? <CoordinationPage /> : path === '/admin/colonias' ? <AdminColoniasPage /> : path === '/admin/usuarios' ? <AdminUsuariosPage /> : path === '/mi-zona' ? <ZonePage /> : path === '/dashboard' || path === '/tablero' ? <DashboardPage /> : path === '/auditoria' ? <AuditPage /> : path.startsWith('/reportes/') ? <ReportDetailPage folio={decodeURIComponent(path.split('/')[2] ?? '')} /> : <PublicHomePage />;
  return (
    <>
    <SiteHeader /><RainBanner />{contenido}<footer className="site-footer">
      <svg className="site-footer__art" viewBox="0 0 1200 240" preserveAspectRatio="xMidYMax slice" aria-hidden="true" focusable="false">
        <path d="M-20 60C120 30 260 90 420 70s300-50 460-10 260 40 360 20" />
        <path d="M-20 140c200-20 400 10 620-10s380-40 600-10" />
        <path d="M180 0c20 80 10 160 40 260M560 0c-10 90 0 170-20 260M900 0c30 70 20 170 50 260" />
        <path d="M-20 140c200-20 400 10 620-10s380-40 600-10" className="glow" />
      </svg>
      <div className="site-footer__inner">
        <p className="site-footer__brand">Calles Seguras <span>Juárez</span></p>
        <p>Información pública para una movilidad más segura en Ciudad Juárez, Chihuahua.</p>
        <p className="site-footer__note"><Icon name="shield" size={16} />Las vistas públicas nunca muestran datos de quien reporta.</p>
      </div>
    </footer>
    </>
  )
}

export default App
