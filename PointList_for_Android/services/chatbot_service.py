"""
services/chatbot_service.py
PointList v0.14.25experiment
Servicio de integración con la API de Groq Cloud (Llama 3) para el chatbot académico.
Ofrece una alternativa gratuita, ultra rápida y potente.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno (Ruta absoluta para compatibilidad Android/PC)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_PATH = os.path.join(os.path.dirname(_ROOT), ".env")
if os.path.exists(_ENV_PATH):
    load_dotenv(_ENV_PATH)
else:
    load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN HÍBRIDA DE PROVEEDORES DE IA (Groq, OpenRouter, Google Gemini)
# ─────────────────────────────────────────────────────────────────────────────

def get_ai_clients():
    """
    Crea clientes dedicados para texto (Groq) y visión (Gemini/OpenRouter).
    Permite una arquitectura HÍBRIDA perfecta.
    """
    from openai import OpenAI

    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")

    clients = {
        "text_client": None,
        "text_model": "llama-3.3-70b-versatile",
        "vision_client": None,
        "vision_model": None,
        "text_provider": None,
        "vision_provider": None,
    }

    # 1. Configurar Cliente de Texto (Prioridad Groq por su velocidad)
    if groq_key:
        try:
            clients["text_client"] = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
            groq_m = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            if "vision" in groq_m or "preview" in groq_m:
                groq_m = "llama-3.3-70b-versatile"
            clients["text_model"] = groq_m
            clients["text_provider"] = "Groq Cloud (Llama 3.3)"
        except Exception as e:
            print(f"[ChatBot] Error en cliente Groq: {e}")

    # 2. Configurar Cliente de Visión para Imágenes (Gemini o OpenRouter)
    if gemini_key:
        try:
            clients["vision_client"] = OpenAI(api_key=gemini_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            clients["vision_model"] = "gemini-flash-latest"
            clients["vision_provider"] = "Google Gemini (Visión Real)"
        except Exception as e:
            print(f"[ChatBot] Error en cliente Gemini: {e}")

    elif openrouter_key:
        try:
            clients["vision_client"] = OpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1")
            clients["vision_model"] = "google/gemini-2.0-flash-exp:free"
            clients["vision_provider"] = "OpenRouter (Visión Real Gratis)"
        except Exception as e:
            print(f"[ChatBot] Error en cliente OpenRouter: {e}")

    # Fallback si no hay Groq para texto pero sí Gemini/OpenRouter
    if not clients["text_client"] and clients["vision_client"]:
        clients["text_client"] = clients["vision_client"]
        clients["text_model"] = clients["vision_model"]
        clients["text_provider"] = clients["vision_provider"]

    # Fallback si solo está Groq para ambos
    if not clients["vision_client"] and clients["text_client"]:
        clients["vision_client"] = clients["text_client"]
        clients["vision_model"] = clients["text_model"]
        clients["vision_provider"] = clients["text_provider"]

    return clients if (clients["text_client"] or clients["vision_client"]) else None


# Prompt de sistema que define la personalidad del chatbot
SYSTEM_PROMPT = """Eres PointBit, el asistente académico inteligente de la aplicación PointList.
Eres un sistema de inteligencia artificial diseñado para ayudar a los estudiantes en su camino académico.

Tu rol es ayudar a los estudiantes con:
- Técnicas de estudio y organización académica
- Explicación de conceptos de cualquier materia
- Análisis de calificaciones y rendimiento
- Planificación de horarios y tareas
- Consejos de productividad y bienestar estudiantil

Reglas de comportamiento:
1. Responde siempre en el idioma del usuario (español o inglés).
2. Sé amable, motivador y empático con el estudiante.
3. Usa emojis ocasionalmente para hacer la conversación más amena.
4. Si el usuario pregunta algo fuera del ámbito académico, puedes responder brevemente
   pero redirige la conversación hacia temas de estudio.
5. Proporciona respuestas estructuradas con listas o pasos cuando sea apropiado.
6. Siempre termina con una pregunta de seguimiento o una motivación para el estudiante.

