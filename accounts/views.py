import logging
import random
from datetime import datetime

from rest_framework import filters, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework import serializers


from .models import EctypeTradeAccount, EctypeCopierTrade
from notification.models import Notification

from .serializers import (
    TradingAccountSerializer,
    EctypeCopierTradeSerializer,
    EctypeSingleCopierTradeSerializer
)

from .tradesync import TradeSync, TradeSyncCopier
from .utils import APIResponse

from .thread import SendTradeAccountEmailThread

# make tradesync instances
tradesync = TradeSync()
tradesynccopier = TradeSyncCopier()

# tradesync account status types
# fetch account status again and again if status is one of these
# account_status_type = [
#     "installing",
#     "allocating",
#     "attempt_connection",
#     "attempt_success",
#     "connection_slow",
#     "connection_lost",
# ]


# default name generator method for trading account
def generate_account_name_for(request):
    name = f"{request.user.first_name}{random.randint(1, 10001)}"
    return name


class ExactMatchFilterBackend(filters.BaseFilterBackend):
    """
    A custom filter backend for exact matches.
    """

    def filter_queryset(self, request, queryset, view):
        filters = {}
        for field in view.search_fields:
            value = request.query_params.get(field)
            if value is not None:
                filters[field] = value
        return queryset.filter(**filters)


class AccountsListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Trading Account Details"""

        try:
            queryset = EctypeTradeAccount.objects.filter(user=request.user).order_by(
                "-created_at"
            )
        except EctypeTradeAccount.DoesNotExist as err:
            logging.debug(err)

        total_items = queryset.count()
        page = request.query_params.get("page", None)
        ZERO = 0

        if page is not None and int(page) <= ZERO:
            return APIResponse.send(
                message="Negative or Zero page value not allowed.",
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                error="Invalid page number."
            )

        if page is not None and int(page) > total_items:
            return APIResponse.send(
                message="Page number given more than accounts.",
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                error="Invalid page number."
            )
        if page is not None:
            per_page = 1  # Set the number of items per page

            # Calculate the start and end indices for pagination
            start_index = (int(page) - 1) * per_page
            end_index = int(page) * per_page
            paginated_qs = queryset[start_index:end_index]

            serializer = TradingAccountSerializer(paginated_qs, many=True)

            for index, account in enumerate(paginated_qs):
                response = tradesync.get_account(id=int(account.tradesync_account_id))
                if response["status"] not in [200, 201]:
                    logging.info(response["message"])
                    return APIResponse.send(
                        message=response["message"],
                        status_code=response["status"],
                        error=response["message"]
                    )

                # because those metadata fields are not available if account is not connected
                if response["data"]["status"] == "connection_ok":
                    account_metadata = {
                        "account_status": response["data"]["status"],
                        "currency": response["data"]["currency"],
                        "balance": response["data"]["balance"],
                        "total_profit": response["data"]["total_profit"],
                        "last_ping": response["data"]["last_ping"],
                    }

                    serializer.data[index]["metadata"] = account_metadata

                else:
                    account_metadata = {
                        "account_status": response["data"]["status"],
                        "login_response": response["data"]["login_response"],
                    }
                    serializer.data[index]["metadata"] = account_metadata

            return APIResponse.send(
                message="Trading accounts successfully fetched.",
                status_code=status.HTTP_200_OK,
                count=total_items,
                data=serializer.data,
            )

        # else return all querysets without paginations
        serializer = TradingAccountSerializer(queryset, many=True)

        # this is to fetch some dynamic fields from tradesync
        for index, account in enumerate(queryset):
            response = tradesync.get_account(id=int(account.tradesync_account_id))
            if response["status"] not in [200, 201]:
                logging.info(response["message"])
                return APIResponse.send(
                    message=response["message"],
                    status_code=response["status"],
                    error=response["message"]
                )

            # because those metadata fields are not available if account is not connected
            if response["data"]["status"] == "connection_ok":
                account_metadata = {
                    "account_status": response["data"]["status"],
                    "currency": response["data"]["currency"],
                    "balance": response["data"]["balance"],
                    "total_profit": response["data"]["total_profit"],
                    "last_ping": response["data"]["last_ping"],
                }
                serializer.data[index]["metadata"] = account_metadata
            else:
                account_metadata = {
                    "account_status": response["data"]["status"],
                    "login_response": response["data"]["login_response"],
                }
                serializer.data[index]["metadata"] = account_metadata

        return APIResponse.send(
            message=f"Trading accounts successfully fetched.",
            status_code=status.HTTP_200_OK,
            count=total_items,
            data=serializer.data,
        )


class AccountCopiersListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Trading Account Copiers Details"""
        try:
            queryset = EctypeCopierTrade.objects.filter(
                user=request.user
            ).order_by("-created_at")
        except EctypeCopierTrade.DoesNotExist as err:
            logging.debug(err)

        total_items = queryset.count()
        page = request.query_params.get("page", None)

        if page is not None and int(page) > total_items:
            return APIResponse.send(
                message="Page number given more than number of accounts.",
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                error="Invalid page number."
            )

        if page is not None:
            per_page = 1

            # Calculate the start and end indices for pagination
            start_index = (int(page) - 1) * per_page
            end_index = int(page) * per_page
            paginated_qs = queryset[start_index:end_index]

            serializer = EctypeCopierTradeSerializer(paginated_qs, many=True)

            if serializer.is_valid:

                return APIResponse.send(
                    message="Trading accounts copiers successfully fetched.",
                    status_code=status.HTTP_200_OK,
                    count=total_items,
                    data=serializer.data,
                )
            
            return APIResponse.send(
            message="Serializer error eccountered.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )

        # else return all querysets
        serializer = EctypeCopierTradeSerializer(queryset, many=True)
        if serializer.is_valid:
            return APIResponse.send(
                message=f"Trading account copiers successfully fetched.",
                status_code=status.HTTP_200_OK,
                count=total_items,
                data=serializer.data,
            )

        return APIResponse.send(
            message="Serializer error eccountered.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )


class TradingAccountsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Add a trading account"""

        if not request.user.has_active_subscription:
            logging.info(f"{request.user.email} has no active subscription")
            return APIResponse.send(
                message="Sorry, you do not have an active subscription.",
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Sorry, you do not have active subscription."
            )

        if request.user.current_subscription.first().status in ["EXPIRED", "expired"]:
            logging.info(f"{request.user.email} subscription has expired")
            return APIResponse.send(
                message="Sorry, your current subscription has expired!",
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Sorry, your current subscription has expired!"
            )

        if request.user.free_slots <= 0:
            logging.info(f"{request.user.email} has no available slots.")
            return APIResponse.send(
                message="Sorry, you have exhausted your subscribed slots.",
                status_code=status.HTTP_400_BAD_REQUEST,
                error="No more available slots for you!"
            )

        

        try:
            trading_account = EctypeTradeAccount.objects.filter(
                user=request.user,
                account_number=request.data["account_number"]
            ).order_by("-created_at")
        except EctypeTradeAccount.DoesNotExist as err:
            logging.debug(err)

        if trading_account:
            return APIResponse.send(
                message="Trading Account with same number exists!",
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Account already exists"
            )

        acct_name = generate_account_name_for(request)

        data = {
            "mt_version": int(request.data["account_type"]),
            "account_name": request.data.get("account_name", None)
            if request.data.get("account_name", None) is not None
            else acct_name,
            "account_number": int(request.data["account_number"]),
            "password": request.data["account_password"],
            "broker_server_id": int(request.data["broker_server"]),
        }
        # make POST request to tradesync
        response = tradesync.add_account(data)

        if response["status"] not in [200, 201]:
            logging.info(response["message"])
            return APIResponse.send(
                message=response["message"],
                status_code=response["status"],
                error=response["message"]
            )
            
        # attach tradesync account id and generated name
        request.data["tradesync_account_id"] = response["data"]["id"]
        request.data["account_name"] = response["data"]["account_name"]

        serializer = TradingAccountSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            instance = serializer.save()
            logging.info(
                f"{request.user.email} successfully added trading account at {datetime.now()}"
            )

            Notification.objects.create(
                user=request.user, message=f"Trading Account added successfully"
            )
            
            """EXECUTE Thread To Send Add Success Email"""
            data = {
                "subject": "Ectype Add Account",
                "receiver": request.user.first_name,
                "email": request.user.email,
                "type": "add"
            }
            logging.info(f"Sending account add email to {request.user.first_name}")

            SendTradeAccountEmailThread(data).start() #start threading

            return APIResponse.send(
                message="Success! Allow your account to connect in few seconds.",
                status_code=status.HTTP_201_CREATED,
            )

        return APIResponse.send(
            message="Serializer error eccountered.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )


class TradingAccountsConnectionUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk, *args, **kwargs):
        """Trading Account Details Update Connection"""
        try:
            trading_account = EctypeTradeAccount.objects.get(id=pk)
        except EctypeTradeAccount.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="Trading Account does not exists!",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Account not found!"
            )
            

        # these are the only fields required for update on tradesync API
        data = {
            "password": request.data.get(
                "account_password", trading_account.account_password
            ),
            "broker_server_id": request.data.get(
                "broker_server", trading_account.broker_server
            ),
        }

        response = tradesync.update_account_connection(
            data, int(trading_account.tradesync_account_id)
        )
        if response["status"] not in [200, 201]:
            logging.info(response["message"])
            return APIResponse.send(
                message=response["message"],
                status_code=response["status"],
                error=response["message"]
            )

        serializer = TradingAccountSerializer(
            instance=trading_account,
            data=request.data,
            context={"request": request, "method": "patch"},
            partial=True,
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            logging.info(f"Successfully updated trading account for {request.user.email} at {datetime.now()}")
            Notification.objects.create(
                user=request.user,
                message="You have successfully updated an account connection data.",
            )
            return APIResponse.send(
                message="Trading account connection detail successfully patched.",
                status_code=status.HTTP_201_CREATED,
            )

        return APIResponse.send(
            message="Serializer error eccountered.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )


class TradingAccountsUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        """Trading Account Details Get for one or more fields update"""
        try:
            trading_account = EctypeTradeAccount.objects.get(id=pk)
        except EctypeTradeAccount.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="Trading Account does not exists!",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Account not found!"
            )
        response = tradesync.get_account(id=int(trading_account.tradesync_account_id))

        serializer = TradingAccountSerializer

        if serializer.is_valid:
            data = serializer(trading_account, many=False).data
            if response["status"] not in [200, 201]:
                logging.info(response["message"])
                return APIResponse.send(
                    message=response["message"],
                    status_code=response["status"],
                    error=response["message"]
                )


            # because those metadata fields are not available if account is not connected
            if response["data"]["status"] == "connection_ok":
                account_metadata = {
                    "account_status": response["data"]["status"],
                    "currency": response["data"]["currency"],
                    "balance": response["data"]["balance"],
                    "total_profit": response["data"]["total_profit"],
                    "last_ping": response["data"]["last_ping"],
                }
                data["metadata"] = account_metadata
            else:
                account_metadata = {
                    "account_status": response["data"]["status"],
                    "login_response": response["data"]["login_response"],
                }
                data["metadata"] = account_metadata

            return APIResponse.send(
                message=f"Trading account successfully fetched.",
                status_code=status.HTTP_200_OK,
                data=data,
            )

        return APIResponse.send(
            message="Serializer error eccountered.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )

    def patch(self, request, pk, *args, **kwargs):
        """Trading Account Details Patch for one or more fields update"""
        try:
            trading_account = EctypeTradeAccount.objects.get(id=pk)
        except EctypeTradeAccount.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="Trading Account does not exists!",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Account not found!"
            )

        # this is the required field for update on tradesync API
        data = {
            "account_name": request.data.get(
                "account_name", generate_account_name_for(request)
            )
        }

        response = tradesync.update_account(
            data, int(trading_account.tradesync_account_id)
        )
        if response["status"] not in [200, 201]:
            logging.info(response["message"])
            return APIResponse.send(
                message=response["message"],
                status_code=response["status"],
                error=response["message"]
            )


        serializer = TradingAccountSerializer(
            instance=trading_account,
            data=request.data,
            context={"request": request, "method": "patch"},
            partial=True,
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            logging.info(f"Successfully patched trading account for {request.user.email} at {datetime.now()}")
            Notification.objects.create(
                user=request.user,
                message="You have successfully updated an account.",
            )
            return APIResponse.send(
                message=f"Trading account successfully patched.",
                status_code=status.HTTP_201_CREATED,
            )

        return APIResponse.send(
            message="Serializer error eccountered.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )

    def delete(self, request, pk, *args, **kwargs):
        try:
            trading_account = EctypeTradeAccount.objects.get(id=pk)
        except EctypeTradeAccount.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="Trading Account does not exists!",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Account not found!"
            )

        if trading_account.user != request.user:
            return APIResponse.send(
                message="You do not have access to this resource!",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized request!"
            )
        
        copier_instances = EctypeCopierTrade.objects.all()
        # do not delete if the account is still a follower to a copier
        for copier in copier_instances.values():
            # Filter the follower_ids list to remove the specific follower
            for follower in copier["follower_ids"]:
                if follower["id"] == trading_account.id:
                    return APIResponse.send(
                        message="Sorry, this account is stil copied. Kindly delete its copy first!",
                        status_code=status.HTTP_400_BAD_REQUEST,
                        error="Account still copied!"
                    )
           

        response = tradesync.delete_account(trading_account.tradesync_account_id)
        if response["status"] not in [200, 201]:
            logging.info(response["message"])
            return APIResponse.send(
                message=response["message"],
                status_code=response["status"],
                error=response["message"]
            )

        trading_account.delete()
        Notification.objects.create(
            user=request.user,
            message="You have successfully deleted an account.",
        )
        return APIResponse.send(
            message=f"Trading account deleted.", status_code=status.HTTP_204_NO_CONTENT
        )


class TradingAccountsCopierView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """ " Add a trading account Copier"""
        lead_id = request.data["lead_id"]
        follower_id = request.data["follower_id"]

        if lead_id == follower_id:
            return APIResponse.send(
                message="Cloning from the same account is not allowed.",
                status_code=status.HTTP_403_FORBIDDEN,
                error="Lead and Follower accounts provided are equal.",
            )
        
        existing_copier_instance = None
        try:
            existing_copier_instance = EctypeCopierTrade.objects.get(lead_id=lead_id)
        except EctypeCopierTrade.DoesNotExist as err:
            logging.debug(err)

    
        if existing_copier_instance is not None:
            return APIResponse.send(
                message="Found existing copy for this lead account. Kindly add more follower instead!",
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Account copy exists!"
            )
        try:
            lead_instance = EctypeTradeAccount.objects.get(id=lead_id)
        except EctypeTradeAccount.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="Lead Account does not exist!",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Account does not exists!"
            )

        try:
            follower_instance = EctypeTradeAccount.objects.get(
                id=follower_id
            )
        except EctypeTradeAccount.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="Follower Account does not exist!",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Account does not exists!"
            )


        # due to different key/value fields from our UI to tradesync

        data = {
            "lead_id": lead_instance.tradesync_account_id,
            "follower_id": follower_instance.tradesync_account_id,
            "risk_type": request.data["risk_type"],
            "risk_value": request.data["risk_multiplier"],
        }

        # make POST request to tradesync
        response = tradesynccopier.create_copier_for(data)

        if response["status"] not in [200, 201]:
            logging.info(response["message"])
            return APIResponse.send(
                message=response["message"],
                status_code=response["status"],
                error=response["message"]
            )
            
        # only save new instance if it does not exist before
        new_copier_data = {
            "lead_id": request.data["lead_id"],
            "risk_type": request.data["risk_type"],
            "risk_multiplier": request.data["risk_multiplier"],
            "metadata": {
                "copy_tp": response["data"]["copy_tp"],
                "copy_sl": response["data"]["copy_sl"],
                "max_lot": response["data"]["max_lot"],
                "force_min": response["data"]["force_min"],
                "slippage": response["data"]["slippage"],
                "copy_pending": response["data"]["copy_pending"],
                "reverse": response["data"]["reverse"],
                "is_lead_copy": True
            },
            "follower_ids":   [{
                "id": follower_instance.id,
                "name": follower_instance.account_name,
                "tradesync_copier_id": response["data"]["id"],
                "metadata": {
                    "mode": response["data"]["mode"],
                    "risk_type": response["data"]["risk_type"],
                    "risk_value": response["data"]["risk_value"],
                    "copy_tp": response["data"]["copy_tp"],
                    "copy_sl": response["data"]["copy_sl"],
                    "max_lot": response["data"]["max_lot"],
                    "force_min": response["data"]["force_min"],
                    "slippage": response["data"]["slippage"],
                    "copy_pending": response["data"]["copy_pending"],
                    "reverse": response["data"]["reverse"],
                    "is_lead_copy": True
                }
            }]
            
        }

        serializer = EctypeCopierTradeSerializer(data=new_copier_data, context={"request": request})

        if serializer.is_valid(raise_exception=True):
            serializer.save()
                
            logging.info(
                f"{request.user} successfully added trading account copier at {datetime.now()}"
                )

            Notification.objects.create(
                user=request.user,
                message="You have just successfully copied accounts.",
            )

            """EXECUTE Thread To Send Copy Success Email"""
            data = {
                "subject": "Ectype Copy Account",
                "receiver": request.user.first_name,
                "email": request.user.email,
                "type": "copy"
            }
            logging.info(f"Sending account add email to {request.user.first_name}")

            SendTradeAccountEmailThread(data).start() #start threading

            return APIResponse.send(
                message="Account successfully copied together.",
                status_code=status.HTTP_201_CREATED
            )
    
        return APIResponse.send(
            message="Serializer error eccountered.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )


class AddMoreFollowersCopierView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """ Sync all trading account Copier together"""
        list_of_followers = request.data["followers"]
        copier_id = request.data["copier_id"]
        
        try:
            existing_copier_instance = EctypeCopierTrade.objects.get(id=copier_id)
        except EctypeCopierTrade.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message="No existing account copy found!",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Account copy does not exist!"
            )


        lead_id = existing_copier_instance.lead_id
        
        if lead_id in list_of_followers:
            return APIResponse.send(
                message="Lead account found among followers",
                status_code=status.HTTP_400_BAD_REQUEST,
                error="Cannot copy from same account!"
            )
        try:
            lead_instance = EctypeTradeAccount.objects.get(id=lead_id)
        except EctypeTradeAccount.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                  message=f"Lead Account with id {lead_id} does not exist!",
                  status_code=status.HTTP_404_NOT_FOUND,
                  error="Account not found."
            )
        
        for follower_id in list_of_followers:
            follower_instance = None
           
            try:
                follower_instance = EctypeTradeAccount.objects.get(id=follower_id)
            except EctypeTradeAccount.DoesNotExist as err:
                logging.debug(err)
                return APIResponse.send(
                    message=f"Follower Account with id {follower_id} does not exist!",
                    status_code=status.HTTP_404_NOT_FOUND,
                    error="Account not found."
                )
            data = {
                "lead_id": lead_instance.tradesync_account_id,
                "follower_id": follower_instance.tradesync_account_id,
                "risk_type": existing_copier_instance.risk_type,
                "risk_value": existing_copier_instance.risk_multiplier
            }
            # make POST request to tradesync copier API
            response = tradesynccopier.create_copier_for(data)
            if response["status"] not in [200, 201]:
                logging.info(response["message"])
                return APIResponse.send(
                    message=response["message"],
                    status_code=response["status"],
                    error=response["message"]
                )
            
            # then there is an instance already
            if existing_copier_instance is not None:
                # update fields for existing instance
                existing_copier_instance.follower_ids.append(
                     {
                        "id": follower_instance.id,
                        "name": follower_instance.account_name,
                        "tradesync_copier_id": response["data"]["id"],
                        "metadata": {
                            "mode": response["data"]["mode"],
                            "risk_type": response["data"]["risk_type"],
                            "risk_value": response["data"]["risk_value"],
                            "copy_tp": response["data"]["copy_tp"],
                            "copy_sl": response["data"]["copy_sl"],
                            "max_lot": response["data"]["max_lot"],
                            "force_min": response["data"]["force_min"],
                            "slippage": response["data"]["slippage"],
                            "copy_pending": response["data"]["copy_pending"],
                            "reverse": response["data"]["reverse"],
                            "is_lead_copy": False
                        }
                    }
                )
                existing_copier_instance.save()

        count = len(list_of_followers)
            
        logging.info(f"Successfully added more followers copier for {request.user.email} at {datetime.now()}")

        Notification.objects.create(
           user=request.user,
           message="You have successfully added more follower accounts to a copy.",
        )

        return APIResponse.send(
            message=f"You have successfully copied {count} more follower(s).",
            status_code=status.HTTP_201_CREATED
        )


