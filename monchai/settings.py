"""
Django settings for Mon Chai project.
"""

import os
from pathlib import Path
from decouple import config as decouple_config, Config, RepositoryEnv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = (BASE_DIR / '.env')
config = Config(RepositoryEnv(ENV_FILE)) if ENV_FILE.exists() else decouple_config

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Default primary key field type for all models
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver,192.168.1.11').split(',')

# Feature flags
FEATURE_MS = config('FEATURE_MS', default=True, cast=bool)

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'widget_tweaks',
    'django_extensions',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.onboarding.apps.OnboardingConfig',
    'apps.referentiels',
    'apps.catalogue',
    'apps.metadata',
    'apps.viticulture',
    'apps.stock',
    'apps.sales',
    'apps.billing',
    'apps.imports',
    'apps.clients',
    'apps.produits',
    # New lightweight namespace apps for navigation
    'apps.production.apps.ProductionConfig',
    'apps.ventes',
    'apps.site',
    'apps.drm',
    # AI help module
    'apps.ai',
    # GIS lite module
    'giscore',
    # Urbanisme & PLU proxy API
    'urbanisme',
    # Cadastre clone app (MapLibre + Mes parcelles)
    'cadastre_app',
    # New Commerce app (Refonte Achats/Ventes)
    'apps.commerce',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'apps.core.middleware.ClientsRedirectMiddleware',  # Redirections clients ciblées - Phase 7
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom middlewares (roadmap 06)
    'apps.accounts.middleware.CurrentOrganizationMiddleware',
    'apps.core.middleware.ActiveOrgContextMiddleware',
    'apps.accounts.middleware.SecurityMiddleware',
    'apps.core.middleware.PgRlsMiddleware',
    # 'apps.onboarding.middleware.OnboardingRedirectMiddleware',  # disabled: tour runs across existing pages
    # 'apps.accounts.middleware.OrganizationFilterMiddleware',  # Temporairement désactivé
    # New: Robots noindex by default except public site
    'apps.core.middleware.RobotsNoIndexMiddleware',
]

ROOT_URLCONF = 'monchai.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.accounts.context_processors.multi_chai_context',
                'apps.ai.context_processors.smart_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'monchai.wsgi.application'

# Database
# Default to SQLite for dev; enable PostgreSQL via env flags.
USE_POSTGRES = config('USE_POSTGRES', default=False, cast=bool)
if USE_POSTGRES:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('POSTGRES_DB', default='monchai'),
            'USER': config('POSTGRES_USER', default='monchai'),
            'PASSWORD': config('POSTGRES_PASSWORD', default=''),
            'HOST': config('POSTGRES_HOST', default='127.0.0.1'),
            'PORT': config('POSTGRES_PORT', default='5432'),
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=60, cast=int),
            'OPTIONS': {},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'ATOMIC_REQUESTS': True,
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Encoding settings
DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs (invariants techniques)
LOGIN_URL = config('LOGIN_URL', default='/auth/login/')
LOGIN_REDIRECT_URL = config('LOGIN_REDIRECT_URL', default='/auth/first-run/')
LOGOUT_REDIRECT_URL = config('LOGOUT_REDIRECT_URL', default='/auth/login/')

# Email configuration (console backend for dev)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Mon Chai <noreply@monchai.app>')

# Session configuration
SESSION_COOKIE_AGE = 86400 * 7  # 7 days
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_SAVE_EVERY_REQUEST = True

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Parcelles embed configuration (GIS Lite)
PMTILES_URL = config('PMTILES_URL', default='')
PARCELLES_MODE = config('PARCELLES_MODE', default='LITE')

# Cache configuration: prefer Redis if REDIS_URL provided, else LocMem for dev
if not globals().get('CACHES'):
    REDIS_URL = config('REDIS_URL', default='')
    if REDIS_URL:
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': REDIS_URL,
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'retry_on_timeout': True,
                },
                'KEY_PREFIX': 'monchai',
                'TIMEOUT': None,  # no global timeout; per-key TTLs are used
            }
        }
    else:
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'monchai-local',
            }
        }

