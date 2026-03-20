import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core.models import PlaybookEntry, SourceRecord


class Command(BaseCommand):
    help = "Import normalized ingestion JSON artifacts into control-plane models."

    def add_arguments(self, parser):
        parser.add_argument(
            "--index-file",
            default="services/ingestion/output/huddle_gg_index.json",
            help="Path to normalized index JSON file (repo-relative or absolute).",
        )
        parser.add_argument(
            "--plays-file",
            default="services/ingestion/output/huddle_gg_plays_sample.json",
            help="Path to normalized plays JSON file (repo-relative or absolute).",
        )
        parser.add_argument(
            "--parser-version",
            default="huddle_v1",
            help="Parser version label stored on SourceRecord.",
        )
        parser.add_argument(
            "--replace-source",
            action="store_true",
            help="Delete existing entries for the same source_name before importing.",
        )

    def handle(self, *args, **options):
        repo_root = Path(settings.BASE_DIR).parent.parent

        index_path = self._resolve_path(repo_root, options["index_file"])
        plays_path = self._resolve_path(repo_root, options["plays_file"])
        parser_version = options["parser_version"]
        replace_source = bool(options["replace_source"])

        if not index_path.exists():
            raise CommandError(f"Index file not found: {index_path}")
        if not plays_path.exists():
            raise CommandError(f"Plays file not found: {plays_path}")

        index_data = self._load_json(index_path)
        plays_data = self._load_json(plays_path)

        if not isinstance(index_data, list) or not isinstance(plays_data, list):
            raise CommandError("Input files must contain JSON arrays.")

        index_by_url = {}
        for row in index_data:
            playbook_url = row.get("playbook_url")
            if playbook_url:
                index_by_url[playbook_url] = row

        source_cache: dict[str, SourceRecord] = {}
        created_entries = 0
        updated_entries = 0
        skipped_entries = 0

        if replace_source:
            source_names = {row.get("source_name") for row in plays_data if row.get("source_name")}
            for source_name in source_names:
                stale_sources = SourceRecord.objects.filter(source_name=source_name)
                PlaybookEntry.objects.filter(source__in=stale_sources).delete()
                stale_sources.delete()

        for row in plays_data:
            playbook_url = row.get("playbook_url")
            if not playbook_url:
                continue

            if playbook_url not in source_cache:
                source_name = row.get("source_name") or "unknown_source"
                source, _ = SourceRecord.objects.get_or_create(
                    source_name=source_name,
                    source_url=playbook_url,
                    defaults={"parser_version": parser_version},
                )
                if source.parser_version != parser_version:
                    source.parser_version = parser_version
                    source.save(update_fields=["parser_version"])
                source_cache[playbook_url] = source

            index_row = index_by_url.get(playbook_url, {})
            madden_version = index_row.get("madden_version") or "Unknown"
            offense_personnel = row.get("offense_personnel") or "11"
            formation = row.get("formation") or "Unknown"
            play_name = row.get("play_name") or "Unknown"
            concept = row.get("concept") or "Unknown"

            if not self._is_valid_entry(formation, play_name, concept):
                skipped_entries += 1
                continue

            entry, created = PlaybookEntry.objects.update_or_create(
                madden_version=madden_version,
                offense_personnel=offense_personnel,
                formation=formation,
                play_name=play_name,
                source=source_cache[playbook_url],
                defaults={"concept": concept},
            )

            if created:
                created_entries += 1
            else:
                updated_entries += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported plays: created={created_entries}, updated={updated_entries}, skipped={skipped_entries}"
            )
        )

    @staticmethod
    def _resolve_path(repo_root: Path, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else repo_root / path

    @staticmethod
    def _load_json(path: Path):
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _is_valid_entry(formation: str, play_name: str, concept: str) -> bool:
        blocked_terms = {
            "subscribe",
            "gameplans",
            "offensive coordinator",
            "meta buster",
            "database",
            "playbook finder",
            "privacy",
            "terms",
            "login",
            "sign up",
            "quicksell values",
            "training",
            "platinum",
            "abilities",
            "chems",
        }

        values = [formation, play_name, concept]
        for value in values:
            cleaned = re.sub(r"\s+", " ", (value or "")).strip()
            if len(cleaned) < 2:
                return False
            if not any(char.isalpha() for char in cleaned):
                return False
            alnum = re.sub(r"[^0-9A-Za-z]", "", cleaned)
            if not alnum:
                return False
            digits = sum(1 for char in alnum if char.isdigit())
            if digits / len(alnum) > 0.45:
                return False

        lower_play = re.sub(r"\s+", " ", play_name.lower()).strip()
        if any(term in lower_play for term in blocked_terms):
            return False
        if formation.strip().lower() == "unknown" and concept.strip().lower() == "unknown":
            return False
        if formation.strip().lower() == play_name.strip().lower() and concept.strip().lower() == "unknown":
            return False
        return True
