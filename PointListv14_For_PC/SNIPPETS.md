# 💻 Snippets y Patrones Comunes

Colección de código reutilizable y patrones comunes en PointList.

---

## 🔐 Autenticación

### Login Básico
```python
from services.database_service import DatabaseService

def login_user(email: str, password: str) -> dict:
    """Autenticar usuario"""
    db = DatabaseService()
    user = db.autenticar_usuario(email, password)
    
    if user:
        # Guardar en caché
        from services.navigation_service import NavigationController
        NavigationController._current_user = user
        return user
    else:
        raise Exception("Email o contraseña incorrectos")
```

### Registrar Usuario
```python
def register_user(data: dict) -> dict:
    """Crear nuevo usuario"""
    db = DatabaseService()
    
    # Validar email único
    if db.email_exists(data["email"]):
        raise Exception("Email ya registrado")
    
    # Crear usuario
    user_id = db.registrar_usuario(data)
    return {"id": user_id, "email": data["email"]}
```

---

## 🌍 Internacionalización (i18n)

### Usar en Página
```python
from utils.i18n import translate

class MiPagina(BasePage):
    def build(self):
        return ft.Column([
            ft.Text(self.translate("nav_home")),
            ft.Text(self.translate("button_save")),
        ])
```

### Traducir Directamente
```python
from utils.i18n import translate

# Español (por defecto)
texto = translate("nav_home", "es")  # "Inicio"

# Inglés
texto = translate("nav_home", "en")  # "Home"

# Portugués
texto = translate("nav_home", "pt")  # "Início"
```

### Agregar Nuevas Traducciones
```python
# En utils/i18n.py, agregar a TRANSLATIONS:

TRANSLATIONS = {
    "es": {
        "mi_clave_nueva": "Mi texto en español",
    },
    "en": {
        "mi_clave_nueva": "My text in English",
    },
    "pt": {
        "mi_clave_nueva": "Meu texto em português",
    }
}
```

---

## 🎨 Crear Nuevas Páginas

### Template de Página
```python
import flet as ft
from views.pages.base_page import BasePage

class MiNuevaPagina(BasePage):
    """Descripción de mi página"""
    
    def __init__(self, page: ft.Page, nav_controller):
        super().__init__(page, nav_controller)
        # Inicialización específica
    
    def _build_header(self):
        """Construir encabezado"""
        return ft.Container(
            content=ft.Text(
                self.translate("mi_titulo"),
                size=24,
                weight="bold",
                color=self.theme_colors["text"]
            ),
            padding=20
        )
    
    def _build_content(self):
        """Construir contenido principal"""
        return ft.Container(
            content=ft.Text("Mi contenido aquí"),
            expand=True,
            padding=20
        )
    
    def build(self):
        """Construir página completa"""
        return ft.Column([
            self._build_header(),
            self._build_content(),
        ], expand=True)
```

### Registrar Página en NavigationController
```python
# En services/navigation_service.py, en initialize():

from views.pages.mi_nueva_pagina import MiNuevaPagina

pages = {
    "MiNuevaPagina": MiNuevaPagina,
    # ... otras páginas
}
```

---

## 💾 Base de Datos

### Query Segura
```python
from services.database_service import DatabaseService

db = DatabaseService()

# Query segura (usa prepared statements)
query = "SELECT * FROM usuarios WHERE id = %s"
resultado = db.execute_query(query, (user_id,))
```

### Obtener Datos
```python
# Un usuario
user = db.get_usuario(user_id)  # dict

# Múltiples usuarios
usuarios = db.get_usuarios()  # list[dict]

# Filtrados
notas = db.get_notas(user_id)  # list[dict]
```

### Guardar Datos
```python
# Crear
user_id = db.registrar_usuario({
    "nombre_usuario": "juan",
    "email": "juan@example.com",
    "password_hash": hash_pwd,
    "salt": salt_value
})

# Actualizar
db.update_usuario(user_id, {
    "bio": "Mi biografía",
    "foto_url": "https://..."
})

# Eliminar
db.delete_usuario(user_id)
```

### Transacciones
```python
db.connection.begin()
try:
    db.execute_query("INSERT INTO ...", (...))
    db.execute_query("UPDATE ...", (...))
    db.connection.commit()
except Exception as e:
    db.connection.rollback()
    raise e
```

---

## 🤖 ChatBot / OpenAI

