from django.urls import path, include
from rest_framework import routers

from core import views

app_name = "core"

router = routers.DefaultRouter()
router.register("groups", views.GroupViewSet)
router.register("users", views.UserViewSet)

urlpatterns = [
    # router urls
    path("", include(router.urls)),
]
