from django.urls import path

from . import views

app_name = "brokers"

urlpatterns = [
    path("all", views.EctypeBrokersListAPIView.as_view(), name="get-brokers"),
    path("all/<str:pk>", views.GetEctypeBroker.as_view(), name="get-broker"),
    path(
        "servers/<str:pk>",
        views.GetEctypeBrokerServer.as_view(),
        name="get-broker-server",
    ),
    path(
        "servers",
        views.EctypeBrokerServersListAPIView.as_view(),
        name="get-broker-servers",
    ),
]
