import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import './styles/global.css'
import './styles/layout.css'
import './styles/components.css'
import './styles/pages.css'
import './styles/admin.css'
import './styles/map.css'
import './styles/tiempo-real.css'
import './styles/dark.css'

// HU-08.4: el Service Worker sÃ³lo se registra en producciÃ³n (en desarrollo estorbarÃ­a con la recarga en caliente).
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => { void navigator.serviceWorker.register('/sw.js').catch(() => undefined); });
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider><App /></AuthProvider>
  </StrictMode>,
)