### Obtener Respuesta IA
```python
from services.chatbot_service import ChatbotService

chatbot = ChatbotService()

# Respuesta simple
respuesta = chatbot.get_response("¿Cómo hago un ensayo?")
# → "Para hacer un ensayo debes..."

# Con contexto
respuesta = chatbot.get_response(
    "¿Cómo hago un ensayo?",
    context="Materia: Literatura"
)
```

### Guardar Conversación
```python
chatbot = ChatbotService()

conv_id = chatbot.save_conversation(
    user_id=123,
    data={
        "titulo": "Ayuda con ensayo",
        "mensajes": [
            {"role": "user", "content": "¿Cómo hago un ensayo?"},
            {"role": "assistant", "content": "Para hacer un ensayo..."}
        ]
    }
)
```

### Obtener Historial
```python
chatbot = ChatbotService()

historial = chatbot.get_conversation_history(conv_id=456)
# → [{"role": "user", "content": "..."}, ...]
```

---

## 🧭 Navegación

### Cambiar Vista
```python
from services.navigation_service import NavigationController

# Ir a otra página
NavigationController.update_view("Inicio")
NavigationController.update_view("Perfil")
NavigationController.update_view("Notas")
```

### Obtener Usuario Actual
```python
user = NavigationController.get_current_user()
# → {"id": 123, "email": "user@example.com", "nombre_usuario": "juan", ...}

# Verificar si está logueado
if user and user.get("id"):
    print("Usuario logueado")
else:
    print("No logueado")
```

### Guardar Preferencias
```python
# Cambiar idioma
NavigationController.set_language("en")  # English

# Cambiar tema
page.theme_mode = ft.ThemeMode.DARK

# Guardar en preferencias
NavigationController.save_user_preferences({
    "language": "en",
    "theme": "dark",
    "notifications": True
})
```

---

## 🎨 Componentes UI Comunes

### Card / Tarjeta
```python
def create_card(title: str, content: str, on_click=None):
    """Crear tarjeta reutilizable"""
    return ft.Container(
        content=ft.Column([
            ft.Text(title, size=18, weight="bold"),
            ft.Text(content, size=14),
        ], spacing=10),
        bgcolor="#FFFFFF",
        padding=15,
        border_radius=10,
        on_click=on_click,
        ink=True
    )

# Uso
tarjeta = create_card(
    title="Mi Tarjeta",
    content="Contenido aquí",
    on_click=lambda e: print("Tarjeta clickeada")
)
```

### Loading Indicator
```python
def show_loading():
    """Mostrar indicador de carga"""
    return ft.Container(
        content=ft.Column([
            ft.ProgressRing(
                width=50,
                height=50,
                stroke_width=3,
                color="#3EB534"
            ),
            ft.Text("Cargando...", size=14),
        ], alignment=ft.MainAxisAlignment.CENTER,
           horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        expand=True,
        alignment=ft.alignment.center
    )
```

### Alert Dialog
```python
def show_alert(page, title: str, message: str):
    """Mostrar alerta"""
    def close_alert(e):
        dlg.open = False
        page.update()
    
    dlg = ft.AlertDialog(
        title=ft.Text(title),
        content=ft.Text(message),
        actions=[
            ft.TextButton("OK", on_click=close_alert)
        ]
    )
    page.dialog = dlg
    dlg.open = True
    page.update()

# Uso
show_alert(page, "Éxito", "Usuario registrado correctamente")
```

### Formulario
```python
def create_form_field(label: str, hint: str = ""):
    """Crear campo de formulario reutilizable"""
    return ft.Column([
        ft.Text(label, size=12, weight="bold"),
        ft.TextField(
            hint_text=hint,
            border_radius=8,
            border="underline",
            bgcolor="#F5F5F5"
        )
    ], spacing=5)

# Uso
campo_email = create_form_field(
    label="Email",
    hint="user@example.com"
)
```

---

## 🔐 Seguridad

### Hash de Contraseña
```python
import hashlib
import os

def hash_password(password: str) -> tuple:
    """
    Hash de contraseña segura con sal
    
    Returns:
        (password_hash, salt)
    """
    salt = os.urandom(32).hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000
    ).hex()
    return pwd_hash, salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verificar contraseña"""
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode(),
        salt.encode(),
        100000
    ).hex()
    return pwd_hash == stored_hash
```

### Validar Email
```python
import re

def validate_email(email: str) -> bool:
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Uso
if validate_email("user@example.com"):
    print("Email válido")
```

