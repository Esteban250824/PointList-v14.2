"""
pages/registration_page.py
PointList v0.14.25experiment
Página de registro de nuevos usuarios con diseño de doble panel Figma.
"""

import re
import threading
import os
import flet as ft
from views.pages.base_page import BasePage
from utils.flet_compat import get_scroll_mode


class RegistrationPage(BasePage):
    """Página de registro de nuevos usuarios con diseño premium v13."""

    def __init__(self, page: ft.Page):
        super().__init__(page)
        self.dark_mode = self.page.theme_mode == ft.ThemeMode.DARK
        self._refresh_field_theme()

        self.terms_checkbox = ft.Checkbox(
            label="Acepto los Términos de servicio y la política de privacidad", 
            value=False, 
            scale=1.0
        )
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
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        field_bg = "#1E293B" if is_dark else ft.Colors.WHITE
        field_color = "#F1F5F9" if is_dark else "#111827"
        border_color = "#475569" if is_dark else "#D1D5DB"

        self.name_field = ft.TextField(
            hint_text="Ingresa tu nombre completo",
            prefix_icon=ft.Icons.PERSON,
            expand=True,
            border_radius=10,
            text_size=16,
            height=64,
            bgcolor=field_bg,
            color=field_color,
            border_color="#111827" if not is_dark else border_color,
            focused_border_color="#07547B",
            content_padding=ft.padding.symmetric(horizontal=20, vertical=14),
        )

        self.email_field = ft.TextField(
            hint_text="Ingresa tu correo electrónico",
            prefix_icon=ft.Icons.PERSON,  # Como en Figma: ícono de persona para el correo
            expand=True,
            border_radius=10,
            text_size=16,
            height=64,
            bgcolor=field_bg,
            color=field_color,
            border_color="#111827" if not is_dark else border_color,
            focused_border_color="#07547B",
            content_padding=ft.padding.symmetric(horizontal=20, vertical=14),
            on_change=self._validate_email,
        )

        self.rol_dropdown = ft.Container(
            height=64,
            content=ft.Dropdown(
                hint_text="Tipo de cuenta",
                prefix_icon=ft.Icons.SCHOOL,
                options=[
                    ft.dropdown.Option("estudiante", "Estudiante"),
                    ft.dropdown.Option("profesor", "Profesor"),
                ],
                value="estudiante",
                expand=True,
                border_radius=10,
                text_size=16,
                bgcolor=field_bg,
                color=field_color,
                border_color="#111827" if not is_dark else border_color,
                focused_border_color="#07547B",
                content_padding=ft.padding.symmetric(horizontal=20, vertical=14),
            )
        )

        self.pw_field = ft.TextField(
            hint_text="Ingresa tu contraseña",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            expand=True,
            border_radius=10,
            text_size=16,
            height=64,
            bgcolor=field_bg,
            color=field_color,
            border_color="#111827" if not is_dark else border_color,
            focused_border_color="#07547B",
            content_padding=ft.padding.symmetric(horizontal=20, vertical=14),
        )

        self.confirm_pw_field = ft.TextField(
            hint_text="Confirma tu contraseña",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            expand=True,
            border_radius=10,
            text_size=16,
            height=64,
            bgcolor=field_bg,
            color=field_color,
            border_color="#111827" if not is_dark else border_color,
            focused_border_color="#07547B",
            content_padding=ft.padding.symmetric(horizontal=20, vertical=14),
            on_submit=self._register_user,
        )

        self.error_banner = ft.Container(
            visible=False,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border_radius=8,
            bgcolor=ft.Colors.RED_900 if is_dark else ft.Colors.RED_100,
            content=ft.Row([
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_400),
                ft.Text("", expand=True, color=ft.Colors.RED_400 if is_dark else ft.Colors.RED),
            ]),
            animate=ft.Animation(300, "easeOut"),
        )

    def _validate_email(self, e):
        email = self.email_field.value.strip()
        if email:
            pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            self.email_field.error_text = None if re.match(pattern, email) else "Formato de email inválido"
        else:
            self.email_field.error_text = None
        self.page.update()

    def _validate_password(self, password: str) -> tuple[bool, str]:
        """Valida que la contraseña cumpla los requisitos de Figma."""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres."
        if not re.search(r"[A-Z]", password):
            return False, "La contraseña debe contener al menos una mayúscula."
        if not re.search(r"\d", password):
            return False, "La contraseña debe contener al menos un número."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "La contraseña debe contener al menos un símbolo."
        return True, ""

    def _validate_form(self) -> bool:
        valid = True
        if not self.name_field.value.strip():
            self.name_field.error_text = "Nombre requerido"
            valid = False
        else:
            self.name_field.error_text = None

        if not self.email_field.value.strip():
            self.email_field.error_text = "Email requerido"
            valid = False
        else:
            self.email_field.error_text = None

        if not self.pw_field.value:
            self.pw_field.error_text = "Contraseña requerida"
            valid = False
        else:
            self.pw_field.error_text = None

        if self.pw_field.value != self.confirm_pw_field.value:
            self.confirm_pw_field.error_text = "Las contraseñas no coinciden"
            valid = False
        else:
            self.confirm_pw_field.error_text = None

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

    def _continue_with_google(self, e=None):
        """Abre el diálogo modal oficial de Selección de Cuenta de Google (Account Chooser)."""
        from services.google_service import google_service, GoogleIntegrationService
        from services.database_service import db
        from services.navigation_service import NavigationController

        accounts = GoogleIntegrationService.get_saved_google_accounts()
        custom_email_input = ft.TextField(
            hint_text="ingresa_tu_correo@gmail.com",
            border_radius=10,
            text_size=13,
            visible=False,
            expand=True
        )

        def _login_with_email(target_email):
            self.page.close(dlg)
            res = google_service.authenticate_with_google(target_email)
            if res["ok"]:
                g_email = res["email"]
                g_name = res["name"]
                
                user_res = db.autenticar_usuario(g_email, "google_oauth_pass_2026")
                if not user_res["ok"]:
                    db.crear_usuario(g_name, g_email, "google_oauth_pass_2026", rol="estudiante")
                    user_res = db.autenticar_usuario(g_email, "google_oauth_pass_2026")

                if user_res["ok"]:
                    user = user_res["usuario"]
                    current_user_data = {
                        "id": user.get("id"),
                        "name": user.get("nombre_usuario", g_name),
                        "email": g_email,
                        "photo_url": res["photo_url"],
                        "rol": user.get("rol", "estudiante"),
                    }
                    self.page.client_storage.set("current_user", current_user_data)
                    NavigationController.cache["current_user"] = current_user_data
                    NavigationController.apply_user_preferences()
                    NavigationController.preload_data()
                    NavigationController.update_view("Inicio")

        account_tiles = []
        for acc in accounts:
            account_tiles.append(
                ft.ListTile(
                    leading=ft.CircleAvatar(content=ft.Text(acc["name"][0], weight="bold", color="white"), bgcolor="#4285F4"),
                    title=ft.Text(acc["name"], weight="bold", size=14),
                    subtitle=ft.Text(acc["email"], size=12, color="#64748B"),
                    on_click=lambda _, em=acc["email"]: _login_with_email(em)
                )
            )

        def _toggle_custom_email(e):
            custom_email_input.visible = not custom_email_input.visible
            try: self.page.update()
            except: pass

        def _submit_custom_email(e):
            val = custom_email_input.value.strip()
            if val and "@" in val:
                _login_with_email(val)

        account_tiles.append(
            ft.ListTile(
                leading=ft.Icon(ft.Icons.PERSON_ADD_OUTLINED, color="#4285F4"),
                title=ft.Text("Usar otra cuenta de Google...", size=13, weight="bold", color="#4285F4"),
                on_click=_toggle_custom_email
            )
        )

        dlg = ft.AlertDialog(
            title=ft.Column([
                ft.Row([
                    ft.Text("G", size=24, weight="bold", color="#4285F4"),
                    ft.Text("o", size=24, weight="bold", color="#EA4335"),
                    ft.Text("o", size=24, weight="bold", color="#FBBC05"),
                    ft.Text("g", size=24, weight="bold", color="#4285F4"),
                    ft.Text("l", size=24, weight="bold", color="#34A853"),
                    ft.Text("e", size=24, weight="bold", color="#EA4335"),
                ], spacing=1, alignment=ft.MainAxisAlignment.CENTER),
                ft.Text("Elige una cuenta", size=18, weight="bold", text_align=ft.TextAlign.CENTER),
                ft.Text("para continuar en PointList", size=12, color="#64748B", text_align=ft.TextAlign.CENTER),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            content=ft.Container(
                width=380,
                content=ft.Column([
                    ft.Column(account_tiles, spacing=4),
                    ft.Container(height=6),
                    custom_email_input,
                    ft.ElevatedButton("Continuar con esta cuenta", bgcolor="#4285F4", color="white", on_click=_submit_custom_email)
                ], tight=True, spacing=6)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg))
            ]
        )
        self.page.open(dlg)

    def _show_email_otp_dialog(self, name: str, email: str, pw: str, rol: str):
        """Muestra el diálogo de Verificación de Correo Electrónico con código OTP de 6 dígitos."""
        from services.google_service import google_service
        from services.database_service import db
        from services.navigation_service import NavigationController

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
        smtp_active = bool(os.getenv("SMTP_EMAIL") and os.getenv("SMTP_PASSWORD"))
        if smtp_active:
            subtext = "📩 Revisa tu bandeja de entrada (o spam) para ver tu código de 6 dígitos."
        else:
            subtext = f"⭐ Código de prueba rápido: {otp_code}"

        otp_error_text = ft.Text(subtext, color="#0284C7", size=12, text_align=ft.TextAlign.CENTER)

        def _verify_and_register(e):
            code = otp_field.value.strip()
            if google_service.verify_email_otp(email, code):
                self.page.close(dlg)
                result = db.crear_usuario(name, email, pw, rol=rol)
                if result["ok"]:
                    self._show_success(f"¡Correo verificado con éxito! Bienvenido a PointList como {rol}")
                    threading.Timer(2.0, lambda: NavigationController.update_view("Login")).start()
                else:
                    self._show_error(result["error"])
            else:
                otp_error_text.value = "⚠️ Código inválido o expirado. Revisa tu correo e inténtalo de nuevo."
                otp_error_text.color = "red"
                try: self.page.update()
                except: pass

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.MARK_EMAIL_READ, color="#0284C7", size=24),
                ft.Text("Verificación de Correo", size=16, weight="bold")
            ]),
            content=ft.Column([
                ft.Text(f"Hemos enviado un código OTP de 6 dígitos a:", size=12, color="#64748B"),
                ft.Text(email, size=13, weight="bold", color="#0F172A"),
                ft.Container(height=10),
                ft.Row([otp_field], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=6),
                otp_error_text,
            ], tight=True, spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close(dlg)),
                ft.ElevatedButton("Verificar y Crear Cuenta", bgcolor="#0284C7", color="white", on_click=_verify_and_register),
            ],
        )
        self.page.open(dlg)

    def _register_user(self, e):
        if not self._validate_form():
            return

        email = self.email_field.value.strip()
        name  = self.name_field.value.strip()
        pw    = self.pw_field.value
        rol   = self.rol_dropdown.content.value

        # Validar requisitos de contraseña de Figma
        is_valid_pw, pw_error = self._validate_password(pw)
        if not is_valid_pw:
            self._show_error(pw_error)
            return

        # Lanzar la Verificación de Correo Obligatoria antes de registrar
        self._show_email_otp_dialog(name, email, pw, rol)

    def _build_left_panel(self, is_dark: bool) -> ft.Container:
        left_bg = "#F5F8FD" if not is_dark else "#111827"
        title_color = "#0F172A" if not is_dark else "#F8FAFC"
        subtitle_color = "#475569" if not is_dark else "#94A3B8"

        panel_width = max(300, int((self.page.width or 1600) * 0.25))
        content_width = panel_width - 80

        if self.left_panel_image:
            # Si hay una imagen, la ponemos en el fondo
            illustration = ft.Image(
                src=self.left_panel_image,
                fit=ft.ImageFit.COVER,
                expand=True,
            )
        else:
            # Fallback en base a figuras geométricas premium
            illustration = ft.Stack([
                ft.Container(
                    width=int(content_width * 0.3),
                    height=240,
                    left=0,
                    bottom=0,
                    border_radius=ft.border_radius.only(top_right=120, bottom_right=120),
                    bgcolor="#0AA174",
                ),
                ft.Container(
                    width=content_width,
                    height=240,
                    right=0,
                    bottom=0,
                    border_radius=ft.border_radius.only(top_left=120, bottom_left=120),
                    bgcolor="#0F4E7A",
                ),
                ft.Container(
                    width=int(content_width * 0.7),
                    height=180,
                    left=int(content_width * 0.18),
                    bottom=30,
                    border_radius=ft.border_radius.all(92),
                    bgcolor="#37729C",
                ),
            ], width=content_width, height=240, clip_behavior=ft.ClipBehavior.HARD_EDGE)

        from utils.helpers import get_logo_control
        logo_ctrl = get_logo_control(width=56, height=56)

        return ft.Container(
            width=panel_width,
            bgcolor=left_bg,
            padding=ft.padding.only(left=40, right=40, top=40, bottom=40),
            content=ft.Column([
                ft.Row([
                    logo_ctrl,
                    ft.Container(width=12),
                    ft.Text("PointList", size=30, weight=ft.FontWeight.BOLD, color=title_color),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=32),
                ft.Text(
                    "Crea tu cuenta y empieza a organizarte",
                    size=36,
                    weight=ft.FontWeight.BOLD,
                    color=title_color,
                    width=content_width,
                ),
                ft.Container(height=20),
                ft.Text(
                    "Únete a PointList y lleva tus calificaciones, tareas y proyectos al siguiente nivel.",
                    size=16,
                    color=subtitle_color,
                    width=content_width,
                ),
                ft.Container(height=28),
                ft.Container(expand=True),
                illustration,
            ], expand=True, spacing=0),
        )

    def _social_button(self, icon: str, color: str, label=""):
        on_clk = self._continue_with_google if label == "Google" else lambda e: print(f"Social registration: {label or icon}")
        return ft.Container(
            width=56,
            height=56,
            border_radius=28,
            bgcolor=ft.Colors.WHITE,
            alignment=ft.alignment.center,
            content=ft.Text(icon, color=color, size=26, weight=ft.FontWeight.BOLD),
            on_click=on_clk,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12, offset=ft.Offset(0, 6)),
        )

    def build(self) -> ft.Control:
        from services.navigation_service import NavigationController
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        self._refresh_field_theme()

        colors = self._get_theme_colors()
        page_bg = colors["background"]
        right_bg = colors["surface"]
        title_color = colors["text"]
        subtitle_color = colors["text_secondary"]
        link_color = "#07547B" if not is_dark else "#818CF8"

        form_column = ft.Column([
            ft.Text("Crear cuenta", size=34, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=8),
            ft.Text("Completa tus datos para registrarte en PointList.", size=16, color=subtitle_color),
            ft.Container(height=24),
            self.error_banner,
            
            ft.Text("Nombre completo", size=14, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=8),
            self.name_field,
            ft.Container(height=16),
            
            ft.Text("Correo electrónico", size=14, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=8),
            self.email_field,
            ft.Container(height=16),

            ft.Text("Tipo de cuenta", size=14, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=8),
            self.rol_dropdown,
            ft.Container(height=16),
            
            ft.Text("Contraseña", size=14, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=8),
            self.pw_field,
            ft.Text("Mínimo 8 caracteres, con mayúscula, número y símbolo.", size=11, color=subtitle_color),
            ft.Container(height=16),

            ft.Text("Confirmar contraseña", size=14, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=8),
            self.confirm_pw_field,
            ft.Container(height=16),

            ft.Row([
                self.terms_checkbox
            ]),
            ft.Container(height=20),
            
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Text("Iniciar Sesión", size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.WHITE, size=18),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                on_click=self._register_user,
                bgcolor="#0A1E3D",  # Azul marino oscuro Figma
                height=56,
                expand=True,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16)),
            ),
            ft.Container(height=20),
            ft.Row([
                ft.Container(expand=True, height=1, bgcolor="#E2E8F0"),
                ft.Container(padding=ft.padding.symmetric(horizontal=12), content=ft.Text("o continua con", size=12, color=subtitle_color)),
                ft.Container(expand=True, height=1, bgcolor="#E2E8F0"),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=16),
            ft.Row([
                self._social_button("G", "#EA4335", "Google"),
                ft.Container(width=16),
                self._social_button("f", "#1877F2", "Facebook"),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=20),
            ft.Row([
                ft.Text("¿Ya tienes cuenta?", size=14, color=subtitle_color),
                ft.Container(width=8),
                ft.TextButton(
                    "Iniciar Sesión",
                    on_click=lambda e: NavigationController.update_view("Login"),
                    style=ft.ButtonStyle(color="#FF4D6E", text_style=ft.TextStyle(size=14)),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=12),
            ft.Row([self.loading_indicator], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        # Usar scroll en el formulario para asegurar responsividad vertical
        registration_card = ft.Container(
            width=520,
            padding=ft.padding.all(40),
            bgcolor=right_bg,
            border_radius=24,
            shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.BLACK12, offset=ft.Offset(0, 12)),
            content=ft.Column([form_column], scroll=get_scroll_mode("AUTO")),
        )

        right_panel = ft.Container(
            expand=True,
            bgcolor=page_bg,
            padding=ft.padding.symmetric(horizontal=40, vertical=40),
            alignment=ft.alignment.center,
            content=registration_card,
        )

        left_panel = self._build_left_panel(is_dark)
        right_side = ft.Container(
            expand=True,
            bgcolor=page_bg,
            content=right_panel,
        )

        is_desktop = (self.page.width or 1200) >= 980
        if is_desktop:
            split = ft.Row(
                controls=[left_panel, right_side],
                expand=True,
                spacing=0,
            )
        else:
            split = ft.Column(
                controls=[left_panel, right_side],
                expand=True,
                spacing=0,
            )

        return ft.Container(
            expand=True,
            bgcolor=page_bg,
            content=split,
        )
