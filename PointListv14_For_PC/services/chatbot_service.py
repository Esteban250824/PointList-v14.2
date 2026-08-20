"""
services/chatbot_service.py
PointList v0.14.25experiment
Servicio de IA Híbrida para PointBit:
- Texto ultra-rápido impulsado por Groq Cloud (groq/compound)
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
def get_groq_model(): return os.getenv("GROQ_MODEL", "groq/compound")
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
    - Consultas de Texto -> Groq Cloud (groq/compound)
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
                from groq import Groq
                self._groq_client = Groq(api_key=groq_key)
                self._groq_available = True
                print("[ChatBot] Cliente Groq Cloud (Text AI) inicializado con éxito.")
            except Exception as e:
                print(f"[ChatBot] Error al inicializar cliente Groq: {e}")
                self._groq_available = False

        if gemini_key:
            self._gemini_available = True
            print("[ChatBot] Google Gemini 2.0 Flash (Visión Real AI) activo y listo.")

    def _call_gemini_vision(self, prompt: str, image_path: str, custom_system_prompt: str = SYSTEM_PROMPT) -> str:
        """Envia la imagen y la consulta a la API REST de Google Gemini 2.0 Flash."""
        api_key = get_gemini_api_key()
        if not api_key:
            return "⚠️ Para analizar imágenes es necesario configurar la clave `GEMINI_API_KEY` en el archivo `.env`."

        if not os.path.isfile(image_path):
            return f"⚠️ No se encontró la imagen en la ruta especificada: {image_path}"

        try:
            with open(image_path, "rb") as f:
                img_bytes = f.read()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")

            ext = os.path.splitext(image_path)[1].lower()
            mime_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
                ".gif": "image/gif",
                ".bmp": "image/bmp"
            }
            mime_type = mime_types.get(ext, "image/jpeg")

            full_instruction = (
                f"{custom_system_prompt}\n\n"
                f"El estudiante ha adjuntado una imagen para que la analices.\n"
                f"Instrucción o pregunta del estudiante: '{prompt if prompt else 'Analiza esta imagen minuciosamente.'}'"
            )

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

    def _call_gemini_text(self, messages: list, max_tokens: int = 2000) -> Optional[str]:
        """Fallback a Google Gemini 2.0 Flash para texto si el modelo de Groq no está disponible."""
        api_key = get_gemini_api_key()
        if not api_key:
            return None

        try:
            full_prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
            models_to_try = [get_gemini_model(), "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"]
            for model in models_to_try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": full_prompt}]}]
                }
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
        except Exception as ex:
            print(f"[ChatBot Gemini Text Fallback Error] {ex}")
        return None

    def send_message(
        self,
        user_message: str,
        uid: str = "",
        session_id: str = "",
        history: Optional[list] = None,
        custom_system_prompt: str = SYSTEM_PROMPT,
        attached_files: Optional[list] = None,
        image_path: Optional[str] = None,
        document_path: Optional[str] = None,
        max_tokens: int = 1000,
    ) -> str:
        """
        Envía un mensaje al chatbot con soporte para texto, imágenes (Gemini Visión) y documentos.
        """
        from utils.document_reader import extract_text_from_file

        all_attached = []
        if attached_files and isinstance(attached_files, list):
            all_attached.extend(attached_files)

        images_to_process = []
        if image_path and os.path.exists(image_path):
            images_to_process.append(image_path)

        documents_to_process = []
        if document_path and os.path.exists(document_path):
            documents_to_process.append(document_path)

        for item in all_attached:
            p = item.get("path") if isinstance(item, dict) else str(item)
            if not p or not os.path.exists(p): continue
            t = item.get("type") if isinstance(item, dict) else ""
            ext = os.path.splitext(p)[1].lower()
            if t == "imagen" or ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
                if p not in images_to_process:
                    images_to_process.append(p)
            else:
                if p not in documents_to_process:
                    documents_to_process.append(p)

        # 1. Extraer texto de documentos adjuntos
        doc_contents = []
        for doc_p in documents_to_process:
            doc_res = extract_text_from_file(doc_p)
            if doc_res["ok"]:
                fname = doc_res["filename"]
                words = doc_res["num_words"]
                txt = doc_res["text"]
                doc_contents.append(f"--- [DOCUMENTO ADJUNTO: {fname} ({words} palabras)] ---\n{txt}\n--- [FIN DE {fname}] ---")

        if doc_contents:
            joined_docs = "\n\n".join(doc_contents)
            user_instruction = user_message if user_message else "Por favor, analiza los documentos adjuntos."
            user_message = f"{user_instruction}\n\n{joined_docs}"

        # 2. Si hay imágenes adjuntas -> Enviar a Gemini Visión Real
        if images_to_process:
            primary_img = images_to_process[0]
            if self._gemini_available:
                return self._call_gemini_vision(user_message, primary_img, custom_system_prompt)
            else:
                return "⚠️ El análisis visual de imágenes requiere configurar `GEMINI_API_KEY` en el archivo `.env`."

        # 3. Procesar texto con Groq / Gemini Text Fallback
        if not user_message:
            return ""

        current_history = []
        if history:
            for h in history:
                current_history.append({"role": "user", "content": h.get("pregunta", "")})
                current_history.append({"role": "assistant", "content": h.get("respuesta", "")})
        else:
            current_history = self._conversation_history

        current_history.append({"role": "user", "content": user_message})
        messages = [{"role": "system", "content": custom_system_prompt}] + current_history[-10:]

        models_to_try = [get_groq_model(), "groq/compound", "groq/compound-mini", "openai/gpt-oss-120b", "qwen/qwen3.6-27b"]
        assistant_message = None

        if self._groq_client:
            for model in models_to_try:
                try:
                    response = self._groq_client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=0.7,
                        stream=False,
                    )
                    assistant_message = response.choices[0].message.content
                    if assistant_message:
                        break
                except Exception as e:
                    print(f"[ChatBot] Modelo Groq '{model}' no disponible, probando fallback...")
                    continue

        if not assistant_message and self._gemini_available:
            print("[ChatBot] Usando Google Gemini 2.0 Flash como motor principal de respuesta...")
            assistant_message = self._call_gemini_text(messages, max_tokens)

        if assistant_message:
            self._conversation_history.append({
                "role": "assistant",
                "content": assistant_message,
            })
            if len(self._conversation_history) > 20:
                self._conversation_history = self._conversation_history[-20:]
            return assistant_message

        return self._demo_response(user_message)

    def _demo_response(self, user_message: str) -> str:
        """Respuesta de demostración si no hay claves de API en .env."""
        from services.navigation_service import NavigationController
        lang = NavigationController.cache.get("language", "es")

        if lang == "en":
            return (
                "Hello! 👋 I am **PointBit**, your academic assistant.\n\n"
                "To activate my full hybrid AI capabilities (Groq for Text + Gemini for Vision), "
                "add `GROQ_API_KEY` and `GEMINI_API_KEY` to your `.env` file.\n\n"
                "How can I help you today? 📚"
            )
        else:
            return (
                "¡Hola! 👋 Soy **PointBit**, tu asistente académico inteligente.\n\n"
                "Puedo ayudarte a resumir documentos, resolver dudas de materias y explicar conceptos paso a paso. "
                "¡Escribe tu pregunta o sube un documento o imagen para comenzar! 🚀"
            )

# Instancia singleton global del ChatBot
chatbot = ChatBotService()
