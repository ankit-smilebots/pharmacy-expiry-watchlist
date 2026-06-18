"""
Django settings for the Pharmacy Expiry Watchlist project.

Configuration is driven by environment variables so the same code runs both
locally and on a host (Render / Railway / Fly / a VPS). In development the
sensible defaults below are enough — no environment setup required.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load a local .env file if present (never committed). On a host the platform
# provides the environment variables directly.
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# --- Core -----------------------------------------------------------------

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-dev-only-key-change-me-before-deploying-anywhere",
)

DEBUG = env_bool("DEBUG", default=True)

# In DEBUG we accept localhost; in production set ALLOWED_HOSTS via env.
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
if DEBUG:
    ALLOWED_HOSTS += ["localhost", "127.0.0.1", "0.0.0.0"]

# Needed for HTTPS form posts (CSRF) once deployed, e.g.
# CSRF_TRUSTED_ORIGINS=https://your-app.onrender.com
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# Render sets this automatically — wire it up so deploys work without having to
# hardcode the generated hostname.
_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if _render_host:
    ALLOWED_HOSTS.append(_render_host)
    CSRF_TRUSTED_ORIGINS.append(f"https://{_render_host}")

# The single "simple password" that unlocks the watchlist. Override in env.
WATCHLIST_PASSWORD = os.environ.get("WATCHLIST_PASSWORD", "iqbal123")


# --- Applications ---------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "watchlist",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serves static files in production without a separate server.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pharmacy.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "pharmacy.wsgi.application"


# --- Database -------------------------------------------------------------
# Defaults to a local SQLite file. Set DATABASE_URL (e.g. a Postgres URL) on
# the host to use a managed database instead.

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# --- Password validation --------------------------------------------------
# (Applies to Django's auth users / the admin, not the simple unlock gate.)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Internationalization -------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True


# --- Static files ---------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# In production, hash + compress static files (needs `collectstatic`). In
# development use the plain finder so the dev server and tests work without it.
_static_backend = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
    if DEBUG
    else "whitenoise.storage.CompressedManifestStaticFilesStorage"
)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": _static_backend},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Security (only enforced when DEBUG is off) ---------------------------

if not DEBUG:
    # Respect the X-Forwarded-Proto header set by hosting proxies.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
