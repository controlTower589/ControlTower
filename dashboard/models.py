

# Create your models here.


from django.db import models


class Workspace(models.Model):
    correlation_id = models.UUIDField(db_index=True, null=True, blank=True)

    event_type = models.CharField(max_length=50, default="NEW_INTAKE")
    status = models.CharField(max_length=20, default="READY")

    matrix_room_id = models.CharField(max_length=255, blank=True, null=True)

    # We reuse this existing column name as the “AI session id”
    # (ex: ollama-session-24)
    webui_session_id = models.CharField(max_length=255, blank=True, null=True)

    latest_summary = models.TextField(blank=True, null=True)
    next_actions = models.TextField(blank=True, null=True)

    requester_first_name = models.CharField(max_length=100, blank=True, default="")
    requester_last_name = models.CharField(max_length=100, blank=True, default="")
    requester_email = models.EmailField(blank=True, default="")
    intake_id = models.IntegerField(blank=True, null=True)

    structured_output = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.correlation_id} ({self.event_type})"