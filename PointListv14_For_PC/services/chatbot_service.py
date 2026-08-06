"""
services/chatbot_service.py
PointList v0.14.25experiment
Servicio de IA Híbrida para PointBit:
- Texto ultra-rápido impulsado por Groq Cloud (Llama 3.3 70B)
- Visión por computadora y análisis de imágenes con Google Gemini 2.0 Flash
"""

import os
import base64
import requests
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno (Ruta absoluta para compatibilidad Android/PC)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_PATH = os.path.join(os.path.dirname(_ROOT), ".env")
if os.path.exists(_ENV_PATH):
    load_dotenv(_ENV_PATH)
else:
    load_dotenv()

def get_groq_api_key(): return os.getenv("GROQ_API_KEY", "")
def get_groq_model(): return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
def get_gemini_api_key(): return os.getenv("GEMINI_API_KEY", "")
def get_gemini_model(): return os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

SYSTEM_PROMPT = """Eres PointBit, el asistente académico inteligente de la aplicación PointList.
Eres un sistema de inteligencia artificial diseñado para ayudar a los estudiantes en su camino académico.

Tu rol es ayudar a los estudiantes con:
- Técnicas de estudio y organización académica
- Explicación de conceptos de cualquier materia
- Análisis de calificaciones y rendimiento
- Planificación de horarios y tareas
- Consejos de productividad y bienestar estudiantil
- Análisis visual de apuntes, ejercicios, gráficos o tareas cuando el estudiante comparta una imagen

Reglas de comportamiento:
1. Responde siempre en el idioma del usuario (español o inglés).
2. Sé amable, motivador y empático con el estudiante.
3. Usa emojis ocasionalmente para hacer la conversación más amena.
4. Si el usuario pregunta algo fuera del ámbito académico, puedes responder brevemente pero redirige la conversación hacia temas de estudio.
5. Proporciona respuestas estructuradas con listas o pasos cuando sea apropiado.
6. Siempre termina con una pregunta de seguimiento o una motivación para el estudiante.

Versión de la aplicación: PointList v0.14.25experiment
"""


