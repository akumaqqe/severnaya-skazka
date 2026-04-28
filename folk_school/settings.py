from pathlib import Path

import environ


BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, True))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env(
    "SECRET_KEY",
    default="django-insecure-change-me-before-production",
)
DEBUG = env.bool("DEBUG", default=True)

render_external_hostname = env("RENDER_EXTERNAL_HOSTNAME", default="")

allowed_hosts = [
    host.strip()
    for host in env.list(
        "ALLOWED_HOSTS",
        default=["127.0.0.1", "localhost", "testserver"],
    )
    if host.strip()
]
csrf_trusted_origins = [
    origin.strip()
    for origin in env.list("CSRF_TRUSTED_ORIGINS", default=[])
    if origin.strip()
]

if render_external_hostname:
    if render_external_hostname not in allowed_hosts:
        allowed_hosts.append(render_external_hostname)
    render_origin = f"https://{render_external_hostname}"
    if render_origin not in csrf_trusted_origins:
        csrf_trusted_origins.append(render_origin)

ALLOWED_HOSTS = allowed_hosts
CSRF_TRUSTED_ORIGINS = csrf_trusted_origins


def build_database_config():
    database_url = env("DATABASE_URL", default="")
    if database_url:
        return env.db("DATABASE_URL")

    db_engine = env("DB_ENGINE", default="mysql").lower()

    if db_engine == "mysql":
        return {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME", default="folk_school"),
            "USER": env("DB_USER", default="root"),
            "PASSWORD": env("DB_PASSWORD", default=""),
            "HOST": env("DB_HOST", default="127.0.0.1"),
            "PORT": env("DB_PORT", default="3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }

    if db_engine in {"postgres", "postgresql", "pgsql"}:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", default="folk_school"),
            "USER": env("DB_USER", default="postgres"),
            "PASSWORD": env("DB_PASSWORD", default=""),
            "HOST": env("DB_HOST", default="127.0.0.1"),
            "PORT": env("DB_PORT", default="5432"),
        }

    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "folk_school.urls"

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
    }
]

WSGI_APPLICATION = "folk_school.wsgi.application"

DATABASES = {
    "default": build_database_config()
}

DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 6,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"

USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

if DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"
LOGIN_URL = "login"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=False,
)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
