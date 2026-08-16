import flet as ft
import os
import threading
import time
from utils.env_loader import load_env
from services.navigation_service import NavigationController

def main(page: ft.Page):
    # Configuración básica de la página
    page.title = "PointList"
    try:
        icon_path = os.path.join("assets", "icon.ico")
        if os.path.exists(icon_path):
            page.window.icon = icon_path
    except: pass

    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    page.window.maximized = True
    
    # Contenedor principal de la UI
    main_container = ft.Container(expand=True)
    page.add(main_container)
    NavigationController.initialize(page, main_container)

    # Logo centrado para la pantalla de carga
    from utils.helpers import get_logo_control
    brand_logo = get_logo_control(width=52, height=52)

    loading_screen = ft.Container(
        content=ft.Column([
            brand_logo,
            ft.Container(height=14),
            ft.ProgressRing(width=32, height=32, stroke_width=3, color="#4F46E5"),
            ft.Container(height=16),
            ft.Text("Cargando PointList...", size=16, weight="bold", color="#0F172A"),
            ft.Container(height=6),
            ft.Text("Espera un momento mientras se prepara tu espacio de estudio.", size=12, color="#64748B", text_align=ft.TextAlign.CENTER),
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        expand=True,
        alignment=ft.alignment.center,
        padding=ft.padding.all(24),
    )
    main_container.content = loading_screen
    page.update()

    def launch_app():
        time.sleep(0.5)
        try:
            load_env()
            NavigationController.apply_user_preferences()
        except: pass

        try:
            current_user = NavigationController.get_current_user()
            if current_user and current_user.get("id"):
                NavigationController.update_view("Inicio")
            else:
                NavigationController.update_view("Login")
        except:
            NavigationController.update_view("Login")

        NavigationController.preload_pages(background=True)
        NavigationController.preload_data(background=True)

    threading.Thread(target=launch_app, daemon=True).start()

import socket

def find_free_port(start_port=8550):
    """Busca automáticamente el primer puerto TCP libre en todas las interfaces a partir de start_port."""
    for p in range(start_port, start_port + 100):
        is_free = True
        for host in ["0.0.0.0", "127.0.0.1"]:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind((host, p))
            except Exception:
                is_free = False
                break
        if is_free:
            return p
    import random
    return random.randint(8555, 8999)

if __name__ == "__main__":
    try:
        load_env()
    except: pass
    
    is_web = os.getenv("POINTLIST_WEB", "false").lower() in ("true", "1", "yes")
    port_str = os.getenv("PORT", "8550")
    try: target_port = int(port_str)
    except: target_port = 8550

    active_port = find_free_port(target_port)

    print("\n" + "═" * 62)
    print(" 🚀 PointList iniciado con éxito")
    print(" 💻 Modo Escritorio: Activo")
    print(f" 🌐 Servidor Web disponible en: http://localhost:{active_port}")
    print("═" * 62 + "\n")

    if is_web:
        try:
            ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=active_port)
        except Exception:
            ft.app(target=main, view=ft.AppView.WEB_BROWSER)
    else:
        try:
            ft.app(target=main, view=ft.AppView.FLET_APP_WEB, port=active_port)
        except Exception:
            ft.app(target=main)
