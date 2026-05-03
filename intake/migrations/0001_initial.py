

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="IntakeRequest",
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
                    "request_type",
                    models.CharField(
                        choices=[
                            ("NEW_INTAKE", "New intake submission"),
                            ("WEEKLY_UPDATE", "Weekly update"),
                            ("SUPPORT_REQUEST", "Support request"),
                        ],
                        max_length=20,
                    ),
                ),
                ("first_name", models.CharField(max_length=50)),
                ("last_name", models.CharField(max_length=50)),
                ("email", models.EmailField(max_length=254)),
                ("message", models.TextField(max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
