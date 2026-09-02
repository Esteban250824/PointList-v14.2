"""
views/pages/messaging_page.py
PointList v14.2
Mensajería Rediseñada Figma (Imagen 4):
- Barra lateral izquierda con accesos rápidos (Chats, Grupos, Contactos, Configuración, Modo Oscuro)
- Panel central de conversaciones con buscador, filtros tipo píldora y avatares de iniciales coloreadas
- Ventana de chat activa con fecha "Hoy", reacciones de emojis (❤️ 4, 👍 2), doble check (✓✓) e input estilizado
"""

import flet as ft
import threading
import time
import os
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode


class MessagingPage(BasePage):
    """Página de mensajería rediseñada idéntica a Figma (Imagen 4)."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db = db
        self._user = NavigationController.get_current_user()
        self._uid = self._user.get("id") if self._user else None
        self._contacts: list = []
        self._filtered_contacts: list = []
        self._selected_contact = None
        self._active_filter = "Todos"
        
        self._messages_ref = ft.Ref[ft.Column]()
        self._input_ref = ft.Ref[ft.TextField]()
        self._search_ref = ft.Ref[ft.TextField]()
        self._contacts_list_ref = ft.Ref[ft.Column]()
        self._right_panel_container = ft.Container(expand=True)
        self._file_picker = ft.FilePicker(on_result=self._on_file_selected)
        if self.page and hasattr(self.page, "overlay"):
            self.page.overlay.append(self._file_picker)
        self._poller_started = False
        self._start_realtime_poller()

    def _start_realtime_poller(self):
        """Hilo en segundo plano para sincronizar mensajes en tiempo real."""
        if hasattr(self, "_poller_started") and self._poller_started:
            return
        self._poller_started = True

        def _poll_loop():
            import copy
            while True:
                time.sleep(0.5)
                try:
                    if not self.page or not self._uid: continue
                    if self._selected_contact:
                        cid = self._selected_contact.get("id")
                        if cid and (str(cid).isdigit() or isinstance(cid, int)):
                            db_msgs = self._db.obtener_mensajes(self._uid, cid) or []
                            from services.navigation_service import NavigationController
                            if "messages" not in NavigationController.cache:
                                NavigationController.cache["messages"] = {}
                            old_msgs = NavigationController.cache["messages"].get(cid, [])
                            if len(db_msgs) > len(old_msgs):
                                NavigationController.cache["messages"][cid] = copy.deepcopy(db_msgs)
                                self._refresh_messages()
                except Exception: pass

        threading.Thread(target=_poll_loop, daemon=True).start()

    def _contact_display_name(self, contact: dict) -> str:
        if contact.get("is_group"):
            return contact.get("name", "Grupo de Estudio PointList")
        name = (
            contact.get("name")
            or contact.get("nombre_usuario")
            or contact.get("nombre")
            or contact.get("email")
            or "Usuario"
        )
        return str(name).strip() or "Usuario"

    def _get_avatar_color(self, name: str) -> str:
        """Devuelve un color de avatar vibrante e idéntico a Figma."""
        colors_list = ["#7C3AED", "#2563EB", "#059669", "#D97706", "#DC2626", "#4F46E5", "#9333EA"]
        idx = sum(ord(c) for c in name) % len(colors_list)
        return colors_list[idx]

    def _load_contacts(self):
        """Carga los contactos y el grupo por defecto."""
        from services.navigation_service import NavigationController
        self._contacts = NavigationController.cache.get("contacts", [])
        if not self._contacts:
            raw_users = [c for c in (self._db.obtener_todos_los_usuarios() or []) if self._uid and c["id"] != self._uid]
            if not raw_users:
                raw_users = [
                    {"id": "usr_1", "name": "María", "email": "maria@pointlist.edu", "role": "estudiante"},
                    {"id": "usr_2", "name": "Yei", "email": "yei@pointlist.edu", "role": "estudiante"},
                    {"id": "usr_3", "name": "Ezequiel Deliser", "email": "ezequiel@pointlist.edu", "role": "estudiante"},
                    {"id": "usr_4", "name": "Jessie Campbell", "email": "jessie@pointlist.edu", "role": "estudiante"},
                    {"id": "usr_5", "name": "Omario Bailey", "email": "omario@pointlist.edu", "role": "estudiante"},
                    {"id": "usr_6", "name": "Juan Garces", "email": "juan.g@pointlist.edu", "role": "estudiante"},
                    {"id": "usr_7", "name": "Mario Acosta", "email": "mario@pointlist.edu", "role": "estudiante"},
                    {"id": "usr_8", "name": "Yasmin Rodríguez", "email": "yasmin@pointlist.edu", "role": "estudiante"},
                    {"id": "usr_9", "name": "Sureimi Zuñiga", "email": "sureimi@pointlist.edu", "role": "estudiante"},
                    {"id": "usr_10", "name": "Joel Ellis", "email": "joel@pointlist.edu", "role": "estudiante"},
                ]
            self._contacts = raw_users
            NavigationController.cache["contacts"] = self._contacts

        groups = NavigationController.cache.get("group_chats", [])
        if not groups:
            default_group = {
                "id": "group_default_1",
                "name": "Grupo de estudio PointList",
                "is_group": True,
                "members": ["María", "Yei", "Ezequiel", "Jessie", "Omario", "Juan", "Mario", "Yasmin", "Sureimi", "Joel", "Tú"],
                "unread": 2,
                "last_msg": "María: No olviden revisar el ejercicio 3",
                "time": "3:45 p.m."
            }
            groups = [default_group]
            NavigationController.cache["group_chats"] = groups

        combined = list(groups) + list(self._contacts)
        self._filtered_contacts = combined
        if not self._selected_contact and combined:
            self._selected_contact = combined[0]

    def _select_contact(self, contact):
        self._selected_contact = contact
        self._refresh_contacts_list()
        self._right_panel_container.content = self._build_right_panel_content()
        try: self.page.update()
        except: pass
        self._refresh_messages()

    def _send_message(self, e=None):
        if not self._input_ref.current or not self._input_ref.current.value.strip():
            return
        msg_text = self._input_ref.current.value.strip()
        self._input_ref.current.value = ""

        if not self._selected_contact:
            return

        cid = self._selected_contact["id"]
        from services.navigation_service import NavigationController
        if "messages" not in NavigationController.cache:
            NavigationController.cache["messages"] = {}
        if cid not in NavigationController.cache["messages"]:
            NavigationController.cache["messages"][cid] = []

        new_msg = {
            "id": f"msg_{int(time.time())}",
            "emisor_id": self._uid,
            "sender_name": self._user.get("name", "Tú") if self._user else "Tú",
            "contenido": msg_text,
            "timestamp": "3:42 p.m.",
            "is_user": True,
        }
        NavigationController.cache["messages"][cid].append(new_msg)
        self._refresh_messages()

        def _bg_save():
            try:
                if str(cid).isdigit() or isinstance(cid, int):
                    self._db.guardar_mensaje(self._uid, cid, msg_text)
            except: pass
        threading.Thread(target=_bg_save, daemon=True).start()

    def _on_file_selected(self, e: ft.FilePickerResultEvent):
        if e.files:
            file_name = e.files[0].name
            if self._input_ref.current:
                self._input_ref.current.value = f"[Archivo: {file_name}]"
                self._send_message()

    def _build_left_icon_sidebar(self) -> ft.Control:
        """Columna 1: Barra lateral de iconos rápida (Figma Imagen 4)."""
        colors = self._get_theme_colors()
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK

        def _toggle_theme(e):
            self.page.theme_mode = ft.ThemeMode.LIGHT if is_dark else ft.ThemeMode.DARK
            self.page.update()

        return ft.Container(
            width=68,
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["border"]),
            border_radius=20,
            padding=ft.padding.symmetric(vertical=20, horizontal=10),
            content=ft.Column([
                # Icono Chat Seleccionado (Fondo negro u oscuro)
                ft.Container(
                    width=44, height=44, border_radius=14,
                    bgcolor="#0F172A" if not is_dark else "#1E293B",
                    alignment=ft.alignment.center,
                    content=ft.Icon(ft.Icons.CHAT_BUBBLE_ROUNDED, color="white", size=20)
                ),
                ft.Container(height=16),
                ft.IconButton(ft.Icons.GROUPS_OUTLINED, icon_color="#64748B", icon_size=22, tooltip="Grupos"),
                ft.IconButton(ft.Icons.PERSON_ADD_OUTLINED, icon_color="#64748B", icon_size=22, tooltip="Agregar contacto"),
                ft.IconButton(ft.Icons.SETTINGS_OUTLINED, icon_color="#64748B", icon_size=22, tooltip="Configuración"),
                ft.Container(expand=True),
                # Botón Modo Oscuro al final
                ft.IconButton(
                    ft.Icons.NIGHTLIGHT_OUTLINED if not is_dark else ft.Icons.WB_SUNNY_OUTLINED,
                    icon_color="#0F172A" if not is_dark else "#F59E0B",
                    icon_size=22,
                    tooltip="Cambiar tema",
                    on_click=_toggle_theme
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def _build_middle_chat_list(self) -> ft.Control:
        """Columna 2: Panel de contactos y conversaciones (Figma Imagen 4)."""
        colors = self._get_theme_colors()

        # Cabecera de Mensajes + Botón Redactar
        header_row = ft.Row([
            ft.Text("Mensajes", size=20, weight=ft.FontWeight.BOLD, color=colors["text"]),
            ft.Container(expand=True),
            ft.Container(
                width=36, height=36, border_radius=10,
                border=ft.border.all(1, "#E2E8F0"),
                alignment=ft.alignment.center,
                content=ft.Icon(ft.Icons.EDIT_OUTLINED, color="#0F172A", size=18)
            )
        ])

        # Campo de Búsqueda
        search_field = ft.TextField(
            ref=self._search_ref,
            hint_text="Buscar usuario o grupos",
            prefix_icon=ft.Icons.SEARCH,
            suffix_icon=ft.Icons.TUNE,
            border_radius=12,
            bgcolor=colors["surface"],
            border_color="#E2E8F0",
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
            text_size=12,
        )

        # Filtros Píldora
        pills = ["Todos", "No leídos", "Grupos", "Favoritos"]
        pill_controls = []
        for p in pills:
            is_active = self._active_filter == p
            pill_controls.append(
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    border_radius=16,
                    bgcolor="#DCFCE7" if is_active else "#F1F5F9",
                    content=ft.Text(p, size=11, weight="bold", color="#15803D" if is_active else "#64748B"),
                    ink=True,
                    on_click=lambda e, name=p: self._set_filter(name)
                )
            )
        filter_row = ft.Row(pill_controls, spacing=6, scroll=ft.ScrollMode.HIDDEN)

        # Lista de contactos
        self._contacts_list_ref.current = ft.Column(spacing=4, scroll=get_scroll_mode(self.page))
        self._refresh_contacts_list()

        return ft.Container(
            width=320,
            bgcolor=colors["card_bg"],
            border=ft.border.all(1, colors["border"]),
            border_radius=20,
            padding=16,
            content=ft.Column([
                header_row,
                ft.Container(height=12),
                search_field,
                ft.Container(height=10),
                filter_row,
                ft.Container(height=10),
                ft.Container(content=self._contacts_list_ref.current, expand=True)
            ], spacing=0)
        )

    def _set_filter(self, filter_name: str):
        self._active_filter = filter_name
        self._refresh_contacts_list()

    def _build_contact_tile(self, contact: dict) -> ft.Control:
        """Construye un elemento de la lista de chats estilo Figma."""
        colors = self._get_theme_colors()
        name = self._contact_display_name(contact)
        is_selected = self._selected_contact and self._selected_contact["id"] == contact["id"]
        is_group = contact.get("is_group", False)

        if is_group:
            avatar = ft.CircleAvatar(
                radius=20,
                bgcolor="#0F172A",
                content=ft.Icon(ft.Icons.GROUPS, color="white", size=18)
            )
            subtitle = contact.get("last_msg", "María: No olviden revisar el ejercicio 3")
            time_str = contact.get("time", "3:45 p.m.")
            unread = contact.get("unread", 2)
        else:
            initials = name[:2].upper() if len(name) >= 2 else name[:1].upper()
            avatar = ft.CircleAvatar(
                radius=20,
                bgcolor=self._get_avatar_color(name),
                content=ft.Text(initials, color="white", weight="bold", size=12)
            )
            subtitle = contact.get("last_msg", "Tú: De acuerdo")
            time_str = contact.get("time", "3:15 p.m.")
            unread = 0

        unread_badge = ft.Container(
            width=20, height=20, border_radius=10, bgcolor="#22C55E",
            alignment=ft.alignment.center,
            content=ft.Text(str(unread), size=10, weight="bold", color="white")
        ) if unread > 0 else ft.Container()

        return ft.Container(
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border_radius=14,
            bgcolor="#F0FDF4" if is_selected else "transparent",
            ink=True,
            on_click=lambda e, c=contact: self._select_contact(c),
            content=ft.Row([
                avatar,
                ft.Container(width=10),
                ft.Column([
                    ft.Row([
                        ft.Text(name, size=13, weight=ft.FontWeight.BOLD, color=colors["text"], expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(time_str, size=10, color="#94A3B8")
                    ]),
                    ft.Row([
                        ft.Text(subtitle, size=11, color="#64748B", expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        unread_badge
                    ])
                ], spacing=2, expand=True)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def _refresh_contacts_list(self):
        if not self._contacts_list_ref.current: return
        items = []
        for c in self._filtered_contacts:
            items.append(self._build_contact_tile(c))
        self._contacts_list_ref.current.controls = items

    def _refresh_messages(self):
        if not self._messages_ref.current or not self._selected_contact: return
        cid = self._selected_contact["id"]
        msgs = self._load_messages(cid)

        # Si es el grupo por defecto y no hay mensajes en caché, renderizar la maqueta exacta de Figma (Imagen 4)
        if not msgs and self._selected_contact.get("is_group"):
            msgs = [
                {"sender_name": "María", "initials": "M", "color": "#7C3AED", "content": "¡Hola a todos! ¿Listos para la sesión de estudio de hoy?", "time": "3:40 p.m.", "reaction": "❤️ 4", "is_user": False},
                {"sender_name": "Ezequiel Deliser", "initials": "ED", "color": "#7C3AED", "content": "¡Sí! ¿A qué hora empezamos?", "time": "3:41 p.m.", "is_user": False},
                {"sender_name": "Tú", "content": "Podemos empezar a las 4:00 p.m.", "time": "3:42 p.m.", "is_user": True, "read": True},
                {"sender_name": "Omario Bailey", "initials": "OB", "color": "#7C3AED", "content": "Perfecto para mí", "time": "3:43 p.m.", "reaction": "👍 2", "is_user": False},
                {"sender_name": "María", "initials": "M", "color": "#7C3AED", "content": "No olviden revisar el ejercicio 3 antes de la sesión", "time": "3:44 p.m.", "reaction": "❤️ 2", "is_user": False},
            ]

        bubbles = []

        # Separador de fecha "Hoy"
        bubbles.append(
            ft.Row([
                ft.Text("Hoy", size=11, color="#94A3B8", weight="500")
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

        for m in msgs:
            is_user = m.get("is_user") or str(m.get("emisor_id")) == str(self._uid)
            sender_name = m.get("sender_name") or m.get("emisor") or "Usuario"
            content = m.get("contenido") or m.get("content") or ""
            time_str = m.get("timestamp") or m.get("time") or "Ahora"
            if isinstance(time_str, float):
                time_str = time.strftime("%I:%M %p", time.localtime(time_str))

            reaction = m.get("reaction")

            if is_user:
                # Burbuja Enviada (Verde claro #DCFCE7 derecha)
                b_content = ft.Column([
                    ft.Text(content, size=13, color="#0F172A"),
                    ft.Row([
                        ft.Text(str(time_str), size=9.5, color="#64748B"),
                        ft.Icon(ft.Icons.DONE_ALL, size=14, color="#2563EB")
                    ], alignment=ft.MainAxisAlignment.END, spacing=4)
                ], spacing=2)

                bubble = ft.Container(
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                    bgcolor="#DCFCE7",
                    border_radius=ft.border_radius.only(top_left=16, top_right=16, bottom_left=16, bottom_right=4),
                    content=b_content,
                    constraints=ft.BoxConstraints(max_width=420)
                )

                bubbles.append(ft.Row([bubble], alignment=ft.MainAxisAlignment.END))

            else:
                # Burbuja Recibida (Blanca izquierda)
                initials = m.get("initials") or (sender_name[:2].upper() if len(sender_name) >= 2 else "U")
                avatar_col = m.get("color") or self._get_avatar_color(sender_name)

                avatar = ft.CircleAvatar(
                    radius=16,
                    bgcolor=avatar_col,
                    content=ft.Text(initials, color="white", weight="bold", size=10)
                )

                b_content = ft.Column([
                    ft.Text(sender_name, size=11, weight="bold", color="#2563EB"),
                    ft.Text(content, size=13, color="#0F172A"),
                    ft.Text(str(time_str), size=9.5, color="#94A3B8", text_align=ft.TextAlign.RIGHT)
                ], spacing=2)

                bubble_card = ft.Container(
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                    bgcolor="#FFFFFF",
                    border=ft.border.all(1, "#E2E8F0"),
                    border_radius=ft.border_radius.only(top_left=16, top_right=16, bottom_left=4, bottom_right=16),
                    content=b_content,
                    constraints=ft.BoxConstraints(max_width=420)
                )

                reaction_badge = ft.Container(
                    padding=ft.padding.symmetric(horizontal=8, vertical=3),
                    bgcolor="#FFFFFF",
                    border=ft.border.all(1, "#E2E8F0"),
                    border_radius=10,
                    content=ft.Text(reaction, size=10)
                ) if reaction else None

                msg_column = ft.Column([
                    bubble_card,
                    reaction_badge if reaction_badge else ft.Container()
                ], spacing=2)

                bubbles.append(
                    ft.Row([
                        avatar,
                        ft.Container(width=8),
                        msg_column
                    ], vertical_alignment=ft.CrossAxisAlignment.START)
                )

        try:
            self._messages_ref.current.controls = bubbles
            self._messages_ref.current.update()
        except: pass

    def _load_messages(self, contact_id):
        from services.navigation_service import NavigationController
        if "messages" not in NavigationController.cache:
            NavigationController.cache["messages"] = {}
        return NavigationController.cache["messages"].get(contact_id, [])

    def _build_right_panel_content(self) -> ft.Control:
        """Columna 3: Ventana de conversación activa (Figma Imagen 4)."""
        colors = self._get_theme_colors()

        if not self._selected_contact:
            return ft.Container(
                expand=True,
                bgcolor="#F8FAFC",
                border_radius=20,
                alignment=ft.alignment.center,
                content=ft.Text("Selecciona una conversación para comenzar a chatear", color="#94A3B8")
            )

        contact_name = self._contact_display_name(self._selected_contact)
        is_group = self._selected_contact.get("is_group", False)

        header = ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            bgcolor=colors["surface"],
            border=ft.border.all(1, "#E2E8F0"),
            border_radius=ft.border_radius.only(top_left=20, top_right=20),
            content=ft.Row([
                ft.CircleAvatar(
                    radius=18,
                    bgcolor="#0F172A" if is_group else self._get_avatar_color(contact_name),
                    content=ft.Icon(ft.Icons.GROUPS, color="white", size=18) if is_group else ft.Text(contact_name[:2].upper(), color="white", size=11, weight="bold")
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(contact_name, size=15, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text("11 miembros" if is_group else "En línea", size=10.5, color="#64748B"),
                ], spacing=0, expand=True),
                ft.IconButton(ft.Icons.SEARCH, icon_color="#64748B", icon_size=20),
                ft.IconButton(ft.Icons.PERSON_ADD_OUTLINED, icon_color="#64748B", icon_size=20),
                ft.IconButton(ft.Icons.MORE_VERT, icon_color="#64748B", icon_size=20),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        self._messages_ref.current = ft.Column(spacing=12, scroll=get_scroll_mode(self.page))

        input_bar = ft.Container(
            padding=ft.padding.all(14),
            bgcolor=colors["surface"],
            border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20),
            content=ft.Row([
                ft.IconButton(
                    ft.Icons.ATTACH_FILE,
                    icon_color="#64748B",
                    icon_size=22,
                    on_click=lambda e: self._file_picker.pick_files()
                ),
                ft.TextField(
                    ref=self._input_ref,
                    hint_text="Escribe un mensaje....",
                    border_radius=24,
                    bgcolor="#F8FAFC",
                    border_color="#E2E8F0",
                    content_padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    expand=True,
                    on_submit=self._send_message,
                ),
                ft.IconButton(ft.Icons.INSERT_EMOTICON, icon_color="#64748B", icon_size=22),
                ft.Container(
                    width=40, height=40, border_radius=20,
                    bgcolor="#22C55E",
                    alignment=ft.alignment.center,
                    ink=True,
                    on_click=self._send_message,
                    content=ft.Icon(ft.Icons.SEND_ROUNDED, color="white", size=18)
                )
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        return ft.Container(
            expand=True,
            bgcolor="#F8FAFC",
            border=ft.border.all(1, colors["border"]),
            border_radius=20,
            content=ft.Column([
                header,
                ft.Container(
                    content=self._messages_ref.current,
                    expand=True,
                    padding=16
                ),
                input_bar
            ], spacing=0)
        )

    def build(self) -> ft.Control:
        self._load_contacts()
        colors = self._get_theme_colors()
        navbar = self._build_navbar(self.translate("messaging_title"))

        self._right_panel_container.content = self._build_right_panel_content()

        messaging_layout = ft.Row([
            self._build_left_icon_sidebar(),
            ft.Container(width=12),
            self._build_middle_chat_list(),
            ft.Container(width=12),
            self._right_panel_container
        ], expand=True, spacing=0)

        main_content = ft.Container(
            expand=True,
            padding=ft.padding.all(16),
            bgcolor=colors["background"],
            content=messaging_layout
        )

        return ft.Column([
            navbar,
            main_content
        ], expand=True, spacing=0)
