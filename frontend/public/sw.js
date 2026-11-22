/* Service Worker de Calles Seguras Juárez (HU-08.4).
 *
 * Qué guarda:
 *  - «Shell» de la app (HTML, manifiesto, iconos y los archivos con hash de /assets/): la app abre sin conexión.
 *  - Últimas consultas PÚBLICAS de reportes (lista, mapa y detalle) hechas SIN sesión, para verlas sin conexión.
 *
 * Qué NUNCA guarda (privacidad, RN-04):
 *  - Ninguna petición con encabezado Authorization (token JWT) ni sus respuestas.
 *  - /auth, /notificaciones, /reportes/mios, /moderacion, /admin, /indicadores privados, ni métodos distintos de GET.
 *  - Al cerrar sesión la app envía «limpiar-caches» y se vacía la caché pública.
 */
const VERSION = 'v1';
const CACHE_SHELL = `csj-shell-${VERSION}`;
const CACHE_PUBLICO = `csj-publico-${VERSION}`;
const MAX_ENTRADAS_PUBLICAS = 30;
const SHELL = ['/', '/index.html', '/manifest.webmanifest', '/favicon.svg', '/icons/icon-192.png', '/icons/icon-512.png'];

// Rutas de API públicas cacheables: lista, mapa y detalle por folio (nunca /mios ni /exportar).
const API_PUBLICA = /\/api\/v1\/reportes(\/mapa|\/(BCH|ENC)-\d{4}-\d{6})?$/;

self.addEventListener('install', (evento) => {
  evento.waitUntil(caches.open(CACHE_SHELL).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (evento) => {
  evento.waitUntil(
    caches.keys()
      .then((nombres) => Promise.all(nombres.filter((n) => n.startsWith('csj-') && n !== CACHE_SHELL && n !== CACHE_PUBLICO).map((n) => caches.delete(n))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('message', (evento) => {
  if (evento.data && evento.data.tipo === 'limpiar-caches') evento.waitUntil(caches.delete(CACHE_PUBLICO));
});

async function recortar(cache) {
  const llaves = await cache.keys();
  await Promise.all(llaves.slice(0, Math.max(0, llaves.length - MAX_ENTRADAS_PUBLICAS)).map((k) => cache.delete(k)));
}

async function redPrimero(peticion, nombreCache, alFallar) {
  const cache = await caches.open(nombreCache);
  try {
    const respuesta = await fetch(peticion);
    if (respuesta.ok) {
      await cache.put(peticion, respuesta.clone());
      if (nombreCache === CACHE_PUBLICO) await recortar(cache);
    }
    return respuesta;
  } catch (error) {
    const guardada = (await cache.match(peticion)) || (alFallar ? await alFallar() : undefined);
    if (guardada) return guardada;
    throw error;
  }
}

async function cachePrimero(peticion) {
  const cache = await caches.open(CACHE_SHELL);
  const guardada = await cache.match(peticion);
  if (guardada) return guardada;
  const respuesta = await fetch(peticion);
  if (respuesta.ok) await cache.put(peticion, respuesta.clone());
  return respuesta;
}

self.addEventListener('fetch', (evento) => {
  const peticion = evento.request;
  if (peticion.method !== 'GET') return;
  if (peticion.headers.has('Authorization')) return; // jamás se cachea nada autenticado
  const url = new URL(peticion.url);

  if (peticion.mode === 'navigate') {
    evento.respondWith(redPrimero(peticion, CACHE_SHELL, () => caches.match('/index.html')));
    return;
  }
  if (url.origin === self.location.origin && (url.pathname.startsWith('/assets/') || url.pathname.startsWith('/fonts/') || url.pathname.startsWith('/icons/'))) {
    evento.respondWith(cachePrimero(peticion));
    return;
  }
  if (API_PUBLICA.test(url.pathname) && (url.search === '' || !url.searchParams.has('token'))) {
    evento.respondWith(redPrimero(peticion, CACHE_PUBLICO));
  }
});
