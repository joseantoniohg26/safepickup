"""
SafePickup — Servidor FastAPI principal
========================================
"""

import base64
import io
import sys
import traceback
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.ai.detector     import DetectorFacial
from app.ai.embedder     import GeneradorEmbeddings
from app.ai.anti_spoofing import DetectorAntiSpoofing
from app.database        import mysql_db as db


app = FastAPI(
    title="SafePickup API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RUTA_WEB = Path(__file__).parent.parent / "web"
if RUTA_WEB.exists():
    ruta_css = RUTA_WEB / "css"
    ruta_js  = RUTA_WEB / "js"
    if ruta_css.exists():
        app.mount("/css", StaticFiles(directory=str(ruta_css)), name="css")
    if ruta_js.exists():
        app.mount("/js", StaticFiles(directory=str(ruta_js)), name="js")


print("=" * 60)
print("  SafePickup v2.0 — Iniciando motor de IA")
print("=" * 60)

print("Cargando MTCNN (deteccion facial)...")
detector = DetectorFacial()
print(f"  [OK] MTCNN en {detector.device.upper()}")

print("Cargando FaceNet (embeddings 512D)...")
embedder = GeneradorEmbeddings()
print(f"  [OK] FaceNet en {embedder.device.upper()}")

print("Cargando anti-spoofing...")
anti_spoof = DetectorAntiSpoofing()
print(f"  [OK] Anti-spoofing listo")

print("Verificando conexion a MySQL...")
if db.verificar_conexion():
    print("  [OK] MySQL conectado")
    db.inicializar_schema()
else:
    print("  [WARN] MySQL no disponible")

print("=" * 60)


class ImagenRequest(BaseModel):
    imagen_base64: str

class NuevoApoderadoRequest(BaseModel):
    nombre:        str
    parentesco:    str
    dni:           str
    imagen_base64: str
    telefono:      str = None
    estudiante_id: int = None

class NuevoEstudianteRequest(BaseModel):
    nombres:    str
    apellidos:  str
    fecha_nac:  str
    sexo:       str
    aula_id:    int
    seccion:    str
    turno:      str
    matricula:  str
    dni:        str = None

class NuevaAulaRequest(BaseModel):
    nombre:    str
    edad:      int
    secciones: list
    color:     str = 'blue'

class RecojoRequest(BaseModel):
    apoderado_id:     int = None
    apoderado_nombre: str = None
    confianza:        float = None

class LoginRequest(BaseModel):
    usuario:  str
    password: str


def base64_a_cv2(imagen_base64: str):
    if ',' in imagen_base64:
        imagen_base64 = imagen_base64.split(',')[1]
    imagen_bytes = base64.b64decode(imagen_base64)
    imagen_pil   = Image.open(io.BytesIO(imagen_bytes)).convert('RGB')
    imagen_array = np.array(imagen_pil)
    return cv2.cvtColor(imagen_array, cv2.COLOR_RGB2BGR)


@app.get("/")
@app.get("/app")
def servir_frontend():
    html_path = RUTA_WEB / "index.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return JSONResponse({"error": "index.html no encontrado"}, status_code=404)


@app.post("/api/login")
def login(req: LoginRequest):
    user = db.verificar_usuario(req.usuario, req.password)
    if user:
        return {"ok": True, "usuario": user['usuario'], "nombre": user['nombre'], "rol": user['rol']}
    return JSONResponse({"ok": False, "detail": "Usuario o contraseña incorrectos"}, status_code=401)


@app.get("/api/estado")
def estado_sistema():
    try:
        mysql_ok  = db.verificar_conexion()
        stats     = db.estadisticas_completas() if mysql_ok else {}
        return {
            "sistema":     "activo",
            "mysql":       mysql_ok,
            "dispositivo": detector.device.upper(),
            "apoderados_registrados": stats.get("apoderados_registrados", 0),
            "estudiantes_registrados": stats.get("estudiantes_registrados", 0),
            "eventos_hoy":  stats.get("eventos_hoy", {
                "autorizados": 0, "recojos": 0, "rechazados": 0, "spoofing": 0, "total": 0
            })
        }
    except Exception as e:
        print(f"[ERROR /api/estado] {e}")
        return JSONResponse(
            {"sistema": "error", "mensaje": str(e),
             "apoderados_registrados": 0, "estudiantes_registrados": 0,
             "eventos_hoy": {"autorizados":0,"rechazados":0,"spoofing":0,"total":0}},
            status_code=200
        )


@app.post("/api/verificar")
def verificar_rostro(req: ImagenRequest):
    try:
        try:
            imagen = base64_a_cv2(req.imagen_base64)
        except Exception as e:
            return JSONResponse({"estado": "error", "detail": f"Imagen invalida: {e}"}, status_code=400)

        rostro = detector.detectar_un_rostro(imagen)
        if rostro is None:
            return {"estado": "sin_rostro", "mensaje": "No se detecto ningun rostro"}

        x1, y1, x2, y2 = rostro['coordenadas']
        x1 = max(0, x1); y1 = max(0, y1)
        x2 = min(imagen.shape[1], x2); y2 = min(imagen.shape[0], y2)
        recorte = imagen[y1:y2, x1:x2]

        spoof = anti_spoof.verificar(recorte)
        if not spoof['es_real']:
            try:
                db.registrar_evento(
                    tipo='spoofing_detectado',
                    motivo='; '.join(spoof['motivos'])
                )
            except Exception as e:
                print(f"[WARN] No se pudo registrar evento spoofing: {e}")
            return {
                "estado":              "spoofing_detectado",
                "mensaje":             "Intento de suplantacion detectado",
                "liveness_score":      spoof['liveness_score'],
                "motivos":             spoof['motivos'],
                "coordenadas_rostro":  [x1, y1, x2, y2],
                "confianza_deteccion": float(rostro['confianza'])
            }

        embedding = embedder.generar(rostro['rostro_tensor'])

        apoderados = db.obtener_apoderados_con_embedding()
        if not apoderados:
            return {
                "estado":             "sin_apoderados",
                "mensaje":            "No hay apoderados registrados",
                "coordenadas_rostro": [x1, y1, x2, y2]
            }

        resultado = embedder.buscar_coincidencia(embedding, apoderados)

        if resultado['coincidencia']:
            match = resultado['mejor_match']
            try:
                db.registrar_evento(
                    tipo='autorizado',
                    apoderado_id=match['id_apoderado'],
                    nombre=match['nombre'],
                    confianza=resultado['similitud_porcentual']
                )
            except Exception as e:
                print(f"[WARN] No se pudo registrar evento autorizado: {e}")

            return {
                "estado":   "autorizado",
                "mensaje":  "Apoderado verificado",
                "apoderado": {
                    "id":           match['id_apoderado'],
                    "nombre":       match['nombre'],
                    "parentesco":   match.get('parentesco', ''),
                    "dni":          match.get('dni', ''),
                    "estudiante_id": match.get('estudiante_id')
                },
                "distancia":           resultado['distancia'],
                "similitud_porcentual": resultado['similitud_porcentual'],
                "liveness_score":      spoof['liveness_score'],
                "coordenadas_rostro":  [x1, y1, x2, y2],
                "confianza_deteccion": float(rostro['confianza'])
            }
        else:
            try:
                db.registrar_evento(tipo='no_autorizado', confianza=resultado['similitud_porcentual'])
            except Exception as e:
                print(f"[WARN] No se pudo registrar evento no_autorizado: {e}")

            return {
                "estado":   "no_autorizado",
                "mensaje":  "Persona no registrada",
                "distancia":           resultado['distancia'],
                "similitud_porcentual": resultado['similitud_porcentual'],
                "liveness_score":      spoof['liveness_score'],
                "coordenadas_rostro":  [x1, y1, x2, y2],
                "confianza_deteccion": float(rostro['confianza'])
            }

    except Exception as e:
        print(f"[ERROR /api/verificar] {e}")
        print(traceback.format_exc())
        return JSONResponse({"estado": "error", "detail": str(e)}, status_code=500)


@app.get("/api/apoderados")
def listar_apoderados():
    try:
        apoderados = db.listar_apoderados()
        return {"apoderados": apoderados, "total": len(apoderados)}
    except Exception as e:
        print(f"[ERROR /api/apoderados] {e}")
        return JSONResponse({"apoderados": [], "total": 0, "detail": str(e)}, status_code=200)


@app.post("/api/apoderados/registrar")
def registrar_apoderado(req: NuevoApoderadoRequest):
    """
    Registra un nuevo apoderado. SIEMPRE devuelve JSON, nunca un error 500 crudo.
    """
    try:
        # Paso 1: Decodificar imagen
        try:
            imagen = base64_a_cv2(req.imagen_base64)
        except Exception as e:
            return JSONResponse({"detail": f"Imagen invalida: {e}"}, status_code=400)

        # Paso 2: Detectar rostro
        rostro = detector.detectar_un_rostro(imagen)

        if rostro is None:
            gris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
            brillo = float(np.mean(gris))
            contraste = float(np.std(gris))

            if brillo < 60:
                mensaje = "La foto esta muy oscura. Encienda mas luz."
            elif brillo > 200:
                mensaje = "La foto esta sobreexpuesta."
            elif contraste < 30:
                mensaje = "Poco contraste. Evite el contraluz."
            else:
                mensaje = "No se detecto rostro. Coloquese de frente a la camara."

            return JSONResponse({"detail": mensaje}, status_code=400)

        # Paso 3: Validar calidad
        if rostro['confianza'] < 0.85:
            return JSONResponse({
                "detail": f"Calidad baja ({rostro['confianza']:.0%}). Acerquese mas a la camara."
            }, status_code=400)

        # Paso 4: Generar embedding
        try:
            embedding = embedder.generar(rostro['rostro_tensor'])
        except Exception as e:
            print(f"[ERROR embedding] {e}")
            print(traceback.format_exc())
            return JSONResponse({"detail": f"Error generando embedding: {e}"}, status_code=500)

        # Paso 5: Guardar en MySQL
        try:
            id_nuevo  = db.registrar_apoderado(
                nombre=req.nombre,
                parentesco=req.parentesco,
                dni=req.dni,
                embedding=embedding,
                estudiante_id=req.estudiante_id,
                telefono=req.telefono
            )
        except Exception as e:
            print(f"[ERROR MySQL registrar_apoderado] {e}")
            print(traceback.format_exc())
            return JSONResponse({
                "detail": f"Error al guardar en MySQL: {e}"
            }, status_code=500)

        print(f"[OK Registro] {req.nombre} guardado con ID {id_nuevo} (confianza {rostro['confianza']:.0%})")

        return {
            "estado":              "registrado",
            "mensaje":             f"Apoderado {req.nombre} registrado",
            "id_apoderado":        id_nuevo,
            "confianza_deteccion": float(rostro['confianza'])
        }

    except Exception as e:
        # ÚLTIMO RECURSO: cualquier error inesperado se convierte en JSON
        print(f"[ERROR FATAL /api/apoderados/registrar] {e}")
        print(traceback.format_exc())
        return JSONResponse({
            "detail": f"Error interno del servidor: {str(e)}"
        }, status_code=500)


@app.delete("/api/apoderados/{id_apoderado}")
def eliminar_apoderado(id_apoderado: int):
    try:
        db.eliminar_apoderado(id_apoderado)
        return {"estado": "eliminado", "id": id_apoderado}
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


class EditarApoderadoRequest(BaseModel):
    nombre:        str
    parentesco:    str
    dni:           str
    telefono:      str = None
    estudiante_id: int = None


@app.put("/api/apoderados/{id_apoderado}")
def editar_apoderado_endpoint(id_apoderado: int, req: EditarApoderadoRequest):
    try:
        db.editar_apoderado(
            id_apoderado=id_apoderado,
            nombre=req.nombre,
            dni=req.dni,
            telefono=req.telefono,
            parentesco=req.parentesco,
            estudiante_id=req.estudiante_id
        )
        return {"estado": "actualizado", "id": id_apoderado}
    except Exception as e:
        print(f"[ERROR editar_apoderado] {e}")
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.get("/api/estudiantes")
def listar_estudiantes():
    try:
        return {"estudiantes": db.listar_estudiantes()}
    except Exception as e:
        return JSONResponse({"estudiantes": [], "detail": str(e)}, status_code=200)


@app.post("/api/estudiantes/registrar")
def registrar_estudiante(req: NuevoEstudianteRequest):
    try:
        id_nuevo = db.registrar_estudiante(
            nombres=req.nombres, apellidos=req.apellidos,
            fecha_nac=req.fecha_nac, sexo=req.sexo,
            aula_id=req.aula_id, seccion=req.seccion,
            turno=req.turno, matricula=req.matricula, dni=req.dni
        )
        return {"estado": "registrado", "id_estudiante": id_nuevo}
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.delete("/api/estudiantes/{id_estudiante}")
def eliminar_estudiante(id_estudiante: int):
    try:
        db.eliminar_estudiante(id_estudiante)
        return {"estado": "eliminado", "id": id_estudiante}
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.put("/api/estudiantes/{id_estudiante}/recoger")
def recoger_estudiante(id_estudiante: int, req: RecojoRequest):
    """Confirma el recojo de un estudiante y registra el evento en historial."""
    try:
        db.marcar_recogido(id_estudiante)
        db.registrar_evento(
            tipo='recojo_confirmado',
            apoderado_id=req.apoderado_id,
            nombre=req.apoderado_nombre,
            confianza=req.confianza,
            motivo='Recojo confirmado por personal'
        )
        return {"estado": "confirmado", "id": id_estudiante}
    except Exception as e:
        print(f"[ERROR recoger_estudiante] {e}")
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.put("/api/estudiantes/{id_estudiante}")
def editar_estudiante_endpoint(id_estudiante: int, req: NuevoEstudianteRequest):
    try:
        db.editar_estudiante(
            id_estudiante=id_estudiante,
            nombres=req.nombres, apellidos=req.apellidos,
            fecha_nac=req.fecha_nac, sexo=req.sexo,
            aula_id=req.aula_id, seccion=req.seccion,
            turno=req.turno, matricula=req.matricula, dni=req.dni
        )
        return {"estado": "actualizado", "id": id_estudiante}
    except Exception as e:
        print(f"[ERROR editar_estudiante] {e}")
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.get("/api/aulas")
def listar_aulas():
    try:
        return {"aulas": db.listar_aulas()}
    except Exception as e:
        return JSONResponse({"aulas": [], "detail": str(e)}, status_code=200)


@app.post("/api/aulas/registrar")
def registrar_aula(req: NuevaAulaRequest):
    try:
        id_nuevo = db.registrar_aula(
            nombre=req.nombre, edad=req.edad,
            secciones=req.secciones, color=req.color
        )
        return {"estado": "creada", "id_aula": id_nuevo}
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.put("/api/aulas/{id_aula}")
def editar_aula_endpoint(id_aula: int, req: NuevaAulaRequest):
    try:
        db.editar_aula(
            id_aula=id_aula,
            nombre=req.nombre, edad=req.edad,
            secciones=req.secciones, color=req.color
        )
        return {"estado": "actualizada", "id": id_aula}
    except Exception as e:
        print(f"[ERROR editar_aula] {e}")
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.delete("/api/aulas/{id_aula}")
def eliminar_aula_endpoint(id_aula: int):
    try:
        db.eliminar_aula(id_aula)
        return {"estado": "eliminada", "id": id_aula}
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=500)


@app.get("/api/eventos")
def listar_eventos(limite: int = 50, fecha: str = None, tipo: str = None):
    try:
        eventos = db.listar_eventos(limite=limite, fecha=fecha, tipo=tipo)
        return {"eventos": eventos, "total": len(eventos)}
    except Exception as e:
        return JSONResponse({"eventos": [], "total": 0, "detail": str(e)}, status_code=200)


@app.get("/api/estadisticas")
def estadisticas():
    try:
        return db.estadisticas_completas()
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=200)


if __name__ == "__main__":
    import os
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)), log_level="info")