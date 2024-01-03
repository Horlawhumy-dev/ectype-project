import stripe
import logging
from datetime import datetime
from django.conf import settings
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from notification.models import Notification
from payment.thread import SendSubscriptionInvoiceEmailThread
from referral.models import ReferralPayment

from payment.models import Billing, Card, Plan, Receipt, Subscription
from payment.serializers import (
	 CardDataSerializer,
	 CardSerializer,
	 CreateCardSerializer,
	 PlanSerializer,
	 ReceiptProcessSerializer,
	 ReceiptSerializer,
	 SubscriptionSerializer,
	 ChargeCardSerializer,
	 ValidateCardChargeSerializer,
	 VerifyPaymentSerializer
)
from users.serializers import PermissionSerializer

#secrets import from settings
stripe.api_key = settings.STRIPE_SECRET_KEY
REFERRAL_PERCENT_PER_HEAD = float(settings.REFERRAL_PERCENT_PER_HEAD)
NAIRA_PER_DOLLAR_RATE = float(settings.NAIRA_PER_DOLLAR_RATE)
REFERRAL_MULTIPLIER = REFERRAL_PERCENT_PER_HEAD / 100
MAXIMUM_ACCOUNT_SLOTS = int(settings.MAXIMUM_ACCOUNT_SLOTS)

# helper functions
def get_referral_compensation(PLAN_PRICE):
	return REFERRAL_MULTIPLIER * PLAN_PRICE

def get_equivalent_naira_for(amount):
	return NAIRA_PER_DOLLAR_RATE * amount



class PlanViewSet(viewsets.ReadOnlyModelViewSet):
	serializer_class = PlanSerializer
	queryset = Plan.objects.all()


class ReceiptViewSet(viewsets.ModelViewSet):
	serializer_class = ReceiptSerializer
	http_method_names = [
		"get",
		"post",
		"head",
		"options",
		"trace",
	]

	def get_queryset(self):
		return Receipt.objects.filter(user=self.request.user)

	def create(self, request, *args, **kwargs):
		try:
			plan = Plan.objects.get(id=request.data["plan"])
		except Plan.DoesNotExist as err:
			logging.debug(err)
			return Response(
				{
					"error": "Plan does not exist.",
					"status_code": 404
				}
			)

		perm = plan.features[0]
		plan_value = int(perm.get("data", {}).get("value", 0))

		total_slot_value = request.user.total_slots + plan_value

		if total_slot_value >= MAXIMUM_ACCOUNT_SLOTS:
			logging.info(f"{request.user.email} has reached max slots.")
			return Response(
				{
					"error": f"Sorry, you have reached the maximum {MAXIMUM_ACCOUNT_SLOTS} slots.",
					"status_code": 400
				}
			)

		serializer = self.serializer_class(data=request.data)
		serializer.is_valid(raise_exception=True)
		serializer.save(user=request.user)
		return Response(serializer.data, status=status.HTTP_201_CREATED)

	@action(
		detail=True,
		methods=["post"],
		serializer_class=ReceiptProcessSerializer,
		permission_classes=[IsAuthenticated]
	)
	def process_receipt(self, request: Request, *args, **kwargs):			

		serializer = self.serializer_class(data=request.data)

		serializer.is_valid(raise_exception=True)	

		card_id = serializer.validated_data.get("card_id")
		stripe_customer_id = request.user.metadata.get("stripe_customer_id")
		receipt: Receipt = self.get_object()
		if receipt.status == "SUCCESSFUL":
			return Response({
				"error": f"Receipt already processed with the {receipt.status} status",
				"status_code": 400
		    })
		else:
			try:
				subscription_payment_intent = stripe.PaymentIntent.create(
					#stripe uses 'cents' instead - reason for multiplying by 100.
					amount=int(receipt.amount_to_pay * 100),
					currency="usd",
					customer=stripe_customer_id,
					payment_method_types=["card"],
					description="Subscription payment in US dollar.",
				)
				# confirm payment intent
				confirm_payment_intent = stripe.PaymentIntent.confirm(  # noqa
					subscription_payment_intent.id,
					payment_method=card_id,
				)
			except Exception as err:
				message = str(err)

				raise serializers.ValidationError(message)

			
			# update the receipt status
			receipt.status = "SUCCESSFUL"
			receipt.save(update_fields=["status"])
			subscription = Subscription.objects.create(
				user=request.user,
				plan=receipt.plan,
				receipt=receipt,
			)
			serializer = SubscriptionSerializer(subscription)

			Notification.objects.create(
				user=subscription.user,
				message=f"You have successfully subscribed to {subscription.plan.name}.",
			)

			"""EXECUTE Thread To SEND Subscription EMAIL"""
			data = {
				"subject": "Ectype Plan Subscription",
				"sender": subscription.user.first_name,
				"email": subscription.user.email,
				"plan_name": subscription.plan.name,
				"expiry_date": subscription.next_subscription_datetime.strftime('%B %m, %Y %H:%M:%S %Z')
			}
			logging.info(f"Sending subscription email to {subscription.user.first_name}")

			SendSubscriptionInvoiceEmailThread(data).start()

			"""
				Update the referral details for the customer if referred by existing customer
			"""

			referrer_email = request.user.referred_by

			#return early - if user was not referred
			if not referrer_email:
				return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


			referral_detail_instance = None
			try:
				referral_detail_instance = ReferralPayment.objects.get(owner__email=referrer_email)
			except ReferralPayment.DoesNotExist as err:
				logging.debug(err)

			#only update if the user was referred

			if referral_detail_instance is not None:
				DOLLAR_PLAN_PRICE = float(receipt.price)
				referral_compensation = get_referral_compensation(DOLLAR_PLAN_PRICE)

				existing_cash_out =  float(referral_detail_instance.cash_out)
				referral_detail_instance.cash_out = existing_cash_out + referral_compensation

				referral_detail_instance.unpaid_referrals = referral_detail_instance.unpaid_referrals - 1
				referral_detail_instance.paid_referrals = referral_detail_instance.paid_referrals + 1
				
				referral_detail_instance.save()
				logging.info(f"Referral payment details updated for {referral_detail_instance.owner.email} at {datetime.now()}")

			return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class BillingViewSet(viewsets.ReadOnlyModelViewSet):
	serializer_class = ReceiptSerializer

	def get_queryset(self):
		return Billing.objects.filter(user=self.request.user)


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
	serializer_class = SubscriptionSerializer

	def get_queryset(self):
		return Subscription.objects.filter(user=self.request.user)


