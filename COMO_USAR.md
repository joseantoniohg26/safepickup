# SafePickup - Instrucciones de uso (Fase 1: Integración)

## ¿Qué es esto?

Has llegado a la **Fase 1 de integración**: tu HTML conectado al motor Python real.

Esto significa que ya NO es una simulación. La cámara captura tu rostro,
el backend Python ejecuta MTCNN + FaceNet + Anti-spoofing, y el resultado
se muestra en pantalla.

---

## Archivos que recibes en este avance

```
app/
├── main.py                              ← NUEVO: Servidor FastAPI
└── database/
    ├── __init__.py                      ← NUEVO
    └── json_db.py                       ← NUEVO: Base de datos en JSON

scripts/
├── iniciar_sistema.py                   ← NUEVO: Arranca todo
└── registrar_apoderados.py              ← NUEVO: Para enrolar personas

web/
└── index.html                           ← NUEVO: HTML conectado al backend
```

---

## PASO 1: Copiar los archivos a tu proyecto

Desde el ZIP descargado, copia los archivos a estas ubicaciones EXACTAS:

| Archivo en el ZIP | Destino en tu proyecto |
|---|---|
| `app/main.py` | `C:\proyectos\safepickup_python\app\main.py` |
| `app/database/__init__.py` | `C:\proyectos\safepickup_python\app\database\__init__.py` |
| `app/database/json_db.py` | `C:\proyectos\safepickup_python\app\database\json_db.py` |
| `scripts/iniciar_sistema.py` | `C:\proyectos\safepickup_python\scripts\iniciar_sistema.py` |
| `scripts/registrar_apoderados.py` | `C:\proyectos\safepickup_python\scripts\registrar_apoderados.py` |
| `web/index.html` | `C:\proyectos\safepickup_python\web\index.html` |

**IMPORTANTE:** la carpeta `app/database/` y la carpeta `web/` son NUEVAS.
Tienes que crearlas si no existen.

---

## PASO 2: Preparar fotos de apoderados de prueba

### Opción A: Solo tú en distintos ángulos (recomendada para hoy)

Toma 3 fotos tuyas con tu celular:
- `carmen_mamani_madre.jpg` (foto tuya de frente, sonriendo)
- `jose_ramirez_padre.jpg` (foto tuya de perfil 3/4, expresión neutra)
- `ana_quispe_tutora.jpg` (foto tuya con lentes, otra expresión)

Aunque sean tus fotos, el sistema las tratará como **3 personas distintas**
porque la verificación falla si los rostros son muy iguales.

### Opción B: Familiares reales

Mejor opción si quieres una demo más impactante:
- `juan_perez_padre.jpg` (foto de tu papá o un hombre)
- `maria_lopez_madre.jpg` (foto de tu mamá o una mujer)
- `ana_garcia_tutora.jpg` (foto de tu hermana, una amiga, etc.)

**Reglas para las fotos:**
- Rostro de frente, bien iluminado
- Sin gorras, lentes oscuros ni mascarillas
- Calidad clara (no borrosa)
- Formato JPG o PNG
- Nombre del archivo: `nombre_apellido_parentesco.jpg`

### Dónde colocar las fotos

Crea esta carpeta y mete las fotos ahí:
```
C:\proyectos\safepickup_python\data\fotos_apoderados\
```

---

## PASO 3: Registrar los apoderados (enrolamiento)

Abre PowerShell en `C:\proyectos\safepickup_python` y activa el entorno:

```
venv\Scripts\activate
```

Ejecuta el script de registro:

```
python scripts/registrar_apoderados.py
```

Esto procesará cada foto, generará el embedding facial y guardará a la
persona en la base de datos JSON.

Verás algo así:

```
Procesando: carmen_mamani_madre.jpg
  Nombre: Carmen Mamani
  Parentesco: Madre
  Confianza detección: 99.87%
  Embedding generado (512D)
  [OK] Registrado con ID 1, DNI 70013700
```

Si ves esto, todo va bien.

---

## PASO 4: Iniciar el sistema

