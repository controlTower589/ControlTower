
import os
from dotenv import load_dotenv

load_dotenv()






from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-#m9)tf@)oeg$6)ib&hstgownpf5+$8n=9@=4mz48!7&&@q0%+$"

DEBUG = True

ALLOWED_HOSTS = ['*']


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

"intake",
    "events",
    "workflows",
    "dashboard",
    "audit",
"adapters",
"controltower",
"team",






]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "controltower_db",
        "USER": "controltower_user",
        "PASSWORD": "Aa9886603727$",
        "HOST": "127.0.0.1",
        "PORT": "5432",

    }
}





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




LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_TZ = True




STATIC_URL = "static/"
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
MATRIX_BASE_URL = "http://localhost:8008"
OPENWEBUI_BASE_URL = "http://localhost:3000"
SIMULATE_MATRIX_FAILURE = True
MATRIX_FAILURE_RATE = 1.0  # 20% fail  later we will change after discussing with garry
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "controltower@bisonvp-demo.com"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = "tower2372@gmail.com"
EMAIL_HOST_PASSWORD = "wpyknyjzirfedpea"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


MATRIX_HOMESERVER_URL = os.getenv("MATRIX_HOMESERVER_URL", "http://localhost:8008")
MATRIX_WEB_URL = os.getenv("MATRIX_WEB_URL", "http://localhost:8008")
MATRIX_ACCESS_TOKEN = os.getenv("MATRIX_ACCESS_TOKEN", "")


MATRIX_DEFAULT_INVITEES = [
    u.strip() for u in os.getenv("MATRIX_DEFAULT_INVITEES", "").split(",") if u.strip()
]



