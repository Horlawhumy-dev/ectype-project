from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.tokens import default_token_generator  # noqa
from django.urls import include, path

# from django.conf.urls import url
from django.views import defaults as default_views
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
    path("users/", include("users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
    path("payment/", include("payment.urls", namespace="payments")),
    path("notify/", include("notification.urls", namespace="notification")),
    path("dj-rest-auth/", include("dj_rest_auth.urls")),
    path("trading/", include("accounts.urls", namespace="accounts")),
    path("brokers/", include("brokers.urls", namespace="brokers")),
    path("referral/", include("referral.urls", namespace="referral")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("users.api_router")),
    # DRF auth token
    path("auth-token/", obtain_auth_token),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
