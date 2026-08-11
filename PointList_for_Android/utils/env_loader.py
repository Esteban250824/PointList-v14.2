import os
import sys

def load_env():
    """Carga el archivo .env en orden de prioridad para desarrollo, ejecutable .exe y APK de Android."""
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
    module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    paths = [
        os.path.join(exe_dir, ".env"),                     # 1. Junto al ejecutable
        os.path.join(base_dir, ".env"),                    # 2. En paquete compilado
        os.path.join(module_dir, ".env"),                  # 3. Raíz del paquete de origen
        os.path.join(os.getcwd(), ".env"),                 # 4. Directorio de trabajo actual
        os.path.join(os.path.dirname(base_dir), ".env"),   # 5. Directorio padre
    ]

    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'): continue
                        if '=' in line:
                            k, v = line.split('=', 1)
                            os.environ[k.strip()] = v.strip().strip('"').strip("'")
                return True
            except:
                pass
    return False

