"""
pages/registration_page.py
PointList v13 Mobile Responsive
Página de registro de nuevos usuarios.
"""

import re
import threading
import os
import flet as ft
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode


class RegistrationPage(BasePage):
    """Página de registro de nuevos usuarios adaptada a pantallas táctiles."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self._refresh_field_theme()

        self.terms_checkbox = ft.Checkbox(
            label="Acepto los Términos de servicio", 
            value=False, 
            scale=0.9
        )
        self.error_banner = ft.Container(visible=False)
        self.loading_indicator = ft.ProgressRing(visible=False, width=20, height=20)

    def _refresh_field_theme(self):
        """Recrea campos con colores según tema actual."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK if self.page else False
        field_bg = "#1E293B" if is_dark else ft.Colors.WHITE
        field_color = "#F1F5F9" if is_dark else "#111827"
        border_color = "#334155" if is_dark else "#CBD5E1"

        self.name_field = ft.TextField(
            hint_text="Nombre completo",
            prefix_icon=ft.Icons.PERSON_OUTLINED,
            expand=True,
            border_radius=12,
            text_size=14,
            height=50,
            bgcolor=field_bg,
            color=field_color,
            border_color=border_color,
            focused_border_color="#3B82F6",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )

        self.email_field = ft.TextField(
            hint_text="Correo electrónico",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            expand=True,
            border_radius=12,
            text_size=14,
            height=50,
            bgcolor=field_bg,
            color=field_color,
            border_color=border_color,
            focused_border_color="#3B82F6",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
            on_change=self._validate_email,
        )

        self.rol_dropdown = ft.Dropdown(
            hint_text="Tipo de cuenta",
            prefix_icon=ft.Icons.SCHOOL,
            options=[
                ft.dropdown.Option("estudiante", "Estudiante"),
                ft.dropdown.Option("profesor", "Profesor"),
            ],
            value="estudiante",
            expand=True,
            border_radius=12,
            text_size=14,
            bgcolor=field_bg,
            color=field_color,
            border_color=border_color,
            focused_border_color="#3B82F6",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )


        self.pw_field = ft.TextField(
            hint_text="Contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            password=True,
            can_reveal_password=True,
            expand=True,
            border_radius=12,
            text_size=14,
            height=50,
            bgcolor=field_bg,
            color=field_color,
            border_color=border_color,
            focused_border_color="#3B82F6",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )

        self.confirm_pw_field = ft.TextField(
            hint_text="Confirmar contraseña",
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            password=True,
            can_reveal_password=True,
            expand=True,
            border_radius=12,
            text_size=14,
            height=50,
            bgcolor=field_bg,
            color=field_color,
            border_color=border_color,
            focused_border_color="#3B82F6",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
            on_submit=self._on_register,
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
            self.email_field.error_text = None if re.match(pattern, email) else "Email inválido"
        else:
            self.email_field.error_text = None
        self.page.update()

    def _validate_form(self) -> bool:
        valid = True
        if not self.name_field.value.strip():
            self.name_field.error_text = "Nombre requerido"
            valid = False
        if not self.email_field.value.strip():
            self.email_field.error_text = "Email requerido"
            valid = False
        if not self.pw_field.value:
            self.pw_field.error_text = "Contraseña requerida"
            valid = False
        if self.pw_field.value != self.confirm_pw_field.value:
            self.confirm_pw_field.error_text = "Las contraseñas no coinciden"
            valid = False
        if not self.terms_checkbox.value:
            self._show_error("Debes aceptar los términos y condiciones")
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

    def _on_register(self, e):
        if not self._validate_form():
            return
        nombre = self.name_field.value.strip()
        email = self.email_field.value.strip()
        password = self.pw_field.value
        rol = self.rol_dropdown.value or "estudiante"

        self.loading_indicator.visible = True
        self.error_banner.visible = False
        self.page.update()

        try:
            from services.database_service import db
            from services.navigation_service import NavigationController
            res = db.crear_usuario(nombre, email, password, rol=rol)
            if not res["ok"]:
                self._show_error(res.get("error", "Error al crear la cuenta"))
                return
            user = res["usuario"]
            current_user_data = {
                "id": user.get("id"),
                "name": nombre,
                "email": email,
                "photo_url": "",
                "rol": rol,
            }
            NavigationController.cache["current_user"] = current_user_data
            NavigationController.apply_user_preferences()
            NavigationController.preload_data()
            NavigationController.update_view("Inicio")
        except Exception as err:
            self._show_error(f"Error al registrar: {str(err)}")
        finally:
            self.loading_indicator.visible = False
            self.page.update()

    def build(self) -> ft.Control:
        from services.navigation_service import NavigationController
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK if self.page else False
        self._refresh_field_theme()

        colors = self._get_theme_colors()
        page_bg = colors["background"]
        card_bg = colors["surface"]
        title_color = colors["text"]
        subtitle_color = colors["text_secondary"]
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
            ft.Text("Crea tu cuenta", size=22 if is_mob else 28, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=4),
            ft.Text("Únete a PointList y gestiona tus notas fácilmente.", size=13 if is_mob else 15, color=subtitle_color),
            ft.Container(height=16),
            self.error_banner,
            ft.Text("Nombre completo", size=13, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=4),
            self.name_field,
            ft.Container(height=12),
            ft.Text("Correo electrónico", size=13, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=4),
            self.email_field,
            ft.Container(height=12),
            ft.Text("Rol", size=13, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=4),
            self.rol_dropdown,
            ft.Container(height=12),
            ft.Text("Contraseña", size=13, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=4),
            self.pw_field,
            ft.Container(height=12),
            ft.Text("Confirmar contraseña", size=13, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=4),
            self.confirm_pw_field,
            ft.Container(height=12),
            self.terms_checkbox,
            ft.Container(height=16),
            ft.ElevatedButton(
                "Registrarse",
                on_click=self._on_register,
                bgcolor=self.primary_color,
                color=ft.Colors.WHITE,
                height=48,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), text_style=ft.TextStyle(size=15, weight="bold")),
            ),
            ft.Container(height=16),
            ft.Row([
                ft.Text("¿Ya tienes cuenta?", size=13, color=subtitle_color),
                ft.TextButton(
                    "Inicia sesión aquí",
                    on_click=lambda e: NavigationController.update_view("Login"),
                    style=ft.ButtonStyle(color="#EC4899", text_style=ft.TextStyle(size=13, weight="bold")),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([self.loading_indicator], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        reg_card = ft.Container(
            width=None if is_mob else 500,
            padding=ft.padding.all(20 if is_mob else 32),
            bgcolor=card_bg,
            border_radius=16 if is_mob else 24,
            border=ft.border.all(1, colors["border"]),
            content=form_column,
        )

        return ft.Container(
            expand=True,
            bgcolor=page_bg,
            padding=ft.padding.symmetric(horizontal=16 if is_mob else 32, vertical=16 if is_mob else 32),
            alignment=ft.alignment.center,
            content=ft.Column([reg_card], scroll=get_scroll_mode(self.page), alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )
