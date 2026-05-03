

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Event",
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
                ("title", models.CharField(blank=True, max_length=200)),
                ("event_text", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("NEW", "NEW"),
                            ("RUNNING", "RUNNING"),
                            ("DONE", "DONE"),
                            ("FAILED", "FAILED"),
                        ],
                        default="NEW",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="AgentRun",
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
                ("model_name", models.CharField(default="llama3", max_length=50)),
                ("prompt", models.TextField()),
                ("raw_response", models.TextField()),
                ("structured_output", models.JSONField(blank=True, null=True)),
                ("success", models.BooleanField(default=False)),
                ("error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="runs",
                        to="controltower.event",
                    ),
                ),
            ],
        ),
    ]
