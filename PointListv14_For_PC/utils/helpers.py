"""
utils/helpers.py
PointList v0.14.25experiment
Funciones de utilidad compartidas en toda la aplicación.
"""

import os
import re
import hashlib
import binascii
import threading
from datetime import date, datetime, timedelta

def get_logo_path() -> str:
    """Busca y devuelve la ruta absoluta o relativa existente del archivo logo.png."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base_dir, "assets", "logo.png"),
        os.path.join(os.getcwd(), "assets", "logo.png"),
        os.path.join(os.getcwd(), "PointListv14_For_PC", "assets", "logo.png"),
        os.path.join(base_dir, "assets", "figma_assets", "logo.png"),
        os.path.join("assets", "logo.png"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "assets/logo.png"

def get_logo_control(width: int = 28, height: int = 28):
    """Crea un control ft.Image con la imagen oficial del logo PointList."""
    import flet as ft
    return ft.Image(
        src=get_logo_path(),
        width=width,
        height=height,
        fit=ft.ImageFit.CONTAIN
    )

def send_windows_toast(title: str, message: str):
    """Envía una notificación emergente nativa del sistema operativo Windows 10/11 en segundo plano."""
    def _toast():
        try:
            import subprocess
            t_clean = str(title).replace('"', "'").replace("`", "").replace("'", "")
            m_clean = str(message).replace('"', "'").replace("`", "").replace("'", "")
            
            ps_cmd = (
                '[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; '
                '[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null; '
                '$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; '
                f'$xml.LoadXml("<toast><visual><binding template=\'ToastGeneric\'><text>{t_clean}</text><text>{m_clean}</text></binding></visual></toast>"); '
                '$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); '
                '[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("PointList").Show($toast)'
            )
            
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            subprocess.Popen(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                creationflags=creation_flags
            )
        except Exception:
            pass

    threading.Thread(target=_toast, daemon=True).start()

# ─────────────────────────────────────────────
# CONSTANTES GLOBALES DE TEMA / COLORES
# ─────────────────────────────────────────────
PRIMARY_COLOR    = "#4F46E5"   # Indigo
SECONDARY_COLOR  = "#10B981"   # Emerald
BACKGROUND_COLOR = "#F9FAFB"   # Light gray
CARD_COLOR       = "#FFFFFF"   # White
TEXT_COLOR       = "#1F2937"   # Gray-900
ACCENT_COLOR     = "#EF4444"   # Red
WARNING_COLOR    = "#FBBF24"   # Amber
NAVBAR_COLOR     = "#FFFFFF"

# Paleta de colores del ChatBot
COLORES_POINTLIST = {
    "claro": {
        "fondo_principal":  "#F3F4F6",
        "fondo_tarjeta":    "#FFFFFF",
        "fondo_encabezado": "#EFF6FF",
        "fondo_input":      "#FFFFFF",
        "fondo_usuario":    "#DBEAFE",
        "fondo_bot":        "#F0F8FF",
        "borde_usuario":    "#3B82F6",
        "borde_bot":        "#BFDBFE",
        "texto_principal":  "#1F2937",
        "texto_secundario": "#6B7280",
        "texto_usuario":    "#1E3A8A",
        "texto_bot":        "#1E40AF",
        "sombra":           "#D1D5DB",
        "fondo_boton":      "#3B82F6",
        "texto_boton":      "#FFFFFF",
    },
    "oscuro": {
        "fondo_principal":  "#121212",
        "fondo_tarjeta":    "#1E1E1E",
        "fondo_encabezado": "#0D1B2A",
        "fondo_input":      "#2D3748",
        "fondo_usuario":    "#1E3A8A",
        "fondo_bot":        "#1E2A3A",
        "borde_usuario":    "#3B82F6",
        "borde_bot":        "#2C5282",
        "texto_principal":  "#E5E7EB",
        "texto_secundario": "#A0AEC0",
        "texto_usuario":    "#93C5FD",
        "texto_bot":        "#BFDBFE",
        "sombra":           "#000000",
        "fondo_boton":      "#2563EB",
        "texto_boton":      "#E5E7EB",
    },
}

# ─────────────────────────────────────────────
# SEGURIDAD: HASH DE CONTRASEÑAS
# ─────────────────────────────────────────────
PASSWORD_HASH_ITERATIONS = 100_000


def hash_password(password: str, salt: bytes = None) -> tuple[str, str]:
    """Genera un hash seguro de contraseña con sal (PBKDF2-HMAC-SHA256).

    Returns:
        (hash_hex, salt_hex)
    """
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return binascii.hexlify(key).decode(), binascii.hexlify(salt).decode()


def verify_password(stored_hash: str, provided_password: str, salt: str) -> bool:
    """Verifica una contraseña contra su hash almacenado."""
    salt_bytes = binascii.unhexlify(salt)
    new_hash, _ = hash_password(provided_password, salt_bytes)
    return new_hash == stored_hash


# ─────────────────────────────────────────────
# VALIDACIONES
# ─────────────────────────────────────────────
def validate_email(email: str) -> bool:
    """Valida el formato de una dirección de correo electrónico."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Valida si una cadena es una URL válida."""
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


# ─────────────────────────────────────────────
# UTILIDADES DE FECHA
# ─────────────────────────────────────────────
MONTH_NAMES_ES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

MONTH_NAMES_EN = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def get_month_name(index: int, lang: str = "es") -> str:
    """Devuelve el nombre del mes dado su índice (0-11)."""
    names = MONTH_NAMES_ES if lang == "es" else MONTH_NAMES_EN
    return names[index % 12]


# ─────────────────────────────────────────────
# TEMPORIZADOR REUTILIZABLE
# ─────────────────────────────────────────────
def delayed_call(seconds: float, func, *args, **kwargs) -> threading.Timer:
    """Ejecuta *func* después de *seconds* segundos en un hilo separado."""
    t = threading.Timer(seconds, func, args=args, kwargs=kwargs)
    t.daemon = True
    t.start()
    return t


# ─────────────────────────────────────────────
# CLASE AppTheme (colores de calificaciones)
# ─────────────────────────────────────────────
class AppTheme:
    @staticmethod
    def grade_color(grade: float) -> str:
        # Rojo: 1.0 hasta 2.9
        # Morado: 3.0 hasta 4.0
        # Verde: 4.1 hasta 5.0
        if grade >= 4.1:
            return "#10B981"  # Verde (Emerald)
        elif grade >= 3.0:
            return "#8B5CF6"  # Morado (Violet)
        else:
            return "#EF4444"  # Rojo (Red)
