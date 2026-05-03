from django.urls import path
from .views import audit_for_correlation, audit_for_correlation_api

urlpatterns = [
    path("<str:correlation_id>/", audit_for_correlation, name="audit_logs"),
    path("api/<str:correlation_id>/", audit_for_correlation_api, name="audit_logs_api"),
]

