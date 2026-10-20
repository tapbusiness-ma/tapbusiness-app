"""إعدادات مشروع TAPBusiness — منصة SaaS للمطاعم.

الأسرار كتجي من ملف .env (ما كيتصيفطش لـGitHub).
"""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

import dj_database_url
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
    "apps.menu",
    "apps.orders",
    "apps.tables",
    "apps.subscriptions",
    "axes",  # حماية تسجيل الدخول من تخمين كلمة السر
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # الملفات الثابتة فالإنتاج
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",  # حظر المحاولات الفاشلة المتكررة
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
# محلياً: SQLite. فالإنتاج (Render): PostgreSQL عبر DATABASE_URL
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
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

# ملفات المستخدمين (صور الأطباق...)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# الدخول والخروج
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

# Axes أولاً باش يوقف المحاولات المحظورة، ومن بعد ModelBackend ديال Django
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# --- حماية تسجيل الدخول (django-axes) ---
# 5 محاولات فاشلة بنفس المستخدم ومن نفس IP = حظر مؤقت لمدة ساعة
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(hours=1)
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True
# التطبيق خدام وراء بروكسي واحد (PythonAnywhere): IP الحقيقي كيجي من X-Forwarded-For
AXES_IPWARE_PROXY_COUNT = 1


# --- حماية الإنتاج ---
# فالإنتاج (DEBUG=False) كنرفضو التشغيل إلا كان المفتاح ضعيفاً.
if not DEBUG:
    _weak_markers = ("django-insecure", "change-me", "changeme")
    if (
        not SECRET_KEY
        or len(SECRET_KEY) < 50
        or any(m in SECRET_KEY.lower() for m in _weak_markers)
    ):
        raise ImproperlyConfigured(
            "SECRET_KEY غير آمن: عيّن مفتاحاً قوياً وفريداً (50 حرفاً على الأقل) "
            "فـ SECRET_KEY قبل التشغيل فالإنتاج."
        )
    if "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured("ALLOWED_HOSTS ما خاصوش يكون '*' فالإنتاج.")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000


# --- البريد الإلكتروني (استرجاع كلمة السر) ---
# القيم كتجي من متغيرات البيئة. مثال Gmail:
# EMAIL_HOST_USER=example@gmail.com + كلمة مرور التطبيق (App Password)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "TAPBusiness <noreply@tapbusiness.ma>"
)
