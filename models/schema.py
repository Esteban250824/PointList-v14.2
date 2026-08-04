"""
models/schema.py
PointList v0.14.27
Definición del esquema de la base de datos PostgreSQL con soporte para Roles.
"""

CREATE_TABLES_SQL = [
    # 1. Tabla de usuarios con ROL
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id               SERIAL PRIMARY KEY,
        nombre_usuario   VARCHAR(100)        NOT NULL,
        email            VARCHAR(255) UNIQUE NOT NULL,
        password_hash    VARCHAR(255)        NOT NULL,
        salt             VARCHAR(255)        NOT NULL,
        rol              VARCHAR(20)         DEFAULT 'estudiante', -- 'estudiante' o 'profesor'
        photo_url        TEXT                DEFAULT '',
        bio              TEXT                DEFAULT '',
        telefono         VARCHAR(30)         DEFAULT '',
        ubicacion        VARCHAR(150)        DEFAULT '',
        sitio_web        VARCHAR(255)        DEFAULT '',
        fecha_registro   TIMESTAMP           DEFAULT NOW(),
        ultimo_acceso    TIMESTAMP           DEFAULT NOW()
    );
    """,

    # 2. Tabla de asignaciones / tareas
    """
    CREATE TABLE IF NOT EXISTS asignaciones (
        id              SERIAL PRIMARY KEY,
        usuario_id      INTEGER     NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        titulo          VARCHAR(255) NOT NULL,
        descripcion     TEXT         DEFAULT '',
        asignatura      VARCHAR(100) DEFAULT '',
        fecha_entrega   TIMESTAMP,
        completada      BOOLEAN      DEFAULT FALSE,
        prioridad       VARCHAR(20)  DEFAULT 'normal',
        creado_en       TIMESTAMP    DEFAULT NOW()
    );
    """,

    # 3. Tabla de agenda / eventos de calendario
    """
    CREATE TABLE IF NOT EXISTS agenda (
        id              SERIAL PRIMARY KEY,
        usuario_id      INTEGER      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        titulo          VARCHAR(255) NOT NULL,
        descripcion     TEXT         DEFAULT '',
        fecha_inicio    TIMESTAMP    NOT NULL,
        fecha_fin       TIMESTAMP    NOT NULL,
        tipo_evento     VARCHAR(50)  DEFAULT 'General',
        completado      BOOLEAN      DEFAULT FALSE,
        creado_en       TIMESTAMP    DEFAULT NOW()
    );
    """,

    # 4. Tabla de notas / calificaciones con ASIGNACIÓN DE PROFESOR
    """
    CREATE TABLE IF NOT EXISTS notas (
        id              SERIAL PRIMARY KEY,
        usuario_id      INTEGER        NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        profesor_id     INTEGER        REFERENCES usuarios(id) ON DELETE SET NULL,
        asignatura      VARCHAR(100)   NOT NULL,
        calificacion    DECIMAL(4, 2)  NOT NULL,
        fecha           DATE           NOT NULL DEFAULT CURRENT_DATE,
        comentarios     TEXT           DEFAULT '',
        timestamp       BIGINT         DEFAULT EXTRACT(EPOCH FROM NOW()),
        creado_en       TIMESTAMP      DEFAULT NOW()
    );
    """,

    # 5. Tabla de técnicas de estudio (catálogo global)
    """
    CREATE TABLE IF NOT EXISTS tecnicas_estudio (
        id              SERIAL PRIMARY KEY,
        titulo          VARCHAR(255) NOT NULL,
        descripcion     TEXT         NOT NULL,
        categoria       VARCHAR(100) DEFAULT 'General',
        icon_url        TEXT         DEFAULT '',
        CONSTRAINT unique_titulo UNIQUE (titulo)
    );
    """,

    # 6. Tabla de favoritos de técnicas por usuario
    """
    CREATE TABLE IF NOT EXISTS tecnicas_favoritas (
        usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        tecnica_id      INTEGER NOT NULL REFERENCES tecnicas_estudio(id) ON DELETE CASCADE,
        PRIMARY KEY (usuario_id, tecnica_id)
    );
    """,

    # 7. Tabla de mensajería
    """
    CREATE TABLE IF NOT EXISTS mensajes (
        id              SERIAL PRIMARY KEY,
        emisor_id       INTEGER  NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        receptor_id     INTEGER,
        grupo_id        INTEGER,
        contenido       TEXT     NOT NULL,
        image_data      TEXT,
        timestamp       TIMESTAMP DEFAULT NOW(),
        leido           BOOLEAN   DEFAULT FALSE,
        es_grupo        BOOLEAN   DEFAULT FALSE
    );
    """,

    # 8. Tabla de grupos de mensajería
    """
    CREATE TABLE IF NOT EXISTS grupos (
        id              SERIAL PRIMARY KEY,
        nombre          VARCHAR(255) NOT NULL,
        creador_id      INTEGER      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        creado_en       TIMESTAMP    DEFAULT NOW()
    );
    """,

    # 9. Tabla de miembros de grupos
    """
    CREATE TABLE IF NOT EXISTS grupo_miembros (
        grupo_id        INTEGER NOT NULL REFERENCES grupos(id) ON DELETE CASCADE,
        usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        PRIMARY KEY (grupo_id, usuario_id)
    );
    """,

    # 10. Tabla de historial del chatbot
    """
    CREATE TABLE IF NOT EXISTS historial_chatbot (
        id              SERIAL PRIMARY KEY,
        usuario_id      INTEGER   NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        session_id      VARCHAR(100) DEFAULT 'default',
        pregunta        TEXT      NOT NULL,
        respuesta       TEXT      NOT NULL,
        modelo          VARCHAR(100) DEFAULT 'deepseek-chat',
        timestamp       TIMESTAMP    DEFAULT NOW()
    );
    """,
    
    # 12. Tabla de sesiones de chatbot
    """
    CREATE TABLE IF NOT EXISTS chatbot_sesiones (
        id              SERIAL PRIMARY KEY,
        usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
        session_id      VARCHAR(100) NOT NULL UNIQUE,
        titulo          VARCHAR(255) DEFAULT 'Nueva conversación',
        actualizado_en  TIMESTAMP DEFAULT NOW()
    );
    """,

    # 11. Tabla de configuración de usuario
    """
    CREATE TABLE IF NOT EXISTS configuracion_usuario (
        usuario_id          INTEGER PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
        tema                VARCHAR(20)  DEFAULT 'claro',
        idioma              VARCHAR(10)  DEFAULT 'es',
        voz_pointbit        BOOLEAN      DEFAULT TRUE,
        video_intro_visto   BOOLEAN      DEFAULT FALSE,
        notificaciones      BOOLEAN      DEFAULT TRUE,
        actualizado_en      TIMESTAMP    DEFAULT NOW()
    );
    """,
]

SEED_TECNICAS_SQL = """
INSERT INTO tecnicas_estudio (titulo, descripcion, categoria, icon_url)
VALUES
    ('Técnica Pomodoro',
     'Divide tu tiempo de estudio en bloques de 25 minutos de trabajo intenso seguidos de 5 minutos de descanso. Después de 4 bloques, toma un descanso largo de 15-30 minutos.',
     'Recientes',
     'https://cdn-icons-png.flaticon.com/512/2972/2972531.png'),

    ('Método SMART',
     'Define objetivos Específicos, Medibles, Alcanzables, Relevantes y con un Tiempo definido. Ideal para planificar proyectos académicos.',
     'Recientes',
     'https://cdn-icons-png.flaticon.com/512/3135/3135715.png'),

    ('Mapas Mentales',
     'Crea diagramas visuales que conectan conceptos clave alrededor de una idea central. Facilita la comprensión de relaciones entre temas.',
     'Todos',
     'https://cdn-icons-png.flaticon.com/512/2103/2103633.png'),

    ('Método SQ3R',
     'Survey (Explorar), Question (Preguntar), Read (Leer), Recite (Recitar) y Review (Revisar). Estrategia para lectura activa.',
     'Todos',
     'https://cdn-icons-png.flaticon.com/512/2436/2436874.png'),

    ('Repetición Espaciada',
     'Revisa el material en intervalos de tiempo crecientes para aprovechar el efecto del espaciado. Maximiza la retención a largo plazo.',
     'Todos',
     'https://cdn-icons-png.flaticon.com/512/3132/3132693.png'),

    ('Método Feynman',
     'Aprende un concepto, explícalo con palabras simples como si se lo enseñaras a alguien sin conocimientos previos.',
     'Todos',
     'https://cdn-icons-png.flaticon.com/512/3176/3176395.png')
ON CONFLICT (titulo) DO UPDATE SET 
    descripcion = EXCLUDED.descripcion,
    categoria = EXCLUDED.categoria,
    icon_url = EXCLUDED.icon_url;
"""
