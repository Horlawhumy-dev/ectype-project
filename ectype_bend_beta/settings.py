import os
import logging
import sentry_sdk

from datetime import timedelta
from dotenv import load_dotenv

from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# load_dotenv(BASE_DIR.joinpath("env.example"))
load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = str(os.getenv("SECRET_KEYS"))

DEBUG = bool(os.getenv("DEBUG", False))

# Production - meant for staging/main branches
# if not DEBUG:
#    PROTOCOL = "https"
#    DOMAIN = "ectype-beta.onrender.com"
# CSRF_TRUSTED_ORIGINS = ["https://ectype-beta.onrender.com"]

# ALLOWED_HOSTS = ["ectype-beta.onrender.com"]
# Development - meant for deveop branch
PROTOCOL = "http"
DOMAIN = "localhost:8080"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "crispy_forms",
    "crispy_bootstrap5",
    "dj_rest_auth",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_celery_beat",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "drf_spectacular",
    "dj_rest_auth.registration",
    "allauth.socialaccount.providers.google",
    "djoser",
    "django_jsonform",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_hotp",
    # internal apps
    "users",
    "payment",
    "accounts",
    "notification",
    "brokers",
    "referral"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ectype_bend_beta.urls"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = "users.User"
ACCOUNT_SIGNUP_REDIRECT_URL = "users:homepage"  # temporary redirect view
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = os.getenv("LOGIN_REDIRECT_URL", "")


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ectype_bend_beta.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("DATABASE_NAME"),
        "USER": os.getenv("DATABASE_USER"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST"),
<<<<<<< HEAD
        "PORT": os.getenv("DATABASE_PORT"),
        'OPTIONS': {
            'sslmode': 'require'
        },
=======
        "PORT": os.getenv("DATABASE_PORT")
>>>>>>> staging
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Lagos"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "staticfiles")]
MEDIA_URL = "media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# For Zoho EMail
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USE_TLS = bool(os.getenv("EMAIL_USE_TLS", True))
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", 60))
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_HOST_USER")
ECTYPE_SUPPORT_EMAIL = os.getenv("ECTYPE_SUPPORT_EMAIL")
#Optional configuration
SERVER_EMAIL = ECTYPE_SUPPORT_EMAIL

# Flutterwave Payment Keys

FLUTTERWAVE_PUBLIC_KEY = os.getenv("FLUTTERWAVE_PUBLIC_KEY")
FLUTTERWAVE_SECRET_KEY = os.getenv("FLUTTERWAVE_SECRET_KEY")
FLUTTERWAVE_ENCRYPTION_KEY = os.getenv("FLUTTERWAVE_ENCRYPTION_KEY")
WAVE_BASE_URL = str(os.getenv("WAVE_BASE_URL"))

######## referral secrets ########################
REFERRAL_PERCENT_PER_HEAD = os.getenv("REFERRAL_PERCENT_PER_HEAD")
NAIRA_PER_DOLLAR_RATE = os.getenv("NAIRA_PER_DOLLAR_RATE")
MAXIMUM_ACCOUNT_SLOTS= os.getenv("MAXIMUM_ACCOUNT_SLOTS_PER_USER")

CORS_ALLOW_ALL_ORIGINS = True  # TODO: remove after clarification with dev setup
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://ectype-fend-git-develop-phace.vercel.app",
    "https://www.ectype-fend-git-develop-phace.vercel.app"
]
CORS_ALLOW_HEADERS = ["*"]

# Additional CORS settings
CORS_ALLOW_CREDENTIALS = (
    True  # if you need to allow credentials (e.g., cookies) with cross-origin requests
)
SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer", "JWT"),
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=2),
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = "admin/"
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [("""Brian Obot & Arafat Olayiwola""", "support@ectype.com")]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS
# https://cookiecutter-django.readthedocs.io/en/latest/settings.html#other-environment-settings
# Force the `admin` sign in process to go through the `django-allauth` workflow
DJANGO_ADMIN_FORCE_ALLAUTH = bool(
    os.getenv("DJANGO_ADMIN_FORCE_ALLAUTH", default=False)
)


