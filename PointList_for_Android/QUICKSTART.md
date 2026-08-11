# 🚀 Guía de Inicio Rápido

¡Bienvenido a **PointList**! Sigue estos pasos para tener la aplicación funcionando en minutos.

## ⚡ Inicio Rápido (5 minutos)

### 1️⃣ Requisitos Previos

Asegúrate de tener instalado:
- **Python 3.8+** → [Descargar](https://www.python.org/downloads/)
- **PostgreSQL 12+** → [Descargar](https://www.postgresql.org/download/)
- **Git** → [Descargar](https://git-scm.com/download/)

**Verifica las instalaciones:**
```bash
python --version
psql --version
git --version
```

---

### 2️⃣ Clonar el Repositorio

```bash
git clone https://github.com/tu-usuario/pointlist.git
cd pointlist
```

---

### 3️⃣ Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

---

### 4️⃣ Instalar Dependencias

```bash
pip install -r requirements.txt
```

---

### 5️⃣ Configurar Base de Datos

#### Crear base de datos en PostgreSQL:
```bash
# Abre psql
psql -U postgres

# En la consola de PostgreSQL:
CREATE DATABASE pointlist;
CREATE USER pointlist_user WITH PASSWORD 'tu_contraseña_segura';
ALTER ROLE pointlist_user SET client_encoding TO 'utf8';
ALTER ROLE pointlist_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE pointlist_user SET default_transaction_deferrable TO on;
ALTER ROLE pointlist_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE pointlist TO pointlist_user;
\q
```

---

### 6️⃣ Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Base de Datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pointlist
DB_USER=pointlist_user
DB_PASSWORD=tu_contraseña_segura

# OpenAI API (opcional, para PointBit)
OPENAI_API_KEY=sk-your_key_here

# Configuración de la aplicación
APP_DEBUG=False
DEFAULT_LANGUAGE=es
```

---

### 7️⃣ Inicializar la Base de Datos

```bash
python -c "
from models.schema import CREATE_TABLES_SQL
from services.database_service import DatabaseService

db = DatabaseService()
db.init_db()
print('✅ Base de datos inicializada correctamente')
"
```

---

### 8️⃣ ¡Ejecutar la Aplicación!

```bash
flet run
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8000`

---

## 🎮 Primeros Pasos en la App

1. **Crear una cuenta:**
   - Haz clic en "Registrarse"
   - Usa un email válido
   - Define tu contraseña

2. **Explorar las características:**
   - 📊 **Notas**: Visualiza calificaciones
   - 🏠 **Inicio**: Panel principal
   - 👤 **Perfil**: Personaliza tu cuenta
   - ⏱️ **Técnicas**: Prueba el Pomodoro
   - 💬 **Mensajes**: Chatea con otros
   - 🤖 **ChatBot**: Usa PointBit

3. **Cambiar idioma:**
   - Ve a Perfil → Ajustes
   - Selecciona tu idioma preferido (ES/EN/PT)

---

## 🔧 Desarrollo

### Ejecutar en modo debug

```bash
# Habilitar logs detallados
# Edita main.py y descomenta líneas de debug
flet run --verbose
```

### Verificar sintaxis

```bash
python -m py_compile views/pages/login_page.py
```

### Limpiar cache

```bash
# Elimina archivos __pycache__
python -c "
import shutil
import os
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        shutil.rmtree(os.path.join(root, '__pycache__'))
print('✅ Cache limpiado')
"
```

---

## 📱 Compilar para Móvil

### Android
```bash
# Requiere Android SDK instalado
flet run --android --output ./build/pointlist.apk
```

### iOS
```bash
# Requiere Xcode (macOS)
flet run --ios
```

---

## 🐛 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'flet'"
```bash
# Asegúrate que el entorno virtual está activado
# Luego reinstala dependencias
pip install --upgrade -r requirements.txt
```

### Error: "connection to server at localhost (127.0.0.1), port 5432 failed"
```bash
# Verifica que PostgreSQL está ejecutándose
# Windows: Services → busca PostgreSQL
# macOS: brew services start postgresql
# Linux: sudo service postgresql start
```

### Error: "OPENAI_API_KEY no configurada"
```bash
# Este error es OK si no usas PointBit
# Para habilitar PointBit, agrega tu key en .env
# Obtén una key en: https://platform.openai.com/api-keys
```

### La aplicación se abre en blanco
```bash
# Limpia cache y reinicia
rm -rf .flet_cache
flet run
```

---

## 📚 Recursos Útiles

- 📖 [Documentación de Flet](https://flet.dev)
- 🐘 [Documentación de PostgreSQL](https://www.postgresql.org/docs/)
- 🐍 [Documentación de Python](https://docs.python.org/3/)
- 🤖 [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

---

## 🤝 Necesitas Ayuda?

- 📝 Revisa el [README.md](README.md) completo
- 🐛 Abre un [Issue](https://github.com/tu-usuario/pointlist/issues)
- 💬 Participa en [Discussions](https://github.com/tu-usuario/pointlist/discussions)
- 📧 Contacta: soporte@pointlist.app

---

## ✅ Checklist de Instalación

- [ ] Python 3.8+ instalado
- [ ] PostgreSQL instalado y ejecutándose
- [ ] Repositorio clonado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas
- [ ] Base de datos creada
- [ ] `.env` configurado
- [ ] Tablas de BD inicializadas
- [ ] Aplicación ejecutándose sin errores
- [ ] Puedes crear cuenta y loguear

---

**¡Listo!** 🎉 Ya estás en camino a dominar PointList.

Para más detalles, consulta la [documentación completa](README.md).
