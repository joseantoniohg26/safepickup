/**
 * SafePickup — Modales (ventanas flotantes)
 * ==========================================
 * Controla apertura, cierre, minimización y maximización
 * de las ventanas modales tipo Windows.
 */

function abrirModal(id) {
  $(id).classList.add('show');
  const inner = $(id + 'Inner') || $(id).querySelector('.modal');
  if (inner) inner.classList.remove('minimized', 'maximized');
}

function cerrarModal(id) {
  $(id).classList.remove('show');
  if (id === 'modalApoderado') apoDetenerCam();
}

function minimizarModal(innerId) {
  const m = $(innerId);
  m.classList.toggle('minimized');
  m.classList.remove('maximized');
}

function maximizarModal(innerId) {
  const m = $(innerId);
  m.classList.toggle('maximized');
  m.classList.remove('minimized');
}

/** Hace una modal arrastrable por su barra de título */
function makeDraggable(titlebarId, modalId) {
  const titlebar = $(titlebarId);
  const modal    = $(modalId);
  if (!titlebar || !modal) return;

  let dragging = false, offsetX = 0, offsetY = 0;

  titlebar.addEventListener('mousedown', e => {
    if (e.target.closest('.titlebar-btn')) return;
    if (modal.classList.contains('maximized') ||
        modal.classList.contains('minimized')) return;
    dragging = true;
    const rect = modal.getBoundingClientRect();
    offsetX = e.clientX - rect.left;
    offsetY = e.clientY - rect.top;
    modal.style.position = 'fixed';
    modal.style.margin   = '0';
  });

  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    modal.style.left = (e.clientX - offsetX) + 'px';
    modal.style.top  = (e.clientY - offsetY) + 'px';
  });

  document.addEventListener('mouseup', () => { dragging = false; });
}

// Activar arrastre en el modal de apoderado
makeDraggable('modalApoderadoTitlebar', 'modalApoderadoInner');

// Cerrar modal al hacer clic en el backdrop
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-backdrop')) {
    cerrarModal(e.target.id);
  }
});
