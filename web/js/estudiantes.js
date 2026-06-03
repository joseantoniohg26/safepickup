/**
 * SafePickup — Módulo Estudiantes
 * =================================
 * Gestión de estudiantes conectada al backend MySQL.
 */

window._estudiantesCache = [];

async function renderEstudiantes() {
  try {
    const res  = await fetch(API_URL + '/api/estudiantes');
    const data = await res.json();
    window._estudiantesCache = data.estudiantes || [];
  } catch (e) {
    // Si falla la API, usar localStorage como fallback
    window._estudiantesCache = JSON.parse(localStorage.getItem('safepickup_estudiantes') || '[]');
  }
  _renderTablaEstudiantes(window._estudiantesCache);
  _poblarFiltroAulas();
}

function _poblarFiltroAulas() {
  const select = $('filterAula');
  if (!select) return;
  const aulas = JSON.parse(localStorage.getItem('safepickup_aulas') || '[]');
  select.innerHTML = '<option value="">Todas las aulas</option>' +
    aulas.map(a => `<option value="${a.nombre}">${a.nombre}</option>`).join('');
}

function _renderTablaEstudiantes(lista) {
  const tbody   = $('estudiantesTbody');
  const summary = $('estudiantesSummary');
  const footer  = $('estudiantesFooterInfo');

  if (summary) summary.textContent = `${lista.length} estudiantes — nivel inicial`;
  if (footer)  footer.textContent  = `Mostrando ${lista.length} de ${window._estudiantesCache.length} estudiantes`;

  if (!tbody) return;

  if (!lista.length) {
    tbody.innerHTML = `
      <tr><td colspan="7">
        <div class="empty">
          <svg class="icon icon-lg" viewBox="0 0 24 24" style="opacity:0.4;">
            <path d="M22 10v6M2 10l10-5 10 5-10 5z"/>
          </svg>
          <div class="empty-title">Sin estudiantes registrados</div>
          <div class="empty-sub">Use el botón "Registrar nuevo estudiante"</div>
        </div>
      </td></tr>`;
    return;
  }

  tbody.innerHTML = lista.map(e => {
    // Soporte tanto para API MySQL como localStorage
    const nombre   = e.nombre || `${e.nombres || ''} ${e.apellidos || ''}`.trim();
    const iniciales = nombre.split(' ').filter(Boolean).map(n => n[0]).join('').slice(0, 2).toUpperCase();
    const fechaNac  = e.fecha_nac || e.fechaNac || '';
    const edad      = fechaNac ? calcularEdad(fechaNac) : '--';
    const aula      = e.aula || '';
    const seccion   = e.seccion || e.seccion || '';
    const turno     = e.turno || '';
    const numApo    = e.num_apoderados || e.numApoderados || 0;
    const estado    = e.estado_hoy || e.estado || 'presente';

    const badgeEstado = estado === 'recogido'
      ? `<span class="badge badge-green">Recogido ${e.hora_recojo || ''}</span>`
      : `<span class="badge badge-blue">Presente</span>`;

    const badgeApo = numApo > 0
      ? `<span class="badge badge-green">${numApo} registrado${numApo > 1 ? 's' : ''}</span>`
      : `<span class="badge badge-red">0 sin foto</span>`;

    return `
      <tr>
        <td>
          <div class="cell-name">
            <div class="cell-avatar">${iniciales}</div>
            <div class="cell-info">
              <div class="cell-primary">${nombre}</div>
              <div class="cell-secondary">F.N.: ${fechaNac ? formatearFecha(fechaNac) : '--'}</div>
            </div>
          </div>
        </td>
        <td>${aula}${seccion ? ' — Sección ' + seccion : ''}</td>
        <td>${turno}</td>
        <td>${edad} años</td>
        <td>${badgeApo}</td>
        <td>${badgeEstado}</td>
        <td>
          <div class="row-actions">
            <button class="icon-btn danger" onclick="eliminarEstudianteUI(${e.id})" title="Eliminar">
              <svg class="icon icon-sm" viewBox="0 0 24 24">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/>
              </svg>
            </button>
          </div>
        </td>
      </tr>`;
  }).join('');
}

function filtrarEstudiantes() {
  const q      = ($('searchEstudiantes')?.value || '').toLowerCase();
  const aulaF  = $('filterAula')?.value || '';
  const estadoF = $('filterEstado')?.value || '';

  const filtrados = window._estudiantesCache.filter(e => {
    const nombre = e.nombre || `${e.nombres || ''} ${e.apellidos || ''}`;
    if (q && !nombre.toLowerCase().includes(q)) return false;
    if (aulaF && (e.aula || '') !== aulaF)      return false;
    if (estadoF && (e.estado_hoy || e.estado || 'presente') !== estadoF) return false;
    return true;
  });

  _renderTablaEstudiantes(filtrados);
}

