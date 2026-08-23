from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "todo-development-key"
DEBUG = True
ALLOWED_HOSTS = []
ROOT_URLCONF = "config.urls"
MIDDLEWARE = ["django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware"]
INSTALLED_APPS = ["django.contrib.contenttypes", "django.contrib.auth", "django.contrib.staticfiles", "webapp"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.request"]}}]
USE_TZ = True
TIME_ZONE = "UTC"
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
