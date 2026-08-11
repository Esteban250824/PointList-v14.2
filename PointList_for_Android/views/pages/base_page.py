"""
pages/base_page.py
PointList v13 Mobile Responsive
Clase base para todas las páginas de la aplicación con diseño adaptativo para Android/móvil.
"""

import flet as ft
from utils.flet_compat import run_async_safe
from utils.i18n import I18n, t


class BasePage:
    """
    Clase base que todas las páginas deben heredar.
    Provee acceso a la página de Flet, utilidades responsive y métodos comunes.
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

    def _get_theme_colors(self):
        """Devuelve los colores adecuados según el modo de tema actual."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK if self.page else False
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

    def is_mobile(self) -> bool:
        """Determina si la pantalla actual corresponde a un dispositivo móvil (< 768px)."""
        if not self.page:
            return True
        win_w = getattr(self.page.window, "width", None) if hasattr(self.page, "window") else None
        if win_w and win_w > 0 and win_w < 768:
            return True
        w = self.page.width
        if w and w > 0 and w < 768:
            return True
        if w is None or w == 0:
            return True
        return False


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

    def _build_bottom_nav(self, current_view: str = "Inicio") -> ft.Control:
        """Construye la barra de navegación inferior para pantallas móviles."""
        from services.navigation_service import NavigationController
        colors = self._get_theme_colors()

        view_indices = {
            "Inicio": 0,
            "Notas": 1,
            "Calendario": 2,
            "Tecnicas": 3,
            "ChatBot": 4,
        }
        index_views = ["Inicio", "Notas", "Calendario", "Tecnicas", "ChatBot"]
        selected_idx = view_indices.get(current_view, 0)

        def on_change(e):
            idx = e.control.selected_index
            if 0 <= idx < len(index_views):
                target = index_views[idx]
                NavigationController.update_view(target)

        return ft.NavigationBar(
            selected_index=selected_idx,
            bgcolor=colors["surface"],
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.HOME_OUTLINED,
                    selected_icon=ft.Icons.HOME,
                    label=self.translate("nav_home"),
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.BAR_CHART_OUTLINED,
                    selected_icon=ft.Icons.BAR_CHART,
                    label=self.translate("nav_notes"),
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
                    selected_icon=ft.Icons.CALENDAR_MONTH,
                    label=self.translate("nav_calendar"),
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.LIGHTBULB_OUTLINE,
                    selected_icon=ft.Icons.LIGHTBULB,
                    label=self.translate("nav_techniques"),
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.SMART_TOY_OUTLINED,
                    selected_icon=ft.Icons.SMART_TOY,
                    label=self.translate("nav_chatbot"),
                ),
            ],
            on_change=on_change,
        )

    def _build_navbar(self, title: str, show_user: bool = True) -> ft.Container:
        """Construye la barra de navegación superior responsiva."""
        from services.navigation_service import NavigationController
        colors = self._get_theme_colors()
        is_mob = self.is_mobile()

        current_user = NavigationController.get_current_user()

        right_controls = []
        # Conmutador de tema claro/oscuro
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK if self.page else False
        right_controls.append(
            ft.IconButton(
                icon=ft.Icons.WB_SUNNY_OUTLINED if is_dark else ft.Icons.NIGHTLIGHT_ROUND,
                icon_color=colors["primary"],
                tooltip="Cambiar Tema",
                on_click=lambda e: NavigationController.change_theme(not is_dark),
            )
        )

        if show_user:
            if not is_mob:
                user_name = current_user.get("nombre_usuario", current_user.get("name", ""))
                right_controls.append(ft.Text(user_name, color=colors["text_secondary"], size=14, weight="bold"))
                right_controls.append(ft.Container(width=8))

            photo_url = current_user.get("photo_url", "")
            right_controls.append(
                ft.GestureDetector(
                    content=ft.CircleAvatar(
                        foreground_image_src=photo_url if photo_url else None,
                        radius=16 if is_mob else 18,
                        bgcolor=ft.Colors.BLUE_400,
                        content=ft.Text(
                            (current_user.get("nombre_usuario", current_user.get("name", "U")))[:1].upper(),
                            color=ft.Colors.WHITE,
                            size=12 if is_mob else 14,
                        ) if not photo_url else None,
                    ),
                    on_tap=lambda e: NavigationController.update_view("Perfil"),
                )
            )

        navbar_container = ft.Container(
            height=56 if is_mob else 64,
            bgcolor=colors["navbar"],
            padding=ft.padding.symmetric(horizontal=12 if is_mob else 24),
            border=ft.Border(bottom=ft.BorderSide(1, colors["divider"])),
            content=ft.Row(
                controls=[
                    ft.Row([
                        self._build_popup_menu(),
                        ft.Container(width=4),
                        ft.Image(src="assets/logo.png", width=24 if is_mob else 28, height=24 if is_mob else 28, fit=ft.ImageFit.CONTAIN),
                        ft.Text(
                            title if is_mob else "PointList",
                            size=18 if is_mob else 20,
                            weight=ft.FontWeight.BOLD,
                            color=colors["text"],
                        ),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Row(right_controls, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        return ft.SafeArea(navbar_container, top=True, bottom=False) if is_mob else navbar_container

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

        drawer = ft.NavigationDrawer(
            bgcolor=colors["surface"],
            controls=[
                ft.Container(height=16),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=20, vertical=10),
                    content=ft.Row([
                        ft.Image(src="assets/logo.png", width=28, height=28, fit=ft.ImageFit.CONTAIN),
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
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK if self.page else False

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
                margin=ft.margin.all(16),
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
