# 📚 PointList - Plataforma Educativa Integral

> Una aplicación multiplataforma para estudiantes que desean optimizar su gestión académica, técnicas de estudio y comunicación colaborativa.

[![Flet](https://img.shields.io/badge/Flet-0.28.3-blue.svg)](https://flet.dev)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Características Principales

### 📱 Interfaz Moderna y Responsiva
- **Diseño basado en Figma** con componentes profesionales
- **Modo oscuro** completamente optimizado sin residuos de blanco
- **Modo claro** para máxima comodidad visual
- **Diseño responsivo** que se adapta a cualquier dispositivo

### 👤 Gestión de Perfiles
- **Perfil personalizablecon banner gradiente** (Verde → Azul-Violeta)
- **Avatar con foto de perfil** y botón de cámara
- **Menú lateral** para acceder a Perfil, Seguridad, Ajustes y Actividad
- **Información personal completa** en formato de dos columnas

### 📊 Dashboard de Notas
- **KPIs educativos**: Promedio general, mejor calificación, peor calificación
- **Gráficas interactivas** con visualización de calificaciones por asignatura
- **Panel lateral** con próximos eventos y consejo del día
- **Búsqueda en tiempo real** para filtrar por asignatura

### ⏱️ Técnicas de Estudio Interactivas
- **Pomodoro**: Técnica clásica de bloques de 25 minutos
- **Interfaz de 3 niveles**: Listado → Detalle → Aplicación
- **Temporizador integrado** con visualización en tiempo real
- **Consejos personalizados** para cada técnica

### 💬 Mensajería Colaborativa
- **Chat sin retrasos**: Actualización optimista inmediata
- **Soporte de multimedia**: Imágenes (JPG, PNG) y videos (MP4, AVI, MOV)
- **Sincronización en background** cada 500ms
- **Notificaciones** para nuevos mensajes

### 🤖 ChatBot PointBit
- **Asistente IA integrado** para dudas académicas
- **Conversaciones organizadas** con historial sincronizado
- **Borrado instantáneo** de conversaciones
- **Respuestas en tiempo real** usando OpenAI

### 🌍 Multiidioma (i18n)
- **Español (Latinoamérica)** - Idioma predeterminado
- **English (US)** - Soporte completo
- **Português (Brasil)** - Soporte completo
- **Cambio dinámico** sin necesidad de reiniciar

### 🔐 Autenticación Segura
- **Registro y Login** con validación de email
- **Contraseñas encriptadas** con sal
- **Recuperación de contraseña** por email
- **Sesión persistente** con almacenamiento local

## 🛠️ Stack Tecnológico

### Backend
- **Python 3.8+** - Lenguaje principal
- **Flet 0.28.3** - Framework UI multiplataforma
- **PostgreSQL** - Base de datos relacional
- **pg8000** - Driver PostgreSQL puro en Python
- **python-dotenv** - Gestión de variables de entorno

### Integraciones
- **OpenAI API** - Chatbot IA (PointBit)
- **python-dateutil** - Manejo de fechas

### Características Técnicas
- **Sistema de navegación** centralizado
- **Caché de usuario** para sesiones
- **Precargar datos** en background
- **Sincronización cada 500ms** para datos en tiempo real

## 📋 Estructura del Proyecto

```
pointlist_v13/
├── main.py                      # Punto de entrada de la aplicación
├── requirements.txt             # Dependencias Python
├── README.md                    # Este archivo
├── CHANGELOG_v*.md              # Historial de versiones
├── .env.example                 # Variables de entorno (plantilla)
│
├── models/
│   ├── __init__.py
│   └── schema.py               # Esquema de base de datos PostgreSQL
│
├── services/
│   ├── navigation_service.py   # Controlador de navegación
│   ├── database_service.py     # Operaciones de base de datos
│   └── chatbot_service.py      # Integración con OpenAI
│
├── utils/
│   ├── __init__.py
│   ├── env_loader.py           # Cargador de variables de entorno
│   ├── flet_compat.py          # Compatibilidad con Flet
│   ├── helpers.py              # Funciones utilitarias
│   └── i18n.py                 # Sistema multiidioma
│
├── views/
│   └── pages/
│       ├── base_page.py        # Clase base para todas las páginas
│       ├── login_page.py       # Autenticación
│       ├── registration_page.py # Registro de usuarios
│       ├── recover_page.py     # Recuperación de contraseña
│       ├── home_page.py        # Página principal (Inicio)
│       ├── profile_page.py     # Perfil de usuario
│       ├── notes_page.py       # Dashboard de calificaciones
│       ├── calendar_page.py    # Calendario académico
│       ├── techniques_page.py  # Técnicas de estudio
│       ├── messaging_page.py   # Chat colaborativo
│       └── chatbot_page.py     # Asistente IA (PointBit)
│
└── assets/
    └── figma_assets/           # Recursos visuales (logos, íconos, etc.)
```

## 🚀 Instalación y Configuración

### Prerequisitos
- Python 3.8 o superior
- PostgreSQL 12 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/pointlist.git
cd pointlist
```

2. **Crear entorno virtual**
```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En macOS/Linux
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus credenciales de base de datos y API keys
```

5. **Inicializar la base de datos**
```bash
python -c "from models.schema import CREATE_TABLES_SQL; from services.database_service import DatabaseService; db = DatabaseService(); db.init_db()"
```

6. **Ejecutar la aplicación**

**En la web:**
```bash
flet run
```

**Para Android (requiere Flet CLI):**
```bash
flet run --android
```

**Para iOS (requiere Flet CLI):**
```bash
flet run --ios
```

## 🔧 Configuración de Variables de Entorno

Crear un archivo `.env` con las siguientes variables:

```env
# Base de Datos PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pointlist
DB_USER=postgres
DB_PASSWORD=tu_contraseña

# OpenAI API (Para PointBit)
OPENAI_API_KEY=sk-xxxxxxxxxxxxx

# Aplicación
APP_DEBUG=False
DEFAULT_LANGUAGE=es
```

## 💡 Uso de la Aplicación

### Para Estudiantes
1. **Crear cuenta** con email válido
2. **Configurar perfil** con foto y información personal
3. **Agregar asignaciones** desde el dashboard
4. **Consultar técnicas** de estudio
5. **Usar PointBit** para resolver dudas
6. **Colaborar** con compañeros por mensajería

### Para Desarrolladores

#### Cambiar idioma
```python
page_instance.set_language("en")   # Inglés
page_instance.set_language("pt")   # Portugués
page_instance.set_language("es")   # Español
```

#### Traducir textos
```python
from utils.i18n import translate
texto = translate("nav_home", "es")  # "Inicio"
texto = translate("nav_home", "en")  # "Home"
```

#### Acceder a la base de datos
```python
from services.database_service import DatabaseService
db = DatabaseService()
usuarios = db.get_usuarios()
```

#### Sistema de navegación
```python
from services.navigation_service import NavigationController
# Cambiar vista
NavigationController.update_view("Inicio")
# Obtener usuario actual
user = NavigationController.get_current_user()
```

## 📱 Pantallas Principales

| Pantalla | Descripción |
|----------|-------------|
| **Login** | Autenticación de usuarios con email y contraseña |
| **Registro** | Creación de nuevas cuentas de estudiante |
| **Recuperación** | Reset de contraseña por email |
| **Inicio** | Dashboard principal con resumen de actividades |
| **Perfil** | Edición de información personal y preferencias |
| **Notas** | Visualización de calificaciones y estadísticas |
| **Calendario** | Vista de eventos y fechas importantes |
| **Técnicas** | Técnicas de estudio con temporizador Pomodoro |
| **Mensajería** | Chat colaborativo entre estudiantes |
| **ChatBot** | Asistente IA (PointBit) para dudas académicas |

## 🔐 Seguridad

- ✅ Contraseñas almacenadas con hash y sal
- ✅ Validación de email en registro
- ✅ Sesiones persistentes con caché local
- ✅ Conexión segura a base de datos
- ✅ Variables sensibles en archivo `.env`

## 📊 Estadísticas del Código

- **Módulos**: 15+
- **Páginas**: 10
- **Idiomas soportados**: 3
- **Líneas de código**: 5000+

## 🎨 Paleta de Colores

### Modo Claro
- Fondo: `#F5F8FD`
- Texto principal: `#0F172A`
- Acento: `#3EB534` (Verde)
- Secundario: `#685BFD` (Azul-Violeta)

### Modo Oscuro
- Fondo: `#111827`
- Texto principal: `#F8FAFC`
- Acento: `#3EB534` (Verde)
- Secundario: `#685BFD` (Azul-Violeta)

## 🤝 Contribución

Las contribuciones son bienvenidas. Para cambios importantes:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 📞 Contacto y Soporte

- 📧 Email: soporte@pointlist.app
- 🐛 Reportar bugs: [Issues](https://github.com/tu-usuario/pointlist/issues)
- 💬 Sugerencias: [Discussions](https://github.com/tu-usuario/pointlist/discussions)

## 🙏 Agradecimientos

- Diseño basado en Figma
- UI Framework: Flet
- Base de datos: PostgreSQL
- Inteligencia artificial: OpenAI

---

**PointList** - Simplificando la gestión académica. 🚀

Última actualización: v13 (Rediseño completo con Figma)
