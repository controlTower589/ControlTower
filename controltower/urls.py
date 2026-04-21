from django.urls import path
from .views import create_event, run_event_agent
from .views import control_tower_dashboard
from .views import event_detail
from .views import run_agent_from_ui
from .views import create_event_ui
from .swagger_views import swagger_ui, openapi_yaml


urlpatterns = [
    path("api/events/", create_event),
    path("api/events/<int:event_id>/run/", run_event_agent),
    path("control-tower/", control_tower_dashboard),
    path("control-tower/events/<int:event_id>/", event_detail),
    path("control-tower/events/<int:event_id>/run/", run_agent_from_ui),
    path("control-tower/new/", create_event_ui),
path("api/openapi.yaml", openapi_yaml, name="openapi_yaml"),
    path("swagger/", swagger_ui, name="swagger_ui"),



]
