"""
pages/messaging_page.py - v13.5
PointList Mensajería Rediseñada
Buscador de usuarios, modal instantáneo de nuevo chat, archivado/borrado de chats, avatares reales, burbujas estilizadas.
"""

import flet as ft
import threading
import time
import os
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode

class MessagingPage(BasePage):
    """Página de mensajería rediseñada v13.5 profesional."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db = db
        self._user = NavigationController.get_current_user()
        self._uid = self._user.get("id")
        self._contacts: list = []
        self._filtered_contacts: list = []
        self._all_users: list = []
        self._messages: dict = {}
        self._selected_contact = None
        self._active_tab: str = "chats"  # "chats" | "archivados"

        # Cargar IDs borrados y archivados desde la memoria del usuario
        archived_cache = NavigationController.cache.get(f"archived_chats_{self._uid}", [])
        deleted_cache = NavigationController.cache.get(f"deleted_chats_{self._uid}", [])
        self._archived_ids: set = set(archived_cache)
        self._deleted_ids: set = set(deleted_cache)

        self._messages_ref = ft.Ref[ft.Column]()
        self._input_ref = ft.Ref[ft.TextField]()
        self._search_ref = ft.Ref[ft.TextField]()
        self._contacts_list_ref = ft.Ref[ft.Column]()
        self._main_row_ref = ft.Ref[ft.Row]()
        self._file_picker = ft.FilePicker(on_result=self._on_file_selected)
        self.page.overlay.append(self._file_picker)

        # Iniciar sincronizador de mensajes en tiempo real y notificaciones APK
        self._start_realtime_sync()

    def _save_chat_states(self):
        """Guarda los IDs archivados y borrados en el caché global."""
        from services.navigation_service import NavigationController
        NavigationController.cache[f"archived_chats_{self._uid}"] = list(self._archived_ids)
        NavigationController.cache[f"deleted_chats_{self._uid}"] = list(self._deleted_ids)

    def _clear_active_chat_history(self, e=None):
        """Vacía inmediatamente todo el historial del chat activo (UI, caché y Supabase)."""
        if not self._selected_contact:
            return

        cid = self._selected_contact["id"]
        is_group = self._selected_contact.get("es_grupo", False)
        name = self._contact_display_name(self._selected_contact)

        from services.navigation_service import NavigationController
        if "messages" in NavigationController.cache and cid in NavigationController.cache["messages"]:
            NavigationController.cache["messages"][cid] = []

        self._refresh_messages()

        try:
            self.page.open(ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.CLEANING_SERVICES, color="white"),
                    ft.Text(f"Historial con {name} vaciado por completo", color="white", weight="bold")
                ], spacing=8),
                bgcolor="#10B981"
            ))
        except: pass

        def _bg_clear():
            try:
                if is_group:
                    self._db.eliminar_conversacion(self._uid, gid=cid)
                else:
                    self._db.eliminar_conversacion(self._uid, rid=cid)
            except: pass
        threading.Thread(target=_bg_clear, daemon=True).start()

    def _trigger_apk_notification(self, sender_name: str, msg_content: str):
        """Dispara una notificación flotante instantánea en la app / APK de Android."""
        try:
            if not self.page:
                return
            snack = ft.SnackBar(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHAT_BUBBLE, color="white", size=20),
                    ft.Column([
                        ft.Text(f"💬 Mensaje de {sender_name}", weight="bold", color="white", size=13),
                        ft.Text(msg_content[:45] + ("..." if len(msg_content) > 45 else ""), color="white", size=11),
                    ], spacing=1, tight=True, expand=True)
                ], spacing=10),
                bgcolor="#10B981",
                duration=3500,
                behavior=ft.SnackBarBehavior.FLOATING,
            )
            self.page.open(snack)
        except: pass

    def _start_realtime_sync(self):
        """Polling en tiempo real (1.5s) para mensajes instantáneos y notificaciones de APK."""
        self._stop_sync = False

        def _poll_worker():
            while not getattr(self, "_stop_sync", False):
                time.sleep(0.3)
                try:
                    if not self.page:
                        break
                    if self._selected_contact:
                        cid = self._selected_contact["id"]
                        is_group = self._selected_contact.get("es_grupo", False)

                        if is_group:
                            fresh = self._db.obtener_mensajes(self._uid, gid=cid) or []
                        else:
                            fresh = self._db.obtener_mensajes(self._uid, rid=cid) or []

                        from services.navigation_service import NavigationController
                        if "messages" not in NavigationController.cache:
                            NavigationController.cache["messages"] = {}

                        old = NavigationController.cache["messages"].get(cid, [])
                        if len(fresh) > len(old):
                            new_items = fresh[len(old):]
                            NavigationController.cache["messages"][cid] = fresh
                            self._refresh_messages()

                            for nm in new_items:
                                sender_id = str(nm.get("sender_id") or nm.get("emisor_id"))
                                if sender_id != str(self._uid):
                                    sname = self._contact_display_name(self._selected_contact)
                                    mcontent = nm.get("content") or nm.get("contenido") or "Nuevo adjunto"
                                    self._trigger_apk_notification(sname, mcontent)
                except:
                    pass

        threading.Thread(target=_poll_worker, daemon=True).start()

    def _contact_display_name(self, contact: dict) -> str:
        """Obtiene el nombre visible de un contacto con fallbacks."""
        if not contact: return "Usuario"
        name = (
            contact.get("name")
            or contact.get("nombre_usuario")
            or contact.get("nombre")
            or contact.get("email")
            or "Usuario"
        )
        return str(name).strip() or "Usuario"

    def _media_kind(self, path: str) -> str | None:
        """Detecta si un adjunto es imagen, video u otro archivo."""
        if not path or not str(path).strip():
            return None
        ext = str(path).lower().rsplit(".", 1)[-1] if "." in str(path) else ""
        if ext in ("jpg", "jpeg", "png", "gif", "webp", "bmp"):
            return "image"
        if ext in ("mp4", "avi", "mov", "webm", "mkv", "m4v"):
            return "video"
        if ext:
            return "file"
        return None

    def _normalize_message(self, msg: dict) -> dict:
        """Normaliza mensajes de BD al formato usado por la UI."""
        file_path = msg.get("file_path") or msg.get("image_data")
        content = (msg.get("content") or msg.get("contenido") or "").strip()
        msg_type = msg.get("type", "text")
        if file_path:
            inferred = self._media_kind(file_path)
            if inferred:
                msg_type = inferred
            elif msg_type == "text":
                msg_type = "file"
        return {
            "id": msg.get("id"),
            "sender_id": msg.get("sender_id") or msg.get("emisor_id"),
            "content": content,
            "timestamp": msg.get("timestamp"),
            "type": msg_type,
            "file_path": file_path,
        }

    def _load_contacts(self):
        """Carga contactos individuales y grupos con soporte para archivados y borrados."""
        from services.navigation_service import NavigationController

        cached_users = NavigationController.cache.get("contacts", [])
        if not cached_users and self._db:
            try:
                cached_users = [c for c in (self._db.obtener_todos_los_usuarios() or []) if c["id"] != self._uid]
                NavigationController.cache["contacts"] = cached_users
            except:
                cached_users = []

        self._all_users = cached_users

        cached_groups = NavigationController.cache.get("user_groups", None)
        if cached_groups is None and self._db:
            try:
                cached_groups = self._db.obtener_grupos_usuario(self._uid) or []
                NavigationController.cache["user_groups"] = cached_groups
            except:
                cached_groups = []

        for g in (cached_groups or []):
            g["es_grupo"] = True
            g["nombre_usuario"] = f"👥 {g.get('nombre', 'Grupo')}"

        all_items = (cached_groups or []) + cached_users

        # Filtrar borrados
        visible_items = [c for c in all_items if c["id"] not in self._deleted_ids]

        # Separar en activos vs archivados
        if self._active_tab == "archivados":
            self._contacts = [c for c in visible_items if c["id"] in self._archived_ids]
        else:
            self._contacts = [c for c in visible_items if c["id"] not in self._archived_ids]

        self._filtered_contacts = self._contacts.copy()

        def _bg_sync():
            try:
                fresh_u = [c for c in (self._db.obtener_todos_los_usuarios() or []) if c["id"] != self._uid]
                fresh_g = self._db.obtener_grupos_usuario(self._uid) or []
                NavigationController.cache["contacts"] = fresh_u
                NavigationController.cache["user_groups"] = fresh_g
            except: pass
        threading.Thread(target=_bg_sync, daemon=True).start()

    def _load_messages(self, contact_id):
        """Carga mensajes de un contacto o grupo con caché instantánea."""
        if not self._selected_contact:
            return []

        from services.navigation_service import NavigationController
        if "messages" not in NavigationController.cache:
            NavigationController.cache["messages"] = {}

        if contact_id in NavigationController.cache["messages"]:
            return NavigationController.cache["messages"][contact_id]

        is_group = self._selected_contact.get("es_grupo", False)
        if is_group:
            msgs = self._db.obtener_mensajes(self._uid, gid=contact_id) or []
        else:
            msgs = self._db.obtener_mensajes(self._uid, rid=contact_id) or []

        NavigationController.cache["messages"][contact_id] = msgs
        return msgs

    def _search_contacts(self, e):
        """Filtra contactos según búsqueda."""
        search_text = self._search_ref.current.value.lower() if self._search_ref.current else ""
        if not search_text:
            self._filtered_contacts = self._contacts.copy()
        else:
            self._filtered_contacts = [
                c for c in self._contacts
                if search_text in self._contact_display_name(c).lower() or search_text in c.get("email", "").lower()
            ]
        self._refresh_contacts_list()

    def _show_new_chat_dialog(self, e=None):
        """Abre inmediatamente (0ms) un modal para iniciar un nuevo chat con cualquier usuario."""
        colors = self._get_theme_colors()

        search_input = ft.TextField(
            hint_text="Buscar por nombre o correo...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=10,
            autofocus=True,
            dense=True,
        )

        users_col = ft.Column(spacing=4, scroll=get_scroll_mode("AUTO"))

        def _render_users_list(query=""):
            q = query.strip().lower()
            filtered = [
                u for u in self._all_users
                if not q or (q in self._contact_display_name(u).lower() or q in u.get("email", "").lower())
            ]
            controls = []
            for u in filtered:
                uname = self._contact_display_name(u)
                urole = u.get("rol", "estudiante").capitalize()

                def _start_chat(_, target_user=u):
                    self.page.close(dlg)
                    # Quitar de borrados y archivados si existía
                    self._deleted_ids.discard(target_user["id"])
                    self._archived_ids.discard(target_user["id"])
                    self._save_chat_states()
                    self._active_tab = "chats"
                    self._load_contacts()

                    # Asegurar que está al frente de los contactos
                    existing = [c for c in self._contacts if c["id"] == target_user["id"]]
                    if not existing:
                        self._contacts.insert(0, target_user)
                    else:
                        self._contacts.remove(existing[0])
                        self._contacts.insert(0, existing[0])

                    self._filtered_contacts = self._contacts.copy()
                    self._select_contact(target_user)

                item = ft.Container(
                    content=ft.Row([
                        ft.CircleAvatar(
                            radius=18,
                            bgcolor=self.primary_color,
                            content=ft.Text(uname[:2].upper(), color="white", weight="bold", size=12)
                        ),
                        ft.Column([
                            ft.Text(uname, size=13, weight="bold", color=colors["text"]),
                            ft.Text(f"{u.get('email', '')} • {urole}", size=11, color=ft.Colors.GREY_500),
                        ], expand=True, spacing=1),
                        ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, color="#10B981", size=18)
                    ], spacing=10),
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    border_radius=8,
                    ink=True,
                    on_click=_start_chat,
                )
                controls.append(item)

            if not controls:
                controls.append(
                    ft.Container(
                        padding=ft.padding.all(20),
                        alignment=ft.alignment.center,
                        content=ft.Text("No se encontraron usuarios", color=ft.Colors.GREY_500, size=13)
                    )
                )
            users_col.controls = controls
            try: users_col.update()
            except: pass

        def _on_search_change(e):
            _render_users_list(search_input.value)

        search_input.on_change = _on_search_change

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.PERSON_ADD_ALT_1, color="#10B981"),
                ft.Text("Iniciar Nuevo Chat", weight="bold", size=18)
            ]),
            content=ft.Container(
                width=400,
                height=350,
                content=ft.Column([
                    search_input,
                    ft.Container(height=8),
                    ft.Container(expand=True, content=users_col)
                ], spacing=0)
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self.page.close(dlg))
            ]
        )
        self.page.open(dlg)
        _render_users_list()

    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        """Maneja la selección de archivo (video, imagen, etc)."""
        if e.files:
            file_path = e.files[0].path
            file_name = e.files[0].name
            self._send_message_with_attachment(file_path, file_name)

    def _send_message_with_attachment(self, file_path, file_name):
        """Envía mensaje con adjunto y actualiza la posición del chat."""
        if not self._selected_contact:
            return

        contact_id = self._selected_contact["id"]
        media_kind = self._media_kind(file_path) or "file"

        # Quitar de borrados/archivados
        self._deleted_ids.discard(contact_id)
        self._archived_ids.discard(contact_id)
        self._save_chat_states()

        new_msg = {
            "id": f"temp_{int(time.time())}",
            "sender_id": self._uid,
            "content": os.path.basename(file_name),
            "timestamp": time.time(),
            "file_path": file_path,
            "type": media_kind,
        }

        from services.navigation_service import NavigationController
        if "messages" not in NavigationController.cache:
            NavigationController.cache["messages"] = {}
        if contact_id not in NavigationController.cache["messages"]:
            NavigationController.cache["messages"][contact_id] = []
        NavigationController.cache["messages"][contact_id].append(new_msg)
        self._refresh_messages()

        # Mover contacto arriba en la lista
        self._move_contact_to_top(self._selected_contact)

        def save_task():
            try:
                self._db.guardar_mensaje(self._uid, contact_id, new_msg["content"], file_path)
            except:
                pass
        threading.Thread(target=save_task, daemon=True).start()

    def _move_contact_to_top(self, contact):
        """Mueve un contacto al inicio de la lista lateral."""
        cid = contact["id"]
        existing = [c for c in self._contacts if c["id"] == cid]
        if existing:
            self._contacts.remove(existing[0])
            self._contacts.insert(0, existing[0])
        else:
            self._contacts.insert(0, contact)
        self._filtered_contacts = self._contacts.copy()
        self._refresh_contacts_list()

    def _build_video_content(self, file_path: str, is_sender: bool) -> ft.Control:
        """Muestra un video en el chat o un fallback visual."""
        text_color = "white" if is_sender else self._get_theme_colors()["text"]
        try:
            if hasattr(ft, "Video") and hasattr(ft, "VideoMedia"):
                return ft.Video(
                    width=280,
                    height=180,
                    playlist=[ft.VideoMedia(resource=file_path)],
                    autoplay=False,
                    muted=True,
                    show_play_pause_button=True,
                )
        except Exception:
            pass
        return ft.Container(
            width=260,
            height=160,
            bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
            border_radius=12,
            alignment=ft.alignment.center,
            content=ft.Column([
                ft.Icon(ft.Icons.VIDEO_LIBRARY, size=48, color=text_color),
                ft.Text(os.path.basename(file_path), size=11, color=text_color, text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
        )

    def _build_message_bubble(self, msg: dict, is_sender: bool, colors: dict) -> ft.Container | None:
        """Construye la burbuja de un mensaje (texto, imagen o video)."""
        file_path = msg.get("file_path")
        content = (msg.get("content") or "").strip()
        msg_type = msg.get("type", "text")
        bubble_bg = self.primary_color if is_sender else colors["surface"]
        text_color = "white" if is_sender else colors["text"]

        if file_path and msg_type in ("image", "video", "file"):
            parts: list = []
            if msg_type == "image":
                if os.path.isfile(file_path):
                    parts.append(
                        ft.Image(
                            src=file_path,
                            width=260,
                            height=180,
                            fit=ft.ImageFit.COVER,
                            border_radius=ft.border_radius.all(12),
                        )
                    )
                else:
                    parts.append(ft.Icon(ft.Icons.BROKEN_IMAGE, size=40, color=text_color))
                    parts.append(ft.Text(os.path.basename(file_path), size=11, color=text_color))
            elif msg_type == "video":
                parts.append(self._build_video_content(file_path, is_sender))
            else:
                label = content.replace("📄", "").strip() or os.path.basename(file_path)
                parts.append(ft.Icon(ft.Icons.ATTACH_FILE, size=28, color=text_color))
                parts.append(ft.Text(label, size=12, color=text_color))

            bubble_width = min(300, max(220, self.page.width - 120) if self.page.width else 300)
            return ft.Container(
                padding=ft.padding.all(8),
                bgcolor=bubble_bg,
                border_radius=16,
                content=ft.Column(parts, spacing=6, tight=True),
                width=bubble_width,
            )

        if not content:
            return None

        bubble_width = min(320, max(220, self.page.width - 120) if self.page.width else 320)
        return ft.Container(
            padding=ft.padding.all(12),
            bgcolor=bubble_bg,
            border_radius=16,
            content=ft.Text(content, size=13, color=text_color, selectable=True),
            width=bubble_width,
        )

    def _send_message(self, e):
        """Envía un mensaje de texto a contacto o grupo."""
        if not self._selected_contact:
            return

        msg_text = self._input_ref.current.value.strip() if self._input_ref.current else ""
        if not msg_text:
            return

        contact_id = self._selected_contact["id"]
        is_group = self._selected_contact.get("es_grupo", False)

        # Quitar de borrados/archivados
        self._deleted_ids.discard(contact_id)
        self._archived_ids.discard(contact_id)
        self._save_chat_states()

        new_msg = {
            "id": f"temp_{int(time.time())}",
            "sender_id": self._uid,
            "content": msg_text,
            "timestamp": time.time(),
            "type": "text"
        }

        from services.navigation_service import NavigationController
        if "messages" not in NavigationController.cache:
            NavigationController.cache["messages"] = {}
        if contact_id not in NavigationController.cache["messages"]:
            NavigationController.cache["messages"][contact_id] = []
        NavigationController.cache["messages"][contact_id].append(new_msg)

        if self._input_ref.current:
            self._input_ref.current.value = ""
        self._refresh_messages()

        # Mover al frente del sidebar de chats
        self._move_contact_to_top(self._selected_contact)

        def save_task():
            try:
                if is_group:
                    self._db.guardar_mensaje_grupo(self._uid, contact_id, msg_text)
                else:
                    self._db.guardar_mensaje(self._uid, contact_id, msg_text)
            except:
                pass
        threading.Thread(target=save_task, daemon=True).start()

    def _show_create_group_dialog(self, e=None):
        """Modal estilo WhatsApp para crear un nuevo grupo de chat."""
        colors = self._get_theme_colors()
        group_name_field = ft.TextField(
            label="Nombre del Grupo",
            hint_text="Ej: Proyecto Biología, Grupo 10-A...",
            border_radius=10,
            border_color="#10B981",
        )

        all_users = [u for u in self._all_users if u["id"] != self._uid]
        checkboxes = [
            ft.Checkbox(label=f"{self._contact_display_name(u)} ({u.get('rol', 'estudiante')})", value=False, data=u["id"])
            for u in all_users
        ]

        def _do_create_group(e):
            gname = group_name_field.value.strip()
            if not gname:
                group_name_field.error_text = "Ingresa un nombre para el grupo"
                try: group_name_field.update()
                except: pass
                return

            selected_members = [cb.data for cb in checkboxes if cb.value]
            res = self._db.crear_grupo(gname, self._uid, selected_members)

            self.page.close(dlg)
            if res and res.get("ok"):
                from services.navigation_service import NavigationController
                NavigationController.cache.pop("user_groups", None)
                self._load_contacts()
                self._refresh_contacts_list()
                try: self.page.update()
                except: pass

        dlg = ft.AlertDialog(
            title=ft.Row([
                ft.Icon(ft.Icons.GROUP_ADD, color="#10B981"),
                ft.Text("Nuevo Grupo de Chat", weight="bold", size=18)
            ]),
            content=ft.Container(
                width=400,
                height=320,
                content=ft.Column([
                    group_name_field,
                    ft.Container(height=10),
                    ft.Text("Selecciona participantes:", weight="bold", size=13, color="#475569"),
                    ft.Container(
                        expand=True,
                        content=ft.Column(controls=checkboxes, scroll=get_scroll_mode("AUTO"), spacing=4)
                    )
                ], spacing=0)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Crear Grupo", bgcolor="#10B981", color="white", on_click=_do_create_group)
            ]
        )
        self.page.open(dlg)

    def _refresh_messages(self):
        """Refresca la lista de mensajes."""
        if not self._selected_contact or not self._messages_ref.current:
            return

        contact_id = self._selected_contact["id"]
        messages = [self._normalize_message(m) for m in self._load_messages(contact_id)]
        colors = self._get_theme_colors()

        msg_controls = []
        for msg in messages:
            is_sender = str(msg.get("sender_id")) == str(self._uid)
            bubble = self._build_message_bubble(msg, is_sender, colors)
            if not bubble:
                continue
            gesture_bubble = ft.GestureDetector(
                on_long_press_start=lambda e, m=msg: self._show_message_options(m),
                on_secondary_tap=lambda e, m=msg: self._show_message_options(m),
                content=bubble
            )

            msg_controls.append(
                ft.Row(
                    [gesture_bubble],
                    alignment=ft.MainAxisAlignment.END if is_sender else ft.MainAxisAlignment.START,
                    spacing=10,
                )
            )

        try:
            self._messages_ref.current.controls = msg_controls
            self._messages_ref.current.update()
        except:
            pass

    def _select_contact(self, contact):
        """Selecciona un contacto y abre la conversación de forma instantánea (0ms)."""
        self._selected_contact = contact
        from services.navigation_service import NavigationController
        NavigationController.cache["selected_contact"] = contact

        if self.is_mobile():
            NavigationController.reload_current_view()
        else:
            self._refresh_contacts_list()
            if self._main_row_ref.current and len(self._main_row_ref.current.controls) > 1:
                self._main_row_ref.current.controls[1] = self._build_right_panel()
            try:
                self.page.update()
            except:
                pass
            self._refresh_messages()

    def _delete_chat(self, contact: dict):
        """Borra la conversación y elimina el contacto del panel lateral de inmediato."""
        cid = contact["id"]
        is_group = contact.get("es_grupo", False)

        # Añadir a borrados y guardar
        self._deleted_ids.add(cid)
        self._archived_ids.discard(cid)
        self._save_chat_states()

        # Limpiar caché de mensajes local
        from services.navigation_service import NavigationController
        if "messages" in NavigationController.cache:
            NavigationController.cache["messages"].pop(cid, None)

        # Si el contacto eliminado era el activo, cerrar el panel derecho
        if self._selected_contact and self._selected_contact["id"] == cid:
            self._selected_contact = None
            NavigationController.cache["selected_contact"] = None

        # Actualizar listas inmediatamente
        self._contacts = [c for c in self._contacts if c["id"] != cid]
        self._filtered_contacts = [c for c in self._filtered_contacts if c["id"] != cid]
        self._refresh_contacts_list()

        if self._main_row_ref.current and len(self._main_row_ref.current.controls) > 1:
            self._main_row_ref.current.controls[1] = self._build_right_panel()

        try:
            self.page.update()
        except:
            pass

        # Eliminar en base de datos en segundo plano
        def _bg_del():
            try:
                if is_group:
                    self._db.eliminar_conversacion(self._uid, gid=cid)
                else:
                    self._db.eliminar_conversacion(self._uid, rid=cid)
            except: pass
        threading.Thread(target=_bg_del, daemon=True).start()

    def _archive_chat(self, contact: dict):
        """Archiva una conversación."""
        cid = contact["id"]
        self._archived_ids.add(cid)
        self._deleted_ids.discard(cid)
        self._save_chat_states()

        self._load_contacts()
        self._refresh_contacts_list()
        try: self.page.update()
        except: pass

    def _unarchive_chat(self, contact: dict):
        """Desarchiva una conversación."""
        cid = contact["id"]
        self._archived_ids.discard(cid)
        self._save_chat_states()

        self._load_contacts()
        self._refresh_contacts_list()
        try: self.page.update()
        except: pass

    def _show_contact_options(self, contact: dict):
        """Muestra menú contextual profesional al mantener presionado o dar clic secundario en un chat."""
        name = self._contact_display_name(contact)
        cid = contact.get("id")
        is_archived = cid in self._archived_ids

        def _open(e):
            self.page.close(bs)
            self._select_contact(contact)

        def _toggle_archive(e):
            self.page.close(bs)
            if is_archived:
                self._unarchive_chat(contact)
                self._show_success(f"Chat desarchivado: {name}")
            else:
                self._archive_chat(contact)
                self._show_success(f"Chat archivado: {name}")

        def _do_delete_chat(e):
            self.page.close(bs)
            self._delete_chat(contact)
            self._show_success(f"Conversación con {name} eliminada")

        def _clear_chat(e):
            self.page.close(bs)
            from services.navigation_service import NavigationController
            if "messages" in NavigationController.cache and cid in NavigationController.cache["messages"]:
                NavigationController.cache["messages"][cid] = []
            self._refresh_messages()
            self._show_success("Historial de mensajes vaciado")

        bs = ft.BottomSheet(
            content=ft.Container(
                padding=ft.padding.all(16),
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.ACCOUNT_CIRCLE, color=self.primary_color, size=24),
                        ft.Text(f"{name}", size=16, weight="bold", expand=True)
                    ], spacing=10),
                    ft.Divider(),
                    ft.ListTile(leading=ft.Icon(ft.Icons.CHAT, color="#10B981"), title=ft.Text("Abrir conversación"), on_click=_open),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.UNARCHIVE_OUTLINED if is_archived else ft.Icons.ARCHIVE_OUTLINED, color="#3B82F6"),
                        title=ft.Text("Desarchivar chat" if is_archived else "Archivar chat"),
                        on_click=_toggle_archive
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DELETE_FOREVER, color="#EF4444"),
                        title=ft.Text("Borrar chat completamente", color="#EF4444"),
                        on_click=_do_delete_chat
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.DELETE_OUTLINE, color="#F59E0B"),
                        title=ft.Text("Vaciar historial de mensajes"),
                        on_click=_clear_chat
                    ),
                ], spacing=4, tight=True)
            )
        )
        self.page.open(bs)

    def _show_message_options(self, msg: dict):
        """Muestra menú de opciones al mantener presionado un mensaje."""
        content = (msg.get("content") or "").strip()
        cid = self._selected_contact.get("id") if self._selected_contact else None

        def _copy(e):
            self.page.close(bs)
            if self.page and content:
                self.page.set_clipboard(content)
                self._show_success("Mensaje copiado al portapapeles")

        def _delete(e):
            self.page.close(bs)
            from services.navigation_service import NavigationController
            if cid and "messages" in NavigationController.cache and cid in NavigationController.cache["messages"]:
                msgs = NavigationController.cache["messages"][cid]
                NavigationController.cache["messages"][cid] = [m for m in msgs if m.get("id") != msg.get("id")]
            self._refresh_messages()

        bs = ft.BottomSheet(
            content=ft.Container(
                padding=ft.padding.all(16),
                content=ft.Column([
                    ft.Text("Opciones de mensaje", size=16, weight="bold"),
                    ft.Divider(),
                    ft.ListTile(leading=ft.Icon(ft.Icons.COPY), title=ft.Text("Copiar texto"), on_click=_copy),
                    ft.ListTile(leading=ft.Icon(ft.Icons.DELETE_OUTLINE, color="#EF4444"), title=ft.Text("Eliminar mensaje", color="#EF4444"), on_click=_delete),
                ], spacing=4, tight=True)
            )
        )
        self.page.open(bs)

    def _build_contact_item(self, contact):
        """Crea item de contacto profesional con soporte para toque instantáneo y clic secundario."""
        colors = self._get_theme_colors()

        name = self._contact_display_name(contact)
        initials = name[:2].upper() if name else "U"
        is_selected = self._selected_contact and self._selected_contact["id"] == contact["id"]

        from services.navigation_service import NavigationController
        online_users = NavigationController.cache.get("online_users", [])
        is_group = contact.get("es_grupo", False)
        is_online = is_group or (contact["id"] in online_users)

        def _on_contact_click(e):
            self._select_contact(contact)

        item_container = ft.Container(
            padding=ft.padding.all(12),
            bgcolor=ft.Colors.with_opacity(0.12, self.primary_color) if is_selected else "transparent",
            border_radius=12,
            ink=True,
            on_click=_on_contact_click,
            content=ft.Row([
                ft.CircleAvatar(
                    radius=22,
                    bgcolor="#10B981" if is_group else self.primary_color,
                    content=ft.Text(initials, color="white", weight="bold", size=13)
                ),
                ft.Column([
                    ft.Text(name, size=14, weight="bold", color=colors["text"]),
                    ft.Row([
                        ft.Icon(ft.Icons.CIRCLE, size=8, color=ft.Colors.GREEN_400 if is_online else ft.Colors.GREY_400),
                        ft.Text("En línea" if is_online else "Desconectado", size=11, color=ft.Colors.GREEN_400 if is_online else ft.Colors.GREY_500),
                    ], spacing=4),
                ], expand=True, spacing=2),
            ], spacing=10)
        )

        return ft.GestureDetector(
            on_tap=_on_contact_click,
            on_long_press_start=lambda e, c=contact: self._show_contact_options(c),
            on_secondary_tap=lambda e, c=contact: self._show_contact_options(c),
            content=item_container
        )

    def _build_right_panel(self) -> ft.Container:
        """Construye el panel derecho (vacío o chat activo)."""
        colors = self._get_theme_colors()

        if not self._selected_contact:
            return ft.Container(
                expand=True,
                bgcolor=colors["background"],
                border_radius=ft.border_radius.only(top_right=20, bottom_right=20),
                alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=64, color=ft.Colors.GREY_400),
                    ft.Text(self.translate("messaging_select_contact"), size=16, color=ft.Colors.GREY_500, weight="bold"),
                    ft.Text(self.translate("messaging_empty_hint"), size=12, color=ft.Colors.GREY_400),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            )

        contact_name = self._contact_display_name(self._selected_contact)
        is_mob = self.is_mobile()

        def _go_back(e):
            self._selected_contact = None
            from services.navigation_service import NavigationController
            NavigationController.cache["selected_contact"] = None
            NavigationController.reload_current_view()

        back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=colors["text"],
            on_click=_go_back,
        ) if is_mob else ft.Container()

        return ft.Container(
            expand=True,
            bgcolor=colors["background"],
            border_radius=ft.border_radius.only(top_right=20, bottom_right=20) if not is_mob else 16,
            content=ft.Column([
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12 if is_mob else 15, vertical=10),
                    border=ft.border.only(bottom=ft.border.BorderSide(1, colors["divider"])),
                    content=ft.Row([
                        back_btn,
                        ft.CircleAvatar(
                            radius=18,
                            bgcolor=self.primary_color,
                            content=ft.Text(contact_name[:2].upper(), color="white", weight="bold", size=12),
                        ),
                        ft.Column([
                            ft.Text(contact_name, size=15, weight="bold", color=colors["text"]),
                            ft.Row([
                                ft.Icon(ft.Icons.CIRCLE, size=8, color=ft.Colors.GREEN_400),
                                ft.Text(self.translate("messaging_online"), size=11, color=ft.Colors.GREEN_400),
                            ], spacing=4),
                        ], expand=True, spacing=0),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_SWEEP,
                            icon_color="#EF4444",
                            tooltip="Vaciar todo el historial del chat",
                            on_click=self._clear_active_chat_history,
                        ),
                    ], spacing=8),
                ),
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        ref=self._messages_ref,
                        controls=[],
                        spacing=10,
                        scroll=get_scroll_mode("AUTO"),
                    ),
                    padding=ft.padding.all(12 if is_mob else 15),
                ),
                ft.Container(
                    padding=ft.padding.all(10 if is_mob else 15),
                    content=ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.ATTACH_FILE,
                            icon_color="#64748B",
                            on_click=lambda e: self._file_picker.pick_files(allow_multiple=False),
                            tooltip="Adjuntar archivo o media"
                        ),
                        ft.TextField(
                            ref=self._input_ref,
                            label=self.translate("messaging_type"),
                            expand=True,
                            border_radius=20,
                            min_lines=1,
                            max_lines=3,
                            on_submit=self._send_message,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SEND,
                            icon_color=self.primary_color,
                            on_click=self._send_message,
                        ),
                    ], spacing=6),
                ),
            ], spacing=0),
        )

    def _refresh_contacts_list(self):
        """Refresca la lista de contactos."""
        if not self._contacts_list_ref.current:
            return

        contact_controls = []
        for contact in self._filtered_contacts:
            contact_controls.append(self._build_contact_item(contact))

        if not contact_controls:
            empty_msg = "No hay chats archivados" if self._active_tab == "archivados" else "No tienes conversaciones activas"
            contact_controls.append(
                ft.Container(
                    padding=ft.padding.all(24),
                    alignment=ft.alignment.center,
                    content=ft.Column([
                        ft.Icon(ft.Icons.CHAT_OUTLINED if self._active_tab == "chats" else ft.Icons.ARCHIVE_OUTLINED, color=ft.Colors.GREY_400, size=36),
                        ft.Text(empty_msg, color=ft.Colors.GREY_500, size=13, text_align=ft.TextAlign.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)
                )
            )

        try:
            self._contacts_list_ref.current.controls = contact_controls
            self._contacts_list_ref.current.update()
        except:
            pass

    def build(self) -> ft.Control:
        self._load_contacts()
        from services.navigation_service import NavigationController
        self._selected_contact = NavigationController.cache.get("selected_contact", None)
        colors = self._get_theme_colors()
        navbar = self._build_navbar(self.translate("messaging_title"))
        is_mob = self.is_mobile()

        def _switch_tab(tab_name):
            self._active_tab = tab_name
            self._load_contacts()
            self._refresh_contacts_list()
            try: self.page.update()
            except: pass

        archived_count = len(self._archived_ids)

        tab_row = ft.Row([
            ft.TextButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHAT_OUTLINED, size=16, color=self.primary_color if self._active_tab == "chats" else "#64748B"),
                    ft.Text("Chats", color=colors["text"] if self._active_tab == "chats" else "#64748B", weight="bold" if self._active_tab == "chats" else "normal")
                ], spacing=4, tight=True),
                on_click=lambda _: _switch_tab("chats")
            ),
            ft.TextButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.ARCHIVE_OUTLINED, size=16, color=self.primary_color if self._active_tab == "archivados" else "#64748B"),
                    ft.Text(f"Archivados ({archived_count})", color=colors["text"] if self._active_tab == "archivados" else "#64748B", weight="bold" if self._active_tab == "archivados" else "normal")
                ], spacing=4, tight=True),
                on_click=lambda _: _switch_tab("archivados")
            ),
        ], spacing=4)

        # PANEL IZQUIERDO - Contactos
        left_panel = ft.Container(
            width=None if is_mob else 320,
            expand=is_mob,
            bgcolor=colors["surface"],
            border_radius=16 if is_mob else ft.border_radius.only(top_left=20, bottom_left=20),
            content=ft.Column([
                ft.Container(height=12),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12),
                    content=ft.Row([
                        ft.Text(self.translate("messaging_messages"), size=18, weight="bold", color=colors["text"]),
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.PERSON_ADD_ALT_1,
                                icon_color="#10B981",
                                tooltip="Nuevo Chat",
                                on_click=self._show_new_chat_dialog,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.GROUP_ADD,
                                icon_color="#3B82F6",
                                tooltip="Nuevo Grupo",
                                on_click=self._show_create_group_dialog,
                            ),
                        ], spacing=2)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12),
                    content=ft.TextField(
                        ref=self._search_ref,
                        label=self.translate("messaging_search"),
                        prefix_icon=ft.Icons.SEARCH,
                        border_radius=20,
                        dense=True,
                        on_change=self._search_contacts,
                    ),
                ),
                ft.Container(height=6),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12),
                    content=tab_row
                ),
                ft.Container(height=6),
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        ref=self._contacts_list_ref,
                        controls=[self._build_contact_item(c) for c in self._filtered_contacts],
                        spacing=4,
                        scroll=get_scroll_mode("AUTO"),
                    ),
                    padding=ft.padding.symmetric(horizontal=8),
                ),
                ft.Container(height=12),
            ], spacing=0)
        )

        right_panel = self._build_right_panel()
        if self._selected_contact:
            self._refresh_messages()

        if is_mob:
            if self._selected_contact:
                main_content = right_panel
            else:
                main_content = left_panel
        else:
            main_content = ft.Row(
                ref=self._main_row_ref,
                controls=[left_panel, right_panel],
                spacing=0,
                expand=True,
            )

        controls = [
            navbar,
            ft.Container(
                expand=True,
                content=main_content,
                padding=ft.padding.all(8 if is_mob else 20),
            )
        ]
        if is_mob:
            controls.append(self._build_bottom_nav("Mensajeria"))

        return ft.Column(controls, expand=True, spacing=0)
