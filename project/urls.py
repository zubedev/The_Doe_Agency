"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt import views as jwt

from project import settings

urlpatterns = [
    # admin panel -------------------------------------------------------------
    path("admin/", admin.site.urls),
    # health checks -----------------------------------------------------------
    path("health/", include("health_check.urls")),
    # drf simple jwt ----------------------------------------------------------
    path(
        "token/obtain/",
        jwt.TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh/",
        jwt.TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    # core urls ---------------------------------------------------------------
    path("core/", include("core.urls")),
    # scraper urls ------------------------------------------------------------
    path("api/", include("scraper.urls")),
]

# development environment urls ------------------------------------------------
if settings.ENVIRON == "dev":
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )

    # drf auth endpoints during dev
    urlpatterns.append(path("drf/", include("rest_framework.urls")))

    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

# admin site customizations ---------------------------------------------------
admin.sites.AdminSite.site_header = "TDA Administration"
admin.sites.AdminSite.site_title = "TDA Administration"
admin.sites.AdminSite.index_title = "The Doe Agency Admin Panel"
