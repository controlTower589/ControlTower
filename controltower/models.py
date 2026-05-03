
from django.db import models


class Event(models.Model):
    STATUS_CHOICES = [
        ("NEW", "NEW"),
        ("RUNNING", "RUNNING"),
        ("DONE", "DONE"),
        ("FAILED", "FAILED"),
    ]

    title = models.CharField(max_length=200, blank=True)
    event_text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Event {self.id} - {self.status}"


class AgentRun(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="runs")
    model_name = models.CharField(max_length=50, default="llama3")
    prompt = models.TextField()
    raw_response = models.TextField()
    structured_output = models.JSONField(null=True, blank=True)
    success = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
