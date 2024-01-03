from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.decorators import action

from .models import Notification
from .serializers import NotificationSerializer, SelectNotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    http_method_names = ["get", "put", "patch", "delete", "options", "trace", "head"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=["put"])
    def mark_all_notifications_as_read(self, request: Request, *args, **kwargs):
        all_notifications = Notification.objects.filter(user=request.user)
        data = all_notifications.update(is_read=True)
        return Response({"count": data}, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=["put"], serializer_class=SelectNotificationSerializer
    )
    def mark_notifications_as_read(self, request: Request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        notifications: list[Notification] = serializer.validated_data.get(
            "notifications", []
        )
        list_of_ids = [inst.id for inst in notifications]
        selected_notifications = Notification.objects.filter(id__in=list_of_ids)
        data = selected_notifications.update(is_read=True)
        return Response({"count": data}, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=["put"], serializer_class=SelectNotificationSerializer
    )
    def mark_notifications_as_unread(self, request: Request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        notifications: list[Notification] = serializer.validated_data.get(
            "notifications", []
        )
        list_of_ids = [inst.id for inst in notifications]
        selected_notifications = Notification.objects.filter(id__in=list_of_ids)
        data = selected_notifications.update(is_read=False)
        return Response({"count": data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"])
    def delete_all_notification(self, request: Request, *args, **kwargs):
        all_notifications = Notification.objects.filter(user=request.user)
        data = all_notifications.delete()
        return Response({"count": data}, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["put"], serializer_class=SelectNotificationSerializer
    )
    def delete_notifications(self, request: Request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        notifications: list[Notification] = serializer.validated_data.get(
            "notifications", []
        )
        list_of_ids = [inst.id for inst in notifications]
        selected_notifications = Notification.objects.filter(id__in=list_of_ids)
        data = selected_notifications.delete()
        return Response({"count": data}, status=status.HTTP_200_OK)
