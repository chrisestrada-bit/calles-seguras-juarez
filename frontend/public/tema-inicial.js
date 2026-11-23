/* Aplica el tema antes del primer pintado para evitar parpadeo (FOUC).
 * Vive en un archivo propio (no inline) para que la CSP pueda prohibir scripts inline (auditoría final, M5). */
(function () {
  var tema = 'light';
  try {
    var guardado = localStorage.getItem('csj-theme');
    tema = guardado === 'dark' || guardado === 'light' ? guardado : (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  } catch { /* localStorage o matchMedia no disponibles: queda el tema claro */ }
  document.documentElement.setAttribute('data-theme', tema);
  var meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', tema === 'dark' ? '#0b1120' : '#f3f5f9');
})();
