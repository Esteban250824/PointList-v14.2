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

        logo_path = os.path.join("assets", "logo.png")
        logo_ctrl = ft.Image(src=logo_path, width=28, height=28, fit=ft.ImageFit.CONTAIN) if os.path.isfile(logo_path) else ft.Icon(ft.Icons.SCHOOL, size=28, color=self.primary_color)

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
                        # Logo y nombre
                        ft.Row([
                            logo_ctrl,
                            ft.Text("PointList", size=20 if is_mobile else 22, weight=ft.FontWeight.BOLD, 
                                color=colors["text"], font_family="Poppins", visible=self.page.width > 450)
                        ], spacing=8),
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
        colors = self._get_theme_colors()

        def _nav(view_name):
            try:
                if self.page.drawer:
                    self.page.drawer.open = False
                    self.page.update()
            except: pass
            NavigationController.update_view(view_name)

        logo_path = os.path.join("assets", "logo.png")
        drawer_logo = ft.Image(src=logo_path, width=28, height=28, fit=ft.ImageFit.CONTAIN) if os.path.isfile(logo_path) else ft.Icon(ft.Icons.SCHOOL, color=self.primary_color, size=28)

        drawer = ft.NavigationDrawer(
            bgcolor=colors["surface"],
            controls=[
                ft.Container(height=16),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    content=ft.Row([
                        drawer_logo,
                        ft.Text("PointList", size=22, weight="bold", color=colors["text"]),
                    ], spacing=10)
                ),
                ft.Divider(height=16, color=colors["divider"]),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12),
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.HOME_OUTLINED, color=self.primary_color),
                            title=ft.Text(self.translate("nav_home"), weight="bold", color=colors["text"]),
                            on_click=lambda _: _nav("Inicio"),
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.BAR_CHART_OUTLINED, color=self.primary_color),
                            title=ft.Text(self.translate("nav_notes"), weight="bold", color=colors["text"]),
                            on_click=lambda _: _nav("Notas"),
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.ASSIGNMENT_OUTLINED, color=self.primary_color),
                            title=ft.Text("Asignaciones", weight="bold", color=colors["text"]),
                            on_click=lambda _: _nav("Asignaciones"),
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, color=self.primary_color),
                            title=ft.Text(self.translate("nav_calendar"), weight="bold", color=colors["text"]),
                            on_click=lambda _: _nav("Calendario"),
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.LIGHTBULB_OUTLINE, color=self.primary_color),
                            title=ft.Text(self.translate("nav_techniques"), weight="bold", color=colors["text"]),
                            on_click=lambda _: _nav("Tecnicas"),
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.CHAT_OUTLINED, color=self.primary_color),
                            title=ft.Text(self.translate("nav_messaging"), weight="bold", color=colors["text"]),
                            on_click=lambda _: _nav("Mensajeria"),
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.SMART_TOY_OUTLINED, color=self.primary_color),
                            title=ft.Text(self.translate("nav_chatbot"), weight="bold", color=colors["text"]),
                            on_click=lambda _: _nav("ChatBot"),
                        ),
                        ft.Divider(height=16, color=colors["divider"]),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.PERSON_OUTLINE, color=self.primary_color),
                            title=ft.Text(self.translate("nav_my_profile"), weight="bold", color=colors["text"]),
                            on_click=lambda _: _nav("Perfil"),
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.LOGOUT, color=ft.Colors.RED_400),
                            title=ft.Text(self.translate("nav_logout"), weight="bold", color=ft.Colors.RED_400),
                            on_click=lambda _: NavigationController.logout(),
                        ),
                    ], spacing=2)
                )
            ]
        )
        self.page.drawer = drawer
        drawer.open = True
        self.page.update()

    def _build_popup_menu(self) -> ft.Control:
        """Construye el botón del menú hamburguesa."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK

        return ft.IconButton(
            icon=ft.Icons.MENU,
            icon_color=self.primary_color if not is_dark else ft.Colors.WHITE,
            tooltip="Menú principal",
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
