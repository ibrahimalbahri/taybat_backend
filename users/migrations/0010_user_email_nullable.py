from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0009_remove_driverprofile_earnings_last_month"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(blank=True, db_index=True, max_length=254, null=True, unique=True),
        ),
    ]
