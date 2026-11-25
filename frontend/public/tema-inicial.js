/* Aplica el tema antes del primer pintado para evitar parpadeo (FOUC).
 * Claro editorial es el tema por defecto; Grafito turquesa sólo si la persona lo eligió antes.
 * Vive en un archivo propio (no inline) para que la CSP pueda prohibir scripts inline (auditoría final, M5). */
(function () {
  var tema = 'light';
  try {
    if (localStorage.getItem('csj-theme') === 'dark') tema = 'dark';
  } catch { /* localStorage no disponible: queda el tema claro */ }
  document.documentElement.setAttribute('data-theme', tema);
  var meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute('content', tema === 'dark' ? '#0d1015' : '#f6f4ef');
})();
