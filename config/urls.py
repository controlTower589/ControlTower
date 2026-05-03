

from django.contrib import admin

from django.urls import path, include

from controltower.swagger_views import swagger_ui, openapi_yaml



urlpatterns = [



    path("admin/", admin.site.urls),

    path("", include("intake.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("audit/", include("audit.urls")),


path("swagger/", swagger_ui),
    path("api/openapi.yaml", openapi_yaml),

path("team/", include("team.urls")),
]

