from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "message",
            "is_read",
            "created_at",
            "updated_at",
        ]


class SelectNotificationSerializer(serializers.Serializer):
    notifications = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Notification.objects.all())
    )