# django-allauth
# ------------------------------------------------------------------------------
ACCOUNT_ALLOW_REGISTRATION = bool(os.getenv("DJANGO_ACCOUNT_ALLOW_REGISTRATION", True))
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_AUTHENTICATION_METHOD = "email"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_REQUIRED = True
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_USERNAME_REQUIRED = False
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
# https://django-allauth.readthedocs.io/en/latest/configuration.html
ACCOUNT_ADAPTER = "users.adapters.AccountAdapter"
# https://django-allauth.readthedocs.io/en/latest/forms.html
ACCOUNT_FORMS = {"signup": "users.forms.UserSignupForm"}
# https://django-allauth.readthedocs.io/en/latest/configuration.html
SOCIALACCOUNT_ADAPTER = "users.adapters.SocialAccountAdapter"
# https://django-allauth.readthedocs.io/en/latest/forms.html
SOCIALACCOUNT_FORMS = {"signup": "users.forms.UserSocialSignupForm"}

# django-rest-framework
# -------------------------------------------------------------------------------
# django-rest-framework - https://www.django-rest-framework.org/api-guide/settings/
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "dj_rest_auth.jwt_auth.JWTCookieAuthentication",  # for google jwt auth
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


DJOSER = {
    "SERIALIZERS": {
        "user_create": "users.api.serializers.CustomUserCreateSerializer",
        "activation": "users.api.serializers.ActivationSerializer",
        "password_reset_confirm": "users.api.serializers.PasswordResetConfirmSerializer",
        "token_create": "djoser.serializers.TokenCreateSerializer",
    },
    "SEND_ACTIVATION_EMAIL": True,
    "SEND_CONFIRMATION_EMAIL": True,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": True,
    "EMAIL": {
        "activation": "users.email.ActivationEmail",
        "confirmation": "users.email.ConfirmationEmail",
        "password_reset": "users.email.PasswordResetEmail",
        "password_changed_confirmation": "users.email.PasswordChangedConfirmationEmail",
    },
}

# ------------------------------------------------------------------------------
# Django AllAuth with Google
SITE_ID = 1
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "offline",
        },
        "OAUTH_PKCE_ENABLED": True,
        "METHOD": "oauth2",
    }
}


REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_COOKIE": "jwt-auth",
    "JWT_AUTH_REFRESH_COOKIE": "refresh-token",
    "LOGOUT_ON_PASSWORD_CHANGE": True,
}

CELERY_TASK_EAGER_PROPAGATES = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    }
}

# STRIPE API SETTING
# https://stripe.com/docs/api/authentication
# ------------------------------------------------------------------------------
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# 2fa Authentication Django-OTP
OTP_TOTP_ISSUER = "Ectype"
OTP_TOTP_SECRET_KEY = os.getenv(
    "SECRET_KEYS",
    default="oqWAqSSqmIiIkJCa85TS2Rmyes4oudvBSN4U7gFjcPVBAY0oEyRlOPcjb1CkUlqn",
)

# TRADESYNC API SETTING
# https://app.tradesync.io/api-key/
# ------------------------------------------------------------------------------
TRADE_SYNC_KEY = os.getenv("TRADE_SYNC_KEY")
TRADE_SYNC_SECRET = os.getenv("TRADE_SYNC_SECRET")
TRADE_SYNC_API = os.getenv("TRADE_SYNC_API")

# To prevent development logging by sentry
if DEBUG == False:
    # Sentry Configuration
    import sentry_sdk


    # SENTRY RELATED
    sentry_sdk.init(
        dsn="https://844a8f74e1ee8b7f1cb3ab5707299202@o4506112540999680.ingest.sentry.io/4506123668619264",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
    )


STORAGES = {
    # ...
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}