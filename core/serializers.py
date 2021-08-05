from django.contrib.auth.models import Group
from rest_framework import serializers

from core.models import User


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        exclude = ("permissions",)


class UserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = (
            "last_login",
            "date_joined",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )
        extra_kwargs = {
            "password": {
                "write_only": True,  # does not expose field in GET
                "min_length": 8,  # minimum length of password
                "style": {"input_type": "password"},  # for browsable API
            },
        }