```
python scripts/iniciar_sistema.py
```

Esto hace 3 cosas:
1. Carga todos los modelos de IA (5-10 segundos)
2. Inicia el servidor FastAPI en http://localhost:8000
3. Abre el navegador automáticamente con la página principal

Verás esto en la terminal:

```
╔══════════════════════════════════════════════════════════╗
║              SafePickup - Sistema en marcha              ║
╠══════════════════════════════════════════════════════════╣
║  Backend:  http://localhost:8000                         ║
║  Frontend: http://localhost:8000/app                     ║
║  API docs: http://localhost:8000/docs                    ║
╚══════════════════════════════════════════════════════════╝
```

Si el navegador no abre solo, ve manualmente a:
**http://localhost:8000/app**

---

## PASO 5: Probar el sistema completo

1. **Presiona el botón "▶ Iniciar cámara"** en la página
2. **Permite el acceso a la cámara** cuando el navegador pregunte
3. **Mírate a la cámara** y espera 2 segundos
4. Verás en la pantalla:
   - Cuadro verde sobre tu rostro
   - "ACCESO AUTORIZADO" con tu nombre
   - Métricas: similitud, distancia, tiempo, liveness

5. **Prueba con foto en celular**:
   - Muestra una foto cualquiera en la pantalla de tu celular
   - El sistema debe detectar "INTENTO DE SUPLANTACIÓN"

6. **Prueba con otra persona**:
   - Que se pare alguien que NO esté registrado
   - El sistema debe decir "ACCESO DENEGADO"

---

## Endpoints disponibles (para programadores)

El sistema expone esta API REST:

| Endpoint | Método | Descripción |
|---|---|---|
| `/api/estado` | GET | Estado del sistema |
| `/api/verificar` | POST | Verificar un rostro |
| `/api/apoderados` | GET | Listar apoderados |
| `/api/apoderados/registrar` | POST | Registrar nuevo apoderado |
| `/api/eventos` | GET | Historial de eventos |
| `/api/estadisticas` | GET | Estadísticas para dashboard |

Documentación interactiva en: **http://localhost:8000/docs**

---

## Solución de problemas

### "No se pudo acceder a la cámara"
- Cierra otros programas que estén usando la cámara (Zoom, Teams, etc.)
- En el navegador, permite el acceso a la cámara para localhost
- Prueba en Chrome o Edge (Firefox a veces da problemas)

### "Sin conexión" en la barra superior
- Verifica que el servidor Python esté corriendo en la terminal
- No debe haber errores en la terminal
- Refresca la página (F5)

### El sistema no me reconoce aunque estoy registrado
- Verifica la iluminación (que sea similar a la foto de registro)
- Mírate más cerca de la cámara
- Si la distancia es 0.6-0.9, estás en zona ambigua. Re-registra con otra foto.

### Detecta SPOOF cuando soy yo real
- Esto puede pasar si tu cámara tiene mucha luz directa
- Calibra los umbrales en `app/ai/anti_spoofing.py` (ya hicimos esto)
- Usa modo debug (`d`) para ver los valores y ajustar

---

## Próximo paso (Fase 2)

Una vez que la Fase 1 funcione:

- Conectar las páginas de registro de apoderado y estudiante
- Conectar el historial real al frontend
- Conectar dashboard con estadísticas reales
- Conectar gestión completa

Pero primero, asegúrate de que la Fase 1 funciona sin errores.

---

## Resumen rápido (para sustentación)

> "El sistema utiliza una arquitectura cliente-servidor con FastAPI como
> backend y HTML/JavaScript como frontend. El frontend captura frames de
> la cámara web y los envía mediante peticiones HTTP al backend, que
> ejecuta el pipeline de IA (MTCNN + Anti-spoofing + FaceNet) y devuelve
> el resultado de la verificación en formato JSON. La comunicación es
> asíncrona y se realiza cada 2 segundos, permitiendo procesamiento en
> tiempo casi real sin saturar la CPU."

Eso es lo que vas a decir en sustentación.
