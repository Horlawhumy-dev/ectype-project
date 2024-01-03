import uuid
from django.db import models
from ectype_bend_beta.model_utils import BaseModelMixin

# Create your models here.


def generate_id(length: int = 10):
    return uuid.uuid4().hex[:length]


class EctypeBroker(models.Model):
    id = models.CharField(
        primary_key=True, default=generate_id, editable=False, max_length=255
    )
    tradesync_broker_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    mt_version = models.CharField(max_length=10)

    def __str__(self):
        return self.id


class EctypeBrokerServer(models.Model):
    id = models.CharField(
        primary_key=True, default=generate_id, editable=False, max_length=255
    )
    broker_id = models.CharField(max_length=100)
    tradesync_brokerserver_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    mt_version = models.CharField(max_length=10)

    def __str__(self):
        return self.name
