from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allowed hosts for local development
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'backend']

# CORS Configuration for Local Development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",  # React/Next.js default
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# CSRF Configuration
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]



# Development Tools
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']

# Email Backend for Development (Console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Additional settings for easier debugging
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['handlers']['console']['level'] = 'DEBUG'