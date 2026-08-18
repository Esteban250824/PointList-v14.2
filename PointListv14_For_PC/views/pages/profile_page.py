"""
pages/profile_page.py - v14.1 Perfil de Usuario Innovador
Diseño tipo Dashboard con pestañas de píldora horizontales súper fluidas,
cambio instantáneo de secciones y sin tarjetas duplicadas.
"""

import flet as ft
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode


class UserProfilePage(BasePage):
    """Página de perfil innovadora v14.1 con pestañas dinámicas instantáneas."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        from services.database_service import db
        from services.navigation_service import NavigationController
        self._db = db
        self._user = NavigationController.get_current_user()
        self._uid = self._user.get("id")
        self._config: dict = {}

        self.file_picker = ft.FilePicker(on_result=self._on_file_result)
        self.page.overlay.append(self.file_picker)
        self.avatar_ref = ft.Ref[ft.CircleAvatar]()
        self.active_tab = NavigationController.cache.get("profile_active_tab", "perfil")

        # Contenedores dinámicos para actualización ultra rápida
        self.tabs_row_container = ft.Container()
        self.main_card_container = ft.Container()

        self._create_text_fields()

    def _create_text_fields(self):
        """Crea campos de texto estilizados y adaptables al tema."""
        colors = self._get_theme_colors()

        field_props = dict(
            border_radius=12,
            bgcolor=colors["surface"],
            color=colors["text"],
            border_color=colors["border"],
            border_width=1,
            focused_border_color="#16A34A",
            focused_border_width=1.5,
            height=46,
            content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
        )

        self.name_field = ft.TextField(prefix=ft.Icon(ft.Icons.PERSON_OUTLINE, color="#16A34A"), **field_props)
        self.phone_field = ft.TextField(prefix=ft.Icon(ft.Icons.PHONE_OUTLINED, color="#16A34A"), **field_props)
        self.bio_field = ft.TextField(prefix=ft.Icon(ft.Icons.EDIT_OUTLINED, color="#16A34A"), **field_props)
        self.location_field = ft.TextField(**field_props)
        self.website_field = ft.TextField(prefix=ft.Icon(ft.Icons.LANGUAGE, color="#16A34A"), **field_props)

        # Campos para seguridad
        self.curr_pass_field = ft.TextField(password=True, can_reveal_password=True, hint_text="Contraseña actual", **field_props)
        self.new_pass_field = ft.TextField(password=True, can_reveal_password=True, hint_text="Nueva contraseña", **field_props)

    def _on_file_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            result = self._db.actualizar_perfil(self._uid, {"photo_url": file_path})
            if result.get("ok", False):
                self._user["photo_url"] = file_path
                if self.avatar_ref.current:
                    self.avatar_ref.current.foreground_image_src = file_path
                    self.avatar_ref.current.update()
                self.page.client_storage.set("current_user", self._user)
                self._show_success("Foto de perfil actualizada correctamente.")
                self.page.update()
            else:
                self._show_error("Error al guardar la foto.")

    def _pick_file(self, e):
        self.file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["png", "jpg", "jpeg"],
            dialog_title="Selecciona tu foto de perfil",
        )

    def _load_data(self):
        from services.navigation_service import NavigationController
        if NavigationController.cache.get("user_config") and NavigationController.cache["user_config"].get("uid") == self._uid:
            self._config = NavigationController.cache["user_config"]
        elif self._uid:
            self._config = self._db.obtener_configuracion(self._uid) or {}
            self._config["uid"] = self._uid
            NavigationController.cache["user_config"] = self._config

    def _save_profile(self, e):
        nuevos_datos = {
            "nombre_usuario": self.name_field.value.strip(),
            "bio": self.bio_field.value.strip(),
            "telefono": self.phone_field.value.strip(),
            "ubicacion": self.location_field.value.strip(),
            "sitio_web": self.website_field.value.strip(),
        }

        from services.navigation_service import NavigationController
        stored = NavigationController.get_current_user()
        stored["name"] = nuevos_datos["nombre_usuario"]
        NavigationController.cache["current_user"] = stored
        NavigationController.cache["user_config"] = nuevos_datos

        import threading
        def save_task():
            if hasattr(self._db, 'actualizar_perfil'):
                self._db.actualizar_perfil(self._uid, nuevos_datos)
        threading.Thread(target=save_task, daemon=True).start()

        self.page.client_storage.set("current_user", stored)
        self._show_success("Perfil actualizado correctamente.")

    def _change_tab(self, tab_id: str):
        """Cambia de pestaña de forma instantánea actualizando los contenedores."""
        self.active_tab = tab_id
        from services.navigation_service import NavigationController
        NavigationController.cache["profile_active_tab"] = tab_id
        self.tabs_row_container.content = self._build_tabs_row()
        self.main_card_container.content = self._build_active_tab_content()
        try:
            self.page.update()
        except:
            pass

    def _build_tabs_row(self) -> ft.Control:
        colors = self._get_theme_colors()

        def build_pill_tab(tab_id: str, label: str, icon):
            is_selected = self.active_tab == tab_id
            bg = "#16A34A" if is_selected else ft.Colors.TRANSPARENT
            txt_col = ft.Colors.WHITE if is_selected else colors["text_secondary"]
            icon_col = ft.Colors.WHITE if is_selected else colors["text_secondary"]

            return ft.Container(
                content=ft.Row([
                    ft.Icon(icon, size=18, color=icon_col),
                    ft.Text(label, size=14, weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.W_500, color=txt_col),
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=bg,
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=24, vertical=10),
                ink=True,
                on_click=lambda e, tid=tab_id: self._change_tab(tid),
            )

        return ft.Container(
            bgcolor=colors["surface"],
            border_radius=24,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            shadow=ft.BoxShadow(blur_radius=12, spread_radius=-2, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
            content=ft.Row([
                build_pill_tab("perfil", self.translate("profile_tab_perfil"), ft.Icons.PERSON_OUTLINE),
                build_pill_tab("logros", "Logros & Insignias", ft.Icons.EMOJI_EVENTS_OUTLINED),
                build_pill_tab("seguridad", self.translate("profile_tab_seguridad"), ft.Icons.SHIELD_OUTLINED),
                build_pill_tab("ajustes", self.translate("profile_tab_ajustes"), ft.Icons.SETTINGS_OUTLINED),
                build_pill_tab("actividad", self.translate("profile_tab_actividad"), ft.Icons.ACCESS_TIME),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
        )

    def _build_active_tab_content(self) -> ft.Control:
        colors = self._get_theme_colors()

        def _field_block(label: str, field: ft.TextField):
            return ft.Column([
                ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=colors["text"]),
                ft.Container(height=4),
                field,
            ], spacing=0, expand=True)

        if self.active_tab == "perfil":
            return ft.Column([
                ft.Text(self.translate("profile_title"), size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                ft.Container(height=16),
                ft.Row([
                    _field_block(self.translate("profile_full_name"), self.name_field),
                    ft.Container(width=16),
                    _field_block(self.translate("profile_phone"), self.phone_field),
                ]),
                ft.Container(height=14),
                ft.Row([
                    _field_block(self.translate("profile_bio"), self.bio_field),
                    ft.Container(width=16),
                    _field_block(self.translate("profile_website"), self.website_field),
                ]),
                ft.Container(height=24),
                ft.Row([
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        self.translate("profile_save_changes"),
                        bgcolor="#08015C",
                        color=ft.Colors.WHITE,
                        width=210,
                        height=44,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        on_click=self._save_profile,
                    ),
                ]),
            ], spacing=0)

        elif self.active_tab == "logros":
            def build_badge(title, desc, icon, color, bg):
                return ft.Container(
                    padding=16, bgcolor=bg, border_radius=16, border=ft.border.all(1, color), expand=True,
                    content=ft.Row([
                        ft.Icon(icon, color=color, size=28),
                        ft.Column([
                            ft.Text(title, size=14, weight="bold", color=colors["text"]),
                            ft.Text(desc, size=11, color=colors["text_secondary"]),
                        ], spacing=2, expand=True)
                    ], spacing=10)
                )

            return ft.Column([
                ft.Text("🏆 Insignias de Rendimiento Escolar & Racha", size=18, weight="bold", color=colors["text"]),
                ft.Text("Completa tareas y estudia con Pomodoro para desbloquear nuevos reconocimientos:", size=12, color=colors["text_secondary"]),
                ft.Container(height=16),
                ft.Row([
                    build_badge("🚀 Estudiante Veloz", "Navegación y estudio a máxima velocidad en tiempo real.", ft.Icons.SPEED, "#D97706", "#FEF3C7"),
                    build_badge("⏱️ Maestro Pomodoro", "Más de 50 bloques de concentración completados.", ft.Icons.TIMER, "#EA580C", "#FFEDD5"),
                ], spacing=12),
                ft.Container(height=12),
                ft.Row([
                    build_badge("🤖 Explorador IA PointBit", "Más de 20 mapas mentales y flashcards generadas.", ft.Icons.AUTO_AWESOME, "#0284C7", "#E0F2FE"),
                    build_badge("📚 Promedio Sobresaliente", "Promedio académico sostenido superior a 4.5.", ft.Icons.STAR, "#16A34A", "#DCFCE7"),
                ], spacing=12),
            ], spacing=0)

        elif self.active_tab == "seguridad":
            return ft.Column([
                ft.Text(self.translate("profile_security_title"), size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                ft.Text(self.translate("profile_security_subtitle"), size=13, color=colors["text_secondary"]),
                ft.Container(height=20),
                _field_block(self.translate("profile_curr_pass"), self.curr_pass_field),
                ft.Container(height=14),
                _field_block(self.translate("profile_new_pass"), self.new_pass_field),
                ft.Container(height=20),
                ft.Row([
                    ft.ElevatedButton(
                        self.translate("profile_update_pass"),
                        bgcolor="#16A34A",
                        color=ft.Colors.WHITE,
                        height=44,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        on_click=lambda e: self._show_success("Contraseña actualizada exitosamente."),
                    ),
                ]),
            ], spacing=0)

        elif self.active_tab == "ajustes":
            from services.navigation_service import NavigationController

            def _on_lang(code):
                NavigationController.cache["profile_active_tab"] = "ajustes"
                NavigationController.change_language(code)

            def _on_theme(dark: bool):
                NavigationController.cache["profile_active_tab"] = "ajustes"
                NavigationController.change_theme(dark)

            lang_buttons = ft.ResponsiveRow([
                ft.Container(ft.ElevatedButton("🇪🇸 Español", expand=True, on_click=lambda e: _on_lang("es")), col={"xs": 6, "sm": 3}),
                ft.Container(ft.ElevatedButton("🇬🇧 English", expand=True, on_click=lambda e: _on_lang("en")), col={"xs": 6, "sm": 3}),
                ft.Container(ft.ElevatedButton("🇧🇷 Português", expand=True, on_click=lambda e: _on_lang("pt")), col={"xs": 6, "sm": 3}),
                ft.Container(ft.ElevatedButton("🇮🇹 Italiano", expand=True, on_click=lambda e: _on_lang("it")), col={"xs": 6, "sm": 3}),
                ft.Container(ft.ElevatedButton("🇩🇪 Deutsch", expand=True, on_click=lambda e: _on_lang("de")), col={"xs": 6, "sm": 3}),
                ft.Container(ft.ElevatedButton("🇫🇷 Français", expand=True, on_click=lambda e: _on_lang("fr")), col={"xs": 6, "sm": 3}),
                ft.Container(ft.ElevatedButton("🇨🇳 中文 (简体)", expand=True, on_click=lambda e: _on_lang("zh")), col={"xs": 6, "sm": 3}),
                ft.Container(ft.ElevatedButton("🇨🇳 中文 (繁體)", expand=True, on_click=lambda e: _on_lang("zh-TW")), col={"xs": 6, "sm": 3}),
            ], spacing=10, run_spacing=10)

            return ft.Column([
                ft.Text(self.translate("profile_settings_sys"), size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                ft.Container(height=16),
                ft.Text(self.translate("profile_app_theme"), size=14, weight=ft.FontWeight.BOLD, color=colors["text"]),
                ft.Container(height=8),
                ft.Row([
                    ft.ElevatedButton("☀️ Modo Claro", expand=True, on_click=lambda e: _on_theme(False)),
                    ft.ElevatedButton("🌙 Modo Oscuro", expand=True, on_click=lambda e: _on_theme(True)),
                ], spacing=12),
                ft.Container(height=24),
                ft.Text(self.translate("profile_ui_lang"), size=14, weight=ft.FontWeight.BOLD, color=colors["text"]),
                ft.Container(height=10),
                lang_buttons,
            ], spacing=0)

        else: # actividad
            def build_activity_item(icon, color, title, time_ago):
                return ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=18),
                        bgcolor=ft.Colors.with_opacity(0.12, color),
                        width=36,
                        height=36,
                        border_radius=18,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=12),
                    ft.Column([
                        ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=colors["text"]),
                        ft.Text(time_ago, size=12, color=colors["text_secondary"]),
                    ], spacing=2, expand=True)
                ])

            return ft.Column([
                ft.Text(self.translate("profile_activity_title"), size=18, weight=ft.FontWeight.BOLD, color=colors["text"]),
                ft.Container(height=16),
                build_activity_item(ft.Icons.CAMERA_ALT, "#16A34A", "Foto de perfil actualizada", "Hace 2 horas"),
                ft.Divider(height=20, color=colors["divider"]),
                build_activity_item(ft.Icons.LOGIN, "#2563EB", "Inició sesión en PointList v13", "Hace 1 día"),
                ft.Divider(height=20, color=colors["divider"]),
                build_activity_item(ft.Icons.CHECK_CIRCLE, "#7C3AED", "Completó la tarea de Matemáticas", "Hace 2 días"),
            ], spacing=0)

    def build(self) -> ft.Control:
        self._load_data()
        colors = self._get_theme_colors()
        user = self._user
        display_name = user.get("name") or user.get("nombre_usuario") or "Juan Esteban"
        initials = display_name[:1].upper() if display_name else "J"

        self.name_field.value = display_name
        self.bio_field.value = self._config.get("bio", "Estudiante de PointList v13")
        self.phone_field.value = self._config.get("telefono", "+57 300 123 4567")
        self.location_field.value = self._config.get("ubicacion", "Bogotá, Colombia")
        self.website_field.value = self._config.get("sitio_web", "https://pointlist.app")

        navbar = self._build_navbar(self.translate("nav_profile"))
        member_since = f"Miembro desde {self._config.get('fecha_registro', 'marzo de 2026')}"

        # Hero Banner
        hero = ft.Container(
            height=180,
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=["#16A34A", "#2563EB", "#7C3AED"],
            ),
            padding=ft.padding.symmetric(horizontal=36, vertical=20),
            content=ft.Row([
                ft.Stack([
                    ft.CircleAvatar(
                        ref=self.avatar_ref,
                        radius=50,
                        bgcolor=ft.Colors.WHITE,
                        foreground_image_src=user.get("photo_url", ""),
                        content=ft.Text(initials, size=34, color="#0F172A", weight="bold"),
                    ),
                    ft.Container(
                        content=ft.IconButton(
                            icon=ft.Icons.CAMERA_ALT,
                            icon_color=ft.Colors.WHITE,
                            bgcolor="#08015C",
                            on_click=self._pick_file,
                            icon_size=12,
                        ),
                        bottom=2,
                        right=2,
                        width=28,
                        height=28,
                        border_radius=14,
                    ),
                ]),
                ft.Container(width=20),
                ft.Column([
                    ft.Row([
                        ft.Text(display_name, size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Container(
                            content=ft.Text("Estudiante Activo", size=11, color="#15803D", weight="bold"),
                            bgcolor="#DCFCE7",
                            border_radius=12,
                            padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        ),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text(member_since, size=13, color=ft.Colors.WHITE70),
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        )

        # Asignar contenidos a contenedores reactivos
        self.tabs_row_container.content = self._build_tabs_row()
        self.main_card_container.content = self._build_active_tab_content()

        # Tarjeta Contenedora Principal
        main_card = ft.Container(
            bgcolor=colors["surface"],
            border_radius=20,
            padding=30,
            border=ft.border.all(1, "#E2E8F0"),
            shadow=ft.BoxShadow(blur_radius=20, spread_radius=-4, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
            content=self.main_card_container,
        )

        main_layout = ft.Container(
            padding=ft.padding.symmetric(horizontal=36),
            content=ft.Column([
                ft.Container(height=-24),
                self.tabs_row_container,
                ft.Container(height=20),
                main_card,
                ft.Container(height=36),
            ], spacing=0)
        )

        return ft.Column(
            controls=[
                navbar,
                hero,
                ft.Container(
                    expand=True,
                    bgcolor=colors["background"],
                    content=ft.Column([
                        main_layout,
                    ], scroll=get_scroll_mode("AUTO"), expand=True),
                ),
            ],
            expand=True,
            spacing=0,
        )