class CardViewSet(viewsets.ModelViewSet):
	"""
	- GET: {base_url}/cards/ - Return all card objects linked to the current auth account alone or user
	- POST:{base_url}/cards/ - Create a new card object for the current auth account, user
	- GET: {base_url}/cards/{card_id}/ - Retrieve a card object detail
	- PATCH: {base_url}/cards/{card_id}/ - Patch the details of a card request
	- DELETE: {base_url}/cards/{card_id}/ - Delete a card object
	"""

	serializer_class = CardSerializer

	def get_queryset(self):
		return Card.objects.filter(user=self.request.user)

	def get_serializer_class(self):
		if self.request.method == "POST":
			return CreateCardSerializer
		return CardSerializer

	def create(self, request: Request):
		"""
		Create a new card object.
		---
		parameters:
			- card_number: field 1
			type: string
			required: true
			description: The value of card number
			- cvv: field 2
			type: string
			required: true
			description: The value of card cvv
			- expiration_date: field 3
			type: string (YYYY-MM-DD)
			required: true
			description: The value of card expiration date
			- save_card: field 4
			type: string
			required: false
			default: true
			description: The value of card cvv
		"""
		serializer = self.get_serializer_class()(data=request.data)
		serializer.is_valid(raise_exception=True)
		save_card = serializer.validated_data.get("save_card", False)
		try:
			bank_card = serializer.save(
					user=request.user,
					save_card=save_card,
			)
		except Exception as err:
			try:
					message = eval(err.args[0]).get("error", {}).get("message")
			except Exception as inner_err:  # noqa
					message = "Can not Process Card details"
			return Response(
					{
						"message": "error occurred while processing card creation",
						"detail": f"{message}",
						"error": str(err),
					},
					status=status.HTTP_400_BAD_REQUEST,
			)
		else:
			if save_card:
					serializer = CardSerializer(request=bank_card)
			else:
					serializer = CardDataSerializer(data=bank_card)
					serializer.is_valid()
			return Response(serializer.data, status=status.HTTP_201_CREATED)


class PermissionAPIView(APIView):
	serializer_class = PermissionSerializer

	def get(self, request: Request):
		slot_param = request.query_params.get("slots")
		if slot_param:
			total_slot = request.user.total_slots
			print(total_slot)
			used_slot = request.user.used_slots
			return Response(
					{
						"total_slots": total_slot,
						"used_slots": used_slot,
						"free_slots": total_slot - used_slot,
					}
			)
		serializer = self.serializer_class(request.user)
		return Response(serializer.data)




"""Flutterwave Payment Views"""