# AI Help / Ollama configuration
OLLAMA_URL = config('OLLAMA_URL', default='http://127.0.0.1:11434/api/generate')
OLLAMA_MODEL = config('OLLAMA_MODEL', default='mistral:7b')
# Use standard model for stability during testing
HELP_MODEL = config('HELP_MODEL', default='mistral:7b')
HELP_RATE_LIMIT_CALLS = config('HELP_RATE_LIMIT_CALLS', default=10, cast=int)
HELP_RATE_LIMIT_WINDOW = config('HELP_RATE_LIMIT_WINDOW', default=300, cast=int)  # seconds
HELP_TIMEOUT = config('HELP_TIMEOUT', default=60, cast=int)  # 60s timeout to avoid premature fallback
OLLAMA_KEEP_ALIVE = config('OLLAMA_KEEP_ALIVE', default='30m')  # keep model warmed
HELP_NUM_PREDICT = config('HELP_NUM_PREDICT', default=180, cast=int)
# Robustness tunables
OLLAMA_CONNECT_TIMEOUT = config('OLLAMA_CONNECT_TIMEOUT', default=5, cast=int)
HELP_OLLAMA_RETRIES = config('HELP_OLLAMA_RETRIES', default=2, cast=int)
HELP_CACHE_TTL = config('HELP_CACHE_TTL', default=180, cast=int)
HELP_MAX_HINTS_CHARS = config('HELP_MAX_HINTS_CHARS', default=800, cast=int)
HELP_MAX_DOCS_CHARS = config('HELP_MAX_DOCS_CHARS', default=1200, cast=int)
HELP_HTTP_POOL_SIZE = config('HELP_HTTP_POOL_SIZE', default=20, cast=int)
# Clamp final assistant responses to keep answers concise
HELP_MAX_RESPONSE_CHARS = config('HELP_MAX_RESPONSE_CHARS', default=900, cast=int)
# Enable unrestricted mode for testing
HELP_UNRESTRICTED = config('HELP_UNRESTRICTED', default=True, cast=bool)
HELP_FREE_MODEL = config('HELP_FREE_MODEL', default='')  # optional alternate model for unrestricted mode

# Balanced system prompt: conversational but grounded
HELP_SYSTEM_PROMPT = (
    "Tu es l'assistant Mon Chai, expert en gestion viticole. "
    "Tu es conversationnel et amical. Réponds naturellement aux salutations et questions générales. "
    "\n\n"
    "RÈGLES STRICTES pour questions techniques :\n"
    "1. PRIORITÉ ABSOLUE : Si le contexte contient des sections [DURAS::FACT::...], utilise UNIQUEMENT ces informations.\n"
    "2. Les sections FACT sont des données vérifiées et prioritaires. Ignore les autres sections si elles contredisent les FACT.\n"
    "3. Si l'information n'est PAS dans le contexte, réponds : \"Je ne trouve pas cette information dans les documents disponibles.\"\n"
    "4. N'invente JAMAIS de chiffres, règles ou fonctionnalités.\n"
    "5. Ne donne JAMAIS de code de programmation.\n"
    "\n"
    "Sois concis, précis et utile."
)

# Minimal template: system + prompt (we embed [PAGE] and [QUESTION] into the prompt)
OLLAMA_TEMPLATE = (
    "<|system|>\n{{ .System }}\n<|user|>\n{{ .Prompt }}\n<|assistant|>\n"
)

# Safer generation options
OLLAMA_OPTIONS = {
    'temperature': 0.1,
    'top_p': 0.8,
    'repeat_penalty': 1.2,
    'num_predict': HELP_NUM_PREDICT,
    'stop': ["<|assistant|>", "<|user|>", "[CONTRAINDICE]", "[CONTRAINTE]", "RÈGLES DE SÉCURITÉ & QUALITÉ"],
}
