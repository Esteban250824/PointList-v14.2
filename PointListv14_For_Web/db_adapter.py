"""
db_adapter.py - Conector de Base de Datos para PointList Web
Soporta PostgreSQL mediante DATABASE_URL y SQLite/Memory como respaldo.
"""

import os
import sqlite3
import json
import time
from datetime import datetime
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL")

class DatabaseAdapter:
    def __init__ (self):
        self.use_pg = False
        self.sqlite_file = os.path.join(os.path.dirname(__file__), "pointlist_local.db")
        self._init_db()

    def _get_connection(self):
        if DATABASE_URL and "postgresql://" in DATABASE_URL:
            try:
                import pg8000
                url = urlparse(DATABASE_URL)
                import ssl
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
                conn = pg8000.connect(
                    user=url.username,
                    password=url.password,
                    host=url.hostname,
                    port=url.port or 5432,
                    database=url.path[1:],
                    ssl_context=ssl_ctx
                )
                self.use_pg = True
                return conn
            except Exception as e:
                print(f"[DB] PostgreSQL falló, usando SQLite local: {e}")

        self.use_pg = False
        conn = sqlite3.connect(self.sqlite_file, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        if self.use_pg:
            # Esquema PostgreSQL
            sqls = [
                """CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nombre_usuario VARCHAR(100) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    salt VARCHAR(255) NOT NULL,
                    rol VARCHAR(20) DEFAULT 'estudiante',
                    photo_url TEXT DEFAULT '',
                    bio TEXT DEFAULT '',
                    telefono VARCHAR(30) DEFAULT '',
                    ubicacion VARCHAR(150) DEFAULT '',
                    sitio_web VARCHAR(255) DEFAULT '',
                    fecha_registro TIMESTAMP DEFAULT NOW()
                );""",
                """CREATE TABLE IF NOT EXISTS notas (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER NOT NULL,
                    asignatura VARCHAR(100) NOT NULL,
                    calificacion DECIMAL(4, 2) NOT NULL,
                    fecha DATE DEFAULT CURRENT_DATE,
                    comentarios TEXT DEFAULT ''
                );""",
                """CREATE TABLE IF NOT EXISTS agenda (
                    id SERIAL PRIMARY KEY,
                    usuario_id INTEGER NOT NULL,
                    titulo VARCHAR(255) NOT NULL,
                    descripcion TEXT DEFAULT '',
                    fecha_inicio TIMESTAMP NOT NULL,
                    fecha_fin TIMESTAMP NOT NULL,
                    tipo_evento VARCHAR(50) DEFAULT 'General',
                    prioridad VARCHAR(20) DEFAULT 'normal',
                    completado BOOLEAN DEFAULT FALSE
                );""",
                """CREATE TABLE IF NOT EXISTS mensajes (
                    id SERIAL PRIMARY KEY,
                    emisor_id INTEGER NOT NULL,
                    receptor_id INTEGER,
                    contenido TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT NOW()
                );"""
            ]
        else:
            # Esquema SQLite
            sqls = [
                """CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_usuario TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    rol TEXT DEFAULT 'estudiante',
                    photo_url TEXT DEFAULT '',
                    bio TEXT DEFAULT '',
                    telefono TEXT DEFAULT '',
                    ubicacion TEXT DEFAULT '',
                    sitio_web TEXT DEFAULT '',
                    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
                );""",
                """CREATE TABLE IF NOT EXISTS notas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    asignatura TEXT NOT NULL,
                    calificacion REAL NOT NULL,
                    fecha TEXT DEFAULT CURRENT_DATE,
                    comentarios TEXT DEFAULT ''
                );""",
                """CREATE TABLE IF NOT EXISTS agenda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    titulo TEXT NOT NULL,
                    descripcion TEXT DEFAULT '',
                    fecha_inicio TEXT NOT NULL,
                    fecha_fin TEXT NOT NULL,
                    tipo_evento TEXT DEFAULT 'General',
                    prioridad TEXT DEFAULT 'normal',
                    completado INTEGER DEFAULT 0
                );""",
                """CREATE TABLE IF NOT EXISTS mensajes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    emisor_id INTEGER NOT NULL,
                    receptor_id INTEGER,
                    contenido TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );"""
            ]

        for s in sqls:
            try:
                cursor.execute(s)
            except Exception as e:
                print(f"[DB Init Error]: {e}")

        conn.commit()
        conn.close()

db_adapter = DatabaseAdapter()
