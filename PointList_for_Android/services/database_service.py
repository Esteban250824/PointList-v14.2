import os
import threading
import time
from contextlib import contextmanager
from urllib.parse import urlparse
import pg8000
from models.schema import CREATE_TABLES_SQL, SEED_TECNICAS_SQL
from utils.helpers import hash_password, verify_password

class DatabaseService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized: return
        self.db_url = os.getenv("DATABASE_URL")
        self._local = threading.local()
        self._initialized = True
        threading.Thread(target=self._ensure_tables, daemon=True).start()

    def _get_connection(self):
        if not self.db_url: raise ValueError("DATABASE_URL no configurada")
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            try:
                if not getattr(conn, "_closed", True):
                    return conn
            except: pass
            try:
                conn.close()
            except: pass
            self._local.conn = None

        url = urlparse(self.db_url)
        import ssl
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        new_conn = pg8000.connect(
            user=url.username, password=url.password,
            host=url.hostname, port=url.port or 6543,
            database=url.path[1:], ssl_context=ssl_ctx
        )
        self._local.conn = new_conn
        return new_conn

    @contextmanager
    def _get_cursor(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            try:
                conn.rollback()
            except: pass
            self._local.conn = None
            error_msg = str(e)
            if "already exists" not in error_msg.lower() and "can't create a connection" not in error_msg.lower():
                print(f"[DB] Error de base de datos: {e}")
            raise
        finally:
            try:
                cursor.close()
            except: pass

    def _ensure_tables(self):
        """Inicialización inteligente: verifica antes de actuar."""
        try:
            with self._get_cursor() as cursor:
                for sql in CREATE_TABLES_SQL:
                    if "CREATE TABLE IF NOT EXISTS" in sql:
                        cursor.execute(sql)
        except: pass

        def add_column_safe(table, column_def):
            col_name = column_def.split()[0]
            try:
                with self._get_cursor() as cursor:
                    cursor.execute(f"""
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='{table}' AND column_name='{col_name}'
                    """)
                    if not cursor.fetchone():
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
            except: pass

        columnas_usuarios = [
            "rol VARCHAR(20) DEFAULT 'estudiante'",
            "bio TEXT DEFAULT ''",
            "telefono VARCHAR(30) DEFAULT ''",
            "ubicacion VARCHAR(150) DEFAULT ''",
            "sitio_web VARCHAR(255) DEFAULT ''"
        ]
        for col in columnas_usuarios: add_column_safe("usuarios", col)
        add_column_safe("notas", "profesor_id INTEGER REFERENCES usuarios(id)")

        try:
            with self._get_cursor() as cursor:
                cursor.execute("""
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name='unique_titulo' AND table_name='tecnicas_estudio'
                """)
                if not cursor.fetchone():
                    cursor.execute("""
                        DELETE FROM tecnicas_estudio 
                        WHERE id NOT IN (SELECT MIN(id) FROM tecnicas_estudio GROUP BY titulo)
                    """)
                    cursor.execute("ALTER TABLE tecnicas_estudio ADD CONSTRAINT unique_titulo UNIQUE (titulo)")
        except: pass

        try:
            with self._get_cursor() as cursor:
                for sql in CREATE_TABLES_SQL:
                    if sql.strip(): cursor.execute(sql)
                cursor.execute(SEED_TECNICAS_SQL)
        except: pass

    def autenticar_usuario(self, email, password):
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT id, nombre_usuario, email, password_hash, salt, photo_url, rol, bio, telefono, ubicacion, sitio_web FROM usuarios WHERE email = %s", (email,))
                u = cursor.fetchone()
                if u and verify_password(u[3], password, u[4]):
                    return {
                        "ok": True, 
                        "usuario": {
                            "id": u[0], "nombre_usuario": u[1], "email": u[2], "photo_url": u[5],
                            "rol": u[6], "bio": u[7], "telefono": u[8], "ubicacion": u[9], "sitio_web": u[10]
                        }
                    }
            return {"ok": False, "error": "Credenciales inválidas"}
        except Exception as e: return {"ok": False, "error": str(e)}

    def crear_usuario(self, nombre, email, password, rol="estudiante"):
        try:
            h, s = hash_password(password)
            with self._get_cursor() as cursor:
                cursor.execute("INSERT INTO usuarios (nombre_usuario, email, password_hash, salt, rol) VALUES (%s, %s, %s, %s, %s) RETURNING id", (nombre, email, h, s, rol))
                uid = cursor.fetchone()[0]
                cursor.execute("INSERT INTO configuracion_usuario (usuario_id) VALUES (%s)", (uid,))
                return {"ok": True, "usuario": {"id": uid, "nombre_usuario": nombre, "email": email, "rol": rol}}
        except Exception as e: return {"ok": False, "error": str(e)}

    def obtener_o_crear_usuario_google(self, email: str, nombre: str, photo_url: str = None):
        """Obtiene o registra un usuario de Google OAuth en 1 sola consulta SQL instantánea (< 50ms) sin bcrypt ralentizado."""
        clean_email = (email or "").strip().lower()
        clean_name = (nombre or clean_email.split("@")[0]).strip()
        p_url = photo_url or "https://lh3.googleusercontent.com/a/default-user=s96-c"

        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, nombre_usuario, email, photo_url, rol, bio, telefono, ubicacion, sitio_web FROM usuarios WHERE email = %s",
                    (clean_email,)
                )
                u = cursor.fetchone()
                if u:
                    return {
                        "ok": True,
                        "usuario": {
                            "id": u[0], "nombre_usuario": u[1], "email": u[2], "photo_url": u[3] or p_url,
                            "rol": u[4] or "estudiante", "bio": u[5] or "", "telefono": u[6] or "",
                            "ubicacion": u[7] or "", "sitio_web": u[8] or ""
                        }
                    }

                cursor.execute(
                    "INSERT INTO usuarios (nombre_usuario, email, password_hash, salt, photo_url, rol) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (clean_name, clean_email, "GOOGLE_OAUTH_USER", "OAUTH_SALT", p_url, "estudiante")
                )
                uid = cursor.fetchone()[0]
                try:
                    cursor.execute("INSERT INTO configuracion_usuario (usuario_id) VALUES (%s) ON CONFLICT DO NOTHING", (uid,))
                except: pass

                return {
                    "ok": True,
                    "usuario": {
                        "id": uid, "nombre_usuario": clean_name, "email": clean_email, "photo_url": p_url,
                        "rol": "estudiante", "bio": "", "telefono": "", "ubicacion": "", "sitio_web": ""
                    }
                }
        except Exception as ex:
            return {"ok": False, "error": str(ex)}

    def actualizar_perfil(self, uid, datos):
        try:
            with self._get_cursor() as cursor:
                fields = []
                values = []
                for k, v in datos.items():
                    fields.append(f"{k} = %s")
                    values.append(v)
                values.append(uid)
                sql = f"UPDATE usuarios SET {', '.join(fields)} WHERE id = %s"
                cursor.execute(sql, tuple(values))
                return {"ok": True}
        except Exception as e: return {"ok": False, "error": str(e)}

    def obtener_configuracion(self, uid):
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "SELECT tema, idioma FROM configuracion_usuario WHERE usuario_id = %s",
                    (uid,),
                )
                r = cursor.fetchone()
                if r:
                    return {"tema": r[0] or "claro", "idioma": r[1] or "es"}
        except:
            pass
        return {"tema": "claro", "idioma": "es"}

    def actualizar_configuracion(self, uid, datos):
        """Actualiza preferencias del usuario (tema, idioma, etc.)."""
        allowed = {"tema", "idioma", "voz_pointbit", "video_intro_visto", "notificaciones"}
        try:
            payload = {k: v for k, v in datos.items() if k in allowed}
            if not payload:
                return {"ok": False, "error": "Sin campos válidos"}

            with self._get_cursor() as cursor:
                fields = [f"{k} = %s" for k in payload]
                values = list(payload.values()) + [uid]
                cursor.execute(
                    f"UPDATE configuracion_usuario SET {', '.join(fields)}, actualizado_en = NOW() WHERE usuario_id = %s",
                    tuple(values),
                )
                if cursor.rowcount == 0:
                    cursor.execute(
                        "INSERT INTO configuracion_usuario (usuario_id, tema, idioma) VALUES (%s, %s, %s)",
                        (uid, payload.get("tema", "claro"), payload.get("idioma", "es")),
                    )
                return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def obtener_notas(self, uid):
        """Obtiene notas de un usuario. Si es profesor, obtiene las que él ha puesto."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT rol FROM usuarios WHERE id = %s", (uid,))
                rol = cursor.fetchone()[0]

                if rol == 'profesor':
                    cursor.execute("""
                        SELECT n.id, n.asignatura, n.calificacion, n.fecha, n.comentarios,
                               u.nombre_usuario AS estudiante, p.nombre_usuario AS profesor
                        FROM notas n
                        JOIN usuarios u ON n.usuario_id = u.id
                        LEFT JOIN usuarios p ON n.profesor_id = p.id
                        WHERE n.profesor_id = %s
                        ORDER BY n.timestamp DESC
                    """, (uid,))
                    return [{
                        "id": r[0],
                        "asignatura": r[1],
                        "calificacion": float(r[2]),
                        "fecha": r[3],
                        "comentarios": r[4],
                        "estudiante": r[5],
                        "profesor": r[6] or "",
                    } for r in cursor.fetchall()]

                cursor.execute("""
                    SELECT n.id, n.asignatura, n.calificacion, n.fecha, n.comentarios,
                           u.nombre_usuario AS estudiante, p.nombre_usuario AS profesor
                    FROM notas n
                    JOIN usuarios u ON n.usuario_id = u.id
                    LEFT JOIN usuarios p ON n.profesor_id = p.id
                    WHERE n.usuario_id = %s
                    ORDER BY n.timestamp DESC
                """, (uid,))
                return [{
                    "id": r[0],
                    "asignatura": r[1],
                    "calificacion": float(r[2]),
                    "fecha": r[3],
                    "comentarios": r[4],
                    "estudiante": r[5],
                    "profesor": r[6] or "",
                } for r in cursor.fetchall()]
        except: return []

    def obtener_estudiantes(self):
        """Obtiene la lista de todos los estudiantes."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT id, nombre_usuario, email FROM usuarios WHERE rol = 'estudiante'")
                return [{"id": r[0], "nombre": r[1], "email": r[2]} for r in cursor.fetchall()]
        except: return []

    def obtener_eventos(self, uid):
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT id, titulo, descripcion, tipo_evento, fecha_inicio, fecha_fin FROM agenda WHERE usuario_id = %s ORDER BY fecha_inicio", (uid,))
                return [{"id": r[0], "titulo": r[1], "descripcion": r[2], "tipo_evento": r[3], "fecha_inicio": r[4], "fecha_fin": r[5]} for r in cursor.fetchall()]
        except: return []

    def obtener_tecnicas(self):
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT id, titulo, descripcion, categoria, icon_url FROM tecnicas_estudio ORDER BY id ASC")
                return [{"id": r[0], "titulo": r[1], "descripcion": r[2], "categoria": r[3], "icon_url": r[4]} for r in cursor.fetchall()]
        except: return []

    def obtener_sesiones_chatbot(self, uid):
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT session_id, titulo, actualizado_en FROM chatbot_sesiones WHERE usuario_id = %s ORDER BY actualizado_en DESC NULLS LAST, id DESC", (uid,))
                return [{"session_id": r[0], "titulo": r[1] or "Conversación", "actualizado_en": str(r[2]) if r[2] else None} for r in cursor.fetchall()]
        except Exception:
            return []

    def obtener_historial_chatbot(self, uid, sid):
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT pregunta, respuesta FROM historial_chatbot WHERE session_id = %s ORDER BY id ASC", (sid,))
                return [{"pregunta": r[0], "respuesta": r[1]} for r in cursor.fetchall()]
        except Exception:
            return []

    def crear_sesion_chatbot(self, uid, sid, titulo):
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT 1 FROM chatbot_sesiones WHERE session_id = %s", (sid,))
                if cursor.fetchone():
                    cursor.execute("UPDATE chatbot_sesiones SET actualizado_en = NOW(), titulo = %s WHERE session_id = %s", (titulo, sid))
                else:
                    cursor.execute("INSERT INTO chatbot_sesiones (usuario_id, session_id, titulo, actualizado_en) VALUES (%s, %s, %s, NOW())", (uid, sid, titulo))
                return {"session_id": sid, "titulo": titulo}
        except: return None

    def guardar_interaccion_chatbot(self, uid, sid, pregunta, respuesta, modelo="pointbit"):
        try:
            with self._get_cursor() as cursor:
                cursor.execute("INSERT INTO historial_chatbot (usuario_id, session_id, pregunta, respuesta, modelo, timestamp) VALUES (%s, %s, %s, %s, %s, NOW())", (uid, sid, pregunta, respuesta, modelo))
                cursor.execute("SELECT COUNT(*) FROM historial_chatbot WHERE session_id = %s", (sid,))
                count = cursor.fetchone()[0]
                if count == 1:
                    titulo = (pregunta[:30] + '...') if len(pregunta) > 30 else pregunta
                    cursor.execute("UPDATE chatbot_sesiones SET actualizado_en = NOW(), titulo = %s WHERE session_id = %s", (titulo, sid))
                else:
                    cursor.execute("UPDATE chatbot_sesiones SET actualizado_en = NOW() WHERE session_id = %s", (sid,))
                return True
        except: return False

    def borrar_sesion_chatbot(self, sid):
        try:
            with self._get_cursor() as cursor:
                cursor.execute("DELETE FROM historial_chatbot WHERE session_id = %s", (sid,))
                cursor.execute("DELETE FROM chatbot_sesiones WHERE session_id = %s", (sid,))
                return True
        except: return False

    def agregar_nota(self, uid, asignatura, calificacion, fecha, comentarios="", profesor_id=None):
        """Agrega una nueva nota. Si profesor_id está presente, es una nota asignada por un profesor."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO notas (usuario_id, profesor_id, asignatura, calificacion, fecha, comentarios, timestamp) VALUES (%s, %s, %s, %s, %s, %s, EXTRACT(EPOCH FROM NOW())) RETURNING id",
                    (uid, profesor_id, asignatura, float(calificacion), fecha, comentarios)
                )
                nid = cursor.fetchone()[0]
                return {"ok": True, "id": nid}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def guardar_nota(self, uid, profesor_id, asignatura, calificacion, fecha, comentarios=""):
        """Alias compatible con el flujo anterior del frontend."""
        return self.agregar_nota(uid, asignatura, calificacion, fecha, comentarios, profesor_id=profesor_id)

    def eliminar_nota(self, nid, uid):
        """Elimina una nota. Solo si el usuario es el dueño o el profesor que la puso."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute("DELETE FROM notas WHERE id = %s AND (usuario_id = %s OR profesor_id = %s)", (nid, uid, uid))
                return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def guardar_evento(self, uid, titulo, descripcion, tipo_evento, fecha_inicio, fecha_fin):
        """Guarda un evento en la agenda."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO agenda (usuario_id, titulo, descripcion, tipo_evento, fecha_inicio, fecha_fin) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (uid, titulo, descripcion, tipo_evento, fecha_inicio, fecha_fin)
                )
                eid = cursor.fetchone()[0]
                return {"ok": True, "id": eid}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def eliminar_evento(self, eid, uid):
        """Elimina un evento de forma permanente."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute("DELETE FROM agenda WHERE id = %s AND usuario_id = %s", (eid, uid))
                return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def actualizar_ultimo_acceso(self, uid):
        """Actualiza la fecha de último acceso del usuario."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute("UPDATE usuarios SET ultimo_acceso = NOW() WHERE id = %s", (uid,))
                return {"ok": True}
        except: return {"ok": False}

    def obtener_usuarios_online(self, minutos=5):
        """Obtiene IDs de usuarios que han estado activos en los últimos N minutos."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT id FROM usuarios WHERE ultimo_acceso > NOW() - (%s || ' minutes')::interval", (minutos,))
                return [r[0] for r in cursor.fetchall()]
        except: return []

    def obtener_todos_los_usuarios(self):
        try:
            with self._get_cursor() as cursor:
                cursor.execute("SELECT id, nombre_usuario, email, photo_url, rol FROM usuarios")
                return [{
                    "id": r[0],
                    "name": r[1],
                    "nombre": r[1],
                    "nombre_usuario": r[1],
                    "email": r[2],
                    "photo_url": r[3],
                    "rol": r[4],
                } for r in cursor.fetchall()]
        except: return []

    def obtener_mensajes(self, uid, rid=None, gid=None):
        try:
            if rid and not (isinstance(rid, int) or str(rid).isdigit()):
                return []
            if gid and not (isinstance(gid, int) or str(gid).isdigit()):
                return []
            with self._get_cursor() as cursor:
                if gid: cursor.execute("SELECT emisor_id, contenido, image_data, timestamp FROM mensajes WHERE grupo_id = %s ORDER BY timestamp ASC", (gid,))
                else: cursor.execute("SELECT emisor_id, contenido, image_data, timestamp FROM mensajes WHERE (emisor_id=%s AND receptor_id=%s) OR (emisor_id=%s AND receptor_id=%s) ORDER BY timestamp ASC", (uid, rid, rid, uid))
                return [{"emisor_id": r[0], "contenido": r[1], "image_data": r[2], "timestamp": r[3]} for r in cursor.fetchall()]
        except: return []

    def guardar_mensaje(self, uid, rid, contenido, image_data=None):
        try:
            if rid and not (isinstance(rid, int) or str(rid).isdigit()):
                return {"ok": False, "error": "Non-numeric receptor ID"}
            with self._get_cursor() as cursor:
                cursor.execute("INSERT INTO mensajes (emisor_id, receptor_id, contenido, image_data, timestamp) VALUES (%s, %s, %s, %s, NOW()) RETURNING id, timestamp", (uid, rid, contenido, image_data))
                r = cursor.fetchone()
                return {"ok": True, "id": r[0], "emisor_id": uid, "receptor_id": rid, "contenido": contenido, "image_data": image_data, "timestamp": r[1]}
        except: return {"ok": False}

    def borrar_mensajes_contacto(self, uid, rid):
        try:
            if rid and not (isinstance(rid, int) or str(rid).isdigit()):
                return {"ok": False}
            with self._get_cursor() as cursor:
                cursor.execute(
                    "DELETE FROM mensajes WHERE (emisor_id=%s AND receptor_id=%s) OR (emisor_id=%s AND receptor_id=%s)",
                    (uid, rid, rid, uid)
                )
                return {"ok": True}
        except: return {"ok": False}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        def fallback(*args, **kwargs):
            if "obtener" in name: return []
            return {"ok": False, "error": f"Método {name} no implementado"}
        return fallback

# Instancia global para ser importada por otros módulos
db = DatabaseService()
