from django.urls import include, path
from rest_framework.routers import DefaultRouter

from payment import views

app_name = "payment"


router = DefaultRouter()
router.register(r"cards", views.CardViewSet, basename="card")
router.register(r"plans", views.PlanViewSet, basename="plan")
router.register(r"receipts", views.ReceiptViewSet, basename="receipt")
router.register(r"billings", views.BillingViewSet, basename="billing")
router.register(r"subscriptions", views.SubscriptionViewSet, basename="subscription")


urlpatterns = [
    path("", include(router.urls)),
    path("permissions/", views.PermissionAPIView.as_view(), name="user-permissions"),
    ############################# ENDPOINTS FOR PAYMENT PROVIDER #################
	path('wave/charge/<str:receipt_id>', views.ChargeCardAPIView.as_view(), name="charge-card"),
	path('wave/validate', views.ValidateCardChargeAPIView.as_view(), name="charge-validate"),
    path('wave/verify', views.VerifyPaymentAPIView.as_view(), name="charge-verify"),
    path('receipt/<str:receipt_id>', views.UpdateReceiptStatus.as_view(), name="update-receipt"),
]
