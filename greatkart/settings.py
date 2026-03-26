"""
Django settings for greatkart project.
"""

import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from django.contrib.messages import constants as messages


BASE_DIR = Path(__file__).resolve(strict=True).parent.parent


def load_env_file(path):
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def env(key, default=None):
    return os.environ.get(key, default)


def env_bool(key, default=False):
    value = env(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_list(key, default=""):
    return [item.strip() for item in env(key, default).split(",") if item.strip()]


def database_config_from_url(database_url):
    parsed = urlparse(database_url)
    query = parse_qs(parsed.query)

    if parsed.scheme in {"postgres", "postgresql"}:
        config = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "localhost",
            "PORT": str(parsed.port or "5432"),
        }
        sslmode = query.get("sslmode", [""])[0]
        if sslmode:
            config["OPTIONS"] = {"sslmode": sslmode}
        return config

    if parsed.scheme == "sqlite":
        db_path = parsed.path
        if db_path.startswith("/"):
            db_path = db_path[1:]
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / db_path if db_path else BASE_DIR / "db.sqlite3",
        }

    raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")


load_env_file(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", "unsafe-dev-secret-key")
DEBUG = env_bool("DJANGO_DEBUG", True)
IS_TEST_ENV = "test" in sys.argv
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", "").strip()
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
if RENDER_EXTERNAL_HOSTNAME:
    render_origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "category",
    "accounts",
    "store",
    "carts",
    "orders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "greatkart.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "greatkart.context_processors.site_meta",
                "category.context_processors.menu_links",
                "carts.context_processors.counter",
            ],
        },
    },
]

WSGI_APPLICATION = "greatkart.wsgi.application"

AUTH_USER_MODEL = "accounts.Account"

if env("DATABASE_URL"):
    DATABASES = {
        "default": database_config_from_url(env("DATABASE_URL")),
    }
elif env("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB"),
            "USER": env("POSTGRES_USER", ""),
            "PASSWORD": env("POSTGRES_PASSWORD", ""),
            "HOST": env("POSTGRES_HOST", "localhost"),
            "PORT": env("POSTGRES_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "en"
LANGUAGES = (
    ("en", "English"),
    ("it", "Italian"),
)
TIME_ZONE = env("DJANGO_TIME_ZONE", "Asia/Karachi")
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]


STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
staticfiles_backend = "whitenoise.storage.CompressedStaticFilesStorage"
if DEBUG or IS_TEST_ENV:
    staticfiles_backend = "django.contrib.staticfiles.storage.StaticFilesStorage"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": staticfiles_backend,
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MESSAGE_TAGS = {
    messages.ERROR: "danger",
}

EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@greatkart.local")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST_USER
    else "django.core.mail.backends.console.EmailBackend",
)

SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", bool(RENDER_EXTERNAL_HOSTNAME))
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", bool(RENDER_EXTERNAL_HOSTNAME))
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", bool(RENDER_EXTERNAL_HOSTNAME))

LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"

SITE_NAME = env("SITE_NAME", "GreatKart")
SITE_DESCRIPTION = env("SITE_DESCRIPTION", "A modern Django e-commerce storefront")
SITE_DOMAIN = env(
    "SITE_DOMAIN",
    f"https://{RENDER_EXTERNAL_HOSTNAME}" if RENDER_EXTERNAL_HOSTNAME else "http://localhost:8000",
)
STRIPE_PUBLIC_KEY = env("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", "")
