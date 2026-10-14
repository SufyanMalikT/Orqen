"""
Development settings for Orqen project.
"""

from .base import *

# Ensure DEBUG is True in development by default, or read from env
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '[::1]', 'testserver']

# Development email backend (prints emails to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development logging adjustments
LOGGING['loggers']['django']['level'] = 'INFO'
LOGGING['loggers']['orqen']['level'] = 'DEBUG'
