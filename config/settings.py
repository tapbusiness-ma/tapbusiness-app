"""إعدادات مشروع TAPBusiness — منصة SaaS للمطاعم.

الأسرار كتجي من ملف .env (ما كيتصيفطش لـGitHub).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# المسار الرئيسي ديال المشروع
BASE_DIR = Path(__file__).resolve().parent.parent

# كنقراو المتغيرات من ملف .env إلا كان موجود
load_dotenv(BASE_DIR / ".env")

# --- الأمان ---
# فالإنتاج: SECRET_KEY ضروري يكون فـ .env (ماشي فالكود)
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-only-change-me")
# فالإنتاج خاصو يكون False
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# --- التطبيقات المثبتة ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # تطبيقات TAPBusiness
    "apps.restaurants",
    "apps.accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # الملفات الثابتة فالإنتاج
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
        "DIRS": [BASE_DIR / "templates"],  # القوالب ديالنا غتكون هنا
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

# --- قاعدة البيانات ---
# محلياً: SQLite (بسيطة، بلا إعداد). فالإنتاج: PostgreSQL عبر DATABASE_URL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- اللغة والوقت ---
LANGUAGE_CODE = "fr-fr"      # واجهة الإدارة بالفرنسية
TIME_ZONE = "Africa/Casablanca"
USE_I18N = True
USE_TZ = True

# --- الملفات الثابتة (CSS, JS, صور) ---
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # للإنتاج

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# الدخول والخروج
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"
