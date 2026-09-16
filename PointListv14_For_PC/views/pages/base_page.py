"""
pages/base_page.py
PointList v0.14.25experiment
Clase base para todas las páginas de la aplicación con diseño premium v0.13.
"""

import os
import flet as ft
from utils.flet_compat import run_async_safe
from utils.i18n import I18n, t


class BasePage:
    """
    Clase base que todas las páginas deben heredar.
    Provee acceso a la página de Flet y un método build() abstracto.
    """

    def __init__(self, page: ft.Page = None):
        self.page = page
        self.primary_color = "#4F46E5"  # Indigo premium
        self.accent_color = "#10B981"   # Emerald
        # Idioma del usuario (caché global > almacenamiento local)
        from services.navigation_service import NavigationController
        self.language = (
            NavigationController.cache.get("language")
            or (page.client_storage.get("language") if page else None)
            or "es"
        )
        if self.language not in I18n.LANGUAGES:
            self.language = "es"
        NavigationController.cache["language"] = self.language

    def build(self) -> ft.Control:
        """Construye y devuelve el control principal de la página."""
        raise NotImplementedError("Cada página debe implementar el método build().")

    def is_mobile(self) -> bool:
        """Devuelve True si la ventana de la app tiene un ancho de pantalla móvil (< 768px)."""
        if not self.page or not self.page.width:
            return False
        return self.page.width < 768

    def _get_theme_colors(self):
        """Devuelve los colores adecuados según el modo de tema actual.
        Optimizado para modo oscuro: sin colores blancos residuales.
        """
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        return {
            "primary": self.primary_color if not is_dark else "#818CF8",
            "background": "#F9FAFB" if not is_dark else "#0F172A",
            "surface": "#FFFFFF" if not is_dark else "#1E293B",
            "card_bg": "#FFFFFF" if not is_dark else "#1E293B",
            "text": "#111827" if not is_dark else "#F1F5F9",
            "text_secondary": "#4B5563" if not is_dark else "#CBD5E1",
            "text_muted": "#64748B" if not is_dark else "#94A3B8",
            "divider": "#E5E7EB" if not is_dark else "#334155",
            "border": "#E2E8F0" if not is_dark else "#334155",
            "navbar": "#FFFFFF" if not is_dark else "#1E293B",
            "stat_num": "#0F172A" if not is_dark else "#F8FAFC",
        }

    def set_language(self, lang: str):
        """Cambia el idioma de la aplicación."""
        if I18n.set_language(lang):
            self.language = lang
            from services.navigation_service import NavigationController
            NavigationController.cache["language"] = lang
            if self.page:
                self.page.client_storage.set("language", lang)
            return True
        return False
    
    def translate(self, key: str) -> str:
        """Traduce una clave usando el idioma actual."""
        return t(key, self.language)

    def translate_literal(self, text: str) -> str:
        """Traduce textos heredados que todavía no fueron migrados a claves i18n."""
        return I18n.get_literal(text, self.language)

    def localize_control_tree(self, control: ft.Control | None) -> ft.Control | None:
        """Aplica traducciones literales a un árbol de controles Flet ya construido."""
        visited: set[int] = set()

        def _localize(value):
            if value is None:
                return
            value_id = id(value)
            if value_id in visited:
                return
            visited.add(value_id)

            for attr in ("value", "text", "label", "hint_text", "tooltip"):
                try:
                    attr_value = getattr(value, attr, None)
                    if isinstance(attr_value, str):
                        translated = self.translate_literal(attr_value)
                        if translated != attr_value:
                            setattr(value, attr, translated)
                except Exception:
                    pass

            for attr in (
                "content",
                "leading",
                "trailing",
                "title",
                "subtitle",
                "selected_icon",
            ):
                try:
                    child = getattr(value, attr, None)
                    if isinstance(child, str):
                        translated = self.translate_literal(child)
                        if translated != child:
                            setattr(value, attr, translated)
                    elif child is not None:
                        _localize(child)
                except Exception:
                    pass

            for attr in ("controls", "actions", "options", "tabs", "items"):
                try:
                    children = getattr(value, attr, None)
                    if children:
                        for child in list(children):
                            _localize(child)
                except Exception:
                    pass

        _localize(control)
        return control

    def _build_navbar(self, title: str, show_user: bool = True) -> ft.Container:
        """
        Construye la barra de navegación superior responsiva premium v0.13.
        """
        from services.navigation_service import NavigationController
        colors = self._get_theme_colors()
        # Umbral para ocultar botones centrales (móvil/tablet)
        # Aumentamos el umbral a 950px para asegurar que se oculten antes de amontonarse
        is_mobile = self.page.width < 800

        # Obtener usuario de forma segura (evita Timeout en hilos secundarios)
        current_user = NavigationController.get_current_user()

        # Los botones centrales han sido eliminados para un diseño más limpio y minimalista.
        nav_buttons = ft.Container()

        right_controls = []
        if show_user:
            # En móvil solo mostramos el avatar, en escritorio nombre + avatar
            if not is_mobile:
                right_controls.append(ft.Text(current_user.get("nombre_usuario", current_user.get("name", "")), color=colors["text_secondary"], size=14))
                right_controls.append(ft.Container(width=8))
            
            photo_url = current_user.get("photo_url", "")
            right_controls.append(
                ft.GestureDetector(
                    content=ft.CircleAvatar(
                        foreground_image_src=photo_url if photo_url else None,
                        radius=18,
                        bgcolor=ft.Colors.BLUE_200,
                        content=ft.Text(
                            (current_user.get("nombre_usuario", current_user.get("name", "U")))[:1].upper(),
                            color=ft.Colors.WHITE,
                        ) if not photo_url else None,
                    ),
                    on_tap=lambda e: NavigationController.update_view("Perfil"),
                )
            )

        from utils.helpers import get_logo_control
        logo_ctrl = get_logo_control(width=28, height=28)

        logo_wordmark = ft.Row(
            [
                ft.Text(
                    "Point",
                    size=20 if is_mobile else 22,
                    weight=ft.FontWeight.BOLD,
                    color="#F8FAFC" if self.page.theme_mode == ft.ThemeMode.DARK else "#0A2348",
                    font_family="Poppins",
                ),
                ft.Text(
                    "List",
                    size=20 if is_mobile else 22,
                    weight=ft.FontWeight.BOLD,
                    color="#57E249",
                    font_family="Poppins",
                ),
            ],
            spacing=0,
            visible=self.page.width > 450,
        )

        return ft.Container(
            height=70,
            bgcolor=colors["navbar"],
            padding=ft.padding.symmetric(horizontal=16 if is_mobile else 24),
            shadow=ft.BoxShadow(
                blur_radius=10,
                spread_radius=-2,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2),
            ),
            content=ft.Row(
                controls=[
                    ft.Row([
                        self._build_popup_menu(),
                        ft.Container(width=5 if is_mobile else 10),
                        # Logo y nombre (Acceso directo a Inicio)
                        ft.Container(
                            ink=True,
                            on_click=lambda _: NavigationController.update_view("Inicio"),
                            tooltip="Ir a Inicio",
                            content=ft.Row([
                                logo_ctrl,
                                logo_wordmark,
                            ], spacing=8)
                        ),
                    ]),
                    ft.Row(right_controls, spacing=0),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _toggle_drawer(self, e):
        """Abre el panel lateral de navegación estilo Drawer."""
        from services.navigation_service import NavigationController
        from utils.helpers import get_logo_control
        colors = self._get_theme_colors()

        def _nav(view_name):
            try:
                if self.page.drawer:
                    self.page.drawer.open = False
                    self.page.update()
            except: pass
            NavigationController.update_view(view_name)

        def _logout():
            try:
                if self.page.drawer:
                    self.page.drawer.open = False
                    self.page.update()
            except:
                pass
            NavigationController.logout()

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        drawer_logo = get_logo_control(width=34, height=34)
        active_view = NavigationController.current_view_name
        drawer_bg = "#FFFFFF" if not is_dark else "#111827"
        navy = "#0A2348" if not is_dark else "#E5E7EB"
        inactive_icon_bg = "#F1F5FF" if not is_dark else "#1E293B"
        active_bg = "#EDFFE9" if not is_dark else "#12351E"
        active_green = "#35D64A"

        def _dot_grid():
            return ft.Column(
                [
                    ft.Row(
                        [ft.Container(width=5, height=5, border_radius=3, bgcolor=navy) for _ in range(3)],
                        spacing=6,
                    )
                    for _ in range(3)
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        def _wordmark(size: int = 23):
            return ft.Row(
                [
                    ft.Text("Point", size=size, weight=ft.FontWeight.BOLD, color=navy, font_family="Poppins"),
                    ft.Text("List", size=size, weight=ft.FontWeight.BOLD, color="#57E249", font_family="Poppins"),
                ],
                spacing=0,
            )

        def _drawer_item(view_name: str, label: str, icon, selected: bool = False):
            return ft.Container(
                height=52,
                border_radius=13,
                bgcolor=active_bg if selected else None,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=ft.Row(
                    [
                        ft.Container(width=5, height=52, bgcolor=active_green if selected else ft.Colors.TRANSPARENT),
                        ft.Container(width=14),
                        ft.Container(
                            width=42,
                            height=42,
                            border_radius=12,
                            bgcolor=ft.Colors.TRANSPARENT if selected else inactive_icon_bg,
                            alignment=ft.alignment.center,
                            content=ft.Icon(icon, color=navy, size=24),
                        ),
                        ft.Container(width=16),
                        ft.Text(label, size=18, weight=ft.FontWeight.BOLD, color=navy),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                ink=True,
                on_click=lambda _: _nav(view_name),
            )

        menu_items = [
            ("Inicio", self.translate("nav_home"), ft.Icons.HOME_OUTLINED),
            ("Notas", self.translate("nav_notes"), ft.Icons.BAR_CHART_OUTLINED),
            ("Asignaciones", self.translate("nav_assignments"), ft.Icons.ASSIGNMENT_OUTLINED),
            ("Calendario", self.translate("nav_calendar"), ft.Icons.CALENDAR_MONTH_OUTLINED),
            ("Tecnicas", self.translate("nav_techniques"), ft.Icons.LIGHTBULB_OUTLINE),
            ("Mensajeria", self.translate("nav_messaging"), ft.Icons.CHAT_OUTLINED),
            ("ChatBot", self.translate("nav_chatbot"), ft.Icons.SMART_TOY_OUTLINED),
            ("Perfil", self.translate("nav_my_profile"), ft.Icons.PERSON_OUTLINE),
        ]

        drawer = ft.NavigationDrawer(
            bgcolor=ft.Colors.TRANSPARENT,
            controls=[
                ft.Container(
                    width=310,
                    height=self.page.height or 860,
                    margin=ft.margin.only(left=6, top=8, bottom=8),
                    padding=ft.padding.only(left=20, right=20, top=24, bottom=24),
                    bgcolor=drawer_bg,
                    border_radius=ft.border_radius.all(26),
                    shadow=ft.BoxShadow(blur_radius=24, spread_radius=-8, color=ft.Colors.with_opacity(0.16, ft.Colors.BLACK)),
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    drawer_logo,
                                    _wordmark(),
                                    ft.Container(expand=True),
                                    ft.GestureDetector(
                                        mouse_cursor=ft.MouseCursor.CLICK,
                                        on_tap=lambda _: setattr(self.page.drawer, "open", False) or self.page.update(),
                                        content=ft.Container(
                                            width=48,
                                            height=42,
                                            alignment=ft.alignment.center,
                                            tooltip=self.translate("settings_close"),
                                            content=_dot_grid(),
                                        ),
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Container(height=22),
                            ft.Divider(height=1, color=colors["divider"]),
                            ft.Container(height=20),
                            ft.Column(
                                [
                                    _drawer_item(view_name, label, icon, selected=(active_view == view_name))
                                    for view_name, label, icon in menu_items
                                ],
                                spacing=12,
                            ),
                            ft.Container(expand=True),
                            ft.Divider(height=1, color=colors["divider"]),
                            ft.Container(height=20),
                            ft.Container(
                                height=56,
                                border_radius=14,
                                bgcolor=active_bg,
                                border=ft.border.all(1, "#CDEFCB" if not is_dark else "#2F6B3B"),
                                padding=ft.padding.symmetric(horizontal=18),
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.LOGOUT, color="#16A34A", size=28),
                                        ft.Container(width=14),
                                        ft.Text(self.translate("nav_logout"), size=18, weight=ft.FontWeight.BOLD, color="#16A34A"),
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                ink=True,
                                on_click=lambda _: _logout(),
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                )
            ],
        )
        self.page.drawer = drawer
        drawer.open = True
        self.page.update()

    def _build_popup_menu(self) -> ft.Control:
        """Construye el botón del menú hamburguesa."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK

        return ft.IconButton(
            icon=ft.Icons.MENU,
            icon_color="#000000" if not is_dark else ft.Colors.WHITE,
            icon_size=32,
            tooltip=self.translate("menu_main"),
            on_click=self._toggle_drawer,
        )

    def _show_snackbar(self, message: str, color: str = ft.Colors.BLUE_600):
        """Muestra un mensaje toast en la parte inferior de la pantalla de forma segura."""
        def _update():
            snack = ft.SnackBar(
                content=ft.Text(message, color=ft.Colors.WHITE),
                bgcolor=color,
                behavior=ft.SnackBarBehavior.FLOATING,
                shape=ft.RoundedRectangleBorder(radius=10),
                margin=ft.margin.all(20),
                elevation=8,
                open=True,
            )
            self.page.open(snack)
        run_async_safe(self.page, _update)

    def _show_error(self, message: str):
        self._show_snackbar(f"❌ {message}", ft.Colors.RED_600)

    def _show_success(self, message: str):
        self._show_snackbar(f"✅ {message}", ft.Colors.GREEN_600)

    def _show_info(self, message: str):
        self._show_snackbar(f"ℹ️ {message}", ft.Colors.BLUE_600)
