import uuid
from typing import Any

from django.db import models
from django.utils.translation import gettext_lazy as _


def generate_id(length: int = 10):
    return uuid.uuid4().hex[:length]


class BaseModelMixin(models.Model):
    id = models.CharField(
        primary_key=True, default=generate_id, editable=False, max_length=255
    )
    uid = models.CharField(default=generate_id, editable=False, max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False, db_index=True)
    active = models.BooleanField(_("active"), default=True, db_index=True)

    def __str__(self):
        return f"< {type(self).__name__}({self.id}) >"

    @classmethod
    def _serializer_fields(cls, exclude=[], *args):
        args = ["id", "active", "created_at", "updated_at", *args]
        return sorted(list({field for field in args if field and field not in exclude}))

    @classmethod
    def _serializer_extra_kwargs(cls, exclude=[], **kwargs):
        return {
            key: value for key, value in kwargs.items() if value and key not in exclude
        }

    @classmethod
    def serializer_fields(cls, *args, exclude=[]):
        return cls._serializer_fields(exclude, *args)

    @classmethod
    def serializer_extra_kwargs(cls, exclude=[], **kwargs):
        return cls._serializer_extra_kwargs(exclude, **kwargs)

    def get_field_or_none(self, field_name: str):
        """get a field or return <is not None>,data


        res = getattr(self,field_name,None)\n
        return res is not None,res


        Args:
            field_name (str): _description_

        Returns:
            tuple[bool,Any]: return result . True,Any
        """
        res = getattr(self, field_name, None)
        return res is not None, res

    class Meta:
        abstract = True
        ordering = ["-created_at", "id"]
