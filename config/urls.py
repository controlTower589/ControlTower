"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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

from django.contrib import admin

from django.urls import path, include

from controltower.swagger_views import swagger_ui, openapi_yaml

urlpatterns = [
    path("admin/", admin.site.urls),

    # Existing apps
    path("", include("intake.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("audit/", include("audit.urls")),

    # NEW Control Tower APIs
path("swagger/", swagger_ui),
    path("api/openapi.yaml", openapi_yaml),

path("team/", include("team.urls")),
]

