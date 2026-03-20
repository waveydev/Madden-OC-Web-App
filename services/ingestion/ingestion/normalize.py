from datetime import datetime, timezone


def normalize_index_entries(source_name: str, rows: list[dict]) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    normalized: list[dict] = []
    for row in rows:
        normalized.append(
            {
                "source_name": source_name,
                "captured_at": now,
                "team": row.get("team", "Unknown"),
                "madden_version": row.get("madden_version", "Unknown"),
                "playbook_url": row.get("playbook_url", ""),
                "raw_label": row.get("raw_label", ""),
            }
        )
    return normalized


def normalize_play_entries(source_name: str, playbook_url: str, rows: list[dict]) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    normalized: list[dict] = []
    for row in rows:
        normalized.append(
            {
                "source_name": source_name,
                "captured_at": now,
                "playbook_url": playbook_url,
                "offense_personnel": "11",
                "formation": row.get("formation", "Unknown"),
                "play_name": row.get("play_name", "Unknown"),
                "concept": row.get("concept", "Unknown"),
                "raw_text": row.get("raw_text", ""),
            }
        )
    return normalized
