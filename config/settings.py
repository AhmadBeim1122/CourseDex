"""
Django settings for the iSchool LMS project.

This project replaces the original PHP/MySQL "iSchool" application.
It keeps the same core idea (a learning management system) but is
reshaped into a simple two-sided app:

    * a Django admin panel (Jazzmin themed) where the site owner manages
      Programs -> Semesters -> Subjects -> Topics -> Past Papers
    * a public, read-only frontend (no accounts, no login/signup, no
      payments) where visitors browse that content for free

Settings are environment-driven (see `.env.example`) so the same
codebase runs in development and production.
"""

from pathlib import Path
from decouple import Config, RepositoryEnv, RepositoryEmpty, Csv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    config = Config(RepositoryEnv(str(_env_file)))
else:
    config = Config(RepositoryEmpty())

SECRET_KEY = config(
    "DJANGO_SECRET_KEY",
    default="django-insecure-change-this-key-before-deploying-to-production",
)
DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config(
    "DJANGO_ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv()
)
ALLOWED_HOSTS += [".vercel.app"]
CSRF_TRUSTED_ORIGINS = config(
    "DJANGO_CSRF_TRUSTED_ORIGINS", default="", cast=Csv()
)

# Vercel (and most serverless platforms) terminate HTTPS at the edge and
# forward plain HTTP internally — without this, Django thinks every
# request is insecure, which breaks CSRF/secure cookies on POST requests.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

SITE_NAME = config("SITE_NAME", default="CourseDex")
SITE_INITIALS = config("SITE_INITIALS", default="CX")
SITE_DOMAIN = config("SITE_DOMAIN", default="127.0.0.1:8000")
SITE_DESCRIPTION = config(
    "SITE_DESCRIPTION",
    default="Free study notes, subject outlines and solved past papers "
    "for BSIT, BSCS and other university programs.",
)

# Google AdSense (optional). Leave blank until the site is approved.
ADSENSE_CLIENT_ID = config("ADSENSE_CLIENT_ID", default="")
GOOGLE_SITE_VERIFICATION = config("GOOGLE_SITE_VERIFICATION", default="")
GOOGLE_ANALYTICS_ID = config("GOOGLE_ANALYTICS_ID", default="")

OCR_TIMEOUT_SECONDS = config("OCR_TIMEOUT_SECONDS", default=90, cast=int)
TESSERACT_CMD = config("TESSERACT_CMD", default="")

OLLAMA_API_KEY = config("OLLAMA_API_KEY", default="")
OLLAMA_MODEL = config("OLLAMA_MODEL", default="gpt-oss:20b-cloud")

GROQ_API_KEY = config("GROQ_API_KEY", default="")
GROQ_MODEL = config("GROQ_MODEL", default="llama-3.1-8b-instant")

GEMINI_API_KEY = config("GEMINI_API_KEY", default="")
GEMINI_MODEL = config("GEMINI_MODEL", default="gemini-flash-latest")

OPENROUTER_API_KEY = config("OPENROUTER_API_KEY", default="")
OPENROUTER_MODEL = config("OPENROUTER_MODEL", default="meta-llama/llama-3.1-8b-instruct:free")

YOUTUBE_API_KEY = config("YOUTUBE_API_KEY", default="")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Jazzmin must be listed before django.contrib.admin
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",

    # Third party
    "django_htmx",

    # Local apps
    "apps.core",
    "apps.academics",
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
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "apps.core.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Defaults to SQLite for zero-config local development. The original PHP
# project used MySQL/MariaDB (see SQL/lms_db.sql from the legacy project) -
# to use MySQL in production, set DB_ENGINE=mysql and the DB_* variables in
# .env, then `pip install mysqlclient`.
import dj_database_url

DATABASE_URL = config("DATABASE_URL", default="")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
else:
    DB_ENGINE = config("DB_ENGINE", default="sqlite")
    if DB_ENGINE == "mysql":
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.mysql",
                "NAME": config("DB_NAME", default="lms_db"),
                "USER": config("DB_USER", default="root"),
                "PASSWORD": config("DB_PASSWORD", default=""),
                "HOST": config("DB_HOST", default="127.0.0.1"),
                "PORT": config("DB_PORT", default="3306"),
                "OPTIONS": {"charset": "utf8mb4"},
            }
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
# ---------------------------------------------------------------------------
# Password validation (used only for the staff/admin login)
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = config("TIME_ZONE", default="Asia/Karachi")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Security (tightened automatically once DEBUG=False)
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# Auth redirects (staff-only login, used solely for /admin/)
# ---------------------------------------------------------------------------
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"

# ---------------------------------------------------------------------------
# Content limits (kept in one place so admin validation & docs agree)
# ---------------------------------------------------------------------------
MIN_TOPIC_IMAGES = 0     # a topic may have no images
MAX_TOPIC_IMAGES = 6     # ...but never more than 6 (per the project brief)

# ---------------------------------------------------------------------------
# Jazzmin (admin theme)
# ---------------------------------------------------------------------------
JAZZMIN_SETTINGS = {
    "site_title": f"{SITE_NAME} Admin",
    "site_header": SITE_NAME,
    "site_brand": SITE_NAME,
    "welcome_sign": f"Welcome to the {SITE_NAME} admin panel",
    "copyright": SITE_NAME,
    "search_model": ["academics.Subject", "academics.Topic"],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "academics.Program": "fas fa-graduation-cap",
        "academics.Semester": "fas fa-layer-group",
        "academics.Subject": "fas fa-book",
        "academics.Topic": "fas fa-file-alt",
        "academics.TopicImage": "fas fa-images",
        "academics.PastPaper": "fas fa-file-signature",
        "core.ContactMessage": "fas fa-envelope",
        "core.SiteSetting": "fas fa-cogs",
    },
    "order_with_respect_to": [
        "academics",
        "academics.Program",
        "academics.Semester",
        "academics.Subject",
        "academics.Topic",
        "academics.PastPaper",
        "core",
    ],
    "custom_css": "css/admin-overrides.css",
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
}

JAZZMIN_UI_TWEAKS = {
    "navbar": "navbar-dark",
    "theme": "flatly",
    "dark_mode_theme": None,
    "sidebar": "sidebar-dark-primary",
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}
