from django.urls import path

from . import views

app_name = "referral"

urlpatterns = [
    path("token", views.ReferralTokenView.as_view(), name="create-referral-token"),
    path("add", views.ReferralPaymentView.as_view(), name="add-referral"),
    path("payment", views.GetReferralPayment.as_view(), name="get-referral-payment"),
    path("withdraw", views.ReferralPaymentWithdrawalView.as_view(), name="referral-withdraw")
]