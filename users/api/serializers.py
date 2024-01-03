from typing import Any, Dict  # noqa
import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _
from djoser import serializers as dj_serializers
from djoser.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.request import Request
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db import IntegrityError, transaction

from users.models import User as UserType
from users.models import UserLoginRecord
from referral.models import ReferralToken
from users.token import default_token_generator

from referral.models import ReferralPayment
from notification.models import Notification
from rest_framework.response import Response
from datetime import datetime

User = get_user_model()


class UserSerializer(serializers.ModelSerializer[UserType]):
    name = serializers.SerializerMethodField()
    two_fa = serializers.SerializerMethodField()

    def get_two_fa(self, obj):
        return obj.metadata["2fa"]

    def get_name(self, obj):
        return obj.name or obj.first_name

    class Meta:
        model = User
        fields = ["name", "url", "two_fa"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "pk"},
        }

    


class JwtTokenObtainPair(TokenObtainPairSerializer):
    default_error_messages = {"no_active_account": _("Incorrect login credentials.")}

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["roles"] = list(user.groups.values_list("name", flat=True))
        # ...

        return token

    def validate(self, attrs):
        request: HttpRequest or Request = self.context.get("request")  # noqa
        credentials = {"email": attrs.get("email"), "password": attrs.get("password")}

        # This is answering the original question, but do whatever you need here.
        # For example in my case I had to check a different model that stores more user info
        # But in the end, you should obtain the username to continue.

        user_obj = User.objects.filter(Q(email=str(attrs.get("email")).lower())).first()

        res = super().validate(credentials)
        # attach user to the serializer
        user_data = UserSerializer(user_obj, context=self.context).data

        return {
            **user_data,
            **res,
        }



class CustomUserCreateSerializer(dj_serializers.UserCreateSerializer):
    token = serializers.CharField(required=False)
    class Meta(dj_serializers.UserCreateSerializer.Meta):
        fields = ("first_name", "last_name", "email", "password", "country", "address", "token")


    def create(self, validated_data):
        try:
            user = self.perform_create(validated_data)
        except IntegrityError:
            self.fail("cannot_create_user")

        #No other choice but to do it here.
        if not isinstance(user, User):
            return user
        else:
            referral_pay_instance = None
            referrer = None
            try:
                referral_pay_instance = ReferralPayment.objects.get(owner__email=user.referred_by)
            except ReferralPayment.DoesNotExist as err:
                logging.debug(err)

            if referral_pay_instance is not None:
                referral_pay_instance.unpaid_referrals+=1
                referral_pay_instance.save()
            else:
                referrer = User.objects.get(email=user.referred_by)
                ReferralPayment.objects.create(
                    owner=referrer,
                    unpaid_referrals=1
                )

            logging.info(
                f"Referral is successfully added for {user.referred_by} around {datetime.now()}"
            )

            Notification.objects.create(
                user=referrer or referral_pay_instance.owner, message=f"You have successfully referred {user.first_name} {user.last_name}"
            )

            return user

    def perform_create(self, validated_data):
        user = None
        with transaction.atomic():
            referral_token = validated_data.get("token", None)
            token_instance = None
            if referral_token:

                token_instance = ReferralToken.objects.filter(token=referral_token).first()

                if token_instance is None:
                    raise serializers.ValidationError({"error": "Invalid token provided.", "status_code": 400})

                else:
                    user = User.objects.create_user(
                        referred_by=token_instance.owner.email,
                        **validated_data
                    )
            else:
                user = User.objects.create_user(**validated_data)
                
            if settings.SEND_ACTIVATION_EMAIL and user is not None:
                user.is_active = False
                user.save(update_fields=["is_active"])
        return user





class EmailAndTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()

    default_error_messages = {
        "invalid_token": settings.CONSTANTS.messages.INVALID_TOKEN_ERROR,
        "invalid_email": settings.CONSTANTS.messages.INVALID_UID_ERROR,
    }

    def validate(self, attrs):
        validated_data = super().validate(attrs)

        # uid validation have to be here, because validate_<field_name>
        # doesn't work with modelserializer
        try:
            email = self.initial_data.get("email", "")
            self.user = User.objects.get(email=email)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError) as e:
            key_error = "invalid_email"
            raise ValidationError(
                {"email": [self.error_messages[key_error]]}, code=key_error
            ) from e

        is_token_valid = default_token_generator.check_token(
            self.user, self.initial_data.get("token", "")
        )
        if is_token_valid:
            return validated_data
        else:
            key_error = "invalid_token"
            raise ValidationError(
                {"token": [self.error_messages[key_error]]}, code=key_error
            )


class ActivationSerializer(EmailAndTokenSerializer):
    default_error_messages = {
        "stale_token": settings.CONSTANTS.messages.STALE_TOKEN_ERROR
    }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not self.user.is_active:
            return attrs
        raise PermissionDenied(self.error_messages["stale_token"])


class PasswordResetConfirmSerializer(
    EmailAndTokenSerializer, dj_serializers.PasswordSerializer
):
    pass


class UserActiveChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(write_only=True, required=True)

    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ("new_password", "old_password")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "Old password and new passwords can't be the same."
                    ]
                }
            )

        if not self.instance.check_password(attrs["old_password"]):
            raise serializers.ValidationError(
                {"old_password": ["Password is incorrect."]}
            )

        return attrs

    def update(self, instance, validated_data) -> User:
        user = self.context["request"].user

        if user.pk != instance.pk:
            raise serializers.ValidationError(
                {"authorize": "You do not have permission to update the password."}
            )
        instance.set_password(validated_data.get("new_password", instance.password))
        instance.save()
        return instance


class ActiveUserAccountUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class UserLoginActivitySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    class Meta:
        model = UserLoginRecord
        fields = (
            "id",
            "user",
            "login_success",
            "device_type",
            "ip_address",
            "login_time",
        )


class TwoFactorSetupSerializer(serializers.Serializer):
    otpauth_url = serializers.CharField(read_only=True)


class TwoFactorVerifySerializer(serializers.Serializer):
    code = serializers.CharField()


class Disable2FASerializer(serializers.Serializer):
    code = serializers.CharField(max_length=12, required=True)


class UserDetailViewSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return f"{obj.first_name.capitalize()} {obj.last_name.capitalize()}"

    class Meta:
        model = User
        fields = ["id", "name", "email", "address", "country", "metadata"]
