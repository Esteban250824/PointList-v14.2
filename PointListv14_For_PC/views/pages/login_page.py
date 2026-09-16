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

        self.remember_me = ft.Checkbox(label="Mantener sesión iniciada", value=False, scale=1.0)
        self.error_banner = ft.Container(visible=False)
        self.loading_indicator = ft.ProgressRing(visible=False, width=20, height=20)
        self._asset_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "assets")
        )

    def _refresh_field_theme(self):
        """Recrea campos con colores según tema actual."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        field_bg = "#1E293B" if is_dark else ft.Colors.WHITE
        field_color = "#F1F5F9" if is_dark else "#111827"
        border_color = "#475569" if is_dark else "#D1D5DB"

        self.email_field = ft.TextField(
            hint_text=self.translate("auth_email_hint"),
            prefix_icon=ft.Icons.EMAIL_OUTLINED,
            expand=True,
            border_radius=10,
            text_size=14,
            height=52,
            bgcolor=field_bg,
            color=field_color,
            hint_style=ft.TextStyle(color="#94A3B8", size=14),
            border_color="#334155" if is_dark else "#CBD5E1",
            focused_border_color="#3B82F6",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
            on_change=self._validate_email,
        )
        self.pw_field = ft.TextField(
            hint_text=self.translate("auth_password_hint"),
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            password=True,
            can_reveal_password=True,
            expand=True,
            border_radius=10,
            text_size=14,
            height=52,
            bgcolor=field_bg,
            color=field_color,
            hint_style=ft.TextStyle(color="#94A3B8", size=14),
            border_color="#334155" if is_dark else "#CBD5E1",
            focused_border_color="#3B82F6",
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
            on_submit=self._on_login,
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
            self.email_field.error_text = None if re.match(pattern, email) else self.translate("validation_invalid_email")
        else:
            self.email_field.error_text = None
        self.page.update()

    def _validate_form(self) -> bool:
        valid = True
        if not self.email_field.value.strip():
            self.email_field.error_text = self.translate("validation_email_required")
            valid = False
        if not self.pw_field.value:
            self.pw_field.error_text = self.translate("validation_password_required")
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
            NavigationController.set_user_and_navigate(current_user_data, "Inicio")
        except Exception as err:
            self._show_error(f"Error de conexión: {str(err)}")
        finally:
            self.loading_indicator.visible = False
            self.page.update()

    def _build_left_panel(self, is_dark: bool) -> ft.Container:
        panel_width = int((self.page.width or 1600) * 0.5)
        panel_height = int(self.page.height or 900)
        panel_image_height = int(panel_width * 1105 / 768)
        image_src = self._get_left_panel_image_src()

        return ft.Container(
            width=panel_width,
            height=panel_height,
            bgcolor="#ECEDED" if not is_dark else "#111827",
            expand=True,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.alignment.top_center,
            content=ft.Stack(
                width=panel_width,
                height=panel_height,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                controls=[
                    ft.Image(
                        src=image_src,
                        width=panel_width,
                        height=panel_image_height,
                        fit=ft.ImageFit.FILL,
                        top=0,
                        left=0,
                    )
                ],
            ),
        )

    def _get_left_panel_image_src(self) -> str:
        from services.navigation_service import NavigationController

        lang = (
            NavigationController.cache.get("language")
            or (self.page.client_storage.get("language") if self.page else None)
            or self.language
            or "es"
        )
        lang = "zh-TW" if lang in ("zh-TW", "zh_Hant", "zh-Hant") else lang.split("-")[0]
        filename_by_lang = {
            "es": "login_panel_es.png",
            "en": "login_panel_en.png",
            "it": "login_panel_it.png",
            "pt": "login_panel_pt.png",
            "de": "login_panel_de.png",
            "zh-TW": "login_panel_zh-TW.png",
            "zh": "login_panel_zh.png",
        }
        filename = filename_by_lang.get(lang, filename_by_lang["es"])
        image_path = os.path.join(self._asset_root, "login_panels", filename)
        if os.path.isfile(image_path):
            return image_path
        return os.path.join(self._asset_root, "login_panels", "login_panel_es.png")

    def _continue_with_google(self, e=None):
        """Abre directamente la página oficial de Google OAuth 2.0 en el navegador web (Chrome/Edge)."""
        from services.google_service import google_service
        google_service.launch_real_google_oauth(self.page)

    def _social_button(self, icon: str, color: str, label=""):
        on_clk = self._continue_with_google if label == "Google" else lambda e: print(f"Social login: {label or icon}")
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
        self.remember_me.label = self.translate("auth_remember")

        form_column = ft.Column([
            ft.Text(self.translate("auth_login_title"), size=34, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=10),
            ft.Text(self.translate("auth_login_subtitle"), size=16, color=subtitle_color),
            ft.Container(height=34),
            self.error_banner,
            ft.Text(self.translate("auth_email"), size=14, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=10),
            self.email_field,
            ft.Container(height=20),
            ft.Text(self.translate("auth_password"), size=14, weight=ft.FontWeight.BOLD, color=title_color),
            ft.Container(height=10),
            self.pw_field,
            ft.Container(height=20),
            ft.Row([
                self.remember_me,
                ft.Container(expand=True),
                ft.TextButton(
                    self.translate("auth_forgot"),
                    on_click=lambda e: NavigationController.update_view("Recuperar"),
                    style=ft.ButtonStyle(color=link_color),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=26),
            ft.ElevatedButton(
                self.translate("auth_login_button"),
                on_click=self._on_login,
                bgcolor="#07547B",
                color=ft.Colors.WHITE,
                height=56,
                expand=True,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16), text_style=ft.TextStyle(size=16)),
            ),
            ft.Container(height=28),
            ft.Row([
                ft.Container(expand=True, height=1, bgcolor="#E2E8F0"),
                ft.Container(padding=ft.padding.symmetric(horizontal=12), content=ft.Text(self.translate("auth_continue_with"), size=12, color=subtitle_color)),
                ft.Container(expand=True, height=1, bgcolor="#E2E8F0"),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=24),
            ft.Row([
                self._social_button("G", "#EA4335", "Google"),
                ft.Container(width=16),
                self._social_button("f", "#1877F2", "Facebook"),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=28),
            ft.Row([
                ft.Text(self.translate("auth_no_account"), size=14, color=subtitle_color),
                ft.Container(width=8),
                ft.TextButton(
                    self.translate("auth_register_here"),
                    on_click=lambda e: NavigationController.update_view("Registro"),
                    style=ft.ButtonStyle(color="#FF4D6E", text_style=ft.TextStyle(size=14)),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=18),
            ft.Row([self.loading_indicator], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

        login_card = ft.Container(
            width=520,
            padding=ft.padding.all(40),
            bgcolor=right_bg,
            border_radius=24,
            shadow=ft.BoxShadow(blur_radius=24, color=ft.Colors.BLACK12, offset=ft.Offset(0, 12)),
            content=form_column,
        )

        right_panel = ft.Container(
            expand=True,
            bgcolor=page_bg,
            padding=ft.padding.symmetric(horizontal=40, vertical=40),
            alignment=ft.alignment.top_center,
            content=login_card,
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