Versión de la aplicación: PointList v0.14.25experiment
"""


class ChatBotService:
    """
    Servicio de IA Híbrido de PointList:
    - Texto ultra rápido con Groq (Llama 3.3 70B)
    - Visión inteligente de imágenes con Google Gemini 2.0 / OpenRouter
    """

    def __init__(self):
        self._available = False
        self._ai_setup = None
        self._conversation_history: list[dict] = []
        self._initialize_client()

    def _initialize_client(self):
        """Inicializa el enrutador híbrido de IA."""
        setup = get_ai_clients()
        if not setup:
            print("[ChatBot] Sin clave de IA configurada en .env. Usando modo demostración.")
            return

        self._ai_setup = setup
        self._available = True
        txt_p = setup.get('text_provider', 'Genérico')
        vis_p = setup.get('vision_provider', 'Texto')
        print(f"[ChatBot] Arquitectura Híbrida Activa: Texto con '{txt_p}' | Visión con '{vis_p}'.")

    @property
    def is_available(self) -> bool:
        return self._available

    def reset_conversation(self):
        """Reinicia el historial de conversación local."""
        self._conversation_history = []

    def send_message(self, user_message: str, uid=None, session_id=None, history: list = None, attached_file: dict = None, attached_files: list = None, max_tokens: int = 2000) -> str:
        """
        Envía un mensaje al motor híbrido de IA.
        Enruta automáticamente imágenes a Gemini y texto/documentos a Groq (Llama 3.3).
        Soporta múltiples archivos adjuntos simultáneos (PDF, DOCX, imágenes, etc.).
        """
        from services.navigation_service import NavigationController
        lang = NavigationController.cache.get("language", "es")
        
        lang_names = {
            "es": "español", "en": "English", "pt": "português", "it": "italiano",
            "de": "Deutsch (alemán)", "fr": "français (francés)", "zh": "中文 (chino simplificado)",
        }
        target_lang = lang_names.get(lang, "español")
        custom_system_prompt = SYSTEM_PROMPT + f"\n[IMPORTANTE] Responde obligatoriamente en el idioma {target_lang}."

        # Normalizar adjuntos a lista
        all_attachments = list(attached_files or [])
        if attached_file and attached_file not in all_attachments:
            all_attachments.append(attached_file)

        # 1. Modo Demostración sin API keys
        if not self._available:
            return self._demo_response(user_message, all_attachments[0] if all_attachments else None)

        image_items = [f for f in all_attachments if f.get("type") == "imagen"]
        text_items = [f for f in all_attachments if f.get("type") != "imagen"]

        doc_summary_text = ""
        for doc in text_items:
            doc_summary_text += f"\n\n--- [CONTENIDO DEL ARCHIVO ADJUNTO: {doc.get('name')}] ---\n{doc.get('content', '')[:10000]}"

        combined_prompt = (user_message or "Por favor analiza el contenido de estos archivos.") + doc_summary_text

        # 2. ENRUTAMIENTO DE IMÁGENES -> Canal de Visión (Gemini 2.0 / OpenRouter)
        if image_items:
            user_content = [{"type": "text", "text": combined_prompt}]
            for img in image_items:
                user_content.append({"type": "image_url", "image_url": {"url": img.get("content", "")}})

            vision_messages = [
                {"role": "system", "content": custom_system_prompt},
                {"role": "user", "content": user_content}
            ]

            vis_client = self._ai_setup.get("vision_client")
            vis_model = self._ai_setup.get("vision_model")


            if vis_client and vis_model and "llama-3.3" not in vis_model:
                try:
                    response = vis_client.chat.completions.create(
                        model=vis_model,
                        messages=vision_messages,
                        max_tokens=max_tokens,
                        temperature=0.7,
                    )
                    assistant_message = response.choices[0].message.content
                    self._conversation_history.append({"role": "assistant", "content": assistant_message})
                    return assistant_message
                except Exception as ex:
                    print(f"[ChatBot Vision Router Warning]: {ex}")

            # Fallback si no hay clave de visión activa en .env
            final_user_message = f"🖼️ [Imagen Adjunta: {f_name}]\n{prompt_text}"
        elif attached_file:
            f_name = attached_file.get("name", "archivo")
            f_content = attached_file.get("content", "")
            final_user_message = f"{user_message or 'Por favor analiza el siguiente documento:'}\n\n--- DOCUMENTO ADJUNTO ({f_name}) ---\n{f_content}\n--- FIN DOCUMENTO ---"
        else:
            final_user_message = user_message

        # 3. ENRUTAMIENTO DE TEXTO -> Canal de Texto Ultra Rápido (Groq Llama 3.3)
        current_history = []
        if history:
            for h in history:
                current_history.append({"role": "user", "content": h["pregunta"]})
                current_history.append({"role": "assistant", "content": h["respuesta"]})
        else:
            current_history = self._conversation_history

        current_history.append({"role": "user", "content": final_user_message})
        messages = [{"role": "system", "content": custom_system_prompt}] + current_history[-10:]

        try:
            txt_client = self._ai_setup.get("text_client")
            txt_model = self._ai_setup.get("text_model", "llama-3.3-70b-versatile")
            
            response = txt_client.chat.completions.create(
                model=txt_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                stream=False,
            )

            assistant_message = response.choices[0].message.content
            self._conversation_history.append({"role": "assistant", "content": assistant_message})

            if len(self._conversation_history) > 20:
                self._conversation_history = self._conversation_history[-20:]

            return assistant_message

        except Exception as e:
            error_msg = f"Error al comunicarse con la IA: {str(e)}"
            print(f"[ChatBot Error]: {error_msg}")
            return f"⚠️ {error_msg}\n\nPor favor, verifica tu conexión a internet y tus claves de API en el archivo .env."





    def _demo_response(self, user_message: str, attached_file: dict = None) -> str:
        """Respuesta de demostración traducida según el idioma de la aplicación."""
        from services.navigation_service import NavigationController
        lang = NavigationController.cache.get("language", "es")
        
        if attached_file and attached_file.get("type") == "imagen":
            f_name = attached_file.get("name", "imagen")
            return (
                f"🖼️ **[Modo Demostración - Imagen Recibida: {f_name}]**\n\n"
                "¡El sistema de lectura de imágenes está 100% integrado! "
                "Para que la IA procese y describa imágenes en tiempo real con visión artificial (Groq Llama 3.2 Vision), "
                "agrega tu `GROQ_API_KEY` gratuita en el archivo `.env`."
            )
        elif attached_file:
            f_name = attached_file.get("name", "documento")
            return (
                f"📄 **[Modo Demostración - Documento Recibido: {f_name}]**\n\n"
                "¡El lector de documentos está 100% activo! "
                "Para obtener un análisis y resumen completo en tiempo real con Groq Llama 3, "
                "agrega tu `GROQ_API_KEY` gratuita en el archivo `.env`."
            )

        message_lower = (user_message or "").lower()

        if lang == "en":
            if any(word in message_lower for word in ["hello", "hi", "hey", "good morning"]):
                return (
                    "Hello! 👋 I am **PointBit**, your academic assistant from PointList.\n\n"
                    "I am currently in demo mode because the Groq API is not configured. "
                    "To activate me fully (it's free!), add your `GROQ_API_KEY` to the `.env` file.\n\n"
                    "How can I help you today? 📚"
                )
            elif any(word in message_lower for word in ["pomodoro", "technique", "study"]):
                return (
                    "📖 **Pomodoro Technique**\n\n"
                    "It is one of the most effective study techniques:\n\n"
                    "1. ⏱️ Focus and work for **25 minutes**\n"
                    "2. 🛑 Take a **5-minute** break\n"
                    "3. 🔄 Repeat the cycle **4 times**\n"
                    "4. 🌟 Take a long **15-30 minute** break\n\n"
                    "This technique improves focus and reduces mental fatigue. "
                    "Would you like to know about other study methods? 🎯"
                )
            elif any(word in message_lower for word in ["pointbit", "assistant"]):
                return (
                    "🤖 **I am PointBit**\n\n"
                    "I am your smart academic assistant in PointList. "
                    "I'm here to help you with your studies, learning techniques, "
                    "performance analysis, and productivity tips. Always ready to support you! ✨\n\n"
                    "How can I help you today? 📚"
                )
            else:
                return (
                    "🤖 I am in **demo mode**.\n\n"
                    "To access all my capabilities with **Groq Cloud (Llama 3)**, "
                    "configure your `GROQ_API_KEY` in the `.env` file.\n\n"
                    "Meanwhile, I can help you with basic information on study techniques "
                    "and the PointList app. What do you need? 📚"
                )
        elif lang == "pt":
            if any(word in message_lower for word in ["ola", "oi", "bom dia", "boa tarde"]):
                return (
                    "Olá! 👋 Eu sou o **PointBit**, seu assistente acadêmico da PointList.\n\n"
                    "No momento, estou em modo de demonstração porque a API do Groq não está configurada. "
                    "Para me ativar totalmente (é grátis!), adicione sua `GROQ_API_KEY` no arquivo `.env`.\n\n"
                    "Como posso te ajudar hoje? 📚"
                )
            elif any(word in message_lower for word in ["pomodoro", "tecnica", "estudo"]):
                return (
                    "📖 **Técnica Pomodoro**\n\n"
                    "É uma das técnicas de estudo mais eficazes:\n\n"
                    "1. ⏱️ Trabalhe focado por **25 minutos**\n"
                    "2. 🛑 Faça uma pausa de **5 minutos**\n"
                    "3. 🔄 Repita o ciclo **4 vezes**\n"
                    "4. 🌟 Faça uma pausa longa de **15 a 30 minutos**\n\n"
                    "Essa técnica melhora o foco e reduz a fadiga mental. "
                    "Gostaria de saber sobre outras técnicas de estudo? 🎯"
                )
            elif any(word in message_lower for word in ["pointbit", "assistente"]):
                return (
                    "🤖 **Eu sou o PointBit**\n\n"
                    "Sou seu assistente acadêmico inteligente no PointList. "
                    "Estou aqui para ajudar nos seus estudos, técnicas de aprendizagem, "
                    "análise do seu desempenho e dicas de produtividade. Sempre pronto para te apoiar! ✨\n\n"
                    "Como posso te ajudar hoje? 📚"
                )
            else:
                return (
                    "🤖 Estou no **modo de demonstração**.\n\n"
                    "Para acessar todos os meus recursos com **Groq Cloud (Llama 3)**, "
                    "configure sua `GROQ_API_KEY` no arquivo `.env`.\n\n"
                    "Enquanto isso, posso ajudar com informações básicas sobre técnicas de estudo "
                    "e o aplicativo PointList. O que você precisa? 📚"
                )
        else: # "es"
            if any(word in message_lower for word in ["hola", "hi", "hello", "buenas"]):
                return (
                    "¡Hola! 👋 Soy **PointBit**, tu asistente académico de PointList.\n\n"
                    "Actualmente estoy en modo de demostración porque la API de Groq "
                    "no está configurada. Para activarme completamente (¡es gratis!), agrega tu "
                    "`GROQ_API_KEY` en el archivo `.env`.\n\n"
                    "¿En qué puedo ayudarte hoy? 📚"
                )
            elif any(word in message_lower for word in ["pomodoro", "técnica", "estudio"]):
                return (
                    "📖 **Técnica Pomodoro**\n\n"
                    "Es una de las técnicas de estudio más efectivas:\n\n"
                    "1. ⏱️ Trabaja enfocado durante **25 minutos**\n"
                    "2. 🛑 Toma un descanso de **5 minutos**\n"
                    "3. 🔄 Repite el ciclo **4 veces**\n"
                    "4. 🌟 Toma un descanso largo de **15-30 minutos**\n\n"
                    "Esta técnica mejora la concentración y reduce la fatiga mental. "
                    "¿Te gustaría saber sobre otras técnicas de estudio? 🎯"
                )
            elif any(word in message_lower for word in ["pointbit", "asistente"]):
                return (
                    "🤖 **Soy PointBit**\n\n"
                    "Soy tu asistente académico inteligente en PointList. "
                    "Estoy aquí para ayudarte con tus estudios, técnicas de aprendizaje, "
                    "análisis de tu rendimiento y consejos de productividad. ¡Siempre listo para apoyarte! ✨\n\n"
                    "¿En qué puedo ayudarte hoy? 📚"
                )
            else:
                return (
                    "🤖 Estoy en **modo de demostración**.\n\n"
                    "Para acceder a todas mis capacidades con **Groq Cloud (Llama 3)**, "
                    "configura tu `GROQ_API_KEY` en el archivo `.env`.\n\n"
                    "Mientras tanto, puedo ayudarte con información básica sobre "
                    "técnicas de estudio y la aplicación PointList. ¿Qué necesitas? 📚"
                )

    def get_history(self) -> list[dict]:
        """Devuelve el historial de conversación actual."""
        return self._conversation_history.copy()


# Instancia global del servicio
chatbot = ChatBotService()
