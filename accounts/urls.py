from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("account", views.TradingAccountsView.as_view(), name="create-trading-account"),
    path("accounts", views.AccountsListAPIView.as_view(), name="get-trading-accounts"),
    path(
        "accounts/<str:pk>",
        views.TradingAccountsUpdateView.as_view(),
        name="update-delete-trading-account",
    ),
    path(
        "accounts/<str:pk>/connection",
        views.TradingAccountsConnectionUpdateView.as_view(),
        name="update-trading-account-connection",
    ),
    path(
        "copiers",
        views.AccountCopiersListAPIView.as_view(),
        name="get-trading-accounts-copiers",
    ),
    path(
        "copier",
        views.TradingAccountsCopierView.as_view(),
        name="create-trading-accounts-copier",
    ),
    path(
        "group/copiers/<str:pk>",
        views.TradingAccountsCopierUpdateView.as_view(),
        name="update-delete-trading-accounts-copier",
    ),
    path("copier/more", views.AddMoreFollowersCopierView.as_view(), name="add-more-follower"),
    path("copier/<str:copier_id>/delete/<str:follower_id>", \
    views.UpdateDeleteSingleCopierFromGroupView.as_view(), name="delete-single-copier-from-group"),
    # path("syncs/all", views.SyncAllAccountsCopyView.as_view(), name="sync-all-accounts"),

]