class TradingAccountsCopierUpdateView(APIView):
    permission_classes = []

    def get(self, request, pk, *args, **kwargs):
        """Trading Account Copier Details"""
        try:
            ectype_copier_trade_instance = EctypeCopierTrade.objects.get(id=pk)
        except EctypeCopierTrade.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message=f"No trading account copy found.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Account copy does not exist!"
            )

        serializer = EctypeCopierTradeSerializer

        if serializer.is_valid:
            data = serializer(ectype_copier_trade_instance, many=False).data
            return APIResponse.send(
                message=f"Trading account copy is successfully fetched.",
                status_code=status.HTTP_200_OK,
                data=data
            )
        return APIResponse.send(
            message="Serializer error eccountered.",
            status_code=status.HTTP_400_BAD_REQUEST,
            error=str(serializer.errors)
        )
    
    def get_copier_update_data(self, request, trading_account_copier, follower):
        data = {
            "mode": request.data.get("mode", trading_account_copier.mode),
            "risk_type": request.data.get(
                "risk_type", trading_account_copier.risk_type
            ),
            "risk_value": request.data.get(
                "risk_multiplier", trading_account_copier.risk_multiplier
            ),
            "copy_tp": request.data.get(
                "copy_tp", trading_account_copier.metadata["copy_tp"]
            ),
            "copy_sl": request.data.get(
                "copy_sl", trading_account_copier.metadata["copy_sl"]
            ),
            "max_lot": request.data.get(
                "max_lot", trading_account_copier.metadata["max_lot"]
            ),
            "slippage": request.data.get(
                "slippage", trading_account_copier.metadata["slippage"]
            ),
            "force_min": request.data.get(
                "force_min", trading_account_copier.metadata["force_min"]
            )
        }

        return data

    def patch(self, request, pk, *args, **kwargs):
        """Trading Account Copier Details Patch for one or more fields update"""
        try:
            ectype_copier_instance = EctypeCopierTrade.objects.get(id=pk)
        except EctypeCopierTrade.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message=f"No trading account copy found.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Account copy does not exist!"
            )
        
        followers = ectype_copier_instance.follower_ids

        for index in range(len(followers)):
            
            # make PUT request to tradesync API
            data = self.get_copier_update_data(request, ectype_copier_instance, followers[index])
            response = tradesynccopier.update_account_copier_for(
                data, followers[index]["tradesync_copier_id"]
            )

            if response["status"] not in [200, 201]:
                logging.info(response["message"])
                return APIResponse.send(
                    message=response["message"],
                    status_code=response["status"],
                    error=response["message"]
                )
            
           
            request.data["metadata"] = {
                "mode": response["data"]["mode"],
                "risk_type": response["data"]["risk_type"],
                "risk_value": response["data"]["risk_value"],
                "copy_pending": response["data"]["copy_pending"],
                "max_lot": response["data"]["max_lot"],
                "reverse": response["data"]["reverse"],
                "copy_sl": response["data"]["copy_sl"],
                "copy_tp": response["data"]["copy_tp"],
                "force_min": response["data"]["force_min"],
                "slippage": response["data"]["slippage"],
                "is_lead_copy": ectype_copier_instance.follower_ids[index]["metadata"]["is_lead_copy"]

            }
             #update follower metadata
            ectype_copier_instance.follower_ids[index]["metadata"] = request.data["metadata"]
            
            serializer = EctypeCopierTradeSerializer(
                instance=ectype_copier_instance,
                data=request.data,
                context={"request": request, "method": "patch"},
                partial=True,
            )
            if serializer.is_valid():
                serializer.save()
                logging.info(f"Successfully updated copier for {request.user.email} at {datetime.now()}")

        Notification.objects.create(
            user=request.user,
            message="You have successfully updated your copy.",
        )


        return APIResponse.send(
            message=f"Your copier is successfully updated.",
            status_code=status.HTTP_201_CREATED
        )

    def delete(self, request, pk, *args, **kwargs):
        try:
            ectype_copier_trade = EctypeCopierTrade.objects.get(id=pk)
        except EctypeCopierTrade.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message=f"No trading account copy found.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Account copy does not exist!"
            )

        if ectype_copier_trade.user != request.user:
            return APIResponse.send(
                message= "You do not have access to this resource.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized access"
            )

        followers = ectype_copier_trade.follower_ids
        
        for follower in followers:
            response = tradesynccopier.delete_copier_for(
                follower["tradesync_copier_id"]
            )


            if response["status"] not in [200, 201]:
                logging.info(response["message"])
                return APIResponse.send(
                    message=response["message"],
                    status_code=response["status"],
                    error=response["message"]
                )

        ectype_copier_trade.delete()
        Notification.objects.create(
            user=request.user,
            message="You have successfully deleted a copy.",
        )
        return APIResponse.send(
            message=f"Trading account copy is deleted.",
            status_code=status.HTTP_204_NO_CONTENT
        )


