"""
Local development settings for downhill_skateboarding_events project.
This file is loaded when DJANGO_SETTINGS_MODULE=downhill_skateboarding_events.settings_local
"""

from .settings import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-56s_1r#qg48relbdfhbaab2u$n-h(s2%4pz^c=fn+^qzik*sgq"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Use SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# If you want to use a local PostgreSQL database instead, uncomment this:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'downhill_dev',
#         'USER': 'postgres',
#         'PASSWORD': 'postgres',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# Email backend for development (prints emails to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable Cloudinary in development if needed
# DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Tailwind development settings
TAILWIND_DEV_MODE = True
NPM_BIN_PATH = "C:/Users/user/AppData/Roaming/npm/npm.cmd"

# Set this to True if you want to use production media files
USE_PRODUCTION_MEDIA = False

# Add Django Debug Toolbar for development
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # Add as first middleware

# Debug toolbar settings
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
}

# Ensure correct internal IPs for debug toolbar
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# Override the root URLconf for debug toolbar
ROOT_URLCONF = "downhill_skateboarding_events.urls_local"
