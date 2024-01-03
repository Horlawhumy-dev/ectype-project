import base64
import logging
import time
import requests

from rest_framework import serializers

from django.conf import settings


class TradeSyncBrokers:
    base_url = settings.TRADE_SYNC_API
    username = settings.TRADE_SYNC_KEY
    password = settings.TRADE_SYNC_SECRET

    credentials = f"{username}:{password}"
    credentials_b64 = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials_b64}",
        "Content-Type": "application/json",
    }

    def get_brokers(self, last_id=0, limit=100):
        try:
            response = requests.get(
                f"{self.base_url}/brokers?order=asc&limit={limit}&last_id={last_id}",
                headers=self.headers,
            )

            return response.json()
        except Exception as err:
            logging.debug(err)

    def get_brokerservers(self, last_id=0, limit=100):
        try:
            response = requests.get(
                f"{self.base_url}/broker-servers?order=asc&last_id={last_id}&limit={limit}",
                headers=self.headers,
            )
            return response.json()
        except Exception as err:
            logging.debug(err)


class TradeSync:
    base_url = settings.TRADE_SYNC_API
    username = settings.TRADE_SYNC_KEY
    password = settings.TRADE_SYNC_SECRET

    credentials = f"{username}:{password}"
    credentials_b64 = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials_b64}",
        "Content-Type": "application/json",
    }

    def get_account(self, id):
        try:
            response = requests.get(
                f"{self.base_url}/accounts/{id}", headers=self.headers
            )

            return response.json()
        except Exception as err:
            logging.debug(err)

    """
        func: {get_account_status} Not in use for now!
    """

    # def get_account_status(
    #     self, id, desired_status, polling_interval=1, max_attempts=2
    # ):
    #     """
    #     account_status: str
    #         > allocating
    #         > installing
    #         > attempt_connection
    #         > attempt_success
    #         > attempt_failed
    #         > connection_ok
    #         > connection_slow
    #         > connection_lost
    #     """

    #     attempts = 0
    #     account_status = None
    #     while attempts < max_attempts:
    #         response = self.get_account(id)
    #         status_code = int(response["status"])
    #         if status_code == 200:
    #             data = response["data"]
    #             account_status = data.get("status")
    #             if account_status == desired_status:
    #                 return account_status
    #         attempts += 1
    #         time.sleep(polling_interval)
    #     return account_status

    def add_account(self, data):
        try:
            response = requests.post(
                f"{self.base_url}/accounts", json=data, headers=self.headers
            )
            return response.json()

        except Exception as err:
            logging.debug(err)


    def update_account(self, data, id):
        """This will update account name and any allowed field"""
        try:
            response = requests.patch(
                f"{self.base_url}/accounts/{id}", json=data, headers=self.headers
            )
            return response.json()

        except Exception as err:
            logging.debug(err)

    def update_account_connection(self, data, id):
        """ " This will update password and broker_server"""
        try:
            response = requests.patch(
                f"{self.base_url}/accounts/{id}/connection",
                json=data,
                headers=self.headers,
            )
            return response.json()

        except Exception as err:
            logging.debug(err)

    def delete_account(self, id):
    
        try:
            response = requests.delete(
                f"{self.base_url}/accounts/{id}", headers=self.headers
            )
            return response.json()

        except Exception as err:
            logging.debug(err)

class TradeSyncCopier:
    base_url = settings.TRADE_SYNC_API
    username = settings.TRADE_SYNC_KEY
    password = settings.TRADE_SYNC_SECRET

    credentials = f"{username}:{password}"
    credentials_b64 = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials_b64}",
        "Content-Type": "application/json",
    }

    def create_copier_for(self, data):
    
        try:
            response = requests.post(
                f"{self.base_url}/copiers", json=data, headers=self.headers
            )
            return response.json()

        except Exception as err:
            logging.debug(err)

    def update_account_copier_for(self, data, id):
        """ " This will update mode, risk type and risk value"""
        try:
            response = requests.patch(
                f"{self.base_url}/copiers/{id}", json=data, headers=self.headers
            )
            return response.json()
        except Exception as err:
            logging.debug(err)

    def delete_copier_for(self, id):
        try:
            response = requests.delete(
                f"{self.base_url}/copiers/{id}", headers=self.headers
            )
            return response.json()
        except Exception as err:
            logging.debug(err)

    def get_account_copier(self, id):
        try:
            response = requests.get(
                f"{self.base_url}/copiers/{id}", headers=self.headers
            )
            return response.json()
        except Exception as err:
            logging.debug(err)

    # def get_account_copier_status(
    #     self, id, desired_status, polling_interval=1, max_attempts=5
    # ):
    #     """
    #     account_status: str
    #         > allocating
    #         > installing
    #         > attempt_connection
    #         > attempt_success
    #         > attempt_failed
    #         > connection_ok
    #         > connection_slow
    #         > connection_lost
    #     """

    #     attempts = 0
    #     account_status = None
    #     while attempts < max_attempts:
    #         response = self.get_account_copier(id)
    #         status_code = int(response["status"])
    #         if status_code == 200:
    #             data = response["data"]
    #             account_status = data.get("status")
    #             if account_status == desired_status:
    #                 return account_status
    #         attempts += 1
    #         time.sleep(polling_interval)
    #     return account_status
