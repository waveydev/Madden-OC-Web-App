from django.contrib import admin

from .models import PlaybookEntry, SourceRecord


@admin.register(SourceRecord)
class SourceRecordAdmin(admin.ModelAdmin):
    list_display = ("source_name", "source_url", "parser_version", "captured_at")
    search_fields = ("source_name", "source_url")


@admin.register(PlaybookEntry)
class PlaybookEntryAdmin(admin.ModelAdmin):
    list_display = ("play_name", "formation", "concept", "offense_personnel", "madden_version")
    list_filter = ("madden_version", "offense_personnel", "concept")
    search_fields = ("play_name", "formation", "concept")
