from django.db import models

# Create your models here.
from django.db import models

class IntakeRequest(models.Model):
    class RequestType(models.TextChoices):
        NEW_INTAKE = "NEW_INTAKE", "New intake submission"
        WEEKLY_UPDATE = "WEEKLY_UPDATE", "Weekly update"
        SUPPORT_REQUEST = "SUPPORT_REQUEST", "Support request"

    request_type = models.CharField(max_length=20, choices=RequestType.choices)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=254)
    message = models.TextField(max_length=1000)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.request_type} - {self.first_name} {self.last_name}"
