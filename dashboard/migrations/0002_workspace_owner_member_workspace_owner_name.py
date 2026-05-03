

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_initial"),
        ("team", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="workspace",
            name="owner_member",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="team.teammember",
            ),
        ),
        migrations.AddField(
            model_name="workspace",
            name="owner_name",
            field=models.CharField(blank=True, default="None", max_length=255),
        ),
    ]
