import flet as ft
import os
import threading
import time
from utils.env_loader import load_env
from services.navigation_service import NavigationController


def main(page: ft.Page):
    # 1. Cargar variables de entorno inmediatamente
    load_env()

    # 2. Configuración de ventana y tema (Simulación de teléfono móvil Samsung A03)
    page.title = "PointList"
    page.window.icon = "assets/logo.png"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0

    page.window.width = 390
    page.window.height = 810
    page.window.min_width = 320
    page.window.min_height = 600
    page.window.maximized = False
    page.window.resizable = True

    # 3. Contenedor principal de la UI protegido con SafeArea para evitar solapamientos con la barra de estado/notch
    main_container = ft.Container(expand=True)
    page.add(ft.SafeArea(main_container, expand=True))
    NavigationController.initialize(page, main_container)

    # 4. Pantalla de Carga Inicial elegante con ProgressRing
    loading_splash = ft.Container(
        expand=True,
        alignment=ft.alignment.center,
        bgcolor="#0F172A" if page.theme_mode == ft.ThemeMode.DARK else "#F8FAFC",
        content=ft.Column([
            ft.Image(src="assets/logo.png", width=64, height=64, fit=ft.ImageFit.CONTAIN),
            ft.Container(height=16),
            ft.ProgressRing(color="#10B981", stroke_width=4, width=36, height=36),
            ft.Container(height=16),
            ft.Text(
                "Espera un momento mientras se carga la aplicación...",
                size=13,
                weight="bold",
                color="#0F172A" if page.theme_mode == ft.ThemeMode.LIGHT else "#F8FAFC",
                text_align=ft.TextAlign.CENTER,
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)
    )
    main_container.content = loading_splash
    try: page.update()
    except: pass

    # 5. Aplicar preferencias y precargar datos para máxima velocidad 0ms
    try:
        NavigationController.apply_user_preferences()
        NavigationController.preload_pages(background=False)

        current_user = NavigationController.get_current_user()
        if current_user and current_user.get("id"):
            NavigationController.preload_data(background=False)
            NavigationController.update_view("Inicio")
        else:
            NavigationController.update_view("Login")
    except Exception as e:
        try:
            NavigationController.update_view("Login")
        except:
            pass



if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
