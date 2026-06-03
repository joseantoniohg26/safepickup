/**
 * SafePickup — Autenticación
 * ===========================
 * Maneja el login, logout y sesión del usuario.
 */

function hacerLogin() {
  const user = $('loginUser').value.trim();
  const pass = $('loginPass').value;
  const err  = $('loginError');

  if (CREDENCIALES[user] && CREDENCIALES[user] === pass) {
    sessionStorage.setItem('safepickup_user', user);
    mostrarApp(user);
    err.classList.remove('show');
  } else {
    err.classList.add('show');
  }
}

function mostrarApp(user) {
  $('loginScreen').style.display = 'none';
  $('app').classList.add('show');

  const nombre   = user === 'admin' ? 'Directora Sánchez' : 'Director General';
  const iniciales = nombre.split(' ').map(n => n[0]).join('').slice(0, 2);
  $('userName').textContent    = nombre;
  $('userInitials').textContent = iniciales;

  // Cargar datos iniciales
  verificarBackend();
  cargarEventosDashboard();
  cargarApoderados();
  renderAulas();
  renderEstudiantes();
}

function cerrarSesion() {
  if (!confirm('¿Cerrar sesión?')) return;
  detenerCamara();
  sessionStorage.removeItem('safepickup_user');
  $('loginScreen').style.display = 'flex';
  $('app').classList.remove('show');
  $('loginUser').value = '';
  $('loginPass').value = '';
}

// Auto-login si ya tenía sesión activa
const _userGuardado = sessionStorage.getItem('safepickup_user');
if (_userGuardado) mostrarApp(_userGuardado);

// Enter en el campo de contraseña
document.addEventListener('DOMContentLoaded', () => {
  const passInput = $('loginPass');
  if (passInput) passInput.addEventListener('keypress', e => {
    if (e.key === 'Enter') hacerLogin();
  });
});
