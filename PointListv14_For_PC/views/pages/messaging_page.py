"""
pages/messaging_page.py - v19.0
PointList Mensajería Rediseñada con:
- Selección de chat 100% garantizada e instantánea
- Menú contextual flotante de Clic Derecho en las coordenadas exactas del cursor (estilo ChatBot)
- Sección y Modal de 'Chats Archivados' desplegable con botón 'Desarchivar' sin botones flotantes sobrepuestos
"""

import flet as ft
import threading
import time
import os
import uuid
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode

class MessagingPage(BasePage):
    """Página de mensajería v19.0 con gestión completa de chats archivados y desarchivado instantáneo."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db = db
        self._user = NavigationController.get_current_user()
        self._uid = self._user.get("id")
        self._contacts: list = []
        self._filtered_contacts: list = []
        self._selected_contact = None
        self._messages_ref = ft.Ref[ft.Column]()
        self._input_ref = ft.Ref[ft.TextField]()
        self._search_ref = ft.Ref[ft.TextField]()
        self._contacts_list_ref = ft.Ref[ft.Column]()
        self._right_panel_container = ft.Container(expand=True)
        self._file_picker = ft.FilePicker(on_result=self._on_file_selected)
        self.page.overlay.append(self._file_picker)

    def _contact_display_name(self, contact: dict) -> str:
        if contact.get("is_group"):
            return contact.get("name", "Grupo de Estudio")
        name = (
            contact.get("name")
            or contact.get("nombre_usuario")
            or contact.get("nombre")
            or contact.get("email")
            or "Usuario"
        )
        return str(name).strip() or "Usuario"

    def _media_kind(self, path: str) -> str | None:
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
            "sender_name": msg.get("sender_name", ""),
            "content": content,
            "timestamp": msg.get("timestamp"),
            "type": msg_type,
            "file_path": file_path,
        }

    def _load_contacts(self):
        """Carga contactos e incorpora grupos guardados."""
        from services.navigation_service import NavigationController
        
        self._contacts = NavigationController.cache.get("contacts", [])
        if not self._contacts:
            raw_users = [c for c in (self._db.obtener_todos_los_usuarios() or []) if c["id"] != self._uid]
            for idx, user in enumerate(raw_users):
                user["is_online"] = user.get("is_online", user.get("online", idx == 0))
            self._contacts = raw_users
            NavigationController.cache["contacts"] = self._contacts

        groups = NavigationController.cache.get("group_chats", [])
        if not groups:
            default_group = {
                "id": "group_default_1",
                "name": "👥 Grupo de Estudio PointList",
                "is_group": True,
                "members": ["Todos los estudiantes"],
                "description": "Espacio general para dudas y tareas compartidas.",
            }
            groups = [default_group]
            NavigationController.cache["group_chats"] = groups

        combined = list(groups) + list(self._contacts)
        self._filtered_contacts = [c for c in combined if not c.get("is_archived") and not c.get("is_deleted")]

    def _load_messages(self, contact_id):
        from services.navigation_service import NavigationController
        if "messages" not in NavigationController.cache:
            NavigationController.cache["messages"] = {}
        
        if contact_id not in NavigationController.cache["messages"]:
            is_numeric = str(contact_id).isdigit() or isinstance(contact_id, int)
            msgs = (self._db.obtener_mensajes(self._uid, contact_id) or []) if is_numeric else []
            NavigationController.cache["messages"][contact_id] = msgs
        return NavigationController.cache["messages"].get(contact_id, [])

    def _search_contacts(self, e):
        search_text = self._search_ref.current.value.lower() if self._search_ref.current else ""
        from services.navigation_service import NavigationController
        groups = NavigationController.cache.get("group_chats", [])
        all_list = [c for c in (list(groups) + list(self._contacts)) if not c.get("is_archived") and not c.get("is_deleted")]
        
        if not search_text:
            self._filtered_contacts = all_list.copy()
        else:
            self._filtered_contacts = [c for c in all_list if search_text in self._contact_display_name(c).lower() or search_text in c.get("email", "").lower()]
        self._refresh_contacts_list()

    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            file_name = e.files[0].name
            self._send_message_with_attachment(file_path, file_name)

    def _send_message_with_attachment(self, file_path, file_name):
        if not self._selected_contact:
            return
        
        contact_id = self._selected_contact["id"]
        media_kind = self._media_kind(file_path) or "file"

        new_msg = {
            "id": f"temp_{int(time.time())}",
            "sender_id": self._uid,
            "sender_name": self._user.get("name", "Tú"),
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
        
        if self._selected_contact:
            self._selected_contact["is_deleted"] = False
            self._selected_contact["is_archived"] = False
            self._search_contacts(None)

        self._refresh_messages()
        
        def save_task():
            try:
                if str(contact_id).isdigit() or isinstance(contact_id, int):
                    self._db.guardar_mensaje(self._uid, contact_id, new_msg["content"], file_path)
            except: pass
        threading.Thread(target=save_task, daemon=True).start()

    def _build_video_content(self, file_path: str, is_sender: bool) -> ft.Control:
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
        file_path = msg.get("file_path")
        content = (msg.get("content") or "").strip()
        msg_type = msg.get("type", "text")
        bubble_bg = self.primary_color if is_sender else colors["surface"]
        text_color = "white" if is_sender else colors["text"]

        is_group = self._selected_contact and self._selected_contact.get("is_group")
        sender_label = None
        if is_group and not is_sender and msg.get("sender_name"):
            sender_label = ft.Text(msg.get("sender_name"), size=10, weight="bold", color="#7C3AED")

        if file_path and msg_type in ("image", "video", "file"):
            parts: list = []
            if sender_label: parts.append(sender_label)
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
        bubble_content = [ft.Text(content, size=13, color=text_color, selectable=True)]
        if sender_label:
            bubble_content.insert(0, sender_label)

        return ft.Container(
            padding=ft.padding.all(12),
            bgcolor=bubble_bg,
            border_radius=16,
            content=ft.Column(bubble_content, spacing=4, tight=True),
            width=bubble_width,
        )

    def _send_message(self, e):
        if not self._selected_contact:
            return
        
        msg_text = self._input_ref.current.value.strip() if self._input_ref.current else ""
        if not msg_text:
            return
        
        contact_id = self._selected_contact["id"]
        
        new_msg = {
            "id": f"temp_{int(time.time())}",
            "sender_id": self._uid,
            "sender_name": self._user.get("name", "Tú"),
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
        
        if self._selected_contact:
            self._selected_contact["is_deleted"] = False
            self._selected_contact["is_archived"] = False
            if self._selected_contact not in self._contacts:
                self._contacts.append(self._selected_contact)
            self._search_contacts(None)

        if self._input_ref.current:
            self._input_ref.current.value = ""
            try: self._input_ref.current.update()
            except: pass
        self._refresh_messages()
        
        def save_task():
            try:
                if str(contact_id).isdigit() or isinstance(contact_id, int):
                    self._db.guardar_mensaje(self._uid, contact_id, msg_text)
            except: pass
        threading.Thread(target=save_task, daemon=True).start()

    def _refresh_messages(self):
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
            msg_controls.append(
                ft.Row(
                    [bubble],
                    alignment=ft.MainAxisAlignment.END if is_sender else ft.MainAxisAlignment.START,
                    spacing=10,
                )
            )
        
        try:
            self._messages_ref.current.controls = msg_controls
            self._messages_ref.current.update()
        except: pass

    def _select_contact(self, contact):
        """Selecciona un contacto y actualiza directamente el contenedor del panel derecho."""
        self._selected_contact = contact
        self._refresh_contacts_list()
        self._right_panel_container.content = self._build_right_panel_content()
        try:
            self.page.update()
        except: pass
        self._refresh_messages()

    def _delete_chat_action(self, contact):
        cid = contact["id"]
        contact["is_deleted"] = True
        contact["is_archived"] = True
        from services.navigation_service import NavigationController
        if "messages" not in NavigationController.cache:
            NavigationController.cache["messages"] = {}
        NavigationController.cache["messages"][cid] = []

        if str(cid).isdigit() or isinstance(cid, int):
            threading.Thread(
                target=lambda: self._db.borrar_mensajes_contacto(self._uid, cid),
                daemon=True
            ).start()

        if self._selected_contact and self._selected_contact["id"] == cid:
            self._selected_contact = None

        if self._messages_ref.current:
            self._messages_ref.current.controls.clear()
            try: self._messages_ref.current.update()
            except: pass

        self._search_contacts(None)
        self._right_panel_container.content = self._build_right_panel_content()
        try: self.page.update()
        except: pass

    def _archive_chat_action(self, contact):
        contact["is_archived"] = True
        if self._selected_contact and self._selected_contact["id"] == contact["id"]:
            self._selected_contact = None
        self._search_contacts(None)
        self._right_panel_container.content = self._build_right_panel_content()
        try: self.page.update()
        except: pass

    def _open_archived_chats_dialog(self, e=None):
        """Abre un modal limpio y estructurado para ver y gestionar chats archivados."""
        archived_list = ft.Column(spacing=6, scroll=get_scroll_mode("AUTO"), expand=True)

        def _unarchive(c):
            c["is_archived"] = False
            c["is_deleted"] = False
            self.page.close(dlg)
            self._search_contacts(None)
            self._select_contact(c)

        def _delete_perm(c):
            self.page.close(dlg)
            self._delete_chat_action(c)

        def _render_archived():
            from services.navigation_service import NavigationController
            groups = NavigationController.cache.get("group_chats", [])
            all_list = list(groups) + list(self._contacts)
            archived = [c for c in all_list if c.get("is_archived") and not c.get("is_deleted")]

            if not archived:
                archived_list.controls = [
                    ft.Container(
                        padding=40,
                        alignment=ft.alignment.center,
                        content=ft.Column([
                            ft.Icon(ft.Icons.ARCHIVE_OUTLINED, size=48, color="#94A3B8"),
                            ft.Text("No tienes chats archivados", color="#64748B", size=14, weight="bold"),
                            ft.Text("Los chats que me archives aparecerán aquí para desarchivarlos cuando quieras.", size=11, color="#94A3B8", text_align=ft.TextAlign.CENTER),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
                    )
                ]
            else:
                archived_list.controls = [
                    ft.Container(
                        padding=10,
                        border_radius=10,
                        bgcolor="#F8FAFC",
                        border=ft.border.all(1, "#E2E8F0"),
                        content=ft.Row([
                            ft.CircleAvatar(
                                radius=20,
                                bgcolor=self.primary_color,
                                content=ft.Text((self._contact_display_name(c))[:2].upper(), color="white", weight="bold", size=12)
                            ),
                            ft.Column([
                                ft.Text(self._contact_display_name(c), size=14, weight="bold", color="#0F172A"),
                                ft.Text("Chat Archivado", size=11, color="#64748B"),
                            ], spacing=2, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.UNARCHIVE,
                                icon_color="#7C3AED",
                                tooltip="Desarchivar (volver a lista principal)",
                                on_click=lambda e, curr=c: _unarchive(curr)
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color="#EF4444",
                                tooltip="Borrar conversación",
                                on_click=lambda e, curr=c: _delete_perm(curr)
                            ),
                        ])
                    ) for c in archived
                ]
            try: self.page.update()
            except: pass

        _render_archived()

        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Row([
                ft.Icon(ft.Icons.ARCHIVE, color="#7C3AED", size=22),
                ft.Text("Chats Archivados", size=18, weight="bold")
            ]),
            content=ft.Container(
                width=440, height=380,
                content=archived_list
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self.page.close(dlg))
            ]
        )
        self.page.open(dlg)

    def _open_new_chat_dialog(self, e=None):
        """Abre de inmediato en 0ms un modal estilo WhatsApp para iniciar un chat nuevo."""
        search_field = ft.TextField(hint_text="Buscar usuario por nombre o correo...", border_radius=10, autofocus=True)
        users_col = ft.Column(spacing=4, scroll=get_scroll_mode("AUTO"), expand=True)

        all_users = list(self._contacts)

        def _select_and_close(user):
            self.page.close(dlg)
            user["is_archived"] = False
            user["is_deleted"] = False
            if user not in self._contacts:
                self._contacts.append(user)
            self._search_contacts(None)
            self._select_contact(user)

        def _render_user_list(term=""):
            term_l = term.lower().strip()
            filtered = [u for u in all_users if not term_l or term_l in (u.get("name") or u.get("email") or "").lower()]
            users_col.controls = [
                ft.Container(
                    padding=10,
                    border_radius=10,
                    bgcolor="#F8FAFC",
                    border=ft.border.all(1, "#E2E8F0"),
                    ink=True,
                    on_click=lambda e, u=u: _select_and_close(u),
                    content=ft.Row([
                        ft.CircleAvatar(
                            radius=20,
                            bgcolor=self.primary_color,
                            content=ft.Text((u.get("name") or "U")[:2].upper(), color="white", weight="bold", size=12)
                        ),
                        ft.Column([
                            ft.Text(self._contact_display_name(u), size=14, weight="bold", color="#0F172A"),
                            ft.Text(u.get("email", ""), size=11, color="#64748B"),
                        ], spacing=2, expand=True),
                        ft.Icon(ft.Icons.CHAT_OUTLINED, color="#7C3AED", size=20)
                    ])
                ) for u in filtered
            ]
            try: self.page.update()
            except: pass

        search_field.on_change = lambda e: _render_user_list(e.control.value)
        _render_user_list("")

        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Row([
                ft.Icon(ft.Icons.CHAT, color="#7C3AED", size=24),
                ft.Text("Nuevo Chat (Estilo WhatsApp)", size=18, weight="bold")
            ]),
            content=ft.Container(
                width=440, height=400,
                content=ft.Column([
                    ft.Text("Selecciona un usuario de la comunidad para iniciar una conversación privada:", size=12, color="#64748B"),
                    ft.Container(height=8),
                    search_field,
                    ft.Container(height=12),
                    users_col,
                ], spacing=0, expand=True)
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda e: self.page.close(dlg))
            ]
        )
        self.page.open(dlg)

        def _fetch_all_bg():
            try:
                fresh = [c for c in (self._db.obtener_todos_los_usuarios() or []) if c["id"] != self._uid]
                if fresh:
                    nonlocal all_users
                    all_users = fresh
                    _render_user_list(search_field.value or "")
            except: pass
        threading.Thread(target=_fetch_all_bg, daemon=True).start()

    def _create_group_dialog(self, e):
        """Abre un modal interactivo para crear un nuevo Grupo de Estudio."""
        group_name_input = ft.TextField(hint_text="Nombre del grupo (ej: Proyecto Biología)", border_radius=10, autofocus=True)
        selected_members = []

        def _toggle_member(uid, is_checked):
            if is_checked and uid not in selected_members:
                selected_members.append(uid)
            elif not is_checked and uid in selected_members:
                selected_members.remove(uid)

        member_checkboxes = [
            ft.Checkbox(
                label=self._contact_display_name(c),
                on_change=lambda e, cid=c["id"]: _toggle_member(cid, e.control.value)
            ) for c in self._contacts
        ]

        def _save_group(e):
            g_name = group_name_input.value.strip()
            if not g_name: return
            new_group = {
                "id": f"group_{uuid.uuid4().hex[:8]}",
                "name": f"👥 {g_name}",
                "is_group": True,
                "members": selected_members + [self._uid],
            }

            from services.navigation_service import NavigationController
            groups = NavigationController.cache.get("group_chats", [])
            groups.append(new_group)
            NavigationController.cache["group_chats"] = groups

            self.page.close(dlg)
            self._search_contacts(None)
            self._select_contact(new_group)

        dlg = ft.AlertDialog(
            modal=False,
            title=ft.Text("Crear Nuevo Grupo de Estudio", size=18, weight="bold"),
            content=ft.Container(
                width=400,
                height=320,
                content=ft.Column([
                    ft.Text("Ingresa el nombre del grupo e invita a tus compañeros:", size=12, color="#64748B"),
                    ft.Container(height=8),
                    group_name_input,
                    ft.Container(height=12),
                    ft.Text("Seleccionar Miembros:", size=13, weight="bold"),
                    ft.Column(member_checkboxes, scroll=get_scroll_mode("AUTO"), expand=True),
                ], spacing=0, expand=True)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Crear Grupo", bgcolor="#16A34A", color="white", on_click=_save_group),
            ]
        )
        self.page.open(dlg)

    def _build_right_panel_content(self) -> ft.Control:
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
        is_group = self._selected_contact.get("is_group", False)
        is_online = self._selected_contact.get("is_online", False) or self._selected_contact.get("online", False)

        if is_group:
            status_indicator = ft.Row([
                ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=12, color="#7C3AED"),
                ft.Text(f"{len(self._selected_contact.get('members', []))} miembros", size=11, color="#7C3AED", weight="bold"),
            ], spacing=4)
            avatar_content = ft.Icon(ft.Icons.GROUPS, color="white", size=18)
            avatar_bg = "#7C3AED"
        else:
            status_color = ft.Colors.GREEN_400 if is_online else ft.Colors.GREY_400
            status_text = self.translate("messaging_online") if is_online else "Desconectado"
            status_indicator = ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=8, color=status_color),
                ft.Text(status_text, size=12, color=status_color),
            ], spacing=5)
            avatar_content = ft.Text(contact_name[:2].upper(), color="white", weight="bold", size=12)
            avatar_bg = self.primary_color

        contact_id = self._selected_contact["id"]
        messages = [self._normalize_message(m) for m in self._load_messages(contact_id)]
        initial_bubbles = []
        for msg in messages:
            is_sender = str(msg.get("sender_id")) == str(self._uid)
            bubble = self._build_message_bubble(msg, is_sender, colors)
            if bubble:
                initial_bubbles.append(
                    ft.Row(
                        [bubble],
                        alignment=ft.MainAxisAlignment.END if is_sender else ft.MainAxisAlignment.START,
                        spacing=10,
                    )
                )

        options_popup = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            icon_color=colors["text_secondary"],
            tooltip="Opciones de chat",
            items=[
                ft.PopupMenuItem(
                    icon=ft.Icons.DELETE_OUTLINE,
                    text="Borrar chat",
                    on_click=lambda e: self._delete_chat_action(self._selected_contact)
                ),
                ft.PopupMenuItem(
                    icon=ft.Icons.ARCHIVE,
                    text="Archivar chat",
                    on_click=lambda e: self._archive_chat_action(self._selected_contact)
                ),
            ]
        )

        return ft.Container(
            expand=True,
            bgcolor=colors["background"],
            border_radius=ft.border_radius.only(top_right=20, bottom_right=20),
            content=ft.Column([
                ft.Container(
                    padding=ft.padding.all(15),
                    bgcolor=colors["surface"],
                    border_radius=ft.border_radius.only(top_right=20),
                    content=ft.Row([
                        ft.CircleAvatar(
                            radius=20,
                            bgcolor=avatar_bg,
                            content=avatar_content,
                        ),
                        ft.Column([
                            ft.Text(contact_name, size=16, weight="bold", color=colors["text"]),
                            status_indicator,
                        ], expand=True, spacing=0),
                        options_popup,
                    ], spacing=10),
                ),
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        ref=self._messages_ref,
                        controls=initial_bubbles,
                        spacing=10,
                        scroll=get_scroll_mode("AUTO"),
                    ),
                    padding=ft.padding.all(15),
                ),
                ft.Container(
                    padding=ft.padding.all(15),
                    content=ft.Row([
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
                            icon=ft.Icons.ATTACH_FILE,
                            icon_color=self.primary_color,
                            on_click=lambda e: self._file_picker.pick_files(
                                allowed_extensions=["mp4", "avi", "mov", "jpg", "png", "pdf"]
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SEND,
                            icon_color=self.primary_color,
                            on_click=self._send_message,
                        ),
                    ], spacing=10),
                ),
            ], spacing=0),
        )

    def _refresh_contacts_list(self):
        if not self._contacts_list_ref.current:
            return
        
        contact_controls = []
        for contact in self._filtered_contacts:
            contact_controls.append(self._build_contact_item(contact))
        
        try:
            self._contacts_list_ref.current.controls = contact_controls
            self._contacts_list_ref.current.update()
        except: pass

    def _show_floating_context_menu(self, e, contact):
        """Muestra un menú contextual flotante justo en las coordenadas (x, y) donde se hizo Clic Derecho (estilo ChatBot)."""
        x = getattr(e, "global_x", 180)
        y = getattr(e, "global_y", 180)
        colors = self._get_theme_colors()

        menu_items = ft.Container(
            width=170,
            bgcolor=colors["surface"],
            border=ft.border.all(1, colors["border"]),
            border_radius=10,
            padding=ft.padding.symmetric(vertical=4),
            shadow=ft.BoxShadow(
                blur_radius=12,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
            ),
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.DELETE_OUTLINE, color="#EF4444", size=16),
                        ft.Text("Borrar chat", size=13, color="#EF4444", weight="bold")
                    ], spacing=10),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    ink=True,
                    on_click=lambda _: (_close_menu(), self._delete_chat_action(contact)),
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ARCHIVE, color="#7C3AED", size=16),
                        ft.Text("Archivar chat", size=13, color="#7C3AED", weight="bold")
                    ], spacing=10),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    ink=True,
                    on_click=lambda _: (_close_menu(), self._archive_chat_action(contact)),
                ),
            ], spacing=0, tight=True)
        )

        dismiss_detector = ft.GestureDetector(
            on_tap=lambda _: _close_menu(),
            on_secondary_tap=lambda _: _close_menu(),
            expand=True,
        )

        max_x = max(10, min(x, (self.page.width or 900) - 190))
        max_y = max(10, min(y, (self.page.height or 700) - 120))

        floating_menu = ft.Stack([
            dismiss_detector,
            ft.Container(
                content=menu_items,
                left=max_x,
                top=max_y,
            )
        ])

        def _close_menu():
            if floating_menu in self.page.overlay:
                self.page.overlay.remove(floating_menu)
            try: self.page.update()
            except: pass

        self.page.overlay.append(floating_menu)
        try: self.page.update()
        except: pass

    def _build_contact_item(self, contact):
        colors = self._get_theme_colors()
        name = self._contact_display_name(contact)
        is_selected = self._selected_contact and self._selected_contact["id"] == contact["id"]
        is_group = contact.get("is_group", False)
        is_online = contact.get("is_online", False) or contact.get("online", False)

        if is_group:
            avatar = ft.CircleAvatar(
                radius=22,
                bgcolor="#7C3AED",
                content=ft.Icon(ft.Icons.GROUPS, color="white", size=18)
            )
            sub_indicator = ft.Row([
                ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=10, color="#7C3AED"),
                ft.Text(f"{len(contact.get('members', []))} miembros", size=11, color="#7C3AED", weight="w500"),
            ], spacing=4)
        else:
            initials = name[:2].upper() if name else "U"
            avatar = ft.CircleAvatar(
                radius=22,
                bgcolor=self.primary_color,
                content=ft.Text(initials, color="white", weight="bold", size=13)
            )
            status_color = ft.Colors.GREEN_400 if is_online else ft.Colors.GREY_400
            status_text = self.translate("messaging_online") if is_online else "Desconectado"
            sub_indicator = ft.Row([
                ft.Icon(ft.Icons.CIRCLE, size=8, color=status_color),
                ft.Text(status_text, size=11, color=status_color),
            ], spacing=5)

        options_popup = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            icon_size=18,
            icon_color="#94A3B8",
            tooltip="Opciones de chat",
            items=[
                ft.PopupMenuItem(
                    icon=ft.Icons.DELETE_OUTLINE,
                    text="Borrar chat",
                    on_click=lambda e, c=contact: self._delete_chat_action(c)
                ),
                ft.PopupMenuItem(
                    icon=ft.Icons.ARCHIVE,
                    text="Archivar chat",
                    on_click=lambda e, c=contact: self._archive_chat_action(c)
                ),
            ]
        )

        clickable_item = ft.Container(
            content=ft.Row([
                avatar,
                ft.Column([
                    ft.Text(name, size=13, weight="bold", color=colors["text"], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    sub_indicator,
                ], expand=True, spacing=2),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            on_click=lambda e, c=contact: self._select_contact(c),
        )

        item_row = ft.Row([
            clickable_item,
            options_popup,
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.GestureDetector(
            on_secondary_tap_down=lambda e, c=contact: self._show_floating_context_menu(e, c),
            content=ft.Container(
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                bgcolor=ft.Colors.with_opacity(0.14, self.primary_color) if is_selected else "transparent",
                border_radius=12,
                ink=True,
                content=item_row
            )
        )

    def build(self) -> ft.Control:
        self._load_contacts()
        colors = self._get_theme_colors()
        navbar = self._build_navbar(self.translate("messaging_title"))

        new_chat_btn = ft.IconButton(
            icon=ft.Icons.PERSON_ADD_ALT_1,
            icon_color="#7C3AED",
            icon_size=20,
            tooltip="Nuevo Chat con Usuario",
            on_click=self._open_new_chat_dialog,
        )

        archived_btn = ft.IconButton(
            icon=ft.Icons.ARCHIVE,
            icon_color="#7C3AED",
            icon_size=20,
            tooltip="Chats Archivados",
            on_click=self._open_archived_chats_dialog,
        )

        create_group_btn = ft.IconButton(
            icon=ft.Icons.GROUP_ADD,
            icon_color="#7C3AED",
            icon_size=20,
            tooltip="Crear Grupo de Estudio",
            on_click=self._create_group_dialog,
        )

        from services.navigation_service import NavigationController
        groups = NavigationController.cache.get("group_chats", [])
        archived_count = len([c for c in (list(groups) + list(self._contacts)) if c.get("is_archived") and not c.get("is_deleted")])

        archived_banner = ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            margin=ft.padding.only(left=10, right=10, bottom=6),
            bgcolor="#F1F5F9" if self.page and self.page.theme_mode != ft.ThemeMode.DARK else "#334155",
            border_radius=10,
            ink=True,
            on_click=self._open_archived_chats_dialog,
            content=ft.Row([
                ft.Icon(ft.Icons.ARCHIVE, size=18, color="#7C3AED"),
                ft.Text("Archivados", size=13, weight="bold", color=colors["text"]),
                ft.Container(expand=True),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    bgcolor="#7C3AED",
                    border_radius=10,
                    content=ft.Text(str(archived_count), size=10, color="white", weight="bold")
                )
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        ) if archived_count > 0 else ft.Container()

        left_panel = ft.Container(
            width=300,
            bgcolor=colors["surface"],
            border_radius=ft.border_radius.only(top_left=20, bottom_left=20),
            content=ft.Column([
                ft.Container(height=12),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=15),
                    content=ft.Row([
                        ft.Text(self.translate("messaging_messages"), size=16, weight="bold", color=colors["text"]),
                        ft.Container(expand=True),
                        archived_btn,
                        new_chat_btn,
                        create_group_btn,
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                ft.Container(height=10),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=15),
                    content=ft.TextField(
                        ref=self._search_ref,
                        label=self.translate("messaging_search"),
                        prefix_icon=ft.Icons.SEARCH,
                        border_radius=20,
                        height=42,
                        content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
                        on_change=self._search_contacts,
                    ),
                ),
                ft.Container(height=8),
                archived_banner,
                ft.Container(
                    expand=True,
                    content=ft.Column(
                        ref=self._contacts_list_ref,
                        controls=[self._build_contact_item(c) for c in self._filtered_contacts],
                        spacing=4,
                        scroll=get_scroll_mode("AUTO"),
                    ),
                    padding=ft.padding.symmetric(horizontal=10),
                ),
                ft.Container(height=12),
            ], spacing=0)
        )

        self._right_panel_container.content = self._build_right_panel_content()
        if self._selected_contact:
            self._refresh_messages()

        main_content = ft.Row(
            controls=[
                left_panel,
                self._right_panel_container,
            ],
            spacing=0,
            expand=True,
        )

        return ft.Column([
            navbar,
            ft.Container(
                expand=True,
                content=main_content,
                padding=ft.padding.all(20),
            )
        ], expand=True, spacing=0)
