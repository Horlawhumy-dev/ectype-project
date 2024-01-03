import logging
import re

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView


from accounts.utils import APIResponse
from users.api.serializers import (
    ActiveUserAccountUpdateSerializer,
    Disable2FASerializer,
    UserActiveChangePasswordSerializer,
    UserDetailViewSerializer,
    UserLoginActivitySerializer,
)
from users.models import UserLoginRecord

User = get_user_model()


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        assert (
            self.request.user.is_authenticated
        )  # for mypy to know that the user is authenticated
        return self.request.user.get_absolute_url()

    def get_object(self):
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


# Temporary View Method for account signup redirect with social auth
def homepage(request):
    return render(
        request=request,
        template_name="users/home.html",
    )


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


google_login = GoogleLogin.as_view()


class ActiveUserAccountChangePasswordView(APIView):
    """This view is actually for an active/logged in user to change password"""

    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        serializer = UserActiveChangePasswordSerializer(
            data=request.data,
            instance=request.user,
            context={"request": request},
            partial=True,
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return APIResponse.send(
                message="Password updated successfully.",
                status_code=status.HTTP_201_CREATED,
            )

        return APIResponse.send(
            message="Invalid serializers",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors),
        )


update_active_password = ActiveUserAccountChangePasswordView.as_view()


class ActiveUserAccountUpdateProfile(APIView):
    """This view is actually for an active/logged in user to update profile data"""

    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = self.request.user  # Get the authenticated user

        # Check if the user exists
        if not user:
            return APIResponse.send(
                message="User is not found.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Unknown request user",
            )

        # Not for password/email update
        if (
            request.data.get("password", None)
            or request.data.get("email", None) is not None
        ):
            return APIResponse.send(
                message="Sorry, this endpoint is not meant for password/email update.",
                status_code=status.HTTP_403_FORBIDDEN,
                error="Invalid endpoint invoked",
            )

        # Not for password/email update
        if request.data.get("2fa", None) is not None:
            return APIResponse.send(
                message="Sorry, this is meant for 2fa update request.",
                status_code=status.HTTP_403_FORBIDDEN,
                error="Invalid endpoint invoked",
            )

        serializer = ActiveUserAccountUpdateSerializer(
            instance=user, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return APIResponse.send(
                message="Success! Your profile data is updated.",
                status_code=status.HTTP_201_CREATED,
            )
        return APIResponse.send(
            message="Serializer error.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors),
        )


update_active_profile = ActiveUserAccountUpdateProfile.as_view()

class UserLoginActivityGetView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserLoginActivitySerializer

    def get_queryset(self):
        return UserLoginRecord.objects.select_related().filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        paginated_data = self.paginate_queryset(queryset)

        if paginated_data is not None:
            serializer = self.get_serializer(paginated_data, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



# class UserLoginActivityGetView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         try:
#             user_login_record_instance = UserLoginRecord.objects.select_related().filter(
#                 user=request.user
#             )

#         except UserLoginRecord.DoesNotExist as err:
#             logging.debug(err)
#             return APIResponse.send(
#                 message="No activity logs found.",
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 error=str(err)
#             )

#         serializer = UserLoginActivitySerializer(user_login_record_instance, many=True)

#         if serializer.is_valid:
#             return APIResponse.send(
#                 message="Success. Login activity logs found.",
#                 status_code=status.HTTP_200_OK,
#                 count=user_login_record_instance.count(),
#                 data=serializer.data
#             )

#         return APIResponse.send(
#             message="Serializer error occured.",
#             status_code=status.HTTP_400_BAD_REQUEST,
#             error=str(serializer.errors)
#         )


get_user_login_activities = UserLoginActivityGetView.as_view()


class UserLoginActivityDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, *args, **kwargs):
        try:
            user_login_activity_instance = UserLoginRecord.objects.get(id=pk)
        except UserLoginRecord.DoesNotExist as e:
            return APIResponse.send(
                message="Login activity logs not found",
                status_code=status.HTTP_404_NOT_FOUND,
                error=str(e)
            )
        except Exception as e:
            return APIResponse.send(
                message="Exception occurred",
                status_code=status.HTTP_400_BAD_REQUEST,
                error=str(e)
            )

        user_login_activity_instance.delete()
        return APIResponse.send(
            message="Success. Login activity log deleted.",
            status_code=status.HTTP_200_OK,
        )


delete_user_login_activity = UserLoginActivityDeleteView.as_view()


class TwoFactorSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            totp_device, created = TOTPDevice.objects.get_or_create(user=user)
        except Exception as err:
            logging.debug(err)

            return APIResponse.send(
                message="2FA was not set up.",
                status_code=status.HTTP_400_BAD_REQUEST,
                error=str(err)
            )

        totp_device.save()
        # parse out secret code from the 2fa url response
        secret = None
        pattern = r"secret=([^&]+)"
        match = re.search(pattern, totp_device.config_url)

        if match:
            secret = match.group(1)

        return APIResponse.send(
            message="2FA URL is successfully created.",
            status_code=status.HTTP_201_CREATED,
            data={"secret": secret, "2fa_url": totp_device.config_url}
        )


class TwoFactorVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        token = request.data.get("code")

        try:
            totp_device = TOTPDevice.objects.filter(user=user).first()
        except TOTPDevice.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="2FA record was not found.",
                status_code=status.HTTP_404_NOT_FOUND,
                error=str(err)
            )

        if not totp_device:
            return APIResponse.send(
                message="2FA was not setup.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="User has not setup 2FA"
            )
        if totp_device.verify_token(int(token)):
            # updated detail for 2fa enabled
            user = User.objects.get(email=request.user.email)
            user.metadata["2fa"] = True
            user.save()
            return APIResponse.send(
                message="2FA verified successfully.", status_code=status.HTTP_200_OK
            )
        else:
            return APIResponse.send(
                message="Invalid token provided.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized token provided."
            )


two_factor_setup_view = TwoFactorSetupView.as_view()
two_factor_verify_view = TwoFactorVerifyView.as_view()


class Disable2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = Disable2FASerializer(data=request.data)

        if serializer.is_valid():
            code = serializer.validated_data.get("code")

            try:
                totp_device = TOTPDevice.objects.get(user=user)
            except TOTPDevice.DoesNotExist as err:
                logging.debug(err)
                return APIResponse.send(
                    message="2FA record was not found..",
                    status_code=status.HTTP_404_NOT_FOUND,
                    error=str(err)
                )

            if totp_device.verify_token(int(code)):
                totp_device.delete()
                # updated detail for 2fa disabled
                user = User.objects.get(email=request.user.email)
                user.metadata["2fa"] = False
                user.save()

                return APIResponse.send(
                    message="2FA has been successfully disabled.",
                    status_code=status.HTTP_200_OK
                )
            else:
                return APIResponse.send(
                    message="Invalid 2FA token provided.",
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    error="Token not found."
                )

        return APIResponse.send(
            message="Serializer erorrs.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )


two_factor_disable_view = Disable2FAView.as_view()


class UserDetailView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            user = User.objects.get(email=request.user.email)
        except User.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="user does not exist",
                status_code=status.HTTP_404_NOT_FOUND,
                error=str(err)
            )

        serializer = UserDetailViewSerializer(user, many=False)

        if serializer.is_valid:
            data = serializer.data

            return APIResponse.send(
                message="Details fetched successfully",
                status_code=status.HTTP_200_OK,
                data=data
            )

        return APIResponse.send(
            message="Serializer error",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors),
        )


user_detail_view = UserDetailView.as_view()
