"""
Django settings for lms_connector project.

Generated by 'django-admin startproject' using Django 2.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

STAGE = os.environ.get('STAGE', 'local')
IS_LOCAL = STAGE == 'local'

if IS_LOCAL:
    API_KEY = os.environ.get('API_KEY')
else:
    API_KEY = os.environ['API_KEY']

if IS_LOCAL and os.environ.get('SECRET_KEY') is None:
    SECRET_KEY = 'wvj**=&qmbzlu@prd&+he_3!h6f^o_6r-zc-1k+btivmfj(+_j'
else:
    SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Should work to remove the wildcard
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'lms-connector.tophat.com',
    'host.docker.internal',
    '.dev.tophat.com',
]


# Application definition

INSTALLED_APPS = [
    'rest_framework_swagger',
    'django.contrib.staticfiles',
    'django.contrib.contenttypes',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'lms_connector.middleware.cloudwatch.CloudWatch',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
STATIC_ROOT = './'
STATIC_URL = '/templates/'

ROOT_URLCONF = 'lms_connector.urls'

WSGI_APPLICATION = 'lms_connector.wsgi.application'

DATABASES = {}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-ca'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


REST_FRAMEWORK = {
    # https://github.com/encode/django-rest-framework/issues/3262#issuecomment-147541598
    'UNAUTHENTICATED_USER': None,

    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'lms_connector.permissions.ValidateApiKey',
    ],
    'EXCEPTION_HANDLER': 'lms_connector.exception_handler.exception_handler',
}
