"""Production settings and globals."""

from __future__ import absolute_import
from .base import *
from common import utils


# DEBUG CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
# END DEBUG CONFIGURATION

# HOST CONFIGURATION
# See:
# https://docs.djangoproject.com/en/1.5/releases/1.5/#allowed-hosts-required-in-production
ALLOWED_HOSTS = ['staging.openprescribing.net']
# END HOST CONFIGURATION

# EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = environ.get('EMAIL_HOST', 'smtp.gmail.com')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-password
EMAIL_HOST_PASSWORD = environ.get('EMAIL_HOST_PASSWORD',
                                  utils.get_env_setting('GMAIL_PASS'))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host-user
EMAIL_HOST_USER = environ.get('EMAIL_HOST_USER',
                              'openprescribing.errors@gmail.com')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = environ.get('EMAIL_PORT', 587)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = '[%s] ' % SITE_NAME

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-use-tls
EMAIL_USE_TLS = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#server-email
SERVER_EMAIL = EMAIL_HOST_USER
# END EMAIL CONFIGURATION

# DATABASE CONFIGURATION
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': utils.get_env_setting('DB_NAME', ''),
        'USER': utils.get_env_setting('DB_USER', ''),
        'PASSWORD': utils.get_env_setting('DB_PASS', ''),
        'HOST': utils.get_env_setting('DB_HOST', '127.0.0.1')
    }
}
# END DATABASE CONFIGURATION


# CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
# END CACHE CONFIGURATION

# LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s [%(name)s:%(lineno)s] %(module)s %(process)d %(thread)d %(message)s'
        }
    },
    'handlers': {
        'gunicorn': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/webapps/openprescribing_staging/logs/gunicorn.log',
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        }
    },
    'loggers': {
        'django.request': {
            'level': 'DEBUG',
            'handlers': ['gunicorn'],
            'propagate': True,
        },
    }
}
