from rest_framework import serializers

from .models import EctypeTradeAccount, EctypeCopierTrade
from .utils import get_hashed_password_for


class TradingAccountSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    class Meta:
        model = EctypeTradeAccount
        fields = "__all__"

    def create(self, validated_data):
        user = self.context["request"].user
        hashed_pasword = get_hashed_password_for(validated_data["account_password"])
        trading_account = EctypeTradeAccount.objects.create(
            user=user,
            account_name=validated_data["account_name"],
            account_number=validated_data["account_number"],
            account_type=validated_data["account_type"],
            # account_status=validated_data["account_status"],
            account_password=hashed_pasword,
            broker_server=validated_data["broker_server"],
            broker_name=validated_data["broker_name"],
            tradesync_account_id=validated_data["tradesync_account_id"],
            metadata=validated_data["metadata"],
        )

        return trading_account

    def update(self, instance, validated_data):
        user = self.context["request"].user

        if user.email != instance.user.email:
            raise serializers.ValidationError({"User": "Unauthorized request user"})

        hashed_password = get_hashed_password_for(
            validated_data.get("account_password", instance.account_password)
        )
        instance.account_name = validated_data.get(
            "account_name", instance.account_name
        )
        instance.account_number = validated_data.get(
            "account_number", instance.account_number
        )
        instance.account_type = validated_data.get(
            "account_type", instance.account_type
        )
        instance.account_password = hashed_password
        instance.broker_server = validated_data.get(
            "broker_server", instance.broker_server
        )
        instance.tradesync_account_id = validated_data.get(
            "tradesync_account_id", instance.tradesync_account_id
        )
        instance.broker_name = validated_data.get("broker_name", instance.broker_name)
        instance.metadata = validated_data.get("metadata", instance.metadata)

        instance.save()
        return instance


# class CopierSerializer(serializers.ModelSerializer):
#     user = serializers.SerializerMethodField()
#     lead = serializers.SerializerMethodField()
#     follower = serializers.SerializerMethodField()

#     def get_instance(self, id):
#         instance = EctypeTradeAccount.objects.get(id=id)
#         return instance

#     def get_lead(self, obj):
#         lead = self.get_instance(obj.lead_id)
#         return lead.account_name

#     def get_follower(self, obj):
#         follower = self.get_instance(obj.follower_id)
#         return follower.account_name

#     def get_user(self, obj):
#         return f"{obj.user.first_name} {obj.user.last_name}"

#     class Meta:
#         model = EctypeTradeAccountCopier
#         fields = [
#             "id",
#             "user",
#             "lead_id",
#             "lead",
#             "follower_id",
#             "follower",
#             "risk_multiplier",
#             "risk_type",
#             "tradesync_copier_id",
#             "mode",
#             "metadata",
#             "created_at",
#         ]

#     follower_id = serializers.CharField(required=False)

#     def create(self, validated_data):
#         user = self.context["request"].user
#         trading_account_copier = EctypeTradeAccountCopier.objects.create(
#             user=user,
#             lead_id=validated_data["lead_id"],
#             follower_id=validated_data["follower_id"],
#             risk_multiplier=validated_data["risk_multiplier"],
#             risk_type=validated_data["risk_type"],
#             tradesync_copier_id=validated_data["tradesync_copier_id"],
#             metadata=validated_data["metadata"],
#         )

#         return trading_account_copier

#     def update(self, instance, validated_data):
#         user = self.context["request"].user

#         if user.email != instance.user.email:
#             raise serializers.ValidationError({"User": "Unauthorized request user"})

#         instance.mode = validated_data.get("mode", instance.mode)
#         instance.risk_type = validated_data.get("risk_type", instance.risk_type)
#         instance.risk_multiplier = validated_data.get(
#             "risk_multiplier", instance.risk_multiplier
#         )
#         instance.metadata = validated_data.get("metadata", instance.metadata)
#         instance.save()
#         return instance


class EctypeCopierTradeSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    lead = serializers.SerializerMethodField()

    def get_instance(self, id):
        instance = EctypeTradeAccount.objects.get(id=id)
        return instance
    
    def get_lead(self, obj):
        lead = self.get_instance(obj.lead_id)
        return lead.account_name

    def get_user(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    
    class Meta:

        model = EctypeCopierTrade
        fields = "__all__"


    def create(self, validated_data):
        user = self.context["request"].user
        ectype_copier_trade = EctypeCopierTrade.objects.create(
            user=user,
            lead_id=validated_data["lead_id"],
            follower_ids = validated_data["follower_ids"],
            risk_multiplier=validated_data["risk_multiplier"],
            risk_type=validated_data["risk_type"],
            metadata=validated_data["metadata"]
        )

        return ectype_copier_trade
    
    def update(self, instance, validated_data):
        user = self.context["request"].user
        instance.mode = validated_data.get("mode", instance.mode)
        instance.risk_type = validated_data.get("risk_type", instance.risk_type)
        instance.risk_multiplier = validated_data.get(
            "risk_multiplier", instance.risk_multiplier
        )
        instance.metadata = validated_data.get(
            "metadata",
            instance.metadata
        )
        instance.save()
        return instance





class EctypeSingleCopierTradeSerializer(serializers.ModelSerializer):
    class Meta:

        model = EctypeCopierTrade
        fields = "__all__"
    
    def update(self, instance, validated_data):
        user = self.context["request"].user
        follower_index = self.context["index"]
        follower_copier = instance.follower_ids[follower_index]
        #update global metadata for lead copy only
        if follower_copier["metadata"]["is_lead_copy"]:
            instance.metadata = validated_data.get(
                "metadata",
                instance.metadata
            )
            instance.mode = instance.metadata["mode"]
            instance.risk_type = instance.metadata["risk_type"]
            instance.risk_value = instance.metadata["risk_value"]

        instance.follower_ids[follower_index]["metadata"] = validated_data.get("metadata", instance.metadata)
        instance.save()
        return instance