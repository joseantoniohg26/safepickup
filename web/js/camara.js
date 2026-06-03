/**
 * SafePickup — Módulo Cámara en vivo
 * ====================================
 * Captura frames de la webcam, los envía al backend y
 * procesa el resultado de verificación facial.
 */

// Estado de la cámara
let stream        = null;
let intervaloVerif = null;
let procesando    = false;

// ============================================================
// CONTROL DE LA CÁMARA
// ============================================================

async function iniciarCamara() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 1280, height: 720 }, audio: false
    });

    const video = $('video');
    video.srcObject = stream;

    $('cameraEmpty').style.display = 'none';
    $('recIndicator').style.display = 'flex';
    $('camLiveChip').style.display  = 'inline-flex';
    $('btnIniciar').disabled = true;
    $('btnDetener').disabled = false;

    video.addEventListener('loadedmetadata', () => {
      const c   = $('canvas-hidden');
      c.width   = video.videoWidth;
      c.height  = video.videoHeight;
    });

    intervaloVerif = setInterval(verificarFrame, INTERVALO_VERIFICACION);
  } catch (e) {
    alert('No se pudo acceder a la cámara: ' + e.message);
  }
}

function detenerCamara() {
  if (stream)         { stream.getTracks().forEach(t => t.stop()); stream = null; }
  if (intervaloVerif) { clearInterval(intervaloVerif); intervaloVerif = null; }

  const camEmpty = $('cameraEmpty');
  if (!camEmpty) return;

  camEmpty.style.display = 'flex';
  $('recIndicator').style.display = 'none';
  $('camLiveChip').style.display  = 'none';
  $('btnIniciar').disabled = false;
  $('btnDetener').disabled = true;
  $('faceBox').style.display = 'none';
  resetResultados();
}

// ============================================================
// CAPTURA Y ENVÍO AL BACKEND
// ============================================================

async function verificarFrame() {
  if (procesando) return;
  procesando = true;

  const c   = $('canvas-hidden');
  const ctx = c.getContext('2d');
  ctx.drawImage($('video'), 0, 0, c.width, c.height);
  const imagenB64 = c.toDataURL('image/jpeg', 0.85);

  try {
    const res  = await fetch(API_URL + '/api/verificar', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ imagen_base64: imagenB64 })
    });
    const data = await res.json();
    procesarResultado(data);
  } catch (e) {
    console.error('[Cámara] Error al verificar:', e);
  } finally {
    procesando = false;
  }
}

// ============================================================
// PROCESAR RESULTADO DEL BACKEND
// ============================================================

function procesarResultado(data) {
  const hora = new Date().toLocaleTimeString('es-PE', { hour12: false });

  switch (data.estado) {

    case 'sin_rostro':
      $('faceBox').style.display = 'none';
      break;

    case 'sin_apoderados':
      $('faceBox').style.display = 'none';
      break;

    case 'spoofing_detectado':
      mostrarRostro(data.coordenadas_rostro, 'warning',
        'SUPLANTACIÓN', `liveness ${data.liveness_score?.toFixed(0)}%`);
      mostrarAlerta({
        title:   'Suplantación detectada',
        subtitle: `Acceso bloqueado — ${hora}`,
        name:    'Intento de suplantación',
        meta:    data.motivos?.[0] || 'Imagen no real',
        confianza: data.liveness_score,
        isSpoof: true
      });
      break;

    case 'autorizado':
      const p = data.apoderado;
      mostrarRostro(data.coordenadas_rostro, 'success',
        p.nombre.split(' ')[0] + ' — AUTORIZADO',
        `${data.similitud_porcentual?.toFixed(1)}%`);
      mostrarAutorizado({
        nombre:     p.nombre,
        parentesco: p.parentesco,
        dni:        p.dni,
        confianza:  data.similitud_porcentual,
        hora
      });
      break;

    case 'no_autorizado':
      mostrarRostro(data.coordenadas_rostro, 'error',
        'DESCONOCIDO — ALERTA',
        `${data.similitud_porcentual?.toFixed(1)}%`);
      mostrarAlerta({
        title:    'Persona NO AUTORIZADA',
        subtitle: `Acceso denegado — ${hora}`,
        name:     'Identidad desconocida',
        meta:     'No encontrado en base de datos',
        confianza: data.similitud_porcentual,
        isSpoof:  false
      });
      break;
  }
}

