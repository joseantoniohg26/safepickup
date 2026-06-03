/**
 * SafePickup — Configuración global y utilidades
 * ================================================
 * Este archivo se carga PRIMERO. Define variables globales
 * y funciones de utilidad usadas por todos los módulos.
 */

// ============================================================
// CONFIGURACIÓN
// ============================================================

const API_URL = window.location.origin.includes('localhost')
  ? 'http://localhost:8000'
  : window.location.origin;

const INTERVALO_VERIFICACION = 2000; // ms entre verificaciones de cámara

const CREDENCIALES = {
  'admin':    'safepickup2026',
  'director': 'director123'
};

// Claves de localStorage
const STORAGE_CONFIG = 'safepickup_config';

// Configuración por defecto del sistema
const CONFIG_DEFAULT = {
  umbral: 0.60, antispoof: 'ensemble', votos: '2',
  resolucion: '1280x720', intervalo: '2',
  iluminacion: 'clahe', espejo: 'on', backup: 'daily'
};

// ============================================================
// UTILIDADES GLOBALES
// ============================================================

/** Shortcut para document.getElementById */
function $(id) {
  return document.getElementById(id);
}

/** Actualiza el reloj del topbar y la cámara */
function tick() {
  const t = new Date().toLocaleTimeString('es-PE', { hour12: false });
  const chipHora = $('chipHora');
  const camChip  = $('camChipTime');
  if (chipHora) chipHora.textContent = t;
  if (camChip)  camChip.textContent  = t;
}
setInterval(tick, 1000);
tick();

/** Verifica la conexión con el backend FastAPI cada 5 segundos */
async function verificarBackend() {
  try {
    const res  = await fetch(API_URL + '/api/estado');
    if (!res.ok) throw new Error('no ok');
    const data = await res.json();

    $('chipBackend').innerHTML = '<span class="chip-dot"></span>Backend activo';
    $('chipBackend').className = 'chip chip-green';
    $('statusDot').classList.remove('offline');
    $('statusText').textContent = 'Sistema activo';

    const apoderados = data.apoderados_registrados || 0;
    $('chipApoderados').textContent = apoderados + ' apoderados';

    // Actualizar KPIs del dashboard si existen
    if ($('kpiApoderados'))  $('kpiApoderados').textContent  = apoderados;
    if ($('kpiEstudiantes')) $('kpiEstudiantes').textContent = data.estudiantes_registrados || 0;
    if ($('kpiAutorizados')) $('kpiAutorizados').textContent = data.eventos_hoy?.autorizados || 0;

    const alertas = (data.eventos_hoy?.rechazados || 0) + (data.eventos_hoy?.spoofing || 0);
    if ($('kpiAlertas')) $('kpiAlertas').textContent = alertas;

    const badge = $('navAlertBadge');
    if (badge) {
      badge.style.display = alertas > 0 ? 'inline-block' : 'none';
      badge.textContent   = alertas;
    }

    return true;
  } catch (e) {
    $('chipBackend').innerHTML = '<span class="chip-dot"></span>Sin conexión';
    $('chipBackend').className = 'chip';
    $('statusDot').classList.add('offline');
    $('statusText').textContent = 'Sin conexión';
    return false;
  }
}
setInterval(verificarBackend, 5000);

/** Formatea una fecha ISO a formato local */
function formatearFecha(fecha) {
  if (!fecha) return '--';
  return new Date(fecha).toLocaleDateString('es-PE', {
    day: '2-digit', month: '2-digit', year: 'numeric'
  });
}

/** Calcula la edad a partir de una fecha de nacimiento */
function calcularEdad(fechaNac) {
  if (!fechaNac) return '--';
  const hoy = new Date();
  const nac = new Date(fechaNac);
  let edad  = hoy.getFullYear() - nac.getFullYear();
  const m   = hoy.getMonth() - nac.getMonth();
  if (m < 0 || (m === 0 && hoy.getDate() < nac.getDate())) edad--;
  return edad;
}
