/**
 * SafePickup — Módulo Aulas
 * ==========================
 * Gestión de aulas conectada a MySQL (con fallback localStorage).
 */

async function renderAulas() {
  let aulas = [];
  try {
    const res  = await fetch(API_URL + '/api/aulas');
    const data = await res.json();
    aulas = data.aulas || [];
    // Sincronizar con localStorage para que otros módulos puedan usarlas
    localStorage.setItem('safepickup_aulas', JSON.stringify(
      aulas.map(a => ({
        id: a.id, nombre: a.nombre, edad: a.edad,
        secciones: (a.secciones || 'A').split(','),
        color: a.color || 'blue'
      }))
    ));
  } catch (_) {
    // Fallback a localStorage
    aulas = JSON.parse(localStorage.getItem('safepickup_aulas') || '[]');
    if (!aulas.length) {
      // Aulas por defecto si no hay nada
      aulas = [
        { id: 1, nombre: 'Mariposas',   edad: 3, secciones: 'A,B',   color: 'amber',  num_estudiantes: 0 },
        { id: 2, nombre: 'Pollitos',    edad: 4, secciones: 'A,B',   color: 'green',  num_estudiantes: 0 },
        { id: 3, nombre: 'Ositos',      edad: 5, secciones: 'A',     color: 'blue',   num_estudiantes: 0 },
        { id: 4, nombre: 'Estrellitas', edad: 4, secciones: 'A,B,C', color: 'purple', num_estudiantes: 0 }
      ];
    }
  }

  _renderGridAulas(aulas);
}

function _renderGridAulas(aulas) {
  const grid = $('aulasGrid');
  if (!grid) return;

  if (!aulas.length) {
    grid.innerHTML = '<div class="empty" style="grid-column:1/-1"><div class="empty-title">Sin aulas creadas</div></div>';
    return;
  }

  grid.innerHTML = aulas.map(a => {
    const secciones = typeof a.secciones === 'string'
      ? a.secciones.split(',')
      : a.secciones || ['A'];
    const color = a.color || 'blue';
    const num   = a.num_estudiantes || 0;

    return `
      <div class="aula-card">
        <div class="aula-card-head">
          <div class="aula-icon kpi-${color}">
            <svg class="icon icon-lg" viewBox="0 0 24 24">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          </div>
          <div class="aula-info">
            <div class="aula-name">${a.nombre}</div>
            <div class="aula-edad">${a.edad} años · Nivel inicial</div>
          </div>
        </div>
        <div class="aula-secciones">
          ${secciones.map(s => `<span class="aula-seccion-tag">Sección ${s.trim()}</span>`).join('')}
        </div>
        <div class="aula-stats">
          <span class="aula-stat-label">Estudiantes:</span>
          <span class="aula-stat-value">${num}</span>
        </div>
      </div>`;
  }).join('');
}

function abrirModalAula() {
  if ($('aulaNombre')) $('aulaNombre').value = '';
  if ($('aulaEdad'))   $('aulaEdad').value   = '';
  if ($('aulaColor'))  $('aulaColor').value  = 'blue';
  document.querySelectorAll('.seccionCheck').forEach((c, i) => c.checked = i === 0);
  abrirModal('modalAula');
}

async function guardarAula() {
  const nombre   = $('aulaNombre')?.value.trim();
  const edad     = parseInt($('aulaEdad')?.value);
  const color    = $('aulaColor')?.value || 'blue';
  const secciones = Array.from(document.querySelectorAll('.seccionCheck:checked'))
                         .map(c => c.value);

  if (!nombre || !edad || !secciones.length) {
    alert('Complete nombre, edad y al menos una sección'); return;
  }

  try {
    const res = await fetch(API_URL + '/api/aulas/registrar', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre, edad, secciones, color })
    });
    if (res.ok) {
      cerrarModal('modalAula');
      renderAulas();
      return;
    }
  } catch (_) { /* fallback localStorage */ }

  // Fallback localStorage
  const lista = JSON.parse(localStorage.getItem('safepickup_aulas') || '[]');
  lista.push({
    id: Date.now(), nombre, edad,
    secciones, color, num_estudiantes: 0
  });
  localStorage.setItem('safepickup_aulas', JSON.stringify(lista));
  cerrarModal('modalAula');
  renderAulas();
}
