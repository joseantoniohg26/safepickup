/**
 * SafePickup — Módulo Apoderados
 * ================================
 * Carga, renderiza, filtra y gestiona los apoderados.
 * Incluye el registro con cámara en modal flotante.
 */

let apoderadosCache = [];

// ============================================================
// CARGAR Y RENDERIZAR
// ============================================================

async function cargarApoderados() {
  try {
    const res  = await fetch(API_URL + '/api/apoderados');
    const data = await res.json();
    apoderadosCache = data.apoderados || [];
    renderApoderados(apoderadosCache);
    actualizarMiniStats(apoderadosCache);
  } catch (e) {
    console.error('[Apoderados] Error al cargar:', e);
  }
}

function actualizarMiniStats(lista) {
  const total      = lista.length;
  const conFoto    = lista.filter(a => a.tiene_embedding).length;
  const sinFoto    = total - conFoto;

  if ($('apoderadosTotal'))     $('apoderadosTotal').textContent     = total;
  if ($('apoderadosCompletos')) $('apoderadosCompletos').textContent = conFoto;
  if ($('apoderadosPendientes'))$('apoderadosPendientes').textContent = sinFoto;
  if ($('apoderadosSummary'))   $('apoderadosSummary').textContent   =
    `${conFoto} con foto — ${sinFoto} pendientes`;
}

function renderApoderados(lista) {
  const tbody = $('apoderadosTbody');
  if (!tbody) return;

  if (!lista.length) {
    tbody.innerHTML = `
      <tr><td colspan="7">
        <div class="empty">
          <svg class="icon icon-lg" viewBox="0 0 24 24" style="opacity:0.4;">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
          </svg>
          <div class="empty-title">Sin apoderados registrados</div>
        </div>
      </td></tr>`;
    return;
  }

  tbody.innerHTML = lista.map(ap => {
    const ini    = (ap.nombre || '').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
    const fecha  = ap.fecha_registro ? formatearFecha(ap.fecha_registro) : '--';
    const badgeEmb = ap.tiene_embedding
      ? '<span class="badge badge-green">Generado</span>'
      : '<span class="badge badge-amber">Pendiente</span>';
    return `
      <tr>
        <td>
          <div class="cell-name">
            <div class="cell-avatar green">${ini}</div>
            <div class="cell-info">
              <div class="cell-primary">${ap.nombre}</div>
              <div class="cell-secondary">${ap.telefono || '--'}</div>
            </div>
          </div>
        </td>
        <td style="font-family:monospace;">${ap.dni || '--'}</td>
        <td>${ap.parentesco || '--'}</td>
        <td>${ap.estudiante_nombre || '—'}</td>
        <td>${badgeEmb}</td>
        <td><span class="badge badge-green">Activo</span></td>
        <td>
          <div class="row-actions">
            <button class="icon-btn danger" onclick="eliminarApoderado(${ap.id})" title="Eliminar">
              <svg class="icon icon-sm" viewBox="0 0 24 24">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/>
              </svg>
            </button>
          </div>
        </td>
      </tr>`;
  }).join('');

  if ($('apoderadosFooterInfo'))
    $('apoderadosFooterInfo').textContent = `Mostrando ${lista.length} apoderados`;
}

function filtrarApoderados() {
  const q = ($('searchApoderados')?.value || '').toLowerCase();
  const filtrados = apoderadosCache.filter(ap =>
    (ap.nombre || '').toLowerCase().includes(q) ||
    (ap.dni    || '').includes(q)
  );
  renderApoderados(filtrados);
}

