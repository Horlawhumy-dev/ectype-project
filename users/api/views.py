import logging
from datetime import datetime
from django.contrib.auth import authenticate, get_user_model, login
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt import views as auth_views
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .serializers import JwtTokenObtainPair, UserSerializer
from users.models import UserLoginRecord
from django.contrib.auth import get_user_model

User = get_user_model()

def get_client_ip_and_device(request):
    device_name = request.headers.get("x-device-name", "Unknown Device")
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")

    return (ip, device_name)

def log_user_logged_in_success(sender, request, **kwargs):
    ip, device_name = get_client_ip_and_device(request)
    try:
        UserLoginRecord.objects.create(
            ip_address=ip, user=sender, device_type=device_name, login_success=True
        )

        logging.info(f"{sender.email}'s login request on {ip} was successful with {device_name} around {datetime.now()}")

    except Exception as e:
        logging.debug(e)


def log_user_logged_in_failure(sender, request, **kwargs):
    ip, device_name = get_client_ip_and_device(request)
    logging.info(f"{sender}'s login request on {ip} failed with {device_name} around {datetime.now()}")



class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "pk"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class CreateLoginToken(auth_views.TokenObtainPairView):
    permission_classes = []
    serializer_class = JwtTokenObtainPair

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            log_user_logged_in_failure(sender=request.data["email"], request=request)
            raise InvalidToken(e.args[0])
        except AuthenticationFailed as e:
            log_user_logged_in_failure(sender=request.data["email"], request=request)
            raise ValidationError(dict(detail=e.args[0]))

        user = authenticate(
            request, username=request.data["email"], password=request.data["password"]
        )
        if user is not None:
            # If the user is authenticated, log them in using Django's login method
            # this is required to keep track of user logins activity
            login(request, user)

            # Call the signal receiver function to log the user login
            log_user_logged_in_success(sender=user, request=request)

            return Response(serializer.validated_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)