import logging
import time
from django.shortcuts import render

from rest_framework import generics, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from accounts.utils import APIResponse

from accounts.views import ExactMatchFilterBackend

from .models import EctypeBroker, EctypeBrokerServer
from .serializers import EctypeBrokerSerializer, EctypeBrokerServerSerializer


class EctypeBrokersListAPIView(generics.ListAPIView):
    queryset = EctypeBroker.objects.all()
    serializer_class = EctypeBrokerSerializer
    filter_backends = [ExactMatchFilterBackend]
    search_fields = ["name", "mt_version", "tradesync_broker_id"]
    permission_classes = [AllowAny]
    pagination_class = None


class EctypeBrokerServersListAPIView(generics.ListAPIView):
    queryset = EctypeBrokerServer.objects.all()
    serializer_class = EctypeBrokerServerSerializer
    filter_backends = [ExactMatchFilterBackend]
    search_fields = ["name", "mt_version", "broker_id", "tradesync_brokerserver_id"]
    permission_classes = [AllowAny]
    pagination_class = None


class GetEctypeBroker(APIView):
    permission_classes = [AllowAny]
    pagination_class = None

    def get(self, request, pk, *args, **kwargs):
        try:
            Ectypebroker = EctypeBroker.objects.get(id=pk)

        except EctypeBroker.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message=f"EctypeBroker with id {pk} does not exist.",
                status_code=status.HTTP_404_NOT_FOUND,
                error=str(err),
            )

        serializer = EctypeBrokerSerializer

        if serializer.is_valid:
            data = serializer(Ectypebroker, many=False).data
            return APIResponse.send(
                message="Success. EctypeBroker is fetched",
                status_code=status.HTTP_200_OK,
                count=1,
                data=data,
            )

        return APIResponse.send(
            message="Serializer error",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.erorrs),
        )


class GetEctypeBrokerServer(APIView):
    permission_classes = [AllowAny]
    pagination_class = None

    def get(self, request, pk, *args, **kwargs):
        try:
            Ectypebroker = EctypeBrokerServer.objects.get(id=pk)
        except EctypeBrokerServer.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message=f"EctypeBroker Server with id {pk} does not exist.",
                status_code=status.HTTP_404_NOT_FOUND,
                error=str(err),
            )

        serializer = EctypeBrokerServerSerializer

        if serializer.is_valid:
            data = serializer(Ectypebroker, many=False).data
            return APIResponse.send(
                message="Success. EctypeBroker server fetched",
                status_code=status.HTTP_200_OK,
                count=1,
                data=data,
            )

        return APIResponse.send(
            message="Serializer error",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.erorrs),
        )


# used to load brokers to remote database

# class LoadBrokers(APIView):
#     permission_classes = []

#     def get(self, request, *args, **kwargs):
#         tr = TradeSyncBrokers()

#         response = tr.get_brokerservers(last_id=3671,limit=10)
#         # print(response["data"])
#         for data in response["data"]:
#             EctypeBrokerServer.objects.create(
#                 broker_id=data["broker_id"],
#                 tradesync_brokerserver_id=data["id"],
#                 name=data["name"],
#                 mt_version=data["mt_version"]
#             )
#         # for data in response["data"]:
#         #     EctypeBroker.objects.create(
#         #         tradesync_broker_id=data["id"],
#         #         name=data["name"],
#         #         mt_version=data["mt_version"]
#         #     )

#         return APIResponse.send(
#             message=response["meta"]["last_id"],
#             status_code=200
#         )
