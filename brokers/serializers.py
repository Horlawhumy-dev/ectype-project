from rest_framework import serializers

from .models import EctypeBroker, EctypeBrokerServer


class EctypeBrokerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EctypeBroker
        fields = "__all__"


class EctypeBrokerServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EctypeBrokerServer
        fields = "__all__"
