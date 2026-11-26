import { useAuth } from './context/useAuth';
import { SiteHeader } from './components/SiteHeader';
import { Icon } from './components/Icon';
import { Logo } from './components/Logo';
import { Splash } from './components/Splash';
import { SeccionInstalacion } from './components/InstalarApp';
import { RainBanner } from './components/RainBanner';
import { BannerRed } from './components/BannerRed';
import { PuntosRecurrentesPage } from './pages/PuntosRecurrentesPage';
import { AdminCatalogosPage } from './pages/AdminCatalogosPage';
import { CuadrillasPage } from './pages/CuadrillasPage';
import { EnlacePage } from './pages/EnlacePage';
import { PerfilPage } from './pages/PerfilPage';
import { ResumenColoniaPage } from './pages/ResumenColoniaPage';
import { TrayectoPage } from './pages/TrayectoPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { PublicHomePage } from './pages/PublicHomePage';
import { ReportDetailPage } from './pages/ReportDetailPage';
import { ReportCreatePage } from './pages/ReportCreatePage';
import { ZonePage } from './pages/ZonePage';
import { AdminColoniasPage } from './pages/AdminColoniasPage';
import { AdminUsuariosPage } from './pages/AdminUsuariosPage';
import { MyReportsPage } from './pages/MyReportsPage';
import { PrivacyNoticePage } from './pages/PrivacyNoticePage';
import { ReportEditPage } from './pages/ReportEditPage';
import { AuditPage, CoordinationPage, DashboardPage, ModerationPage } from './pages/AdminPages';

function App() {
  useAuth();
  const path = window.location.pathname;
  const folioEdicion = path === '/reportar' ? new URLSearchParams(window.location.search).get('editar') : null;
  const contenido = path === '/login' ? <LoginPage /> : path === '/registro' ? <RegisterPage /> : path === '/aviso-de-privacidad' ? <PrivacyNoticePage /> : folioEdicion ? <ReportEditPage folio={folioEdicion} /> : path === '/reportar' ? <ReportCreatePage /> : path === '/mis-reportes' ? <MyReportsPage /> : path === '/moderacion' ? <ModerationPage /> : path === '/coordinacion' ? <CoordinationPage /> : path === '/puntos-recurrentes' ? <PuntosRecurrentesPage /> : path === '/cuadrillas' ? <CuadrillasPage /> : path === '/enlace' ? <EnlacePage /> : path === '/admin/catalogos' ? <AdminCatalogosPage /> : path === '/perfil' ? <PerfilPage /> : path === '/trayecto' ? <TrayectoPage /> : path === '/resumen-colonia' ? <ResumenColoniaPage /> : path === '/admin/colonias' ? <AdminColoniasPage /> : path === '/admin/usuarios' ? <AdminUsuariosPage /> : path === '/mi-zona' ? <ZonePage /> : path === '/dashboard' || path === '/tablero' ? <DashboardPage /> : path === '/auditoria' ? <AuditPage /> : path.startsWith('/reportes/') ? <ReportDetailPage folio={decodeURIComponent(path.split('/')[2] ?? '')} /> : <PublicHomePage />;
  return (
    <>
    <Splash /><SiteHeader /><BannerRed /><RainBanner />{contenido}<footer className="site-footer">
      <svg className="site-footer__art" viewBox="0 0 1200 240" preserveAspectRatio="xMidYMax slice" aria-hidden="true" focusable="false">
        <path d="M-20 60C120 30 260 90 420 70s300-50 460-10 260 40 360 20" />
        <path d="M-20 140c200-20 400 10 620-10s380-40 600-10" />
        <path d="M180 0c20 80 10 160 40 260M560 0c-10 90 0 170-20 260M900 0c30 70 20 170 50 260" />
        <path d="M-20 140c200-20 400 10 620-10s380-40 600-10" className="glow" />
      </svg>
      <Logo variante="tonal" size={320} className="site-footer__sello" />
      <div className="site-footer__inner">
        <p className="site-footer__brand"><Logo variante="mono" size={40} className="site-footer__logo" /><span>Calles Seguras <em>Juárez</em></span></p>
        <p>Información pública para una movilidad más segura en Ciudad Juárez, Chihuahua.</p>
        <p className="site-footer__note"><Icon name="shield" size={16} />Las vistas públicas nunca muestran datos de quien reporta.</p>
        <SeccionInstalacion />
      </div>
    </footer>
    </>
  )
}

export default App
