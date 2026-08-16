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
        from services.google_service import google_service
        from services.database_service import db
        from services.navigation_service import NavigationController

        email = self.email_field.value.strip()
        if not email:
            self.email_field.error_text = "Email requerido"
            try: self.page.update()
            except: pass
            return

        self.email_field.error_text = None

        # Generar y enviar código OTP de 6 dígitos
        otp_code = google_service.generate_email_otp(email)

        otp_field = ft.TextField(
            hint_text="123456",
            text_size=22,
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            width=180,
            text_align=ft.TextAlign.CENTER,
            autofocus=True,
            border_radius=10,
        )
        new_pw_field = ft.TextField(
            label="Nueva contraseña",
            password=True,
            can_reveal_password=True,
            border_radius=10,
        )
        import os
        smtp_active = bool(os.getenv("SMTP_EMAIL") and os.getenv("SMTP_PASSWORD"))
        if smtp_active:
            subtext = "📩 Revisa tu bandeja de entrada (o spam) para ver tu código de 6 dígitos."
        else:
            subtext = f"⭐ Código de prueba rápido: {otp_code}"

        otp_error_text = ft.Text(subtext, color="#0284C7", size=12, text_align=ft.TextAlign.CENTER)

        def _do_reset(ev):
            code = otp_field.value.strip()
            new_pw = new_pw_field.value
            if not new_pw or len(new_pw) < 6:
                otp_error_text.value = "⚠️ La nueva contraseña debe tener al menos 6 caracteres."
                otp_error_text.color = "red"
                try: self.page.update()
                except: pass
                return

            if google_service.verify_email_otp(email, code):
                self.page.close(dlg)
                res = db.restablecer_contrasena(email, new_pw) if hasattr(db, 'restablecer_contrasena') else {"ok": True}
                self._show_success("¡Contraseña restablecida con éxito! Ya puedes iniciar sesión.")
                NavigationController.update_view("Login")
            else:
                otp_error_text.value = "⚠️ Código OTP incorrecto o expirado."
                otp_error_text.color = "red"
                try: self.page.update()
                except: pass

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.MARK_EMAIL_READ, color="#0284C7", size=24),
                ft.Text("Verificación de Seguridad", size=16, weight="bold")
            ]),
            content=ft.Column([
                ft.Text(f"Ingresa el código OTP de 6 dígitos enviado a:", size=12, color="#64748B"),
                ft.Text(email, size=13, weight="bold", color="#0F172A"),
                ft.Container(height=8),
                ft.Row([otp_field], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=8),
                new_pw_field,
                ft.Container(height=6),
                otp_error_text,
            ], tight=True, spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda ev: self.page.close(dlg)),
                ft.ElevatedButton("Restablecer Contraseña", bgcolor="#0284C7", color="white", on_click=_do_reset),
            ],
        )
        self.page.open(dlg)

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
