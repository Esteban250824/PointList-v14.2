# 📂 Estructura del Proyecto - Guía Detallada

## 📋 Tabla de Contenidos
1. [Estructura General](#estructura-general)
2. [Módulos Core](#módulos-core)
3. [Vistas y Páginas](#vistas-y-páginas)
4. [Servicios](#servicios)
5. [Utilidades](#utilidades)
6. [Modelos](#modelos)
7. [Assets](#assets)
8. [Flujo de Datos](#flujo-de-datos)

---

## 📊 Estructura General

```
pointlist_v13/
│
├── 📄 Archivos de Configuración
│   ├── main.py                    # Punto de entrada principal
│   ├── requirements.txt           # Dependencias del proyecto
│   ├── .env.example              # Plantilla de variables de entorno
│   ├── .gitignore                # Archivos a ignorar en Git
│   └── .env                      # Variables de entorno (NO en repositorio)
│
├── 📚 Documentación
│   ├── README.md                 # Documentación principal
│   ├── QUICKSTART.md             # Guía de inicio rápido
│   ├── CONTRIBUTING.md           # Guía para contribuidores
│   ├── PROJECT_STRUCTURE.md      # Este archivo
│   ├── EXECUTIVE_SUMMARY.md      # Resumen ejecutivo
│   ├── GITHUB_DESCRIPTION.md     # Descripción para GitHub
│   ├── CHANGELOG_v11.md          # Historial v11
│   ├── CHANGELOG_v12.md          # Historial v12
│   └── CHANGELOG_v13.md          # Historial v13 (actual)
│
├── 🎨 Assets
│   └── figma_assets/
│       ├── logo.png              # Logo principal
│       ├── logo_white.png        # Logo versión blanca
│       ├── login_left_panel.png  # Panel izquierdo login
│       └── [...otros assets]
│
├── 🧠 Models (Modelos de Datos)
│   ├── __init__.py
│   └── schema.py                 # Esquema de base de datos
│
├── 🔧 Services (Servicios/Lógica Negocio)
│   ├── navigation_service.py     # Controlador de navegación
│   ├── database_service.py       # Operaciones de base de datos
│   └── chatbot_service.py        # Integración OpenAI
│
├── 🛠️ Utils (Utilidades)
│   ├── __init__.py
│   ├── env_loader.py             # Cargador de .env
│   ├── flet_compat.py            # Compatibilidad Flet
│   ├── helpers.py                # Funciones auxiliares
│   └── i18n.py                   # Internacionalización
│
└── 👁️ Views (Interfaz de Usuario)
    └── pages/
        ├── base_page.py          # Clase base para todas las páginas
        ├── login_page.py         # Autenticación
        ├── registration_page.py  # Registro
        ├── recover_page.py       # Recuperación de contraseña
        ├── home_page.py          # Página de inicio
        ├── profile_page.py       # Perfil de usuario
        ├── notes_page.py         # Dashboard de notas
        ├── calendar_page.py      # Calendario académico
        ├── techniques_page.py    # Técnicas de estudio
        ├── messaging_page.py     # Chat colaborativo
        └── chatbot_page.py       # Asistente IA
```

---

## 🧠 Módulos Core

### 1. **main.py** - Punto de Entrada
```python
# Flujo:
# 1. Configurar página base (title, theme, padding)
# 2. Mostrar pantalla de carga
# 3. Cargar entorno (.env)
# 4. Inicializar navegación
# 5. Verificar sesión del usuario
# 6. Cargar vista apropiada (Login o Inicio)
```

**Responsabilidades:**
- Inicialización de la app
- Configuración de tema
- Flujo de autenticación
- Carga de datos preliminares

### 2. **requirements.txt** - Dependencias
```
flet==0.28.3              # Framework UI
python-dotenv             # Manejo de .env
pg8000>=1.30.0           # Driver PostgreSQL
openai>=1.0.0            # API ChatBot IA
packaging                # Versionado
scramp                   # Autenticación SCRAM
requests                 # HTTP requests
python-dateutil          # Manejo de fechas
```

---

## 👁️ Vistas y Páginas

### Arquitectura de Páginas

Todas las páginas heredan de `BasePage`:

```python
class MiPagina(BasePage):
    def __init__(self, page, nav_controller):
        super().__init__(page, nav_controller)
        
    def build(self):
        """Construir interfaz"""
        return ft.Container(
            content=self.get_content()
        )
```

### Páginas del Proyecto

#### 1. **login_page.py** 🔐
**Propósito**: Autenticación de usuarios

**Componentes**:
- Panel izquierdo con diseño/imagen
- Formulario de login (email, contraseña)
- Botón "Olvidé contraseña"
- Link a registro

**Flujo**:
1. Usuario ingresa email y contraseña
2. Validación de email con regex
3. Llamada a `database_service.autenticar_usuario()`
4. Si es correcto → Guardar en caché → Ir a "Inicio"
5. Si es incorrecto → Mostrar error

#### 2. **registration_page.py** ✍️
**Propósito**: Crear nuevas cuentas

**Validaciones**:
- Email válido y único
- Contraseña fuerte (min 8 caracteres, mayús, minús, números)
- Aceptación de términos

**Flujo**:
1. Rellenar formulario
2. Validar datos
3. Crear usuario en BD
4. Guardar sesión
5. Ir a Inicio

#### 3. **recover_page.py** 🔄
**Propósito**: Recuperar acceso a cuenta

**Proceso**:
1. Ingresa email
2. Verificar si existe en BD
3. Enviar email con link de reset
4. Usuario hace clic en link
5. Ingresar nueva contraseña

#### 4. **home_page.py** 🏠
**Propósito**: Panel principal después de login

**Componentes**:
- Bienvenida personalizada
- Resumen de calificaciones
- Eventos próximos
- Acceso rápido a características
- Notificaciones

#### 5. **profile_page.py** 👤
**Propósito**: Gestión del perfil de usuario

**Secciones**:
- Banner gradiente (Verde → Azul-Violeta)
- Avatar con foto de perfil
- Menú lateral:
  - Perfil: Editar información
  - Seguridad: Cambiar contraseña
  - Ajustes: Preferencias
  - Actividad: Historial
- Formulario de información personal

#### 6. **notes_page.py** 📊
**Propósito**: Dashboard de calificaciones

**Componentes**:
- 4 KPIs:
  - Total de asignaciones
  - Promedio general
  - Mejor calificación
  - Peor calificación
- Gráfica de barras por asignatura
- Lista de calificaciones recientes
- Panel lateral con eventos y consejos
- Búsqueda por asignatura

#### 7. **calendar_page.py** 📅
**Propósito**: Vista de eventos académicos

**Funcionalidades**:
- Calendario mensual
- Eventos destacados (tareas, exámenes)
- Filtro por tipo de evento
- Notificaciones

#### 8. **techniques_page.py** ⏱️
**Propósito**: Técnicas de estudio interactivas

**3 Niveles**:
1. **Listado**: Grid de técnicas disponibles
2. **Detalle**: Explicación de técnica (Pomodoro)
3. **Aplicación**: Temporizador ejecutable

**Técnicas Incluidas**:
- Pomodoro (25 min: trabajo, 5 min: descanso)
- Cornell Notes
- Spaced Repetition

#### 9. **messaging_page.py** 💬
**Propósito**: Chat colaborativo entre estudiantes

**Características**:
- Lista de conversaciones
- Chat en tiempo real
- Soporte de imágenes y videos
- Indicador de escritura
- Marca como leído/no leído
- Sincronización cada 500ms

#### 10. **chatbot_page.py** 🤖
**Propósito**: Asistente IA para dudas académicas

**Características**:
- Historial de conversaciones
- Respuestas en tiempo real (OpenAI)
- Borrado instantáneo
- Crear nuevas conversaciones
- Guardar conversaciones favoritas

#### 11. **base_page.py** 🏗️
**Propósito**: Clase base para todas las páginas

**Funcionalidades Heredadas**:
```python
class BasePage:
    - __init__(page, nav_controller)
    - get_theme_colors()          # Colores según tema
    - translate(key)              # i18n
    - apply_theme()               # Aplicar tema
    - get_current_user()          # Usuario actual
    - show_loading()              # Indicador carga
    - show_error(message)         # Mostrar error
    - show_success(message)       # Mostrar éxito
    - build()                     # Construir interfaz
```

**Estructura de Tema**:
```python
LIGHT_MODE = {
    "bg": "#F5F8FD",
    "text": "#0F172A",
    "primary": "#3EB534",
    "secondary": "#685BFD",
    "error": "#DC2626"
}

DARK_MODE = {
    "bg": "#111827",
    "text": "#F8FAFC",
    "primary": "#3EB534",
    "secondary": "#685BFD",
    "error": "#EF4444"
}
```

---

## 🔧 Servicios

### 1. **navigation_service.py** 🧭
```python
class NavigationController:
    # Métodos estáticos principales:
    
    + initialize(page, container)
    + update_view(view_name)
    + get_current_user() -> dict
    + apply_user_preferences()
    + preload_data(background=True)
    + set_language(lang_code)
```

**Flujo de Navegación**:
```
Usuario → NavigationController.update_view()
→ Cargar página correspondiente
→ Renderizar en main_container
```

### 2. **database_service.py** 💾
```python
class DatabaseService:
    # Métodos principales:
    
    + init_db()
    + autenticar_usuario(email, password) -> dict
    + registrar_usuario(datos) -> int
    + get_usuarios() -> list
    + get_notas(user_id) -> list
    + save_nota(user_id, datos) -> bool
    + get_mensajes(user_id) -> list
    + save_mensaje(datos) -> bool
```

**Conexión a BD**:
```python
# Usa pg8000 para conexión directa a PostgreSQL
# Maneja queries SQL seguras
# Retorna diccionarios con resultados
```

### 3. **chatbot_service.py** 🤖
```python
class ChatbotService:
    + get_response(message) -> str
    + get_conversation_history(conv_id) -> list
    + save_conversation(user_id, data) -> int
    + delete_conversation(conv_id) -> bool
```

**Integración OpenAI**:
```python
# Usa openai.ChatCompletion.create()
# Envía contexto de estudiante
# Retorna respuestas formateadas
```

---

## 🛠️ Utilidades

### 1. **env_loader.py** 📝
```python
def load_env():
    """Cargar variables de .env a os.environ"""
    # Lee archivo .env
    # Establece variables de entorno
    # Validación de requeridas
```

**Uso**:
```python
from utils.env_loader import load_env
load_env()  # Llamar en main()
```

### 2. **flet_compat.py** 🔧
```python
# Compatibilidad con versiones de Flet
# Workarounds para limitaciones
# Ejemplos:
# - FontWeight.MEDIUM → FontWeight.BOLD
# - Layout alternativo para temas
```

### 3. **helpers.py** 🆘
```python
def format_currency(amount) -> str
def format_date(date) -> str
def validate_email(email) -> bool
def hash_password(password) -> tuple
def validate_password_strength(pwd) -> bool
```

### 4. **i18n.py** 🌍
```python
TRANSLATIONS = {
    "es": {
        "nav_home": "Inicio",
        "nav_profile": "Perfil",
        ...
    },
    "en": {
        "nav_home": "Home",
        "nav_profile": "Profile",
        ...
    },
    "pt": {
        "nav_home": "Início",
        "nav_profile": "Perfil",
        ...
    }
}

def translate(key: str, lang: str = "es") -> str
```

**Uso en Páginas**:
```python
# En BasePage:
texto = self.translate("nav_home")  # Automático con idioma actual

# Directo:
from utils.i18n import translate
texto = translate("nav_home", "en")
```

---

## 🧠 Modelos

### **schema.py** - Esquema de Base de Datos

**Tablas Principales**:

#### 1. **usuarios**
```sql
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre_usuario VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    rol VARCHAR(20) DEFAULT 'estudiante',  -- 'estudiante' o 'profesor'
    photo_url TEXT,
    bio TEXT,
    telefono VARCHAR(30),
    ubicacion VARCHAR(150),
    sitio_web VARCHAR(255),
    fecha_registro TIMESTAMP DEFAULT NOW(),
    ultimo_acceso TIMESTAMP DEFAULT NOW()
);
```

#### 2. **asignaciones**
```sql
CREATE TABLE asignaciones (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    asignatura VARCHAR(100),
    descripcion TEXT,
    profesor VARCHAR(100),
    fecha_entrega TIMESTAMP,
    calificacion DECIMAL(5,2),
    estado VARCHAR(20),  -- 'pendiente', 'completada'
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
```

#### 3. **mensajes**
```sql
CREATE TABLE mensajes (
    id SERIAL PRIMARY KEY,
    remitente_id INT NOT NULL,
    receptor_id INT NOT NULL,
    contenido TEXT,
    adjuntos JSONB,  -- URLs de archivos
    fecha_envio TIMESTAMP DEFAULT NOW(),
    leido BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (remitente_id) REFERENCES usuarios(id),
    FOREIGN KEY (receptor_id) REFERENCES usuarios(id)
);
```

#### 4. **conversaciones_chatbot**
```sql
CREATE TABLE conversaciones_chatbot (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    titulo VARCHAR(255),
    mensajes JSONB,  -- Array de mensajes
    fecha_creacion TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
```

---

## 🎨 Assets

**Ubicación**: `assets/figma_assets/`

**Archivos**:
```
figma_assets/
├── logo.png                    # Logo principal
├── logo_white.png             # Logo blanco
├── logo_dark.png              # Logo modo oscuro
├── login_left_panel.png       # Panel login (imagen prediseñada)
├── icon_home.png              # Ícono inicio
├── icon_profile.png           # Ícono perfil
├── icon_notes.png             # Ícono notas
├── icon_techniques.png        # Ícono técnicas
├── icon_messaging.png         # Ícono mensajería
└── [más assets...]
```

**Uso en Código**:
```python
import flet as ft

# Cargar imagen
imagen = ft.Image(
    src="assets/figma_assets/logo.png",
    width=100,
    height=100
)
```

---

## 🔄 Flujo de Datos

### Flujo Típico de Login

```
┌─────────────────┐
│   Usuario       │
│ Ingresa datos   │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────┐
│  login_page.py                  │
│  - Valida email (regex)         │
│  - Muestra loading indicator    │
└────────┬────────────────────────┘
         │
         ↓
┌─────────────────────────────────┐
│  database_service.py            │
│  autenticar_usuario(email, pwd) │
│  - Query a BD                   │
│  - Verifica hash password       │
└────────┬────────────────────────┘
         │
    ┌────┴─────┐
    ↓          ↓
┌────────┐  ┌──────────┐
│ Éxito  │  │  Error   │
└───┬────┘  └────┬─────┘
    │            │
    ↓            ↓
 Guardar    Mostrar
 sesión en  mensaje
 caché      error
    │            │
    ↓            ↓
 Ir a Inicio  Limpiar
             formulario
```

### Flujo de Mensajería

```
┌──────────────┐         ┌──────────────┐
│   Usuario A  │         │   Usuario B  │
└──────┬───────┘         └──────┬───────┘
       │                        │
       ├─ Escribe mensaje       │
       │                        │
       ├─ Envía (POST)          │
       │  → database_service    │
       │  → Guardar en BD       │
       │                        │
       └─────────────────────→ Recibe
                              (Polling 500ms)
                              ← Sincroniza
       ← Lee en UI
```

### Flujo de ChatBot

```
┌─────────────┐
│   Usuario   │
│  Pregunta   │
└──────┬──────┘
       │
       ↓
┌──────────────────────────┐
│  chatbot_page.py         │
│  - Muestra typing...     │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  chatbot_service.py      │
│  - Envía a OpenAI API    │
│  - Aguarda respuesta     │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  OpenAI GPT-3.5/4        │
│  - Procesa pregunta      │
│  - Genera respuesta IA   │
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│  Mostrar respuesta       │
│  - Guardar en historial  │
│  - Actualizar UI         │
└──────────────────────────┘
```

---

## 🎯 Convenciones de Código

### Nombres de Variables
```python
# ✅ Bien
user_email = "user@example.com"
is_admin = True
total_grades = 10

# ❌ Evitar
e = "user@example.com"
admin = True
tg = 10
```

### Nombres de Funciones
```python
# ✅ Bien
def get_user_grades(user_id):
def validate_email(email):
def save_message(message_data):

# ❌ Evitar
def getgrades(uid):
def validate(e):
def save(d):
```

### Comentarios
```python
# ✅ Bien
# Calcular promedio de calificaciones
average = sum(grades) / len(grades)

# ❌ Evitar
# loop
for g in grades:
    ...
```

---

## 📖 Guía de Lectura Recomendada

Para entender el proyecto:

1. **Nuevo en el proyecto**: `QUICKSTART.md` → `README.md`
2. **Empezar desarrollo**: `PROJECT_STRUCTURE.md` (este) → `main.py` → `base_page.py`
3. **Agregar feature**: `CONTRIBUTING.md` → Código relevante
4. **Entender negocio**: `EXECUTIVE_SUMMARY.md`

---

## 🔗 Relaciones entre Componentes

```
main.py
  ├→ NavigationController (init)
  │   ├→ DatabaseService
  │   ├→ ChatbotService
  │   └→ Cargar todas las páginas
  │
  └→ BasePage (herencia)
      ├→ LoginPage
      ├→ HomePage
      ├→ ProfilePage
      ├→ NotesPage
      ├→ TechniquesPage
      ├→ MessagingPage
      └→ ChatbotPage
      
Todas las páginas acceden a:
  ├→ DatabaseService (datos)
  ├→ NavigationController (navegar)
  └→ utils/i18n.py (traducir)
```

---

## 📞 ¿Necesitas Ayuda?

- 📖 Revisa README.md
- 🚀 Sigue QUICKSTART.md
- 🤝 Lee CONTRIBUTING.md
- 🐛 Abre un Issue
- 💬 Participa en Discussions

---

**Última actualización**: Julio 2026
**Versión**: v13
**Documentación**: 100% actualizada
