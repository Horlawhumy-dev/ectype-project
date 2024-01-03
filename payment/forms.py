from django import forms
from django_jsonform.forms.fields import JSONFormField

from .models import Plan
from .platform_features import PlatformFeatures

features_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Give short note about the feature.",
            },
            "on": {
                "type": "boolean",
                "description": "Enable or diable feature",
                "default": False,
            },
            "uid": {
                "type": "string",
                "enum": [x.value for x in PlatformFeatures],
                "enumNames": [x.name.replace("_", " ") for x in PlatformFeatures],
                "description": "platform feature id",
            },
            "data": {
                "additionalProperties": True,
                "type": "object",
                "properties": {}
                # "oneOf": [
                #     {
                #         "if": {"properties": {"uid": {"const": x.value}}},
                #         "then": PlatformFeatures.get_schema(x)
                #     }
                #     for x in PlatformFeatures
                # ],
            },
        },
        "required": ["name", "on", "uid"],
    },
}


class PlanForm(forms.ModelForm):
    features = JSONFormField(
        label="features",
        schema=features_schema,
    )

    class Meta:
        model = Plan
        fields = "__all__"