function abrirModalEstudiante() {
  ['estNombres','estApellidos','estDni','estMatricula'].forEach(id => {
    if ($(id)) $(id).value = '';
  });
  if ($('estFechaNac')) $('estFechaNac').value = '';
  if ($('estSexo'))     $('estSexo').value     = '';
  if ($('estTurno'))    $('estTurno').value     = '';

  // Llenar selector de aulas desde MySQL o localStorage
  if ($('estAula')) {
    fetch(API_URL + '/api/aulas').then(r => r.json()).then(data => {
      $('estAula').innerHTML = '<option value="">Seleccionar aula...</option>' +
        (data.aulas || []).map(a =>
          `<option value="${a.id}" data-secciones="${a.secciones}">${a.nombre} (${a.edad} años)</option>`
        ).join('');
    }).catch(() => {
      const aulas = JSON.parse(localStorage.getItem('safepickup_aulas') || '[]');
      $('estAula').innerHTML = '<option value="">Seleccionar aula...</option>' +
        aulas.map(a =>
          `<option value="${a.nombre}" data-secciones="${a.secciones.join(',')}">${a.nombre} (${a.edad} años)</option>`
        ).join('');
    });
  }
  if ($('estSeccion')) $('estSeccion').innerHTML = '<option value="">Seleccionar...</option>';

  abrirModal('modalEstudiante');
}

function actualizarSecciones() {
  const opt = $('estAula')?.selectedOptions[0];
  if (!opt || !$('estSeccion')) return;
  const secs = (opt.dataset.secciones || 'A').split(',');
  $('estSeccion').innerHTML = '<option value="">Seleccionar...</option>' +
    secs.map(s => `<option value="${s}">Sección ${s}</option>`).join('');
}

async function guardarEstudiante() {
  const nombres   = $('estNombres')?.value.trim();
  const apellidos = $('estApellidos')?.value.trim();
  const fechaNac  = $('estFechaNac')?.value;
  const sexo      = $('estSexo')?.value;
  const matricula = $('estMatricula')?.value.trim();
  const aulaVal   = $('estAula')?.value;
  const seccion   = $('estSeccion')?.value;
  const turno     = $('estTurno')?.value;
  const dni       = $('estDni')?.value.trim();

  if (!nombres || !apellidos || !fechaNac || !sexo || !matricula || !aulaVal || !seccion || !turno) {
    alert('Complete todos los campos requeridos'); return;
  }

  try {
    // Intentar API MySQL
    const res = await fetch(API_URL + '/api/estudiantes/registrar', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nombres, apellidos, fecha_nac: fechaNac, sexo,
        aula_id: parseInt(aulaVal) || null,
        seccion, turno, matricula, dni: dni || null
      })
    });

    if (res.ok) {
      cerrarModal('modalEstudiante');
      renderEstudiantes();
      return;
    }
  } catch (_) { /* fallback localStorage */ }

  // Fallback: guardar en localStorage si API no disponible
  const lista = JSON.parse(localStorage.getItem('safepickup_estudiantes') || '[]');
  const aulas = JSON.parse(localStorage.getItem('safepickup_aulas') || '[]');
  const aulaObj = aulas.find(a => a.nombre === aulaVal || a.id == aulaVal);

  lista.push({
    id: Date.now(), nombres, apellidos, fechaNac, sexo, dni,
    matricula, aula: aulaObj?.nombre || aulaVal, seccion, turno,
    numApoderados: 0, estado: 'presente'
  });
  localStorage.setItem('safepickup_estudiantes', JSON.stringify(lista));
  cerrarModal('modalEstudiante');
  renderEstudiantes();
}

async function eliminarEstudianteUI(id) {
  if (!confirm('¿Eliminar este estudiante?')) return;
  try {
    await fetch(API_URL + '/api/estudiantes/' + id, { method: 'DELETE' });
  } catch (_) {
    // Fallback localStorage
    const lista = JSON.parse(localStorage.getItem('safepickup_estudiantes') || '[]');
    localStorage.setItem('safepickup_estudiantes',
      JSON.stringify(lista.filter(e => e.id !== id)));
  }
  renderEstudiantes();
}