class UpdateDeleteSingleCopierFromGroupView(APIView):
    permission_classes = [IsAuthenticated]


    def find_follower_copier_from(self, followers, follower_id):
        tradesync_copier_id, copier_index = -1, -1
        for index in range(len(followers)):
            if followers[index]["id"] == follower_id:
                tradesync_copier_id = followers[index]["tradesync_copier_id"]
                copier_index = index
                break

        return (tradesync_copier_id, copier_index)

    def get_follower_copier_data(self, request, trading_account_copier, follower_copier_index):
        copier = trading_account_copier.follower_ids[follower_copier_index]
        data = {
            "mode": request.data.get("mode", copier["metadata"]["mode"]),
            "risk_type": request.data.get(
                "risk_type", copier["metadata"]["risk_type"]
            ),
            "risk_value": request.data.get(
                "risk_multiplier", copier["metadata"]["risk_value"]
            ),
            "copy_tp": request.data.get(
                "copy_tp", copier["metadata"]["copy_tp"]
            ),
            "copy_sl": request.data.get(
                "copy_sl", copier["metadata"]["copy_sl"]
            ),
            "max_lot": request.data.get(
                "max_lot", copier["metadata"]["max_lot"]
            ),
            "slippage": request.data.get(
                "slippage", copier["metadata"]["slippage"]
            ),
            "force_min": request.data.get(
                "force_min", copier["metadata"]["force_min"]
            )
        }

        return data

    def get_lead_copier_update_data(self, request, trading_account_copier, follower_copier_index):
        data = {
            "mode": request.data.get("mode", trading_account_copier.mode),
            "risk_type": request.data.get(
                "risk_type", trading_account_copier.risk_type
            ),
            "risk_value": request.data.get(
                "risk_multiplier", trading_account_copier.risk_multiplier
            ),
            "copy_tp": request.data.get(
                "copy_tp", trading_account_copier.metadata["copy_tp"]
            ),
            "copy_sl": request.data.get(
                "copy_sl", trading_account_copier.metadata["copy_sl"]
            ),
            "max_lot": request.data.get(
                "max_lot", trading_account_copier.metadata["max_lot"]
            ),
            "slippage": request.data.get(
                "slippage", trading_account_copier.metadata["slippage"]
            ),
            "force_min": request.data.get(
                "force_min", trading_account_copier.metadata["force_min"]
            )
        }

        return data
 
    def unpack_metadata_from(self, response, ectype_copier_instance):
        data = {
            "mode": response["data"]["mode"],
            "risk_type": response["data"]["risk_type"],
            "risk_value": response["data"]["risk_value"],
            "copy_pending": response["data"]["copy_pending"],
            "max_lot": response["data"]["max_lot"],
            "reverse": response["data"]["reverse"],
            "copy_sl": response["data"]["copy_sl"],
            "copy_tp": response["data"]["copy_tp"],
            "force_min": response["data"]["force_min"],
            "slippage": response["data"]["slippage"],
            "is_lead_copy": ectype_copier_instance.follower_ids[copier_index_to_update]["metadata"]["is_lead_copy"]

        }

        return data

    
    def patch(self, request, copier_id, follower_id, *args, **kwargs):
        """Trading Account Copier Details patch for a follower fields update"""
        try:
            ectype_copier_instance = EctypeCopierTrade.objects.get(id=copier_id)
        except EctypeCopierTrade.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                message=f"No trading account copy found.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Lead copy does not exist!"
            )
        if ectype_copier_instance.user != request.user:
            return APIResponse.send(
                message= "You do not have access to this resource.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized access"
            )
        
        followers = ectype_copier_instance.follower_ids
        tradesync_copier_id_to_delete, copier_index_to_update = self.find_follower_copier_from(followers, follower_id)

        if tradesync_copier_id_to_delete == -1:
            return APIResponse.send(
                message= "No follower account copier matches.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Follower copy does not exist!"
            )

        # just to diff the global metadata
        data = {}
        if ectype_copier_instance.follower_ids[copier_index_to_update]["metadata"]["is_lead_copy"]:
            data = self.get_lead_copier_update_data(request, ectype_copier_instance, copier_index_to_update)
        else:
            data = self.get_follower_copier_data(request, ectype_copier_instance, copier_index_to_update)
        
        # make PUT request to tradesync API
        response = tradesynccopier.update_account_copier_for(
            data, tradesync_copier_id_to_delete
        )

        if response["status"] not in [200, 201]:
            logging.info(response["message"])
            return APIResponse.send(
                message=response["message"],
                status_code=response["status"],
                error=response["message"]
            )
        #unpack metadata to update
        request.data["metadata"] = self.unpack_metadata_from(response, ectype_copier_instance)

        serializer = EctypeSingleCopierTradeSerializer(
            instance=ectype_copier_instance,
            data=request.data,
            context={"request": request, "method": "patch", "index": copier_index_to_update},
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            logging.info(f"Successfully updated followed copier for {request.user.email} at {datetime.now()}")
           
            Notification.objects.create(
                user=request.user,
                message="You have successfully updated a copy from its group.",
            )
            return APIResponse.send(
                message="Your follower copy is successfully updated.",
                status_code=status.HTTP_201_CREATED
            )
        else:
            return APIResponse.send(
                message="Serializer error occured.",
                status_code=status.HTTP_400_BAD_REQUEST,
                error=str(serializer.errors)
            )


    def delete(self, request, copier_id, follower_id, *args, **kwargs):
        try:
            ectype_copier_trade = EctypeCopierTrade.objects.get(id=copier_id)
        except EctypeCopierTrade.DoesNotExist as err:
            logging.debug(err)
            return APIResponse.send(
                # message=f"No trading account copy found.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Lead copy does not exist!"
            )

        if ectype_copier_trade.user != request.user:
            return APIResponse.send(
                # message= "You do not have access to this resource.",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error="Unauthorized access to delete copy"
            )

        # Get the follower copier to delete
        followers = ectype_copier_trade.follower_ids
        tradesync_copier_id_to_delete, copier_index_to_delete = self.find_follower_copier_from(followers, follower_id)

        if tradesync_copier_id_to_delete == -1:
            return APIResponse.send(
                # message= "No follower account copy that matches.",
                status_code=status.HTTP_404_NOT_FOUND,
                error="Follower copy does not exist!"
            )

        # make DELETE request to tradesync API
        response = tradesynccopier.delete_copier_for(
            tradesync_copier_id_to_delete
        )

        if response["status"] not in [200, 201]:
            logging.info(response["message"])
            return APIResponse.send(
                # message=response["message"],
                status_code=response["status"],
                error=response["message"]
            )

        # Delete copy from Ectype database
        lenght_of_copier_followers = len(ectype_copier_trade.follower_ids)
        follower_id_to_delete = ectype_copier_trade.follower_ids[copier_index_to_delete]["id"]

        if lenght_of_copier_followers == 1:
            ectype_copier_trade.delete() # delete whole copy instance
            logging.info(f"Successfully deleted copier at {datetime.now()}")
            Notification.objects.create(
                user=request.user,
                message="You have successfully deleted the copy.",
            )
            return APIResponse.send(
                message="The copy instance is deleted.",
                status_code=status.HTTP_204_NO_CONTENT,
            )

        #check if copy to delete is lead/first copy
        is_lead_copy = ectype_copier_trade.follower_ids[copier_index_to_delete]["metadata"]["is_lead_copy"]
        
        del ectype_copier_trade.follower_ids[copier_index_to_delete] #list index already decreased but yet to save to db
        
        # update the global metadata to next follower copier if present
        if is_lead_copy:
            ectype_copier_trade.metadata = ectype_copier_trade.follower_ids[0]["metadata"]
            ectype_copier_trade.follower_ids[0]["metadata"]["is_lead_copy"] = True
        
        #save the instance having deleted the follower from its group
        ectype_copier_trade.save()
    
        logging.info(f"Successfully deleted copier at {datetime.now()}")
        Notification.objects.create(
            user=request.user,
            message="You have successfully deleted a copy from its group.",
        )
        return APIResponse.send(
            message="The copy is deleted from its group.",
            status_code=status.HTTP_204_NO_CONTENT,
        )
