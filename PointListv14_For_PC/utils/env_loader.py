import os
import sys

def load_env():
    """Carga las variables de entorno para desarrollo y ejecutable .exe congelado."""
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()

    # Prioridad: 
    # 1. Archivo .env empaquetado dentro del binario (_MEIPASS)
    # 2. Archivo .env externo junto al ejecutable (para personalizaciones opcionales)
    # 3. Archivo .env en la raíz del código fuente
    paths = [
        os.path.join(base_dir, ".env"),
        os.path.join(exe_dir, ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(base_dir), ".env"),
    ]

    loaded = False
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            k, v = line.split('=', 1)
                            # Cargar la variable si no está previamente establecida en el sistema
                            var_key = k.strip()
                            if var_key not in os.environ:
                                os.environ[var_key] = v.strip().strip('"').strip("'")
                loaded = True
            except:
                pass
    return loaded
