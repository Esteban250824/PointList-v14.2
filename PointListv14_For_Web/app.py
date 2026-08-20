"""
app.py - Servidor Backend Flask y API REST para PointList v14 Web
"""

import os
import json
import hashlib
import uuid
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

PORT = int(os.getenv("PORT", 5000))
HOST = os.getenv("HOST", "0.0.0.0")

# Almacenamiento en memoria/fallback si no hay BD externa
USERS_DB = {}
NOTES_DB = []
EVENTS_DB = []
MESSAGES_DB = [
    {
        "id": 1,
        "emisor": "Prof. Carlos Mendoza",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Carlos",
        "contenido": "Recuerden revisar el capítulo 4 de Física para la entrega del viernes.",
        "timestamp": "10:30 AM",
        "es_mio": False
    },
    {
        "id": 2,
        "emisor": "Ana Martínez",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Ana",
        "contenido": "¿Alguien tiene los apuntes de la clase de Química?",
        "timestamp": "11:15 AM",
        "es_mio": False
    }
]
CHATBOT_HISTORIAL = []

def hash_password(password, salt=None):
    if not salt:
        salt = uuid.uuid4().hex
    pwd_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return pwd_hash, salt

# ─── Rutas Estáticas ────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    if os.path.exists(path):
        return send_from_directory(".", path)
    return send_from_directory(".", "index.html")

# ─── API Auth ───────────────────────────────────────────────────────────────
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    nombre = data.get("nombre", "").strip()
    rol = data.get("rol", "estudiante")

    if not email or not password or not nombre:
        return jsonify({"success": False, "error": "Todos los campos son requeridos"}), 400

    if email in USERS_DB:
        return jsonify({"success": False, "error": "El usuario ya existe"}), 400

    pwd_hash, salt = hash_password(password)
    user_data = {
        "id": len(USERS_DB) + 1,
        "email": email,
        "nombre_usuario": nombre,
        "rol": rol,
        "password_hash": pwd_hash,
        "salt": salt,
        "photo_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={nombre}",
        "bio": "Estudiante apasionado por el aprendizaje continuo.",
        "telefono": "+57 300 123 4567",
        "ubicacion": "Bogotá, Colombia",
        "sitio_web": "https://pointlist.edu"
    }
    USERS_DB[email] = user_data
    return jsonify({"success": True, "user": user_data})

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = USERS_DB.get(email)
    if not user:
        # Usuario demo por defecto
        if email == "demo@pointlist.com" and password == "123456":
            user = {
                "id": 1,
                "email": "demo@pointlist.com",
                "nombre_usuario": "Juan Esteban",
                "rol": "estudiante",
                "photo_url": "assets/figma_assets/logo.png",
                "bio": "Estudiante de Ingeniería de Software.",
                "telefono": "+57 310 987 6543",
                "ubicacion": "Medellín, Colombia",
                "sitio_web": "https://github.com/pointlist"
            }
            USERS_DB[email] = user
            return jsonify({"success": True, "user": user})
        return jsonify({"success": False, "error": "Credenciales inválidas"}), 401

    pwd_hash, _ = hash_password(password, user.get("salt"))
    if pwd_hash != user.get("password_hash") and user.get("email") != "demo@pointlist.com":
        return jsonify({"success": False, "error": "Contraseña incorrecta"}), 401

    return jsonify({"success": True, "user": user})

# ─── API Calificaciones / Notas ─────────────────────────────────────────────
@app.route("/api/notes", methods=["GET", "POST", "DELETE"])
def handle_notes():
    if request.method == "GET":
        return jsonify({"success": True, "notes": NOTES_DB})
    elif request.method == "POST":
        data = request.json or {}
        note = {
            "id": len(NOTES_DB) + 1,
            "asignatura": data.get("asignatura", "General"),
            "calificacion": float(data.get("calificacion", 0.0)),
            "fecha": data.get("fecha", "2026-08-20"),
            "comentarios": data.get("comentarios", "")
        }
        NOTES_DB.append(note)
        return jsonify({"success": True, "note": note})

# ─── API Calendario / Agenda ────────────────────────────────────────────────
@app.route("/api/calendar", methods=["GET", "POST"])
def handle_calendar():
    if request.method == "GET":
        return jsonify({"success": True, "events": EVENTS_DB})
    elif request.method == "POST":
        data = request.json or {}
        event = {
            "id": len(EVENTS_DB) + 1,
            "titulo": data.get("titulo", "Nuevo Evento"),
            "descripcion": data.get("descripcion", ""),
            "fecha_inicio": data.get("fecha_inicio", ""),
            "fecha_fin": data.get("fecha_fin", ""),
            "tipo_evento": data.get("tipo_evento", "General"),
            "prioridad": data.get("prioridad", "normal"),
            "completado": False
        }
        EVENTS_DB.append(event)
        return jsonify({"success": True, "event": event})

# ─── API Chatbot PointBit ────────────────────────────────────────────────────
@app.route("/api/chatbot/ask", methods=["POST"])
def chatbot_ask():
    data = request.json or {}
    pregunta = data.get("pregunta", "").strip()
    api_key = os.getenv("OPENAI_API_KEY")

    respuesta = ""
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres PointBit, un asistente de estudio educativo inteligente de la plataforma PointList v14. Responde con claridad, empatía y formato Markdown útil para estudiantes."},
                    {"role": "user", "content": pregunta}
                ]
            )
            respuesta = completion.choices[0].message.content
        except Exception as e:
            respuesta = f"Hubo un detalle con la conexión a OpenAI: {str(e)}. Pero como tu asistente PointBit, ¡estoy aquí para ayudarte! En qué más te asesoro?"
    else:
        # Respuestas educacionales inteligentes predefinidas
        p_lower = pregunta.lower()
        if "pomodoro" in p_lower:
            respuesta = "La **Técnica Pomodoro** consiste en alternar 25 minutos de estudio enfocado sin distracciones con 5 minutos de descanso corto. ¡Después de 4 bloques, toma un descanso largo de 15 a 30 minutos!"
        elif "feynman" in p_lower:
            respuesta = "El **Método Feynman** consiste en: 1) Elegir un concepto. 2) Explicárselo a un niño de 10 años en lenguaje sencillo. 3) Identificar lagunas de conocimiento. 4) Simplificar y usar analogías."
        elif "nota" in p_lower or "promedio" in p_lower or "calificacion" in p_lower:
            respuesta = "Para mejorar tu **promedio general en PointList**, te recomiendo organizar tus entregas en el Calendario, usar repaso espaciado (*Active Recall*) y revisar el desglose de calificaciones por asignatura."
        else:
            respuesta = f"¡Excelente pregunta sobre **{pregunta}**!\n\nPara dominar este tema eficientemente en **PointList v14**:\n\n1. **Aplica Active Recall**: Ponte a prueba antes de releer los apuntos.\n2. **Usa bloques Pomodoro**: Mantén sesiones de 25m de concentración profunda.\n3. **Crea un mapa conceptual**: Conecta las ideas clave de tu materia.\n\n¿Deseas que profundicemos en algún punto específico?"

    msg_obj = {"pregunta": pregunta, "respuesta": respuesta, "timestamp": "Ahora"}
    CHATBOT_HISTORIAL.append(msg_obj)
    return jsonify({"success": True, "respuesta": respuesta, "historial": CHATBOT_HISTORIAL})

if __name__ == "__main__":
    print(f"🚀 Servidor PointList Web iniciado exitosamente en http://localhost:{PORT}")
    app.run(host=HOST, port=PORT, debug=True)