async function eliminarApoderado(id) {
  if (!confirm('¿Eliminar este apoderado? Esta acción no se puede deshacer.')) return;
  try {
    await fetch(API_URL + '/api/apoderados/' + id, { method: 'DELETE' });
    await cargarApoderados();
    verificarBackend();
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

// ============================================================
// MODAL — REGISTRO DE APODERADO
// ============================================================

let apoStream        = null;
let apoFotoCapturada = null;

function abrirModalApoderado() {
  // Limpiar formulario
  ['apoNombres','apoApellidos','apoDni','apoTelefono'].forEach(id => {
    if ($(id)) $(id).value = '';
  });
  if ($('apoParentesco')) $('apoParentesco').value = '';

  // Llenar selector de estudiantes
  if ($('apoEstudiante')) {
    $('apoEstudiante').innerHTML = '<option value="">Seleccionar estudiante...</option>' +
      (window._estudiantesCache || []).map(e =>
        `<option value="${e.id}">${e.nombres} ${e.apellidos} — ${e.aula || ''}</option>`
      ).join('');
  }

  // Resetear foto
  apoFotoCapturada = null;
  if ($('apoVideo'))   $('apoVideo').style.display   = 'block';
  if ($('apoPreview')) $('apoPreview').style.display = 'none';
  if ($('apoEmpty'))   $('apoEmpty').style.display   = 'flex';
  if ($('apoBtnInit'))    $('apoBtnInit').disabled    = false;
  if ($('apoBtnCapture')) $('apoBtnCapture').disabled = true;
  if ($('apoBtnReset'))   $('apoBtnReset').disabled   = true;
  if ($('btnGuardarApoderado')) $('btnGuardarApoderado').disabled = true;

  abrirModal('modalApoderado');
}

async function apoIniciarCam() {
  try {
    apoStream = await navigator.mediaDevices.getUserMedia({
      video: { width: 640, height: 480 }, audio: false
    });
    $('apoVideo').srcObject    = apoStream;
    $('apoEmpty').style.display = 'none';
    $('apoBtnInit').disabled    = true;
    $('apoBtnCapture').disabled = false;
  } catch (e) {
    alert('No se pudo acceder a la cámara: ' + e.message);
  }
}

function apoDetenerCam() {
  if (apoStream) { apoStream.getTracks().forEach(t => t.stop()); apoStream = null; }
  if ($('apoVideo')) $('apoVideo').srcObject = null;
}

function apoCapturar() {
  const video = $('apoVideo');
  const c     = document.createElement('canvas');
  c.width     = video.videoWidth;
  c.height    = video.videoHeight;
  c.getContext('2d').drawImage(video, 0, 0);
  apoFotoCapturada = c.toDataURL('image/jpeg', 0.95);

  $('apoVideo').style.display   = 'none';
  $('apoPreview').src            = apoFotoCapturada;
  $('apoPreview').style.display  = 'block';
  $('apoBtnCapture').disabled    = true;
  $('apoBtnReset').disabled      = false;
  $('btnGuardarApoderado').disabled = false;
}

function apoResetear() {
  apoFotoCapturada              = null;
  $('apoVideo').style.display   = 'block';
  $('apoPreview').style.display = 'none';
  $('apoBtnCapture').disabled   = false;
  $('apoBtnReset').disabled     = true;
  $('btnGuardarApoderado').disabled = true;
}

async function guardarApoderado() {
  const nombres    = $('apoNombres')?.value.trim();
  const apellidos  = $('apoApellidos')?.value.trim();
  const dni        = $('apoDni')?.value.trim();
  const telefono   = $('apoTelefono')?.value.trim();
  const parentesco = $('apoParentesco')?.value;
  const estId      = $('apoEstudiante')?.value;

  if (!nombres || !apellidos || !dni || !parentesco) {
    alert('Complete nombres, apellidos, DNI y parentesco'); return;
  }
  if (!apoFotoCapturada) {
    alert('Capture una foto del apoderado'); return;
  }

  $('btnGuardarApoderado').disabled    = true;
  $('btnGuardarApoderado').textContent = 'Procesando...';

  try {
    const res = await fetch(API_URL + '/api/apoderados/registrar', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nombre:        nombres + ' ' + apellidos,
        parentesco, dni, telefono,
        imagen_base64: apoFotoCapturada,
        estudiante_id: estId ? parseInt(estId) : null
      })
    });
    const data = await res.json();

    if (res.ok) {
      alert(`✓ ${data.mensaje}\nConfianza detección: ${(data.confianza_deteccion * 100).toFixed(1)}%`);
      apoDetenerCam();
      cerrarModal('modalApoderado');
      cargarApoderados();
      verificarBackend();
    } else {
      alert('Error: ' + (data.detail || 'No se pudo registrar'));
    }
  } catch (e) {
    alert('Error de conexión: ' + e.message);
  } finally {
    $('btnGuardarApoderado').disabled    = false;
    $('btnGuardarApoderado').textContent = 'Guardar y generar embedding facial';
  }
}