class ChatBotService:
    """
    Servicio de IA Híbrida:
    - Consultas de Texto -> Groq Cloud (Llama 3.3 70B)
    - Consultas con Imágenes -> Google Gemini 2.0 Flash
    """

    def __init__(self):
        self._groq_client = None
        self._groq_available = False
        self._gemini_available = False
        self._conversation_history: list[dict] = []
        self._initialize_clients()

    def _initialize_clients(self):
        """Inicializa los clientes de Groq y Gemini."""
        groq_key = get_groq_api_key()
        gemini_key = get_gemini_api_key()

        if groq_key:
            try:
                from openai import OpenAI
                self._groq_client = OpenAI(
                    api_key=groq_key,
                    base_url=GROQ_BASE_URL,
                )
                self._groq_available = True
            except Exception as e:
                print(f"[ChatBot] Error al inicializar Groq: {e}")

        if gemini_key:
            self._gemini_available = True

        if self._groq_available and self._gemini_available:
            print(f"[ChatBot] Arquitectura Híbrida Activa: Texto con 'Groq Cloud (Llama 3.3 70B)' | Visión con 'Google Gemini 2.0 (Visión Real)'.")
        elif self._groq_available:
            print(f"[ChatBot] Cliente Groq activo con modelo '{get_groq_model()}'.")
        elif self._gemini_available:
            print(f"[ChatBot] Cliente Google Gemini activo para Texto y Visión con '{get_gemini_model()}'.")
        else:
            print("[ChatBot] Ni GROQ_API_KEY ni GEMINI_API_KEY configuradas. Se usarán respuestas de demostración.")

    @property
    def is_available(self) -> bool:
        return self._groq_available or self._gemini_available

    def reset_conversation(self):
        self._conversation_history = []

    def _call_gemini_vision(self, prompt: str, image_path: str, custom_system_prompt: str) -> str:
        """Envía una imagen a la API de Google Gemini (Visión por Computadora)."""
        api_key = get_gemini_api_key()
        if not api_key:
            return "⚠️ No se encontró la clave `GEMINI_API_KEY` en el archivo `.env` para analizar imágenes."

        try:
            ext = os.path.splitext(image_path)[1].lower()
            mime_type = "image/jpeg"
            if ext == ".png": mime_type = "image/png"
            elif ext == ".webp": mime_type = "image/webp"
            elif ext == ".gif": mime_type = "image/gif"

            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            user_prompt = prompt if prompt else "Analiza esta imagen y ayuda al estudiante con su contenido académico."
            full_instruction = f"{custom_system_prompt}\n\n[Pregunta del estudiante]: {user_prompt}"

            models_to_try = [get_gemini_model(), "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"]
            for model in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": full_instruction},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": img_b64
                                }
                            }
                        ]
                    }]
                }

                resp = requests.post(url, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                elif resp.status_code == 404:
                    continue
                else:
                    print(f"[ChatBot] Gemini API error ({model}): {resp.status_code} - {resp.text}")

            return "⚠️ Ocurrió un inconveniente al comunicarse con la API de Google Gemini para la lectura de la imagen."

        except Exception as e:
            return f"⚠️ Error al procesar la imagen con Gemini: {str(e)}"

    def send_message(self, user_message: str, uid=None, session_id=None, history: list = None, max_tokens: int = 2000, image_path: str = None, document_path: str = None, attached_file: dict = None, attached_files: list = None) -> str:
        """
        Envía un mensaje al chatbot con soporte para múltiples archivos adjuntos simultáneos (Documentos + Imágenes).
        """
        from services.navigation_service import NavigationController
        from utils.document_reader import extract_text_from_file

        lang = NavigationController.cache.get("language", "es")

        lang_names = {
            "es": "español",
            "en": "English",
            "pt": "português",
            "it": "italiano",
            "de": "Deutsch",
            "fr": "français",
            "zh": "中文 (简体)",
            "zh-TW": "中文 (繁體)",
        }
        target_lang = lang_names.get(lang, "español")
        custom_system_prompt = SYSTEM_PROMPT + f"\n[IMPORTANTE] Responde obligatoriamente en el idioma {target_lang}."

        # Normalizar lista de archivos adjuntos
        all_attached = []
        if attached_files and isinstance(attached_files, list):
            all_attached.extend(attached_files)
        elif attached_file and isinstance(attached_file, dict):
            all_attached.append(attached_file)

        images_to_process = []
        if image_path and os.path.exists(image_path):
            images_to_process.append(image_path)

        documents_to_process = []
        if document_path and os.path.exists(document_path):
            documents_to_process.append(document_path)

        for item in all_attached:
            p = item.get("path")
            if not p or not os.path.exists(p): continue
            t = item.get("type")
            if t == "imagen":
                if p not in images_to_process:
                    images_to_process.append(p)
            else:
                if p not in documents_to_process:
                    documents_to_process.append(p)

        # 1. Procesar todos los documentos adjuntos
        doc_contents = []
        for doc_p in documents_to_process:
            doc_res = extract_text_from_file(doc_p)
            if doc_res["ok"]:
                fname = doc_res["filename"]
                words = doc_res["num_words"]
                txt = doc_res["text"]
                doc_contents.append(f"--- [DOCUMENTO ADJUNTO: {fname} ({words} palabras)] ---\n{txt}\n--- [FIN DE {fname}] ---")
            else:
                doc_contents.append(f"⚠️ Error al leer '{os.path.basename(doc_p)}': {doc_res.get('error')}")

        if doc_contents:
            joined_docs = "\n\n".join(doc_contents)
            user_instruction = user_message if user_message else "Por favor, analiza y procesa los documentos adjuntos."
            user_message = f"{user_instruction}\n\n{joined_docs}"

        # 2. Si hay imágenes, procesar con Gemini Visión
        if images_to_process:
            primary_img = images_to_process[0]
            if self._gemini_available:
                return self._call_gemini_vision(user_message, primary_img, custom_system_prompt)
            else:
                return "⚠️ El análisis de imágenes requiere configurar `GEMINI_API_KEY` en el archivo `.env`."

        # 3. Si solo hay texto o documentos, procesar con Groq Cloud (Llama 3.3 70B - 128K Context)
        if not self._groq_available and self._gemini_available:
            return self._call_gemini_vision(user_message, "", custom_system_prompt)

        if not self._groq_available:
            return self._demo_response(user_message)

        current_history = []
        if history:
            for h in history:
                current_history.append({"role": "user", "content": h["pregunta"]})
                current_history.append({"role": "assistant", "content": h["respuesta"]})
        else:
            current_history = self._conversation_history

        current_history.append({"role": "user", "content": user_message})
        messages = [{"role": "system", "content": custom_system_prompt}] + current_history[-10:]

        try:
            response = self._groq_client.chat.completions.create(
                model=get_groq_model(),
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                stream=False,
            )

            assistant_message = response.choices[0].message.content

            self._conversation_history.append({
                "role": "assistant",
                "content": assistant_message,
            })

            if len(self._conversation_history) > 20:
                self._conversation_history = self._conversation_history[-20:]

            return assistant_message

        except Exception as e:
            error_msg = f"Error al comunicarse con Groq: {str(e)}"
            print(f"[ChatBot] {error_msg}")
            return f"⚠️ {error_msg}\n\nPor favor, verifica tu conexión a internet y las claves de API."

    def _demo_response(self, user_message: str) -> str:
        """Respuesta de demostración si no hay claves de API en .env."""
        from services.navigation_service import NavigationController
        lang = NavigationController.cache.get("language", "es")
        message_lower = user_message.lower()

        if lang == "en":
            return (
                "Hello! 👋 I am **PointBit**, your academic assistant.\n\n"
                "To activate my full hybrid AI capabilities (Groq for Text + Gemini for Vision), "
                "add `GROQ_API_KEY` and `GEMINI_API_KEY` to your `.env` file.\n\n"
                "How can I help you today? 📚"
            )
        else:
            return (
                "¡Hola! 👋 Soy **PointBit**, tu asistente académico de PointList.\n\n"
                "Para activarme completamente con **IA Híbrida** (Groq para Texto + Gemini 2.0 para Visión), "
                "agrega tus claves `GROQ_API_KEY` y `GEMINI_API_KEY` en el archivo `.env`.\n\n"
                "¿En qué puedo ayudarte hoy? 📚"
            )

    def get_history(self) -> list[dict]:
        return self._conversation_history.copy()


chatbot = ChatBotService()
