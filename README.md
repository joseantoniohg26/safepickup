# SafePickup — Sistema de verificación facial

## Estructura del proyecto

```
safepickup_python/
├── app/
│   ├── main.py                   ← Servidor FastAPI (rutas, endpoints)
│   ├── ai/
│   │   ├── detector.py           ← MTCNN (detección facial)
│   │   ├── embedder.py           ← FaceNet 512D (embeddings)
│   │   └── anti_spoofing.py      ← Ensemble anti-spoofing calibrado
│   └── database/
│       ├── mysql_db.py           ← Capa de acceso a MySQL
│       └── schema.sql            ← Tablas y datos iniciales
│
├── scripts/
│   ├── iniciar_servidor.py       ← Arranca el sistema
│   ├── configurar_mysql.py       ← Crea la BD en MySQL
│   ├── verificar_instalacion.py  ← Comprueba dependencias
│   └── registrar_apoderados.py   ← Enrola desde carpeta de fotos
│
├── web/
│   ├── index.html                ← Interfaz principal (9 módulos)
│   ├── css/
│   │   └── app.css               ← Todos los estilos
│   └── js/
│       ├── app.js                ← Configuración y utilidades globales
│       ├── auth.js               ← Login y sesión
│       ├── nav.js                ← Navegación entre páginas
│       ├── modales.js            ← Ventanas flotantes
│       ├── camara.js             ← Módulo cámara en vivo
│       ├── apoderados.js         ← Módulo apoderados
│       ├── estudiantes.js        ← Módulo estudiantes
│       ├── aulas.js              ← Módulo aulas
│       └── reportes.js           ← Historial, estadísticas, configuración
│
├── data/
│   ├── fotos_apoderados/         ← Fotos para enrolamiento masivo
│   └── modelos/                  ← Pesos de IA descargados
│
└── requirements.txt              ← Dependencias Python
```

---

## Instalación paso a paso

### Paso 1: Instalar MySQL Community Server

Descarga desde: https://dev.mysql.com/downloads/mysql/

Durante la instalación:
- Selecciona "Developer Default"
- Anota la contraseña del usuario root (la necesitarás)
- Deja el puerto en 3306

**Windows:** el instalador crea el servicio automáticamente.
**Verifica que esté corriendo:** en Servicios de Windows busca "MySQL80" → debe estar "En ejecución".

### Paso 2: Instalar Python 3.11

Descarga desde: https://www.python.org/downloads/release/python-3119/
- Marca "Add Python to PATH" durante la instalación
- NO uses Python 3.13 o 3.14 (incompatibles con facenet-pytorch)

### Paso 3: Crear entorno virtual

```powershell
cd C:\proyectos\safepickup_python
py -3.11 -m venv venv
venv\Scripts\activate
```

### Paso 4: Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Esto tardará 5-15 minutos la primera vez (descarga PyTorch ~2GB).

### Paso 5: Configurar MySQL

Abre `scripts/configurar_mysql.py` y cambia la contraseña:

```python
MYSQL_PASSWORD = 'tu_contraseña_aqui'   # ← línea 44
```

Luego ejecuta:

```powershell
python scripts/configurar_mysql.py
```

Verás que crea la base de datos, las tablas y los datos iniciales.

### Paso 6: Verificar instalación

```powershell
python scripts/verificar_instalacion.py
```

Debe mostrar [OK] en todos los componentes.

### Paso 7: Iniciar el sistema

```powershell
python scripts/iniciar_servidor.py
```

El navegador se abre automáticamente en `http://localhost:8000/`

### Credenciales

- Usuario: `admin` — Contraseña: `safepickup2026`
- Usuario: `director` — Contraseña: `director123`

---

## Uso del sistema

### Registrar apoderados (forma rápida)

1. Coloca fotos en `data/fotos_apoderados/`
2. Nómbralas: `nombre_apellido_parentesco.jpg`
3. Ejecuta: `python scripts/registrar_apoderados.py`

### Registrar apoderados (desde la interfaz)

1. Ir a "Apoderados" → "Registrar apoderado"
2. Capturar foto con la cámara
3. Llenar datos
4. Guardar

### Realizar verificación

1. Ir a "Cámara en vivo"
2. Presionar "Iniciar cámara"
3. El sistema verifica automáticamente cada 2 segundos

---

## Variables de entorno (opcional)

En lugar de editar `mysql_db.py`, puedes crear un archivo `.env`:

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=tu_contraseña
MYSQL_DB=safepickup
```
