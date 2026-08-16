import flet as ft
import threading
import time
from datetime import datetime
from typing import Optional

class NavigationController:
    page: ft.Page = None
    content_container: ft.Container = None
    current_page_instance = None
    current_view_name: str = "Login"
    
    # Sistema de Caché Global Ultra-Rápido
    cache = {
        "notes": [],
        "events": [],
        "tecnicas": [],
        "user_config": {},
        "messages": {},      # {contact_id: [messages]}
        "contacts": [],
        "online_users": [],  # [user_ids]
        "is_preloading": False,
        "current_user": None,
        "last_sync": None,
        "chatbot_sessions": [],
        "chatbot_histories": {}  # {session_id: [history]}
    }
    page_classes = {}
    page_instances = {}
    page_contents = {}

    @classmethod
    def initialize(cls, page: ft.Page, container: ft.Container):
        cls.page = page
        cls.content_container = container
        
        # Sincronización en segundo plano optimizada
        def background_sync():
            time.sleep(2)  # Inicio más rápido
            while True:
                try:
                    user = cls.get_current_user()
                    if user and user.get("id"):
                        uid = user["id"]
                        from services.database_service import db
                        # Latido de "En línea"
                        db.actualizar_ultimo_acceso(uid)
                        # Sincronización de datos en background
                        cls.preload_data(background=True)
                except: pass
                time.sleep(8)  # Sincronizar cada 8 segundos para "tiempo real"
                
        threading.Thread(target=background_sync, daemon=True).start()

    @classmethod
    def preload_pages(cls, background=True):
        """Precarga los módulos y clases de página para hacer la app más rápida."""
        def task():
            try:
                from views.pages.login_page import LoginPage
                from views.pages.registration_page import RegistrationPage
                from views.pages.recover_page import RecuperarContrasenaPage
                from views.pages.home_page import HomePage
                from views.pages.notes_page import NotesPage
                from views.pages.calendar_page import CalendarPage
                from views.pages.techniques_page import StudyMethodsPage
                from views.pages.messaging_page import MessagingPage
                from views.pages.profile_page import UserProfilePage
                from views.pages.chatbot_page import ChatBotPage

                pages = {
                    "Login": LoginPage,
                    "Registro": RegistrationPage,
                    "Recuperar": RecuperarContrasenaPage,
                    "Inicio": HomePage,
                    "Notas": NotesPage,
                    "Calendario": CalendarPage,
                    "Tecnicas": StudyMethodsPage,
                    "Mensajeria": MessagingPage,
                    "Perfil": UserProfilePage,
                    "ChatBot": ChatBotPage,
                }

                for name, cls_page in pages.items():
                    cls.page_classes[name] = cls_page

                # Precargar e instanciar contenidos en memoria para cambio de vista ultra instantáneo (0ms)
                if cls.page:
                    for name in ["Inicio", "ChatBot", "Mensajeria", "Notas", "Calendario", "Tecnicas", "Perfil"]:
                        if name not in cls.page_instances:
                            try:
                                page_cls = pages[name]
                                inst = page_cls(cls.page)
                                cls.page_instances[name] = inst
                                cls.page_contents[name] = inst.build()
                            except Exception:
                                pass
            except:
                pass

        if background:
            threading.Thread(target=task, daemon=True).start()
        else:
            task()

    @classmethod
    def get_current_user(cls) -> dict:
        if cls.cache.get("current_user"):
            return cls.cache["current_user"]
        if cls.page:
            try:
                user = cls.page.client_storage.get("current_user")
                if user:
                    cls.cache["current_user"] = user
                    return user
            except: pass
        return {"name": "Usuario", "photo_url": "", "id": None}

    @classmethod
    def preload_data(cls, background=True):
        """Carga datos sin bloquear la UI con paralelismo optimizado."""
        if cls.cache["is_preloading"]: return
        
        # Evitar re-sincronizaciones frecuentes si fue sincronizado hace menos de 5 segundos
        now = datetime.now()
        if cls.cache.get("last_sync") and (now - cls.cache["last_sync"]).total_seconds() < 5:
            return

        def task():
            cls.cache["is_preloading"] = True
            try:
                from services.database_service import db
                user = cls.get_current_user()
                uid = user.get("id")
                if uid:
                    # Funciones de carga paralela
                    def load_notes():
                        try:
                            cls.cache["notes"] = db.obtener_notas(uid) or []
                        except: pass

                    def load_events():
                        try:
                            cls.cache["events"] = db.obtener_eventos(uid) or []
                        except: pass

                    def load_tecnicas():
                        try:
                            cls.cache["tecnicas"] = db.obtener_tecnicas() or []
                        except: pass

                    def load_contacts():
                        try:
                            cls.cache["contacts"] = [c for c in (db.obtener_todos_los_usuarios() or []) if c["id"] != uid]
                        except: pass

                    def load_online_users():
                        try:
                            cls.cache["online_users"] = db.obtener_usuarios_online() or []
                        except: pass

                    def load_chatbot():
                        try:
                            cls.cache["chatbot_sessions"] = db.obtener_sesiones_chatbot(uid) or []
                        except: pass

                    # Ejecutar cargas principales en paralelo
                    threads = [
                        threading.Thread(target=load_notes, daemon=True),
                        threading.Thread(target=load_events, daemon=True),
                        threading.Thread(target=load_tecnicas, daemon=True),
                        threading.Thread(target=load_contacts, daemon=True),
                        threading.Thread(target=load_online_users, daemon=True),
                        threading.Thread(target=load_chatbot, daemon=True),
                    ]

                    for thread in threads:
                        thread.start()

                    for thread in threads:
                        thread.join(timeout=2)

                    cls.cache["last_sync"] = datetime.now()
            except: 
                pass
            finally:
                cls.cache["is_preloading"] = False

        if background:
            threading.Thread(target=task, daemon=True).start()
        else:
            task()

    @classmethod
    def _apply_page_theme(cls, dark: bool):
        bg = "#0F172A" if dark else "#F9FAFB"
        cls.page.theme_mode = ft.ThemeMode.DARK if dark else ft.ThemeMode.LIGHT
        cls.page.bgcolor = bg
        cls.cache["theme_dark"] = dark
        try:
            cls.page.client_storage.set("theme_dark", dark)
        except:
            pass
        if cls.content_container:
            cls.content_container.bgcolor = bg

    @classmethod
    def apply_user_preferences(cls):
        """Carga tema e idioma guardados y los aplica a la app."""
        if not cls.page:
            return

        lang = "es"
        dark = False
        try:
            lang = cls.page.client_storage.get("language") or "es"
            stored_theme = cls.page.client_storage.get("theme_dark")
            if stored_theme is not None:
                dark = bool(stored_theme)
        except:
            pass

        user = cls.get_current_user()
        if user and user.get("id"):
            try:
                from services.database_service import db
                config = db.obtener_configuracion(user["id"]) or {}
                config["uid"] = user["id"]
                cls.cache["user_config"] = {**cls.cache.get("user_config", {}), **config}
                lang = config.get("idioma") or lang
                dark = config.get("tema") == "oscuro"
            except:
                pass

        cls.cache["language"] = lang if lang in ("es", "en", "pt", "it", "de", "fr", "zh", "zh-TW") else "es"
        try:
            cls.page.client_storage.set("language", cls.cache["language"])
        except:
            pass
        cls._apply_page_theme(dark)

    @classmethod
    def change_language(cls, lang_code: str):
        """Cambia idioma de forma inmediata, persiste y reconstruye la vista actual."""
        if not cls.page or lang_code not in ("es", "en", "pt", "it", "de", "fr", "zh", "zh-TW"):
            return

        cls.cache["language"] = lang_code
        try:
            cls.page.client_storage.set("language", lang_code)
        except:
            pass

        user = cls.get_current_user()
        if user and user.get("id"):
            def save_task():
                try:
                    from services.database_service import db
                    db.actualizar_configuracion(user["id"], {"idioma": lang_code})
                except:
                    pass
            threading.Thread(target=save_task, daemon=True).start()

        cls.reload_current_view(show_message="language")

    @classmethod
    def change_theme(cls, dark: bool):
        """Cambia tema, persiste y reconstruye la vista actual."""
        if not cls.page:
            return

        cls._apply_page_theme(dark)
        user = cls.get_current_user()
        if user and user.get("id"):
            def save_task():
                try:
                    from services.database_service import db
                    db.actualizar_configuracion(user["id"], {"tema": "oscuro" if dark else "claro"})
                except:
                    pass
            threading.Thread(target=save_task, daemon=True).start()

        cls.reload_current_view(show_message="theme")

    @classmethod
    def reload_current_view(cls, show_message: str = None):
        """Reconstruye la pantalla actual (útil tras cambiar tema o idioma)."""
        if cls.current_view_name:
            cls.page_instances.clear()
            cls.page_contents.clear()
            cls.update_view(cls.current_view_name, force_rebuild=True)
            if show_message and cls.current_page_instance:
                try:
                    if show_message == "language":
                        cls.current_page_instance._show_success(
                            cls.current_page_instance.translate("msg_language_changed")
                        )
                    elif show_message == "theme":
                        cls.current_page_instance._show_success(
                            cls.current_page_instance.translate("msg_theme_changed")
                        )
                except:
                    pass

    @classmethod
    def logout(cls):
        """Cierra la sesión del usuario y limpia el caché."""
        if cls.page:
            try:
                cls.page.client_storage.remove("current_user")
                cls.cache["current_user"] = None
                cls.cache["notes"] = []
                cls.cache["events"] = []
                cls.cache["messages"] = {}
                cls.update_view("Login")
            except: pass

    @classmethod
    def update_view(cls, view_name: str, data=None, force_rebuild: bool = False):
        # Importaciones Lazy
        from views.pages.login_page import LoginPage
        from views.pages.registration_page import RegistrationPage
        from views.pages.recover_page import RecuperarContrasenaPage
        from views.pages.home_page import HomePage
        from views.pages.notes_page import NotesPage
        from views.pages.calendar_page import CalendarPage
        from views.pages.techniques_page import StudyMethodsPage
        from views.pages.messaging_page import MessagingPage
        from views.pages.profile_page import UserProfilePage
        from views.pages.chatbot_page import ChatBotPage

        view_map = {
            "Login": LoginPage,
            "Registro": RegistrationPage,
            "Recuperar": RecuperarContrasenaPage,
            "Inicio": HomePage,
            "Notas": NotesPage,
            "Calendario": CalendarPage,
            "Tecnicas": StudyMethodsPage,
            "Mensajeria": MessagingPage,
            "Perfil": UserProfilePage,
            "ChatBot": ChatBotPage,
        }

        cls.current_view_name = view_name
        page_class = cls.page_classes.get(view_name) or view_map.get(view_name, HomePage)

        if force_rebuild or view_name not in cls.page_instances:
            cls.page_instances[view_name] = page_class(cls.page)
            cls.page_contents[view_name] = cls.page_instances[view_name].build()
        elif view_name not in cls.page_contents:
            cls.page_contents[view_name] = cls.page_instances[view_name].build()

        cls.current_page_instance = cls.page_instances[view_name]
        cls.content_container.content = cls.page_contents[view_name]
        bg = "#0F172A" if cls.page.theme_mode == ft.ThemeMode.DARK else "#F9FAFB"
        cls.content_container.bgcolor = bg
        try:
            cls.page.update()
        except:
            pass

        # Precargar datos en el fondo después de cambiar de vista para la siguiente
        cls.preload_data(background=True)
