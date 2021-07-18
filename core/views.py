from django.contrib.auth.models import Group
from rest_framework import viewsets

from core.models import User
from core.serializers import GroupSerializer, UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    # authentication_classes = ()  # check defaults in settings
    # permission_classes = ()  # check defaults in settings
    # filter_backends = ()  # check defaults in settings
    search_field = ("name",)
    ordering_fields = ("id", "name")


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # authentication_classes = ()  # check defaults in settings
    # permission_classes = ()  # check defaults in settings
    # filter_backends = ()  # check defaults in settings
    filterset_fields = ("is_staff", "is_superuser", "is_active")
    search_field = ("username", "email", "first_name", "last_name")
    ordering_fields = ("id", "username", "email", "first_name", "last_name")
