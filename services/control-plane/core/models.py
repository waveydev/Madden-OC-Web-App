from django.db import models


class SourceRecord(models.Model):
    source_name = models.CharField(max_length=128)
    source_url = models.URLField()
    parser_version = models.CharField(max_length=32, default="v1")
    captured_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.source_name} @ {self.captured_at.date()}"


class PlaybookEntry(models.Model):
    madden_version = models.CharField(max_length=16)
    offense_personnel = models.CharField(max_length=16)
    formation = models.CharField(max_length=128)
    play_name = models.CharField(max_length=128)
    concept = models.CharField(max_length=64)
    source = models.ForeignKey(SourceRecord, on_delete=models.PROTECT, related_name="entries")

    class Meta:
        unique_together = (
            "madden_version",
            "offense_personnel",
            "formation",
            "play_name",
            "source",
        )

    def __str__(self) -> str:
        return f"{self.play_name} ({self.formation})"
