import re
import threading
import os
import flet as ft
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode


class LoginPage(BasePage):
    def __init__(self, page: ft.Page):
        super().__init__(page)
        self._refresh_field_theme()

        self.remember_me = ft.Checkbox(label="Mantener sesión iniciada", value=False, scale=0.9)
        self.error_banner = ft.Container(visible=False)
        self.loading_indicator = ft.ProgressRing(visible=False, width=20, height=20)

        self.left_panel_image = None
        for filename in [
            "login_left_panel.png",
            "login_left_panel.jpg",
            "login_left_panel.jpeg",
            "login_left_panel.webp",
        ]:
            path = os.path.join("assets", "figma_assets", filename)
            if os.path.isfile(path):
                self.left_panel_image = path
                break

    def _refresh_field_theme(self):
        """Recrea campos con colores según tema actual."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK if self.page else False
        field_bg = "#1E293B" if is_dark else ft.Colors.WHITE
        field_color = "#F1F5F9" if is_dark else "#111827"

        self.email_field = ft.TextField(
            hint_text="correo@ejemplo.com",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            expand=True,
            border_radius=12,
            text_size=14,
            height=50,
            bgcolor=field_bg,
            color=field_color,
            hint_style=ft.TextStyle(color="#94A3B8", size=14),
            border_color="#334155" if is_dark else "#CBD5E1",
            focused_border_color="#3B82F6",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
            on_change=self._validate_email,
        )
        self.pw_field = ft.TextField(
            hint_text="Ingresa tu contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            password=True,
            can_reveal_password=True,
            expand=True,
            border_radius=12,
            text_size=14,
            height=50,
            bgcolor=field_bg,
            color=field_color,
            hint_style=ft.TextStyle(color="#94A3B8", size=14),
            border_color="#334155" if is_dark else "#CBD5E1",
            focused_border_color="#3B82F6",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
            on_submit=self._on_login,
        )

        self.error_banner = ft.Container(
            visible=False,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border_radius=10,
            bgcolor=ft.Colors.RED_900 if is_dark else ft.Colors.RED_100,
            content=ft.Row([
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_400, size=20),
                ft.Text("", expand=True, color=ft.Colors.RED_400 if is_dark else ft.Colors.RED_700, size=13),
            ]),
        )

    def _validate_email(self, e):
        email = self.email_field.value.strip()
        if email:
            pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            self.email_field.error_text = None if re.match(pattern, email) else "Formato de email inválido"
        else:
            self.email_field.error_text = None
        self.page.update()

    def _validate_form(self) -> bool:
        valid = True
        if not self.email_field.value.strip():
            self.email_field.error_text = "Email requerido"
            valid = False
        if not self.pw_field.value:
            self.pw_field.error_text = "Contraseña requerida"
            valid = False
        self.page.update()
        return valid

    def _show_error(self, message: str):
        self.error_banner.content.controls[1].value = message
        self.error_banner.visible = True
        self.page.update()
        threading.Timer(5.0, self._hide_error).start()

    def _hide_error(self):
        self.error_banner.visible = False
        try:
            self.page.update()
        except:
            pass

    def _on_login(self, e):
        if not self._validate_form():
            return
        email = self.email_field.value.strip()
        password = self.pw_field.value
        self.loading_indicator.visible = True
        self.error_banner.visible = False
        self.page.update()
        try:
            from services.database_service import db
            from services.navigation_service import NavigationController
            result = db.autenticar_usuario(email, password)
            if not result["ok"]:
                self._show_error(result["error"])
                return
            user = result["usuario"]
            current_user_data = {
                "id": user.get("id"),
                "name": user.get("nombre_usuario", ""),
                "email": email,
                "photo_url": user.get("photo_url", ""),
                "rol": user.get("rol", "estudiante"),
            }
            if self.remember_me.value:
                self.page.client_storage.set("current_user", current_user_data)
            NavigationController.cache["current_user"] = current_user_data
            NavigationController.apply_user_preferences()
            NavigationController.preload_data()
            NavigationController.update_view("Inicio")
        except Exception as err:
            self._show_error(f"Error de conexión: {str(err)}")
        finally:
            self.loading_indicator.visible = False
            self.page.update()

    def _build_left_panel(self, is_dark: bool) -> ft.Container:
        left_bg = "#F5F8FD" if not is_dark else "#111827"
        title_color = "#0F172A" if not is_dark else "#F8FAFC"
        subtitle_color = "#475569" if not is_dark else "#94A3B8"

        panel_width = max(300, int((self.page.width or 1200) * 0.3))
        content_width = panel_width - 60

        if self.left_panel_image:
            return ft.Container(
                width=panel_width,
                bgcolor=left_bg,
                expand=True,
                content=ft.Image(
                    src=self.left_panel_image,
                    fit=ft.ImageFit.COVER,
                    expand=True,
                ),
            )

        return ft.Container(
            width=panel_width,
            bgcolor=left_bg,
            padding=ft.padding.all(32),
            content=ft.Column([
                ft.Row([
                    ft.Image(src="assets/logo.png", width=36, height=36, fit=ft.ImageFit.CONTAIN),
                    ft.Container(width=10),
                    ft.Text("PointList", size=26, weight=ft.FontWeight.BOLD, color=title_color),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=32),
                ft.Text(
                    "Tus notas, nuestra prioridad.",
                    size=36,
                    weight=ft.FontWeight.BOLD,
                    color=title_color,
                ),
                ft.Container(height=16),
                ft.Text(
                    "PointList te ayuda a organizar y dar seguimiento a tus calificaciones en cualquier dispositivo.",
                    size=14,
                    color=subtitle_color,
                ),
            ], expand=True, alignment=ft.MainAxisAlignment.CENTER),
        )

    def _social_button(self, icon: str, color: str, label=""):
        return ft.Container(
            width=48,
            height=48,
            border_radius=24,
            bgcolor=ft.Colors.WHITE,
            alignment=ft.alignment.center,
            content=ft.Text(icon, color=color, size=22, weight=ft.FontWeight.BOLD),
            on_click=lambda e: print(f"Social login: {label or icon}"),
            border=ft.border.all(1, "#E2E8F0"),
        )

    def build(self) -> ft.Control:
        from services.navigation_service import NavigationController
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK if self.page else False
        self._refresh_field_theme()

        colors = self._get_theme_colors()
        page_bg = colors["background"]
        card_bg = colors["surface"]
        title_color = colors["text"]
        subtitle_color = colors["text_secondary"]
        link_color = self.primary_color if not is_dark else "#818CF8"
        is_mob = self.is_mobile()




        header_mob = ft.Column([
            ft.Row([
                ft.Image(src="assets/logo.png", width=32, height=32, fit=ft.ImageFit.CONTAIN),
                ft.Text("PointList", size=24, weight="bold", color=title_color),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=12),
        ], visible=is_mob)

        form_column = ft.Column([
            header_mob,
            ft.Text("¡Bienvenido de nuevo!", size=22 if is_mob else 28, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=4),
            ft.Text("Por favor inicia sesión en tu cuenta.", size=13 if is_mob else 15, color=subtitle_color),
            ft.Container(height=20),
            self.error_banner,
            ft.Text("Correo electrónico", size=13, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=6),
            self.email_field,
            ft.Container(height=14),
            ft.Text("Contraseña", size=13, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=6),
            self.pw_field,
            ft.Container(height=14),
            ft.Row([
                self.remember_me,
                ft.TextButton(
                    "¿Olvidaste?",
                    on_click=lambda e: NavigationController.update_view("Recuperar"),
                    style=ft.ButtonStyle(color=link_color, padding=0),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=20),
            ft.ElevatedButton(
                "Iniciar Sesión",
                on_click=self._on_login,
                bgcolor=self.primary_color,
                color=ft.Colors.WHITE,
                height=48,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), text_style=ft.TextStyle(size=15, weight="bold")),
            ),
            ft.Container(height=20),
            ft.Row([
                ft.Container(expand=True, height=1, bgcolor=colors["divider"]),
                ft.Container(padding=ft.padding.symmetric(horizontal=8), content=ft.Text("o continúa con", size=12, color=subtitle_color)),
                ft.Container(expand=True, height=1, bgcolor=colors["divider"]),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=16),
            ft.Row([
                self._social_button("G", "#EA4335", "Google"),
                ft.Container(width=12),
                self._social_button("f", "#1877F2", "Facebook"),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=20),
            ft.Row([
                ft.Text("¿No tienes cuenta?", size=13, color=subtitle_color),
                ft.TextButton(
                    "Regístrate aquí",
                    on_click=lambda e: NavigationController.update_view("Registro"),
                    style=ft.ButtonStyle(color="#EC4899", text_style=ft.TextStyle(size=13, weight="bold")),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([self.loading_indicator], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        login_card = ft.Container(
            width=None if is_mob else 480,
            padding=ft.padding.all(20 if is_mob else 32),
            bgcolor=card_bg,
            border_radius=16 if is_mob else 24,
            border=ft.border.all(1, colors["border"]),
            content=form_column,
        )

        right_panel = ft.Container(
            expand=True,
            bgcolor=page_bg,
            padding=ft.padding.symmetric(horizontal=16 if is_mob else 32, vertical=16 if is_mob else 32),
            alignment=ft.alignment.center,
            content=ft.Column([login_card], scroll=get_scroll_mode(self.page), alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )

        if not is_mob:
            left_panel = self._build_left_panel(is_dark)
            return ft.Container(
                expand=True,
                bgcolor=page_bg,
                content=ft.Row([left_panel, right_panel], expand=True, spacing=0),
            )

        return ft.Container(
            expand=True,
            bgcolor=page_bg,
            content=right_panel,
        )
