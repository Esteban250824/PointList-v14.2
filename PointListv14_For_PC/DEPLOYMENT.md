# 🚀 Guía de Despliegue y Producción

Instrucciones para desplegar PointList en producción y mantenerlo operativo.

---

## 📋 Tabla de Contenidos
1. [Pre-Deploy Checklist](#pre-deploy-checklist)
2. [Despliegue Web](#despliegue-web)
3. [Despliegue Móvil](#despliegue-móvil)
4. [Configuración de Producción](#configuración-de-producción)
5. [Monitoreo y Mantenimiento](#monitoreo-y-mantenimiento)
6. [Backup y Recuperación](#backup-y-recuperación)
7. [Escalamiento](#escalamiento)

---

## ✅ Pre-Deploy Checklist

Antes de desplegar a producción:

### Código
- [ ] Todas las pruebas pasan
- [ ] Sin errores de compilación
- [ ] Sin warnings no resueltos
- [ ] Código revisado por al menos 2 personas
- [ ] No hay credenciales en el código
- [ ] Variables de entorno configuradas
- [ ] CHANGELOG actualizado

### Base de Datos
- [ ] Esquema actualizado
- [ ] Migraciones probadas
- [ ] Backups automáticos configurados
- [ ] Índices optimizados
- [ ] Connection pooling configurado

### Seguridad
- [ ] SSL/TLS habilitado
- [ ] CORS configurado correctamente
- [ ] Rate limiting implementado
- [ ] Validación de input en todas partes
- [ ] Contraseñas hasheadas y saladas
- [ ] API keys rotadas

### Performance
- [ ] Aplicación testada bajo carga
- [ ] Caché configurado
- [ ] Imágenes optimizadas
- [ ] BD indexada correctamente
- [ ] Queries optimizadas

### Documentación
- [ ] README actualizado
- [ ] API documentada
- [ ] Runbooks de emergencia listos
- [ ] Contactos de soporte documentados

---

## 🌐 Despliegue Web

### Opción 1: Heroku (Recomendado para inicio)

#### Requisitos Previos
```bash
# Instalar Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

heroku login
heroku create pointlist-app
```

#### Procfile
Crear archivo `Procfile`:
```
web: flet run --web --port=$PORT
```

#### Setup Variables de Entorno
```bash
heroku config:set DB_HOST=your-db-host
heroku config:set DB_NAME=pointlist
heroku config:set DB_USER=pointlist_user
heroku config:set DB_PASSWORD=your_secure_password
heroku config:set OPENAI_API_KEY=sk-xxxxx
heroku config:set APP_DEBUG=False
```

#### Deploy
```bash
git push heroku main
```

#### Monitoreo
```bash
# Ver logs
heroku logs --tail

# Escalar dynos
heroku ps:scale web=2

# Reiniciar
heroku restart
```

---

### Opción 2: DigitalOcean App Platform

#### Crear App
```bash
# https://www.digitalocean.com/products/app-platform

# 1. Conectar repositorio GitHub
# 2. Configurar:
#    - Comando: flet run --web
#    - Puerto: 8000
#    - Variables de entorno

# 3. Deplegar
```

#### Configurar PostgreSQL
```bash
# Crear base de datos managed
# En DigitalOcean console:
# - Databases → Create Database Cluster
# - Tipo: PostgreSQL
# - Conectar a app

# Environment Variables:
DB_HOST=<your-db-host>
DB_PORT=5432
DB_NAME=pointlist
DB_USER=pointlist_user
DB_PASSWORD=<secure-password>
```

---

### Opción 3: AWS (ECS + RDS)

#### Crear Docker Image
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["flet", "run", "--web", "--port", "8000"]
```

#### Build y Push
```bash
# Build
docker build -t pointlist:latest .

# Push a ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker tag pointlist:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/pointlist:latest

docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/pointlist:latest
```

#### Deploy ECS
```bash
# Crear cluster ECS
# Crear task definition
# Crear service
# Conectar RDS
```

---

## 📱 Despliegue Móvil

### Android - Google Play Store

#### Preparar APK Firmado
```bash
# 1. Crear keystore
keytool -genkey -v -keystore pointlist-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias pointlist-key

# 2. Compilar APK
flet run --android --output ./build/pointlist.apk

# 3. Firmar APK
jarsigner -verbose -sigalg MD5withRSA -digestalg SHA1 \
  -keystore pointlist-keystore.jks \
  build/pointlist.apk pointlist-key
```

#### Upload a Play Store
```bash
# 1. Crear Google Play Developer Account ($25)
# 2. Crear aplicación
# 3. Completar información de tienda:
#    - Título
#    - Descripción
#    - Capturas de pantalla
#    - Icono
#    - Privacidad
# 4. Upload APK
# 5. Enviar a revisión
```

### iOS - Apple App Store

#### Requisitos
- Mac con Xcode
- Apple Developer Account ($99/año)
- Certificados de desarrollador

#### Compilar
```bash
# 1. Compilar app para iOS
flet run --ios

# 2. Seguir instrucciones de Xcode
# 3. Archive y upload a TestFlight
# 4. Submit a App Store
```

---

## ⚙️ Configuración de Producción

### variables de Entorno (.env)
```env
# Database - Producción
DB_HOST=prod-db.example.com
DB_PORT=5432
DB_NAME=pointlist_prod
DB_USER=pointlist_prod_user
DB_PASSWORD=VERY_SECURE_PASSWORD_HERE

# OpenAI - Producción
OPENAI_API_KEY=sk-prod-key-here

# Aplicación
APP_DEBUG=False
DEFAULT_LANGUAGE=es
TIMEZONE=America/Bogota

# Seguridad
SECRET_KEY=very-long-random-secret-key
ALLOWED_HOSTS=pointlist.app,www.pointlist.app

# Email (para recuperación de contraseña)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=noreply@pointlist.app
EMAIL_PASSWORD=app_password_here

# Monitoreo
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
LOG_LEVEL=WARNING
```

### SSL/TLS
```bash
# Usando Let's Encrypt (gratuito)

# En DigitalOcean/Heroku: Automático
# En AWS: Use AWS Certificate Manager
# En servidor propio:

# Instalar certbot
sudo apt-get install certbot

# Obtener certificado
sudo certbot certonly --standalone -d pointlist.app -d www.pointlist.app

# Renovación automática
sudo systemctl enable certbot.timer
```

### Rate Limiting
```python
# En main.py o servicio

from flask_limiter import Limiter

limiter = Limiter(
    key_func=lambda: request.remote_addr,
    default_limits=["200 per day", "50 per hour"]
)

# Aplicar a rutas críticas
@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    pass
```

---

## 📊 Monitoreo y Mantenimiento

### Health Check Endpoint
```python
# Agregar endpoint de health check

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "db": check_database(),
        "api": check_external_apis()
    }
```

### Logs
```bash
# Configurar logging centralizado

# Opción: Sentry para error tracking
import sentry_sdk
sentry_sdk.init("https://xxxxx@sentry.io/xxxxx")

# Opción: ELK Stack (Elasticsearch, Logstash, Kibana)
# Opción: CloudWatch (AWS)
```

### Uptime Monitoring
```bash
# Usar servicio externo:
# - UptimeRobot (gratuito)
# - Datadog
# - New Relic

# Configurar alertas para:
# - 500+ errors
# - Respuesta > 5s
# - API rate limits
# - Database connection issues
```

### Performance Monitoring
```python
# Agregar métricas

from prometheus_client import Counter, Histogram

request_count = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.route('/api/users')
def get_users():
    with request_duration.time():
        request_count.inc()
        # ... código
```

---

## 💾 Backup y Recuperación

### Backup Automático PostgreSQL

```bash
#!/bin/bash
# backup.sh - Script de backup diario

BACKUP_DIR="/backups/pointlist"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="pointlist"
DB_USER="pointlist_user"

# Crear backup
pg_dump -U $DB_USER $DB_NAME > "$BACKUP_DIR/db_$DATE.sql"

# Comprimir
gzip "$BACKUP_DIR/db_$DATE.sql"

# Eliminar backups viejos (más de 30 días)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

# Upload a storage externo (S3, Google Cloud, etc)
aws s3 cp "$BACKUP_DIR/db_$DATE.sql.gz" s3://pointlist-backups/

echo "Backup completado: db_$DATE.sql.gz"
```

### Configurar Cron Job
```bash
# Agregar a crontab
# crontab -e

# Backup diario a las 2:00 AM
0 2 * * * /scripts/backup.sh

# Backup semanal a las 3:00 AM cada domingo
0 3 * * 0 /scripts/backup-weekly.sh
```

### Restaurar desde Backup
```bash
# Listar backups
ls -lh /backups/pointlist/

# Restaurar
gunzip < /backups/pointlist/db_20260703_020000.sql.gz | psql -U pointlist_user pointlist
```

---

## 📈 Escalamiento

### Vertical Scaling (Aumentar recursos)
```bash
# Más CPU/RAM
# Heroku: heroku ps:type Standard-2X

# DigitalOcean: Aumentar droplet size

# AWS: Cambiar instancia a mayor size
```

### Horizontal Scaling (Más instancias)
```bash
# Heroku
heroku ps:scale web=3

# Kubernetes (si aplica)
kubectl scale deployment pointlist --replicas=5

# Load Balancing
# - Heroku: Automático
# - AWS: Use ELB / ALB
# - DigitalOcean: Use Load Balancer
```

### Database Optimization

#### Indexes
```sql
-- Crear índices para queries frecuentes
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_asignaciones_usuario_id ON asignaciones(usuario_id);
CREATE INDEX idx_mensajes_receptor_id ON mensajes(receptor_id);

-- Verificar índices
SELECT * FROM pg_indexes WHERE schemaname = 'public';
```

#### Query Optimization
```python
# ❌ N+1 queries problem
usuarios = db.get_usuarios()
for user in usuarios:
    notas = db.get_notas(user.id)  # Query para cada usuario

# ✅ Usar JOIN
query = """
    SELECT u.*, n.* FROM usuarios u
    LEFT JOIN asignaciones n ON u.id = n.usuario_id
"""
```

#### Connection Pooling
```python
# En services/database_service.py

from pg8000 import connect
from contextlib import contextmanager

class DatabaseService:
    def __init__(self, pool_size=10):
        self.pool = create_pool(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            min_pool_size=5,
            max_pool_size=pool_size
        )
    
    @contextmanager
    def get_connection(self):
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
```

---

## 🚨 Incident Response

### Procedure Ante Errores

1. **Detectar**: Alertas automáticas disparan
2. **Notificar**: Equipo recibe notificación
3. **Investigar**: Revisar logs y métricas
4. **Mitigar**: Rollback o hotfix rápido
5. **Resolver**: Fix definitivo
6. **Post-Mortem**: Aprender y mejorar

### Rollback Rápido
```bash
# Heroku
heroku releases
heroku rollback v123

# Git
git revert HEAD
git push production

# Docker
docker pull pointlist:stable
docker stop pointlist
docker run pointlist:stable
```

### Comunicación
```bash
# Template de notificación
📢 INCIDENT: [Servicio] está down

Impacto: [descripción]
Causa: [investigación preliminar]
Estado: [En investigación / Mitigando / Resuelto]
ETA: [tiempo estimado de resolución]

Actualizaciones en: status.pointlist.app
```

---

## 📞 Contactos y Escalación

```
NIVEL 1 - Soporte Técnico
Teléfono: +57-1-XXXX-XXXX
Email: soporte@pointlist.app
Disponibilidad: L-V 8:00-18:00

NIVEL 2 - Ingeniero Senior
Nombre: [Nombre]
Teléfono: +57-3XX-XXXX-XXXX
Email: [email]
Disponibilidad: 24/7 emergencias

NIVEL 3 - Management
Nombre: [Nombre]
Teléfono: +57-3XX-XXXX-XXXX
Email: [email]
```

---

## 🔗 Recursos Útiles

- [Heroku Deployment Guide](https://devcenter.heroku.com/)
- [AWS Best Practices](https://docs.aws.amazon.com/)
- [PostgreSQL Production Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Flet Production Deployment](https://flet.dev/docs/deployment)
- [OWASP Security Guidelines](https://owasp.org/)

---

## ✅ Checklist Post-Deploy

- [ ] App accesible en URL de producción
- [ ] Database conectando correctamente
- [ ] Backups ejecutándose
- [ ] Monitoreo activo
- [ ] Alertas funcionando
- [ ] Team notificado
- [ ] Documentación actualizada
- [ ] Post-mortem completado (si aplicaba)

---

**Última actualización**: Julio 2026
**Versión**: v1.0
