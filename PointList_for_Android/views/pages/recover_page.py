"""
pages/recover_page.py
PointList v13 Mobile Responsive
Página de recuperación de contraseña.
"""

import flet as ft
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode


class RecuperarContrasenaPage(BasePage):
    """Página para solicitar recuperación de contraseña por email."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.status_text = ft.Text("", color=ft.Colors.GREEN_600, size=13, text_align=ft.TextAlign.CENTER)

    def _send_recovery(self, e):
        email = self.email_field.value.strip()
        if not email:
            self.email_field.error_text = "Email requerido"
            self.page.update()
            return

        self.status_text.value = (
            f"Si '{email}' está registrado, recibirás un correo con instrucciones. "
            "Revisa tu bandeja de entrada."
        )
        self.page.update()

    def build(self) -> ft.Control:
        colors = self._get_theme_colors()
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK if self.page else False
        is_mob = self.is_mobile()



        field_bg = "#1E293B" if is_dark else ft.Colors.WHITE
        field_color = "#F1F5F9" if is_dark else "#111827"
        border_color = "#334155" if is_dark else "#CBD5E1"

        self.email_field = ft.TextField(
            hint_text="correo@ejemplo.com",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            keyboard_type=ft.KeyboardType.EMAIL,
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

        card = ft.Container(
            width=None if is_mob else 440,
            padding=ft.padding.all(20 if is_mob else 32),
            bgcolor=colors["surface"],
            border_radius=16 if is_mob else 24,
            border=ft.border.all(1, colors["border"]),
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Icon(ft.Icons.LOCK_RESET, size=28, color=self.primary_color),
                        ft.Container(width=8),
                        ft.Text("Recuperar contraseña", size=20, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=12),
                    ft.Text(
                        "Ingresa tu correo electrónico y te enviaremos instrucciones para restablecer tu contraseña.",
                        size=13, color=colors["text_secondary"], text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=20),
                    self.email_field,
                    ft.Container(height=16),
                    ft.ElevatedButton(
                        "Enviar instrucciones",
                        on_click=self._send_recovery,
                        bgcolor=self.primary_color,
                        color=ft.Colors.WHITE,
                        height=48,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), text_style=ft.TextStyle(size=14, weight="bold")),
                    ),
                    ft.Container(height=12),
                    self.status_text,
                    ft.Container(height=16),
                    ft.Row([
                        ft.TextButton(
                            "← Volver al inicio de sesión",
                            on_click=lambda e: NavigationController.update_view("Login"),
                            style=ft.ButtonStyle(color=self.primary_color),
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

        return ft.Container(
            expand=True,
            bgcolor=colors["background"],
            padding=ft.padding.symmetric(horizontal=16 if is_mob else 32, vertical=16 if is_mob else 32),
            alignment=ft.alignment.center,
            content=ft.Column([card], scroll=get_scroll_mode(self.page), alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )
