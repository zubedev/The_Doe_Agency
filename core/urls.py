from django.urls import path, include
from rest_framework import routers

from core import views

router = routers.DefaultRouter()
router.register("groups", views.GroupViewSet)
router.register("users", views.UserViewSet)

urlpatterns = [
    # router urls
    path("", include(router.urls)),
]
