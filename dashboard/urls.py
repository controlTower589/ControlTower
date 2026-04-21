from django.urls import path

from .views import (
    dashboard_home,
    workspace_detail,
    retry_workflow,
    create_matrix_room,
)

urlpatterns = [
    path("", dashboard_home, name="dashboard_home"),

    path("ws/<int:workspace_id>/", workspace_detail, name="workspace_detail"),


    path("ws/<int:workspace_id>/retry/", retry_workflow, name="retry_workflow"),

    path("ws/<int:workspace_id>/matrix/", create_matrix_room, name="create_matrix_room"),
]
