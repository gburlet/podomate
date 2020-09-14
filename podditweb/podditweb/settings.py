import datetime
import os
from pathlib import Path
from utils import get_local_ip, get_linux_ec2_private_ip


BASE_DIR = Path(__file__).resolve().parent.parent

DEPLOY_ENV = os.environ.get("DEPLOY_ENV", "local")  # {local, dev, prod}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')

DEBUG = DEPLOY_ENV == "local"

ALLOWED_HOSTS = [
    'localhost', '127.0.0.1', get_local_ip()
]
private_ip = get_linux_ec2_private_ip()
if private_ip:
    # append IP of ELB health check pinger
    ALLOWED_HOSTS.append(private_ip)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'server'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'podditweb.urls'

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

WSGI_APPLICATION = 'podditweb.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('RDS_DB_NAME', ''),
        'USER': os.environ.get('RDS_USERNAME', ''),
        'PASSWORD': os.environ.get('RDS_PASSWORD', ''),
        'HOST': os.environ.get('RDS_HOSTNAME', ''),
        'PORT': os.environ.get('RDS_PORT', ''),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Option to use S3 for media storage/serving or local HDD
STATIC_DIR = "static"
MEDIA_DIR = "media"
USE_S3 = DEPLOY_ENV != "local"
if USE_S3:
    DEFAULT_FILE_STORAGE = 'aimusiclessons.storage_backends.MediaStorage'
    STATICFILES_STORAGE = 'aimusiclessons.storage_backends.StaticStorage'
    AWS_S3_SECURE_URLS = True
    AWS_S3_URL_PROTOCOL = 'https:'
    AWS_QUERYSTRING_AUTH = False     # don't add complex authentication-related query parameters for requests
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    AWS_LOCATION = STATIC_DIR
    AWS_STORAGE_BUCKET_NAME = 'aimusiclessonsdata' if DEPLOY_ENV == "prod" else 'aimusiclessonsdevdata'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    AWS_IS_GZIPPED = True

    # set cache expiration headers
    two_months = datetime.timedelta(days=61)
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=%d, must-revalidate, stale-while-revalidate=120' %(int(two_months.total_seconds()),),
    }

    STATIC_URL = "%s//%s/%s/" % (AWS_S3_URL_PROTOCOL, AWS_S3_CUSTOM_DOMAIN, STATIC_DIR)
    MEDIA_URL = "%s//%s/%s/" % (AWS_S3_URL_PROTOCOL, AWS_S3_CUSTOM_DOMAIN, MEDIA_DIR)
else:
    MEDIA_URL = "/%s/" % MEDIA_DIR
    MEDIA_ROOT = os.path.join(BASE_DIR, "%s/" % MEDIA_DIR)
    STATIC_URL = "/%s/" % STATIC_DIR
    STATIC_ROOT = os.path.join(BASE_DIR, "aimlserv/%s" % STATIC_DIR)

SITE_ID = 1
