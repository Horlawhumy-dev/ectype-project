import logging
import time
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from .utils import get_referral_token_for
from .serializers import ReferralTokenSerializer, ReferralPaymentSerializer
from accounts.utils import APIResponse
from rest_framework import exceptions

from .models import ReferralToken, ReferralPayment
from .thread import SendReferralPaymentWithdrawEMailThread


class ReferralTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:

            referral_token_instance = ReferralToken.objects.get(owner=request.user)

        except ReferralToken.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="You do not have an existing token.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Referral token not found!"
            )

        serializer = ReferralTokenSerializer

        if serializer.is_valid:
            serializer = serializer(referral_token_instance, many=False)

            return APIResponse.send(
                message="Success, your referral token is fetched.",
                status_code=status.HTTP_200_OK,
                data=serializer.data
            )

        return APIResponse.send(
            message="Serializer error occured.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )
            


    def post(self, request):

        try:
            existing_instance = ReferralToken.objects.filter(owner=request.user).first()

        except ReferralToken.DoesNotExist as err:
            logging.debug(err)

        if existing_instance:
            return APIResponse.send(
                message="Please reset your existing token.",
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Existing referral token!"
            )
            
        serializer = ReferralTokenSerializer(data={}, context={"request": request})

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return APIResponse.send(
                message="Your token generated successfully",
                status_code=status.HTTP_201_CREATED,
                data=serializer.data
            )

        return APIResponse.send(
            message="Serializer error occured.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )



    def patch(self, request):
        try:

            referral_token_instance = ReferralToken.objects.get(owner=request.user)

        except ReferralToken.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="You do not have an existing token.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="No referral token found!"
            )
        if referral_token_instance.owner.email != request.user.email:
            return APIResponse.send(
                message="You are not authorized to reset the token.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized access!"
            )

        serializer = ReferralTokenSerializer(
            instance=referral_token_instance, 
            context={"request": request}, data={}, partial=True)

        if serializer.is_valid():
            serializer.save()
            return APIResponse.send(
                message="Your token resetted successfully",
                status_code=status.HTTP_201_CREATED,
                data=serializer.data
            )

        return APIResponse.send(
            message="Serializer error occured.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )

        

class ReferralPaymentView(APIView):
    permission_classes = []

    def post(self, request):

        try:
            referral_token_instance = ReferralToken.objects.get(token=request.data["token"])
        except ReferralToken.DoesNotExist as err:
            return APIResponse.send(
                message="Invalid referral token given",
                status_code=status.HTTP_404_NOT_FOUND,
                error="No referral token record found!"
            )

        serializer = ReferralPaymentSerializer(data={}, context={"token_instance": referral_token_instance})

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return APIResponse.send(
                message="Referral added successfully",
                status_code=status.HTTP_201_CREATED,
            )

        return APIResponse.send(
            message="Serializer error occured.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )



class GetReferralPayment(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Referral details view"""
        try:
            referral_pay_instance = ReferralPayment.objects.get(owner=request.user)
        except ReferralPayment.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="You do not have referral details.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="You have not referred anybody."
            )

        serializer = ReferralPaymentSerializer

        if serializer.is_valid:
            data = serializer(referral_pay_instance, many=False).data

            return APIResponse.send(
                message=f"Your referral details successfully fetched.",
                status_code=status.HTTP_200_OK,
                data=data,
            )


class ReferralPaymentWithdrawalView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            referral_pay_instance = ReferralPayment.objects.get(owner=request.user)
        except ReferralPayment.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                status_code=status.HTTP_404_NOT_FOUND,
                error="You have not made any referral yet."
            )

        MINIMUM_AMOUNT_PER_WITHDRAWAL = 10.00 #USD
        if float(referral_pay_instance.cash_out) < MINIMUM_AMOUNT_PER_WITHDRAWAL:
            return APIResponse.send(
                status_code=status.HTTP_400_BAD_REQUEST,
                error=f"Sorry, your referral balance is less than ${MINIMUM_AMOUNT_PER_WITHDRAWAL}."
            )
            
        subject = "Request for Ectype Referral Payouts"
        SendReferralPaymentWithdrawEMailThread(email=request.user.email, subject=subject, user=request.user.first_name).start()

        return APIResponse.send(
            message="Referral payout would be processed soon.",
            status_code=status.HTTP_200_OK
        )


