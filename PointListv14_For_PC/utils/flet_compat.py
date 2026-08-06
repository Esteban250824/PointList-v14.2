"""
utils/flet_compat.py
PointList v0.14.25experiment
Capa de compatibilidad universal para Python 3.13-3.14+ y Flet 0.28.3-0.82.0+.
Normaliza componentes, constantes y comportamientos que han cambiado entre versiones.
"""

import flet as ft
import sys
import importlib.metadata
from packaging import version

# Obtener la versión actual de Flet de forma robusta
try:
    # Intentamos obtenerla desde los metadatos del paquete instalado
    FLET_VERSION_STR = importlib.metadata.version("flet")
except importlib.metadata.PackageNotFoundError:
    # Si no se encuentra, intentamos desde el atributo __version__ (si existe)
    FLET_VERSION_STR = getattr(ft, "__version__", "0.28.3")

FLET_VERSION = version.parse(FLET_VERSION_STR)
PY_VERSION = sys.version_info


def _ensure_icon_aliases():
    """Añade aliases para iconos que cambiaron de nombre entre versiones de Flet."""
    alias_map = {
        "CLIPBOARD_OUTLINED": ("CLIPBOARD", "CONTENT_PASTE", "PASTE"),
        "CHAT_BUBBLE_OUTLINE": ("CHAT", "CHAT_BUBBLE", "CHAT_OUTLINED"),
        "CHAT_OUTLINED": ("CHAT", "CHAT_BUBBLE"),
        "DELETE_OUTLINE": ("DELETE", "DELETE_FOREVER"),
        "THUMB_UP_OUTLINE": ("THUMB_UP", "THUMB_UP_ALT"),
        "THUMB_DOWN_OUTLINE": ("THUMB_DOWN", "THUMB_DOWN_ALT"),
        "ADD_CIRCLE_OUTLINE": ("ADD_CIRCLE", "ADD"),
        "SETTINGS_OUTLINED": ("SETTINGS",),
        "ASSIGNMENT_OUTLINED": ("ASSIGNMENT",),
        "SCHOOL_OUTLINED": ("SCHOOL",),
        "LIGHTBULB_OUTLINE": ("LIGHTBULB",),
        "HELP_OUTLINE": ("HELP",),
        "SHIELD_OUTLINED": ("SHIELD", "SECURITY"),
        "SEND_ROUNDED": ("SEND",),
        "LOGOUT_ROUNDED": ("LOGOUT", "EXIT_TO_APP"),
        "EMAIL_OUTLINED": ("EMAIL",),
        "MENU_BOOK_OUTLINED": ("MENU_BOOK",),
        "ACCOUNT_TREE_OUTLINED": ("ACCOUNT_TREE",),
        "PSYCHOLOGY_OUTLINED": ("PSYCHOLOGY",),
        "TIMER_OUTLINED": ("TIMER",),
        "ARROW_BACK": ("ARROW_BACK_IOS",),
    }

    for icon_name, candidates in alias_map.items():
        if hasattr(ft.Icons, icon_name):
            continue
        for candidate in candidates:
            if hasattr(ft.Icons, candidate):
                setattr(ft.Icons, icon_name, getattr(ft.Icons, candidate))
                break
        else:
            fallback = getattr(ft.Icons, "HELP_OUTLINE", None)
            if fallback is not None:
                setattr(ft.Icons, icon_name, fallback)


_ensure_icon_aliases()


def get_scroll_mode(mode_name: str):
    """
    Devuelve el modo de scroll correcto según la versión de Flet.
    Normaliza entre ScrollMode.AUTO, ScrollMode.HORIZONTAL, etc.
    """
    try:
        mode_name = mode_name.upper()
        if mode_name == "HORIZONTAL":
            if hasattr(ft.ScrollMode, "HORIZONTAL"):
                return ft.ScrollMode.HORIZONTAL
            return ft.ScrollMode.AUTO
        
        if hasattr(ft.ScrollMode, mode_name):
            return getattr(ft.ScrollMode, mode_name)
        
        return ft.ScrollMode.AUTO
    except:
        return ft.ScrollMode.AUTO

def create_chip(label_text: str, on_click=None, selected: bool = False, is_filter: bool = False):
    """
    Crea un Chip compatible con todas las versiones de Flet.
    Normaliza entre Chip, FilterChip y ActionChip.
    """
    # En versiones antiguas (< 0.30.0), usamos el Chip básico
    if FLET_VERSION < version.parse("0.30.0"):
        return ft.Chip(
            label=ft.Text(label_text, size=12),
            on_click=on_click,
            bgcolor=ft.Colors.INDIGO_100 if selected else ft.Colors.GREY_100,
        )
    
    # En versiones nuevas, intentamos usar los componentes específicos con manejo de errores
    try:
        if is_filter and hasattr(ft, "FilterChip"):
            return ft.FilterChip(
                label=ft.Text(label_text, size=12),
                selected=selected,
                on_select=on_click,
                selected_color=ft.Colors.INDIGO_100,
            )
        elif hasattr(ft, "ActionChip"):
            return ft.ActionChip(
                label=ft.Text(label_text, size=12),
                on_click=on_click,
                bgcolor=ft.Colors.INDIGO_50 if not selected else ft.Colors.INDIGO_100,
            )
    except (AttributeError, TypeError):
        pass
        
    # Fallback universal robusto
    return ft.Chip(
        label=ft.Text(label_text, size=12),
        on_click=on_click,
        bgcolor=ft.Colors.INDIGO_100 if selected else ft.Colors.GREY_100,
    )

def run_async_safe(page: ft.Page, func, *args, **kwargs):
    """
    Ejecuta una función de forma segura en el hilo principal de Flet.
    Compatible con cambios en el manejo de hilos de Python 3.14+.
    """
    import traceback
    import asyncio
    try:
        # En versiones recientes de Flet, run_task es preferible pero requiere corrutinas
        if hasattr(page, "run_task"):
            if asyncio.iscoroutinefunction(func):
                page.run_task(func, *args, **kwargs)
            else:
                # Si es una función normal, la envolvemos para que sea asíncrona
                async def wrapper():
                    func(*args, **kwargs)
                page.run_task(wrapper)
        else:
            # Fallback para versiones antiguas (Flet < 0.30)
            func(*args, **kwargs)
            page.update()
    except Exception as e:
        print(f"[Compat] Error en ejecución asíncrona: {e}")
        traceback.print_exc()

def get_theme_mode(mode_name: str):
    """Normaliza ThemeMode entre versiones."""
    try:
        mode_name = mode_name.upper()
        if hasattr(ft.ThemeMode, mode_name):
            return getattr(ft.ThemeMode, mode_name)
        return ft.ThemeMode.SYSTEM
    except:
        return ft.ThemeMode.SYSTEM

def get_icon(icon_name: str):
    """Asegura que el icono exista en la versión actual de Flet."""
    if hasattr(ft.Icons, icon_name):
        return getattr(ft.Icons, icon_name)
    # Fallback si el icono fue renombrado o eliminado
    return ft.Icons.HELP_OUTLINE
