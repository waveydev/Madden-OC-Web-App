from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SourceRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_name", models.CharField(max_length=128)),
                ("source_url", models.URLField()),
                ("parser_version", models.CharField(default="v1", max_length=32)),
                ("captured_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="PlaybookEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("madden_version", models.CharField(max_length=16)),
                ("offense_personnel", models.CharField(max_length=16)),
                ("formation", models.CharField(max_length=128)),
                ("play_name", models.CharField(max_length=128)),
                ("concept", models.CharField(max_length=64)),
                (
                    "source",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="entries", to="core.sourcerecord"),
                ),
            ],
            options={
                "unique_together": {("madden_version", "offense_personnel", "formation", "play_name", "source")},
            },
        ),
    ]
