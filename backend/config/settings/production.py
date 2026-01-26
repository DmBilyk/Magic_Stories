from .base import *
import sys

# SECURITY WARNING: keep the secret key used in production secret!
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

if not SECRET_KEY or SECRET_KEY == 'your-secret-key-here':
    raise ValueError("DJANGO_SECRET_KEY must be set in production!")

# Allowed hosts must be explicitly set in production
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]

if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS must be set in production!")

# ============================================
# CORS Configuration - ВИПРАВЛЕНО
# ============================================
cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
CORS_ALLOWED_ORIGINS = [o.strip() for o in cors_origins.split(',') if o.strip()]

csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins.split(',') if o.strip()]

# Якщо не встановлено, використовуємо дефолтні значення для локальної розробки
if not CORS_ALLOWED_ORIGINS:
    print("⚠️ WARNING: CORS_ALLOWED_ORIGINS not set, using defaults")
    CORS_ALLOWED_ORIGINS = [
        "https://magicstories224159.pp.ua",
    ]

if not CSRF_TRUSTED_ORIGINS:
    print("⚠️ WARNING: CSRF_TRUSTED_ORIGINS not set, using defaults")
    CSRF_TRUSTED_ORIGINS = [
        "https://magicstories224159.pp.ua",
    ]

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

# ============================================
# Security Settings - ВИПРАВЛЕНО
# ============================================

# ✅ КРИТИЧНО: Force HTTPS
SECURE_SSL_REDIRECT = True  # Завжди True в production

# ✅ КРИТИЧНО: Secure Cookies
SESSION_COOKIE_SECURE = True   # ✅ ВИПРАВЛЕНО: True для HTTPS
CSRF_COOKIE_SECURE = True      # ✅ ВИПРАВЛЕНО: True для HTTPS

# Additional Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ✅ ВИПРАВЛЕНО: SAMEORIGIN замість DENY для LiqPay
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Дозволяє iframe з того ж домену

# ✅ КРИТИЧНО: HTTP Strict Transport Security (HSTS)
SECURE_HSTS_SECONDS = 31536000          # ✅ ВИПРАВЛЕНО: 1 рік
SECURE_HSTS_INCLUDE_SUBDOMAINS = True   # ✅ ВИПРАВЛЕНО: True
SECURE_HSTS_PRELOAD = True              # ✅ ВИПРАВЛЕНО: True

# Secure Proxy SSL Header (if behind a reverse proxy like Nginx)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ✅ КРИТИЧНО: Session Security
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'  # ✅ ВИПРАВЛЕНО: Strict замість Lax
SESSION_COOKIE_AGE = 86400  # 24 години

# ✅ КРИТИЧНО: CSRF Security
CSRF_COOKIE_HTTPONLY = False  # False для доступу з JavaScript
CSRF_COOKIE_SAMESITE = 'Strict'  # ✅ ВИПРАВЛЕНО: Strict замість Lax

# Database connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600

# ============================================
# Logging - Production level
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'payment_service': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'bookings': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'gunicorn': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
