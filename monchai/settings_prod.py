"""
Production settings for PythonAnywhere deployment.
Import this in your WSGI file with:
    from monchai.settings_prod import *
"""

from .settings import *
import os

# Security settings
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'CHANGE-ME-IN-PRODUCTION-USE-LONG-RANDOM-STRING')

# PythonAnywhere domain - CHANGEZ 'votreusername' par votre nom d'utilisateur PythonAnywhere
ALLOWED_HOSTS = [
    'votreusername.pythonanywhere.com',  # <-- MODIFIEZ ICI
    'localhost',
    '127.0.0.1',
]

# Database - SQLite pour le test (simple)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files with WhiteNoise
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Disable Redis cache (use local memory on free tier)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'monchai-prod',
    }
}

# Disable AI/Ollama features (not available on PythonAnywhere free)
OLLAMA_URL = ''

# Email - console for now
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
