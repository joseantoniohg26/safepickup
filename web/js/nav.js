/**
 * SafePickup — Navegación
 * ========================
 * Controla el cambio entre páginas del sistema.
 */

const PAGE_TITLES = {
  dashboard:     'Panel general',
  camara:        'Cámara en vivo',
  estudiantes:   'Estudiantes',
  apoderados:    'Apoderados',
  aulas:         'Aulas',
  historial:     'Historial de eventos',
  estadisticas:  'Estadísticas del sistema',
  configuracion: 'Configuración del sistema'
};

const PAGE_BREADCRUMBS = {
  dashboard:     'Inicio',
  camara:        'Cámara en vivo',
  estudiantes:   'Gestión › Estudiantes',
  apoderados:    'Gestión › Apoderados',
  aulas:         'Gestión › Aulas',
  historial:     'Reportes › Historial',
  estadisticas:  'Reportes › Estadísticas',
  configuracion: 'Sistema › Configuración'
};

function navegar(page) {
  // Detener cámara si salimos de ese módulo
  if (page !== 'camara') detenerCamara();

  // Cambiar página activa
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const pageEl = $('page-' + page);
  const navEl  = document.querySelector(`.nav-item[data-page="${page}"]`);

  if (pageEl) pageEl.classList.add('active');
  if (navEl)  navEl.classList.add('active');

  $('pageTitle').textContent  = PAGE_TITLES[page]      || page;
  $('breadcrumb').textContent = PAGE_BREADCRUMBS[page] || page;

  // Cargar datos según la página
  const loaders = {
    dashboard:     () => { verificarBackend(); cargarEventosDashboard(); },
    estudiantes:   () => renderEstudiantes(),
    apoderados:    () => cargarApoderados(),
    aulas:         () => renderAulas(),
    historial:     () => cargarHistorialCompleto(),
    estadisticas:  () => cargarEstadisticas(),
    configuracion: () => cargarConfiguracion()
  };

  if (loaders[page]) loaders[page]();
}
