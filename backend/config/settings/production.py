from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Allowed hosts must be explicitly set in production
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# CORS Configuration for Production
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')

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






# Security Settings
# Force HTTPS
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Additional Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure Proxy SSL Header (if behind a reverse proxy like Nginx)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400

# CSRF Security
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')

# Database connection pooling (optional but recommended)
DATABASES['default']['CONN_MAX_AGE'] = 600

# Logging - Production level
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['payment_service']['level'] = 'INFO'

# Email configuration for production (ensure proper SMTP settings)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'