### Validar Contraseña
```python
def validate_password_strength(password: str) -> dict:
    """Validar fortaleza de contraseña"""
    result = {
        "valid": True,
        "errors": []
    }
    
    if len(password) < 8:
        result["errors"].append("Al menos 8 caracteres")
    if not re.search(r'[A-Z]', password):
        result["errors"].append("Al menos una mayúscula")
    if not re.search(r'[a-z]', password):
        result["errors"].append("Al menos una minúscula")
    if not re.search(r'[0-9]', password):
        result["errors"].append("Al menos un número")
    
    result["valid"] = len(result["errors"]) == 0
    return result

# Uso
validacion = validate_password_strength("MiPassword123")
if validacion["valid"]:
    print("Contraseña fuerte")
else:
    print("Errores:", validacion["errors"])
```

---

## 📊 Manejo de Datos

### Formatear Moneda
```python
def format_currency(amount: float, currency: str = "USD") -> str:
    """Formatear como moneda"""
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "COP":
        return f"${amount:,.0f}"
    else:
        return f"{amount:,.2f}"

# Uso
print(format_currency(1234.56, "USD"))  # $1,234.56
```

### Formatear Fecha
```python
from datetime import datetime

def format_date(date: datetime, format: str = "%d/%m/%Y") -> str:
    """Formatear fecha"""
    return date.strftime(format)

# Uso
hoy = datetime.now()
print(format_date(hoy))  # 03/07/2026
```

### Paginar Lista
```python
def paginate_list(items: list, page: int = 1, per_page: int = 10) -> dict:
    """Paginar una lista"""
    total = len(items)
    total_pages = (total + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages
    }

# Uso
usuarios = [f"user_{i}" for i in range(100)]
resultado = paginate_list(usuarios, page=1, per_page=10)
# → {"items": ["user_0", ...], "page": 1, "total": 100, ...}
```

---

## 🎯 Manejo de Errores

### Try-Except Personalizado
```python
def safe_db_query(query: str, params: tuple = ()):
    """Ejecutar query con manejo de errores"""
    try:
        db = DatabaseService()
        result = db.execute_query(query, params)
        return {"success": True, "data": result}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
```

### Logging
```python
import logging

def setup_logging():
    """Configurar logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

# Uso
logger = logging.getLogger(__name__)
logger.info("Aplicación iniciada")
logger.error("Error en login:", exc_info=True)
```

---

## 📝 Tips y Mejores Prácticas

### 1. Siempre Validar Input
```python
# ❌ Mal
def login(email, password):
    return db.autenticar_usuario(email, password)

# ✅ Bien
def login(email: str, password: str) -> dict:
    if not email or not password:
        raise ValueError("Email y contraseña requeridos")
    if not validate_email(email):
        raise ValueError("Email inválido")
    return db.autenticar_usuario(email, password)
```

### 2. Usar Type Hints
```python
# ✅ Bien
def get_user(user_id: int) -> dict | None:
    """Obtener usuario por ID"""
    pass

# Con múltiples tipos
def process_data(data: str | list | dict) -> bool:
    pass
```

### 3. Documentar Funciones
```python
def calculate_grade_average(grades: list[float]) -> float:
    """
    Calcula el promedio de calificaciones.
    
    Args:
        grades: Lista de calificaciones numéricas
        
    Returns:
        El promedio como float
        
    Raises:
        ValueError: Si la lista está vacía
        TypeError: Si los elementos no son números
    """
    if not grades:
        raise ValueError("Lista de calificaciones no puede estar vacía")
    return sum(grades) / len(grades)
```

### 4. Usar Context Managers
```python
# ✅ Para archivos
with open('archivo.txt', 'r') as f:
    contenido = f.read()

# ✅ Para base de datos (si está implementado)
# with db.connection:
#     result = db.execute_query(...)
```

### 5. Evitar Hardcoding
```python
# ❌ Mal
API_KEY = "sk-1234567890abcdef"

# ✅ Bien
from utils.env_loader import load_env
import os

load_env()
API_KEY = os.getenv("OPENAI_API_KEY")
```

---

## 🔗 Referencias Rápidas

- **Flet Docs**: https://flet.dev
- **Python Docs**: https://docs.python.org/3
- **PostgreSQL**: https://www.postgresql.org/docs/
- **OpenAI API**: https://platform.openai.com/docs
- **Git Guide**: https://git-scm.com/book

---

**Última actualización**: Julio 2026
**Versión**: v1.0
