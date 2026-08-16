"""
views/pages/chatbot_page.py
PointBit AI v12: Zero Latency - Diseño Figma de 3 columnas completo.
Soporte Multiformato (PDF, DOCX, TXT, MD, CSV, JSON, PNG, JPG).
"""

import flet as ft
import uuid
import time
import threading
import os
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode

class ChatBotPage(BasePage):
    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db = db
        self._user = NavigationController.get_current_user()
        self._uid = self._user.get("id")
        
        # Estado local
        self._sessions = NavigationController.cache.get("chatbot_sessions", [])
        self._current_session_id = self.page.client_storage.get(f"last_chatbot_session_{self._uid}")
        self._is_typing = False
        self._stop_sync = False
        
        # Referencias UI
        self._chat_list = ft.ListView(
            expand=True,
            spacing=15,
            padding=ft.padding.all(20),
            auto_scroll=True,
        )
        self._sessions_column = ft.Column(scroll=get_scroll_mode("AUTO"), spacing=5)
        
        self._input_field = ft.TextField(
            hint_text="Escribe tu mensaje aquí...",
            expand=True,
            border_color=ft.Colors.TRANSPARENT,
            on_submit=self._send_message,
            content_padding=ft.padding.all(10),
            color="#0F172A",
            hint_style=ft.TextStyle(color="#94A3B8"),
            multiline=False,
        )
        
        self._attached_files: list[dict] = []
        self._file_badge = ft.Container(visible=True, content=None)
        self._chat_container = ft.Container(expand=True)
        self._file_picker = ft.FilePicker(on_result=self._on_file_result)
        self.page.overlay.append(self._file_picker)

        # Cargar estado inicial
        self._load_initial_state()

        # Sincronización en background
        threading.Thread(target=self._sync_sessions_background, daemon=True).start()

    def is_mobile(self) -> bool:
        """Determina si la app está en modo móvil."""
        try:
            return bool(self.page and self.page.width and self.page.width < 768)
        except:
            return False

    def _load_initial_state(self):
        """Carga el estado inicial desde el caché o la base de datos."""
        from services.navigation_service import NavigationController
        self._sessions = NavigationController.cache.get("chatbot_sessions", [])
        if not self._sessions:
            try:
                self._sessions = self._db.obtener_sesiones_chatbot(self._uid) or []
                NavigationController.cache["chatbot_sessions"] = self._sessions
            except Exception as ex:
                self._sessions = []

        self._sessions_column.controls = [self._build_session_item(s) for s in self._sessions]
        
        if self._current_session_id:
            exists = any(s["session_id"] == self._current_session_id for s in self._sessions)
            if not exists and self._sessions:
                self._current_session_id = self._sessions[0]["session_id"]
            elif not exists:
                self._current_session_id = None

        if not self._current_session_id:
            self._new_chat(silent=True)
        else:
            self._select_session(self._current_session_id, update_ui=False)

    def _sync_sessions_background(self):
        """Sincroniza sesiones en background sin sobrescribir si hay error de DB."""
        time.sleep(15.0)
        while not self._stop_sync:
            try:
                if self._is_typing:
                    time.sleep(10.0)
                    continue

                from services.navigation_service import NavigationController
                new_sessions = self._db.obtener_sesiones_chatbot(self._uid)
                
                if new_sessions and new_sessions != self._sessions:
                    self._sessions = new_sessions
                    NavigationController.cache["chatbot_sessions"] = new_sessions
                    self._sessions_column.controls = [self._build_session_item(s) for s in self._sessions]
                    try: self.page.update()
                    except: pass
                
                if self._current_session_id and not self._is_typing:
                    new_history = self._db.obtener_historial_chatbot(self._uid, self._current_session_id)
                    cached_history = NavigationController.cache.get("chatbot_histories", {}).get(self._current_session_id, [])
                    
                    if new_history and (len(new_history) != len(cached_history) or (cached_history and new_history[-1] != cached_history[-1])):
                        NavigationController.cache["chatbot_histories"][self._current_session_id] = new_history
                        
                        self._chat_list.controls.clear()
                        for interaction in new_history:
                            self._chat_list.controls.append(self._build_message_bubble(interaction["pregunta"], is_user=True))
                            self._chat_list.controls.append(self._build_message_bubble(interaction["respuesta"], is_user=False))
                        
                        try:
                            self.page.update()
                            self._chat_list.scroll_to(offset=-1, duration=50)
                        except: pass
            except: pass
            time.sleep(12.0)

    def _select_session(self, session_id: str, update_ui=True):
        from services.navigation_service import NavigationController
        self._current_session_id = session_id
        
        def save_session_async():
            try: self.page.client_storage.set(f"last_chatbot_session_{self._uid}", session_id)
            except: pass
        threading.Thread(target=save_session_async, daemon=True).start()
        
        history = NavigationController.cache.get("chatbot_histories", {}).get(session_id, None)
        if history is None:
            try:
                history = self._db.obtener_historial_chatbot(self._uid, session_id) or []
            except Exception:
                history = []
            if "chatbot_histories" not in NavigationController.cache:
                NavigationController.cache["chatbot_histories"] = {}
            NavigationController.cache["chatbot_histories"][session_id] = history

        self._chat_list.controls.clear()
        
        if history:
            for interaction in history:
                self._chat_list.controls.append(self._build_message_bubble(interaction["pregunta"], is_user=True))
                self._chat_list.controls.append(self._build_message_bubble(interaction["respuesta"], is_user=False))
        else:
            is_mob = self.is_mobile()
            self._chat_list.controls.append(
                ft.Container(
                    content=self._build_quick_cards(),
                    alignment=ft.alignment.center,
                    padding=12 if is_mob else 40
                )
            )
        
        self._sessions_column.controls = [self._build_session_item(s) for s in self._sessions]
        
        if update_ui:
            try:
                self.page.update()
                self._chat_list.scroll_to(offset=-1, duration=50)
            except: pass

    def _new_chat(self, e=None, silent=False):
        from services.navigation_service import NavigationController
        new_id = str(uuid.uuid4())
        
        new_session = {
            "session_id": new_id,
            "titulo": "Nueva conversación",
            "actualizado_en": None
        }
        
        self._sessions.insert(0, new_session)
        NavigationController.cache["chatbot_sessions"] = self._sessions
        if "chatbot_histories" not in NavigationController.cache:
            NavigationController.cache["chatbot_histories"] = {}
        NavigationController.cache["chatbot_histories"][new_id] = []
        
        self._current_session_id = new_id
        self.page.client_storage.set(f"last_chatbot_session_{self._uid}", new_id)
        
        is_mob = self.is_mobile()
        self._chat_list.controls.clear()
        self._chat_list.controls.append(
            ft.Container(
                content=self._build_quick_cards(),
                alignment=ft.alignment.center,
                padding=12 if is_mob else 40
            )
        )
        self._sessions_column.controls = [self._build_session_item(s) for s in self._sessions]
        
        if not silent:
            try:
                self.page.update()
                self._input_field.focus()
            except: pass
        
        threading.Thread(
            target=lambda: self._db.crear_sesion_chatbot(self._uid, new_id, "Nueva conversación"),
            daemon=True
        ).start()

    def _delete_session(self, session_id: str):
        from services.navigation_service import NavigationController
        self._sessions = [s for s in self._sessions if s["session_id"] != session_id]
        NavigationController.cache["chatbot_sessions"] = self._sessions
        if session_id in NavigationController.cache["chatbot_histories"]:
            del NavigationController.cache["chatbot_histories"][session_id]
        
        self._sessions_column.controls = [self._build_session_item(s) for s in self._sessions]
        
        if self._current_session_id == session_id:
            if self._sessions:
                self._select_session(self._sessions[0]["session_id"], update_ui=True)
            else:
                self._new_chat(silent=True)
        else:
            try: self.page.update()
            except: pass
        
        threading.Thread(target=lambda: self._db.borrar_sesion_chatbot(session_id), daemon=True).start()

    def _build_session_item(self, session: dict) -> ft.Container:
        sid = session["session_id"]
        is_selected = self._current_session_id == sid

        def _rename_session(e):
            name_field = ft.TextField(
                value=session.get("titulo", "Conversación"),
                autofocus=True,
                border_radius=8,
            )
            def _do_rename(e):
                new_name = name_field.value.strip()
                if new_name:
                    session["titulo"] = new_name
                    self._sessions_column.controls = [self._build_session_item(s) for s in self._sessions]
                    import threading
                    threading.Thread(
                        target=lambda: self._db.renombrar_sesion_chatbot(sid, new_name) if hasattr(self._db, 'renombrar_sesion_chatbot') else None,
                        daemon=True
                    ).start()
                self.page.close(rename_dlg)
                try: self.page.update()
                except: pass

            rename_dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Renombrar conversación", size=16, weight="bold"),
                content=name_field,
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: self.page.close(rename_dlg)),
                    ft.ElevatedButton("Guardar", bgcolor="#4F46E5", color="white", on_click=_do_rename),
                ],
            )
            self.page.open(rename_dlg)

        def _archive_session(e):
            session["archived"] = True
            self._sessions = [s for s in self._sessions if s.get("session_id") != sid or not s.get("archived")]
            self._sessions_column.controls = [self._build_session_item(s) for s in self._sessions]
            try: self.page.update()
            except: pass

        def _delete_session_ctx(e):
            self._delete_session(sid)

        def _show_floating_menu(e):
            x = e.global_x
            y = e.global_y

            menu_items = ft.Container(
                width=160,
                bgcolor="#1B2A4A",
                border=ft.border.all(1, "#2D3F6A"),
                border_radius=10,
                padding=ft.padding.symmetric(vertical=4),
                shadow=ft.BoxShadow(
                    blur_radius=12,
                    spread_radius=1,
                    color=ft.Colors.with_opacity(0.4, ft.Colors.BLACK),
                ),
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.EDIT_OUTLINED, color="#4F46E5", size=16),
                            ft.Text("Renombrar", size=13, color=ft.Colors.WHITE)
                        ], spacing=10),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        ink=True,
                        on_click=lambda _: (_close_menu(), _rename_session(None)),
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ARCHIVE_OUTLINED, color="#64748B", size=16),
                            ft.Text("Archivar", size=13, color=ft.Colors.WHITE)
                        ], spacing=10),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        ink=True,
                        on_click=lambda _: (_close_menu(), _archive_session(None)),
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DELETE_OUTLINE, color="#EF4444", size=16),
                            ft.Text("Borrar", size=13, color="#EF4444")
                        ], spacing=10),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        ink=True,
                        on_click=lambda _: (_close_menu(), _delete_session_ctx(None)),
                    ),
                ], spacing=0, tight=True)
            )

            dismiss_detector = ft.GestureDetector(
                on_tap=lambda _: _close_menu(),
                on_secondary_tap=lambda _: _close_menu(),
                expand=True,
            )

            floating_menu = ft.Stack([
                dismiss_detector,
                ft.Container(
                    content=menu_items,
                    left=x,
                    top=y,
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

        return ft.GestureDetector(
            on_secondary_tap_down=_show_floating_menu,
            on_long_press_start=lambda e, s=session: self._show_session_options_modal(s),
            content=ft.Container(
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                bgcolor="#1A2F4C" if is_selected else ft.Colors.TRANSPARENT,
                border_radius=10,
                on_click=lambda e: self._select_session(sid),
                content=ft.Row([
                    ft.Icon(ft.Icons.CHAT_OUTLINED, size=18, color="#00E676" if is_selected else "#94A3B8"),
                    ft.Text(
                        session.get("titulo", "Conversación"),
                        size=14,
                        color=ft.Colors.WHITE if is_selected else "#CBD5E1",
                        expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS
                    ),
                ], spacing=10),
            )
        )

    def _open_mobile_history(self, e=None):
        """Abre el historial de conversaciones en un BottomSheet para móviles."""
        def _on_select(sid):
            self.page.close(bs)
            self._select_session(sid)

        try:
            db_sessions = self._db.obtener_sesiones_chatbot(self._uid)
            if db_sessions:
                self._sessions = db_sessions
                from services.navigation_service import NavigationController
                NavigationController.cache["chatbot_sessions"] = self._sessions
        except Exception as ex:
            print(f"[ChatBot] Error fetching sessions for history: {ex}")

        session_controls = []
        for s in self._sessions:
            is_active = s["session_id"] == self._current_session_id
            session_controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.CHAT_OUTLINED, color="#00E676" if is_active else "#64748B"),
                    title=ft.Text(s.get("titulo", "Conversación"), weight="bold" if is_active else "normal", size=14),
                    on_click=lambda _, sid=s["session_id"]: _on_select(sid),
                    on_long_press=lambda _, sess=s: (self.page.close(bs), self._show_session_options_modal(sess)),
                )
            )

        bs = ft.BottomSheet(
            content=ft.Container(
                padding=ft.padding.all(16),
                content=ft.Column([
                    ft.Row([
                        ft.Text("Historial de Conversaciones", size=16, weight="bold"),
                        ft.IconButton(icon=ft.Icons.ADD_COMMENT_OUTLINED, icon_color="#00E676", tooltip="Nuevo Chat", on_click=lambda _: (self.page.close(bs), self._new_chat())),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    ft.Container(
                        height=320,
                        content=ft.Column(session_controls, scroll=ft.ScrollMode.AUTO)
                    ) if session_controls else ft.Text("No hay conversaciones anteriores", color="#64748B", italic=True),
                ], spacing=10, tight=True)
            )
        )

        self.page.open(bs)

    def _show_session_options_modal(self, session: dict):
        """Muestra menú modal de opciones al mantener presionado una sesión."""
        sid = session["session_id"]

        def _rename(e):
            self.page.close(bs)
            name_field = ft.TextField(
                value=session.get("titulo", "Conversación"),
                autofocus=True,
                border_radius=8,
            )
            def _do_rename(e):
                new_name = name_field.value.strip()
                if new_name:
                    session["titulo"] = new_name
                    self._sessions_column.controls = [self._build_session_item(s) for s in self._sessions]
                    import threading
                    threading.Thread(
                        target=lambda: self._db.renombrar_sesion_chatbot(sid, new_name) if hasattr(self._db, 'renombrar_sesion_chatbot') else None,
                        daemon=True
                    ).start()
                self.page.close(rename_dlg)
                try: self.page.update()
                except: pass

            rename_dlg = ft.AlertDialog(
                modal=True,
                title=ft.Text("Renombrar conversación", size=16, weight="bold"),
                content=name_field,
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: self.page.close(rename_dlg)),
                    ft.ElevatedButton("Guardar", bgcolor="#4F46E5", color="white", on_click=_do_rename),
                ],
            )
            self.page.open(rename_dlg)

        def _archive(e):
            self.page.close(bs)
            session["archived"] = True
            self._sessions = [s for s in self._sessions if s.get("session_id") != sid or not s.get("archived")]
            self._sessions_column.controls = [self._build_session_item(s) for s in self._sessions]
            try: self.page.update()
            except: pass

        def _delete(e):
            self.page.close(bs)
            self._delete_session(sid)

        bs = ft.BottomSheet(
            content=ft.Container(
                padding=ft.padding.all(16),
                content=ft.Column([
                    ft.Text(session.get("titulo", "Opciones de Sesión"), size=16, weight="bold"),
                    ft.Divider(),
                    ft.ListTile(leading=ft.Icon(ft.Icons.EDIT_OUTLINED, color="#3B82F6"), title=ft.Text("Renombrar"), on_click=_rename),
                    ft.ListTile(leading=ft.Icon(ft.Icons.ARCHIVE_OUTLINED, color="#EAB308"), title=ft.Text("Archivar"), on_click=_archive),
                    ft.ListTile(leading=ft.Icon(ft.Icons.DELETE_OUTLINE, color="#EF4444"), title=ft.Text("Eliminar conversación"), on_click=_delete),
                ], spacing=4, tight=True)
            )
        )
        self.page.open(bs)

    def _show_msg_options_modal(self, msg_text: str, msg_row: ft.Row):
        """Muestra opciones para un mensaje individual al mantener presionado."""
        def _copy(e):
            self.page.close(bs)
            self.page.set_clipboard(msg_text)
            self._show_info("Texto copiado al portapapeles")

        def _delete(e):
            self.page.close(bs)
            if msg_row in self._chat_list.controls:
                self._chat_list.controls.remove(msg_row)
                try: self.page.update()
                except: pass

        bs = ft.BottomSheet(
            content=ft.Container(
                padding=ft.padding.all(16),
                content=ft.Column([
                    ft.Text("Opciones del mensaje", size=16, weight="bold"),
                    ft.Divider(),
                    ft.ListTile(leading=ft.Icon(ft.Icons.COPY, color="#3B82F6"), title=ft.Text("Copiar texto"), on_click=_copy),
                    ft.ListTile(leading=ft.Icon(ft.Icons.DELETE_OUTLINE, color="#EF4444"), title=ft.Text("Eliminar mensaje"), on_click=_delete),
                ], spacing=4, tight=True)
            )
        )
        self.page.open(bs)

    def _build_message_bubble(self, text: str | None = None, is_user: bool = False, media_path: str | None = None, media_type: str | None = None) -> ft.Row:
        colors = self._get_theme_colors()
        is_mob = self.is_mobile()
        max_w = 295 if is_mob else 520

        if is_user:
            bubble = ft.Container(
                content=ft.Text(
                    (text or "").strip(),
                    color="#0F172A",
                    size=14,
                    selectable=True,
                ),
                padding=ft.padding.symmetric(horizontal=14 if is_mob else 16, vertical=10 if is_mob else 12),
                bgcolor="#E2E8F0",
                border_radius=16,
                width=max_w,
            )
            row = ft.Row([bubble], alignment=ft.MainAxisAlignment.END)
            gesture = ft.GestureDetector(
                on_long_press_start=lambda e, t=text, r=row: self._show_msg_options_modal(t or "", r),
                content=bubble
            )
            row.controls = [gesture]
            return row
        else:
            bubble_content = ft.Column([
                ft.Markdown(
                    text or "",
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    code_theme="atom-one-dark",
                ),
                ft.Container(height=4),
                ft.Row([
                    ft.IconButton(icon=ft.Icons.THUMB_UP_OUTLINE, icon_size=16, icon_color="#64748B"),
                    ft.IconButton(icon=ft.Icons.THUMB_DOWN_OUTLINE, icon_size=16, icon_color="#64748B"),
                ], spacing=2, alignment=ft.MainAxisAlignment.END)
            ], spacing=4)

            bubble = ft.Container(
                content=bubble_content,
                padding=ft.padding.symmetric(horizontal=14 if is_mob else 16, vertical=10 if is_mob else 12),
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, "#E2E8F0"),
                border_radius=16,
                width=max_w,
                theme_mode=ft.ThemeMode.LIGHT,
            )
            row = ft.Row([bubble], alignment=ft.MainAxisAlignment.START)
            gesture = ft.GestureDetector(
                on_long_press_start=lambda e, t=text, r=row: self._show_msg_options_modal(t or "", r),
                content=bubble
            )
            row.controls = [gesture]
            return row

    def _handle_quick_action(self, action_title: str):
        prompts = {
            "Haz una pregunta": "¿Cuáles son las mejores técnicas de estudio para exámenes de matemáticas?",
            "Resumir Apuntes": "Por favor, extrae las ideas principales y hazme un resumen estructurado del siguiente texto:",
            "Resolver Tareas": "Necesito ayuda paso a paso para organizar mis tareas y prioridades.",
            "Genera ideas": "Dame ideas para un proyecto académico de ciencias o tecnología.",
            "Generar Imagen IA": "PointBit, dibuja una imagen educativa y detallada sobre el proceso de la fotosíntesis en las plantas.",
        }
        self._input_field.value = prompts.get(action_title, "")
        self._input_field.focus()
        try: self.page.update()
        except: pass

    def _build_quick_cards(self) -> ft.Column:
        """Construye las tarjetas de acciones rápidas para el estado inicial vacío."""
        is_mob = self.is_mobile()

        def build_card(title, subtitle, icon, is_green):
            bg = "#E8F5E9" if is_green else "#F1F5F9"
            txt_col = "#2E7D32" if is_green else "#1E293B"
            icon_col = "#2E7D32" if is_green else "#4B5563"

            if is_mob:
                return ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(icon, color=icon_col, size=22),
                            width=36,
                            height=36,
                            border_radius=18,
                            bgcolor="#C8E6C9" if is_green else "#E2E8F0",
                            alignment=ft.alignment.center,
                        ),
                        ft.Container(width=10),
                        ft.Column([
                            ft.Text(title, color=txt_col, size=13, weight=ft.FontWeight.BOLD),
                            ft.Text(subtitle, color="#6B7280", size=10, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ], spacing=1, expand=True, alignment=ft.MainAxisAlignment.CENTER)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=bg,
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    on_click=lambda e: self._handle_quick_action(title)
                )

            return ft.Container(
                content=ft.Column([
                    ft.Icon(icon, color=icon_col, size=28),
                    ft.Text(title, color=txt_col, size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(subtitle, color="#6B7280", size=11, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ], spacing=4),
                bgcolor=bg,
                border_radius=16,
                padding=16,
                expand=True,
                height=130,
                on_click=lambda e: self._handle_quick_action(title)
            )

        if is_mob:
            return ft.Column([
                ft.Text("PointBit AI", size=22, weight=ft.FontWeight.BOLD, color="#0F172A", text_align=ft.TextAlign.CENTER),
                ft.Text(self.translate("chat_subtitle"), size=12, color="#4B5563", text_align=ft.TextAlign.CENTER),
                ft.Container(height=8),
                build_card(self.translate("chat_qa_title"), self.translate("chat_qa_sub"), ft.Icons.CHAT_BUBBLE_OUTLINE, True),
                build_card(self.translate("chat_homework_title"), self.translate("chat_homework_sub"), ft.Icons.SCHOOL_OUTLINED, True),
                build_card(self.translate("chat_ideas_title"), self.translate("chat_ideas_sub"), ft.Icons.LIGHTBULB_OUTLINE, False),
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        card_row_1 = ft.Row([
            build_card(self.translate("chat_qa_title"), self.translate("chat_qa_sub"), ft.Icons.CHAT_BUBBLE_OUTLINE, True),
            build_card(self.translate("chat_doc_title"), self.translate("chat_doc_sub"), ft.Icons.CLIPBOARD_OUTLINED, False),
        ], spacing=16)

        card_row_2 = ft.Row([
            build_card(self.translate("chat_homework_title"), self.translate("chat_homework_sub"), ft.Icons.SCHOOL_OUTLINED, True),
            build_card(self.translate("chat_ideas_title"), self.translate("chat_ideas_sub"), ft.Icons.LIGHTBULB_OUTLINE, False),
        ], spacing=16)

        return ft.Column([
            ft.Text("PointBit", size=48, weight=ft.FontWeight.BOLD, color="#0F172A", text_align=ft.TextAlign.CENTER),
            ft.Text(self.translate("chat_subtitle"), size=16, color="#4B5563", text_align=ft.TextAlign.CENTER),
            ft.Container(height=30),
            card_row_1,
            ft.Container(height=8),
            card_row_2
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _pick_file(self, e=None):
        """Abre el explorador de archivos nativo permitiendo selección múltiple (Imágenes y Documentos)."""
        try:
            if self._file_picker not in self.page.overlay:
                self.page.overlay.append(self._file_picker)
                self.page.update()
        except: pass

        self._file_picker.pick_files(
            allow_multiple=True,
            file_type=ft.FilePickerFileType.ANY,
            dialog_title="Selecciona tus archivos (PDF, Word, Texto e Imágenes)"
        )

    def _remove_single_file(self, index: int):
        """Elimina un archivo específico de la lista de adjuntos por su índice."""
        if 0 <= index < len(self._attached_files):
            self._attached_files.pop(index)
            self._render_file_badges()

    def _clear_attached_files(self, e=None):
        """Limpia todos los archivos adjuntos seleccionados."""
        self._attached_files.clear()
        self._render_file_badges()

    def _render_file_badges(self):
        """Renderiza una lista de chips responsivos para cada archivo adjunto."""
        if not self._attached_files:
            self._file_badge.content = None
            try: self.page.update()
            except: pass
            return

        chips = []
        for idx, item in enumerate(self._attached_files):
            f_name = item["name"]
            ext = item["ext"]
            f_type = item["type"]

            if f_type == "imagen":
                icon = ft.Icons.IMAGE
                badge_bg = "#DCFCE7"
                badge_border = "#86EFAC"
                icon_col = "#15803D"
                label = f"📷 {f_name}"
            else:
                icon = ft.Icons.PICTURE_AS_PDF if ext == ".pdf" else (ft.Icons.DESCRIPTION if ext == ".docx" else ft.Icons.ARTICLE)
                badge_bg = "#E0F2FE"
                badge_border = "#7DD3FC"
                icon_col = "#0369A1"
                label = f"📄 {f_name}"

            chip = ft.Container(
                content=ft.Row([
                    ft.Icon(icon, size=15, color=icon_col),
                    ft.Text(label, size=12, weight=ft.FontWeight.BOLD, color=icon_col, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.IconButton(
                        icon=ft.Icons.CANCEL_ROUNDED,
                        icon_size=15,
                        icon_color=icon_col,
                        on_click=lambda _, i=idx: self._remove_single_file(i),
                        tooltip="Quitar este archivo"
                    )
                ], spacing=4, tight=True),
                bgcolor=badge_bg,
                border=ft.border.all(1, badge_border),
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
            )
            chips.append(chip)

        if len(chips) > 1:
            clear_all_btn = ft.TextButton(
                "Limpiar todo",
                icon=ft.Icons.DELETE_SWEEP,
                icon_color="#EF4444",
                style=ft.ButtonStyle(color="#EF4444"),
                on_click=lambda _: self._clear_attached_files()
            )
            chips.append(clear_all_btn)

        self._file_badge.content = ft.Container(
            content=ft.Row(chips, scroll=ft.ScrollMode.AUTO, spacing=8),
            margin=ft.margin.only(bottom=6),
        )

        try:
            self.page.update()
        except:
            try: self._file_badge.update()
            except: pass

    def _open_google_drive_modal(self, e=None):
        """Muestra modal para importar documentos desde Google Drive y Google Classroom para análisis con IA."""
        try:
            from services.google_service import google_service
            drive_files = google_service.import_from_google_drive()
            class_tasks = google_service.import_from_google_classroom()

            def _import_item(name, source):
                self._attached_files.append({
                    "path": f"cloud://{source}/{name}",
                    "name": f"[{source}] {name}",
                    "type": "documento",
                    "ext": ".pdf"
                })
                self.page.close(dlg)
                self._render_file_badges()
                self._show_info(f"📂 Archivo '{name}' importado desde {source} para PointBit IA.")

            drive_controls = []
            for f in drive_files:
                drive_controls.append(
                    ft.ListTile(
                        leading=ft.Text(f.get("icon", "📄"), size=20),
                        title=ft.Text(f.get("name", "Documento"), size=13, weight="bold"),
                        subtitle=ft.Text(f"Google Drive • {f.get('size')}", size=11, color="#64748B"),
                        on_click=lambda _, n=f.get("name"), s="Google Drive": _import_item(n, s)
                    )
                )

            class_controls = []
            for c in class_tasks:
                class_controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.SCHOOL, color="#0284C7", size=20),
                        title=ft.Text(c.get("assignment", "Tarea"), size=13, weight="bold"),
                        subtitle=ft.Text(f"{c.get('course')} • Entrega: {c.get('due_date')}", size=11, color="#64748B"),
                        on_click=lambda _, n=f"{c.get('course')} - {c.get('assignment')}", s="Google Classroom": _import_item(n, s)
                    )
                )

            dlg = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.CLOUD_DOWNLOAD_OUTLINED, color="#0284C7", size=24),
                    ft.Text("Importar desde Google", size=16, weight="bold")
                ]),
                content=ft.Container(
                    width=420,
                    height=360,
                    content=ft.Column([
                        ft.Text("Documentos en tu Google Drive:", size=13, weight="bold", color="#0F172A"),
                        ft.Column(drive_controls, spacing=2),
                        ft.Divider(),
                        ft.Text("Tareas de Google Classroom:", size=13, weight="bold", color="#0F172A"),
                        ft.Column(class_controls, spacing=2),
                    ], scroll=get_scroll_mode("AUTO"), spacing=6)
                ),
                actions=[
                    ft.TextButton("Cerrar", on_click=lambda _: self.page.close(dlg))
                ]
            )
            self.page.open(dlg)
        except Exception as ex:
            self._show_info(f"⚠️ Error al abrir Google Drive: {str(ex)}")

    def _on_file_result(self, e: ft.FilePickerResultEvent):
        """Maneja la selección múltiple de cualquier tipo de archivo."""
        if not e.files or len(e.files) == 0:
            return

        for picked_file in e.files:
            f_path = getattr(picked_file, "path", None) or getattr(picked_file, "name", None)
            if not f_path: continue

            f_name = os.path.basename(f_path)
            ext = os.path.splitext(f_name)[1].lower()

            f_type = "imagen" if ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"] else "documento"

            file_info = {
                "path": f_path,
                "name": f_name,
                "type": f_type,
                "ext": ext,
            }
            if not any(f["path"] == f_path for f in self._attached_files):
                self._attached_files.append(file_info)

        self._render_file_badges()

    def _send_message(self, e):
        from services.chatbot_service import chatbot
        from services.navigation_service import NavigationController
        
        query = self._input_field.value.strip()
        current_attached = list(self._attached_files)
        if not query and not current_attached: return
        if self._is_typing: return
        
        if not self._current_session_id:
            self._new_chat(silent=True)
        
        # Limpiar tarjetas de bienvenida si están presentes
        if self._chat_list.controls and len(self._chat_list.controls) == 1 and isinstance(self._chat_list.controls[0], ft.Container) and not getattr(self._chat_list.controls[0], "bgcolor", None) == "#E2E8F0":
            self._chat_list.controls.clear()

        display_query = query
        if current_attached:
            file_names = [f["name"] for f in current_attached]
            if len(file_names) == 1:
                prefix = "📷 [Imagen" if current_attached[0].get("type") == "imagen" else "📄 [Documento"
                file_label = f"{prefix}: {file_names[0]}]"
            else:
                file_label = f"📎 [{len(file_names)} Archivos adjuntos: {', '.join(file_names)}]"

            display_query = f"{file_label}\n{query}" if query else file_label
            self._clear_attached_files()

        img_paths = [f["path"] for f in current_attached if f.get("type") == "imagen"]
        primary_img = img_paths[0] if img_paths else None

        self._chat_list.controls.append(self._build_message_bubble(display_query, is_user=True, media_path=primary_img))
        self._input_field.value = ""
        self._is_typing = True
        
        typing_indicator = ft.Row([ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, "#E2E8F0"),
            border_radius=16,
            content=ft.Text(self.translate("chat_typing"), italic=True, size=12, color=ft.Colors.GREY_500)
        )])
        self._chat_list.controls.append(typing_indicator)
        self.page.update()
        
        history = NavigationController.cache.get("chatbot_histories", {}).get(self._current_session_id, [])
        is_first_message = len(history) == 0
        sid = self._current_session_id
        
        def _process():
            try:
                response = chatbot.send_message(query, self._uid, sid, history=history, attached_files=current_attached)
                self._db.guardar_interaccion_chatbot(self._uid, sid, display_query, response)
                
                new_interaction = {"pregunta": display_query, "respuesta": response}
                if sid not in NavigationController.cache["chatbot_histories"]:
                    NavigationController.cache["chatbot_histories"][sid] = []
                NavigationController.cache["chatbot_histories"][sid].append(new_interaction)
                
                if typing_indicator in self._chat_list.controls:
                    self._chat_list.controls.remove(typing_indicator)
                self._chat_list.controls.append(self._build_message_bubble(response, is_user=False))
                
                if is_first_message:
                    title_src = query or (current_attached[0]['name'] if current_attached else "Conversación")
                    new_title = (title_src[:30] + '...') if len(title_src) > 30 else title_src
                    for s in self._sessions:
                        if s["session_id"] == sid:
                            s["titulo"] = new_title
                            break
                    self._sessions_column.controls = [self._build_session_item(s) for s in self._sessions]
                
            except Exception as ex:
                if typing_indicator in self._chat_list.controls:
                    self._chat_list.controls.remove(typing_indicator)
                self._chat_list.controls.append(self._build_message_bubble(f"Error: {str(ex)}", is_user=False))
            
            self._is_typing = False
            try:
                self.page.update()
                self._chat_list.scroll_to(offset=-1, duration=50)
            except: pass
        
        threading.Thread(target=_process, daemon=True).start()

    def build(self) -> ft.Control:
        from services.navigation_service import NavigationController
        colors = self._get_theme_colors()
        navbar = self._build_navbar(self.translate("nav_chatbot"))
        self._input_field.hint_text = self.translate("chat_input_hint")
        
        # 1. SIDEBAR IZQUIERDO (Azul Oscuro - #0B192C)
        new_chat_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color="#00E676", size=24),
                ft.Text(self.translate("chat_new_chat"), color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            border=ft.border.all(1, "#1A2F4C"),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            on_click=self._new_chat,
        )

        chat_actual_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, color="#00E676", size=20),
                ft.Text(self.translate("chat_current_chat"), color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            bgcolor="#1E2D4A",
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )

        # Perfil y opciones en la base del sidebar
        user_name = self._user.get("nombre_usuario", self._user.get("name", "Juan"))
        user_avatar_letter = (user_name)[:1].upper()
        
        user_profile_box = ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    radius=20,
                    bgcolor="#7C3AED",
                    content=ft.Text(user_avatar_letter, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                ),
                ft.Container(width=4),
                ft.Column([
                    ft.Text(user_name, color=ft.Colors.WHITE, size=15, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Icon(ft.Icons.STAR, color="#00E676", size=12),
                        ft.Text("Plan Premium", color="#00E676", size=11, weight=ft.FontWeight.BOLD),
                    ], spacing=4)
                ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
            ]),
            padding=ft.padding.symmetric(vertical=10),
        )

        config_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SETTINGS_OUTLINED, color="#94A3B8", size=20),
                ft.Text("Configuración", color="#E2E8F0", size=14),
            ], spacing=10),
            on_click=lambda e: NavigationController.update_view("Perfil"),
            padding=ft.padding.symmetric(vertical=8),
        )
        
        salir_btn = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LOGOUT_ROUNDED, color="#94A3B8", size=20),
                ft.Text("Salir", color="#E2E8F0", size=14),
            ], spacing=10),
            on_click=lambda e: NavigationController.logout(),
            padding=ft.padding.symmetric(vertical=8),
        )

        sidebar_panel = ft.Container(
            width=280,
            bgcolor="#0B192C",
            padding=ft.padding.all(20),
            content=ft.Column([
                ft.Row([
                    ft.Text("Point", color=ft.Colors.WHITE, size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Bit", color="#00E676", size=24, weight=ft.FontWeight.BOLD),
                ], spacing=4),
                ft.Container(height=24),
                new_chat_btn,
                ft.Container(height=12),
                chat_actual_btn,
                ft.Container(height=24),
                ft.Text("Historial", size=12, color="#64748B", weight=ft.FontWeight.W_600),
                ft.Container(height=8),
                ft.Container(content=self._sessions_column, expand=True),
                ft.Divider(color="#1A2F4C"),
                user_profile_box,
                config_btn,
                salir_btn
            ], spacing=0)
        )

        is_mob = self.is_mobile()
        top_banner = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.SMART_TOY, color="#00E676", size=20 if is_mob else 24),
                    ft.Text("PointBit AI", size=14 if is_mob else 16, weight="bold", color="#0F172A"),
                ], spacing=6),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.HISTORY,
                        icon_color="#3B82F6",
                        tooltip="Historial de conversaciones",
                        on_click=self._open_mobile_history,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD_COMMENT_OUTLINED,
                        icon_color="#00E676",
                        tooltip="Nuevo Chat",
                        on_click=lambda e: self._new_chat(),
                    ),
                ], spacing=2)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=12 if is_mob else 24, vertical=6 if is_mob else 12),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, "#E2E8F0")),
        )

        # Caja de entrada blanca con borde verde
        input_container = ft.Container(
            border=ft.border.all(1, "#00E676"),
            border_radius=16,
            bgcolor=ft.Colors.WHITE,
            padding=ft.padding.only(left=12, right=12, top=6, bottom=6),
            content=ft.Column([
                self._file_badge,
                self._input_field,
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ATTACH_FILE,
                        icon_color="#10B981",
                        icon_size=22,
                        tooltip="Adjuntar cualquier archivo (PDF, Word, Texto, Imagen, Código)",
                        on_click=self._pick_file,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLOUD_DOWNLOAD_OUTLINED,
                        icon_color="#0284C7",
                        icon_size=22,
                        tooltip="Importar desde Google Drive / Google Classroom",
                        on_click=self._open_google_drive_modal,
                    ),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Icon(ft.Icons.SEND_ROUNDED, color=ft.Colors.WHITE, size=16),
                        bgcolor="#00E676",
                        border_radius=8,
                        width=36,
                        height=36,
                        alignment=ft.alignment.center,
                        on_click=self._send_message,
                        tooltip="Enviar mensaje",
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            ], spacing=4)
        )

        has_history = len(self._chat_list.controls) > 0

        chat_content = ft.Container(
            content=self._chat_list,
            expand=True,
            bgcolor="#F5F7F8",
        )

        chat_panel = ft.Container(
            expand=True,
            bgcolor="#F5F7F8",
            content=ft.Column([
                top_banner,
                chat_content,
                ft.Container(
                    padding=ft.padding.all(20),
                    content=input_container
                )
            ], spacing=0)
        )

        show_help_panel = not has_history
        def build_help_item(title, desc, icon):
            return ft.Row([
                ft.Container(
                    content=ft.Icon(icon, color="#2E7D32", size=20),
                    bgcolor="#C8E6C9",
                    width=36,
                    height=36,
                    border_radius=18,
                    alignment=ft.alignment.center
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(title, size=14, color="#1B5E20", weight=ft.FontWeight.BOLD),
                    ft.Text(desc, size=12, color="#2E7D32", width=180),
                ], spacing=2, expand=True)
            ], vertical_alignment=ft.CrossAxisAlignment.START)

        help_items = ft.Column([
            build_help_item("Responder preguntas", "Obtén respuestas claras y útiles.", ft.Icons.HELP_OUTLINE),
            ft.Container(height=16),
            build_help_item("Ayudar con tareas", "Te ayuda a redactar, resumir, analizar y más.", ft.Icons.ASSIGNMENT_OUTLINED),
            ft.Container(height=16),
            build_help_item("Generar ideas", "Lluvia de ideas, planes, estrategias y soluciones.", ft.Icons.LIGHTBULB_OUTLINE),
            ft.Container(height=16),
            build_help_item("Explicar conceptos", "Te explico temas complejos de forma sencilla.", ft.Icons.SCHOOL_OUTLINED),
        ], spacing=0)

        privacy_card = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SHIELD_OUTLINED, color="#2E7D32", size=20),
                ft.Container(width=8),
                ft.Text("Tu privacidad también es importante\nTus conversaciones están protegidas con encriptación de extremo a extremo.", size=11, color="#2E7D32", expand=True)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#C8E6C9",
            border_radius=12,
            padding=12,
            border=ft.border.all(1, "#A5D6A7")
        )

        help_panel = ft.Container(
            width=280,
            bgcolor="#E8F5E9",
            padding=ft.padding.all(24),
            content=ft.Column([
                ft.Container(height=20),
                ft.Row([
                    ft.Text("Point", color="#0F172A", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text("Bit", color="#2E7D32", size=28, weight=ft.FontWeight.BOLD),
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
                ft.Text("Tu asistente inteligente de confianza.", size=12, color="#4B5563", text_align=ft.TextAlign.CENTER),
                ft.Container(height=15),
                ft.Divider(color="#C8E6C9"),
                ft.Container(height=15),
                ft.Text("¿Qué puedo hacer por ti?", size=16, color="#1B5E20", weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                help_items,
                ft.Container(expand=True),
                privacy_card
            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # Adaptabilidad Responsiva
        is_mob = self.is_mobile()
        is_desktop = (self.page.width or 1200) >= 1024
        is_tablet = 768 <= (self.page.width or 1200) < 1024

        if is_desktop:
            right_panels = [help_panel] if show_help_panel else []
            layout = ft.Row([sidebar_panel, chat_panel] + right_panels, expand=True, spacing=0)
        elif is_tablet:
            layout = ft.Row([sidebar_panel, chat_panel], expand=True, spacing=0)
        else:
            layout = ft.Row([chat_panel], expand=True, spacing=0)

        controls = [navbar, layout]
        if is_mob:
            controls.append(self._build_bottom_nav("ChatBot"))

        return ft.Column(controls, expand=True, spacing=0)
