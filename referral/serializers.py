from rest_framework import serializers
from .models import ReferralToken, ReferralPayment
from .utils import get_referral_token_for
from rest_framework import exceptions


class ReferralTokenSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    token = serializers.CharField(required=False)


    def get_owner(self, obj):

        return f"{obj.owner.first_name} {obj.owner.last_name}"

    class Meta:

        model = ReferralToken

        fields = ["id", "owner", "token", "active", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        hashed_email = get_referral_token_for(user.email)[:21]
        referral_token_instance = ReferralToken.objects.create(
            owner=user,
            token=hashed_email
        )

        return referral_token_instance

    def update(self, instance, validated_data):
        user = self.context["request"].user
        hashed_email = get_referral_token_for(user.email)[:21]
        instance.token = hashed_email
        instance.save()
        return instance



class ReferralPaymentSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()

    def get_owner(self, obj):

        return f"{obj.owner.first_name} {obj.owner.last_name}"

    class Meta:

        model = ReferralPayment

        fields = fields = ["id", "owner", "cash_out", "unpaid_referrals", "paid_referrals", "created_at", "updated_at"]

    def create(self, validated_data):
        token_instance = self.context["token_instance"]
        user = token_instance.owner
        pay_instance = None
        pay_instance = ReferralPayment.objects.filter(owner=user).first()
        if pay_instance is not None:
            pay_instance.unpaid_referrals+=1
            pay_instance.save()

            return pay_instance

        referral_pay_instance = ReferralPayment.objects.create(
            owner=user,
            unpaid_referrals=1
        )

        return referral_pay_instance