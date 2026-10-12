"""نقطة دخول الإنتاج — gunicorn كيستعمل هاد الملف ملي نحطو الموقع online.
محلياً كنستعملو runserver وما كنحتاجوهش.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
