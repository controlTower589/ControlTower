from django.urls import path
from . import views

urlpatterns = [
    path("members/", views.team_members_list, name="team_members_list"),
    path("members/add/", views.team_member_create, name="team_member_create"),
    path("members/<int:member_id>/edit/", views.team_member_edit, name="team_member_edit"),
    path("members/<int:member_id>/toggle/", views.team_member_toggle, name="team_member_toggle"),
    path("members/<int:member_id>/delete/", views.team_member_delete, name="team_member_delete"),
]
