from rest_framework import serializers

from payment.models import Card, Plan, Receipt, Subscription
from .utils import send_charge_otp

class PlanSerializer(serializers.ModelSerializer):
	class Meta:
		model = Plan
		fields = [
			"id",
			"name",
			"price",
			"duration",
			"billing_interval",
			"created_at",
			"updated_at",
			"features",
		]


class ReceiptSerializer(serializers.ModelSerializer):
	status = serializers.ReadOnlyField()

	class Meta:
		model = Receipt
		fields = [
			"id",
			"plan",
			"vat",
			"status",
			"price",
			"amount_to_pay",
			"plan_name",
			"created_at",
			"updated_at",
		]

	def create(self, validated_data: dict):
		plan: Plan = validated_data.get("plan")
		receipt = Receipt.objects.create(price=plan.price, **validated_data)
		return receipt


class SubscriptionSerializer(serializers.ModelSerializer):
	plan = serializers.StringRelatedField()
	receipt = serializers.StringRelatedField()

	class Meta:
		model = Subscription
		fields = [
			"id",
			"plan",
			"price",
			"active",
			"receipt",
			"start_date",
			"end_date",
		]


class CreateCardSerializer(serializers.Serializer):
	"""
	Serializer class for validating card details for card creation.
	"""

	token = serializers.CharField(max_length=255, required=False)

	def create(self, validated_data):
		user = validated_data.get("user")  # noqa
		try:
			bank_card = Card.create_card(
				**validated_data,
			)
		except Exception as err:
			raise err
		else:
			return bank_card


class CardSerializer(serializers.ModelSerializer):
	"""
	Model Serializer for retrieving model instance from the database
	"""

	class Meta:
		model = Card
		fields = (
			"id",
			"name",
			"brand",
			"funding",
			"is_default",
			"last_4_digits",
		)


class CardDataSerializer(serializers.Serializer):
	"""
	Serializer to support serialization of card data that are not saved to the database.
	"""

	id = serializers.CharField(required=True)
	name = serializers.CharField(required=True)
	brand = serializers.CharField(required=True)
	funding = serializers.CharField(required=True)
	is_default = serializers.BooleanField(required=False, default=False)
	last_4_digits = serializers.CharField(required=True)


class ReceiptProcessSerializer(serializers.Serializer):
	card_id = serializers.CharField()


"""Payment Serializers"""

import random
import string
import logging
from datetime import datetime
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .wave import Flutterwave
from .thread import SendChargeOTPThread

User = get_user_model()
flutterwave = Flutterwave()


class ChargeCardSerializer(serializers.Serializer):
	"""Serializer for collecting card details"""

	card_number = serializers.CharField(write_only=True)
	cvv = serializers.CharField(write_only=True)
	expiry_month = serializers.CharField(write_only=True)
	expiry_year = serializers.CharField(write_only=True)
	currency = serializers.CharField(default='NGN', write_only=True)
	amount = serializers.CharField(write_only=True)
	fullname = serializers.CharField(write_only=True)
	email = serializers.EmailField(write_only=True)
	pin = serializers.CharField(write_only=True)

	@staticmethod
	def get_transaction_reference(length=24):
		"""Generate Transaction Random String"""
		letters = string.ascii_lowercase
		random_str = ''.join(random.choice(letters) for i in range(length))
		ectype_transaction_reference = f'ECTYPE-{datetime.now().year}-{random_str.upper()}'

		return	ectype_transaction_reference

	def charge_card(self):
		"""Charge Card"""
		self.is_valid(raise_exception=True)
		data = {
			"card_number": self.validated_data.get('card_number'),
			"cvv": self.validated_data.get('cvv'),
			"expiry_month": self.validated_data.get('expiry_month'),
			"expiry_year": self.validated_data.get('expiry_year'),
			"currency": self.validated_data.get('currency'),
			"amount": self.validated_data.get('amount'),
			"fullname": self.validated_data.get('fullname'),
			"email": self.validated_data.get('email'),
			# "phone_number": "2348029733525",
			"tx_ref": ChargeCardSerializer.get_transaction_reference(),
			"authorization": {
				"mode": "pin",
				"pin": self.validated_data.get('pin')
			}
		}
		response = flutterwave.charge_card(data)	
		if response.status_code in [200, 201]:
			# execute otp task
			customer =  response.json()["data"]["customer"]
			customer["phone"] = customer.get("phone", "08029733525") #default to that number
			logging.info(f"Sending Charge OTP to Customer Email at {datetime.now()}")
			SendChargeOTPThread(customer).start()
		return response

	

	def create(self, validated_data):
		"""Create Method"""
		pass

	def update(self, instance, validated_data):
		"""Update Method"""
		pass


class ValidateCardChargeSerializer(serializers.Serializer):
	"""Serializer for confirming payment"""

	otp = serializers.CharField()
	flw_ref = serializers.CharField()

	def validate_charge(self):
		"""Validate charge"""
		self.is_valid(raise_exception=True)
		flw_ref = self.validated_data.get('flw_ref')
		otp = self.validated_data.get('otp')
		response = flutterwave.validate_charge(flw_ref, otp)
		return response

	def update(self, instance, validated_data):
		"""Update Method"""
		pass

	def create(self, validated_data):
		"""Create Method"""
		pass



class VerifyPaymentSerializer(serializers.Serializer):
	"""Serializer for Verifying payment"""

	transaction_id = serializers.CharField()

	def verify_payment(self):
		"""Verify Payment"""
		self.is_valid(raise_exception=True)
		_id = self.validated_data.get('transaction_id')
		response = flutterwave.verify_transaction(_id)
		return response

	def update(self, instance, validated_data):
		"""Update Method"""
		pass

	def create(self, validated_data):
		"""Create Method"""
		pass