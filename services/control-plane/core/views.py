from django.http import JsonResponse

from .models import PlaybookEntry


def healthz(_request):
    return JsonResponse({"status": "ok"})


def playbook_entries(request):
    offense_personnel = request.GET.get("offense_personnel")
    madden_version = request.GET.get("madden_version")
    concepts_param = request.GET.get("concepts", "")
    limit = min(int(request.GET.get("limit", "100")), 250)

    concepts = [item.strip().lower() for item in concepts_param.split(",") if item.strip()]

    queryset = PlaybookEntry.objects.select_related("source").all().order_by("play_name")

    if offense_personnel:
        queryset = queryset.filter(offense_personnel=offense_personnel)

    if madden_version:
        queryset = queryset.filter(madden_version=madden_version)

    if concepts:
        queryset = queryset.filter(concept__iregex="|".join(concepts))

    records = [
        {
            "id": entry.id,
            "madden_version": entry.madden_version,
            "offense_personnel": entry.offense_personnel,
            "formation": entry.formation,
            "play_name": entry.play_name,
            "concept": entry.concept,
            "source_name": entry.source.source_name,
            "source_url": entry.source.source_url,
        }
        for entry in queryset[:limit]
    ]

    return JsonResponse({"count": len(records), "results": records})
