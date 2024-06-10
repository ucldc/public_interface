import subprocess

"""
Django settings for public_interface project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

from django.utils.crypto import get_random_string  # http://stackoverflow.com/a/16630719/1763984

import os
import sys


def getenv(variable, default):
    ''' getenv wrapper that decodes the same as python 3 in python 2
    '''
    try:  # decode for python2
        return os.getenv(variable, default).decode(sys.getfilesystemencoding())
    except AttributeError:
        return os.getenv(variable, default)


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

S3_STASH = getenv('UCLDC_S3_STASH', '')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = getenv(
    'DJANGO_SECRET_KEY',
    get_random_string(50,
                      'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'))

SOLR_URL = getenv('UCLDC_SOLR_URL', '')         # http://localhost:8983/solr
SOLR_API_KEY = getenv('UCLDC_SOLR_API_KEY', '')
EXHIBITS_SOLR_URL = getenv('UCLDC_EXHIBITS_SOLR_URL','http://localhost:8983/solr')
EXHIBITS_SOLR_API_KEY = getenv('UCLDC_EXHIBITS_SOLR_API_KEY', '')

ES_HOST = getenv('ES_HOST', '')
ES_USER = getenv('ES_USER', '')
ES_PASS = getenv('ES_PASS', '')
ES_ALIAS = getenv('ES_ALIAS', '')

MULTI_INDEX = bool(SOLR_URL and ES_HOST)

# Homepage images, featured images, campus images, posters
UCLDC_IMAGES = getenv('UCLDC_IMAGES', '').rstrip('/')

if ES_HOST:
    # these settings variables are exclusively for use with the ES index
    # but the environment varibles can be used for both ES and SOLR - 
    # this makes it so we don't have to rename all the environment
    # variables on calisphere-test and prod. 
    THUMBNAIL_URL = getenv('UCLDC_THUMBNAIL_URL', '')
    UCLDC_MEDIA = getenv('UCLDC_MEDIA', '')
    UCLDC_IIIF = getenv('UCLDC_IIIF', '')
    UCLDC_NUXEO_THUMBS = getenv('UCLDC_NUXEO_THUMBS', '')

if SOLR_URL:
    # these settings variables are exclusively for use with the Solr
    # index. these settings variables read from UCLDC_*_SOLR env vars
    # if they are set, and otherwise falls back to reading from UCLDC_*
    SOLR_THUMBNAILS = getenv(
        'UCLDC_THUMBNAIL_URL_SOLR', getenv(
            'UCLDC_THUMBNAIL_URL', 'https://calisphere.org/'))
    SOLR_MEDIA = getenv('UCLDC_MEDIA_SOLR', getenv('UCLDC_MEDIA', ''))
    SOLR_IIIF = getenv('UCLDC_IIIF_SOLR', getenv('UCLDC_IIIF', ''))
    SOLR_NUXEO_THUMBS = getenv(
        'UCLDC_NUXEO_THUMBS_SOLR', getenv('UCLDC_NUXEO_THUMBS', ''))

if MULTI_INDEX:
    DEFAULT_INDEX = "es"
elif SOLR_URL:
    DEFAULT_INDEX = "solr"
    THUMBNAIL_URL = SOLR_THUMBNAILS
elif ES_HOST:
    DEFAULT_INDEX = "es"
else:
    raise AttributeError("No index or thumbnail server specified")


UCLDC_REGISTRY_URL = getenv('UCLDC_REGISTRY_URL',
                               'https://registry.cdlib.org/')

UCLDC_FRONT = getenv('UCLDC_FRONT', '')
UCLDC_REDIS_URL = getenv('UCLDC_REDIS_URL', False)
UCLDC_DISQUS = getenv('UCLDC_DISQUS', 'test')  # set to 'prod' to use the prod disqus shortcode value

UCLDC_METADATA_SUMMARY = getenv('UCLDC_METADATA_SUMMARY', False)

RECAPTCHA_PUBLIC_KEY = getenv('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = getenv('RECAPTCHA_PRIVATE_KEY', '')

EMAIL_BACKEND = getenv('EMAIL_BACKEND',
                          'django.core.mail.backends.console.EmailBackend')

EMAIL_HOST = getenv('EMAIL_HOST', '')
EMAIL_HOST_PASSWORD = getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_HOST_USER = getenv('EMAIL_HOST_USER', '')
try:
    EMAIL_PORT = int(getenv('EMAIL_PORT', ''))
except ValueError:
    pass
EMAIL_USE_TLS = bool(getenv('EMAIL_USE_TLS', ''))
CSRF_COOKIE_SECURE = bool(getenv('CSRF_COOKIE_SECURE', ''))

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

DEFAULT_FROM_EMAIL = getenv('DEFAULT_FROM_EMAIL', 'project@example.edu')

ADMINS = (('', DEFAULT_FROM_EMAIL), )
MANAGERS = ADMINS

GA_SITE_CODE = getenv('UCLDC_GA_SITE_CODE', False)
GA4_SITE_CODE = getenv('UCLDC_GA4_SITE_CODE', False)
MATOMO_SITE_CODE = getenv('UCLDC_MATOMO_SITE_CODE', False)
UCLDC_WALKME = getenv('UCLDC_WALKME', False)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(os.environ.get('UCLDC_DEBUG'))  # <-- this is django's debug

UCLDC_DEVEL = bool(os.environ.get('UCLDC_DEVEL'))
#<-- this has to do with css via devMode

# When EXHIBIT_PREVIEW = False, show only exhibits, themes, lesson plans, and essays marked 'published'
# When EXHIBIT_PREVIEW = True, show ALL exhibits, themes, lesson plans, and essays
EXHIBIT_PREVIEW = bool(os.environ.get('UCLDC_EXHIBIT_PREVIEW'))
EXHIBIT_TEMPLATE = 'calisphere/base.html,calisphere/pjaxTemplates/pjax-base.html'
CALISPHERE = True

# https://dryan.com/articles/elb-django-allowed-hosts/
ALLOWED_HOSTS = [
    'calisphere.org',
    '.cdlib.org',
    '.compute-1.amazonaws.com',
    '.elasticbeanstalk.com',
    'd2q6gnsy5fzbu2.cloudfront.net',    # pad-prd acct calisphere-stg
    'd8qsgtswnfjyl.cloudfront.net',      # pad-prd acct calisphere-prd
    '127.0.0.1',
]

EC2_PRIVATE_IP = None
try:
    result = subprocess.check_output(["ec2-metadata", "--local-ipv4"]).decode("utf-8")
    EC2_PRIVATE_IP = result.split(":")[1].strip()
except FileNotFoundError:
    pass

if EC2_PRIVATE_IP:
    ALLOWED_HOSTS.append(EC2_PRIVATE_IP)

SITE_ID = 1

PERMISSIONS_POLICY = {
    'geolocation': [],
    'midi': [],
    'microphone': [],
    'camera': [],
    'magnetometer': [],
    'gyroscope': [],
    'accelerometer': [],
    'ambient-light-sensor': [],
    'autoplay': [],
    'payment': [],

    'fullscreen': 'self',
    'sync-xhr': '*',
}

# Application definition

INSTALLED_APPS = ('exhibits.apps.ExhibitsConfig', 'django.contrib.admin',
                  'django.contrib.auth', 'django.contrib.contenttypes',
                  'django.contrib.sessions', 'django.contrib.messages',
                  'django.contrib.staticfiles', 'django.contrib.sites',
                  'django.contrib.humanize', 'django.contrib.sitemaps',
                  'easy_pjax', 'calisphere', 'static_sitemaps', 'health_check',
                  'health_check.cache', 'health_check.storage', 'snowpenguin.django.recaptcha2', )

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django_permissions_policy.PermissionsPolicyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    # 'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'calisphere.redirects.redirect_middleware.InMemoryRedirectMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware', )

ROOT_URLCONF = 'public_interface.urls'

WSGI_APPLICATION = 'public_interface.wsgi.application'

APPEND_SLASH = True

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {
        "builtins": ["easy_pjax.templatetags.pjax_tags",
        "exhibits.templatetags.exhibit_extras"],
        "context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            'public_interface.context_processors.settings',
            'exhibits.context_processors.settings'
        ],
        "debug":
        UCLDC_DEVEL,
        'loaders': [
            ('django.template.loaders.cached.Loader', [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]),
        ],
    }
}]

if UCLDC_DEVEL or DEBUG or 1 == 1:
    # turn off template cache if we are debugging
    TEMPLATES[0]['APP_DIRS'] = True
    TEMPLATES[0]['OPTIONS'].pop('loaders', None)
    TEMPLATES[0]['OPTIONS']['debug'] = True

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {}

if os.environ.get(
        'RDS_DB_NAME') and not os.environ.get('UCLDC_EXHIBITIONS_DATA'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'CONN_MAX_AGE': 60 * 60,  # in seconds
            'HOST': os.environ.get('RDS_HOSTNAME'),
            'NAME': os.environ.get('RDS_DB_NAME'),
            'PASSWORD': os.environ.get('RDS_PASSWORD'),
            'PORT': os.environ.get('RDS_PORT'),
            'USER': os.environ.get('RDS_USERNAME'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }


# Cache / Redis
#

DJANGO_CACHE_TIMEOUT = int(getenv('DJANGO_CACHE_TIMEOUT', 60 * 15))  # seconds

CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = DJANGO_CACHE_TIMEOUT
CACHE_MIDDLEWARE_KEY_PREFIX = ''

if UCLDC_REDIS_URL:
    # DJANGO_REDIS_IGNORE_EXCEPTIONS = True
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': UCLDC_REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler"
]

MEDIA_ROOT = os.path.join(BASE_DIR, "media_root")
MEDIA_URL = '/media/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = getenv('UCLDC_STATIC_URL',
                       'http://localhost:9000/')  # `gulp serve`

STATIC_ROOT = os.path.join(BASE_DIR, "static_root")

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATICFILES_DIRS = (os.path.join(BASE_DIR, "dist"), )

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
    },
}

CONTRUBUTOR_CONTACT_FLAG = 'link'  # 'email'

SITE_ID = 1

STATICSITEMAPS_ROOT_SITEMAP = 'public_interface.urls.sitemaps'

STATICSITEMAPS_ROOT_DIR = os.path.join(BASE_DIR, "sitemaps")

STATICSITEMAPS_URL = UCLDC_FRONT

STATICSITEMAPS_PING_GOOGLE = False

try:
    from public_interface.local_settings import *
except ImportError:
    pass
