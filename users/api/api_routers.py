from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from users.api.views import UserViewSetX  # noqa

PREFIX = "users"
API_VERSION = settings.API_VERSION

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()


# router.register("users", UserViewSetX)


app_name = f"{PREFIX}"
urlpatterns = router.urls
