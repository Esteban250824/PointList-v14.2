"""
pages/recover_page.py
PointList v0.14.25experiment
Página de recuperación de contraseña.
"""

import flet as ft
from views.pages.base_page import BasePage


class RecuperarContrasenaPage(BasePage):
    """Página para solicitar recuperación de contraseña por email."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.email_field = ft.TextField(
            label="Correo electrónico",
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            keyboard_type=ft.KeyboardType.EMAIL,
            expand=True,
            border_radius=12,
            text_size=14,
        )
        self.status_text = ft.Text("", color=ft.Colors.GREEN_700, size=14,
                                   text_align=ft.TextAlign.CENTER)

    def _send_recovery(self, e):
        email = self.email_field.value.strip()
        if not email:
            self.email_field.error_text = "Email requerido"
            self.page.update()
            return

        # En producción, aquí se enviaría un email de recuperación.
        # Por ahora, se muestra un mensaje informativo.
        self.status_text.value = (
            f"Si '{email}' está registrado, recibirás un correo con instrucciones. "
            "Revisa tu bandeja de entrada."
        )
        self.page.update()

    def build(self) -> ft.Control:
        from services.navigation_service import NavigationController

        card = ft.Container(
            width=min(400, (self.page.width or 500) - 40),
            padding=ft.padding.all(36),
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            shadow=ft.BoxShadow(
                blur_radius=20, spread_radius=2,
                offset=ft.Offset(0, 6),
                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
            ),
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Icon(ft.Icons.LOCK_RESET, size=30, color=ft.Colors.INDIGO_700),
                        ft.Container(width=10),
                        ft.Text("Recuperar contraseña", size=20,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=16),
                    ft.Text(
                        "Ingresa tu correo electrónico y te enviaremos instrucciones "
                        "para restablecer tu contraseña.",
                        size=14, color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=20),
                    self.email_field,
                    ft.Container(height=16),
                    ft.ElevatedButton(
                        "Enviar instrucciones",
                        on_click=self._send_recovery,
                        bgcolor=ft.Colors.INDIGO_700,
                        color=ft.Colors.WHITE,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.padding.symmetric(vertical=14),
                        ),
                        expand=True,
                    ),
                    ft.Container(height=12),
                    self.status_text,
                    ft.Container(height=12),
                    ft.Row([
                        ft.TextButton(
                            "← Volver al inicio de sesión",
                            on_click=lambda e: NavigationController.update_view("Login"),
                            style=ft.ButtonStyle(color=ft.Colors.INDIGO_600),
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.Colors.INDIGO_50, ft.Colors.BLUE_50],
            ),
            content=ft.Column(
                controls=[ft.Container(height=60), ft.Row([card], alignment=ft.MainAxisAlignment.CENTER)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
        )
