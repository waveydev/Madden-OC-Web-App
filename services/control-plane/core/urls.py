from django.urls import path

from .views import healthz, playbook_entries

urlpatterns = [
    path("healthz", healthz),
    path("api/playbook-entries", playbook_entries),
]
