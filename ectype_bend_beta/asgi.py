import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ectype_bend_beta.settings")

application = get_asgi_application()
