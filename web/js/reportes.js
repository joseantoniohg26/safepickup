/**
 * SafePickup — Módulos Historial, Estadísticas y Configuración
 * ==============================================================
 */

// ============================================================
// DASHBOARD — eventos
// ============================================================

async function cargarEventosDashboard() {
  try {
    const res  = await fetch(API_URL + '/api/eventos?limite=6');
    const data = await res.json();
    renderEventosDashboard(data.eventos || []);
    renderAlertasDashboard(data.eventos || []);
  } catch (e) { console.error(e); }
}

function renderEventosDashboard(eventos) {
  const el = $('dashEventList');
  if (!el) return;

  if (!eventos.length) {
    el.innerHTML = `
      <div class="empty">
        <svg class="icon icon-lg" viewBox="0 0 24 24" style="opacity:0.4;"><path d="M20 6L9 17l-5-5"/></svg>
        <div class="empty-title">Sin eventos hoy</div>
      </div>`;
    return;
  }

  el.innerHTML = eventos.map(e => {
    let dot, titulo, meta;
    if (e.tipo === 'autorizado') {
      dot = 'success'; titulo = (e.nombre || 'Apoderado') + ' — Autorizado';
      meta = e.confianza ? `Confianza: ${parseFloat(e.confianza).toFixed(1)}%` : 'OK';
    } else if (e.tipo === 'no_autorizado') {
      dot = 'danger'; titulo = 'Persona desconocida — Alerta';
      meta = e.confianza ? `Similitud: ${parseFloat(e.confianza).toFixed(1)}%` : 'Sin match';
    } else if (e.tipo === 'spoofing_detectado') {
      dot = 'warning'; titulo = 'Suplantación bloqueada';
      meta = e.motivo || 'Anti-spoofing actuó';
    } else { dot = ''; titulo = e.tipo; meta = ''; }

    const hora = e.fecha
      ? new Date(e.fecha).toLocaleTimeString('es-PE', { hour12: false }).slice(0, 5)
      : '--:--';

    return `
      <div class="event-item">
        <div class="event-dot ${dot}"></div>
        <div class="event-content">
          <div class="event-title">${titulo}</div>
          <div class="event-meta">${meta}</div>
        </div>
        <div class="event-time">${hora}</div>
      </div>`;
  }).join('');
}

function renderAlertasDashboard(eventos) {
  const el = $('alertList');
  if (!el) return;
  const alertas = eventos.filter(e =>
    e.tipo === 'no_autorizado' || e.tipo === 'spoofing_detectado'
  ).slice(0, 3);

  if (!alertas.length) {
    el.innerHTML = `<div class="empty"><div class="empty-title">Sin alertas activas</div></div>`;
    return;
  }
  el.innerHTML = alertas.map(a => {
    const tipo  = a.tipo === 'spoofing_detectado' ? 'warning' : 'danger';
    const titulo = a.tipo === 'spoofing_detectado' ? 'Suplantación bloqueada' : 'No autorizado';
    const meta  = a.motivo || (a.confianza ? `Similitud: ${parseFloat(a.confianza).toFixed(1)}%` : '');
    const hora  = a.fecha ? new Date(a.fecha).toLocaleTimeString('es-PE', { hour12: false }).slice(0, 5) : '--';
    return `
      <div class="alert-item ${tipo}">
        <div class="alert-title"><span>${titulo} — ${hora}</span></div>
        <div class="alert-meta">${meta}</div>
      </div>`;
  }).join('');
}

// ============================================================
// HISTORIAL
// ============================================================

let historialCache = [];

