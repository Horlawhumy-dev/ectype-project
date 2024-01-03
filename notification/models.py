from django.db import models
from ectype_bend_beta.model_utils import BaseModelMixin


class Notification(BaseModelMixin):
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
