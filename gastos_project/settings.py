"""
Configuración de Django para el proyecto gastos_project.

Esta versión está adaptada para producción y compatible con despliegues
en Koyeb u otras plataformas PaaS. Se emplean variables de entorno para
parámetros sensibles y se incluye WhiteNoise para servir archivos
estáticos sin necesidad de nginx.
"""

import os
from pathlib import Path

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Clave secreta: usa una variable de entorno en producción
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-key")

# Modo debug: desactiva en producción
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

# Hosts permitidos: separados por comas en la variable de entorno
ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS",
    "localhost,127.0.0.1"
).split(",")

# Aplicaciones instaladas
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise permite servir archivos estáticos en producción
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# URL raíz
ROOT_URLCONF = "gastos_project.urls"

# Plantillas
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Objeto WSGI
WSGI_APPLICATION = "gastos_project.wsgi.application"
"""
# Base de datos: usa PostgreSQL en Koyeb o SQLite por defecto
DATABASES = {
    "default": {
        # Motor por defecto: PostgreSQL; si no se definen las variables,
        # se usará una base de datos SQLite local (desarrollo).
        "ENGINE": "django.db.backends.postgresql"
        if os.environ.get("POSTGRES_DB")
        else "django.db.backends.sqlite3",
        "NAME": os.environ.get(
            "POSTGRES_DB",
            BASE_DIR / "db.sqlite3"
        ),
        "USER": os.environ.get("POSTGRES_USER", ""),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}
"""

# gastos_project/settings.py
from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

DB_URL = os.environ.get("DATABASE_URL", "").strip()

if DB_URL:
    # Fuerza SSL solo si es Postgres
    SSL_REQUIRED = DB_URL.startswith(("postgres://", "postgresql://"))
    DATABASES = {
        "default": dj_database_url.parse(
            DB_URL,
            conn_max_age=600,
            ssl_require=SSL_REQUIRED,
        )
    }
else:
    # Local por defecto: SQLite sin opciones raras
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }



# Validadores de contraseña
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internacionalización
LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

# Archivos estáticos
STATIC_URL = "/static/"
# Carpeta donde se recopilan los archivos al ejecutar collectstatic
STATIC_ROOT = BASE_DIR / "staticfiles"
# Almacenamiento que comprime y versiona los estáticos (WhiteNoise)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Clave primaria por defecto
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging básico
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