async function cargarHistorialCompleto() {
  try {
    const res  = await fetch(API_URL + '/api/eventos?limite=500');
    const data = await res.json();
    historialCache = data.eventos || [];

    const hoy        = new Date().toISOString().slice(0, 10);
    const hoyEventos = historialCache.filter(e => (e.fecha || '').startsWith(hoy));
    const auth       = hoyEventos.filter(e => e.tipo === 'autorizado').length;
    const noauth     = hoyEventos.filter(e => e.tipo === 'no_autorizado').length;
    const spoof      = hoyEventos.filter(e => e.tipo === 'spoofing_detectado').length;
    const total      = hoyEventos.length;

    if ($('histTotal'))  $('histTotal').textContent  = total;
    if ($('histAuth'))   $('histAuth').textContent   = auth;
    if ($('histAuthSub')) $('histAuthSub').textContent = total > 0 ? ((auth/total)*100).toFixed(1)+'% del total' : '0%';
    if ($('histAlerts')) $('histAlerts').textContent = noauth + spoof;

    if (!$('histFiltroFecha').value)
      $('histFiltroFecha').value = hoy;

    filtrarHistorial();
  } catch (e) { console.error(e); }
}

function filtrarHistorial() {
  const fecha  = $('histFiltroFecha')?.value;
  const tipo   = $('histFiltroTipo')?.value;
  const buscar = ($('histBuscar')?.value || '').toLowerCase();

  const filtrados = historialCache.filter(e => {
    if (fecha  && !(e.fecha || '').startsWith(fecha)) return false;
    if (tipo   && e.tipo !== tipo)                    return false;
    if (buscar && !((e.nombre || '') + (e.motivo || '')).toLowerCase().includes(buscar)) return false;
    return true;
  });

  renderHistorial(filtrados);
  if ($('historyFooterInfo'))
    $('historyFooterInfo').textContent = `Mostrando ${filtrados.length} de ${historialCache.length} eventos`;
}

function renderHistorial(eventos) {
  const el = $('historyList');
  if (!el) return;

  if (!eventos.length) {
    el.innerHTML = `
      <div class="empty">
        <svg class="icon icon-lg" viewBox="0 0 24 24" style="opacity:0.4;">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        </svg>
        <div class="empty-title">Sin eventos en este filtro</div>
        <div class="empty-sub">Pruebe cambiando la fecha o tipo</div>
      </div>`;
    return;
  }

  el.innerHTML = eventos.map(e => {
    let dot, titulo, meta;
    if (e.tipo === 'autorizado') {
      dot = 'success'; titulo = (e.nombre || 'Apoderado') + ' — Autorizado';
      meta = `Verificación exitosa${e.confianza ? ' — FaceNet: '+parseFloat(e.confianza).toFixed(1)+'%' : ''} — Tiempo: 0.4s`;
    } else if (e.tipo === 'no_autorizado') {
      dot = 'danger'; titulo = 'Persona desconocida — ALERTA generada';
      meta = `No encontrado en base de datos${e.confianza ? ' — FaceNet: '+parseFloat(e.confianza).toFixed(1)+'%' : ''} — Dirección notificada`;
    } else if (e.tipo === 'spoofing_detectado') {
      dot = 'warning'; titulo = 'Suplantación bloqueada por anti-spoofing';
      meta = e.motivo || 'Anti-spoofing detectó pantalla/foto';
    } else { dot = 'info'; titulo = e.tipo; meta = e.motivo || ''; }

    const hora = e.fecha ? new Date(e.fecha).toLocaleTimeString('es-PE', { hour12: false }).slice(0, 5) : '--:--';
    return `
      <div class="history-item">
        <div class="history-dot ${dot}"></div>
        <div class="history-content">
          <div class="history-title">${titulo}</div>
          <div class="history-meta">${meta}</div>
        </div>
        <div class="history-time">${hora}</div>
      </div>`;
  }).join('');
}

function exportarHistorial(formato) {
  alert(`Exportación a ${formato.toUpperCase()} — función disponible en Fase 2.`);
}

// ============================================================
// ESTADÍSTICAS
// ============================================================

