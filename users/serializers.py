from rest_framework import serializers

from users.models import User


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "has_active_subscription", "permissions"]