class ChargeCardAPIView(APIView):
	"""View for charging card"""
	permission_classes = [IsAuthenticated]

	serializer_class = ChargeCardSerializer

	def post(self, request, receipt_id):
		"""Post method"""

		# if request.user.total_slots >= MAXIMUM_ACCOUNT_SLOTS:
		# 	logging.info(f"{request.user.email} has reached max slots.")
		# 	return Response(
		# 		{
		# 			"error": f"Sorry, you have reached the maximum {MAXIMUM_ACCOUNT_SLOTS} slots.",
		# 			"status_code": 400
		# 		}
		# 	)

		try:
			receipt = Receipt.objects.get(id=receipt_id)
		except Receipt.DoesNotExist as err:
			logging.debug(err)
			return Response({
				"message": "No billing receipt found",
				"status_code": 404,
				"error": "Invalid billing receipt"
			})

		if receipt.status == "SUCCESSFUL":
			return Response({
				"message": f"Receipt already processed with the {receipt.status} status!",
				"status_code": 400,
				"error": "Processed receipt found!"
			})

		amount_to_pay_in_naira = get_equivalent_naira_for(float(receipt.amount_to_pay))
		request_user_fullname = f"{request.user.first_name} {request.user.last_name}"
		request.data["fullname"] = request_user_fullname
		request.data["currency"] = "NGN"
		request.data["amount"] = str(amount_to_pay_in_naira)
		request.data["email"] = request.user.email

		serializer = self.serializer_class(data=request.data,  context={"request": request})
		if serializer.is_valid():
			response = serializer.charge_card()
			logging.info(f"{request.user.email}: {response.json()['message']} at {datetime.now()}")
			return Response(response.json(), status=response.status_code)
		else:
			return Response(serializer.errors, status=400)


class ValidateCardChargeAPIView(APIView):
	"""View for Validating Card Charge"""
	permission_classes = [IsAuthenticated]

	serializer_class = ValidateCardChargeSerializer

	def post(self, request):
		"""POST Request"""
		serializer = self.serializer_class(data=request.data,  context={"request": request})
		if serializer.is_valid():
			response = serializer.validate_charge()
			logging.info(f"{request.user.email}: {response.json()['message']} at {datetime.now()}")
			return Response(response.json(), status=response.status_code)
		else:
			return Response(serializer.errors, status=400)




class VerifyPaymentAPIView(APIView):
	"""View for Verifying Payment"""
	permission_classes = [IsAuthenticated]

	serializer_class = VerifyPaymentSerializer


	def post(self, request):
		"""POST Request"""
		serializer = self.serializer_class(data=request.data, context={"request": request})
		if serializer.is_valid():
			response = serializer.verify_payment()
			logging.info(f"{request.user.email}: {response.json()['message']} at {datetime.now()}")
			return Response(response.json(), status=response.status_code)
		else:
			return Response(serializer.errors, status=400)


class UpdateReceiptStatus(APIView):
	"""View for update Receipt and make Subscription for payment via Flutterwave only"""
	permission_classes = [IsAuthenticated]

	serializer_class = ReceiptSerializer


	def patch(self, request, receipt_id):
		"""PATCH Request"""
		try:
			receipt = Receipt.objects.get(id=receipt_id)
		except Receipt.DoesNotExist as err:
			logging.debug(err)
			return Response({
				"error": "No receipt found!",
				"status_code": 404
			})


		if request.user != receipt.user:
			return Response({
				"error": "You do not have access to update the receipt!",
				"status_code": 401
		    })

		if receipt.status == "SUCCESSFUL":
			return Response({
				"message": f"Receipt already processed with the {receipt.status} status",
				"status_code": 400,
				"error": "Processed receipt found!"
		    })

		receipt.status = "SUCCESSFUL"
		receipt.save(update_fields=["status"])

		# create subscription for the successful receipt
		subscription = Subscription.objects.create(
			user=request.user,
			plan=receipt.plan,
			receipt=receipt,
		)
		SubscriptionSerializer(subscription).data
		Notification.objects.create(
			user=request.user,
			message=f"You have successfully subscribed to {subscription.plan.name}.",
		)

		referrer_email = request.user.referred_by # could be empty string if not referred

		"""EXECUTE Thread To SEND Subscription EMAIL"""
		data = {
			"subject": "Ectype Plan Subscription",
			"sender": subscription.user.first_name,
			"email": subscription.user.email,
			"plan_name": subscription.plan.name,
			"expiry_date": subscription.next_subscription_datetime.strftime('%B %m, %Y %H:%M:%S %Z')
		}
		logging.info(f"Sending subscription email to {request.user.first_name}")

		SendSubscriptionInvoiceEmailThread(data).start()

		#return early - if user was not referred
		if not referrer_email:
			return Response({
				"message": "You have been subscribed successfully.",
				"status_code": 201
			})

		referral_detail_instance = None
		
		try:
			referral_detail_instance = ReferralPayment.objects.get(owner__email=referrer_email)
		except ReferralPayment.DoesNotExist as err:
			logging.debug(err)

		# #only update if the user was referred

		if referral_detail_instance is not None:
			DOLLAR_PLAN_PRICE = float(receipt.price)
			referral_compensation = get_referral_compensation(DOLLAR_PLAN_PRICE)

			existing_cash_out =  float(referral_detail_instance.cash_out)
			referral_detail_instance.cash_out = existing_cash_out + referral_compensation

			referral_detail_instance.unpaid_referrals = referral_detail_instance.unpaid_referrals - 1
			referral_detail_instance.paid_referrals = referral_detail_instance.paid_referrals + 1
			
			referral_detail_instance.save()

			logging.info(f"Referral payment details updated for {referral_detail_instance.owner.email} at {datetime.now()}")

		return Response({
				"message": "You have been subscribed successfully.",
				"status_code": 201
		})