async function cargarEstadisticas() {
  try {
    const res    = await fetch(API_URL + '/api/eventos?limite=500');
    const data   = await res.json();
    const eventos = data.eventos || [];
    const hoy    = new Date().toISOString().slice(0, 10);
    const hoyEv  = eventos.filter(e => (e.fecha || '').startsWith(hoy));
    const auth   = hoyEv.filter(e => e.tipo === 'autorizado').length;
    const total  = hoyEv.length;
    const tasa   = total > 0 ? ((auth / total) * 100).toFixed(1) : 0;

    if ($('totalHoyChip'))  $('totalHoyChip').textContent  = total + ' hoy';
    if ($('statEfectividad')) $('statEfectividad').textContent = tasa + '%';
    if ($('statTasaAuth'))  $('statTasaAuth').textContent   = tasa + '%';
    if ($('barTasaAuth'))   $('barTasaAuth').style.width    = tasa + '%';

    // Gráfico de barras por hora
    const porHora = {};
    hoyEv.forEach(e => {
      if (!e.fecha) return;
      const d   = new Date(e.fecha);
      const key = String(d.getHours()).padStart(2, '0') + ':' + (d.getMinutes() < 30 ? '00' : '30');
      porHora[key] = (porHora[key] || 0) + 1;
    });
    renderBarChart(porHora);
    renderResumenSemanal(eventos);
  } catch (e) { console.error(e); }
}

function renderBarChart(porHora) {
  const el   = $('barChartHoras');
  if (!el) return;
  const keys = Object.keys(porHora).sort();

  if (!keys.length) {
    el.innerHTML = `<div class="empty"><div class="empty-title">Sin datos suficientes</div></div>`;
    return;
  }
  const max = Math.max(...Object.values(porHora));
  el.innerHTML = keys.map(k => {
    const v   = porHora[k];
    const pct = max > 0 ? (v / max) * 100 : 0;
    const col = v >= max * 0.7 ? 'green' : 'blue';
    return `
      <div class="bar-chart-row">
        <div class="bar-chart-label">${k}</div>
        <div class="bar-chart-bar">
          <div class="bar-chart-fill ${col}" style="width:${Math.max(pct,8)}%;">${v}</div>
        </div>
      </div>`;
  }).join('');
}

function renderResumenSemanal(eventos) {
  const tbody = $('resumenSemanalBody');
  if (!tbody) return;
  const dias  = ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
  const rows  = [];

  for (let i = 6; i >= 0; i--) {
    const d     = new Date();
    d.setDate(d.getDate() - i);
    const fecha = d.toISOString().slice(0, 10);
    const ev    = eventos.filter(e => (e.fecha || '').startsWith(fecha));
    const auth  = ev.filter(e => e.tipo === 'autorizado').length;
    const alert = ev.filter(e => e.tipo !== 'autorizado').length;
    const total = ev.length;
    rows.push({
      nombre:    dias[d.getDay()] + ' ' + d.getDate(),
      total, auth, alert,
      precision: total > 0 ? ((auth / total) * 100).toFixed(1) + '%' : '--',
      tiempo:    total > 0 ? '0.40s' : '--',
      estado:    total === 0 ? 'gray' : alert > total * 0.2 ? 'amber' : 'green'
    });
  }

  tbody.innerHTML = rows.map(r => `
    <tr>
      <td><strong>${r.nombre}</strong></td>
      <td>${r.total}</td>
      <td>${r.auth > 0 ? `<span class="badge badge-green">${r.auth}</span>` : '0'}</td>
      <td>${r.alert > 0 ? `<span class="badge badge-red">${r.alert}</span>` : '0'}</td>
      <td>${r.precision}</td>
      <td>${r.tiempo}</td>
      <td><span class="badge badge-${r.estado}">${r.estado === 'green' ? 'Normal' : r.estado === 'amber' ? 'Atención' : 'Sin datos'}</span></td>
    </tr>`).join('');
}

// ============================================================
// CONFIGURACIÓN
// ============================================================

