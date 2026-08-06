# 🤝 Guía de Contribución

¡Gracias por tu interés en contribuir a **PointList**! Este documento te guiará sobre cómo reportar bugs, sugerir mejoras y enviar código.

## 📋 Código de Conducta

Esperamos que todos los colaboradores:
- Traten a otros con respeto
- Proporcionen retroalimentación constructiva
- Se enfoquen en lo que es mejor para la comunidad
- Acepten críticas de manera profesional

## 🐛 Reportar Bugs

Antes de reportar un bug, verifica:
1. Si el bug ya existe en [Issues](https://github.com/tu-usuario/pointlist/issues)
2. Si estás usando la versión más reciente
3. Que sea reproducible

### Formato de reporte:
```markdown
**Título:** Descripción clara del bug

**Versión:** v13 (u otra)

**Pasos para reproducir:**
1. ...
2. ...
3. ...

**Comportamiento esperado:**
Debería...

**Comportamiento actual:**
En su lugar...

**Capturas/Logs:**
[Adjunta si es posible]

**Entorno:**
- SO: Windows/macOS/Linux
- Python: 3.8/3.9/3.10/3.11
- Navegador (si aplica): Chrome/Firefox/Safari
```

## 💡 Sugerir Mejoras

Las sugerencias de nuevas características son bienvenidas. Por favor:
1. Usa un título descriptivo
2. Proporciona casos de uso claros
3. Lista ejemplos de funcionalidades similares

## 🔄 Proceso de Pull Request

### 1. Fork y Clonar
```bash
git clone https://github.com/TU-USUARIO/pointlist.git
cd pointlist
```

### 2. Crear rama de feature
```bash
git checkout -b feature/nombre-descriptivo
# Ejemplos:
# feature/agregar-notificaciones
# fix/bug-login-oscuro
# docs/mejorar-readme
```

### 3. Hacer cambios
- Sigue el estilo de código existente
- Comenta el código complejo
- Usa nombres de variables descriptivos

### 4. Testear
```bash
# Compilar para verificar sintaxis
python -m py_compile archivo_modificado.py

# Ejecutar en local
flet run
```

### 5. Commit y Push
```bash
git add .
git commit -m "tipo: descripción breve

Descripción más detallada si es necesario.
- Punto 1
- Punto 2"

# Tipos de commit:
# feat: Nueva característica
# fix: Corrección de bug
# docs: Cambios en documentación
# style: Formato de código (sin cambios de lógica)
# refactor: Refactorización de código
# perf: Mejoras de rendimiento
# test: Agregar o actualizar tests

git push origin feature/nombre-descriptivo
```

### 6. Crear Pull Request
- Proporciona descripción clara
- Referencia issues relacionados con `Closes #123`
- Espera revisión

## 📝 Directrices de Código

### Estilo Python
```python
# ✅ Bien
from services.database_service import DatabaseService
from utils.i18n import translate

def get_user_grades(user_id: int) -> list:
    """Obtiene las calificaciones de un usuario."""
    db = DatabaseService()
    return db.get_grades(user_id)

# ❌ Evitar
from services.database_service import *
def get_user_grades(id):
    return DatabaseService().get_grades(id)
```

### Comentarios y Docstrings
```python
def calculate_average(grades: list[float]) -> float:
    """
    Calcula el promedio de calificaciones.
    
    Args:
        grades: Lista de calificaciones
        
    Returns:
        Promedio como float
        
    Raises:
        ValueError: Si la lista está vacía
    """
    if not grades:
        raise ValueError("La lista de calificaciones no puede estar vacía")
    
    return sum(grades) / len(grades)
```

### Nombres de variables
```python
# ✅ Bien
user_email = "estudiante@example.com"
total_students = 150
is_admin = True

# ❌ Evitar
e = "estudiante@example.com"
ts = 150
admin = True
```

## 🌍 Contribuciones de Traducción

Para agregar o mejorar traducciones:

1. Edita `utils/i18n.py`
2. Sigue el formato existente
3. Verifica que todas las claves estén traducidas
4. Crea PR con cambios de traducción

Idiomas actualmente soportados:
- 🇪🇸 Español (es)
- 🇺🇸 Inglés (en)
- 🇧🇷 Portugués (pt)

## 📚 Documentación

- Documenta nuevas características
- Actualiza el README si aplica
- Agrega ejemplos de código cuando sea relevante
- Comenta cambios en el CHANGELOG

## 🔍 Revisión de PR

Los maintainers revisarán:
- ✅ Calidad de código
- ✅ Compatibilidad con Flet
- ✅ Seguridad
- ✅ Documentación
- ✅ Tests

## 🎯 Áreas donde podemos usar ayuda

- 🐛 Reportar y corregir bugs
- 📱 Soporte iOS/Android
- 🌍 Nuevas traducciones
- 📊 Mejoras de UI/UX
- ⚡ Optimizaciones de rendimiento
- 📖 Documentación
- ✅ Tests automatizados

## ❓ Preguntas o Dudas

- Abre una [Discussion](https://github.com/tu-usuario/pointlist/discussions)
- Contacta a los maintainers
- Revisa Issues existentes

---

¡Gracias por ayudar a mejorar PointList! 🙏