// ============================================================
// VISUALIZACIÓN — CUADRO SOBRE EL ROSTRO
// ============================================================

function mostrarRostro(coords, tipo, label, conf) {
  if (!coords || coords.length !== 4) return;
  const [x1, y1, x2, y2] = coords;
  const video  = $('video');
  const c      = $('canvas-hidden');
  const vRect  = video.getBoundingClientRect();
  const scaleX = vRect.width  / c.width;
  const scaleY = vRect.height / c.height;
  const x1m    = c.width - x2;

  const box = $('faceBox');
  box.style.cssText = `
    display:block;
    left:${x1m * scaleX}px;
    top:${y1 * scaleY}px;
    width:${(x2 - x1) * scaleX}px;
    height:${(y2 - y1) * scaleY}px;
  `;
  box.className = 'face-box' + (tipo === 'error' ? ' error' : tipo === 'warning' ? ' warning' : '');
  $('faceBoxText').textContent = label;
  $('faceBoxConf').textContent = conf;
}

// ============================================================
// VISUALIZACIÓN — TARJETAS DE RESULTADO
// ============================================================

function mostrarAutorizado({ nombre, parentesco, dni, confianza, hora }) {
  $('authEmpty').style.display   = 'none';
  $('authContent').style.display = 'block';
  $('resultCardAuth').classList.add('active-success');

  $('authTitle').textContent = 'Apoderado AUTORIZADO';
  $('authSub').textContent   = `Acceso permitido — ${hora}`;

  const ini = nombre.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
  $('authAvatar').textContent = ini;
  $('authName').textContent   = nombre;
  $('authMeta').textContent   = `${parentesco} — DNI: ${dni}`;

  $('authConfVal').textContent    = confianza.toFixed(1) + '%';
  $('authConfBar').style.width    = Math.min(100, confianza) + '%';
  $('authThreshold').textContent  = confianza >= 85
    ? `Umbral 85% — Supera por ${(confianza - 85).toFixed(1)} puntos`
    : `Umbral 85%`;
}

function mostrarAlerta({ title, subtitle, name, meta, confianza, isSpoof }) {
  $('alertEmpty').style.display   = 'none';
  $('alertContent').style.display = 'block';
  $('resultCardAlert').classList.add('active-danger');

  $('alertTitle').textContent   = title;
  $('alertSub').textContent     = subtitle;
  $('alertAvatar').className    = 'person-avatar ' + (isSpoof ? 'warn' : 'danger');
  $('alertAvatar').textContent  = isSpoof ? '!' : '?';
  $('alertName').textContent    = name;
  $('alertMeta').textContent    = meta;
  $('alertConfVal').textContent = (confianza || 0).toFixed(1) + '%';
  $('alertConfBar').style.width = Math.min(100, confianza || 0) + '%';
}

function resetResultados() {
  $('authEmpty').style.display   = 'block';
  $('authContent').style.display = 'none';
  $('resultCardAuth').classList.remove('active-success');
  $('authSub').textContent       = 'Esperando verificación...';

  $('alertEmpty').style.display   = 'block';
  $('alertContent').style.display = 'none';
  $('resultCardAlert').classList.remove('active-danger');
  $('alertSub').textContent       = 'Esperando verificación...';
}

function confirmarRecojo() {
  alert('✓ Recojo confirmado y registrado en historial');
  resetResultados();
  $('faceBox').style.display = 'none';
}

function llamarDireccion() {
  alert('Notificando a dirección del colegio...');
}