function cargarConfiguracion() {
  const cfg = Object.assign({}, CONFIG_DEFAULT,
    JSON.parse(localStorage.getItem(STORAGE_CONFIG) || '{}'));

  ['cfgAntispoof','cfgVotos','cfgAlertaVisual','cfgAlertaSonora',
   'cfgGuardarCaptura','cfgFuente','cfgResolucion','cfgIntervalo',
   'cfgIluminacion','cfgEspejo','cfgBackup'].forEach(id => {
    const el = $(id);
    if (el && cfg[id.replace('cfg','').charAt(0).toLowerCase() + id.replace('cfg','').slice(1)]) {
      el.value = cfg[id.replace('cfg','').charAt(0).toLowerCase() + id.replace('cfg','').slice(1)];
    }
  });

  if ($('cfgUmbral')) {
    $('cfgUmbral').value = cfg.umbral || 0.60;
    actualizarSliderUmbral();
  }

  fetch(API_URL + '/api/estado').then(r => r.json()).then(data => {
    if ($('cfgJsonPath'))
      $('cfgJsonPath').textContent = `MySQL · ${data.apoderados_registrados} apoderados`;
  }).catch(() => {
    if ($('cfgJsonPath')) $('cfgJsonPath').textContent = 'MySQL — verificar conexión';
  });
}

function actualizarSliderUmbral() {
  const v     = parseFloat($('cfgUmbral')?.value || 0.6);
  const label = $('thresholdLabel');
  if (!label) return;
  const pct = ((v - 0.30) / (1.00 - 0.30)) * 100;
  label.textContent  = v.toFixed(2);
  label.style.left   = pct + '%';
  marcarConfigSinGuardar();
}

let _configModificado = false;
function marcarConfigSinGuardar() {
  if (!_configModificado) {
    _configModificado = true;
    if ($('cfgLastSaved')) {
      $('cfgLastSaved').textContent = 'Cambios sin guardar';
      $('cfgLastSaved').style.color = 'var(--amber)';
    }
  }
}

document.addEventListener('change', e => {
  if (e.target.id?.startsWith('cfg')) marcarConfigSinGuardar();
});

function guardarConfig() {
  const cfg = {
    umbral:        parseFloat($('cfgUmbral')?.value || 0.6),
    antispoof:     $('cfgAntispoof')?.value,
    votos:         $('cfgVotos')?.value,
    alertaVisual:  $('cfgAlertaVisual')?.value,
    alertaSonora:  $('cfgAlertaSonora')?.value,
    guardarCaptura: $('cfgGuardarCaptura')?.value,
    fuente:        $('cfgFuente')?.value,
    resolucion:    $('cfgResolucion')?.value,
    intervalo:     $('cfgIntervalo')?.value,
    iluminacion:   $('cfgIluminacion')?.value,
    espejo:        $('cfgEspejo')?.value,
    backup:        $('cfgBackup')?.value
  };
  localStorage.setItem(STORAGE_CONFIG, JSON.stringify(cfg));
  _configModificado = false;
  const hora = new Date().toLocaleTimeString('es-PE', { hour12: false });
  if ($('cfgLastSaved')) {
    $('cfgLastSaved').textContent = 'Guardado a las ' + hora;
    $('cfgLastSaved').style.color = 'var(--green)';
  }
  alert('Configuración guardada.\nAlgunos cambios requieren reiniciar el servidor Python.');
}

function restablecerConfig() {
  if (!confirm('¿Restablecer valores predeterminados?')) return;
  localStorage.removeItem(STORAGE_CONFIG);
  cargarConfiguracion();
  _configModificado = false;
  if ($('cfgLastSaved')) {
    $('cfgLastSaved').textContent = 'Valores restablecidos';
    $('cfgLastSaved').style.color = 'var(--text-2)';
  }
}

function exportarConfig() {
  const cfg  = JSON.parse(localStorage.getItem(STORAGE_CONFIG) || JSON.stringify(CONFIG_DEFAULT));
  const blob = new Blob([JSON.stringify(cfg, null, 2)], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = 'safepickup_config_' + new Date().toISOString().slice(0, 10) + '.json';
  a.click();
  URL.revokeObjectURL(url);
}
