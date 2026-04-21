from django.urls import path
from .views import create_request

urlpatterns = [
    path("", create_request, name="create_request"),
]
