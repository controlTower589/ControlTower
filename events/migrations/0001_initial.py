

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="OperationalEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "correlation_id",
                    models.UUIDField(db_index=True, default=uuid.uuid4, editable=False),
                ),
                ("event_type", models.CharField(max_length=30)),
                ("payload", models.JSONField()),
                ("status", models.CharField(default="PENDING", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
