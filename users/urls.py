from django.urls import path
from rest_framework_simplejwt import views as auth_views

from users.api import views
from users.views import (
    delete_user_login_activity,
    get_user_login_activities,
    google_login,
    homepage,
    two_factor_disable_view,
    two_factor_setup_view,
    two_factor_verify_view,
    update_active_password,
    update_active_profile,
    user_detail_view,
    user_redirect_view,
    user_update_view,
)

app_name = "users"

urlpatterns = [
    path("auth/login/", views.CreateLoginToken.as_view(), name="jwt-create"),
    path("auth/refresh/", auth_views.TokenRefreshView.as_view(), name="jwt-refresh"),
    path("auth/verify/", auth_views.TokenVerifyView.as_view(), name="jwt-verify"),
]

urlpatterns += [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<int:pk>/", view=user_detail_view, name="detail"),
    # fetch user detail profile
    path("profile/", view=user_detail_view, name="user_detail_view"),
    # for frontend request to google login
    path("login/google/", view=google_login, name="google_login"),
    # 2fa Authentication
    path("2fa/setup/", view=two_factor_setup_view, name="two-factor-setup"),
    path("2fa/verify/", view=two_factor_verify_view, name="two-factor-verify"),
    path("2fa/disable/", view=two_factor_disable_view, name="two_factor_disable_view"),
    # for active user to change password and update profile data,
    path(
        "active/change-password",
        view=update_active_password,
        name="update_active_password",
    ),
    path(
        "active/update-profile",
        view=update_active_profile,
        name="update_active_profile",
    ),
    # get and remove user login activity logs
    path(
        "activity/logs/",
        view=get_user_login_activities,
        name="get_user_login_activities",
    ),
    path(
        "activity/logs/<str:pk>/",
        view=delete_user_login_activity,
        name="delete_user_login_activity",
    ),
    # temporary account signup with google redirect view
    path("home/", view=homepage, name="homepage"),
]
