from django.db import models

# Create your models here.
import uuid
from django.db import models

class OperationalEvent(models.Model):
    correlation_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)

    event_type = models.CharField(max_length=30)   # NEW_INTAKE / WEEKLY_UPDATE / SUPPORT_REQUEST
    payload = models.JSONField()                   # stores form data
    status = models.CharField(max_length=20, default="PENDING")  # PENDING/PROCESSING/DONE/FAILED

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} ({self.correlation_id})"
